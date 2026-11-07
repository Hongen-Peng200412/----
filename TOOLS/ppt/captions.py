"""把正式作者图集的当前备注复制到同图名候选, 不改幻灯片内容或科学图元.

preserve_notes接收两个本地PPT地址和明确的完整图名列表. 只替换候选notesSlide中的备注正文, 作者PPT只读; 候选临时打包文件放其所在的本次构建目录.
"""

from copy import copy, deepcopy
from pathlib import Path
from zipfile import ZipFile
from TOOLS.ppt.deck import Deck, relationship_target, xml_bytes

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
NOTES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"


def preserve_notes(candidate: Path, author_pptx: Path, figures: list[str]):
    """原样复制figures对应页的当前备注正文, 包括双语文字、公式和格式.

    candidate: Path, 本次构建生成的候选. author_pptx: Path, 作者维护的正式图集, 不写入. figures: list[str], 包括版本后缀的完整图名, 如调用方声明的一个或多个标识. 两图集均须实际有这些页及备注正文.
    """
    target, author = Deck(candidate), Deck(author_pptx)
    for figure in figures:
        bodies = []
        parts = []
        for deck in (target, author):
            page = deck.figures[figure]
            relationships = (
                page.part.rsplit("/", 1)[0]
                + "/_rels/"
                + page.part.rsplit("/", 1)[1]
                + ".rels"
            )
            part = next(
                relationship_target(page.part, relation.get("Target"))
                for relation in deck.tree(relationships)
                if relation.get("Type") == NOTES
            )
            body = deck.tree(part).xpath(
                '//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody', namespaces=NS
            )[0]
            parts.append(part)
            bodies.append(body)
        bodies[0].getparent().replace(bodies[0], deepcopy(bodies[1]))
        target.changed.add(parts[0])
    staged = candidate.with_suffix(".notes-staging.pptx")
    try:
        with ZipFile(candidate) as source, ZipFile(staged, "w") as destination:
            destination.comment = source.comment
            for info in source.infolist():
                raw = (
                    xml_bytes(target.trees[info.filename])
                    if info.filename in target.changed
                    else source.read(info.filename)
                )
                destination.writestr(copy(info), raw)
        staged.replace(candidate)
    finally:
        staged.unlink(missing_ok=True)
