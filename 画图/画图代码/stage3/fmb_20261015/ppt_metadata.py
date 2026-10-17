"""用 PowerPoint 原生文件接口添加唯一图标识并渲染当前候选稿.

复用既有图集的批注写法, 只打开和关闭temp/fmb_20261015/candidate.pptx; 不关闭作者文件.
"""

import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import win32com.client


def main():
    """添加 3 个 @@id 评论, 导出每页 PNG 与整套 PDF 供实际渲染验收.

    输入文件:
        - manifest.json: 每页 id 与双语图注, 页序与 candidate.pptx 一致.
        - candidate.pptx: artifact-tool 创建的 3 页原生形状.
    输出文件:
        - candidate.pptx: 写入传统@@批注与双语备注, 恢复180×240 mm页尺寸, 保留原生文字与几何对象.
        - ppt_preview/slide-*.png、candidate.pdf: PowerPoint 实际渲染的验收中间文件.
    """
    build = Path(__file__).resolve().parents[4] / "temp/fmb_20261015"
    pages = json.loads((build / "manifest.json").read_text(encoding="utf-8"))
    application = win32com.client.Dispatch("PowerPoint.Application")
    presentation = application.Presentations.Open(str(build / "candidate.pptx"), False, False, False)
    try:
        preview = build / "ppt_preview"
        preview.mkdir(exist_ok=True)
        for number, page in enumerate(pages, 1):
            slide = presentation.Slides(number)
            slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = page["notes"]
            if slide.Comments.Count == 0:
                slide.Comments.Add(0, 0, "Codex", "C", "@@" + page["id"])
            slide.Export(str(preview / f"slide-{number:02d}.png"), "PNG", 1600, 2133)
        presentation.Save()
        presentation.SaveAs(str(build / "candidate.pdf"), 32)
    finally:
        presentation.Close()
    # PowerPoint 保存时会把页尺寸舍入为单精度 pt; 包内恢复最初批准的 180×240 mm.
    candidate = build / "candidate.pptx"
    with zipfile.ZipFile(candidate) as archive:
        members = {item.filename: archive.read(item.filename) for item in archive.infolist()}
    root = ET.fromstring(members["ppt/presentation.xml"])
    size = root.find("{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz")
    size.set("cx", "6480000")
    size.set("cy", "8640000")
    members["ppt/presentation.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(candidate, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)


if __name__ == "__main__":
    main()
