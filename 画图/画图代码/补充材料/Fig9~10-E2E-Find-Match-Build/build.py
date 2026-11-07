"""从具名服务器原件构造本目录对应图, 所需面板在此明确列出."""

from pathlib import Path
import json, csv
from TOOLS.runtime.paths import load_module
from TOOLS.server_io.source import SourceStore
from TOOLS.ppt.svg_native import build_candidate

ROOT = Path(__file__).resolve().parents[4]
MAIN = ROOT / "画图/画图代码/正文/Fig6-result-E2E"
PREPARE = load_module(MAIN / "prepare.py", "fig6_prepare")
COMPLETION = load_module(MAIN / "completion.py", "fig6_completion")
PLOT = load_module(Path(__file__).with_name("plot.py"), "current_e2e_plot")
PANELS = (
    "actual_CA2_pose1_rmsd2.0",
    "actual_CA2_pose1_rmsd3.0",
    "actual_CA2_pose5_rmsd2.0",
    "actual_CA2_pose5_rmsd3.0",
    "actual_CA2_pose50_rmsd2.0",
    "actual_CA2_pose50_rmsd3.0",
    "actual_GT_pose1_rmsd2.0",
    "actual_GT_pose1_rmsd3.0",
    "actual_GT_pose5_rmsd2.0",
    "actual_GT_pose5_rmsd3.0",
    "actual_GT_pose50_rmsd2.0",
    "actual_GT_pose50_rmsd3.0",
)


# ================================================================================================
def build(output: Path):
    """只重算PANELS明确的本图条件, 返回可编辑候选路径.

    output: Path, 本次根temp空目录. data/master.json保留完整分母/事件/曲线, source_data.csv保留逐PDB预算记录, server_reads.json保留原件身份. 不覆盖正式作者PPT, 不写服务器.
    """
    output.mkdir(parents=True, exist_ok=True)
    data = output / "data"
    data.mkdir()
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    try:
        panels = PREPARE.prepare_panels(store, PANELS)
        (data / "server_reads.json").write_text(json.dumps(store.reads, ensure_ascii=False, indent=2), encoding="utf8")
    finally:
        store.close()
    master, rows = COMPLETION.summarize_panels(panels)
    (data / "master.json").write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf8")
    with (data / "source_data.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    PLOT.draw(output)
    pages = json.loads((output / "manifest.json").read_text(encoding="utf8"))
    display = json.loads(Path(__file__).with_name("display.json").read_text(encoding="utf8"))
    return build_candidate(output, pages, display["canvas"], {"name": "Hongen Peng", "initials": "HP"}, display)
