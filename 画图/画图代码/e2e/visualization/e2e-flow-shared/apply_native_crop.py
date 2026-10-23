"""将装配记录的显示裁切写入 PPT 原生 srcRect, 保留全部原始 PNG/SVG 媒体字节.

可用 --build-root 指定独立构建目录; 默认读取论文仓库 temp/e2e_flow_v2_20261003. build_deck.mjs 在导出临时 candidate.pptx 后、结构验收前调用本脚本.
temp/e2e_flow_v2_20261003/deck_manifest.json 是逐页数组, panels 按三维图片插入顺序保存 key(视图名)、crop_bbox_px([left,top,right,bottom], 1440×1080 源像素)、source_path(源 PNG)和 rectangle_px(画布占位).
本脚本只替换对应 slideN.xml 的 srcRect 与图片名称/说明; 对应页的中间 SVG 身份图片及包内媒体、备注和关系文件不变.
原生 srcRect 的四个值以十万分比记录源图被移除的左、上、右、下边缘; PPT 内可取消裁切.
"""

import json
import argparse
from pathlib import Path
import zipfile

from lxml import etree


project = next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file() and (p/'论文草稿.md').is_file())
parser = argparse.ArgumentParser(description="给临时PPT应用冻结记录中的原生非破坏裁切")
parser.add_argument("--build-root", type=Path, default=project / "temp/e2e_flow_v2_20261003")
temporary = parser.parse_args().build_root
presentation_path = temporary / "candidate.pptx"
deck = json.loads((temporary / "deck_manifest.json").read_text(encoding="utf-8"))
namespaces = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
# 原 ZipInfo/媒体字节保留, 仅通过下方 replacements 替换每页 XML 的显示属性.
with zipfile.ZipFile(presentation_path) as archive:
    members = [(item, archive.read(item.filename)) for item in archive.infolist()]
replacements = {}
for number, case in enumerate(deck, 1):
    slide_name = f"ppt/slides/slide{number}.xml"
    slide = etree.fromstring(next(data for item, data in members if item.filename == slide_name))
    pictures = slide.findall(".//p:pic", namespaces)
    panels = case["panels"]
    # 图片顺序为输入/Find PNG、Match SVG、末尾三个 Build PNG, 与 build_deck.mjs 的插入循环一致.
    assert len(pictures) == len(panels) + len(case["identities"]), case["pdb"]
    scientific_pictures = pictures[:len(panels) - 3] + pictures[-3:]
    for picture, panel in zip(scientific_pictures, panels):
        left, top, right, bottom = panel["crop_bbox_px"]
        # 四个百分比对应源图移除边缘; 源轴 x/y 为 PNG 屏幕坐标, 不参与任何原子世界坐标计算.
        insets = {"l": left / 1440, "t": top / 1080, "r": (1440 - right) / 1440, "b": (1080 - bottom) / 1080}
        fill = picture.find("p:blipFill", namespaces)
        crop = fill.find("a:srcRect", namespaces)
        if crop is None:
            crop = etree.Element(f"{{{namespaces['a']}}}srcRect")
            fill.insert(1, crop)
        crop.attrib.clear()
        for edge, fraction in insets.items():
            crop.set(edge, str(round(fraction * 100000)))
        properties = picture.find("p:nvPicPr/p:cNvPr", namespaces)
        properties.set("name", panel["key"])
        properties.set("descr", f"{case['pdb'].upper()} {panel['key']}; native ChimeraX; source {panel['source_path']}; editable crop only")
    replacements[slide_name] = etree.tostring(slide, encoding="UTF-8", xml_declaration=True, standalone=True)
with zipfile.ZipFile(presentation_path, "w") as archive:
    for item, data in members:
        archive.writestr(item, replacements.get(item.filename, data))
print(f"Native non-destructive crop applied to {len(deck)} pages.")
