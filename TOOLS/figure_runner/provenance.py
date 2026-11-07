"""依照各图自己的声明检查或更新 PPT 来源短指路.

--check 只读核对, --sync 仅改来源批注并把本次比对副本放根 temp.
图名、图集及追溯说明均由 Figure 声明, 本工具不定义实验选择或评价规则.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from TOOLS.runtime.paths import configure_runtime

configure_runtime(ROOT)
from TOOLS.figure_runner.catalog import discover, trace_comment
from TOOLS.ppt.deck import Deck, comment_text, set_comment_text


def update_source_comment(deck, slide, expected: str, synchronize: bool) -> bool:
    """核对一页的唯一来源短指路, 写入时沿用既有批注身份和制式."""
    matches = [
        (part, node)
        for part in slide.comments
        for node in deck.comments(part)
        if comment_text(node).startswith(("TRACE v", "PROVENANCE", "SOURCE:"))
    ]
    if not synchronize:
        return len(matches) == 1 and comment_text(matches[0][1]) == expected
    if not matches:
        deck.append(slide, expected)
        return True
    part, node = matches[0]
    if comment_text(node) != expected:
        set_comment_text(node, expected)
        deck.changed.add(part)
    for extra_part, extra_node in matches[1:]:
        deck.tree(extra_part).remove(extra_node)
        deck.changed.add(extra_part)
    return True


def annotate_candidate(candidate: Path, figure_directory: Path):
    """为本次候选补齐本图声明的短指路, 不修改正式图集或作者备注.

    figure_directory 是包含 figure.json 的当前图目录, candidate 必须位于项目根 temp.
    候选的完整图名集合必须与声明完全相同, 防止向其它页面附加错误来源.
    """
    candidate = candidate.resolve()
    candidate.relative_to(ROOT / "temp")
    key = figure_directory.resolve().relative_to(ROOT / "画图/画图代码").as_posix()
    entry = discover(ROOT)[key]
    deck = Deck(candidate)
    if set(deck.figures) != set(entry["figures"]):
        raise ValueError("候选页范围不等于声明: " + key)
    for figure in entry["figures"]:
        update_source_comment(deck, deck.figures[figure], trace_comment(entry), True)
    if deck.changed:
        deck.save(candidate.parent, candidate.parent / "source-comment-before")


def process(project: Path, synchronize: bool):
    """核对声明图的唯一页面与两个本图说明, 必要时原位替换来源批注.

    synchronize 为 True 时只写发生变化的图集批注部件.
    返回检查图数、修改图集数及错误文字, 由调用方决定如何呈现和退出.
    """
    entries = discover(project)
    decks = {}
    errors = []
    count = 0
    for key, entry in entries.items():
        for name in ("README.md", "trace.md"):
            if not (entry["directory"] / name).is_file():
                errors.append(f"{key} 缺少 {name}")
        if entry["kind"] == "table":
            continue
        path = (project / entry["pptx"]).resolve()
        path.relative_to(project)
        if path not in decks:
            decks[path] = Deck(path)
        deck = decks[path]
        expected = trace_comment(entry)
        for figure in entry["figures"]:
            count += 1
            if figure not in deck.figures:
                errors.append(f'{entry["pptx"]} 缺少唯一图名 {figure}')
                continue
            slide = deck.figures[figure]
            if not update_source_comment(deck, slide, expected, synchronize):
                errors.append(f"{figure} 的来源批注未对应当前 Figure 目录")
    changed = [deck for deck in decks.values() if deck.changed]
    if errors:
        return count, len(changed), errors
    if synchronize:
        backup = (
            project
            / "temp/provenance"
            / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        )
        for deck in changed:
            deck.save(project, backup)
    return count, len(changed), errors


def main():
    """执行只读核查或来源批注同步, 有缺项时保留作者文件并失败退出."""
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--sync", action="store_true")
    args = parser.parse_args()
    count, changed, errors = process(ROOT, args.sync)
    for error in errors:
        print(error, file=sys.stderr)
    print(f"检查图数: {count}; 修改图集: {changed}; 问题: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
