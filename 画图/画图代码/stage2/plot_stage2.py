"""从冻结计数绘制 Stage2 的六张论文结果图。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


SKILL_SCRIPTS = Path.home() / ".codex" / "skills" / "nature-figure" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parents[1] / "formal" / "stage2"
DATA = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))

COLORS = {
    "strongest-1": "#BE493B",
    "density_only-106": "#265B8A",
    "density_only-0": "#438D79",
    "pocket_only-0": "#8A6D9B",
    "EMERALD-ID": "#B46932",
    "small": "#265B8A",
    "sugar": "#8A6D9B",
    "metal": "#438D79",
    "peptide": "#B46932",
}


def save_figure(fig: plt.Figure, name: str) -> None:
    """导出同一张图的可编辑矢量与论文插图位图。

    输入参数:
        - fig: Matplotlib Figure; 已完成布局的单面板结果图。
        - name: str; 不含扩展名的稳定图名，决定 OUTPUT 下的文件名前缀。
    """
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        json_out=str(OUTPUT / f"{name}.alignment.json"),
        overlay_svg=str(OUTPUT / f"{name}.alignment.svg"),
        strict=True,
    )
    fig.savefig(OUTPUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.svg", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.png", bbox_inches="tight", dpi=600)
    fig.savefig(OUTPUT / f"{name}.tiff", bbox_inches="tight", dpi=600)
    plt.close(fig)


def plot_radar(condition: str, label: str) -> None:
    """比较同一受体条件下四个 Matcher 变体的六项完整测试指标。

    输入参数:
        - condition: str; data.json 的 real 或 cryo 键。
        - label: str; 写入图内的英文受体条件名称。
    """
    keys = ("f1", "overall", "small", "sugar", "metal", "peptide")
    labels = (
        "Foreground F1",
        "Overall SMILES",
        "Small molecule",
        "Sugar",
        "Metal ion",
        "Peptide",
    )
    angles = np.linspace(0, 2 * np.pi, len(keys), endpoint=False)
    closed_angles = np.r_[angles, angles[0]]
    fig = plt.figure(figsize=(7.1, 5.15))
    ax = fig.add_axes([0.10, 0.12, 0.59, 0.79], projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rlim(30, 100)
    ax.set_rticks([50, 70, 90, 100])
    ax.set_yticklabels(["50", "70", "90", "100"], color="#5A6570", fontsize=7)
    ax.set_rlabel_position(15)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.grid(color="#D9E0E4", linewidth=0.7)
    ax.spines["polar"].set_color("#9CA7AF")
    ax.tick_params(axis="x", pad=20)

    # 每个分数严格由 data.json 中的正确数和支持数取得；F1 单独保存为浮点值。
    for model, metrics in DATA["radar"][condition].items():
        scores = np.array([100 * metrics[key][0] / metrics[key][1] for key in keys])
        ax.plot(
            closed_angles,
            np.r_[scores, scores[0]],
            color=COLORS[model], linewidth=1.8, marker="o", markersize=3.5,
            label=model.replace("_", " "),
        )

    emerald = DATA["radar"]["emerald_small_known_site"][condition]
    ax.scatter(
        [angles[2]], [100 * emerald[0] / emerald[1]], s=70,
        marker="D", facecolor=COLORS["EMERALD-ID"], edgecolor="white",
        linewidth=0.9, zorder=10, label="EMERALD-ID*",
    )
    fig.text(0.755, 0.87, label, fontsize=12, fontweight="bold", color="#233443")
    fig.legend(
        loc="center left", bbox_to_anchor=(0.72, 0.53), frameon=False,
        fontsize=8, handlelength=2.2, labelspacing=1.05,
    )
    fig.text(
        0.745, 0.20, "*Small-molecule scored sites only\n  (different test population)",
        fontsize=6.9, color="#58636D", linespacing=1.45,
    )
    fig.text(0.745, 0.10, "Radial axis: 30–100%", fontsize=7.2, color="#58636D")
    save_figure(fig, f"stage2_radar_{condition}")


def plot_strongest_categories(condition: str, label: str) -> None:
    """按 PDB 内候选 SMILES 数绘制 strongest-1 的分层身份准确率。

    输入参数:
        - condition: str; data.json 的 real 或 cryo 键。
        - label: str; 写入图内的英文受体条件名称。
    """
    grouped = DATA["strongest_by_candidate_smiles_count"][condition]
    x = np.arange(1, 6)
    fig, ax = plt.subplots(figsize=(7.1, 4.4))
    fig.subplots_adjust(left=0.11, right=0.72, top=0.86, bottom=0.17)
    for category, display in (
        ("small", "Small molecule"), ("sugar", "Sugar"),
        ("metal", "Metal ion"), ("peptide", "Peptide"),
    ):
        counts = np.asarray(grouped[category], dtype=int)
        accuracy = np.divide(
            100 * counts[:, 0], counts[:, 1],
            out=np.full(5, np.nan), where=counts[:, 1] > 0,
        )
        ax.plot(
            x, accuracy, marker="o", markersize=5, linewidth=2,
            color=COLORS[category], label=f"{display} (n={counts[:, 1].sum()})",
        )
    ax.set_xlim(0.8, 5.2)
    ax.set_ylim(0, 104)
    ax.set_xticks(x, ["1", "2", "3", "4", "≥5"])
    ax.set_yticks(np.arange(0, 101, 20))
    ax.set_xlabel("Candidate SMILES per PDB", labelpad=8)
    ax.set_ylabel("SMILES matching accuracy (%)")
    ax.set_title(f"strongest-1 · {label}", loc="left", fontweight="bold", pad=13)
    ax.grid(axis="y", color="#DDE3E6", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(bbox_to_anchor=(1.02, 0.78), loc="upper left", frameon=False, fontsize=8)
    fig.text(0.73, 0.29, "One peptide candidate\nin a single-identity PDB", fontsize=7.2, color="#58636D")
    save_figure(fig, f"stage2_strongest_categories_{condition}")


def plot_known_site_comparison(condition: str, label: str) -> None:
    """比较 density_only-106 与 EMERALD-ID 的固定及有评分分母结果。

    输入参数:
        - condition: str; data.json 的 real 或 cryo 键。
        - label: str; 写入图内的英文受体条件名称。
    """
    data = DATA["small_known_site"][condition]
    support = np.asarray(DATA["small_known_site"]["group_support"], dtype=int)
    x = np.arange(1, 5)
    fig, ax = plt.subplots(figsize=(7.1, 4.4))
    fig.subplots_adjust(left=0.11, right=0.71, top=0.84, bottom=0.19)
    for prefix, name, color in (
        ("matcher", "density only 106", COLORS["density_only-106"]),
        ("emerald", "EMERALD-ID", COLORS["EMERALD-ID"]),
    ):
        correct = np.asarray(data[f"{prefix}_correct"], dtype=int)
        scored = np.asarray(data[f"{prefix}_scored"], dtype=int)
        ax.plot(x, 100 * correct / support, color=color, linewidth=2.2,
                marker="o", markersize=5, label=f"{name} · all sites")
        ax.plot(x, 100 * correct / scored, color=color, linewidth=1.8,
                linestyle=(0, (4, 2.5)), marker="s", markersize=4,
                markerfacecolor="white", label=f"{name} · scored sites")
    ax.set_xlim(0.8, 4.2)
    ax.set_ylim(0, 105)
    ax.set_xticks(x, [f"{n}\nn={count}" for n, count in zip(x, support)])
    ax.set_yticks(np.arange(0, 101, 20))
    ax.set_xlabel("Small-molecule SMILES per PDB", labelpad=8)
    ax.set_ylabel("Top-1 matching accuracy (%)")
    ax.set_title(f"Known-site comparison · {label}", loc="left", fontweight="bold", pad=13)
    ax.grid(axis="y", color="#DDE3E6", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(bbox_to_anchor=(1.02, 0.81), loc="upper left", frameon=False,
              fontsize=7.6, labelspacing=1.1)
    fig.text(0.72, 0.27, "Dashed: at least one\nscored SMILES at the site", fontsize=7.2, color="#58636D")
    save_figure(fig, f"stage2_known_site_{condition}")


def main() -> None:
    """检查计数加和，并以相同绘图契约生成两种受体条件的全部图。"""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })
    support = DATA["small_known_site"]["group_support"]
    assert sum(support) == 357
    for condition in ("real", "cryo"):
        grouped = DATA["strongest_by_candidate_smiles_count"][condition]
        for category, key in (("small", "small"), ("sugar", "sugar"),
                              ("metal", "metal"), ("peptide", "peptide")):
            observed = np.asarray(grouped[category], dtype=int).sum(axis=0)
            expected = DATA["radar"][condition]["strongest-1"][key]
            assert observed.tolist() == expected
        known = DATA["small_known_site"][condition]
        assert sum(known["matcher_correct"]) == (301 if condition == "real" else 303)
        assert sum(known["emerald_correct"]) == (233 if condition == "real" else 263)
        assert sum(known["emerald_scored"]) == DATA["radar"]["emerald_small_known_site"][condition][1]
        label = "Real receptor" if condition == "real" else "CryoAtom2 receptor"
        plot_radar(condition, label)
        plot_strongest_categories(condition, label)
        plot_known_site_comparison(condition, label)


if __name__ == "__main__":
    main()
