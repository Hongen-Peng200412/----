"""沿作者 2×2 模板绘制 E2E Top-5 主图, 数据只读取同次准备的 master.json.

draw 将全配体 Find/Match、小分子正确身份比较和实际三阶段完成度汇总为四面板.
输出在调用方指定的本次临时目录中, 包含同源 SVG、PDF、PNG、最终物理尺寸与对齐报告; 不修改正式 PPT.
配色、图型、分区和图例沿作者模板, 仅作最终版心的字形与留白适配.
"""

import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from pathlib import Path
from matplotlib.text import Text

from TOOLS.ppt.svg_native import export_figure, panel_header, place_right_labels, scale_figure_artists

EXPORT_SCALE = (159.262 / 25.4) / 11.8

INK = "#243442"
MUTED = "#5A6B78"
GRID = "#E3E9ED"

C_EMAP = "#9A6324"  # 棕色表示Emap2lig密度基线.
C_EMAP_MID = "#C49358"  # 面板b中300%预算的浅棕线.
C_EMAP_LIGHT = "#DFBE9F"  # 棕色填充.

C_CA2 = "#4860B8"  # 蓝色表示CA2受体的LigandSeek.
C_CA2_MID = "#8294DF"  # 面板b中300%预算的浅蓝线.
C_CA2_LIGHT = "#AEBCEF"  # 蓝色填充.

C_GT = "#0D8A82"  # 青色表示GT受体的LigandSeek.
C_GT_MID = "#58B8B1"  # 面板b中300%预算的浅青线.
C_GT_LIGHT = "#94D4CF"  # 青色填充.

plt.rcParams.update(
    {
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
    }
)


