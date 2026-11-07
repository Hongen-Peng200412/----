"""只绘制补Fig2的无显式level四面板, 不运行主图或其他补图.

render接收本次no_level的逐PDB指标和分布, 输出SVG/PDF/PNG与本页scene. 共同Find科学指标和绘图原语由正文Fig3显式提供.
"""

from pathlib import Path
import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from TOOLS.runtime.paths import load_module
from TOOLS.ppt.matplotlib_export import export_scene

ROOT = Path(__file__).resolve().parents[4]
ARTISTS = load_module(ROOT / "画图/画图代码/正文/Fig3-result-Find/artists.py", "fig3_find_artists")
MODELS, COLOURS, LABELS = ARTISTS.MODELS, ARTISTS.COLOURS, ARTISTS.LABELS


FIGURE = "stage1-no-level-comparison-NO_LEVEL"


# ================================================================================================
def render(data, build: Path):
    """构造无level单页, 上下行分别为全部配体和全部小分子.

    data仅含no_level的179/94-PDB轴; bars使用Dice/PRAUC0.3/PRAUC0.5, distribution使用两阈值P/R. 不请求完成度、分辨率或配对比较.
    """
    build.mkdir(parents=True, exist_ok=True)
    plt.rcdefaults()
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Calibri", "Arial"],
            "font.size": 8,
            "axes.labelsize": 7.6,
            "axes.titlesize": 8.1,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "text.color": "#263746",
            "axes.labelcolor": "#263746",
            "xtick.color": "#263746",
            "ytick.color": "#263746",
        }
    )
    fig = plt.figure(figsize=(180 / 25.4, 148 / 25.4))
    grid = fig.add_gridspec(2, 2, left=0.095, right=0.985, bottom=0.16, top=0.86, wspace=0.25, hspace=0.55)
    handles = [
        Patch(
            facecolor=COLOURS[model],
            edgecolor="none",
            label="Emap2lig-Find (no level)" if model == "Emap" else LABELS[model],
        )
        for model in MODELS
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.98),
        ncol=3,
        frameon=False,
        fontsize=7.6,
        handlelength=1.2,
        columnspacing=1.2,
    )
    for row, cohort in enumerate(("full", "small")):
        block = data["cohorts"][cohort]
        for column in range(2):
            ax = fig.add_subplot(grid[row, column])
            if column == 0:
                ARTISTS.draw_scores(
                    ax,
                    block,
                    ("dice", "oto03", "oto05"),
                    [
                        "Semantic\nDice",
                        "Instance-level\n" + r"$\mathrm{PRAUC}_{0.3}$",
                        "Instance-level\n" + r"$\mathrm{PRAUC}_{0.5}$",
                    ],
                )
            else:
                ARTISTS.draw_precision_recall(
                    ax,
                    block,
                    ("precision", "recall", "precision05", "recall05"),
                    [
                        "Precision\n" + r"$\tau=0.3$",
                        "Recall\n" + r"$\tau=0.3$",
                        "Precision\n" + r"$\tau=0.5$",
                        "Recall\n" + r"$\tau=0.5$",
                    ],
                )
            ax.grid(axis="y", color="#E5E9EC", linewidth=0.45, zorder=0)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7.2, length=2.5, width=0.65)
            letter = chr(97 + row * 2 + column)
            ax.set_gid(letter)
            ax.annotate(
                letter,
                xy=(0, 1),
                xycoords="axes fraction",
                xytext=(-27, 8),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                va="bottom",
                annotation_clip=False,
            )
            ax.set_title(
                "All ligands" if cohort == "full" else "Small molecules", loc="left", pad=10, fontweight="bold"
            )
    exemptions = []
    # 当前双语备注只由正式作者PPT维护, run.py在候选完成后原样复制; 图元阶段不另存一份图注.
    scene = export_scene(fig, FIGURE, "", build, exemptions)
    (build / "scenes.json").write_text(json.dumps([scene], ensure_ascii=False), encoding="utf-8")
    (build / "manifest.json").write_text(
        json.dumps([{key: value for key, value in scene.items() if key != "shapes"}], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return scene
