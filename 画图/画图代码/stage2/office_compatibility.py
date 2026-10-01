"""把 Artifact Tool 图集重新封装为本机 PowerPoint 可导出的 OOXML。"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import win32com.client
from PIL import Image


BUNDLED_PACKAGES = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages"
sys.path.insert(0, str(BUNDLED_PACKAGES))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "转换工具"))
from ppt_figures import read_ppt_figures  # noqa: E402


PAPER = Path(__file__).resolve().parents[3]
ARTIFACT_DECK = PAPER / "temp/stage2-deck-build/final/stage2_results_v3.pptx"
OFFICE_DECK = PAPER / "temp/stage2-deck-build/stage2_results_v3_office.pptx"
DELIVERY_DECK = PAPER / "画图/stage2结果图_v3.pptx"
IMAGE_ROOT = PAPER / "画图/formal/stage2"
IMAGES = (
    ("stage2-radar-pair", "stage2_radar_pair.png"),
    ("stage2-strongest-pair", "stage2_strongest_pair.png"),
)


def main() -> None:
    """保留既定图像、图名及页备注，只更换 PowerPoint 的文件封装。"""
    captions = read_ppt_figures(ARTIFACT_DECK)
    application = win32com.client.DispatchEx("PowerPoint.Application")
    deck = application.Presentations.Add(False)
    try:
        deck.PageSetup.SlideWidth = 960
        deck.PageSetup.SlideHeight = 850
        for page, (name, image_name) in enumerate(IMAGES, 1):
            slide = deck.Slides.Add(page, 12)  # 12 是 PowerPoint 的空白幻灯片版式。
            image_path = IMAGE_ROOT / image_name
            with Image.open(image_path) as source:
                image_width, image_height = source.size
            scale = min(940 / image_width, 830 / image_height)
            width, height = image_width * scale, image_height * scale
            slide.Shapes.AddPicture(
                str(image_path), False, True,
                (960 - width) / 2, (850 - height) / 2, width, height,
            )
            slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = captions[name][1]
            slide.Comments.Add(8, 8, "Manuscript figure", "MF", f"@@{name}")
            slide.Comments.Add(18, 18, "Manuscript figure", "MF", f"Source: {image_name}; data.json; plot_stage2_pairs.py")
        deck.SaveAs(str(OFFICE_DECK), 24)
    finally:
        deck.Close()
        application.Quit()
    shutil.copyfile(OFFICE_DECK, DELIVERY_DECK)
    print(DELIVERY_DECK)


if __name__ == "__main__":
    main()
