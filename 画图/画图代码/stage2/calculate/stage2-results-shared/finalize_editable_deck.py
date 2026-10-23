"""给两页原生 PowerPoint 图形补充图名批注, 供 Markdown→Word 转换器定位图页。"""

from __future__ import annotations

from pathlib import Path
import argparse

import win32com.client


PAPER = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").is_file() and (parent / "论文草稿.md").is_file())
SOURCE = PAPER / "temp/stage2-deck-build/stage2_editable_powerpoint_v6.pptx"
OUTPUT = PAPER / "temp/stage2-deck-build/stage2_named_candidate.pptx"
FIGURE_NAMES = ("stage2-radar-pair", "stage2-strongest-pair")


def main(source: Path, output: Path) -> None:
    """以 PowerPoint 打开原生组件图集, 给两页加入转换器识别的图名批注, 再另存为交付文件。"""
    application = win32com.client.DispatchEx("PowerPoint.Application")
    deck = application.Presentations.Open(str(source), False, False, False)
    try:
        for page, name in enumerate(FIGURE_NAMES, 1):
            deck.Slides(page).Comments.Add(8, 8, "Manuscript figure", "MF", f"@@{name}")
        output.parent.mkdir(parents=True, exist_ok=True)
        deck.SaveAs(str(output), 24)
    finally:
        deck.Close()
        application.Quit()
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    main(args.source.resolve(), args.output.resolve())
