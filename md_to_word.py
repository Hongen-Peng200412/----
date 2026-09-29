"""直接运行可将论文草稿.md 转换成 Nature Article 初次投稿用 Word。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from manuscript_conversion import markdown_to_word


def main() -> None:
    parser = argparse.ArgumentParser(description="Markdown → Nature Article Word")
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).with_name("论文草稿.md"))
    parser.add_argument("--output", type=Path, help="输出 DOCX；默认与输入同名，加 .nature.docx")
    parser.add_argument("--bib", type=Path, help="BibTeX 文献库；默认输入旁的 references.bib")
    options = parser.parse_args()
    output = options.output or options.source.with_name(options.source.stem + ".nature.docx")
    markdown_to_word(options.source, output, options.bib)
    print(f"已生成：{output.resolve()}")


if __name__ == "__main__":
    main()
