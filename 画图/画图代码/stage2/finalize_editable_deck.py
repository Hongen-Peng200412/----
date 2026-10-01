"""给两页原生 PowerPoint 图形补充图名批注, 供 Markdown→Word 转换器定位图页。"""

from __future__ import annotations

from pathlib import Path

import win32com.client


PAPER = Path(__file__).resolve().parents[3]
SOURCE = PAPER / "temp/stage2-deck-build/stage2_editable_powerpoint_v6.pptx"
OUTPUT = PAPER / "画图/stage2结果图_v6_可编辑.pptx"
FIGURE_NAMES = ("stage2-radar-pair", "stage2-strongest-pair")


def main() -> None:
    """以 PowerPoint 打开原生组件图集, 给两页加入转换器识别的图名批注, 再另存为交付文件。"""
    application = win32com.client.DispatchEx("PowerPoint.Application")
    deck = application.Presentations.Open(str(SOURCE), False, False, False)
    try:
        for page, name in enumerate(FIGURE_NAMES, 1):
            deck.Slides(page).Comments.Add(8, 8, "Manuscript figure", "MF", f"@@{name}")
        deck.SaveAs(str(OUTPUT), 24)
    finally:
        deck.Close()
        application.Quit()
    print(OUTPUT)


if __name__ == "__main__":
    main()
