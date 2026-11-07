"""按调用方提供的OOXML显示定义应用作者排版, 不选择科学对象或实验.

apply_display_transforms修改平移、尺寸和文字格式; append_display_objects追加原生显示对象并重编号. 对象名称、排除对象集合和文字内容全部由Figure调用者提供.
"""

from lxml import etree as E
from copy import copy
from zipfile import ZipFile

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def apply_display_transforms(slide, definition, excluded_names):
    """应用明确显示补丁, excluded_names仅跳过几何变换, 保留文字处理.

    slide: lxml元素, 一张幻灯片. definition: dict, changes以原生对象名索引, translate_emu为二维EMU位移, ext/chOff/chExt为OOXML属性, text_format_xml为完整txBody. excluded_names: set[str], 由调用者声明需另行重算的对象名.
    """
    tree = slide.find("p:cSld/p:spTree", NS)
    for shape in list(tree):
        prop = shape.find("p:nvGrpSpPr/p:cNvPr", NS)
        if prop is not None and prop.get("name") in definition["remove"]:
            tree.remove(shape)
    aliases = {value: key for key, value in definition["rename"].items()}
    for shape in list(slide.findall(".//p:sp", NS)):
        prop = shape.find("p:nvSpPr/p:cNvPr", NS)
        name = aliases.get(prop.get("name"), prop.get("name"))
        prop.set("name", name)
        if name in definition["remove"]:
            shape.getparent().remove(shape)
            continue
        change = definition["changes"].get(name, {})
        xf = shape.find("p:spPr/a:xfrm", NS)
        if xf is not None and name not in excluded_names:
            if "translate_emu" in change:
                off = xf.find("a:off", NS)
                for axis, delta in zip(["x", "y"], change["translate_emu"]):
                    off.set(axis, str(int(off.get(axis)) + delta))
            for kind in ["ext", "chOff", "chExt"]:
                if kind in change:
                    node = xf.find("a:" + kind, NS)
                    if node is not None:
                        node.attrib.update(change[kind])
        if "text_format_xml" in change:
            old = shape.find("p:txBody", NS)
            texts = [text.text or "" for text in old.findall(".//a:t", NS)]
            fresh = E.fromstring(change["text_format_xml"].encode())
            if not change.get("literal_text"):
                for i, text in enumerate(fresh.findall(".//a:t", NS)):
                    text.text = "".join(texts) if i == 0 else ""
            shape.replace(old, fresh)
        if "text" in change:
            for i, text in enumerate(shape.findall(".//a:t", NS)):
                text.text = change["text"] if i == 0 else ""
    for group in slide.findall(".//p:grpSp", NS):
        name = group.find("p:nvGrpSpPr/p:cNvPr", NS).get("name")
        change = definition["changes"].get(name, {})
        xf = group.find("p:grpSpPr/a:xfrm", NS)
        if "translate_emu" in change:
            off = xf.find("a:off", NS)
            for axis, delta in zip(["x", "y"], change["translate_emu"]):
                off.set(axis, str(int(off.get(axis)) + delta))
        for kind in ["ext", "chOff", "chExt"]:
            if kind in change:
                xf.find("a:" + kind, NS).attrib.update(change[kind])


def append_display_objects(slide, xml_strings):
    """按输入顺序追加显示对象并重编号, 保留调用者已重算的路径与文字.

    slide: lxml元素, 目标幻灯片. xml_strings: list[str], 调用方提供的完整原生对象XML; 不含科学字段解析或输入文件地址.
    """
    tree = slide.find("p:cSld/p:spTree", NS)
    for raw in xml_strings:
        tree.append(E.fromstring(raw.encode()))
    for i, node in enumerate(slide.findall(".//p:cNvPr", NS), 1):
        node.set("id", str(i))


def patch_presentation(pptx, definition, excluded_names, finalize=None):
    """给单页候选应用显示事务, 完整保留其他部件原字节与ZIP条目信息.

    pptx: Path, 本次生成的单页候选. definition/excluded_names见apply_display_transforms. finalize: callable或None, 若调用者需在追加作者对象前重算本图对象, 接收slide元素并原位处理; 本工具不解释其科学数据.
    """
    with ZipFile(pptx) as archive:
        entries = [(copy(info), archive.read(info)) for info in archive.infolist()]
        comment = archive.comment
    raw = next(payload for info, payload in entries if info.filename == "ppt/slides/slide1.xml")
    slide = E.fromstring(raw)
    apply_display_transforms(slide, definition, excluded_names)
    if finalize is not None:
        finalize(slide)
    append_display_objects(slide, definition["design_additions_xml"])
    replacement = E.tostring(slide, encoding="UTF-8", xml_declaration=True, standalone=True)
    staged = pptx.with_name(pptx.stem + ".display-staging.pptx")
    with ZipFile(staged, "w") as archive:
        archive.comment = comment
        for info, payload in entries:
            archive.writestr(
                copy(info), replacement if info.filename == "ppt/slides/slide1.xml" else payload
            )
    staged.replace(pptx)
