"""以冻结作者v1为排版原件，局部运输a图横向加宽后的科学几何。

先运行prepare_data和plot_main --author-v1，再调用本入口生成单页candidate.pptx、
原生PDF及默认裁边PNG。仅允许登记的a图对象改变x，五条曲线另改变横向尺寸；
全部文字、纵坐标、字号、样式及b/c/d对象保留。--publish仅从已核验rebuilt.pptx
更新正式v1页和其来源批注，不替换整份图集；并发保存会中止发布。
"""

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
FROZEN = ROOT / "画图/画图代码/e2e/output/e2e-top5-revision/author-v1"
sys.path.insert(0, str(ROOT / "转换工具/ops"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from figure_provenance import Deck, relationship_target, xml_bytes
from build_pptx import build_editable_candidate

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def shape_points(shape):
    """将自定义线条的局部路径展开为EMU页面坐标，供重绘科学曲线逐点比对。"""
    x = shape.find("p:spPr/a:xfrm", NS)
    off, ext = x.find("a:off", NS), x.find("a:ext", NS)
    points = []
    for path in shape.findall("p:spPr/a:custGeom/a:pathLst/a:path", NS):
        width, height = int(path.get("w")), int(path.get("h"))
        for point in path.findall(".//a:pt", NS):
            points.append((int(off.get("x")) + int(point.get("x")) * int(ext.get("cx")) / width,
                           int(off.get("y")) + int(point.get("y")) * int(ext.get("cy")) / height))
    return points


def build_v1(build):
    """从本次科学重绘和作者冻结原件生成局部候选；清单外差异阻止输出。"""
    config = json.loads((FROZEN / "layout.json").read_text(encoding="utf-8"))
    author = Deck(FROZEN / config["source_pptx"])
    assert hashlib.sha256(author.original).hexdigest() == config["source_sha256"]
    slide = author.figures[config["figure"]]
    rel = slide.part.rsplit("/", 1)[0] + "/_rels/" + slide.part.rsplit("/", 1)[1] + ".rels"
    note_rel = next(r for r in author.tree(rel) if r.get("Type").endswith("/notesSlide"))
    note = author.tree(relationship_target(slide.part, note_rel.get("Target")))
    body = note.xpath('//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody', namespaces=NS)[0]
    notes = "\n".join("".join(p.xpath(".//a:t/text()", namespaces=NS)) for p in body.findall("a:p", NS))

    # 本次重绘先运输为原生参考，只取其科学曲线作逐点核对，不恢复旧标题或布局。
    geometry = json.loads((build / "figures/e2e-v1-baseline.geometry.json").read_text(encoding="utf-8"))
    manifest = [{"id": "e2e-main-top5", "stem": "e2e-v1-baseline", "width": geometry["width_mm"] / 25.4 * 72,
                 "height": geometry["height_mm"] / 25.4 * 72, "notes": notes}]
    (build / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    build_editable_candidate(build)
    os.replace(build / "candidate.pptx", build / "reference-native.pptx")
    reference = Deck(build / "reference-native.pptx")
    reference_tree = reference.tree(reference.figures["e2e-main-top5"].part)
    ref_shapes = {s.find("p:nvSpPr/p:cNvPr", NS).get("id"): s for s in reference_tree.findall("p:cSld/p:spTree/p:sp", NS)}

    tree = copy.deepcopy(author.tree(slide.part))
    shapes = {s.find("p:nvSpPr/p:cNvPr", NS).get("id"): s for s in tree.findall("p:cSld/p:spTree/p:sp", NS)}
    assert len(shapes) == config["expected_shape_count"] and not tree.findall(".//p:grpSp", NS)
    before = {key: E.tostring(value, method="c14n", exclusive=True) for key, value in shapes.items()}
    left, width, scale = config["a_left_emu"], config["a_width_emu"], config["x_stretch"]
    changes = {}
    curve_ids = set(config["curve_panels"])
    point_ids = set(map(str, config["errorbar_ids"] + config["data_marker_ids"]))
    allowed = curve_ids | point_ids | set(config["x_ticks"]) | set(map(str, config["reference_and_note_ids"] + config["percentage_ids"]))
    for key in allowed:
        shape = shapes[key]
        transform = shape.find("p:spPr/a:xfrm", NS)
        off, ext = transform.find("a:off", NS), transform.find("a:ext", NS)
        old_x, old_w = int(off.get("x")), int(ext.get("cx"))
        if key in curve_ids:
            off.set("x", str(round(left + (old_x - left) * scale)))
            ext.set("cx", str(round(old_w * scale)))
        else:
            if key in point_ids:
                centre = old_x + old_w / 2
                budget = min((50, 100, 200, 300), key=lambda b: abs(centre - left - width * b / 400))
            elif key in config["x_ticks"]:
                budget = config["x_ticks"][key]
            else:
                budget = 100 if int(key) in config["reference_and_note_ids"] else 300
            # 圆点、帽宽、刻度字宽及作者注记留白不拉伸，只移动相应预算位置。
            off.set("x", str(old_x + round(width * budget / 400 * (scale - 1))))
        if E.tostring(shape, method="c14n", exclusive=True) != before[key]:
            changes[key] = {"x_before": old_x, "x_after": int(off.get("x")), "width_before": old_w, "width_after": int(ext.get("cx"))}
        restored = copy.deepcopy(shape)
        restored.find("p:spPr/a:xfrm/a:off", NS).set("x", str(old_x))
        restored.find("p:spPr/a:xfrm/a:ext", NS).set("cx", str(old_w))
        assert E.tostring(restored, method="c14n", exclusive=True) == before[key], key
    assert all(E.tostring(shape, method="c14n", exclusive=True) == before[key] for key, shape in shapes.items() if key not in allowed)

    # 以预算0及绘图区底边为运输锚点，核对每条曲线的所有科学路径点。
    ref_axis = ref_shapes["11"].find("p:spPr/a:xfrm/a:off", NS)
    current_axis = shapes["11"].find("p:spPr/a:xfrm/a:off", NS)
    ref_left = int(ref_axis.get("x"))
    dy = int(current_axis.get("y")) - int(ref_axis.get("y"))
    curve_checks = []
    for key, panel in config["curve_panels"].items():
        got, expected = shape_points(shapes[key]), shape_points(ref_shapes[key])
        assert len(got) == len(expected), panel
        error = max(max(abs(a[0] - (left + (b[0] - ref_left) * scale)), abs(a[1] - b[1] - dy)) for a, b in zip(got, expected))
        assert error < 75, (panel, error)  # <0.0021mm，覆盖PPT整数EMU与SVG小数的运输舍入。
        curve_checks.append({"panel": panel, "points": len(got), "maximum_error_emu": error})

    # 单页候选保留作者主题、备注和对象树；未引用包部件不参与页面显示。
    data = dict(author.data)
    presentation = copy.deepcopy(author.tree("ppt/presentation.xml"))
    ids = presentation.find("p:sldIdLst", NS)
    selected = ids[slide.page - 1]
    for element in list(ids):
        if element is not selected:
            ids.remove(element)
    data["ppt/presentation.xml"] = xml_bytes(presentation)
    data[slide.part] = xml_bytes(tree)
    candidate = build / "candidate.pptx"
    with ZipFile(candidate, "w", ZIP_DEFLATED) as output:
        for name, value in data.items():
            output.writestr(name, value)
    report = {"source_sha256": config["source_sha256"], "x_stretch": scale, "changed_shapes": changes,
              "unchanged_shapes": len(shapes) - len(changes), "only_x_and_curve_width_changed": True, "scientific_curve_checks": curve_checks}
    (build / "v1-preservation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Author v1 candidate: ", len(changes), "horizontal updates;", report["unchanged_shapes"], "objects unchanged")


def publish_v1(build):
    """仅发布v1页面与来源批注；原图、图注、其他页及PPT包部件逐字节保留。"""
    config = json.loads((FROZEN / "layout.json").read_text(encoding="utf-8"))
    target = ROOT / "画图/E2E结果.pptx"
    current = Deck(target)
    assert hashlib.sha256(current.original).hexdigest() == config["source_sha256"], "作者另有保存，停止覆盖"
    candidate = Deck(build / "rebuilt.pptx")
    old_page, new_page = current.figures[config["figure"]], candidate.figures[config["figure"]]
    assert old_page.part == new_page.part and old_page.comments == new_page.comments
    data = dict(current.data)
    changed = [old_page.part, *old_page.comments]
    for name in changed:
        data[name] = candidate.data[name]
    staged = build / "publish-ready.pptx"
    with ZipFile(staged, "w", ZIP_DEFLATED) as output:
        for name, value in data.items():
            output.writestr(name, value)
    assert target.read_bytes() == current.original, "发布前作者再次保存，停止覆盖"
    os.replace(staged, target)
    (build / "publication.json").write_text(json.dumps({"changed_parts": changed, "preserved_parts": len(data) - len(changed)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Published only author v1 slide and provenance")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="保留作者v1的局部横向加宽运输")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--build-root", type=Path)
    args = parser.parse_args()
    build = args.build_root.resolve() if args.build_root else Path(os.environ["FIGURE_BUILD_ROOT"])
    if args.publish:
        publish_v1(build)
    else:
        build_v1(build)
