"""沿用作者四面板模板,展示每PDB至少成功一个实例的端到端top-k成功率.

输入为本次服务器原始结果重算的十八条整数曲线;纵坐标为原始计数除以共同分母.
main输出同次SVG/PDF/PNG、坐标轴对齐报告、实际绘制数值及双语PPT装配清单.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

from TOOLS.ppt.svg_native import export_figure, panel_header, place_right_labels, scale_figure_artists

EXPORT_SCALE = (159.262 / 25.4) / 11.8
INK = "#243442"
MUTED = "#5A6B78"
GRID = "#E3E9ED"
C_EMAP = "#9A6324"
C_CA2 = "#4860B8"
C_CA2_MID = "#7E92E2"
C_GT = "#0D8A82"
C_GT_MID = "#52B7B0"


# ================================================================================================
def draw(build: Path):
    """用十八条本次重算曲线生成四面板top-k图、渲染核查数据和双语PPT装配清单.

    build为同次临时构建目录;输入为本次重算的显式level条件topk_data.json.
    counts为K=1..10的成功PDB数,y_percent严格为counts/denominator*100.
    不更改候选排序、计费、RMSD或成功定义,正式图集由独立发布步骤维护.
    """
    out_dir = build / "figures"
    stem = "e2e-topk-success"
    data_path = build / "data/topk_data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    (build / "data").mkdir(exist_ok=True)
    plotted_series = []
    out_dir.mkdir(parents=True, exist_ok=True)
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

    fig, axes = plt.subplots(2, 2, figsize=(11.8 * EXPORT_SCALE, 8.3 * EXPORT_SCALE), dpi=300)
    plt.subplots_adjust(left=0.075, right=0.935, top=0.925, bottom=0.13, wspace=0.32, hspace=0.35)

    ks = np.arange(1, 11, dtype=float)
    y_min_ab = 30
    y_min_cd = 30
    min_gap_ab = 5.5
    min_gap_cd = 4.7

    # --------------------------------------------------------------------------
    # 面板a/b分别显示全配体与小分子的定位和身份识别.
    # --------------------------------------------------------------------------
    ab_configs = [
        (
            axes[0, 0],
            "a",
            "All ligands: detection (Find) and identification (Match)",
            179,
            [
                ("Find only · GT", data["full"]["real_stage1_only"], C_GT, "--", 1.55, False),
                ("Find + Match · GT", data["full"]["real_stage1_matcher"], C_GT, "-", 2.15, True),
                ("Find only · CA2", data["full"]["cryo_stage1_only"], C_CA2, "--", 1.55, False),
                ("Find + Match · CA2", data["full"]["cryo_stage1_matcher"], C_CA2, "-", 2.15, True),
                ("Emap2lig-Find", data["full"]["emap2lig"], C_EMAP, "--", 1.70, False),
            ],
        ),
        (
            axes[0, 1],
            "b",
            "Small molecules: detection (Find) and identification (Match)",
            77,
            [
                ("Find only · GT", data["small_find"]["real_receptor"], C_GT, "--", 1.55, False),
                ("Find + Match · GT", data["small_match"]["real_receptor"], C_GT, "-", 2.15, True),
                ("Find only · CA2", data["small_find"]["cryoatom2_receptor"], C_CA2, "--", 1.55, False),
                ("Find + Match · CA2", data["small_match"]["cryoatom2_receptor"], C_CA2, "-", 2.15, True),
                ("Emap2lig-Find", data["small_find"]["emap2lig"], C_EMAP, "--", 1.70, False),
            ],
        ),
    ]

    for ax, letter, title, denom, specs in ab_configs:
        panel_header(
            ax,
            letter,
            title,
            x_offset=-0.135,
            fontsize=10.6 * EXPORT_SCALE,
            label_size=11.3 * EXPORT_SCALE,
            y_offset=1.135,
            pad=6.5 * EXPORT_SCALE,
            color=INK,
        )
        ax.axvspan(0.75, 1.35, color="#F8FAFC", zorder=0)
        ax.axvline(1.0, color="#94A3B8", linestyle=":", linewidth=0.85, zorder=1)
        ax.text(
            1.42,
            y_min_ab + 3.2,
            "Single attempt (K = 1)",
            fontsize=8.8 * EXPORT_SCALE,
            color=MUTED,
            va="bottom",
            ha="left",
        )

        right_labels = []
        for label, counts, col, ls, lw, is_filled in specs:
            pcts = np.array(counts, dtype=float) * 100.0 / denom
            draw_y = pcts  # 数据点保持原百分比;仅文字标签允许避让.
            (curve,) = ax.plot(ks, draw_y, color=col, linestyle=ls, linewidth=lw, zorder=4 if is_filled else 5)
            curve.set_gid(f"{letter}:{label}")
            plotted_series.append(
                {
                    "panel": letter,
                    "label": label,
                    "denominator": denom,
                    "counts": counts,
                    "K": ks.tolist(),
                    "y_percent": curve.get_ydata().tolist(),
                }
            )
            ax.plot(
                ks,
                draw_y,
                marker="o",
                markersize=4.0 if is_filled else 5.3,
                markerfacecolor=col if is_filled else "white",
                markeredgecolor=col,
                markeredgewidth=1.2,
                linestyle="none",
                zorder=8 if is_filled else 7,
            )
            right_labels.append((draw_y[-1], f"{pcts[-1]:.1f}%", col, is_filled))

        place_right_labels(
            ax,
            10.28,
            right_labels,
            min_gap=min_gap_ab,
            style={
                "font_size": 9.3 * EXPORT_SCALE,
                "line_start": 10.03,
                "line_end_gap": 0.16,
                "line_threshold": 0.45,
                "line_width": 0.55,
                "line_alpha": 0.65,
            },
        )

        ax.set_xlim(0.65, 11.45)
        ax.set_ylim(y_min_ab, 102)
        ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ax.set_xticklabels(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        ax.set_yticks(range(y_min_ab, 101, 10))
        ax.set_xlabel("Charged attempts (K)")
        ax.set_ylabel("Successful PDB entries (%)")
        # 网格仅覆盖数据区;图例下方和末端文字区保持留白.
        ax.hlines(range(50, 101, 10), 0.65, 10.10, color=GRID, linewidth=0.55, zorder=0)

        loc_ab = [
            Line2D(
                [0],
                [0],
                color=INK,
                linestyle="-",
                linewidth=2.0,
                marker="o",
                markersize=4.6,
                markerfacecolor=INK,
                markeredgecolor=INK,
                label="Find + Match",
            ),
            Line2D(
                [0],
                [0],
                color=INK,
                linestyle="--",
                linewidth=1.55,
                marker="o",
                markersize=4.6,
                markerfacecolor="white",
                markeredgecolor=INK,
                markeredgewidth=1.2,
                label="Find only",
            ),
        ]
        ax.legend(
            handles=loc_ab,
            loc="lower right",
            frameon=True,
            facecolor="white",
            edgecolor="#E2E8F0",
            framealpha=0.95,
            fontsize=5.5,
            handlelength=2.2,
        )

    # --------------------------------------------------------------------------
    # 面板c/d分别显示CA2与GT的小分子实际构象成功率.
    # --------------------------------------------------------------------------
    cd_configs = [
        (axes[1, 0], "c", "Small molecules: end-to-end pose reconstruction (CA2)", "CA2", C_CA2, C_CA2_MID),
        (axes[1, 1], "d", "Small molecules: end-to-end pose reconstruction (GT)", "GT", C_GT, C_GT_MID),
    ]

    for ax, letter, title, dom, c_strict, c_relaxed in cd_configs:
        panel_header(
            ax,
            letter,
            title,
            x_offset=-0.135,
            fontsize=10.6 * EXPORT_SCALE,
            label_size=11.3 * EXPORT_SCALE,
            y_offset=1.135,
            pad=6.5 * EXPORT_SCALE,
            color=INK,
        )
        ax.axvspan(0.75, 1.35, color="#F8FAFC", zorder=0)
        ax.axvline(1.0, color="#94A3B8", linestyle=":", linewidth=0.85, zorder=1)
        ax.text(1.42, y_min_cd + 12.0, "Single attempt (K = 1)", fontsize=5.5, color=MUTED, va="bottom", ha="left")

        b_dict = data["build"][dom]["local_cov-C"]
        denom = data["denominators"]["small"]

        curve_specs = [
            ("Best-of-50 · <3 Å", b_dict["pose50_lt3"], c_relaxed, "--", 1.65, False),
            ("Best-of-50 · <2 Å", b_dict["pose50_lt2"], c_strict, "--", 1.65, False),
            ("Top-1 · <3 Å", b_dict["pose1_lt3"], c_relaxed, "-", 2.15, True),
            ("Top-1 · <2 Å", b_dict["pose1_lt2"], c_strict, "-", 2.15, True),
        ]

        right_labels = []
        for label, counts, col, ls, lw, is_filled in curve_specs:
            pcts = np.array(counts, dtype=float) * 100.0 / denom
            draw_y = pcts  # 数据点保持原百分比;仅文字标签允许避让.
            (curve,) = ax.plot(ks, draw_y, color=col, linestyle=ls, linewidth=lw, zorder=4 if is_filled else 5)
            curve.set_gid(f"{letter}:{label}")
            plotted_series.append(
                {
                    "panel": letter,
                    "label": label,
                    "denominator": denom,
                    "counts": counts,
                    "K": ks.tolist(),
                    "y_percent": curve.get_ydata().tolist(),
                }
            )
            ax.plot(
                ks,
                draw_y,
                marker="o",
                markersize=4.0 if is_filled else 5.3,
                markerfacecolor=col if is_filled else "white",
                markeredgecolor=col,
                markeredgewidth=1.2,
                linestyle="none",
                zorder=8 if is_filled else 7,
            )
            right_labels.append((draw_y[-1], f"{pcts[-1]:.1f}%", col, is_filled))

        place_right_labels(
            ax,
            10.28,
            right_labels,
            min_gap=min_gap_cd,
            style={
                "font_size": 9.3 * EXPORT_SCALE,
                "line_start": 10.03,
                "line_end_gap": 0.16,
                "line_threshold": 0.45,
                "line_width": 0.55,
                "line_alpha": 0.65,
            },
        )

        ax.set_xlim(0.65, 11.45)
        ax.set_ylim(y_min_cd, 90)
        ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ax.set_xticklabels(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        ax.set_yticks(range(y_min_cd, 91, 10))
        ax.set_xlabel("Charged attempts (K)")
        ax.set_ylabel("Successful PDB entries (%)")
        ax.hlines(range(50, 91, 10), 0.65, 10.10, color=GRID, linewidth=0.55, zorder=0)

        loc_cd = [
            Line2D(
                [0],
                [0],
                color=c_strict,
                linestyle="-",
                linewidth=2.0,
                marker="o",
                markersize=4.5,
                markerfacecolor=c_strict,
                markeredgecolor=c_strict,
                label="Top-1 (<2 Å)",
            ),
            Line2D(
                [0],
                [0],
                color=c_relaxed,
                linestyle="-",
                linewidth=2.0,
                marker="o",
                markersize=4.5,
                markerfacecolor=c_relaxed,
                markeredgecolor=c_relaxed,
                label="Top-1 (<3 Å)",
            ),
            Line2D(
                [0],
                [0],
                color=c_strict,
                linestyle="--",
                linewidth=1.55,
                marker="o",
                markersize=4.5,
                markerfacecolor="white",
                markeredgecolor=c_strict,
                markeredgewidth=1.2,
                label="Best-of-50 (<2 Å)",
            ),
            Line2D(
                [0],
                [0],
                color=c_relaxed,
                linestyle="--",
                linewidth=1.55,
                marker="o",
                markersize=4.5,
                markerfacecolor="white",
                markeredgecolor=c_relaxed,
                markeredgewidth=1.2,
                label="Best-of-50 (<3 Å)",
            ),
        ]
        ax.legend(
            handles=loc_cd,
            loc="lower right",
            ncol=2,
            frameon=True,
            facecolor="white",
            edgecolor="#E2E8F0",
            framealpha=0.95,
            fontsize=5.5,
            handlelength=2.0,
            columnspacing=1.0,
        )

    # --------------------------------------------------------------------------
    # 底部全局三色图例(与 e2e-main-top5(v1) 完全一致)
    # --------------------------------------------------------------------------
    handles_global = [
        Patch(facecolor=C_EMAP, edgecolor=INK, linewidth=0.6, label="Emap2lig"),
        Patch(facecolor=C_CA2, edgecolor=INK, linewidth=0.6, label="LigandSeek (CA2)"),
        Patch(facecolor=C_GT, edgecolor=INK, linewidth=0.6, label="LigandSeek (GT)"),
    ]
    leg = fig.legend(
        handles=handles_global,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.012),
        ncol=3,
        frameon=True,
        facecolor="#F8FAFC",
        edgecolor="#CBD5E1",
        fontsize=9.8 * EXPORT_SCALE,
        handlelength=1.5,
        handleheight=0.9,
        columnspacing=2.8,
    )
    leg.get_frame().set_linewidth(0.6)

    scale_figure_artists(fig, EXPORT_SCALE, 6.5, 5.5)
    page = export_figure(fig, out_dir, stem, 600, False)
    (build / "manifest.json").write_text(json.dumps([page], ensure_ascii=False, indent=2), encoding="utf8")
    (build / "data/plotted_series.json").write_text(
        json.dumps(plotted_series, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    plt.close(fig)
