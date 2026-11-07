"""复核本图原始科学条件并构造当前单页作者显示, 不读取旧stage入口."""

import json, subprocess
from pathlib import Path
from TOOLS.runtime.paths import load_module
from TOOLS.server_io.source import SourceStore
from TOOLS.ppt.author_display import build_display
from TOOLS.chimerax.session_render import render_sessions as open_sessions

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FIG7 = ROOT / "画图/画图代码/正文/Fig7-visual-E2E-9BJJ"


def build(output, render_sessions):
    """读取本图必要原件, 生成单页candidate, 可选只读重开作者原会话."""
    output.mkdir(parents=True, exist_ok=True)
    config = json.loads((HERE / "case.json").read_text(encoding="utf-8"))
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    try:
        receipt = load_module(FIG7 / "selection.py", "fig7_case_selection").read_case(
            store, config["pdb"], True
        )
        assert (receipt["success_count"], receipt["target_count"]) == (
            config["expected_success_count"],
            config["expected_target_count"],
        ), "原预算/Top1结果与采用图不符"
        scene = load_module(FIG7 / "atoms.py", "fig7_case_atoms").materialize(
            store, receipt, output / "scientific-input", config["display"]
        )
        (output / "scientific-input/scene.json").write_text(
            json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output / "scientific_receipt.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output / "source_reads.json").write_text(
            json.dumps(store.reads, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    finally:
        store.close()
    # 本次完整科学重建独立生成CXS/PNG, 当前采用作者显示仍用design中的明确原件.
    script = output / "scientific-input/run_native.py"
    script.write_text(
        "from pathlib import Path\ntask_scene="
        + repr(str((output / "scientific-input/scene.json").resolve()))
        + "\nexec(compile(Path("
        + repr(str(FIG7 / "native.py"))
        + ').read_text(encoding="utf-8"),'
        + repr(str(FIG7 / "native.py"))
        + ',"exec"),globals())\n',
        encoding="utf-8",
    )
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "TOOLS/chimerax/run_chimerax.ps1"),
            "-CxcPath",
            str(script.resolve()),
            "-LogPrefix",
            str((output / "scientific-input/native").resolve()),
        ],
        check=True,
    )
    for filename in ["complex.png", "complex.cxs"]:
        if not (output / "scientific-input/native-output" / filename).is_file():
            raise RuntimeError("原生完整重建未完成: " + filename)

    candidate = build_display(HERE / "design", output)
    if render_sessions:
        metadata = json.loads((HERE / "design/design.json").read_text(encoding="utf-8"))
        open_sessions(
            [ROOT / path for path in metadata["native_sessions"]],
            output / "author-native",
            *config["native_size"],
            config["native_window_size"]
        )
    return candidate
