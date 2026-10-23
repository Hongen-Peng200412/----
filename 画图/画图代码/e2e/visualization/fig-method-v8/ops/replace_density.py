"""把冻结的9LLG实验密度嵌入方法图候选；不发布正式PPT或Word。"""

from pathlib import Path
from zipfile import ZipFile
import argparse
import os
import json

from lxml import etree as E
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--input", type=Path, required=True, help="密度替换前的候选PPT")
parser.add_argument("--output", type=Path, required=True, help="temp或output/regenerated内的新候选")
args = parser.parse_args()
source_path, target_path = args.input.resolve(), args.output.resolve()
assert source_path != (ROOT / "画图/Method总图.pptx").resolve(), "仅操作构建候选，不读取正式图集作为待改写输入。"
assert source_path != target_path, "替换前后候选分别保留。"
assert target_path.is_relative_to(ROOT / "temp") or (
    target_path.is_relative_to(ROOT / "画图/画图代码/e2e/output/fig-method-v8/regenerated")
), "候选必须写入temp或本图regenerated。"
target_path.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(source_path) as source:
    infos = source.infolist()
    contents = {name: source.read(name) for name in source.namelist()}

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
root = E.fromstring(contents["ppt/slides/slide5.xml"])
rels = E.fromstring(contents["ppt/slides/_rels/slide5.xml.rels"])
image_path = Path(os.environ["FIGURE_RENDER_ROOT"]) / "density_corresponding_cropped.png" if "FIGURE_RENDER_ROOT" in os.environ else ROOT / "画图/画图代码/e2e/output/fig-method-v8/late-density-20261022/density_corresponding_cropped.png"
with Image.open(image_path) as image:
    ratio = image.width / image.height

new_shapes = []
for identity, name, cx, cy, maxw, maxh in [
    ("15", "Find corresponding experimental density", 65.784, 53.55, 39.5, 39.5),
    ("306", "Match corresponding experimental density", 96.927, 200.55, 27.4, 26.4),
    ("967", "Build corresponding experimental density", 437.83, 99.55, 29.8, 27.2),
]:
    old = root.xpath('//p:cNvPr[@id="' + identity + '"]', namespaces=NS)[0].getparent().getparent()
    parent, index = old.getparent(), list(old.getparent()).index(old)
    h = min(maxh, maxw / ratio)
    w = h * ratio
    pic = E.Element("{" + NS["p"] + "}pic")
    nv = E.SubElement(pic, "{" + NS["p"] + "}nvPicPr")
    E.SubElement(nv, "{" + NS["p"] + "}cNvPr", id=identity, name=name, descr="Experimental 9LLG density around chain C1 of the displayed CryoAtom2 receptor, at the original contour level and the identical camera orientation.")
    E.SubElement(nv, "{" + NS["p"] + "}cNvPicPr")
    E.SubElement(nv, "{" + NS["p"] + "}nvPr")
    fill = E.SubElement(pic, "{" + NS["p"] + "}blipFill")
    E.SubElement(fill, "{" + NS["a"] + "}blip", {"{" + NS["r"] + "}embed": "rIdDensityC1"})
    E.SubElement(E.SubElement(fill, "{" + NS["a"] + "}stretch"), "{" + NS["a"] + "}fillRect")
    properties = E.SubElement(pic, "{" + NS["p"] + "}spPr")
    xf = E.SubElement(properties, "{" + NS["a"] + "}xfrm")
    E.SubElement(xf, "{" + NS["a"] + "}off", x=str(round((cx - w / 2) * 12700)), y=str(round((cy - h / 2) * 12700)))
    E.SubElement(xf, "{" + NS["a"] + "}ext", cx=str(round(w * 12700)), cy=str(round(h * 12700)))
    E.SubElement(E.SubElement(properties, "{" + NS["a"] + "}prstGeom", prst="rect"), "{" + NS["a"] + "}avLst")
    parent.remove(old)
    parent.insert(index, pic)
    new_shapes.append({"name": name, "bbox_pt": [cx - w / 2, cy - h / 2, w, h]})

assert not any(rel.get("Id") == "rIdDensityC1" for rel in rels), "输入须为密度替换前候选。"
E.SubElement(rels, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship", Id="rIdDensityC1", Type=NS["r"] + "/image", Target="../media/fig2_density_corresponding.png")
updates = {
    "ppt/slides/slide5.xml": E.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True),
    "ppt/slides/_rels/slide5.xml.rels": E.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True),
    "ppt/media/fig2_density_corresponding.png": image_path.read_bytes(),
}
with ZipFile(target_path, "w") as destination:
    for info in infos:
        destination.writestr(info, updates.get(info.filename, contents[info.filename]))
    destination.writestr("ppt/media/fig2_density_corresponding.png", updates["ppt/media/fig2_density_corresponding.png"])
report = {"case": "9LLG", "chain": "C1", "same_experimental_map_and_camera": True, "shapes": new_shapes, "changed_parts": list(updates), "source": str(image_path.relative_to(ROOT)).replace("\\", "/")}
(target_path.parent / "density_assembly.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
