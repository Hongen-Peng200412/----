"""沿用作者四面板模板，展示每PDB至少成功一个实例的端到端top-k成功率。

输入为显式EMDB level条件的十八条冻结整数曲线；不重算实验，不对纵坐标抖动。
main输出同次SVG/PDF/PNG、坐标轴对齐报告、实际绘制数值及双语PPT装配清单。
"""
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import Collection
from matplotlib.lines import Line2D, Line2D as MplLine
from matplotlib.patches import Patch, Patch as MplPatch
from matplotlib.text import Text
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
sys.path.insert(0, str(Path.home() / ".codex/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment

EXPORT_SCALE = (159.262 / 25.4) / 11.8
INK = "#243442"
MUTED = "#5A6B78"
GRID = "#E3E9ED"
C_EMAP = "#9A6324"
C_CA2 = "#4860B8"
C_CA2_MID = "#7E92E2"
C_GT = "#0D8A82"
C_GT_MID = "#52B7B0"

CAPTION_EN = (
    "End-to-end top-k success across complexes. "
    "Success is the fraction of PDB entries with at least one target ligand instance successfully processed within K charged attempts (K = 1–10). "
    "Find and Match denote LigandSeek-Find and LigandSeek-Match. "
    "a,b, Find-only and Find–Match success across all ligands (a; 179 PDB entries, 2,502 instances) and eligible small molecules (b; 77 PDB entries, 446 instances). "
    "Eligible small molecules are single-residue organic small molecules with no atoms missing relative to their templates. "
    "Dashed lines with open circles indicate Find only; solid lines with filled circles indicate Find–Match. "
    "Emap2lig-Find received the EMDB-recommended contour level. "
    "c,d, Full Find–Match–Build success using DG-PocketXMol with CryoAtom2-reconstructed receptors (CA2; c) and deposited receptors (GT; d). "
    "Dark and light curves denote heavy-atom RMSD <2 Å and <3 Å, respectively. "
    "Solid lines with filled circles show model-ranked top-1 poses; dashed lines with open circles show the lowest RMSD among all 50 model-ranked poses (best-of-50). "
    "Brown, blue and teal denote Emap2lig, LigandSeek with CA2 receptors and LigandSeek with GT receptors, respectively."
)
CAPTION_ZH = (
    "复合物层面的端到端top-k成功率。成功率为前K次计费尝试（K = 1–10）内至少成功处理一个目标配体实例的PDB条目比例。"
    "Find和Match分别表示LigandSeek-Find和LigandSeek-Match。a、b，全配体（a；179个PDB条目，2,502个实例）及合格小分子（b；77个PDB条目，446个实例）的仅检出与检出加身份匹配成功率。"
    "合格小分子为单残基、相对于模板无缺失原子的有机小分子。空心圆虚线表示仅Find，实心圆实线表示Find–Match。Emap2lig-Find接收EMDB推荐的contour level。"
    "c、d，采用DG-PocketXMol及CryoAtom2重建受体（CA2；c）或沉积受体（GT；d）的完整Find–Match–Build成功率。深、浅色分别表示重原子RMSD <2 Å和<3 Å。"
    "实心圆实线表示模型原排名第一的构象；空心圆虚线表示全部50个原排名构象中的最低RMSD（best-of-50）。棕、蓝、青绿色分别表示Emap2lig、CA2受体条件下的LigandSeek及GT受体条件下的LigandSeek。"
)

def panel_header(ax, letter: str, title: str, x_offset: float = -0.135):
    ax.set_title(title, loc="left", fontsize=10.6 * EXPORT_SCALE, fontweight="bold", pad=6.5 * EXPORT_SCALE, color=INK)
    ax.text(x_offset, 1.135, letter, transform=ax.transAxes, fontsize=11.3 * EXPORT_SCALE, fontweight="bold", va="top", ha="left", color=INK)


def place_right_labels(ax, x_pos: float, raw_entries: list[tuple[float, str, str, bool]], min_gap: float):
    """在 x_pos 处放置右侧末端百分比标签，仅对间距小于 min_gap 的相邻簇做局部对称避让，保持独立点严格原位对齐。"""
    entries = sorted(raw_entries, key=lambda item: item[0])  # 从低到高
    ys = [item[0] for item in entries]
    # 聚类：只把间距 < min_gap 的相邻标签归入同一冲突簇进行最小二乘保心展开
    clusters: list[list[int]] = [[0]]
    for i in range(1, len(ys)):
        if ys[i] - ys[clusters[-1][-1]] < min_gap:
            clusters[-1].append(i)
        else:
            clusters.append([i])

    # 迭代合并因展开而新触碰的簇
    changed = True
    while changed:
        changed = False
        resolved_ys = list(ys)
        for cl in clusters:
            if len(cl) > 1:
                center = float(np.mean([ys[idx] for idx in cl]))
                span = (len(cl) - 1) * min_gap
                for k_i, idx in enumerate(cl):
                    resolved_ys[idx] = center - span / 2.0 + k_i * min_gap
        new_clusters: list[list[int]] = [clusters[0]]
        for cl in clusters[1:]:
            prev_last = new_clusters[-1][-1]
            curr_first = cl[0]
            if resolved_ys[curr_first] - resolved_ys[prev_last] < min_gap - 1e-6:
                new_clusters[-1].extend(cl)
                changed = True
            else:
                new_clusters.append(cl)
        clusters = new_clusters

    for idx, (orig_y, text, col, is_bold) in enumerate(entries):
        draw_y = resolved_ys[idx]
        if abs(draw_y - orig_y) > 0.45:
            ax.plot([10.03, x_pos - 0.16], [orig_y, draw_y], color=col, linewidth=0.55, alpha=0.65, zorder=2)
        ax.text(
            x_pos, draw_y, text,
            fontsize=9.3 * EXPORT_SCALE,
            fontweight="bold" if is_bold else "normal",
            color=col, va="center", ha="left"
        )


# ================================================================================================
def main():
    """用十八条冻结曲线生成四面板top-k图、渲染核查数据和双语PPT装配清单。

    FIGURE_BUILD_ROOT为同次临时构建目录；输入仅为显式level条件的topk_data.json。
    counts为K=1..10的成功PDB数，y_percent严格为counts/denominator*100。
    不更改候选排序、计费、RMSD或成功定义，正式图集由独立发布步骤维护。
    """
    build = Path(os.environ["FIGURE_BUILD_ROOT"])
    out_dir = build / "figures"
    stem = "e2e-topk-success"
    data_path = ROOT / "画图/画图代码/e2e/output/find-build-shared/explicit_emdb_level/topk_data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    (build / "data").mkdir(exist_ok=True)
    (build / "data/topk_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    plotted_series = []
    out_dir.mkdir(parents=True, exist_ok=True)
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

    fig, axes = plt.subplots(2, 2, figsize=(11.8 * EXPORT_SCALE, 8.3 * EXPORT_SCALE), dpi=300)
    plt.subplots_adjust(left=0.075, right=0.935, top=0.925, bottom=0.13, wspace=0.32, hspace=0.35)

    ks = np.arange(1, 11, dtype=float)
    y_min_ab = 30
    y_min_cd = 30
    min_gap_ab = 5.5
    min_gap_cd = 4.7

    # --------------------------------------------------------------------------
    # Panel a & Panel b: Detection (Find) and Identification (Match)
    # --------------------------------------------------------------------------
    ab_configs = [
        (
            axes[0, 0], "a", "All ligands: detection (Find) and identification (Match)",
            179,
            [
                ("Find only · GT",     data["full"]["real_stage1_only"],    C_GT,   "--", 1.55, False),
                ("Find + Match · GT",  data["full"]["real_stage1_matcher"], C_GT,   "-",  2.15, True),
                ("Find only · CA2",    data["full"]["cryo_stage1_only"],    C_CA2,  "--", 1.55, False),
                ("Find + Match · CA2", data["full"]["cryo_stage1_matcher"], C_CA2,  "-",  2.15, True),
                ("Emap2lig-Find",      data["full"]["emap2lig"],            C_EMAP, "--", 1.70, False),
            ],
        ),
        (
            axes[0, 1], "b", "Small molecules: detection (Find) and identification (Match)",
            77,
            [
                ("Find only · GT",     data["small_find"]["real_receptor"],       C_GT,   "--", 1.55, False),
                ("Find + Match · GT",  data["small_match"]["real_receptor"],      C_GT,   "-",  2.15, True),
                ("Find only · CA2",    data["small_find"]["cryoatom2_receptor"],  C_CA2,  "--", 1.55, False),
                ("Find + Match · CA2", data["small_match"]["cryoatom2_receptor"], C_CA2,  "-",  2.15, True),
                ("Emap2lig-Find",      data["small_find"]["emap2lig"],            C_EMAP, "--", 1.70, False),
            ],
        ),
    ]

    for ax, letter, title, denom, specs in ab_configs:
        panel_header(ax, letter, title)
        ax.axvspan(0.75, 1.35, color="#F8FAFC", zorder=0)
        ax.axvline(1.0, color="#94A3B8", linestyle=":", linewidth=0.85, zorder=1)
        ax.text(1.42, y_min_ab + 3.2, "Single attempt (K = 1)", fontsize=8.8 * EXPORT_SCALE, color=MUTED, va="bottom", ha="left")

        right_labels = []
        for label, counts, col, ls, lw, is_filled in specs:
            pcts = np.array(counts, dtype=float) * 100.0 / denom
            draw_y = pcts  # 数据点保持原百分比；仅文字标签允许避让。
            curve, = ax.plot(ks, draw_y, color=col, linestyle=ls, linewidth=lw, zorder=4 if is_filled else 5)
            curve.set_gid(f"{letter}:{label}")
            plotted_series.append({"panel": letter, "label": label, "denominator": denom, "counts": counts,
                                   "K": ks.tolist(), "y_percent": curve.get_ydata().tolist()})
            ax.plot(
                ks, draw_y, marker="o", markersize=4.0 if is_filled else 5.3,
                markerfacecolor=col if is_filled else "white",
                markeredgecolor=col, markeredgewidth=1.2,
                linestyle="none", zorder=8 if is_filled else 7
            )
            right_labels.append((draw_y[-1], f"{pcts[-1]:.1f}%", col, is_filled))

        place_right_labels(ax, 10.28, right_labels, min_gap=min_gap_ab)

        ax.set_xlim(0.65, 11.45)
        ax.set_ylim(y_min_ab, 102)
        ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ax.set_xticklabels(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        ax.set_yticks(range(y_min_ab, 101, 10))
        ax.set_xlabel("Charged attempts (K)")
        ax.set_ylabel("Successful PDB entries (%)")
        # 网格仅覆盖数据区；图例下方和末端文字区保持留白。
        ax.hlines(range(50, 101, 10), 0.65, 10.10, color=GRID, linewidth=0.55, zorder=0)

        loc_ab = [
            Line2D([0], [0], color=INK, linestyle="-", linewidth=2.0, marker="o", markersize=4.6,
                   markerfacecolor=INK, markeredgecolor=INK, label="Find + Match"),
            Line2D([0], [0], color=INK, linestyle="--", linewidth=1.55, marker="o", markersize=4.6,
                   markerfacecolor="white", markeredgecolor=INK, markeredgewidth=1.2, label="Find only"),
        ]
        ax.legend(
            handles=loc_ab, loc="lower right", frameon=True, facecolor="white",
            edgecolor="#E2E8F0", framealpha=0.95, fontsize=5.5, handlelength=2.2
        )

    # --------------------------------------------------------------------------
    # Panel c (CA2) & Panel d (GT): End-to-end Small-Molecule Pose Reconstruction
    # --------------------------------------------------------------------------
    cd_configs = [
        (
            axes[1, 0], "c", "Small molecules: end-to-end pose reconstruction (CA2)",
            "CA2", C_CA2, C_CA2_MID
        ),
        (
            axes[1, 1], "d", "Small molecules: end-to-end pose reconstruction (GT)",
            "GT", C_GT, C_GT_MID
        ),
    ]

    for ax, letter, title, dom, c_strict, c_relaxed in cd_configs:
        panel_header(ax, letter, title)
        ax.axvspan(0.75, 1.35, color="#F8FAFC", zorder=0)
        ax.axvline(1.0, color="#94A3B8", linestyle=":", linewidth=0.85, zorder=1)
        ax.text(1.42, y_min_cd + 12.0, "Single attempt (K = 1)", fontsize=5.5, color=MUTED, va="bottom", ha="left")

        b_dict = data["build"][dom]["local_cov-C"]
        denom = data["denominators"]["small"]

        curve_specs = [
            ("Best-of-50 · <3 Å", b_dict["pose50_lt3"], c_relaxed, "--", 1.65, False),
            ("Best-of-50 · <2 Å", b_dict["pose50_lt2"], c_strict,  "--", 1.65, False),
            ("Top-1 · <3 Å",      b_dict["pose1_lt3"],  c_relaxed, "-",  2.15, True),
            ("Top-1 · <2 Å",      b_dict["pose1_lt2"],  c_strict,  "-",  2.15, True),
        ]

        right_labels = []
        for label, counts, col, ls, lw, is_filled in curve_specs:
            pcts = np.array(counts, dtype=float) * 100.0 / denom
            draw_y = pcts  # 数据点保持原百分比；仅文字标签允许避让。
            curve, = ax.plot(ks, draw_y, color=col, linestyle=ls, linewidth=lw, zorder=4 if is_filled else 5)
            curve.set_gid(f"{letter}:{label}")
            plotted_series.append({"panel": letter, "label": label, "denominator": denom, "counts": counts,
                                   "K": ks.tolist(), "y_percent": curve.get_ydata().tolist()})
            ax.plot(
                ks, draw_y, marker="o", markersize=4.0 if is_filled else 5.3,
                markerfacecolor=col if is_filled else "white",
                markeredgecolor=col, markeredgewidth=1.2,
                linestyle="none", zorder=8 if is_filled else 7
            )
            right_labels.append((draw_y[-1], f"{pcts[-1]:.1f}%", col, is_filled))

        place_right_labels(ax, 10.28, right_labels, min_gap=min_gap_cd)

        ax.set_xlim(0.65, 11.45)
        ax.set_ylim(y_min_cd, 90)
        ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ax.set_xticklabels(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        ax.set_yticks(range(y_min_cd, 91, 10))
        ax.set_xlabel("Charged attempts (K)")
        ax.set_ylabel("Successful PDB entries (%)")
        ax.hlines(range(50, 91, 10), 0.65, 10.10, color=GRID, linewidth=0.55, zorder=0)

        loc_cd = [
            Line2D([0], [0], color=c_strict,  linestyle="-",  linewidth=2.0, marker="o", markersize=4.5,
                   markerfacecolor=c_strict, markeredgecolor=c_strict, label="Top-1 (<2 Å)"),
            Line2D([0], [0], color=c_relaxed, linestyle="-",  linewidth=2.0, marker="o", markersize=4.5,
                   markerfacecolor=c_relaxed, markeredgecolor=c_relaxed, label="Top-1 (<3 Å)"),
            Line2D([0], [0], color=c_strict,  linestyle="--", linewidth=1.55, marker="o", markersize=4.5,
                   markerfacecolor="white", markeredgecolor=c_strict, markeredgewidth=1.2, label="Best-of-50 (<2 Å)"),
            Line2D([0], [0], color=c_relaxed, linestyle="--", linewidth=1.55, marker="o", markersize=4.5,
                   markerfacecolor="white", markeredgecolor=c_relaxed, markeredgewidth=1.2, label="Best-of-50 (<3 Å)"),
        ]
        ax.legend(
            handles=loc_cd, loc="lower right", ncol=2, frameon=True, facecolor="white",
            edgecolor="#E2E8F0", framealpha=0.95, fontsize=5.5,
            handlelength=2.0, columnspacing=1.0
        )

    # --------------------------------------------------------------------------
    # 底部全局三色图例（与 e2e-main-top5(v1) 完全一致）
    # --------------------------------------------------------------------------
    handles_global = [
        Patch(facecolor=C_EMAP, edgecolor=INK, linewidth=0.6, label="Emap2lig"),
        Patch(facecolor=C_CA2,  edgecolor=INK, linewidth=0.6, label="LigandSeek (CA2)"),
        Patch(facecolor=C_GT,   edgecolor=INK, linewidth=0.6, label="LigandSeek (GT)"),
    ]
    leg = fig.legend(
        handles=handles_global, loc="lower center", bbox_to_anchor=(0.5, 0.012), ncol=3,
        frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.8 * EXPORT_SCALE,
        handlelength=1.5, handleheight=0.9, columnspacing=2.8
    )
    leg.get_frame().set_linewidth(0.6)

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
        ax._set_title_offset_trans(6.5 * scale)
        for tick in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tick.set_pad(tick.get_pad() * scale)

    for text in fig.findobj(Text):
        text.set_fontsize(max(5.5, text.get_fontsize()))
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=out_dir / f"{stem}.alignment.json",
                                       overlay_svg=out_dir / f"{stem}.alignment.svg", tolerance_pt=1.5)
    fig.savefig(out_dir / f"{stem}.svg", facecolor="white")
    fig.savefig(out_dir / f"{stem}.pdf", facecolor="white")
    fig.savefig(out_dir / f"{stem}.png", dpi=600, facecolor="white")
    manifest = [{"id": stem, "stem": stem, "width": fig.get_figwidth()*72,
                 "height": fig.get_figheight()*72, "notes": CAPTION_ZH + "\nENGLISH:\n" + CAPTION_EN}]
    (build / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (build / "data/plotted_series.json").write_text(json.dumps(plotted_series, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    plt.close(fig)


if __name__ == "__main__":
    main()
