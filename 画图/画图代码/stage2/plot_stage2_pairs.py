"""把四张基础评估图排成两张双面板论文插图, 不重新计算冻结预测."""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from plot_stage2 import COLORS, DATA, OUTPUT
from audit_panel_alignment import require_matplotlib_panel_alignment


def save_pair(fig: plt.Figure, name: str) -> None:
    """导出一张上下排列的双面板图, 并按实际绘制矩形比较两面板的左右边界.

    输入参数:
        - fig: Matplotlib Figure, 第一轴为真实受体, 第二轴为 CryoAtom2 受体.
        - name: str, 在画图/formal/stage2 下的文件名前缀.
    """
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        panel_ids=["a", "b"],
        column_groups=[["a", "b"]],
        json_out=str(OUTPUT / f"{name}.alignment.json"),
        overlay_svg=str(OUTPUT / f"{name}.alignment.svg"),
        strict=True,
    )
    fig.savefig(OUTPUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.svg", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.png", bbox_inches="tight", dpi=600)
    fig.savefig(OUTPUT / f"{name}.tiff", bbox_inches="tight", dpi=600)
    plt.close(fig)


def plot_radar_pair() -> None:
    """在同一六轴刻度上展示真实受体和 CryoAtom2 条件.

    数据:
        - DATA["radar"]: 两种受体条件下四个模型的前景 F1 与各类别身份正确数/支持数.
        - DATA["radar"]["emerald_small_known_site"]: 另一组真实小分子位点中至少一个身份有分数的正确数/位点数.

    产物:
        - stage2_radar_pair.{pdf,svg,png,tiff}: 上下两个受体条件, a/b 面板使用同一六轴顺序和径向刻度.
    """
    # 六轴自顶端顺时针排列；糖类与小分子交换位置，其余四轴不变。
    keys = ("overall", "small", "sugar", "f1", "metal", "peptide")
    labels = ("Overall SMILES", "Small molecule", "Sugar", "Foreground F1", "Metal ion", "Peptide")
    display_names = {
        "strongest-1": "strongest",
        "density_only-106": "voxel-only",
        "density_only-0": "density-only",
        "pocket_only-0": "pocket-only",
    }
    angles = np.linspace(0, 2 * np.pi, len(keys), endpoint=False)
    closed_angles = np.r_[angles, angles[0]]
    fig = plt.figure(figsize=(7.1, 6.5))
    axes = [
        fig.add_axes([0.07, 0.60, 0.60, 0.34], projection="polar"),
        fig.add_axes([0.07, 0.09, 0.60, 0.34], projection="polar"),
    ]

    for panel, (condition, title, ax) in enumerate(
        zip(("real", "cryo"), ("Real receptor", "CryoAtom2 receptor"), axes),
    ):
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_rlim(20, 100)
        ax.set_rticks([50, 90, 100])
        ax.set_yticklabels(["50", "90", "100"], fontsize=6.2, color="#5A6570")
        ax.set_rlabel_position(15)
        ax.set_xticks(angles)
        tick_labels = list(labels)
        tick_labels[1] = ""
        ax.set_xticklabels(tick_labels, fontsize=7)
        ax.tick_params(axis="x", pad=9)
        # 右上角的“小分子”比其他轴标题长，单独移出外环以免压住轮廓。
        ax.annotate(
            labels[1], xy=(angles[1], 100), xytext=(16, -7),
            textcoords="offset points", ha="left", va="center", fontsize=7,
        )
        ax.grid(color="#D9E0E4", linewidth=0.65)
        ax.spines["polar"].set_color("#9CA7AF")

        for model, metrics in DATA["radar"][condition].items():
            scores = np.array([100 * metrics[key][0] / metrics[key][1] for key in keys])
            ax.plot(
                closed_angles, np.r_[scores, scores[0]],
                color=COLORS[model], linewidth=1.5, marker="o", markersize=2.5,
                label=display_names[model],
            )

        scored = DATA["radar"]["emerald_small_known_site"][condition]
        ax.scatter(
            [angles[1]], [100 * scored[0] / scored[1]], s=42,
            marker="D", color=COLORS["EMERALD-ID"], edgecolor="white",
            linewidth=0.7, zorder=10, label="EMERALD-ID",
        )
        fig.text(0.04, 0.97 if panel == 0 else 0.50, f"{'ab'[panel]}",
                 fontsize=8.5, fontweight="bold", color="#233443")
        fig.text(0.067, 0.97 if panel == 0 else 0.50, title,
                 fontsize=8.5, fontweight="bold", color="#233443")

    for ax, legend_y in zip(axes, (0.72, 0.23)):
        handles, legend_labels = ax.get_legend_handles_labels()
        fig.legend(
            handles, legend_labels,
            loc="center left", bbox_to_anchor=(0.72, legend_y),
            fontsize=7, handlelength=2.0, labelspacing=1.0,
        )
    save_pair(fig, "stage2_radar_pair")


def plot_categories_pair() -> None:
    """按 PDB 内候选 SMILES 数比较 strongest-1 的类别准确率.

    数据:
        - DATA["strongest_by_candidate_smiles_count"]: (5, 2) 的类别计数, 五组依次为 1、2、3、4、至少 5 种身份, 末轴为正确数和支持数.

    产物:
        - stage2_strongest_pair.{pdf,svg,png,tiff}: 上下两个受体条件, a/b 面板共用类别颜色和百分比坐标.
    """
    fig, axes = plt.subplots(2, 1, figsize=(7.1, 6.1))
    fig.subplots_adjust(left=0.11, right=0.70, top=0.92, bottom=0.10, hspace=0.38)
    x = np.arange(1, 6)
    categories = (
        ("small", "Small molecule"), ("sugar", "Sugar"),
        ("metal", "Metal ion"), ("peptide", "Peptide"),
    )

    for panel, (condition, title, ax) in enumerate(
        zip(("real", "cryo"), ("Real receptor", "CryoAtom2 receptor"), axes),
    ):
        grouped = DATA["strongest_by_candidate_smiles_count"][condition]
        for category, display in categories:
            counts = np.asarray(grouped[category], dtype=int)
            accuracy = np.divide(
                100 * counts[:, 0], counts[:, 1],
                out=np.full(5, np.nan), where=counts[:, 1] > 0,
            )
            ax.plot(x, accuracy, marker="o", markersize=3.7, linewidth=1.7,
                    color=COLORS[category], label=display)
        ax.set_xlim(0.8, 5.2)
        ax.set_ylim(0, 104)
        ax.set_xticks(x, ["1", "2", "3", "4", "≥5"])
        ax.set_yticks(np.arange(0, 101, 20))
        ax.set_ylabel("SMILES matching accuracy (%)", fontsize=7.5)
        ax.set_title(f"{'ab'[panel]}  strongest · {title}",
                     loc="left", fontsize=9, fontweight="bold", pad=10)
        ax.grid(axis="y", color="#DDE3E6", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)

    axes[1].set_xlabel("Candidate SMILES per PDB", fontsize=7.5, labelpad=8)
    for ax, legend_y in zip(axes, (0.72, 0.27)):
        handles, legend_labels = ax.get_legend_handles_labels()
        fig.legend(
            handles, legend_labels,
            loc="center left", bbox_to_anchor=(0.73, legend_y), fontsize=7.5,
            handlelength=2.0, labelspacing=1.0,
        )
    save_pair(fig, "stage2_strongest_pair")


def main() -> None:
    """按同一配色生成图 4 和图 5 所需的两个双面板文件."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })
    plot_radar_pair()
    plot_categories_pair()


if __name__ == "__main__":
    main()