def draw(master, outdir: Path):
    """将本次重算的Top-1/Top-5科学图元绘到指定临时目录."""
    outdir.mkdir(parents=True, exist_ok=True)
    out_prefix = "e2e-main-top5"
    a_x_stretch = 1.0
    # a_x_stretch仅拉开预算的横向显示距离;保留原图兼容值1,不改变预算标值和纵向数据.
    pose_key = "pose5"
    pose_label = "Top-5 poses"

    panels = master["panels"]
    summaries = master["summaries"]

    fig, axes = plt.subplots(2, 2, figsize=(11.8 * EXPORT_SCALE, 8.3 * EXPORT_SCALE), dpi=300)
    plt.subplots_adjust(left=0.065, right=0.975, top=0.93, bottom=0.125, wspace=0.31, hspace=0.34)

    ax_a = axes[0, 0]
    panel_header(
        ax_a,
        "a",
        "All ligands: detection and identification\n(179 PDBs, 2,502 instances)",
        x_offset=-0.115,
        fontsize=10.8 * EXPORT_SCALE,
        label_size=10.5 * EXPORT_SCALE,
        y_offset=1.17,
        pad=7.0 * EXPORT_SCALE,
        color=INK,
    )

    specs_a = [
        ("find_full_GT", C_GT, "--", 1.6, False, -2.2),
        ("full_GT", C_GT, "-", 2.2, True, +2.2),
        ("find_full_CA2", C_CA2, "--", 1.6, False, -2.2),
        ("full_CA2", C_CA2, "-", 2.2, True, +2.2),
        ("find_full_Emap2lig", C_EMAP, "--", 1.75, False, 0.0),
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
                    xp,
                    mval,
                    yerr=[[mval - s["ci_low"]], [s["ci_high"] - mval]],
                    fmt="none",
                    ecolor=col,
                    elinewidth=0.95,
                    capsize=2.2,
                    capthick=0.9,
                    alpha=0.85,
                    zorder=5,
                )
            ax_a.plot(
                xp,
                mval,
                marker="o",
                markersize=5.0,
                markerfacecolor=col if is_filled else "white",
                markeredgecolor=col,
                markeredgewidth=1.3,
                zorder=6,
            )

    ax_a.text(
        300 * a_x_stretch + 5,
        summaries["find_full_GT"]["300"]["mean"] + 2.9,
        f"{summaries['find_full_GT']['300']['mean']:.1f}% (Find)",
        fontsize=9.6 * EXPORT_SCALE,
        color=C_GT,
        va="center",
    )
    ax_a.text(
        300 * a_x_stretch + 5,
        summaries["full_GT"]["300"]["mean"] + 0.7,
        f"{summaries['full_GT']['300']['mean']:.1f}% (Find+Match)",
        fontsize=9.6 * EXPORT_SCALE,
        fontweight="bold",
        color=C_GT,
        va="center",
    )
    ax_a.text(
        300 * a_x_stretch + 5,
        summaries["find_full_CA2"]["300"]["mean"] - 0.8,
        f"{summaries['find_full_CA2']['300']['mean']:.1f}% (Find)",
        fontsize=9.6 * EXPORT_SCALE,
        color=C_CA2,
        va="center",
    )
    ax_a.text(
        300 * a_x_stretch + 5,
        summaries["full_CA2"]["300"]["mean"] - 1.6,
        f"{summaries['full_CA2']['300']['mean']:.1f}% (Find+Match)",
        fontsize=9.6 * EXPORT_SCALE,
        fontweight="bold",
        color=C_CA2,
        va="center",
    )
    ax_a.text(
        300 * a_x_stretch + 5,
        summaries["find_full_Emap2lig"]["300"]["mean"],
        f"{summaries['find_full_Emap2lig']['300']['mean']:.1f}% (Find)",
        fontsize=9.6 * EXPORT_SCALE,
        color=C_EMAP,
        va="center",
    )

    ax_a.axvline(100 * a_x_stretch, color="#94A3B8", linestyle=":", linewidth=0.9, zorder=1)
    ax_a.text(
        100 * a_x_stretch + 3,
        7.0,
        "100% budget\n(1× true count)",
        fontsize=9.6 * EXPORT_SCALE,
        color=MUTED,
        va="bottom",
    )

    ax_a.set_xlim(0, 400)
    ax_a.set_ylim(0, 84)
    ax_a.set_yticks(range(0, 81, 10))
    ax_a.set_xticks(np.array([0, 50, 100, 200, 300]) * a_x_stretch)
    ax_a.set_xticklabels(["0%", "50%", "100%", "200%", "300%"])
    ax_a.set_xlabel("Relative candidate attempt budget (% of true instances per PDB)")
    ax_a.set_ylabel("Per-PDB mean completion (%)")
    ax_a.grid(axis="y", color=GRID, linewidth=0.55, zorder=0)

    loc_a = [
        Line2D(
            [0],
            [0],
            color=INK,
            linestyle="-",
            linewidth=2.0,
            marker="o",
            markersize=5.0,
            markerfacecolor=INK,
            markeredgecolor=INK,
            label="Find + Match (location + identity)",
        ),
        Line2D(
            [0],
            [0],
            color=INK,
            linestyle="--",
            linewidth=1.6,
            marker="o",
            markersize=5.0,
            markerfacecolor="white",
            markeredgecolor=INK,
            markeredgewidth=1.3,
            label="Find only (location detection)",
        ),
    ]
    ax_a.legend(
        handles=loc_a,
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="#E2E8F0",
        framealpha=0.94,
        fontsize=9.6 * EXPORT_SCALE,
        handlelength=2.4,
    )

    ax_b = axes[0, 1]
    panel_header(
        ax_b,
        "b",
        "Small molecules: detection and pose reconstruction\n(Find + Build)",
        x_offset=-0.115,
        fontsize=10.8 * EXPORT_SCALE,
        label_size=10.5 * EXPORT_SCALE,
        y_offset=1.17,
        pad=7.0 * EXPORT_SCALE,
        color=INK,
    )

    rows_b = [
        ("2.0", "Emap2lig", "100", 10.5, C_EMAP, True),
        ("2.0", "Emap2lig", "300", 9.6, C_EMAP_MID, False),
        ("2.0", "CA2", "100", 8.3, C_CA2, True),
        ("2.0", "CA2", "300", 7.4, C_CA2_MID, False),
        ("2.0", "GT", "100", 6.1, C_GT, True),
        ("2.0", "GT", "300", 5.2, C_GT_MID, False),
        ("3.0", "Emap2lig", "100", 3.0, C_EMAP, True),
        ("3.0", "Emap2lig", "300", 2.15, C_EMAP_MID, False),
        ("3.0", "CA2", "100", 1.0, C_CA2, True),
        ("3.0", "CA2", "300", 0.1, C_CA2_MID, False),
        ("3.0", "GT", "100", -1.2, C_GT, True),
        ("3.0", "GT", "300", -2.1, C_GT_MID, False),
    ]

    ax_b.axhspan(4.35, 12.5, color="#F8FAFC", zorder=0)
    ax_b.axhline(4.35, color="#64748B", linestyle="--", linewidth=1.0, zorder=2)
    ax_b.text(
        1.5,
        11.7,
        "Strict threshold: RMSD < 2 Å",
        fontsize=9.6 * EXPORT_SCALE,
        fontweight="bold",
        color=INK,
        va="center",
    )
    ax_b.text(
        1.5,
        3.9,
        "Relaxed threshold: RMSD < 3 Å",
        fontsize=9.6 * EXPORT_SCALE,
        fontweight="bold",
        color=INK,
        va="center",
    )

    for rmsd_s, dom, b_str, yp, col, is_100 in rows_b:
        v_top1 = summaries[f"assume_{dom}_pose1_rmsd{rmsd_s}"][b_str]["mean"]
        v_pool = summaries[f"assume_{dom}_{pose_key}_rmsd{rmsd_s}"][b_str]["mean"]
        lw = 2.6 if is_100 else 2.0
        ax_b.plot([v_top1, v_pool], [yp, yp], color=col, linewidth=lw, linestyle="-", zorder=3)
        ax_b.plot(
            v_top1,
            yp,
            marker="o",
            markersize=6.2,
            markerfacecolor=col,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=5,
        )
        ax_b.plot(
            v_pool,
            yp,
            marker="o",
            markersize=6.2,
            markerfacecolor="white",
            markeredgecolor=col,
            markeredgewidth=1.6,
            zorder=5,
        )
        ax_b.text(
            v_top1 - 1.65,
            yp,
            f"{v_top1:.1f}%",
            fontsize=9.6 * EXPORT_SCALE,
            color=col,
            ha="right",
            va="center",
            fontweight="bold" if is_100 else "normal",
        )
        ax_b.text(
            v_pool + 1.65,
            yp,
            f"{v_pool:.1f}%",
            fontsize=9.6 * EXPORT_SCALE,
            color=col,
            ha="left",
            va="center",
            fontweight="bold" if is_100 else "normal",
        )

    ax_b.set_yticks([10.05, 7.85, 5.65, 2.575, 0.55, -1.65])
    ax_b.set_yticklabels(
        ["Emap2lig", "LigandSeek (CA2)", "LigandSeek (GT)", "Emap2lig", "LigandSeek (CA2)", "LigandSeek (GT)"],
        fontsize=9.6 * EXPORT_SCALE,
        rotation=32,
        ha="right",
        va="center",
    )
    ax_b.set_xlim(0, 84)
    ax_b.set_xticks(range(0, 81, 10))
    ax_b.set_ylim(-3.2, 12.5)
    ax_b.set_xlabel("Per-PDB mean Find + Build completion (%, oracle SMILES)")
    ax_b.grid(axis="x", color=GRID, linewidth=0.55, zorder=0)

    loc_b = [
        Line2D([0], [0], color=INK, linewidth=2.5, label="Dark line: 100% budget"),
        Line2D([0], [0], color="#8896A6", linewidth=2.0, label="Light line: 300% budget"),
        Line2D(
            [0],
            [0],
            color="none",
            marker="o",
            markersize=5.8,
            markerfacecolor=INK,
            markeredgecolor=INK,
            label="Filled circle: Top-1 pose",
        ),
        Line2D(
            [0],
            [0],
            color="none",
            marker="o",
            markersize=5.8,
            markerfacecolor="white",
            markeredgecolor=INK,
            markeredgewidth=1.5,
            label=f"Open circle: {pose_label}",
        ),
    ]
    ax_b.legend(
        handles=loc_b,
        loc="lower left",
        frameon=True,
        facecolor="white",
        edgecolor="#E2E8F0",
        framealpha=0.95,
        fontsize=9.6 * EXPORT_SCALE,
        ncol=1,
    )

    for ax_cd, letter, dom, title_str, c_dark, c_light in [
        (axes[1, 0], "c", "CA2", "Small molecules: automated end-to-end modelling\n(CA2)", C_CA2, C_CA2_LIGHT),
        (axes[1, 1], "d", "GT", "Small molecules: automated end-to-end modelling\n(GT)", C_GT, C_GT_LIGHT),
    ]:
        panel_header(
            ax_cd,
            letter,
            title_str,
            x_offset=-0.115,
            fontsize=10.8 * EXPORT_SCALE,
            label_size=10.5 * EXPORT_SCALE,
            y_offset=1.17,
            pad=7.0 * EXPORT_SCALE,
            color=INK,
        )
        x_100 = np.array([0, 1, 2, 3], dtype=float)
        x_300 = np.array([4.8, 5.8, 6.8, 7.8], dtype=float)
        bw = 0.78

        ax_cd.axvspan(3.9, 8.6, color="#F8FAFC", zorder=0)
        ax_cd.plot([3.9, 3.9], [0, 84.5], color="#64748B", linestyle="--", linewidth=1.0, zorder=2)
        ax_cd.text(
            1.5, 88.0, "100% attempt budget", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=INK, ha="center"
        )
        ax_cd.text(
            6.3, 88.0, "300% attempt budget", fontsize=9.6 * EXPORT_SCALE, fontweight="bold", color=INK, ha="center"
        )

        for xs, b_str in [(x_100, "100"), (x_300, "300")]:
            v_find = summaries[f"find_small_{dom}_poseNone_rmsdNone"][b_str]["mean"]
            v_fm = summaries[f"find_match_small_{dom}"][b_str]["mean"]
            v_b3_1 = summaries[f"actual_{dom}_pose1_rmsd3.0"][b_str]["mean"]
            v_b3_p = summaries[f"actual_{dom}_{pose_key}_rmsd3.0"][b_str]["mean"]
            v_b2_1 = summaries[f"actual_{dom}_pose1_rmsd2.0"][b_str]["mean"]
            v_b2_p = summaries[f"actual_{dom}_{pose_key}_rmsd2.0"][b_str]["mean"]

            for idx_pre, v_pre in [(0, v_find), (1, v_fm)]:
                ax_cd.bar(
                    xs[idx_pre],
                    v_pre,
                    width=bw,
                    color=c_light,
                    alpha=0.42,
                    edgecolor=c_dark,
                    linewidth=1.1,
                    linestyle="--",
                    zorder=3,
                )
                ax_cd.text(
                    xs[idx_pre],
                    v_pre + 2.6,
                    f"{v_pre:.1f}%",
                    fontsize=9.6 * EXPORT_SCALE,
                    color=INK,
                    fontweight="bold",
                    ha="center",
                    va="bottom",
                )

            ax_cd.bar(xs[2], v_b3_1, width=bw, color=c_dark, edgecolor="white", linewidth=0.5, zorder=3)
            ax_cd.bar(
                xs[2],
                v_b3_p - v_b3_1,
                bottom=v_b3_1,
                width=bw,
                color=c_light,
                edgecolor=c_dark,
                linewidth=0.6,
                zorder=3,
            )
            ax_cd.text(
                xs[2],
                v_b3_1 / 2.0,
                f"{v_b3_1:.1f}%",
                fontsize=9.6 * EXPORT_SCALE,
                color="white",
                fontweight="bold",
                ha="center",
                va="center",
                zorder=5,
            )
            ax_cd.text(
                xs[2],
                v_b3_p + 2.6,
                f"{v_b3_p:.1f}%",
                fontsize=9.6 * EXPORT_SCALE,
                color=c_dark,
                fontweight="bold",
                ha="center",
                va="bottom",
            )

            ax_cd.bar(xs[3], v_b2_1, width=bw, color=c_dark, edgecolor="white", linewidth=0.5, zorder=3)
            ax_cd.bar(
                xs[3],
                v_b2_p - v_b2_1,
                bottom=v_b2_1,
                width=bw,
                color=c_light,
                edgecolor=c_dark,
                linewidth=0.6,
                zorder=3,
            )
            ax_cd.text(
                xs[3],
                v_b2_1 / 2.0,
                f"{v_b2_1:.1f}%",
                fontsize=9.6 * EXPORT_SCALE,
                color="white",
                fontweight="bold",
                ha="center",
                va="center",
                zorder=5,
            )
            ax_cd.text(
                xs[3],
                v_b2_p + 2.6,
                f"{v_b2_p:.1f}%",
                fontsize=9.6 * EXPORT_SCALE,
                color=c_dark,
                fontweight="bold",
                ha="center",
                va="bottom",
            )

            ax_cd.plot(xs, [v_find, v_fm, v_b3_p, v_b2_p], color=c_dark, linestyle=":", linewidth=1.0, zorder=4)

        ax_cd.set_xticks(list(x_100) + list(x_300))
        ax_cd.set_xticklabels(
            ["Find\nonly", "Find +\nMatch", "E2E\n(<3 Å)", "E2E\n(<2 Å)"] * 2, fontsize=9.6 * EXPORT_SCALE
        )
        ax_cd.set_xlim(-0.7, 8.5)
        ax_cd.set_ylim(0, 101)
        ax_cd.set_yticks(range(0, 101, 20))
        ax_cd.set_ylabel("Per-PDB mean completion (%)")
        ax_cd.grid(axis="y", color=GRID, linewidth=0.55, zorder=0)

        # 每个实际建模面板仅保留Top1和Top5两个作者图例.
        loc_cd = [
            Patch(facecolor=c_dark, edgecolor="white", label="Top-1 pose"),
            Patch(facecolor=c_light, edgecolor=c_dark, label=pose_label),
        ]
        ax_cd.legend(
            handles=loc_cd,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.015),
            ncol=2,
            frameon=True,
            facecolor="white",
            edgecolor="#E2E8F0",
            framealpha=0.95,
            fontsize=9.6 * EXPORT_SCALE,
            columnspacing=1.8,
        )

    handles_global = [
        Patch(facecolor=C_EMAP, edgecolor=INK, linewidth=0.6, label="Emap2lig (density-only baseline)"),
        Patch(
            facecolor=C_CA2, edgecolor=INK, linewidth=0.6, label="LigandSeek · CA2 (CryoAtom2-reconstructed receptor)"
        ),
        Patch(facecolor=C_GT, edgecolor=INK, linewidth=0.6, label="LigandSeek · GT (deposited receptor)"),
    ]
    leg = fig.legend(
        handles=handles_global,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.012),
        ncol=3,
        frameon=True,
        facecolor="#F8FAFC",
        edgecolor="#CBD5E1",
        fontsize=9.6 * EXPORT_SCALE,
        handlelength=1.5,
        handleheight=0.9,
        columnspacing=2.2,
    )
    leg.get_frame().set_linewidth(0.6)

    # 源画布已经采用最终物理尺寸, 字体在创建时设置, 其余长度按同一比例运输.
    scale_figure_artists(fig, EXPORT_SCALE, 7.0, None)
    page = export_figure(fig, outdir, out_prefix, 450, True)
    (outdir.parent / "manifest.json").write_text(json.dumps([page], ensure_ascii=False, indent=2), encoding="utf8")
    geometry = {
        "width_mm": fig.get_figwidth() * 25.4,
        "height_mm": fig.get_figheight() * 25.4,
        "minimum_font_pt": min(t.get_fontsize() for t in fig.findobj(Text) if t.get_text()),
    }
    (outdir / f"{out_prefix}.geometry.json").write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    plt.close(fig)
    print("Saved E2E figure:", outdir / f"{out_prefix}.png")
    return outdir / f"{out_prefix}.png", outdir / f"{out_prefix}.svg"
