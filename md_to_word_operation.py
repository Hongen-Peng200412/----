"""直接运行可将论文草稿.md 转换成 Operation 版式的阅读用 Word。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from manuscript_conversion import OPERATION_REFERENCE, markdown_to_word


def main() -> None:
    parser = argparse.ArgumentParser(description="Markdown → Operation 版式 Word")
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).with_name("论文草稿.md"))
    parser.add_argument("--output", type=Path, help="输出 DOCX；默认与输入同名，加 .operation.docx")
    parser.add_argument("--bib", type=Path, help="BibTeX 文献库；默认输入旁的 references.bib")
    parser.add_argument("--english", action="store_true", help="选择 PPT 备注中 ENGLISH: 独立行之后的英文图注")
    parser.add_argument("--image-align", choices=("left", "center", "right"), default="center",
                        help="独立图片对齐方式；默认 center")
    parser.add_argument("--image-size", choices=("fit", "original"), default="fit",
                        help="独立图片等比适配版心或保留原插入尺寸；默认 fit")
    parser.add_argument("--reference", type=Path, default=OPERATION_REFERENCE,
                        help="版式参考 Word；默认 D:/OneDrive/Operation.docx")
    options = parser.parse_args()
    output = options.output or options.source.with_name(options.source.stem + ".operation.docx")
    markdown_to_word(options.source, output, options.bib,
                     profile="operation", reference=options.reference,
                     image_align=options.image_align, image_size=options.image_size,
                     english=options.english)
    print(f"已生成：{output.resolve()}")


if __name__ == "__main__":
    main()
