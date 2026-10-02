"""从冻结逐实例 RMSD 绘制两张 Stage3 定量图的印刷预览与统计摘要。

入口 ``main`` 读取同目录 ``data.json``; 在 ``画图/formal/stage3`` 输出两张 PDF、SVG、
PNG 和 TIFF, 以及每组的有效数、中位数、四分位数和 5–95 百分位数。
PowerPoint 成品由同目录的原生对象脚本读取同一份 ``data.json`` 生成。
"""

import hashlib
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Rectangle


PAPER = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent / "data.json"
OUTPUT = PAPER / "画图/formal/stage3"
QA = PAPER / "temp/stage3-figure-qa"
sys.path.insert(0, "C:/Users/15919/.codex/skills/nature-figure/scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment


COLORS = {"GT": "#32887D", "CA2": "#5575B2", "Build": "#B17642"}
mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)


def draw_distribution(ax, rows, field, x, color, cap=None):
    """画出同一实验组全部有效配体实例及中位数、四分位数、5–95 百分位数。

    ``rows`` 的每个实例含 ``pdb_id``、``occurrence_id``、``top1``、``best``;
    ``field`` 指定其中一个单位为 Å 的 RMSD。缺少姿态的 null 不造数值点, 但在
    ``data.json`` 中保留。横向抖动仅用于区分重叠的实例, 不改变纵坐标或汇总统计。
    返回有效实例数及五个分位数, 供图注核对。
    """
    valid = [row for row in rows if row[field] is not None]
    values = np.array([row[field] for row in valid], dtype=float)
    assert np.all(values > 0), "对数 RMSD 轴只接受正值"
    # (N,), 为同一实验组 N 个实例计算稳定的横向抖动; SHA-256 只影响显示位置。
    offsets = np.array(
        [
            (int.from_bytes(hashlib.sha256(f"{row['pdb_id']}/{row['occurrence_id']}".encode()).digest()[:4], "big") / 2**32 - 0.5) * 0.18
            for row in valid
        ]
    )
    # 完整集的大于 50 Å 观测值显示在顶端 50+ 区；分位数仍由原始值计算。
    shown = np.where(values > cap, 80, values) if cap is not None else values
    ordinary = values <= cap if cap is not None else np.ones(len(values), dtype=bool)
    ax.scatter(x + offsets[ordinary], shown[ordinary], s=2.2, c=color,
               alpha=0.34, linewidths=0, rasterized=False)
    if cap is not None:
        ax.scatter(x + offsets[~ordinary], shown[~ordinary], s=13, marker="^",
                   c=color, alpha=0.8, linewidths=0, rasterized=False)
    quantiles = np.quantile(values, [0.05, 0.25, 0.5, 0.75, 0.95])
    ax.vlines(x, quantiles[0], quantiles[4], color=color, linewidth=0.8, zorder=4)
    ax.hlines([quantiles[0], quantiles[4]], x - 0.055, x + 0.055, color=color, linewidth=0.8, zorder=4)
    ax.add_patch(Rectangle((x - 0.075, quantiles[1]), 0.15, quantiles[3] - quantiles[1], facecolor="white", edgecolor=color, linewidth=1.0, zorder=5))
    ax.hlines(quantiles[2], x - 0.075, x + 0.075, color=color, linewidth=1.6, zorder=6)
    return {"n": len(values), "p05": float(quantiles[0]), "p25": float(quantiles[1]), "median": float(quantiles[2]), "p75": float(quantiles[3]), "p95": float(quantiles[4]), "max": float(values.max())}


def save_figure(fig, name):
    """在最终版式下检查面板对齐, 再保存可选文字的 PDF/SVG 和高分辨率预览。"""
    QA.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        json_out=str(QA / f"{name}.alignment.json"),
        overlay_svg=str(QA / f"{name}.alignment.svg"),
        tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(OUTPUT / f"{name}.pdf")
    fig.savefig(OUTPUT / f"{name}.svg")
    fig.savefig(OUTPUT / f"{name}.png", dpi=300)
    fig.savefig(OUTPUT / f"{name}.tiff", dpi=600)
    plt.close(fig)


