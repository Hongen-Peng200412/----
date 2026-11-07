"""只组装本目录规定的完成度图, 面板由本次明确请求的master提供."""

from pathlib import Path
import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from TOOLS.runtime.paths import load_module
from TOOLS.ppt.svg_native import export_figure

ROOT = Path(__file__).resolve().parents[4]
ARTISTS = load_module(ROOT / "画图/画图代码/正文/Fig6-result-E2E/completion_artists.py", "fig6_completion_artists")
draw_panel, MEAN_COLOR, MEDIAN_COLOR = ARTISTS.draw_panel, ARTISTS.MEAN_COLOR, ARTISTS.MEDIAN_COLOR


# ================================================================================================
def draw(build: Path):
    """读取本图的6面板/页数据, 原Top1/Top5/best50分别占一行, 不运行另一身份条件.

    build: Path, 本次temp目录, data/master.json内仅含本目录的18或12面板. 每页左/右列严格RMSD<2/<3 Å, 画面由本目录display.json保留作者图层和完整图集画布.
    """
    master = json.loads((build / "data/master.json").read_text(encoding="utf8"))
    figures = build / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    manifest = []
    handles = [
        Line2D([], [], color=MEAN_COLOR, linewidth=1.8, marker="o", markersize=3.2, label="Mean"),
        Line2D(
            [],
            [],
            color=MEDIAN_COLOR,
            linewidth=1.05,
            marker="D",
            markerfacecolor="none",
            markersize=3.5,
            label="Median",
        ),
        Line2D([], [], color="#7F8C97", marker="o", linestyle="none", markersize=3, label="Individual PDB"),
    ]
    for domain, suffix, title in [
        ("Emap2lig", "emap2lig", "Emap2lig"),
        ("CA2", "ca2", "LigandSeek, CryoAtom2 receptor"),
        ("GT", "gt", "LigandSeek, deposited receptor"),
    ]:
        figure_id = "supp-find-correct-match-build-" + suffix
        fig = plt.figure(figsize=(159.262 / 25.4, 162 / 25.4))
        grid = fig.add_gridspec(3, 2, left=0.11, right=0.97, bottom=0.085, top=0.855, wspace=0.28, hspace=0.64)
        for index in range(6):
            pose = (1, 5, 50)[index // 2]
            threshold = (2.0, 3.0)[index % 2]
            panel = master["panels"][f"assume_{domain}_pose{pose}_rmsd{threshold}"]
            ax = fig.add_subplot(grid[index // 2, index % 2])
            pose_label = {1: "Top-1", 5: "Top-5", 50: "Best-of-50"}[pose]
            draw_panel(ax, panel, f"{pose_label}, RMSD <{threshold:g} Å", chr(97 + index), True)
            ax.texts[-1].set_position((-0.14, 1.26))
            if index % 2 == 0:
                ax.set_ylabel("Completion (%)", fontsize=7.5)
            if index >= 4:
                ax.set_xlabel("Relative attempt budget (%)", fontsize=8)
            else:
                ax.tick_params(axis="x", labelbottom=False)
        fig.text(0.11, 0.973, title, fontsize=9.3, fontweight="bold", va="top")
        fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.10, 0.94), ncol=3, frameon=False, fontsize=7.5)
        manifest.append(export_figure(fig, figures, figure_id, 600, False))
    (build / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")
