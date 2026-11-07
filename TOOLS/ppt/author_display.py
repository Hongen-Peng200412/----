"""将作者原生显示设计源码构造成单页可编辑PPT.

入口build_display(source,build)读取drawing.xml和仅含本图依赖的Office容器. 只生成本次temp中的candidate.pptx与设计说明, 不计算科学数据.
"""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from lxml import etree as E

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").is_file())
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def build_display(source: Path, build: Path):
    """按图名构造当前作者设计的单页原生PPT, 包括既有示意媒体和双语图注."""
    metadata = json.loads((source / "design.json").read_text(encoding="utf-8"))
    build = build.resolve()
    if not build.is_relative_to(ROOT / "temp"):
        raise ValueError("构建目录必须位于项目temp")
    build.mkdir(parents=True, exist_ok=True)
    package = {
        p.relative_to(source / "package").as_posix(): p.read_bytes()
        for p in (source / "package").rglob("*")
        if p.is_file()
    }
    slide = E.fromstring(package[metadata["page_part"]])
    tree = slide.find("p:cSld/p:spTree", NS)
    tree.getparent().replace(tree, E.parse(str(source / "drawing.xml")).getroot())
    package[metadata["page_part"]] = E.tostring(
        slide, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    with ZipFile(build / "candidate.pptx", "w", ZIP_DEFLATED) as archive:
        for name, raw in package.items():
            archive.writestr(name, raw)
    (build / "design_receipt.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return build / "candidate.pptx"


def extract_design(pptx: Path, figure: str, destination: Path):
    """只读提取指定完整图名的一页DrawingML及Office关系闭包.

    pptx: Path, 作者正式图集. figure: str, 唯一@@标识. destination: Path, 调用方指定的新设计目录. 只保留本页和关系所需主题、备注、批注、媒体; 不复制其他页或无关系预览. 返回design.json的显示元数据, 不解析科学数据.
    """
    import hashlib
    import posixpath
    from TOOLS.ppt.deck import Deck, relationship_target

    deck = Deck(pptx)
    selected = deck.figures[figure]
    package = dict(deck.data)
    presentation = E.fromstring(package["ppt/presentation.xml"])
    relations = E.fromstring(package["ppt/_rels/presentation.xml.rels"])
    office_r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    keep_id = next(
        node.get("Id")
        for node in relations
        if node.get("Type").endswith("/slide")
        and relationship_target("ppt/presentation.xml", node.get("Target")) == selected.part
    )
    for node in list(presentation.find("p:sldIdLst", NS)):
        if node.get("{" + office_r + "}id") != keep_id:
            node.getparent().remove(node)
    for node in list(relations):
        if node.get("Type").endswith("/slide") and node.get("Id") != keep_id:
            relations.remove(node)
    package["ppt/presentation.xml"] = E.tostring(
        presentation, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    package["ppt/_rels/presentation.xml.rels"] = E.tostring(
        relations, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    root_rel = E.fromstring(package["_rels/.rels"])
    for node in list(root_rel):
        if node.get("Type").endswith("/thumbnail"):
            root_rel.remove(node)
    package["_rels/.rels"] = E.tostring(
        root_rel, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    needed = set()
    pending = ["_rels/.rels"]
    while pending:
        part = pending.pop()
        if part in needed:
            continue
        needed.add(part)
        directory, filename = posixpath.split(part)
        rel_part = posixpath.join(directory, "_rels", filename + ".rels")
        if rel_part in package and rel_part not in needed:
            pending.append(rel_part)
        if part.endswith(".rels"):
            source = (
                ""
                if part == "_rels/.rels"
                else posixpath.join(posixpath.dirname(directory), filename[:-5])
            )
            for relation in E.fromstring(package[part]):
                if relation.get("TargetMode") != "External":
                    target = relationship_target(source, relation.get("Target"))
                    if target not in package:
                        raise ValueError("Office依赖缺失: " + target)
                    pending.append(target)
    types = E.fromstring(package["[Content_Types].xml"])
    for node in list(types):
        if E.QName(node).localname == "Override" and node.get("PartName").lstrip("/") not in needed:
            types.remove(node)
    package["[Content_Types].xml"] = E.tostring(
        types, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    needed.add("[Content_Types].xml")
    destination.mkdir(parents=True, exist_ok=False)
    for part in sorted(needed):
        target = destination / "package" / part
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(package[part])
    slide = E.fromstring(package[selected.part])
    tree = slide.find("p:cSld/p:spTree", NS)
    (destination / "drawing.xml").write_bytes(
        E.tostring(tree, encoding="UTF-8", xml_declaration=True)
    )
    metadata = dict(
        figure=figure,
        page_part=selected.part,
        source_page=selected.page,
        author_design_origin=str(pptx) + " @@" + figure,
        source_pptx_sha256=hashlib.sha256(deck.original).hexdigest(),
        role="当前作者采用的单页显示定义及必要媒体, 不承担科学真值职责",
        package_files=len(needed),
        native_objects=len(tree) - 2,
        native_sessions=[],
    )
    (destination / "design.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadata
