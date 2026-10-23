"""在作者第五页上局部修改原生图形, 仅生成待核查副本和装配报告."""

import os
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import json
import math
import subprocess
import sys

from lxml import etree as E

PROJECT = next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file() and (p/'论文草稿.md').is_file())
SOURCE = PROJECT/'画图/画图代码/e2e/output/fig-method-v8'
B = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else PROJECT/'temp/fig-method-v8'
B.mkdir(parents=True,exist_ok=True)
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


def element(tag, **attributes):
    prefix, local = tag.split(":")
    return E.Element(f"{{{NS[prefix]}}}{local}", {k: str(v) for k, v in attributes.items()})


def child(parent, tag, **attributes):
    node = element(tag, **attributes)
    parent.append(node)
    return node


def emu(value):
    return round(value * 12700)


with ZipFile(SOURCE / "disk-before.pptx") as package:
    contents = {name: package.read(name) for name in package.namelist()}

# 重渲染时把同一真实素材的新PNG嵌回作者基底；对象布局和坐标不变。
if "FIGURE_RENDER_ROOT" in os.environ:
    rendered = Path(os.environ["FIGURE_RENDER_ROOT"])
    for frozen, fresh in [(SOURCE / "receptor-9llg/receptor_final.png", rendered / "receptor-9llg/receptor_final.png"), (SOURCE / "build-pose-9bjj/9bjj_a.png", rendered / "build-pose-9bjj/9bjj_a.png")]:
        original_image = frozen.read_bytes()
        for name in contents:
            if name.startswith("ppt/media/") and contents[name] == original_image:
                contents[name] = fresh.read_bytes()
root = E.fromstring(contents["ppt/slides/slide5.xml"])
tree = root.find("p:cSld/p:spTree", NS)
next_id = max(int(x.get("id")) for x in root.findall(".//p:cNvPr", NS)) + 1
coordinates = {}


def index_shapes(container, sx=1, sy=1, tx=0, ty=0):
    # sx/sy 与 tx/ty 把组合内部 EMU 坐标映射到整页坐标, 不改变已有组合.
    for shape in container:
        kind = E.QName(shape).localname
        if kind not in ("sp", "grpSp", "pic", "cxnSp"):
            continue
        nv = shape.find(".//p:cNvPr", NS)
        coordinates[nv.get("id")] = (shape, sx, sy, tx, ty)
        if kind == "grpSp":
            xf = shape.find("p:grpSpPr/a:xfrm", NS)
            off, ext = xf.find("a:off", NS), xf.find("a:ext", NS)
            co, ce = xf.find("a:chOff", NS), xf.find("a:chExt", NS)
            gx, gy = int(ext.get("cx")) / int(ce.get("cx")), int(ext.get("cy")) / int(ce.get("cy"))
            index_shapes(shape, sx * gx, sy * gy, tx + sx * (int(off.get("x")) - gx * int(co.get("x"))), ty + sy * (int(off.get("y")) - gy * int(co.get("y"))))


index_shapes(tree)


def move_shape(identity, dx, dy):
    shape, sx, sy, _, _ = coordinates[str(identity)]
    path = "p:grpSpPr/a:xfrm/a:off" if E.QName(shape).localname == "grpSp" else "p:spPr/a:xfrm/a:off"
    off = shape.find(path, NS)
    off.set("x", str(int(off.get("x")) + round(emu(dx) / sx)))
    off.set("y", str(int(off.get("y")) + round(emu(dy) / sy)))


def remove_shape(identity):
    shape = coordinates[str(identity)][0]
    shape.getparent().remove(shape)


def new_shape(name, x, y, width, height, fill, stroke, line_width, geometry="custom", dashed=False, radius=0):
    global next_id
    shape = element("p:sp")
    nv = child(shape, "p:nvSpPr")
    child(nv, "p:cNvPr", id=next_id, name=name)
    next_id += 1
    child(nv, "p:cNvSpPr")
    child(nv, "p:nvPr")
    properties = child(shape, "p:spPr")
    xf = child(properties, "a:xfrm")
    child(xf, "a:off", x=emu(x), y=emu(y))
    child(xf, "a:ext", cx=max(1, emu(width)), cy=max(1, emu(height)))
    if geometry != "custom":
        geom = child(properties, "a:prstGeom", prst=geometry)
        adjustments = child(geom, "a:avLst")
        if geometry == "roundRect":
            child(adjustments, "a:gd", name="adj", fmla=f"val {round(radius / min(width, height) * 100000)}")
    else:
        geom = child(properties, "a:custGeom")
        for tag in ["avLst", "gdLst", "ahLst", "cxnLst"]:
            child(geom, "a:" + tag)
        child(geom, "a:rect", l="l", t="t", r="r", b="b")
        child(geom, "a:pathLst")
    if fill:
        child(child(properties, "a:solidFill"), "a:srgbClr", val=fill)
    else:
        child(properties, "a:noFill")
    line = child(properties, "a:ln", w=emu(line_width), cap="rnd")
    if stroke and line_width:
        child(child(line, "a:solidFill"), "a:srgbClr", val=stroke)
        child(line, "a:prstDash", val="dash" if dashed else "solid")
        child(line, "a:round")
    else:
        child(line, "a:noFill")
    tree.append(shape)
    return shape


def path_shape(name, commands, stroke, width, fill=None, dashed=False):
    points = [point for command, point_list in commands for point in point_list]
    left, top = min(p[0] for p in points), min(p[1] for p in points)
    w, h = max(p[0] for p in points) - left, max(p[1] for p in points) - top
    shape = new_shape(name, left, top, w, h, fill, stroke, width, dashed=dashed)
    path = child(shape.find("p:spPr/a:custGeom/a:pathLst", NS), "a:path", w=max(1, emu(w)), h=max(1, emu(h)))
    for command, point_list in commands:
        segment = child(path, "a:" + command)
        for px, py in point_list:
            child(segment, "a:pt", x=emu(px - left), y=emu(py - top))
    return shape


def polyline(name, points, color, width):
    return path_shape(name, [("moveTo", [points[0]])] + [("lnTo", [p]) for p in points[1:]], color, width)


def arrow(name, points, color, width, head_length, head_width):
    a, b = points[-2:]
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    c, s = math.cos(angle), math.sin(angle)
    stem = points[:-1] + [(b[0] - head_length * .45 * c, b[1] - head_length * .45 * s)]
    polyline(name, stem, color, width)
    p1 = (b[0] - head_length * c + head_width / 2 * s, b[1] - head_length * s - head_width / 2 * c)
    p2 = (b[0] - head_length * c - head_width / 2 * s, b[1] - head_length * s + head_width / 2 * c)
    path_shape(name + " head", [("moveTo", [b]), ("lnTo", [p1]), ("lnTo", [p2]), ("close", [])], None, 0, color)


def circle(name, x, y, diameter, fill, stroke, width):
    return new_shape(name, x - diameter / 2, y - diameter / 2, diameter, diameter, fill, stroke, width, "ellipse")


# 只替换需要改变的输入连线, 图内其余网络结构全部保留.
for identity in [1326, 1327, 1330, 1331, 1431, 1432, 1433, 1434]:
    remove_shape(identity)
purple, blue, muted = "9481B1", "4083B4", "71808C"
new_shape('V8 embedding computation frame', 96.8, 102.8, 30.4, 32.9, 'F8FAFC', 'C5BDD5', .48, 'roundRect', False, 2.0)
bar_x, bar_y, cell_w, bar_h = 112.3, 119.55, 1.55, 2.70
center_x, center_y = 109.8, 120.9
neighbors = [(100.3, 108.1), (117.6, 107.7), (123.2, 113.4), (100.1, 127.8), (109.0, 132.2)]
for index, (x, y) in enumerate(neighbors, 1):
    distance = math.hypot(center_x - x, center_y - y)
    ux, uy = (center_x - x) / distance, (center_y - y) / distance
    start = (x + ux * 1.55, y + uy * 1.55)
    end = (center_x - ux * 2.55, center_y - uy * 2.55)
    if index == 3:
        end = (111.2, 118.7)
        path_shape('V8 embedding upper curved aggregation', [('moveTo', [start]), ('cubicBezTo', [(122.0, 117.0), (116.0, 116.5), (112.5, 118.0)])], purple, .46)
        arrow('V8 embedding upper curved aggregation tip', [(112.5, 118.0), end], purple, .46, 1.55, 1.40)
    elif index == 4:
        end = (107.3, 120.0)
        path_shape('V8 embedding curved aggregation', [('moveTo', [start]), ('cubicBezTo', [(100.0, 120.7), (102.8, 118.4), (106.1, 119.4)])], purple, .70)
        arrow('V8 embedding curved aggregation tip', [(106.1, 119.4), end], purple, .70, 1.8, 1.65)
    else:
        arrow(f"V8 embedding neighbor {index} to center", [start, end], purple, .46, 1.55, 1.40)
    circle(f"V8 embedding neighbor {index}", x, y, [2.25, 2.45, 2.2, 2.5, 2.3][index - 1], None, '9481B1', .56)
circle("V8 embedding center", center_x, center_y, 3.5, None, "3B8C80", .78)
palette = ["3E8F9A", "88BEC3", "67AD9F", "B6D8CC", "3B8C80", "A3CDDA", "6CAFA4", "C4DDE0"]
for index, color in enumerate(palette):
    new_shape(f"V8 embedding feature {index + 1}", bar_x + index * cell_w, bar_y, cell_w - .10, bar_h, color, None, 0, "rect")
entry_y = 104.027
output_y = bar_y + bar_h / 2
polyline("V8 embedding shared output", [(bar_x + 8 * cell_w, output_y), (131.3, output_y)], purple, .67)
arrow("V8 embedding to point branch", [(131.3, entry_y), (137.294, entry_y)], purple, .67, 2.23, 1.92)
arrow("V8 embedding to voxel branch", [(131.3, output_y), (131.3, 51.695)], purple, .67, 2.23, 1.92)
arrow("V8 density and receptor to voxel", [(128.674, 51.695), (137.294, 51.695)], blue, .67, 2.23, 1.92)
circle("V8 voxel input junction", 131.3, 51.695, 1.25, blue, None, 0)

# 用一致圆角收拢阶梯转折, 横线只描一次, 避免共用边出现双线.
old_boundary, boundary_sx, boundary_sy, boundary_tx, boundary_ty = coordinates['6']
boundary_parent = old_boundary.getparent()
boundary_index = list(boundary_parent).index(old_boundary)
remove_shape(6)
x0, y0, x1, x2, split_y, bottom, radius = 41.745, 176.834, 114.615, 147.654, 217.879, 260.930, 2.5
commands = [
    ("moveTo", [(x0 + radius, y0)]), ("lnTo", [(x1 - radius, y0)]),
    ("cubicBezTo", [(x1 - .45 * radius, y0), (x1, y0 + .45 * radius), (x1, y0 + radius)]),
    ("lnTo", [(x1, split_y - radius)]),
    ("cubicBezTo", [(x1, split_y - .45 * radius), (x1 + .45 * radius, split_y), (x1 + radius, split_y)]),
    ("lnTo", [(x2 - radius, split_y)]),
    ("cubicBezTo", [(x2 - .45 * radius, split_y), (x2, split_y + .45 * radius), (x2, split_y + radius)]),
    ("lnTo", [(x2, bottom - radius)]),
    ("cubicBezTo", [(x2, bottom - .45 * radius), (x2 - .45 * radius, bottom), (x2 - radius, bottom)]),
    ("lnTo", [(x0 + radius, bottom)]),
    ("cubicBezTo", [(x0 + .45 * radius, bottom), (x0, bottom - .45 * radius), (x0, bottom - radius)]),
    ("lnTo", [(x0, y0 + radius)]),
    ("cubicBezTo", [(x0, y0 + .45 * radius), (x0 + .45 * radius, y0), (x0 + radius, y0)]), ("close", [])]
boundary = path_shape("V8 Match input boundary", commands, "B6CEC5", .574, "FFFFFF")
tree.remove(boundary)
boundary_xf = boundary.find('p:spPr/a:xfrm', NS)
boundary_off = boundary_xf.find('a:off', NS)
boundary_ext = boundary_xf.find('a:ext', NS)
boundary_off.set('x', str(round((int(boundary_off.get('x')) - boundary_tx) / boundary_sx)))
boundary_off.set('y', str(round((int(boundary_off.get('y')) - boundary_ty) / boundary_sy)))
boundary_ext.set('cx', str(round(int(boundary_ext.get('cx')) / boundary_sx)))
boundary_ext.set('cy', str(round(int(boundary_ext.get('cy')) / boundary_sy)))
boundary_parent.insert(boundary_index, boundary)
polyline("V8 Match input divider", [(x0, split_y), (x1 + radius, split_y)], "B6CEC5", .574)
for identity in range(1285, 1317):
    move_shape(identity, 0, 2.35)

# 给原有 Concat 标签留出真实字形间距, 只下移合流横线并缩短入 MLP 的箭头.
for identity, (shape, *_transform) in coordinates.items():
    name = shape.find('.//p:cNvPr', NS).get('name')
    if name in ['Pool concat refined', 'Attention concat refined', 'Concat to MLP refined', 'Concat to MLP refined head']:
        shape.getparent().remove(shape)
