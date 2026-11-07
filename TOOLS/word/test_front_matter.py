"""核对论文开头在两种 Word 版式、回转及 Word 手工修改中的保留行为."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from TOOLS.word.manuscript_conversion import TEMP_ROOT, ensure_dependencies, markdown_to_word, word_to_markdown


def main() -> None:
    ensure_dependencies()
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    styles = ("Manuscript Title", "Manuscript Authors", "Manuscript Affiliation", "Manuscript Correspondence")
    texts = ("Automated ligand model building in Cryo-EM maps using LigandSeek",
             "Hongen Peng, xxx, Jianyi Yang*",
             "MOE Frontiers Science Center for Nonlinear Expectations, Research Center for Mathematics and Interdisciplinary Sciences, Shandong University, Qingdao, China.",
             "*Corresponding author: yangjy@sdu.edu.cn")
    blocks = []
    for index, (style, text) in enumerate(zip(styles, texts)):
        text = text.replace("*", r"\*")
        blocks.append(f'::: {{custom-style="{style}"}}\n' + (f"**{text}**" if index == 0 else text) + "\n:::")
    front = "\n\n".join(blocks) + "\n\n"
    body = "# Abstract\n\nBody with $x^2$ and **emphasis**.\n\n# Introduction\n\nNext paragraph.\n"
    TEMP_ROOT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="front_matter_test_", dir=TEMP_ROOT) as folder:
        work = Path(folder)
        source = work / "article.md"
        source.write_text(front + body, encoding="utf-8")
        plain = work / "plain.md"
        plain.write_text(body, encoding="utf-8")
        reference = work / "reference.docx"
        Document().save(reference)
        for profile in ("nature", "operation"):
            word = work / f"{profile}.docx"
            markdown_to_word(source, word, profile=profile, reference=reference)
            actual = Document(word)
            assert [p.text for p in actual.paragraphs[:4]] == list(texts)
            assert [p.style.name for p in actual.paragraphs[:4]] == list(styles)
            assert actual.paragraphs[4].text == "Abstract"
            assert actual.paragraphs[4].style.name == "Heading 1"
            assert actual._element.xpath(".//m:oMath"), "正文原生公式丢失"
            for index, paragraph in enumerate(actual.paragraphs[:4]):
                fmt = paragraph.paragraph_format
                assert fmt.first_line_indent == Pt(0)
                assert fmt.line_spacing == (2.0 if index == 0 else 1.5)
                assert fmt.keep_together is True
                assert fmt.keep_with_next == (index != 3)
                assert paragraph.alignment == (WD_ALIGN_PARAGRAPH.CENTER if index == 1 else WD_ALIGN_PARAGRAPH.JUSTIFY)
                assert all(run.font.name == "Times New Roman" for run in paragraph.runs)
                assert all(run.font.size == Pt(14 if index == 0 else 12) for run in paragraph.runs)
                assert all(run.font.superscript is not True for run in paragraph.runs)
            assert all(run.bold for run in actual.paragraphs[0].runs)
            if profile == "operation":
                assert actual.paragraphs[5].paragraph_format.first_line_indent == Pt(21)
            first = work / f"{profile}_first.md"
            word_to_markdown(word, first)
            returned = first.read_text(encoding="utf-8")
            assert all(f'custom-style="{style}"' in returned for style in styles)
            assert r"Yang\*" in returned and r"\*Corresponding author:" in returned
            rebuilt = work / f"{profile}_rebuilt.docx"
            markdown_to_word(first, rebuilt, profile=profile, reference=reference)
            second = work / f"{profile}_second.md"
            word_to_markdown(rebuilt, second)
            assert first.read_bytes() == second.read_bytes(), "两次回转内容不一致"
            assert [p.text for p in Document(rebuilt).paragraphs[:4]] == list(texts)
            for run in actual.paragraphs[1].runs:
                run.text = run.text.replace("xxx", "Example Coauthor")
            edited = work / f"{profile}_edited.docx"
            actual.save(edited)
            edited_md = work / f"{profile}_edited.md"
            word_to_markdown(edited, edited_md)
            assert "Example Coauthor" in edited_md.read_text(encoding="utf-8")
            assert "xxx" not in edited_md.read_text(encoding="utf-8")
            edited_rebuilt = work / f"{profile}_edited_rebuilt.docx"
            markdown_to_word(edited_md, edited_rebuilt, profile=profile, reference=reference)
            assert Document(edited_rebuilt).paragraphs[1].text == texts[1].replace("xxx", "Example Coauthor")
            plain_word = work / f"{profile}_plain.docx"
            markdown_to_word(plain, plain_word, profile=profile, reference=reference)
            assert Document(plain_word).paragraphs[0].text == "Abstract", "未指定开头的稿件被添加了开头"
            print(f"通过: {profile} 开头文字、格式、连续回转、Word 改署名及无开头稿件.")


if __name__ == "__main__":
    main()
