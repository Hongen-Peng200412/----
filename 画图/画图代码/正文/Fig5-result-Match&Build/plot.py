"""只绘制正文Fig5的九面板, 科学数组由同图science.py提供."""

from functools import partial
import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from TOOLS.ppt.matplotlib_export import export_scene, panel_title, y_grid

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
M = [
    ("overall", "Overall", "#1C2833", "D"),
    ("small", "Small molecule", "#2E86C1", "o"),
    ("metal", "Metal ion", "#28B463", "s"),
    ("sugar", "Sugar", "#D35400", "^"),
]
WIDTH = 6.27


def plot(data, output):
    """Build三个面板使用235固定分母;第三行复用作者的三个原生病例视图."""
    fig = plt.figure(figsize=(WIDTH, 6.55))
    gs = fig.add_gridspec(
        3,
        3,
        left=0.073,
        right=0.987,
        bottom=0.025,
        top=0.945,
        wspace=0.34,
        hspace=0.65,
        height_ratios=[1, 1, 0.85],
    )
    axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
    ax = axes[0]
    x = np.arange(4)
    for receptor, off in [("GT", -0.19), ("CA2", 0.19)]:
        vals = [data["match"]["categories"][receptor][m[0]]["accuracy_pct"] for m in M]
        ax.bar(x + off, vals, 0.36, color=C[receptor], alpha=0.8, zorder=2)
        for pos, val in zip(x + off, vals):
            ax.text(pos, val + 1.4, f"{val:.1f}", ha="center", fontsize=5.2, color=C[receptor])
    ax.set_xticks(x, ["Overall", "Small\nmolecule", "Metal\nion", "Sugar"])
    ax.set_ylim(0, 107)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_ylabel("Matching accuracy (%)")
    grid(ax)
    title(ax, "a", "Match: category accuracy")
    ax.legend(
        handles=[Patch(color=C[k], alpha=0.8, label=k) for k in ("GT", "CA2")],
        loc="lower left",
        fontsize=5.3,
        handlelength=1,
        borderpad=0.3,
    )
    for ax, receptor, letter in zip(axes[1:3], ["GT", "CA2"], ["b", "c"]):
        for key, label, color, marker in M:
            yy = data["match"]["by_candidate_count"][receptor][key]["accuracy_pct"]
            ax.plot(
                np.arange(5),
                yy,
                color=color,
                marker=marker,
                ms=2.6,
                ls="-" if key == "overall" else "--",
                label=label,
                lw=1 if key == "overall" else 0.8,
            )
        ax.set_xticks(np.arange(5), ["1", "2", "3", "4", "≥5"])
        ax.set_xlim(-0.12, 4.12)
        ax.set_ylim(35, 105)
        ax.set_yticks([40, 60, 80, 100])
        ax.set_xlabel("Candidate SMILES per PDB")
        ax.set_ylabel("Matching accuracy (%)")
        grid(ax)
        title(ax, letter, f"Match ({receptor})")
        ax.legend(
            loc="lower left",
            fontsize=5.2,
            handlelength=1.5,
            labelspacing=0.18,
            borderpad=0.3,
            framealpha=0.95,
        )
    build = data["main_build"]
    n = build["denominator"]
    ax = axes[3]
    for name in ("Emap2lig", "CA2", "GT"):
        for pose, style in [("top1", "-"), ("top5", "--")]:
            arr = np.sort(build["series"][name][pose])
            # 严格小于阈值的经验分布;完整n参与分母,窗口只显示0–4Å.
            xx = np.unique(
                np.r_[[0, 1, 2, 3, 4], np.linspace(0, 4, 400), arr[(arr >= 0) & (arr <= 4)]]
            )
            yy = np.searchsorted(arr, xx, side="left") / n * 100
            ax.step(xx, yy, where="pre", color=C[name], ls=style, lw=1)
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 103)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xlabel("RMSD threshold (Å)")
    ax.set_ylabel("Cumulative success (%)")
    for t, style in [(1, ":"), (2, "--")]:
        ax.axvline(t, color="#666666", ls=style, lw=0.65)
    handles = [
        Line2D([], [], color=C[k], label=v)
        for k, v in [("Emap2lig", "Emap2lig-Build"), ("CA2", "DG (CA2)"), ("GT", "DG (GT)")]
    ]
    leg = ax.legend(
        handles=handles, loc="lower right", fontsize=5.2, borderpad=0.3, labelspacing=0.3
    )
    ax.add_artist(leg)
    ax.legend(
        handles=[
            Line2D([], [], color="#555555", ls=s, label=l)
            for s, l in [("-", "Top-1"), ("--", "Top-5")]
        ],
        loc="upper left",
        fontsize=5.2,
        borderpad=0.3,
    )
    title(ax, "d", "Build: cumulative accuracy")
    grid(ax)
    ax = axes[4]
    poses = ["top1", "top5", "best50"]
    handles = []
    for offset, name, label in [
        (-0.25, "Emap2lig", "Emap2lig"),
        (0, "CA2", "DG (CA2)"),
        (0.25, "GT", "DG (GT)"),
    ]:
        values = [np.asarray(build["series"][name][p]) for p in poses]
        low = [np.mean(a < 1) * 100 for a in values]
        high = [np.mean(a < 2) * 100 for a in values]
        xx = np.arange(3) + offset
        ax.bar(
            xx, high, 0.22, color=C[name], alpha=0.34, edgecolor=C[name], linewidth=0.6, zorder=2
        )
        ax.bar(xx, low, 0.22, color=C[name], alpha=0.95, zorder=3)
        for xp, lo, hi in zip(xx, low, high):
            ax.text(xp, hi + 1.4, f"{hi:.0f}", ha="center", fontsize=5.2, color=C[name])
            ax.text(
                xp,
                max(lo / 2, 3.5),
                f"{lo:.0f}",
                ha="center",
                va="center",
                fontsize=5.2,
                color="white",
            )
        handles.extend(
            [
                Patch(facecolor=C[name], label=label + " <1 Å"),
                Patch(facecolor=C[name], alpha=0.34, label=label + " <2 Å"),
            ]
        )
    # 图例同模型同一行,左<1Å、右<2Å;matplotlib按列填充.
    order = [0, 2, 4, 1, 3, 5]
    ax.legend(
        handles=[handles[i] for i in order],
        ncol=2,
        loc="upper center",
        fontsize=5.05,
        columnspacing=0.6,
        handlelength=0.9,
        handletextpad=0.3,
        labelspacing=0.18,
        borderpad=0.25,
    )
    ax.set_ylim(0, 137)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xticks(range(3), ["Top-1", "Top-5", "Best of 50"])
    ax.set_ylabel("Success rate (%)")
    title(ax, "e", "Build: success thresholds")
    grid(ax)
    ax = axes[5]
    e = np.asarray(build["series"]["Emap2lig"]["top1"])
    ax.fill_between([0, 5], [0, 0], [0, 5], color="#EAF2F8", alpha=0.7)
    ax.plot([0, 5], [0, 5], "--", color="#333333", lw=0.7)
    for name, marker in [("CA2", "^"), ("GT", "o")]:
        arr = np.asarray(build["series"][name]["top1"])
        win = np.mean(arr < e) * 100
        ax.scatter(
            np.minimum(e, 5),
            np.minimum(arr, 5),
            s=5.2,
            color=C[name],
            alpha=0.55,
            marker=marker,
            edgecolors="none",
            label=f"{name}: {win:.1f}% wins",
        )
    ax.set_xlim(0, 5.15)
    ax.set_ylim(0, 5.15)
    for dim in ("x", "y"):
        getattr(ax, f"set_{dim}ticks")([0, 1, 2, 3, 4, 5], ["0", "1", "2", "3", "4", "≥5"])
    ax.axhline(2, ls=":", color="#999999", lw=0.55)
    ax.axvline(2, ls=":", color="#999999", lw=0.55)
    ax.set_xlabel("Emap2lig-Build RMSD (Å)")
    ax.set_ylabel("DG-PocketXMol RMSD (Å)")
    ax.legend(loc="upper left", fontsize=5.2, borderpad=0.3, handlelength=1, labelspacing=0.3)
    title(ax, "f", "Build: paired Top-1 poses")
    # 目标区域为SVG/PPT左上角起算的pt;分子原生对象稍后按同一尺寸注入.
    fig.text(
        0.53,
        1 - 351 / (6.55 * 72),
        "9WUP · FAD (A:1103)",
        ha="center",
        fontsize=7,
        fontweight="bold",
    )
    case_rects = []
    for c, letter in enumerate("ghi"):
        box = gs[2, c].get_position(fig)
        x0 = box.x0 * WIDTH * 72
        y0 = (1 - box.y1) * 6.55 * 72
        fig.text(
            (x0 - 19) / (WIDTH * 72),
            (6.55 * 72 - y0 + 7) / (6.55 * 72),
            letter,
            fontsize=8,
            fontweight="bold",
        )
        case_rects.append([x0 - 6, y0, box.width * WIDTH * 72 + 8, box.height * 6.55 * 72])
    (output / "case_rects.json").write_text(json.dumps(case_rects), encoding="utf-8")
    notes = (
        "配体身份匹配与构象构建。a，LigandSeek-Match在GT与CA2受体条件下的总体及分类匹配准确率。b、c，按每个PDB的候选SMILES身份数分层；Overall按正确数及支持数汇总。a–c的身份支持blob分别为1238（GT）与1160（CA2）。d–f使用三个方法共同检出且可评价的235个实例。d，Top-1（实线）和Top-5（虚线）的累计成功率。e，深色为RMSD<1 Å，浅色柱总高为<2 Å。Top-5及best-of-50分别取原排序前5个及全部50个候选的最小RMSD。f，Top-1配对比较；≥5 Å显示在边界，胜率由未截断值计算。g–i，9WUP的FAD（A:1103）：原始PocketXMol、DG-PocketXMol及Emap2lig-Build的原有视图，叠加显示沉积受体；前两者以该受体的标准Centre口袋为输入。D为推荐密度阈值覆盖的配体重原子比例，Clash为受体碰撞原子对数。\nENGLISH:\n"
        "Ligand identity matching and pose construction. a, Overall and class-specific accuracy of LigandSeek-Match with deposited (GT) and CryoAtom2 (CA2) receptors. b, c, Accuracy by the number of candidate SMILES identities per PDB; Overall pools correct assignments and supports. a–c include 1,238 (GT) and 1,160 (CA2) identity-supported blobs. d–f, Comparison on 235 jointly detected, evaluable instances. d, Cumulative success for Top-1 (solid) and Top-5 (dashed). e, Dark bars show RMSD <1 Å; total light-bar heights show <2 Å. Top-5 and best-of-50 report the minimum RMSD among the original top five and all 50 candidates, respectively. f, Paired Top-1 RMSDs; values ≥5 Å appear at the boundary, with wins calculated before capping. g–i, FAD (A:1103) in 9WUP: PocketXMol-official, DG-PocketXMol and Emap2lig-Build. Overlaid receptors are the deposited structures; the first two methods use standard Centre pockets. D denotes the fraction of ligand heavy atoms above the recommended density threshold; Clash counts receptor-clashing atom pairs."
    )
    page = export_scene(
        fig,
        "stage2-stage3-results(v1)",
        notes,
        output,
        [],
        dpi=400,
        text_width_extra=1,
        font_policy="Arial",
        default_font_size=8,
        require_panel_labels=True,
    )
    page["stem"] = "results"
    for index, shape in enumerate(page["shapes"]):
        shape["name"] = ("text_" if shape["kind"] == "text" else "results_") + str(index)
    return page
