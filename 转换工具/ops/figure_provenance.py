"""核对八份图表追溯文档, 并把完整记录同步到现有 PPT 来源批注.

这是可复用运维工具, 不计算实验指标、不重画图形、不修改备注或作者批注.
主要入口为 run(root, sync), 命令为 `python 转换工具/ops/figure_provenance.py --check|--sync`.
--root 指定论文仓库; 默认使用本脚本所属仓库. 报告及写入前备份只进入 root/temp/.

每条 Markdown 记录由 `<!-- provenance:begin ID -->` 和相同 ID 的 end 标记包围.
记录首个非空行为 `<!-- provenance-meta {JSON} -->`, 随后的完整正文进入 PPT 来源批注.
JSON 必填字段为 id、kind、entries、inputs、status; figure 还需 pptx 和 figure.
entries 为 [{"path": "仓库相对路径", "symbol": "可选 Python 限定名"}], inputs 为路径字符串列表.
kind 为 figure、table 或 claim; table 用整数 table 对应正文表号. 额外字段原样容忍.
本工具只追加或更新以 PROVENANCE v1 开头的自有批注. 新批注复用现有作者,
不创建新账户; 只按作者授权归并 Figure Editor 占位署名, 传统批注追加时推进 lastIdx.
目标图必须已有独立 @@图名批注及 comments 关系; 本工具不猜测无图名页面的身份.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import posixpath
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rebuild_support.source_dependencies import code_dependencies, source_owner
try:
    from lxml import etree as XML
except ImportError:
    # 优先采用当前 Python 的二进制扩展, 避免不同 Python 版本的本地依赖抢先遮蔽.
    if (REPOSITORY / ".manuscript_deps").is_dir():
        sys.path.insert(0, str(REPOSITORY / ".manuscript_deps"))
    for module_name in list(sys.modules):
        if module_name == "lxml" or module_name.startswith("lxml."):
            del sys.modules[module_name]
    from lxml import etree as XML


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
M = "http://schemas.microsoft.com/office/powerpoint/2018/8/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_R = "http://schemas.openxmlformats.org/package/2006/relationships"
STAGES = ("stage1", "stage2", "stage3", "e2e")
CATEGORIES = ("calculate", "visualization")
MANUSCRIPTS = ("论文草稿.md", "draft.md", "补充材料.md", "supplementary.md")
BLOCK = re.compile(r"<!--\s*provenance:begin\s+([^\s>]+)\s*-->(.*?)<!--\s*provenance:end\s+\1\s*-->", re.S)
META = re.compile(r"\A\s*<!--\s*provenance-meta\s+(\{.*?\})\s*-->\s*", re.S)
PPTFIG = re.compile(r'\{\{pptfig:\s*"([^"]+)"\s*\|\s*([^\s|{}]+)(?:\|[^{}]*)?\}\}')
FIGURE = re.compile(r"@@([^\s|{}]+)\Z")
MANAGED = re.compile(r"\APROVENANCE v1\nid: ([^\n]+)\nsource: ([^\n]+)\n")
XML_PARSER = XML.XMLParser(remove_blank_text=False, resolve_entities=False, no_network=True)


@dataclass
class Record:
    """一条可冷读来源记录; body 为去掉机器元注释后的 Markdown 原文."""

    identifier: str
    document: str
    metadata: dict
    body: str

    @property
    def comment(self) -> str:
        return f"PROVENANCE v1\nid: {self.identifier}\nsource: {self.document}\n\n{self.body}"


@dataclass
class Slide:
    """实际 presentation 关系中的幻灯片, 不用 slideN 文件名推断页码."""

    part: str
    page: int
    comments: list[str]
    names: list[str]


def base_figure(name: str) -> str:
    """去掉末尾作者版本号, 如 foo-NO_LEVEL(v2) -> foo-NO_LEVEL; 保留科学条件和其他名称."""
    return re.sub(r"\(v[0-9]+\)$", "", name)


def xml_bytes(node) -> bytes:
    return XML.tostring(node, encoding="UTF-8", xml_declaration=True, standalone=True)


def relationship_target(part: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target).lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def relative_path(root: Path, value: str) -> Path:
    """把机器字段解析为仓库内路径, 禁止绝对路径与越界路径."""
    if not isinstance(value, str) or not value.strip() or Path(value).is_absolute() or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"需要非空仓库相对路径: {value!r}")
    path = (root / value.replace("\\", "/")).resolve()
    path.relative_to(root)
    return path


def comment_text(comment) -> str:
    """现代段落与传统 text 都还原成 LF 文本, 保留正文内部换行."""
    legacy = comment.find(f"{{{P}}}text")
    if legacy is not None:
        return (legacy.text or "").replace("\r\n", "\n").replace("\r", "\n")
    body = comment.find(f"{{{M}}}txBody")
    if body is None:
        return ""
    paragraphs = []
    for paragraph in body.findall(f"{{{A}}}p"):
        paragraphs.append("".join("\n" if node.tag == f"{{{A}}}br" else node.text or "" for node in paragraph.iter() if node.tag in (f"{{{A}}}t", f"{{{A}}}br")))
    return "\n".join(paragraphs)


def set_comment_text(comment, text: str) -> None:
    legacy = comment.find(f"{{{P}}}text")
    if legacy is not None:
        legacy.text = text
        return
    body = comment.find(f"{{{M}}}txBody")
    replacement = XML.Element(f"{{{M}}}txBody")
    if body is not None:
        comment.replace(body, replacement)
    else:
        comment.append(replacement)
    body = replacement
    XML.SubElement(body, f"{{{A}}}bodyPr")
    XML.SubElement(body, f"{{{A}}}lstStyle")
    for line in text.split("\n"):
        paragraph = XML.SubElement(body, f"{{{A}}}p")
        run = XML.SubElement(paragraph, f"{{{A}}}r")
        content = XML.SubElement(run, f"{{{A}}}t")
        content.text = line
        if line != line.strip():
            content.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


class Deck:
    """读取 ZIP 图集并维护有限部件补丁; 未修改部件的解压字节完全保留."""

    def __init__(self, path: Path):
        self.path = path
        self.original = path.read_bytes()
        with ZipFile(path) as package:
            self.data = {name: package.read(name) for name in package.namelist()}
        self.trees = {}
        self.changed = set()
        self.slides = []
        self.figures = {}
        self.author_parts = []
        presentation = self.tree("ppt/presentation.xml")
        relations = self.tree("ppt/_rels/presentation.xml.rels")
        by_id = {relation.get("Id"): relation for relation in relations}
        for relation in relations:
            if relation.get("Type", "").rsplit("/", 1)[-1] in ("authors", "commentAuthors"):
                self.author_parts.append(relationship_target("ppt/presentation.xml", relation.get("Target")))
        for page, slide_node in enumerate(presentation.findall(f"{{{P}}}sldIdLst/{{{P}}}sldId"), 1):
            relation = by_id[slide_node.get(f"{{{R}}}id")]
            part = relationship_target("ppt/presentation.xml", relation.get("Target"))
            rel_part = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
            comment_parts = []
            names = []
            if rel_part in self.data:
                for slide_relation in self.tree(rel_part):
                    if slide_relation.get("Type", "").endswith("/comments"):
                        comment_part = relationship_target(part, slide_relation.get("Target"))
                        self.tree(comment_part)
                        comment_parts.append(comment_part)
                        for comment in self.comments(comment_part):
                            match = FIGURE.fullmatch(comment_text(comment).strip())
                            if match:
                                names.append(match.group(1))
            slide = Slide(part, page, comment_parts, names)
            self.slides.append(slide)
            if len(names) > 1:
                raise ValueError(f"第 {page} 页含多个 @@ 图名: {names}")
            for name in names:
                if name in self.figures:
                    raise ValueError(f"图名重复: {name}, 第 {self.figures[name].page}、{page} 页")
                self.figures[name] = slide

    def tree(self, part: str):
        if part not in self.trees:
            self.trees[part] = XML.fromstring(self.data[part], parser=XML_PARSER)
        return self.trees[part]

    def comments(self, part: str):
        return [node for node in self.tree(part) if isinstance(node.tag, str) and XML.QName(node).localname == "cm"]

    def managed(self) -> dict[str, list[tuple[Slide, str, object]]]:
        found = {}
        for slide in self.slides:
            for part in slide.comments:
                for comment in self.comments(part):
                    match = MANAGED.match(comment_text(comment))
                    if match:
                        found.setdefault(match.group(1), []).append((slide, part, comment))
        return found

    def use_author(self, name: str, initials: str) -> None:
        """将旧 Figure Editor 批注归于作者已有身份, 不增加作者ID或修改批注文字.

        name/initials 是作者确认的显示姓名与缩写; 若图集中仅有旧编辑占位身份, 原位更名并沿用其ID.
        传统批注的 idx 在归并后重新分配, 避免不同作者原先相同的序号发生冲突.
        """
        for part in self.author_parts:
            authors = self.tree(part)
            aliases = [node for node in authors if node.get('name') == 'Figure Editor']
            if not aliases:
                continue
            owner = next((node for node in authors if node.get('name') == name), aliases[0])
            owner.set('name', name)
            owner.set('initials', initials)
            previous = {node.get('id') for node in aliases if node is not owner}
            last_index = int(owner.get('lastIdx', '0'))
            for comment_part in self.data:
                if comment_part.startswith('ppt/comments/') and comment_part.endswith('.xml'):
                    last_index = max([last_index] + [int(node.get('idx', '0')) for node in self.comments(comment_part) if node.get('authorId') == owner.get('id')])
            for comment_part in self.data:
                if not comment_part.startswith('ppt/comments/') or not comment_part.endswith('.xml'):
                    continue
                for node in self.tree(comment_part).iter():
                    if node.get('authorId') in previous:
                        node.set('authorId', owner.get('id'))
                        if XML.QName(node).namespace == P and node.get('idx') is not None:
                            last_index += 1
                            node.set('idx', str(last_index))
                            owner.set('lastIdx', str(last_index))
                        self.changed.add(comment_part)
            for node in aliases:
                if node is not owner:
                    authors.remove(node)
            self.changed.add(part)

    def append(self, slide: Slide, text: str) -> None:
        """基于该页图名批注创建同制式来源批注, 只复用作者注册表中的现有身份."""
        templates = [(part, comment) for part in slide.comments for comment in self.comments(part) if FIGURE.fullmatch(comment_text(comment).strip())]
        if len(templates) != 1:
            raise ValueError(f"第 {slide.page} 页没有唯一可复用的图名批注")
        part, template = templates[0]
        author_id = template.get("authorId")
        modern = XML.QName(template).namespace == M
        author_kind = "author" if modern else "cmAuthor"
        authors = [(author_part, author) for author_part in self.author_parts for author in self.tree(author_part) if isinstance(author.tag, str) and XML.QName(author).localname == author_kind and author.get("id") == author_id]
        if len(authors) != 1:
            raise ValueError(f"无法在现有作者注册表中唯一复用 authorId={author_id}; 不创建账户")
        new = copy.deepcopy(template)
        stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        if modern:
            new.set("id", "{" + str(uuid.uuid4()).upper() + "}")
            new.set("created", stamp)
            for child in list(new):
                if not isinstance(child.tag, str) or XML.QName(child).localname not in ("sldMkLst", "pos"):
                    new.remove(child)
        else:
            author_part, author = authors[0]
            indices = [int(author.get("lastIdx", "0"))]
            for candidate_part in self.data:
                if candidate_part.startswith("ppt/comments/") and candidate_part.endswith(".xml"):
                    indices.extend(int(comment.get("idx", "0")) for comment in self.comments(candidate_part) if comment.get("authorId") == author_id)
            index = max(indices) + 1
            new.set("idx", str(index))
            new.set("dt", stamp)
            author.set("lastIdx", str(index))
            self.changed.add(author_part)
            for child in list(new):
                if not isinstance(child.tag, str) or XML.QName(child).localname not in ("pos", "text"):
                    new.remove(child)
        set_comment_text(new, text)
        self.tree(part).append(new)
        self.changed.add(part)

    def save(self, root: Path, backup_directory: Path) -> None:
        """替换前再次比对原文件, 备份后仅写补丁部件; 锁定的 PPT 保留原文件并报错."""
        if self.path.read_bytes() != self.original:
            raise ValueError(f"PPT 在检查后被外部修改, 请保存后重试: {self.path}")
        backup = backup_directory / self.path.relative_to(root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(self.original)
        root.joinpath("temp").mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="provenance_", suffix=".pptx", dir=root / "temp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
        try:
            with ZipFile(self.path) as source, ZipFile(temporary_path, "w") as target:
                target.comment = source.comment
                for info in source.infolist():
                    payload = xml_bytes(self.trees[info.filename]) if info.filename in self.changed else source.read(info.filename)
                    target.writestr(info, payload)
            if self.path.read_bytes() != self.original:
                raise ValueError(f"PPT 在打包期间被外部修改, 已保留作者文件: {self.path}")
            temporary_path.replace(self.path)
        finally:
            temporary_path.unlink(missing_ok=True)


def load_records(root: Path, errors: list[str]) -> list[Record]:
    """只读八份文档和当前 PPT, 返回显式记录与自动继承的作者版本.

    root 指论文仓库, errors 原位追加格式问题; 不写文件或修改 PPT.
    末尾 (v数字) 页面继承基础记录, 派生 id/figure 为实际页名, author_origin 为基础图名,
    rebuild.figure 保留基础科学入口, body 添加继承说明; 已显式登记的版本保留其原文.
    """
    records = []
    seen = set()
    for stage in STAGES:
        for category in CATEGORIES:
            document = f"画图/画图代码/{stage}/{category}/图表追溯.md"
            path = root / document
            if not path.is_file():
                errors.append(f"追溯文档缺失: {document}")
                continue
            text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            blocks = list(BLOCK.finditer(text))
            if len(blocks) != len(re.findall(r"<!--\s*provenance:begin\b", text)) or len(blocks) != len(re.findall(r"<!--\s*provenance:end\b", text)):
                errors.append(f"记录 begin/end 不配对: {document}")
            for block in blocks:
                identifier, content = block.groups()
                label = f"{document} [{identifier}]"
                if identifier in seen:
                    errors.append(f"追溯 ID 重复: {label}")
                    continue
                seen.add(identifier)
                metadata_match = META.match(content)
                if metadata_match is None:
                    errors.append(f"记录开头缺少 provenance-meta JSON: {label}")
                    continue
                try:
                    metadata = json.loads(metadata_match.group(1))
                    if metadata["id"] != identifier:
                        raise ValueError("meta.id 与 begin/end 不一致")
                    if metadata["kind"] not in ("figure", "table", "claim"):
                        raise ValueError("kind 只允许 figure/table/claim")
                    if not isinstance(metadata["entries"], list) or not isinstance(metadata["inputs"], list):
                        raise ValueError("entries 和 inputs 必须是列表")
                    if any(not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or ("symbol" in entry and not isinstance(entry["symbol"], str)) for entry in metadata["entries"]):
                        raise ValueError("每个 entry 必须含字符串 path, 可选 symbol 也必须是字符串")
                    if any(not isinstance(value, str) for value in metadata["inputs"]):
                        raise ValueError("每个 input 必须是路径字符串")
                    if not isinstance(metadata["status"], str) or not metadata["status"].strip():
                        raise ValueError("status 必须是非空字符串")
                    if metadata["kind"] == "figure" and not all(isinstance(metadata[key], str) and metadata[key].strip() for key in ("pptx", "figure")):
                        raise ValueError("figure 必须提供非空 pptx 和 figure")
                    if metadata["kind"] == "table" and (type(metadata.get("table")) is not int or metadata["table"] < 1):
                        raise ValueError("table 必须提供正整数 table 表号")
                    body = content[metadata_match.end():].strip()
                    if not body:
                        raise ValueError("缺少可冷读追溯正文")
                    records.append(Record(identifier, document, metadata, body))
                except (KeyError, TypeError, ValueError) as error:
                    errors.append(f"记录格式错误: {label}: {error}")
    # 八份文档登记科学基础; 当前 PPT 的 (v数字) 页面自动继承, 不要求复制同一份来源正文.
    registered = {(item.metadata.get('pptx'), item.metadata.get('figure')): item for item in records if item.metadata['kind'] == 'figure'}
    for pptx in dict.fromkeys(key[0] for key in registered):
        try:
            deck = Deck(relative_path(root, pptx))
        except (OSError, KeyError, ValueError, BadZipFile, XML.XMLSyntaxError):
            # 正式 run 会报告损坏或缺失 PPT; 此处只展开能实际定位的作者版本.
            continue
        for name in deck.figures:
            original = base_figure(name)
            source = registered.get((pptx, original))
            if original == name or source is None:
                continue
            existing = registered.get((pptx, name))
            if existing is not None:
                existing.metadata['author_origin'] = original
                continue
            metadata = copy.deepcopy(source.metadata)
            metadata.update(id=name, figure=name, author_origin=original)
            metadata['rebuild']['figure'] = original
            body = f'## {name}｜作者编辑版\n\n本页继承 @@{original} 的科学来源、输入和统计定义。当前可编辑 PPT 保存作者排版；科学重建使用原版入口，不覆盖作者版本。\n\n' + source.body
            derived = Record(name, source.document, metadata, body)
            records.append(derived)
            registered[(pptx, name)] = derived
    return records


def check_sources(root: Path, records: list[Record], errors: list[str]) -> None:
    """检查本地入口、Python 限定名和冻结输入; 不运行科学程序."""
    for record in records:
        if record.metadata['kind']=='figure':
            sharing=record.metadata.get('sharing')
            rebuild=record.metadata.get('rebuild')
            if not isinstance(sharing,list):
                errors.append(f'{record.identifier}: 缺少sharing共享关系登记，独立图也需显式空列表')
                sharing=[]
            expected = {record.metadata['figure'], base_figure(record.metadata['figure'])}
            if not isinstance(rebuild,dict) or rebuild.get('figure') not in expected or rebuild.get('script')!='转换工具/ops/rebuild_figures.py' or not (root/'转换工具/ops/rebuild_figures.py').is_file():
                errors.append(f'{record.identifier}: 缺少有效完整重建入口')
            owners=[]
            for entry in record.metadata['entries']:
                owner=source_owner(root/entry['path'],root)
                if owner is not None:owners.append(owner)
            declared=set()
            for shared in sharing:
                try:
                    owner=relative_path(root,shared['path'])
                    if not owner.is_dir() or not isinstance(shared['figures'],list) or not shared['purpose'].strip():raise ValueError('共享目录、关联图名或用途不完整')
                    known={item.metadata.get('figure') for item in records if item.metadata['kind']=='figure'}
                    # 当前作者版仍可注明已退役的直接来源名, 历史记录不必为改名重写冻结 PPT.
                    known.update(item.metadata['author_origin'] for item in records if item.metadata.get('author_origin'))
                    if any(name not in known for name in shared['figures']):raise ValueError('关联图名没有登记')
                    if '共享' not in record.body or any('@@'+name not in record.body for name in shared['figures']):raise ValueError('共享关系必须在可冷读正文和PPT副本中明确说明')
                    declared.add(owner)
                except (KeyError,TypeError,ValueError) as error:errors.append(f'{record.identifier}: 共享登记错误: {error}')
            if owners:
                try:
                    paths,temporary=code_dependencies(root,record.metadata['entries'])
                    foreign={source_owner(path,root) for path in paths}-{None,owners[0]}
                    for owner in foreign-declared:errors.append(f'{record.identifier}: 未登记跨目录代码依赖: {owner.relative_to(root)}')
                    for path in temporary:errors.append(f'{record.identifier}: 传递依赖包含旧temp搜索路径: {path}')
                except (OSError,SyntaxError,ValueError) as error:errors.append(f'{record.identifier}: 依赖读取失败: {error}')
        for entry in record.metadata["entries"]:
            try:
                path = relative_path(root, entry["path"])
                if not path.is_file():
                    raise ValueError(f"入口文件不存在: {entry['path']}")
                if path.relative_to(root).parts[0] == "temp" or "archive" in path.relative_to(root).parts:
                    raise ValueError(f"有效入口不得依赖 temp/archive: {entry['path']}")
                symbol = entry.get("symbol")
                if symbol:
                    if path.suffix.lower() != ".py":
                        raise ValueError(f"symbol 只支持 Python AST: {entry['path']}")
                    nodes = [ast.parse(path.read_text(encoding="utf-8-sig"))]
                    for name in symbol.split("."):
                        nodes = [child for node in nodes for child in getattr(node, "body", []) if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and child.name == name]
                    if not nodes:
                        raise ValueError(f"Python 符号不存在: {entry['path']}::{symbol}")
            except (KeyError, TypeError, ValueError, OSError, SyntaxError) as error:
                errors.append(f"{record.identifier}: {error}")
        for value in record.metadata["inputs"]:
            try:
                path = relative_path(root, value)
                if not path.exists():
                    raise ValueError(f"冻结输入不存在: {value}")
                if path.relative_to(root).parts[0] == "temp":
                    raise ValueError(f"冻结输入不得留在 temp: {value}")
            except (TypeError, ValueError, OSError) as error:
                errors.append(f"{record.identifier}: {error}")


def check_layout(root: Path, errors: list[str]) -> None:
    base = root / "画图/画图代码"
    if not base.is_dir():
        errors.append("画图/画图代码 不存在")
        return
    expected = set(STAGES) | {"archive"}
    actual = {path.name for path in base.iterdir()}
    if actual != expected:
        errors.append(f"画图代码顶层须恰为 stage1/stage2/stage3/e2e/archive: 实际 {sorted(actual)}")
    for stage in sorted(expected):
        folder = base / stage
        actual = {path.name for path in folder.iterdir()} if folder.is_dir() else set()
        if actual != {"calculate", "visualization", "output"} or any(not (folder / name).is_dir() for name in actual):
            errors.append(f"{stage} 直属层须恰为 calculate/visualization/output 三个目录: 实际 {sorted(actual)}")


def check_coverage(root: Path, records: list[Record], errors: list[str]) -> dict[tuple[str, str], Record]:
    figures = {}
    tables = set()
    for record in records:
        if record.metadata["kind"] == "table":
            tables.add(record.metadata["table"])
        if record.metadata["kind"] != "figure":
            continue
        try:
            pptx = relative_path(root, record.metadata["pptx"]).relative_to(root).as_posix()
            key = (pptx, record.metadata["figure"])
            if key in figures:
                errors.append(f"同一 PPT 图登记多次: {key}")
            figures[key] = record
        except (TypeError, ValueError) as error:
            errors.append(f"{record.identifier}: {error}")
    captions = set()
    for manuscript in MANUSCRIPTS:
        path = root / manuscript
        if not path.is_file():
            errors.append(f"论文源稿缺失: {manuscript}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        # 围栏代码仅是语法示例, 不视为当前论文的引用.
        text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", "", text)
        for pptx, figure in PPTFIG.findall(text):
            try:
                key = (relative_path(root, pptx).relative_to(root).as_posix(), figure)
                if key not in figures:
                    errors.append(f"论文插图未登记: {manuscript}: {key[0]}|{figure}")
            except (TypeError, ValueError) as error:
                errors.append(f"论文插图路径错误: {manuscript}: {error}")
        captions.update(int(number) for number in re.findall(r"<caption[^>]*>\s*(?:表\s*|Table\s+)(\d+)", text, re.I))
    for number in sorted(captions - tables):
        errors.append(f"论文表格未登记: 表 {number}")
    if not any(record.metadata["kind"] == "claim" for record in records):
        errors.append("缺少独立正文实验数字的 claim 记录; 自然语言数字仍须人工逐项核验")
    return figures


def run(root: Path, sync: bool = False) -> dict:
    """预检全部结构与路径后同步, 再重新读取核对; 返回可序列化报告.

    报告字段: mode 为 check/sync, records 为登记总数, figures 为图记录数, 均包含自动继承记录,
    updated 为本轮改写的 PPT 仓库相对路径, errors 为失败说明列表,
    limitations 明确自然语言穷举与科学数值重算不属于此工具的验证边界.
    """
    root = root.resolve()
    errors = []
    check_layout(root, errors)
    records = load_records(root, errors)
    check_sources(root, records, errors)
    figures = check_coverage(root, records, errors)
    decks = {}
    for pptx, _ in figures:
        if pptx in decks:
            continue
        try:
            decks[pptx] = Deck(root / pptx)
        except (OSError, KeyError, ValueError, BadZipFile, XML.XMLSyntaxError) as error:
            errors.append(f"PPT 读取失败: {pptx}: {error}")
    for pptx, deck in decks.items():
        if sync and Path(pptx).parent == Path('画图'):
            deck.use_author('Hongen Peng', 'HP')
        expected_ids = {record.identifier for key, record in figures.items() if key[0] == pptx}
        for identifier, owned in deck.managed().items():
            for slide, _, _ in owned:
                target = next((figures[(pptx, name)] for name in slide.names if (pptx, name) in figures), None)
                if identifier not in expected_ids and (target is None or identifier != target.metadata.get('author_origin')):
                    errors.append(f"PPT 中有未登记的来源批注: {pptx}: {identifier}")
    actions = []
    for (pptx, figure), record in figures.items():
        if pptx not in decks:
            continue
        deck = decks[pptx]
        if figure not in deck.figures:
            errors.append(f"@@ 图名不存在: {pptx}|{figure}; 无 comments 关系的页不能凭页码猜测")
            continue
        slide = deck.figures[figure]
        all_owned = deck.managed().get(record.identifier, [])
        owned = [item for item in all_owned if item[0].part == slide.part]
        unexpected = []
        for item in all_owned:
            if item[0].part == slide.part:
                continue
            children = [figures[(pptx, name)] for name in item[0].names if (pptx, name) in figures]
            if not any(child.metadata.get('author_origin') == record.metadata['figure'] for child in children):
                unexpected.append(item)
        if not owned and record.metadata.get('author_origin'):
            # 作者复制页面或改名时保留的旧来源批注, 在原位置更名, 不再追加第二份.
            parent = figures.get((pptx, record.metadata['author_origin']))
            origin_id = parent.identifier if parent else record.metadata['author_origin']
            owned = [item for item in deck.managed().get(origin_id, []) if item[0].part == slide.part]
        if len(owned) > 1 or unexpected:
            errors.append(f"来源批注重复或附着到错误页面: {pptx}|{figure}: {record.identifier}")
        elif not owned or comment_text(owned[0][2]) != record.comment:
            if sync:
                actions.append((deck, slide, owned, record))
            else:
                errors.append(f"来源批注缺失或与文档不一致: {pptx}|{figure}: {record.identifier}")
    updated = []
    if sync and not errors:
        # 所有追加操作先在内存完成, 避免作者注册表缺失时发生半次同步.
        try:
            for deck, slide, owned, record in actions:
                if owned:
                    _, part, comment = owned[0]
                    set_comment_text(comment, record.comment)
                    deck.changed.add(part)
                else:
                    deck.append(slide, record.comment)
        except (KeyError, ValueError) as error:
            errors.append(f"同步预检失败, 尚未写入 PPT: {error}")
        if not errors:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
            backup_directory = root / "temp/figure_provenance_backups" / stamp
            for pptx, deck in decks.items():
                if not deck.changed:
                    continue
                try:
                    deck.save(root, backup_directory)
                    updated.append(pptx)
                except (OSError, ValueError) as error:
                    errors.append(f"PPT 写入失败: {pptx}: {error}")
            if not errors:
                for (pptx, figure), record in figures.items():
                    owned = Deck(root / pptx).managed().get(record.identifier, [])
                    if len(owned) != 1 or comment_text(owned[0][2]) != record.comment:
                        errors.append(f"写入后复核失败: {pptx}|{figure}")
    report = {
        "mode": "sync" if sync else "check", "records": len(records), "figures": len(figures),
        "updated": updated, "errors": list(dict.fromkeys(errors)),
        "limitations": ["检查登记项和引用覆盖, 不自动穷举任意自然语言实验断言", "只检查来源文件、Python 符号及双写一致性, 不重算科学结果", "人工删例、裁切和调版不要求与最初生成图逐字节一致"],
    }
    report_path = root / "temp/figure_provenance_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="检查图表完整追溯链, 或同步 Markdown 到 PPT 来源批注")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="只读检查; 默认模式")
    mode.add_argument("--sync", action="store_true", help="先预检, 再同步自有批注并保留写入前备份")
    parser.add_argument("--root", type=Path, default=REPOSITORY, help="论文仓库根目录")
    options = parser.parse_args()
    report = run(options.root, options.sync)
    state = "失败" if report["errors"] else "通过"
    print(f"追溯{report['mode']}: {state}; {report['records']} 条记录, {report['figures']} 张图, 更新 {len(report['updated'])} 个 PPT")
    for error in report["errors"][:12]:
        print(f"- {error}")
    if len(report["errors"]) > 12:
        print(f"- 另有 {len(report['errors']) - 12} 项, 见报告")
    print(f"报告: {(options.root.resolve() / 'temp/figure_provenance_report.json')}")
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