def main():
    """按完整 446 实例与 237 个共同可评价实例分别绘制两组图。"""
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    full = {(item["model"], item["receptor"], item["protocol"]): item["rows"] for item in data["series"]}
    subset = {
        (row["pdb_id"], row["occurrence_id"])
        for row in data["build"]
        if row["top1"] is not None and row["best"] is not None
    }
    stats = {"full": {}, "find_hit": {}}

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.35), sharex=True)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.12, top=0.91, hspace=0.30)
    for ax, field, letter, title in zip(
        axes, ("top1", "best"), ("a", "b"), ("Top-1 pose", "Best of 50")
    ):
        for protocol_index, protocol in enumerate(("C0", "E")):
            for model_index, model in enumerate(("official", "local_cov")):
                base = protocol_index * 2 + model_index
                for receptor, offset in (("GT", -0.17), ("CA2", 0.17)):
                    key = f"{model}_{receptor}_{protocol}"
                    stats["full"].setdefault(key, {})[field] = draw_distribution(
                        ax, full[(model, receptor, protocol)], field,
                        base + offset, COLORS[receptor], cap=50
                    )
        ax.set_yscale("log")
        ax.set_ylim(0.15, 95)
        ax.set_yticks([0.2, 0.5, 1, 2, 3, 5, 10, 50, 80],
                      labels=["0.2", "0.5", "1", "2", "3", "5", "10", "50", "50+"])
        ax.set_xticks(range(4), labels=["Official", "Tuned", "Official", "Tuned"])
        ax.set_xlim(-0.52, 3.52)
        ax.set_ylabel("RMSD (Å)")
        ax.axvline(1.5, color="#B8BEC3", linewidth=0.7)
        ax.axhline(2, color="#C7CFD4", linewidth=0.6, linestyle=(0, (3, 2)))
        ax.axhline(3, color="#C7CFD4", linewidth=0.6, linestyle=(0, (3, 2)))
        ax.text(0.25, 1.04, "Centre pocket · C0", ha="center", transform=ax.transAxes, fontsize=7)
        ax.text(0.75, 1.04, "Envelope pocket · E", ha="center", transform=ax.transAxes, fontsize=7)
        ax.text(-0.075, 1.16, letter, transform=ax.transAxes, fontsize=8, fontweight="bold")
        ax.text(-0.025, 1.16, title, transform=ax.transAxes, fontsize=7)
    axes[0].legend(handles=[Patch(facecolor=COLORS["GT"], label="GT receptor"),
                            Patch(facecolor=COLORS["CA2"], label="CryoAtom2 receptor")],
                   frameon=False, ncol=2, loc="upper right", fontsize=6.5,
                   bbox_to_anchor=(0.99, 1.29))
    save_figure(fig, "stage3_official_tuned")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25), sharey=False)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.24, top=0.84, wspace=0.26)
    for ax, field, letter, title in zip(axes, ("top1", "best"), ("a", "b"), ("Top-1", "Best of 50")):
        groups = [
            ("local_cov-C · GT", [row for row in full[("local_cov", "GT", "C0")] if (row["pdb_id"], row["occurrence_id"]) in subset], COLORS["GT"]),
            ("local_cov-C · CA2", [row for row in full[("local_cov", "CA2", "C0")] if (row["pdb_id"], row["occurrence_id"]) in subset], COLORS["CA2"]),
            ("Emap2lig-Build", [row for row in data["build"] if (row["pdb_id"], row["occurrence_id"]) in subset], COLORS["Build"]),
        ]
        for index, (label, rows, color) in enumerate(groups):
            stats["find_hit"].setdefault(label, {})[field] = draw_distribution(ax, rows, field, index, color)
        ax.set_yscale("log")
        ax.set_ylim(0.2, 30)
        ax.set_yticks([0.2, 0.5, 1, 2, 5, 10, 20], labels=["0.2", "0.5", "1", "2", "5", "10", "20"])
        ax.set_xlim(-0.42, 2.42)
        ax.set_xticks(range(3), labels=["local_cov-C\nGT", "local_cov-C\nCryoAtom2", "Emap2lig-\nBuild"])
        ax.axhline(2, color="#C7CFD4", linewidth=0.6, linestyle=(0, (3, 2)))
        ax.axhline(3, color="#C7CFD4", linewidth=0.6, linestyle=(0, (3, 2)))
        ax.set_ylabel("RMSD (Å)")
        ax.text(-0.09, 1.08, letter, transform=ax.transAxes, fontsize=8, fontweight="bold")
        ax.text(0.02, 1.08, title, transform=ax.transAxes, fontsize=7)
    save_figure(fig, "stage3_find_hit_head_to_head")
    (OUTPUT / "summary.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