polyline('V8 pool to concat', [(65.7845, 283.714), (65.7845, 291.6), (93.806, 291.6)], '3B8C80', .67)
polyline('V8 attention to concat', [(121.8425, 283.714), (121.8425, 291.6), (93.806, 291.6)], '3B8C80', .67)
arrow('V8 concat to MLP', [(93.806, 291.6), (93.806, 294.35)], '3B8C80', .67, 2.23, 1.92)

# 保留作者收窄后的 Build 外框, 两个输入分组和两个主流程箭头按现有卡片居中.
new_shape("V8 Build site and identity frame", 371.2, 35.6, 45.0, 92.2, None, "9BB4C8", .55, "roundRect", True, 2.5)
new_shape("V8 Build pocket and density frame", 418.7, 35.6, 38.6, 92.2, None, "9BB4C8", .55, "roundRect", True, 2.5)
move_shape(954, -4.2, 0)
arrow("V8 Build inputs to docking", [(414.2, 132.0), (414.2, 142.3)], muted, 1.04, 3.05, 3.45)
arrow("V8 Build docking to pose", [(414.2, 254.9), (414.2, 265.2)], muted, 1.04, 3.05, 3.45)
coordinates["743"][0].find("p:spPr/a:solidFill/a:srgbClr", NS).set("val", "FFFFFF")
coordinates["744"][0].find("p:spPr/a:solidFill/a:srgbClr", NS).set("val", "3C9486")

notes = E.fromstring(contents["ppt/notesSlides/notesSlide5.xml"])
replacements = {
    "a，Find": "a，Find 将密度与受体信息编码为候选配体区域（blobs）及辅助特征。受体嵌入头为体素分支与点云分支提供原子表征。体素分支将软投影至网格的受体特征与密度通道拼接。体素分支和点云分支通过体素到点的特征融合及迭代回收连接。",
    "a, Find": "a, Find encodes density and receptor information to produce candidate ligand regions (blobs) and auxiliary features. The receptor embedding head supplies atom representations to both branches. The voxel input concatenates the density channels with receptor features softly scattered onto the voxel grid. Voxel-to-point fusion and recycling connect the voxel and point-cloud branches.",
}
for paragraph in notes.findall(".//a:p", NS):
    text = "".join(paragraph.xpath(".//a:t/text()", namespaces=NS))
    for prefix, replacement in replacements.items():
        if text.startswith(prefix):
            old_properties = paragraph.find("a:r/a:rPr", NS)
            for node in list(paragraph):
                if E.QName(node).localname not in ("pPr", "endParaRPr"):
                    paragraph.remove(node)
            run = element("a:r")
            if old_properties is not None:
                properties = deepcopy(old_properties)
                properties.attrib.pop("b", None)
                run.append(properties)
            child(run, "a:t").text = replacement
            end = paragraph.find("a:endParaRPr", NS)
            paragraph.insert(list(paragraph).index(end) if end is not None else len(paragraph), run)

updates = {
    "ppt/slides/slide5.xml": E.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True),
    "ppt/notesSlides/notesSlide5.xml": E.tostring(notes, xml_declaration=True, encoding="UTF-8", standalone=True),
}
with ZipFile(SOURCE / "disk-before.pptx") as source, ZipFile(B / "candidate_before_density.pptx", "w") as destination:
    for info in source.infolist():
        destination.writestr(info, updates.get(info.filename, contents[info.filename]))
subprocess.run([
    sys.executable, "-X", "utf8", "-B", str(Path(__file__).parent / "ops/replace_density.py"),
    "--input", str(B / "candidate_before_density.pptx"),
    "--output", str(B / "candidate.pptx"),
], check=True)
report = {"changed_parts": list(updates) + ["ppt/slides/_rels/slide5.xml.rels", "ppt/media/fig2_density_corresponding.png"], "new_native_shapes": next_id - max(int(x.get("id")) for x in E.fromstring(contents['ppt/slides/slide5.xml']).findall('.//p:cNvPr', NS)) - 1, "embedding_neighbors": 5, "highlight_row_one_based": 2, "highlight_column_one_based": 3, "Build_external_width_preserved": True, "pages_1_to_4_preserved": True, "final_density_case": "9LLG", "final_density_chain": "C1"}
(B / "assembly.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
