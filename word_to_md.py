"""直接运行可把论文草稿.nature.docx 回转成 Markdown。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from manuscript_conversion import word_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Nature Article Word → Markdown")
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).with_name("论文草稿.nature.docx"))
    parser.add_argument("--output", type=Path, help="输出 Markdown；默认与输入同名，加 .from_word.md")
    options = parser.parse_args()
    stem = options.source.stem.removesuffix(".nature")
    output = options.output or options.source.with_name(stem + ".from_word.md")
    word_to_markdown(options.source, output)
    print(f"已生成：{output.resolve()}")


if __name__ == "__main__":
    main()
