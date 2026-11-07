"""运输本次从服务器原始构象生成的9WUP三个原生视图.

只复制可编辑路径、圆形与文字,不重新投影坐标或绘制病例.输入是本次计算得到的
临时原生病例PPT;目标页由主图绘制程序先生成.所选源对象不含媒体或外部关系,
因此可以保留它们的 OOXML,按一个等比例变换组成可解组的视图.
"""

from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EMU_PER_PT = 12700


from TOOLS.ppt.native_geometry import group_native_shapes


def inject_case_views(
    pptx_path,
    panel_rects_pt,
    source_path,
):
    """向现有 PPT 页加入原案例的 official、DG、Emap 三个原生视图.

    panel_rects_pt 是三个 [x, y, width, height],单位为 point,顺序固定.
    方法标题和指标随原对象复制;不添加 g/h/i,由主图统一编号.
    所有正文图形保留为组内可编辑的 PowerPoint 原生对象.函数原位更新
    pptx_path,仅替换目标页 XML,其他页、备注、批注及关系完全保留.
    """
    if len(panel_rects_pt) != 3:
        raise ValueError("9WUP 复用需要固定的三个目标矩形")
    pptx_path = Path(pptx_path)
    with ZipFile(source_path) as archive:
        source = etree.fromstring(archive.read("ppt/slides/slide1.xml"))
    source_tree = list(source.find("p:cSld/p:spTree", NS))
    with ZipFile(pptx_path) as archive:
        package = {entry.filename: archive.read(entry.filename) for entry in archive.infolist()}
    slide_part = "ppt/slides/slide1.xml"
    target = etree.fromstring(package[slide_part])
    target_tree = target.find("p:cSld/p:spTree", NS)
    if target_tree.xpath(".//p:cNvPr[starts-with(@name, '9WUP-reused/') ]", namespaces=NS):
        raise ValueError("目标页已包含 9WUP 原生组，禁止重复注入")
    next_id = max(int(n.get("id", "0")) for n in target.findall(".//p:cNvPr", NS)) + 1
    report = {"source_slide": 1, "native_objects": [], "scales": []}
    for column, (method, rect) in enumerate(zip(("official", "tuned", "build"), panel_rects_pt)):
        prefix = f"9wup_2_{method}_"
        indices = [
            i
            for i, shape in enumerate(source_tree)
            if shape.find(".//p:cNvPr", NS) is not None
            and shape.find(".//p:cNvPr", NS).get("name", "").startswith(prefix)
        ]
        selected = [deepcopy(source_tree[i]) for i in indices]
        # 每个方法的最后一个原子对象后紧接原作者的 RMSD/D/Clash 文本.
        metrics = deepcopy(source_tree[max(indices) + 1])
        if not " ".join(metrics.xpath(".//a:t/text()", namespaces=NS)).startswith("RMSD"):
            raise ValueError("作者 PPT 案例结构变化：指标文本不再紧接原视图")
        selected.append(metrics)
        source_x = (228600, 3200400, 6172200)[column]
        source_y, source_width, source_height = 7953375, 2790825, 1552575
        header = deepcopy(source_tree[2 + column])
        header.find(".//a:xfrm/a:off", NS).set("y", str(source_y - 279400))
        # 仅按术语表统一名称大小写,科学方法和已有图形均不变.
        for text in header.findall(".//a:t", NS):
            if text.text == "DG-PocketXmol":
                text.text = "DG-PocketXMol"
        selected.insert(0, header)
        source_y -= 279400
        source_width, source_height = 2857500, source_height + 279400
        group, next_id, ratio = group_native_shapes(
            selected,
            (source_x, source_y, source_width, source_height),
            rect,
            f"9WUP-reused/{method}",
            next_id,
        )
        target_tree.append(group)
        report["native_objects"].append(len(selected))
        report["scales"].append(ratio)
    package[slide_part] = etree.tostring(
        target, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    staged = pptx_path.with_name(pptx_path.stem + ".case-staging.pptx")
    with ZipFile(staged, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in package.items():
            archive.writestr(name, data)
    staged.replace(pptx_path)
    return report
