"""切换 Stage 2 口径, 保留两稿其他文字和两个 PPT 的图形.

参数 --profile: new 排除 2+2 个不可解析候选; old 恢复旧统计及图引用.
参数 --root: 稿件根目录, 默认由本文件位置解析; 可指向临时副本做切换检查.
英文旧图注由同目录上一级的两种口径图注.json 保存, 仅切回旧口径时写入旧 PPT.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path

OLD_PPT = "画图/stage2结果.pptx"
NEW_PPT = "画图/stage2结果_忽视2+2例子.pptx"
SENTENCES = {
    "论文草稿.md": (
        "由于我们不对blob进行额外过滤或处理，所以Match的测试可以反映真实推理管线的运行情况。",
        "除去对应配体无法解析的blob后，我们不对其余blob进行额外过滤或处理，所以Match的测试可以反映真实推理管线的运行情况。",
    ),
    "draft.md": (
        "We applied no additional filtering or processing to the blobs, so this evaluation reflected the operation of the actual inference pipeline.",
        "After excluding blobs with unparseable ligands, we applied no additional filtering or processing to the remaining blobs. This evaluation therefore reflected the operation of the actual inference pipeline.",
    ),
}


def prepare_old_notes(path: Path, captions: list[dict]) -> tuple[list, dict[str, bytes]]:
    """按当前旧中文备注校验图注映射, 只更新 ENGLISH 区域, 不改中文或图形."""
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        parts = {info.filename: archive.read(info) for info in infos}
    for caption in captions:
        name = f'ppt/notesSlides/notesSlide{caption["page"]}.xml'
        raw = parts[name].decode("utf-8")
        bodies = [m for m in re.finditer(r"<p:sp>.*?</p:sp>", raw, flags=re.S)
                  if 'type="body"' in m.group()]
        if len(bodies) != 1:
            raise ValueError(f"旧图注备注位置不唯一: {name}")
        body = bodies[0]
        tx = re.search(r"<p:txBody>(.*?)</p:txBody>", body.group(), flags=re.S)
        chinese = []
        chinese_text = []
        for paragraph in re.findall(r"<a:p>.*?</a:p>", tx.group(1), flags=re.S):
            text = "".join(html.unescape(s) for s in re.findall(r"<a:t>(.*?)</a:t>", paragraph, flags=re.S))
            if re.fullmatch(r"\s*ENGLISH[:：]\s*", text):
                break
            chinese.append(paragraph)
            chinese_text.append(text)
        if "\n".join(chinese_text) != caption["chinese"]:
            raise ValueError(f"旧中文图注已有新修改, 需先同步两种口径图注.json: {name}")
        extra = "".join(f'<a:p><a:r><a:rPr lang="en-US"/><a:t>{html.escape(t)}</a:t></a:r></a:p>'
                        for t in ["ENGLISH:", caption["english"]])
        prefix = tx.group(1).split("<a:p>", 1)[0]
        updated_body = body.group()[:tx.start()] + "<p:txBody>" + prefix + "".join(chinese) + extra + "</p:txBody>" + body.group()[tx.end():]
        parts[name] = (raw[:body.start()] + updated_body + raw[body.end():]).encode("utf-8")
    return infos, parts


def switch_profile(root: Path, profile: str) -> None:
    """先完整校验两个源稿和目标图集, 再应用有限替换, 不还原全文快照."""
    target_index = 1 if profile == "new" else 0
    other_index = 1 - target_index
    deck = root / (NEW_PPT if target_index else OLD_PPT)
    if not deck.is_file():
        raise FileNotFoundError(deck)
    prepared = {}
    for name, sentences in SENTENCES.items():
        path = root / name
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        current, desired = sentences[other_index], sentences[target_index]
        if text.count(current) == 1 and desired not in text:
            text = text.replace(current, desired, 1)
        elif text.count(desired) != 1 or current in text:
            raise ValueError(f"对应候选处理句已修改, 需先核对: {path}")
        for figure in ["stage2-radar-pair", "stage2-strongest-pair"]:
            refs = [f'{{{{pptfig:"{source}"|{figure}}}}}' for source in [OLD_PPT, NEW_PPT]]
            if sum(text.count(ref) for ref in refs) != 1:
                raise ValueError(f"Stage 2 插图定义缺失或重复: {path}, {figure}")
            text = text.replace(refs[other_index], refs[target_index], 1)
        encoded = text.encode("utf-8")
        if raw.startswith(b"\xef\xbb\xbf"):
            encoded = b"\xef\xbb\xbf" + encoded
        prepared[path] = (raw, encoded)
    old_parts = None
    if profile == "old":
        captions = json.loads((root / "画图/画图代码/stage2/两种口径图注.json").read_text(encoding="utf-8"))
        old_parts = prepare_old_notes(deck, captions["old"])
    # 写入前复核源稿, 防止覆盖工作期间作者刚保存的内容.
    for path, (raw, _) in prepared.items():
        if path.read_bytes() != raw:
            raise RuntimeError(f"源稿在校验后发生变化: {path}")
    if old_parts is not None:
        pending = root / "temp/stage2_profile_switch_old.pptx"
        pending.parent.mkdir(parents=True, exist_ok=True)
        infos, parts = old_parts
        with zipfile.ZipFile(pending, "w") as archive:
            for info in infos:
                archive.writestr(info, parts[info.filename])
        pending.replace(deck)
    for path, (_, encoded) in prepared.items():
        path.write_bytes(encoded)
    active = {"profile": profile, "ppt": NEW_PPT if target_index else OLD_PPT,
              "plot_data": "data_忽视2+2例子.json" if target_index else "data.json",
              "metrics": "两种口径统计.json", "metrics_key": profile,
              "candidate_counts": {"real": 1651 if target_index else 1653,
                                   "cryo": 1649 if target_index else 1651},
              "end_to_end_changed": False}
    (root / "画图/画图代码/stage2/当前口径.json").write_text(json.dumps(active, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Stage 2 默认口径: {profile}; 请用原有两个转换入口分别编译中英文 Word.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="切换 Stage 2 新旧口径及两稿图引用")
    parser.add_argument("--profile", choices=["new", "old"], required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    options = parser.parse_args()
    switch_profile(options.root.resolve(), options.profile)
