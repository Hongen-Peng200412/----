"""仅构造本目录声明的一张消融图, 全部当前采用面板保持原状."""

from functools import partial
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from TOOLS.ppt.matplotlib_export import export_scene, panel_title

title = partial(panel_title, title_size=6.8, label_size=8, pad=7, label_offset=(-19, 7))
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
WIDTH = 6.27


from pathlib import Path
from TOOLS.runtime.paths import load_module

FIG5 = Path(__file__).resolve().parents[2] / "正文/Fig5-result-Match&Build"
# Fig5唯一持有标准Build科学分布显示; 本图只传自己的协议数组, 不调用Fig5入口或9WUP.
boxes = load_module(FIG5 / "build_panels.py", "fig5_build_panels").boxes


def radar(ax, data, receptor, letter):
    """四轴均为身份准确率,不混入前景分类指标."""
    categories = ["overall", "small", "sugar", "metal"]
    angles = np.arange(4) * np.pi / 2
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    for key, label, col, ls, marker in [
        ("strongest", "Strongest", "#C0392B", "-", "o"),
        ("voxel", "Voxel-only", "#2980B9", "--", "s"),
        ("density", "Density-only", "#27AE60", "-.", "^"),
        ("pocket", "Pocket-only", "#8E44AD", ":", "D"),
    ]:
        vals = [data["match"]["ablation"][receptor][key][k]["accuracy_pct"] for k in categories]
        ax.plot(
            np.r_[angles, angles[0]],
            vals + vals[:1],
            color=col,
            ls=ls,
            marker=marker,
            ms=2.4,
            lw=1,
            label=label,
        )
        if key == "strongest":
            ax.fill(np.r_[angles, angles[0]], vals + vals[:1], color=col, alpha=0.07)
    ax.set_ylim(40, 95)
    ax.set_yticks([40, 60, 80, 95])
    ax.set_yticklabels(["40%", "60%", "80%", "95%"], fontsize=5.4, color="#666666")
    ax.set_xticks(angles, ["Overall\nSMILES", "Small\nmolecule", "Sugar", "Metal\nion"], fontsize=6)
    ax.tick_params(pad=2)
    ax.grid(color="#DDE3E6", lw=0.5)
    ax.spines["polar"].set_color("#AAAAAA")
    title(ax, letter, f"Match ablation ({receptor})")


def plot(data, build):
    """绘制本图全部Match雷达与标准Centre构象分布."""
    fig = plt.figure(figsize=(WIDTH, 6.1))
    gs = fig.add_gridspec(
        2, 2, left=0.1, right=0.93, top=0.91, bottom=0.11, wspace=0.31, hspace=0.45
    )
    for col, (r, l) in enumerate([("GT", "a"), ("CA2", "b")]):
        radar(fig.add_subplot(gs[0, col], projection="polar"), data, r, l)
    handles, labels = fig.axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        ncol=4,
        loc="center",
        bbox_to_anchor=(0.515, 0.515),
        fontsize=5.5,
        frameon=False,
        columnspacing=1.0,
        handlelength=2,
    )
    for col, (r, l) in enumerate([("GT", "c"), ("CA2", "d")]):
        boxes(fig.add_subplot(gs[1, col]), data, r, "C0", l)
    base = "身份匹配与密度引导构建的消融。a、b，沉积受体（GT）与CryoAtom2（CA2）条件下LigandSeek-Match四变体的身份准确率（分别1238、1160个身份支持blob）。c、d，GT与CA2条件下标准Centre口袋的三模型对照。"
    en = "Ablation of identity matching and density-guided pose construction. a, b, Identity accuracy of four LigandSeek-Match variants with deposited (GT) and CryoAtom2 (CA2) receptors (1,238 and 1,160 identity-supported blobs, respectively). c, d, Three-model comparison with standard Centre pockets and GT or CA2 receptors. "
    zh = (
        base
        + "Build使用完整446实例；原始模型GT有445个有效数值，其余各组446个。无密度微调模型新增核酸线性投影并共同微调整个网络。小提琴使用完整有效分布，箱体为第25–75百分位，白线为中位数，须为第10–85百分位，不绘离群散点。数字标注中位RMSD；参考线为1及2 Å。Top-5与best-of-50取原排序前5个及全部50个候选的最小RMSD。"
    )
    en += "Build uses the complete 446-instance benchmark; PocketXMol-official has 445 finite GT values and all other groups have 446. Simple fine-tuning adds a nucleic-acid linear projection and jointly updates the network without density input. Violins use the complete finite distributions; boxes span the 25th–75th percentiles, white lines denote medians, and whiskers span the 10th–85th percentiles. Outlier points are omitted. Labels report median RMSD; reference lines mark 1 and 2 Å. Top-5 and best-of-50 take the minimum RMSD among the original top five and all 50 candidates."
    page = export_scene(
        fig,
        "stage2-stage3-ablation-centre(v1)",
        zh + "\nENGLISH:\n" + en,
        build,
        [],
        dpi=400,
        text_width_extra=1,
        font_policy="Arial",
        default_font_size=8,
        require_panel_labels=True,
    )
    page["stem"] = "ablation"
    for index, shape in enumerate(page["shapes"]):
        shape["name"] = ("text_" if shape["kind"] == "text" else "ablation" + "_") + str(
            index + 836
        )
    return page
