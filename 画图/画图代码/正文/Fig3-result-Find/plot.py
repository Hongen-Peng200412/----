"""只绘制正文Fig3的六个Find面板, 输入必须来自本次单条件重算.

render接收plot_data内存对象, 在build写本图SVG/PDF/PNG、scene和manifest. 配对散点使用显式level的Dice, 颜色仅映射原地图分辨率; 不绘制补充图或预算面板.
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


FIGURE = "stage1-overall-performance(v1)"


# ================================================================================================
def render(data, build: Path):
    """输出正文Fig3单页图元; full/small分别保留179/94个PDB.

    data.cohorts[范围]中的values沿ids对齐; resolution单位Å; paired_counts仅用于配对计数字符. build为本次根temp子目录, scene.shapes按绘制顺序保存文字和几何, 不作为下次输入.
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
    plt.rcParams.update(
        {
            "mathtext.fontset": "custom",
            "mathtext.rm": "Calibri",
            "mathtext.it": "Calibri:italic",
            "mathtext.bf": "Calibri:bold",
            "mathtext.default": "regular",
        }
    )
    fig = plt.figure(figsize=(180 / 25.4, 155 / 25.4))
    grid = fig.add_gridspec(2, 3, left=0.085, right=0.955, bottom=0.16, top=0.87, wspace=0.60, hspace=0.70)
    handles = [Patch(facecolor=COLOURS[model], edgecolor="none", label=LABELS[model]) for model in MODELS]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.985),
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
            ax.set_box_aspect(1)
            if column == 0:
                ARTISTS.draw_scores(
                    ax, block, ("dice", "oto03"), ["Semantic Dice", "Instance-level\n" + r"$\mathrm{PRAUC}_{0.3}$"]
                )
            elif column == 1:
                # (N_pdb,), x/y同属同一个PDB轴, 只比较Dice; 不按结果排序或删去相等值.
                x = np.asarray(block["models"]["Emap"]["values"]["dice"])
                y = np.asarray(block["models"]["Cryo"]["values"]["dice"])
                ax.plot([0, 1], [0, 1], color="#8B969F", linewidth=0.8, linestyle=(0, (3, 3)), zorder=1)
                points = ax.scatter(
                    x,
                    y,
                    c=block["resolution"],
                    cmap="viridis_r",
                    vmin=1,
                    vmax=4,
                    s=13,
                    edgecolor="white",
                    linewidth=0.3,
                    alpha=0.8,
                    zorder=2,
                    clip_on=False,
                )
                ax.set(
                    xlim=(0, 1),
                    ylim=(0, 1),
                    xticks=[0, 0.5, 1],
                    yticks=[0, 0.5, 1],
                    xlabel="Emap2lig-Find",
                    ylabel="LigandSeek-Find (CA2)",
                    aspect="equal",
                )
                left, bottom, width, height = ax.get_position().bounds
                colour_axis = fig.add_axes([left + width + 0.012, bottom, 0.010, height], label="<colorbar>")
                colourbar = fig.colorbar(points, cax=colour_axis, ticks=[1, 2, 3, 4])
                colourbar.set_label("Resolution (Å)", fontsize=7.3, labelpad=3)
                colourbar.ax.tick_params(labelsize=7.1, length=2, width=0.6)
                colourbar.outline.set_visible(False)
                colourbar.solids.set_rasterized(False)
                colourbar.solids.set_alpha(1)
                colourbar.solids.set_edgecolor("face")
                colourbar.solids.set_linewidth(0.2)
                counts = block["paired_counts"]
                ax.set_xlabel(
                    f"Emap2lig-Find\nHigher / equal / lower:\n{counts['find_higher']} / {counts['equal']} / {counts['emap_higher']}",
                    fontsize=7.2,
                )
            else:
                ARTISTS.draw_precision_recall(
                    ax, block, ("precision", "recall"), ["Instance-level\nprecision", "Instance-level\nrecall"]
                )
            ax.grid(axis="y", color="#E5E9EC", linewidth=0.45, zorder=0)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7.2, length=2.5, width=0.65)
            ax.set_gid(chr(97 + row * 3 + column))
            ax.annotate(
                chr(97 + row * 3 + column),
                xy=(0, 1),
                xycoords="axes fraction",
                xytext=(-27, 8),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                va="bottom",
                annotation_clip=False,
            )
            title = ("All ligands" if cohort == "full" else "Small molecules") + (" · Dice" if column == 1 else "")
            ax.set_title(title, loc="left", pad=10, fontweight="bold")
    exemptions = []
    # 当前双语备注只由正式作者PPT维护, run.py在候选完成后原样复制; 图元阶段不另存一份图注.
    scene = export_scene(fig, FIGURE, "", build, exemptions)
    (build / "scenes.json").write_text(json.dumps([scene], ensure_ascii=False), encoding="utf-8")
    (build / "manifest.json").write_text(
        json.dumps([{key: value for key, value in scene.items() if key != "shapes"}], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return scene
