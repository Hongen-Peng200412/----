"""用本次原始匹配计数在最终0–105%坐标轴上构造曲线、标记和刻度."""

from copy import deepcopy
import uuid
from lxml import etree
from TOOLS.ppt.native_geometry import xfrm

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def rewrite_axis(root, data, receptor, start, frame_name, next_id):
    """用同一组真实准确率,把35–105范围改成0–105,标记尺寸保持."""
    # 作者对象名是显示定位标识, 科学值仍从本次data读取.
    shapes = {
        shape.find("p:nvSpPr/p:cNvPr", NS).get("name"): shape
        for shape in root.findall(".//p:sp", NS)
    }
    off, ext = xfrm(shapes[frame_name])
    top = int(off.get("y"))
    height = int(ext.get("cy"))

    def ordinate(value):
        """将本次真实百分数映射到本图0–105%轴的EMU纵坐标."""
        return round(top + height * (1 - value / 105))

    marker_checks = []
    for series, key in enumerate(["overall", "small", "metal", "sugar"]):
        line_number = start + 6 * series
        shape = shapes[f"results_{line_number}"]
        off, ext = xfrm(shape)
        path = shape.find("p:spPr/a:custGeom/a:pathLst/a:path", NS)
        points = path.findall(".//a:pt", NS)
        values = data["match"]["by_candidate_count"][receptor][key]["accuracy_pct"]
        if len(points) != 5:
            raise ValueError("作者折线对象结构变化，需要重新定位五个真实观测")
        ys = [ordinate(v) for v in values]
        low, high = min(ys), max(ys)
        off.set("y", str(low))
        ext.set("cy", str(high - low))
        path.set("h", str(high - low))
        for point, y in zip(points, ys):
            point.set("y", str(y - low))
        for i, (value, y) in enumerate(zip(values, ys), 1):
            marker = shapes[f"results_{line_number+i}"]
            mo, me = xfrm(marker)
            old_center = int(mo.get("y")) + int(me.get("cy")) / 2
            expected_old = top + height * (105 - value) / 70
            if abs(old_center - expected_old) > 800:
                raise ValueError("作者标记已移动，旧刻度与冻结数值不符")
            mo.set("y", str(round(y - int(me.get("cy")) / 2)))
            marker_checks.append({"category": key, "value": value, "new_y_emu": y})
    # 现有40/60/80/100网格及标签移动;新增0、20保持原字号、颜色和线宽.
    grid_start = start - 13
    for i, value in enumerate([40, 60, 80, 100]):
        for kind, number in [
            ("results", grid_start + 3 * i),
            ("results", grid_start + 3 * i + 1),
            ("text", grid_start + 3 * i + 2),
        ]:
            s = shapes[f"{kind}_{number}"]
            o, e = xfrm(s)
            if kind == "text":
                old_grid = int(xfrm(shapes[f"results_{grid_start+3*i}"])[0].get("y"))
                # 网格在此轮已移动,文字原有基线距网格2.419pt.
                o.set("y", str(ordinate(value) - round(2.4195 * 12700)))
            else:
                o.set("y", str(ordinate(value)))
    tree = root.find("p:cSld/p:spTree", NS)
    insertion = list(tree).index(shapes[f"results_{grid_start}"])
    for value in [0, 20]:
        for prefix, number in [
            ("results", grid_start),
            ("results", grid_start + 1),
            ("text", grid_start + 2),
        ]:
            s = deepcopy(shapes[f"{prefix}_{number}"])
            prop = s.find("p:nvSpPr/p:cNvPr", NS)
            prop.set("id", str(next_id))
            next_id += 1
            prop.set("name", f"v1-zero-{receptor}-{prefix}-{number}-{value}")
            for node in s.iter():
                if etree.QName(node).localname == "creationId":
                    node.set("id", "{" + str(uuid.uuid4()).upper() + "}")
            o, e = xfrm(s)
            o.set("y", str(ordinate(value) - (round(2.4195 * 12700) if prefix == "text" else 0)))
            if prefix == "text":
                texts = s.findall(".//a:t", NS)
                texts[0].text = str(value)
                for text in texts[1:]:
                    text.text = ""
                if value == 0:
                    for paragraph in s.findall(".//a:p", NS):
                        pp = paragraph.find("a:pPr", NS)
                        if pp is None:
                            pp = etree.Element("{" + NS["a"] + "}pPr")
                            paragraph.insert(0, pp)
                        pp.set("algn", "r")
            tree.insert(insertion, s)
            insertion += 1
    return next_id, marker_checks
