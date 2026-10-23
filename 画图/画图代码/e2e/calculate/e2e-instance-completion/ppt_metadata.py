"""用 PowerPoint 原生文件接口添加唯一图标识并渲染当前候选稿.

本脚本只打开、保存并关闭本 temp 目录中的 candidate.pptx; 不关闭作者打开的文件.
"""

import os
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import win32com.client


def main():
    """添加 12 个 @@id 评论, 导出每页 PNG 与整套 PDF 供实际渲染验收.

    输入文件:
        - manifest.json: 每页 id 与双语图注, 页序与 candidate.pptx 一致.
        - candidate.pptx: artifact-tool 创建的 12 页原生形状.
    输出文件:
        - candidate.pptx: 仅增加唯一评论标识, 保留文字与几何对象.
        - ppt_preview/slide-*.png、candidate.pdf: PowerPoint 实际渲染的验收中间文件.
    """
    root = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
    build = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else root / "temp/e2e_completion_20261011"
    pages = json.loads((build / "manifest.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(build / "candidate.pptx") as package:
        names = set()
        for name in package.namelist():
            if "/comments/" in name and name.endswith(".xml"):
                for comment in ET.fromstring(package.read(name)):
                    value = "".join(comment.itertext()).strip()
                    if value.startswith("@@"):
                        names.add(value[2:])
    assert all(page["id"] in names for page in pages), "候选缺少构造器生成的独立@@图名"
    application = win32com.client.Dispatch("PowerPoint.Application")
    presentation = application.Presentations.Open(str(build / "candidate.pptx"), False, False, False)
    try:
        preview = build / "ppt_preview"
        preview.mkdir(exist_ok=True)
        for number, page in enumerate(pages, 1):
            slide = presentation.Slides(number)
            slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = page["notes"]
            slide.Export(str(preview / f"slide-{number:02d}.png"), "PNG", 1600, 1867)
        presentation.Save()
        presentation.SaveAs(str(build / "candidate.pdf"), 32)
    finally:
        presentation.Close()
    # PowerPoint 保存时会把页尺寸舍入为单精度 pt; 包内恢复最初批准的 180×210 mm.
    candidate = build / "candidate.pptx"
    with zipfile.ZipFile(candidate) as archive:
        members = {item.filename: archive.read(item.filename) for item in archive.infolist()}
    root = ET.fromstring(members["ppt/presentation.xml"])
    size = root.find("{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz")
    size.set("cx", "6480000")
    size.set("cy", "7560000")
    members["ppt/presentation.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(candidate, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)


if __name__ == "__main__":
    main()
