"""原样搬运作者 PPT 中 9WUP/FAD 的三个原生视图。

只复制可编辑路径、圆形与文字，不重新投影坐标或绘制病例。输入是已冻结的
完整作者 PPT；目标页由主图绘制程序先生成。所选源对象不含媒体或外部关系，
因此可以保留它们的 OOXML，按一个等比例变换组成可解组的视图。
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
FROZEN_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "output/stage2-stage3-results/sources/9WUP-case.pptx"
)


def _native_group(shapes, source_rect, target_rect_pt, name, first_id, scale=None):
    """保留子对象坐标，以组变换把源矩形等比例放入目标矩形。"""
    sx, sy, sw, sh = source_rect
    dx, dy, dw, dh = (float(v) * EMU_PER_PT for v in target_rect_pt)
    ratio = min(dw / sw, dh / sh) if scale is None else scale
    width, height = round(sw * ratio), round(sh * ratio)
    if width > dw + 1 or height > dh + 1:
        raise ValueError(f"{name} 的目标矩形不足以保持原视图比例")
    group = etree.Element(f"{{{NS['p']}}}grpSp")
    nv = etree.SubElement(group, f"{{{NS['p']}}}nvGrpSpPr")
    etree.SubElement(nv, f"{{{NS['p']}}}cNvPr", id=str(first_id), name=name)
    etree.SubElement(nv, f"{{{NS['p']}}}cNvGrpSpPr")
    etree.SubElement(nv, f"{{{NS['p']}}}nvPr")
    properties = etree.SubElement(group, f"{{{NS['p']}}}grpSpPr")
    transform = etree.SubElement(properties, f"{{{NS['a']}}}xfrm")
    for tag, attrs in (
        ("off", {"x": round(dx), "y": round(dy)}),
        ("ext", {"cx": width, "cy": height}),
        ("chOff", {"x": sx, "y": sy}),
        ("chExt", {"cx": sw, "cy": sh}),
    ):
        etree.SubElement(transform, f"{{{NS['a']}}}{tag}", **{k: str(v) for k, v in attrs.items()})
    next_id = first_id + 1
    for original in shapes:
        shape = deepcopy(original)
        if shape.xpath(".//@r:embed | .//@r:link | .//@r:id", namespaces=NS):
            raise ValueError("冻结案例对象含外部关系，不能作为无关系原生对象直接搬运")
        for nonvisual in shape.findall(".//p:cNvPr", NS):
            nonvisual.set("id", str(next_id))
            nonvisual.set("name", f"{name}/{nonvisual.get('name', '')}")
            next_id += 1
        # PowerPoint 的组变换缩放路径坐标，却不会同比缩小显式字号。
        # 同步字号才能让原指标和方法标题保持原来的占比与完整可读性。
        for run_properties in shape.xpath(".//a:*[@sz]", namespaces=NS):
            run_properties.set("sz", str(round(int(run_properties.get("sz")) * ratio)))
        group.append(shape)
    return group, next_id, ratio


def inject_case_views(
    pptx_path,
    panel_rects_pt,
    slide_number=1,
    include_headers=True,
    legend_rect_pt=None,
    scale_rect_pt=None,
):
    """向现有 PPT 页加入原案例的 official、DG、Emap 三个原生视图。

    panel_rects_pt 是三个 [x, y, width, height]，单位为 point，顺序固定。
    方法标题和指标随原对象复制；不添加 g/h/i，由主图统一编号。
    legend_rect_pt 可放原四项共用图例。scale_rect_pt 可放原 5 Å 比例尺，
    比例尺严格沿用视图的显示缩放，不能任意改变它代表的长度。
    所有正文图形保留为组内可编辑的 PowerPoint 原生对象。函数原位更新
    pptx_path，仅替换目标页 XML，其他页、备注、批注及关系完全保留。
    """
    if len(panel_rects_pt) != 3:
        raise ValueError("9WUP 复用需要固定的三个目标矩形")
    pptx_path = Path(pptx_path)
    with ZipFile(FROZEN_SOURCE) as archive:
        source = etree.fromstring(archive.read("ppt/slides/slide5.xml"))
    source_tree = list(source.find("p:cSld/p:spTree", NS))
    with ZipFile(pptx_path) as archive:
        package = {entry.filename: archive.read(entry.filename) for entry in archive.infolist()}
    slide_part = f"ppt/slides/slide{slide_number}.xml"
    target = etree.fromstring(package[slide_part])
    target_tree = target.find("p:cSld/p:spTree", NS)
    if target_tree.xpath(".//p:cNvPr[starts-with(@name, '9WUP-reused/') ]", namespaces=NS):
        raise ValueError("目标页已包含 9WUP 原生组，禁止重复注入")
    next_id = max(int(n.get("id", "0")) for n in target.findall(".//p:cNvPr", NS)) + 1
    report = {"source_slide": 5, "native_objects": [], "scales": []}
    for column, (method, rect) in enumerate(zip(("official", "tuned", "build"), panel_rects_pt)):
        prefix = f"9wup_2_{method}_"
        indices = [
            i for i, shape in enumerate(source_tree)
            if shape.find(".//p:cNvPr", NS) is not None
            and shape.find(".//p:cNvPr", NS).get("name", "").startswith(prefix)
        ]
        selected = [deepcopy(source_tree[i]) for i in indices]
        # 每个方法的最后一个原子对象后紧接原作者的 RMSD/D/Clash 文本。
        metrics = deepcopy(source_tree[max(indices) + 1])
        if not " ".join(metrics.xpath(".//a:t/text()", namespaces=NS)).startswith("RMSD"):
            raise ValueError("作者 PPT 案例结构变化：指标文本不再紧接原视图")
        selected.append(metrics)
        source_x = (228600, 3200400, 6172200)[column]
        source_y, source_width, source_height = 7953375, 2790825, 1552575
        if include_headers:
            header = deepcopy(source_tree[2 + column])
            header.find(".//a:xfrm/a:off", NS).set("y", str(source_y - 279400))
            # 仅按术语表统一名称大小写，科学方法和已有图形均不变。
            for text in header.findall(".//a:t", NS):
                if text.text == "DG-PocketXmol":
                    text.text = "DG-PocketXMol"
            selected.insert(0, header)
            source_y -= 279400
            source_width, source_height = 2857500, source_height + 279400
        group, next_id, ratio = _native_group(
            selected, (source_x, source_y, source_width, source_height),
            rect, f"9WUP-reused/{method}", next_id,
        )
        target_tree.append(group)
        report["native_objects"].append(len(selected))
        report["scales"].append(ratio)
    if legend_rect_pt is not None:
        # 页脚的四条颜色线和四个文本是原作者的完整共用图例。
        selected = [deepcopy(s) for s in source_tree[2527:2535]]
        group, next_id, ratio = _native_group(
            selected, (228600, 11582400, 9105900, 238125),
            legend_rect_pt, "9WUP-reused/shared-legend", next_id,
        )
        target_tree.append(group)
        report["legend_scale"] = ratio
    if scale_rect_pt is not None:
        selected = [deepcopy(source_tree[1517]), deepcopy(source_tree[1518])]
        # 5 Å 线长不可独立伸缩；其缩放必须和三个结构视图相同。
        if max(report["scales"]) - min(report["scales"]) > 1e-6:
            raise ValueError("三个视图缩放不同，无法共用同一 5 Å 比例尺")
        group, next_id, ratio = _native_group(
            selected, (8531866, 7705725, 783584, 209550), scale_rect_pt,
            "9WUP-reused/scale-5A", next_id, scale=report["scales"][0],
        )
        target_tree.append(group)
        report["scale_bar_scale"] = ratio
    package[slide_part] = etree.tostring(target, xml_declaration=True, encoding="UTF-8", standalone=True)
    staged = pptx_path.with_name(pptx_path.stem + ".case-staging.pptx")
    with ZipFile(staged, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in package.items():
            archive.writestr(name, data)
    staged.replace(pptx_path)
    return report
