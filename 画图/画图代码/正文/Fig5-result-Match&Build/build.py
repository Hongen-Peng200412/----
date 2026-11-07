"""从本图需要的服务器原件生成单页候选; 不调用其他图入口."""

import json, subprocess
from pathlib import Path
from TOOLS.runtime.paths import load_module
from TOOLS.server_io.source import SourceStore
from TOOLS.ppt.display_patch import patch_presentation

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NODE = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"

SCIENCE = HERE / "science.py"


def build(output):
    """读取本图原件、计算必要统计并应用本图作者显示; 返回单页candidate.pptx."""
    output.mkdir(parents=True, exist_ok=True)
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    science = load_module(SCIENCE, "fig5_match_build_science")
    try:
        data = {
            "match": science.read_match(store, "main"),
            "main_build": science.read_main_build(store),
        }
        summary = {
            "main_build": {
                method: {
                    pose: science.describe_rmsd(values, 235) for pose, values in series.items()
                }
                for method, series in data["main_build"]["series"].items()
            },
            "main_win_pct": data["main_build"]["win_pct"],
        }
        # 只有本图需要9WUP原构象/密度和PCA显示; 消融入口不调用此分支.
        load_module(HERE / "visual/geometry.py", "fig5_9wup_geometry").prepare(
            store, output / "case-source"
        )
        (output / "data").mkdir()
        (output / "data/data.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output / "data/summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (output / "source_reads.json").write_text(
            json.dumps(store.reads, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    finally:
        store.close()
    page = load_module(HERE / "plot.py", "current_figure_plot").plot(data, output)
    (output / "scenes.json").write_text(json.dumps([page], ensure_ascii=False), encoding="utf-8")
    display = {
        "canvas": {"width": 601.92, "height": 628.8},
        "scale": 4 / 3,
        "offset": [0, 0],
        "layouts": {},
        "author": {
            "displayName": "Hongen Peng",
            "initials": "HP",
            "userId": "hongen-peng",
            "providerId": "None",
        },
    }
    (output / "display.json").write_text(json.dumps(display), encoding="utf-8")
    subprocess.run(
        [
            str(NODE),
            str(ROOT / "TOOLS/ppt/build_scene.mjs"),
            str(output),
            str(output / "display.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    case = json.loads((output / "case-source/geometry.json").read_text())["cases"][0]
    metrics = json.loads((output / "case-source/case_metrics.json").read_text())[0]
    case_page = load_module(HERE / "visual/compose.py", "fig5_9wup_compose").scene(case, metrics)
    native = output / "case-native"
    native.mkdir()
    (native / "scenes.json").write_text(json.dumps([case_page]), encoding="utf-8")
    case_display = {
        "canvas": {"width": 980, "height": 1256},
        "scale": 1,
        "offset": [0, 0],
        "layouts": {},
        "author": {
            "displayName": "Figure Editor",
            "initials": "FE",
            "userId": "figure-editor",
            "providerId": "None",
        },
    }
    (native / "display.json").write_text(json.dumps(case_display), encoding="utf-8")
    subprocess.run(
        [
            str(NODE),
            str(ROOT / "TOOLS/ppt/build_scene.mjs"),
            str(native),
            str(native / "display.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    rects = json.loads((output / "case_rects.json").read_text())
    load_module(HERE / "visual/inject.py", "fig5_9wup_inject").inject_case_views(
        output / "candidate.pptx", rects, native / "candidate.pptx"
    )
    definition = json.loads((HERE / "author_layout.json").read_text(encoding="utf-8"))
    # 本图b/c曲线与刻度须由本次真实计数重算至0–105%, 不套用旧科学坐标差分.
    excluded = {f"results_{i}" for i in list(range(81, 105)) + list(range(147, 171))}
    excluded.update(
        f"{prefix}_{i}"
        for prefix in ["results", "text"]
        for i in list(range(68, 80)) + list(range(134, 146))
    )

    def recalculate_match_axes(slide):
        """0–105%轴只属于Fig5; 回调发生在作者图例追加前, 不改原始匹配计数."""
        ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        next_id = max(int(node.get("id")) for node in slide.findall(".//p:cNvPr", ns)) + 1
        axis = load_module(HERE / "visual/axis.py", "fig5_match_axis")
        next_id, _ = axis.rewrite_axis(slide, data, "GT", 81, "results_56", next_id)
        axis.rewrite_axis(slide, data, "CA2", 147, "results_122", next_id)

    patch_presentation(output / "candidate.pptx", definition, excluded, recalculate_match_axes)
    return output / "candidate.pptx"
