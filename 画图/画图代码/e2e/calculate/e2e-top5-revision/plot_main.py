"""沿作者 2×2 模板绘制 E2E Top-5 主图, 数据只读取同次准备的 master.json.

plot_e2e_figure 将全配体 Find/Match、小分子正确身份比较和实际三阶段完成度汇总为四面板.
输出在 FIGURE_BUILD_ROOT/figures 中, 包含同源 SVG、PDF、PNG、最终物理尺寸与对齐报告; 不修改正式 PPT.
配色、图型、分区和图例沿作者模板, 仅作最终版心的字形与留白适配.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from pathlib import Path
import sys
from matplotlib.text import Text
from matplotlib.collections import Collection
from matplotlib.patches import Patch as MplPatch
from matplotlib.lines import Line2D as MplLine

sys.path.insert(0, str(Path.home() / ".codex/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/e2e_top5_20261102/build"
OUT_DIR = BUILD / "figures"
INTER_DIR = OUT_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_SCALE = (159.262 / 25.4) / 11.8

INK = "#243442"
MUTED = "#5A6B78"
GRID = "#E3E9ED"

C_EMAP = "#9A6324"       # Warm rich brown: Emap2lig (density-only baseline)
C_EMAP_MID = "#C49358"   # Light/medium brown for 300% budget line in Panel b
C_EMAP_LIGHT = "#DFBE9F" # Soft tan fill

C_CA2 = "#4860B8"        # Cobalt/indigo blue: LigandSeek (CA2 receptor)
C_CA2_MID = "#8294DF"    # Light/medium blue for 300% budget line in Panel b
C_CA2_LIGHT = "#AEBCEF"  # Soft periwinkle fill

C_GT = "#0D8A82"         # Emerald-teal: LigandSeek (GT receptor)
C_GT_MID = "#58B8B1"     # Light/medium teal for 300% budget line in Panel b
C_GT_LIGHT = "#94D4CF"   # Soft mint-aqua fill

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 9.8 * EXPORT_SCALE,
    "axes.linewidth": 0.7,
    "axes.edgecolor": INK,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})


def panel_header(ax, letter, title, x_offset=-0.115, fontsize=10.8 * EXPORT_SCALE):
    ax.set_title(title, loc="left", fontsize=fontsize, fontweight="bold", pad=7.0 * EXPORT_SCALE, color=INK)
    ax.text(x_offset, 1.17, letter, transform=ax.transAxes, fontsize=10.5 * EXPORT_SCALE, fontweight="bold", va="top", ha="left", color=INK)


def plot_e2e_figure(master, pose_pool="top_5", out_prefix="e2e-main-top5", a_x_stretch=1.0):
    """
    pose_pool:
      - "best_of_50": uses pose50 (Best-of-50 poses) as the multi-pose candidate pool
      - "top_5":      uses pose5  (Top-5 poses)      as the multi-pose candidate pool
    """
    # a_x_stretch仅拉开预算的横向显示距离；保留原图兼容值1，不改变预算标值和纵向数据。
    assert pose_pool in ("best_of_50", "top_5")
    pose_key = "pose50" if pose_pool == "best_of_50" else "pose5"
    pose_label = "Best-of-50 poses" if pose_pool == "best_of_50" else "Top-5 poses"

    panels = master["panels"]
    summaries = master["summaries"]

    fig, axes = plt.subplots(2, 2, figsize=(11.8 * EXPORT_SCALE, 8.3 * EXPORT_SCALE), dpi=300)
    plt.subplots_adjust(left=0.065, right=0.975, top=0.93, bottom=0.125, wspace=0.31, hspace=0.34)

    ax_a = axes[0, 0]
    panel_header(ax_a, "a", "All ligands: detection and identification\n(179 PDBs, 2,502 instances)")

    specs_a = [
        ("find_full_GT",      C_GT,   "--", 1.6, False, -2.2),
        ("full_GT",           C_GT,   "-",  2.2, True,  +2.2),
        ("find_full_CA2",     C_CA2,  "--", 1.6, False, -2.2),
        ("full_CA2",          C_CA2,  "-",  2.2, True,  +2.2),
        ("find_full_Emap2lig",C_EMAP, "--", 1.75,False,  0.0),
    ]

    for pid, col, ls, lw, is_filled, x_jit in specs_a:
        p = panels[pid]
        poly = p["polyline"]
        if poly.get("is_step", False):
            bx = np.array(poly["budget_percent"])
            my = np.array(poly["mean_percent"])
            ax_a.step(bx * a_x_stretch, my, where="post", color=col, linestyle=ls, linewidth=lw, zorder=4)
        else:
            bx = np.array(poly["mean_x"])
            my = np.array(poly["mean_y"])
            ax_a.plot(bx * a_x_stretch, my, color=col, linestyle=ls, linewidth=lw, zorder=4)

        for b in (50, 100, 200, 300):
            s = summaries[pid][str(b)]
            mval = s["mean"]
            xp = b * a_x_stretch + (x_jit if b in (100, 200, 300) else 0.0)
            if b in (100, 200, 300):
                ax_a.errorbar(
                    xp, mval,
                    yerr=[[mval - s["ci_low"]], [s["ci_high"] - mval]],
                    fmt="none", ecolor=col, elinewidth=0.95, capsize=2.2, capthick=0.9, alpha=0.85, zorder=5
                )
            ax_a.plot(
                xp, mval, marker="o", markersize=5.0,
                markerfacecolor=col if is_filled else "white",
                markeredgecolor=col, markeredgewidth=1.3, zorder=6
            )

    ax_a.text(300 * a_x_stretch + 5, summaries["find_full_GT"]["300"]["mean"] + 2.9, f"{summaries['find_full_GT']['300']['mean']:.1f}% (Find)", fontsize=9.6 * EXPORT_SCALE, color=C_GT, va="center")
    ax_a.text(300 * a_x_stretch + 5, summaries["full_GT"]["300"]["mean"] + 0.7, f"{summaries['full_GT']['300']['mean']:.1f}% (Find+Match)", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=C_GT, va="center")
    ax_a.text(300 * a_x_stretch + 5, summaries["find_full_CA2"]["300"]["mean"] - 0.8, f"{summaries['find_full_CA2']['300']['mean']:.1f}% (Find)", fontsize=9.6 * EXPORT_SCALE, color=C_CA2, va="center")
    ax_a.text(300 * a_x_stretch + 5, summaries["full_CA2"]["300"]["mean"] - 1.6, f"{summaries['full_CA2']['300']['mean']:.1f}% (Find+Match)", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=C_CA2, va="center")
    ax_a.text(300 * a_x_stretch + 5, summaries["find_full_Emap2lig"]["300"]["mean"], f"{summaries['find_full_Emap2lig']['300']['mean']:.1f}% (Find)", fontsize=9.6 * EXPORT_SCALE, color=C_EMAP, va="center")

    ax_a.axvline(100 * a_x_stretch, color="#94A3B8", linestyle=":", linewidth=0.9, zorder=1)
    ax_a.text(100 * a_x_stretch + 3, 7.0, "100% budget\n(1× true count)", fontsize=9.6 * EXPORT_SCALE, color=MUTED, va="bottom")

    ax_a.set_xlim(0, 400)
    ax_a.set_ylim(0, 84)
    ax_a.set_yticks(range(0, 81, 10))
    ax_a.set_xticks(np.array([0, 50, 100, 200, 300]) * a_x_stretch)
    ax_a.set_xticklabels(["0%", "50%", "100%", "200%", "300%"])
    ax_a.set_xlabel("Relative candidate attempt budget (% of true instances per PDB)")
    ax_a.set_ylabel("Per-PDB mean completion (%)")
    ax_a.grid(axis="y", color=GRID, linewidth=0.55, zorder=0)

    loc_a = [
        Line2D([0], [0], color=INK, linestyle="-", linewidth=2.0, marker="o", markersize=5.0,
               markerfacecolor=INK, markeredgecolor=INK, label="Find + Match (location + identity)"),
        Line2D([0], [0], color=INK, linestyle="--", linewidth=1.6, marker="o", markersize=5.0,
               markerfacecolor="white", markeredgecolor=INK, markeredgewidth=1.3, label="Find only (location detection)"),
    ]
    ax_a.legend(handles=loc_a, loc="upper left", frameon=True, facecolor="white", edgecolor="#E2E8F0", framealpha=0.94, fontsize=9.6 * EXPORT_SCALE, handlelength=2.4)

    ax_b = axes[0, 1]
    panel_header(ax_b, "b", "Small molecules: detection and pose reconstruction\n(Find + Build)")

    rows_b = [
        ("2.0", "Emap2lig", "100", 10.5, C_EMAP,     True),
        ("2.0", "Emap2lig", "300",  9.6, C_EMAP_MID, False),
        ("2.0", "CA2",      "100",  8.3, C_CA2,      True),
        ("2.0", "CA2",      "300",  7.4, C_CA2_MID,  False),
        ("2.0", "GT",       "100",  6.1, C_GT,       True),
        ("2.0", "GT",       "300",  5.2, C_GT_MID,   False),
        ("3.0", "Emap2lig", "100",  3.0, C_EMAP,     True),
        ("3.0", "Emap2lig", "300",  2.15, C_EMAP_MID, False),
        ("3.0", "CA2",      "100",  1.0, C_CA2,      True),
        ("3.0", "CA2",      "300",  0.1, C_CA2_MID,  False),
        ("3.0", "GT",       "100", -1.2, C_GT,       True),
        ("3.0", "GT",       "300", -2.1, C_GT_MID,   False),
    ]

    ax_b.axhspan(4.35, 12.5, color="#F8FAFC", zorder=0)
    ax_b.axhline(4.35, color="#64748B", linestyle="--", linewidth=1.0, zorder=2)
    ax_b.text(1.5, 11.7, "Strict threshold: RMSD < 2 Å", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=INK, va="center")
    ax_b.text(1.5,  3.9, "Relaxed threshold: RMSD < 3 Å", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=INK, va="center")

    for rmsd_s, dom, b_str, yp, col, is_100 in rows_b:
        v_top1 = summaries[f"assume_{dom}_pose1_rmsd{rmsd_s}"][b_str]["mean"]
        v_pool = summaries[f"assume_{dom}_{pose_key}_rmsd{rmsd_s}"][b_str]["mean"]
        lw = 2.6 if is_100 else 2.0
        ax_b.plot([v_top1, v_pool], [yp, yp], color=col, linewidth=lw, linestyle="-", zorder=3)
        ax_b.plot(v_top1, yp, marker="o", markersize=6.2, markerfacecolor=col, markeredgecolor="white", markeredgewidth=0.6, zorder=5)
        ax_b.plot(v_pool, yp, marker="o", markersize=6.2, markerfacecolor="white", markeredgecolor=col, markeredgewidth=1.6, zorder=5)
        ax_b.text(v_top1 - 1.65, yp, f"{v_top1:.1f}%", fontsize=9.6 * EXPORT_SCALE, color=col, ha="right", va="center", fontweight="bold" if is_100 else "normal")
        ax_b.text(v_pool + 1.65, yp, f"{v_pool:.1f}%", fontsize=9.6 * EXPORT_SCALE, color=col, ha="left", va="center", fontweight="bold" if is_100 else "normal")

    ax_b.set_yticks([10.05, 7.85, 5.65, 2.575, 0.55, -1.65])
    ax_b.set_yticklabels(
        ["Emap2lig", "LigandSeek (CA2)", "LigandSeek (GT)", "Emap2lig", "LigandSeek (CA2)", "LigandSeek (GT)"],
        fontsize=9.6 * EXPORT_SCALE, rotation=32, ha="right", va="center"
    )
    ax_b.set_xlim(0, 84)
    ax_b.set_xticks(range(0, 81, 10))
    ax_b.set_ylim(-3.2, 12.5)
    ax_b.set_xlabel("Per-PDB mean Find + Build completion (%, oracle SMILES)")
    ax_b.grid(axis="x", color=GRID, linewidth=0.55, zorder=0)

    loc_b = [
        Line2D([0], [0], color=INK, linewidth=2.5, label="Dark line: 100% budget"),
        Line2D([0], [0], color="#8896A6", linewidth=2.0, label="Light line: 300% budget"),
        Line2D([0], [0], color="none", marker="o", markersize=5.8, markerfacecolor=INK, markeredgecolor=INK, label="Filled circle: Top-1 pose"),
        Line2D([0], [0], color="none", marker="o", markersize=5.8, markerfacecolor="white", markeredgecolor=INK, markeredgewidth=1.5, label=f"Open circle: {pose_label}"),
    ]
    ax_b.legend(handles=loc_b, loc="lower left", frameon=True, facecolor="white", edgecolor="#E2E8F0", framealpha=0.95, fontsize=9.6 * EXPORT_SCALE, ncol=1)

    for ax_cd, letter, dom, title_str, c_dark, c_light in [
        (axes[1, 0], "c", "CA2", "Small molecules: automated end-to-end modelling\n(CA2)", C_CA2, C_CA2_LIGHT),
        (axes[1, 1], "d", "GT",  "Small molecules: automated end-to-end modelling\n(GT)",  C_GT,  C_GT_LIGHT),
    ]:
        panel_header(ax_cd, letter, title_str)
        x_100 = np.array([0, 1, 2, 3], dtype=float)
        x_300 = np.array([4.8, 5.8, 6.8, 7.8], dtype=float)
        bw = 0.78

        ax_cd.axvspan(3.9, 8.6, color="#F8FAFC", zorder=0)
        ax_cd.plot([3.9, 3.9], [0, 84.5], color="#64748B", linestyle="--", linewidth=1.0, zorder=2)
        ax_cd.text(1.5, 88.0, "100% attempt budget", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=INK, ha="center")
        ax_cd.text(6.3, 88.0, "300% attempt budget", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=INK, ha="center")

        for xs, b_str in [(x_100, "100"), (x_300, "300")]:
            v_find = summaries[f"find_small_{dom}_poseNone_rmsdNone"][b_str]["mean"]
            v_fm   = summaries[f"find_match_small_{dom}"][b_str]["mean"]
            v_b3_1 = summaries[f"actual_{dom}_pose1_rmsd3.0"][b_str]["mean"]
            v_b3_p = summaries[f"actual_{dom}_{pose_key}_rmsd3.0"][b_str]["mean"]
            v_b2_1 = summaries[f"actual_{dom}_pose1_rmsd2.0"][b_str]["mean"]
            v_b2_p = summaries[f"actual_{dom}_{pose_key}_rmsd2.0"][b_str]["mean"]

            for idx_pre, v_pre in [(0, v_find), (1, v_fm)]:
                ax_cd.bar(xs[idx_pre], v_pre, width=bw, color=c_light, alpha=0.42, edgecolor=c_dark, linewidth=1.1, linestyle="--", zorder=3)
                ax_cd.text(xs[idx_pre], v_pre + 2.6, f"{v_pre:.1f}%", fontsize=9.6 * EXPORT_SCALE, color=INK, fontweight="bold", ha="center", va="bottom")

            ax_cd.bar(xs[2], v_b3_1, width=bw, color=c_dark, edgecolor="white", linewidth=0.5, zorder=3)
            ax_cd.bar(xs[2], v_b3_p - v_b3_1, bottom=v_b3_1, width=bw, color=c_light, edgecolor=c_dark, linewidth=0.6, zorder=3)
            ax_cd.text(xs[2], v_b3_1 / 2.0, f"{v_b3_1:.1f}%", fontsize=9.6 * EXPORT_SCALE, color="white", fontweight="bold", ha="center", va="center", zorder=5)
            ax_cd.text(xs[2], v_b3_p + 2.6, f"{v_b3_p:.1f}%", fontsize=9.6 * EXPORT_SCALE, color=c_dark, fontweight="bold", ha="center", va="bottom")

            ax_cd.bar(xs[3], v_b2_1, width=bw, color=c_dark, edgecolor="white", linewidth=0.5, zorder=3)
            ax_cd.bar(xs[3], v_b2_p - v_b2_1, bottom=v_b2_1, width=bw, color=c_light, edgecolor=c_dark, linewidth=0.6, zorder=3)
            ax_cd.text(xs[3], v_b2_1 / 2.0, f"{v_b2_1:.1f}%", fontsize=9.6 * EXPORT_SCALE, color="white", fontweight="bold", ha="center", va="center", zorder=5)
            ax_cd.text(xs[3], v_b2_p + 2.6, f"{v_b2_p:.1f}%", fontsize=9.6 * EXPORT_SCALE, color=c_dark, fontweight="bold", ha="center", va="bottom")

            ax_cd.plot(xs, [v_find, v_fm, v_b3_p, v_b2_p], color=c_dark, linestyle=":", linewidth=1.0, zorder=4)

        ax_cd.set_xticks(list(x_100) + list(x_300))
        ax_cd.set_xticklabels(["Find\nonly", "Find +\nMatch", "E2E\n(<3 Å)", "E2E\n(<2 Å)"] * 2, fontsize=9.6 * EXPORT_SCALE)
        ax_cd.set_xlim(-0.7, 8.5)
        ax_cd.set_ylim(0, 101)
        ax_cd.set_yticks(range(0, 101, 20))
        ax_cd.set_ylabel("Per-PDB mean completion (%)")
        ax_cd.grid(axis="y", color=GRID, linewidth=0.55, zorder=0)

        # Strictly 2 legend items per Sketch 3 ("2个图例即可")
        loc_cd = [
            Patch(facecolor=c_dark, edgecolor="white", label="Top-1 pose"),
            Patch(facecolor=c_light, edgecolor=c_dark, label=pose_label),
        ]
        ax_cd.legend(
            handles=loc_cd, loc="upper center", bbox_to_anchor=(0.5, 1.015), ncol=2,
            frameon=True, facecolor="white", edgecolor="#E2E8F0", framealpha=0.95, fontsize=9.6 * EXPORT_SCALE, columnspacing=1.8
        )

    handles_global = [
        Patch(facecolor=C_EMAP, edgecolor=INK, linewidth=0.6, label="Emap2lig (density-only baseline)"),
        Patch(facecolor=C_CA2,  edgecolor=INK, linewidth=0.6, label="LigandSeek · CA2 (CryoAtom2-reconstructed receptor)"),
        Patch(facecolor=C_GT,   edgecolor=INK, linewidth=0.6, label="LigandSeek · GT (deposited receptor)"),
    ]
    leg = fig.legend(
        handles=handles_global, loc="lower center", bbox_to_anchor=(0.5, 0.012), ncol=3,
        frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.6 * EXPORT_SCALE,
        handlelength=1.5, handleheight=0.9, columnspacing=2.2
    )
    leg.get_frame().set_linewidth(0.6)

    # 源画布已经采用最终物理尺寸, 字体在创建时设置, 其余长度按同一比例运输.
    scale = EXPORT_SCALE
    for item in fig.findobj(MplLine):
        item.set_linewidth(item.get_linewidth() * scale)
        item.set_markersize(item.get_markersize() * scale)
        item.set_markeredgewidth(item.get_markeredgewidth() * scale)
    for item in fig.findobj(MplPatch):
        item.set_linewidth(item.get_linewidth() * scale)
    for item in fig.findobj(Collection):
        if hasattr(item, "get_sizes"):
            item.set_sizes(item.get_sizes() * scale * scale)
        item.set_linewidths(item.get_linewidths() * scale)
    for ax in fig.axes:
        ax.xaxis.labelpad *= scale
        ax.yaxis.labelpad *= scale
        ax._set_title_offset_trans(7.0 * scale)
        for tick in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tick.set_pad(tick.get_pad() * scale)
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=OUT_DIR / f"{out_prefix}.alignment.json", overlay_svg=OUT_DIR / f"{out_prefix}.alignment.svg", tolerance_pt=1.5, strict=True)
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(OUT_DIR / f"{out_prefix}.{suffix}", dpi=450)
    geometry = {"width_mm": fig.get_figwidth() * 25.4, "height_mm": fig.get_figheight() * 25.4, "minimum_font_pt": min(t.get_fontsize() for t in fig.findobj(Text) if t.get_text())}
    (OUT_DIR / f"{out_prefix}.geometry.json").write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    plt.close(fig)
    print("Saved E2E figure:", OUT_DIR / f"{out_prefix}.png")
    return OUT_DIR / f"{out_prefix}.png", OUT_DIR / f"{out_prefix}.svg"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="生成同源2×2参考图；作者v1由局部运输入口维护排版")
    parser.add_argument("--author-v1", action="store_true", help="使用冻结v1的a图横向显示倍率，不改变原图的400显示上限")
    args = parser.parse_args()
    master = json.loads((BUILD / "data/master.json").read_text(encoding="utf-8"))
    if args.author_v1:
        layout = json.loads((ROOT / "画图/画图代码/e2e/output/e2e-top5-revision/author-v1/layout.json").read_text(encoding="utf-8"))
        # 原尺度重绘核对冻结曲线；之后均匀加宽其路径，不触发重新简化造成的节点变化。
        plot_e2e_figure(master, out_prefix="e2e-v1-baseline")
        plot_e2e_figure(master, out_prefix="e2e-v1-reference", a_x_stretch=layout["x_stretch"])
    else:
        plot_e2e_figure(master)
