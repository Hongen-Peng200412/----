"""仅构造本目录声明的一张消融图, 全部当前采用面板保持原状."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from TOOLS.ppt.matplotlib_export import export_scene

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


def plot(data, build):
    """绘制本图GT/CA2两组标准Envelope构象分布."""
    fig = plt.figure(figsize=(WIDTH, 3.2))
    gs = fig.add_gridspec(
        1, 2, left=0.1, right=0.93, top=0.91, bottom=0.19, wspace=0.31, hspace=0.45
    )
    for col, (r, l) in enumerate([("GT", "a"), ("CA2", "b")]):
        boxes(fig.add_subplot(gs[0, col]), data, r, "E", l)
    base = "Envelope口袋中的构象构建消融。a、b，GT与CA2受体条件。"
    en = "Pose-construction ablation with Envelope pockets. a, b, Deposited (GT) and CryoAtom2 (CA2) receptors. "
    zh = (
        base
        + "Build使用完整446实例；原始模型GT有445个有效数值，其余各组446个。无密度微调模型新增核酸线性投影并共同微调整个网络。小提琴使用完整有效分布，箱体为第25–75百分位，白线为中位数，须为第10–85百分位，不绘离群散点。数字标注中位RMSD；参考线为1及2 Å。Top-5与best-of-50取原排序前5个及全部50个候选的最小RMSD。"
    )
    en += "Build uses the complete 446-instance benchmark; PocketXMol-official has 445 finite GT values and all other groups have 446. Simple fine-tuning adds a nucleic-acid linear projection and jointly updates the network without density input. Violins use the complete finite distributions; boxes span the 25th–75th percentiles, white lines denote medians, and whiskers span the 10th–85th percentiles. Outlier points are omitted. Labels report median RMSD; reference lines mark 1 and 2 Å. Top-5 and best-of-50 take the minimum RMSD among the original top five and all 50 candidates."
    page = export_scene(
        fig,
        "stage3-ablation-envelope",
        zh + "\nENGLISH:\n" + en,
        build,
        [],
        dpi=400,
        text_width_extra=1,
        font_policy="Arial",
        default_font_size=8,
        require_panel_labels=True,
    )
    page["stem"] = "envelope"
    for index, shape in enumerate(page["shapes"]):
        shape["name"] = ("text_" if shape["kind"] == "text" else "envelope" + "_") + str(
            index + 1169
        )
    return page
