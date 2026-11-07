"""读取和局部修改PPT容器, 保留未修改的作者部件.

Deck按实际presentation关系定位完整图名、备注与批注, save只保存明确修改的ZIP部件.
来源批注的检查和同步入口位于TOOLS/figure_runner/provenance.py, 本模块不提供CLI.
"""

from __future__ import annotations

import copy
import posixpath
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
try:
    from lxml import etree as XML
except ImportError:
    # 优先采用当前 Python 的二进制扩展, 避免不同 Python 版本的本地依赖抢先遮蔽.
    if (REPOSITORY / "TOOLS/runtime/.manuscript_deps").is_dir():
        sys.path.insert(0, str(REPOSITORY / "TOOLS/runtime/.manuscript_deps"))
    for module_name in list(sys.modules):
        if module_name == "lxml" or module_name.startswith("lxml."):
            del sys.modules[module_name]
    from lxml import etree as XML


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
M = "http://schemas.microsoft.com/office/powerpoint/2018/8/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_R = "http://schemas.openxmlformats.org/package/2006/relationships"
FIGURE = re.compile(r"@@([^\s|{}]+)\Z")
XML_PARSER = XML.XMLParser(remove_blank_text=False, resolve_entities=False, no_network=True)


@dataclass
class Slide:
    """实际 presentation 关系中的幻灯片, 不用 slideN 文件名推断页码."""

    part: str
    page: int
    comments: list[str]
    names: list[str]


def xml_bytes(node) -> bytes:
    return XML.tostring(node, encoding="UTF-8", xml_declaration=True, standalone=True)


def relationship_target(part: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target).lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))




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
                    target.writestr(copy.copy(info), payload)
            if self.path.read_bytes() != self.original:
                raise ValueError(f"PPT 在打包期间被外部修改, 已保留作者文件: {self.path}")
            temporary_path.replace(self.path)
        finally:
            temporary_path.unlink(missing_ok=True)

