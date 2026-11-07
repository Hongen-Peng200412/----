"""从本图需要的服务器原件生成单页候选; 不调用其他图入口."""

import json, subprocess
from pathlib import Path
from TOOLS.runtime.paths import load_module
from TOOLS.server_io.source import SourceStore
from TOOLS.ppt.display_patch import patch_presentation

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NODE = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"

SCIENCE = HERE.parents[1] / "正文/Fig5-result-Match&Build/science.py"


def build(output):
    """读取本图原件、计算必要统计并应用本图作者显示; 返回单页candidate.pptx."""
    output.mkdir(parents=True, exist_ok=True)
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    science = load_module(SCIENCE, "fig5_match_build_science")
    try:
        data = {"ablation": science.read_standard_build(store, "C0")}
        data["match"] = science.read_match(store, "ablation")
        summary = {
            "ablation": {
                protocol: {
                    receptor: {
                        model: {
                            pose: science.describe_rmsd(series[pose], 446)
                            for pose in ["top1", "top5", "best50"]
                        }
                        for model, series in models.items()
                    }
                    for receptor, models in receptors.items()
                }
                for protocol, receptors in data["ablation"].items()
            }
        }
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

    definition = json.loads((HERE / "author_layout.json").read_text(encoding="utf-8"))
    patch_presentation(output / "candidate.pptx", definition, set())
    return output / "candidate.pptx"
