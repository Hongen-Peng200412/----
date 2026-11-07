"""只绘制补Fig1的严格0.5匹配分析和两个Find预算, 不绘制其他图.

render消费当前图的0.5指标与100%/300%预算均值区间. 0.5只用于左两列PRAUC/P/R, 预算命中仍沿用0.3固定归属. 输出本图SVG/PDF/PNG和一页scene.
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
FIGURE = "stage1-additional-analysis"


# ================================================================================================
def render(data, summary, build: Path):
    """构造补Fig1六面板, 保留原作者中列平移、文字间距与图例.

    data沿full/small原PDB轴提供oto05/precision05/recall05; summary键为(cohort,method,budget), mean/lower/upper单位均是0-1比例. build为本次temp子目录, 不从任何既有图稿读取数值.
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
    grid = fig.add_gridspec(2, 3, left=0.095, right=0.985, bottom=0.16, top=0.86, wspace=0.45, hspace=0.55)
    handles = [Patch(facecolor=COLOURS[model], edgecolor="none", label=LABELS[model]) for model in MODELS]
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
        for column in range(3):
            ax = fig.add_subplot(grid[row, column])
            if column == 0:
                ARTISTS.draw_scores(ax, block, ("oto05",), [r"Instance-level $\mathrm{PRAUC}_{0.5}$"])
            elif column == 1:
                ARTISTS.draw_precision_recall(
                    ax, block, ("precision05", "recall05"), ["Instance-level\nprecision", "Instance-level\nrecall"]
                )
            else:
                for budget_index, budget in enumerate((100, 300)):
                    for model_index, model in enumerate(MODELS):
                        x = budget_index + (model_index - 1) * 0.235
                        stats = summary[cohort, model, budget]
                        colour = COLOURS[model]
                        mean, lower, upper = np.asarray([stats["mean"], stats["lower"], stats["upper"]]) * 100
                        ax.bar(x, mean, width=0.205, color=colour, edgecolor="none", zorder=2)
                        ax.vlines(x, lower, upper, color="#42515D", linewidth=0.85, zorder=3)
                        ax.hlines([lower, upper], x - 0.035, x + 0.035, color="#42515D", linewidth=0.85, zorder=3)
                        ax.text(x, upper + 3.2, f"{mean:.1f}", ha="center", va="bottom", fontsize=7.2, color="#263746")
                ax.set(
                    xlim=(-0.53, 1.53),
                    ylim=(0, 100),
                    yticks=[0, 25, 50, 75, 100],
                    xticks=[0, 1],
                    xticklabels=["100", "300"],
                    xlabel="Relative candidate count (%)",
                    ylabel="Mean detection completion (%)",
                )
            if column == 2:
                ax.grid(False)
            else:
                ax.grid(axis="y", color="#E5E9EC", linewidth=0.45, zorder=0)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7.2, length=2.5, width=0.65)
            if column == 1:
                position = ax.get_position()
                ax.set_position([position.x0 - 0.018, position.y0, position.width, position.height])
            if column == 2:
                for index, label in enumerate(ax.texts):
                    budget = (100, 300)[index // len(MODELS)]
                    label.set_y(max(summary[cohort, model, budget]["upper"] for model in MODELS) * 100 + 3.2)
                    label.set_fontsize(6.4)
                    label.set_x(label.get_position()[0] + (index % len(MODELS) - 1) * 0.05)
            letter = chr(97 + row * 3 + column)
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
    exemptions = [
        {
            "panels": ["b", "e"],
            "checks": ["horizontal-gutter"],
            "reason": "作者指定中列左移以平衡数据标记与预算标签的视觉空白; 上下行同步, 轴框大小不变.",
        }
    ]
    # 当前双语备注只由正式作者PPT维护, run.py在候选完成后原样复制; 图元阶段不另存一份图注.
    scene = export_scene(fig, FIGURE, "", build, exemptions)
    (build / "scenes.json").write_text(json.dumps([scene], ensure_ascii=False), encoding="utf-8")
    (build / "manifest.json").write_text(
        json.dumps([{key: value for key, value in scene.items() if key != "shapes"}], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return scene
