"""Fig5持有标准Build的全分布小提琴和原百分位显示规则, Fig9/补图3复用.

boxes只消费read_standard_build返回的同轴原值; KDE用全部有效分布, 第10/25/50/75/85百分位独立计算, 不按当前0–10Å画幅裁剪统计成员.
"""

from functools import partial
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde
from TOOLS.ppt.matplotlib_export import panel_title, y_grid

title = partial(panel_title, title_size=6.8, label_size=8, pad=7, label_offset=(-19, 7))
grid = partial(y_grid, color="#E3E7E9", linewidth=0.45)
plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 6,
        "axes.labelsize": 6,
        "xtick.labelsize": 5.6,
        "ytick.labelsize": 5.6,
        "axes.linewidth": 0.6,
        "lines.linewidth": 1,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "xtick.major.size": 2,
        "ytick.major.size": 2,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
C = {
    "GT": "#2F6B9A",
    "CA2": "#D68B3A",
    "Emap2lig": "#529667",
    "official": "#7F8C8D",
    "nodensity": "#8E5EA2",
    "DG": "#2F6B9A",
}


def boxes(ax, data, receptor, protocol, letter):
    """小提琴拟合全部有效值,箱体和精确百分位须独立从全分布计算."""
    ax.set_box_aspect(1)
    for j, pose in enumerate(["top1", "top5", "best50"]):
        for offset, model in [(-0.25, "official"), (0, "nodensity"), (0.25, "DG")]:
            values = data["ablation"][protocol][receptor][model][pose]
            arr = np.asarray([v for v in values if v is not None and np.isfinite(v)])
            pos = j + offset
            col = C[model]
            kde = gaussian_kde(arr)
            y = np.linspace(0, 10, 220)
            density = kde(y)
            normalizer = np.max(kde(np.linspace(0, float(arr.max()), 800)))
            width = density / normalizer * 0.115
            ax.fill_betweenx(y, pos - width, pos + width, color=col, alpha=0.22, lw=0)
            p10, q1, med, q3, p85 = np.quantile(arr, [0.10, 0.25, 0.50, 0.75, 0.85])
            stat = {"whislo": p10, "q1": q1, "med": med, "q3": q3, "whishi": p85, "fliers": []}
            art = ax.bxp(
                [stat],
                positions=[pos],
                widths=0.15,
                patch_artist=True,
                showfliers=False,
                manage_ticks=False,
                boxprops={"facecolor": col, "edgecolor": col, "alpha": 0.65, "linewidth": 0.6},
                whiskerprops={"color": col, "linewidth": 0.7},
                capprops={"color": col, "linewidth": 0.7},
                medianprops={"color": "white", "linewidth": 1.2},
            )
            ax.text(
                pos,
                -0.14,
                f"{med:.2f}",
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=5.2,
                color=col,
                fontweight="bold",
                clip_on=False,
            )
    ax.axhline(1, color="#777777", ls=":", lw=0.65)
    ax.axhline(2, color="#333333", ls="--", lw=0.7)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(0, 10)
    ax.set_xticks(range(3), ["Top-1", "Top-5", "Best of 50"])
    ax.set_yticks([0, 2, 4, 6, 8, 10])
    ax.set_ylabel("Ligand RMSD (Å)")
    grid(ax)
    ax.set_xlabel("Median RMSD (Å)", fontsize=5.5, labelpad=17)
    title(ax, letter, f"Build ablation ({receptor})")
    ax.legend(
        handles=[
            Patch(facecolor=C[m], alpha=0.65, label=l)
            for m, l in [
                ("official", "PocketXMol-official"),
                ("nodensity", "PocketXMol–simple fine-tune"),
                ("DG", "DG-PocketXMol"),
            ]
        ],
        loc="upper right",
        fontsize=5.4,
        borderpad=0.3,
        handlelength=1.2,
        labelspacing=0.35,
    )
