"""按三种方法分别绘制 Find–Build 的六面板补图, 并登记主图和双语图注.

入口 main 读取同次 data/master.json, 复用原 completion_plot.draw_panel 的分布与事件阶梯.
每张补图为3行2列, 行依次为 Top-1、Top-5、best-of-50, 列为严格 RMSD <2、<3 Å.
输出 figures/*.svg/.pdf/.png、对齐报告及 manifest.json; 不修改原图或正式 PPT.
manifest 的每项保存稳定图名 id、文件前缀 stem、物理宽高 width/height(单位 pt)及 notes 中的双语图注.
"""

import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/e2e_top5_20261102/build"
sys.path.insert(0, str(ROOT / "画图/画图代码/e2e/calculate/find-build-shared"))
from completion_plot import draw_panel, save_figure, MEAN_COLOR, MEDIAN_COLOR


def main():
    """保持原补图图元和统计表达, 只拆方法组、增加原排名 Top-5 行及必要的面板图注."""
    master = json.loads((BUILD / "data/master.json").read_text(encoding="utf-8"))
    figures = BUILD / "figures"
    figures.mkdir(exist_ok=True)
    geometry = json.loads((figures / "e2e-main-top5.geometry.json").read_text(encoding="utf-8"))
    main_en = (
        "End-to-end ligand detection, chemical identification and small-molecule pose reconstruction. "
        "Pipeline colours are unified across panels: Emap2lig (brown), LigandSeek with CryoAtom2-reconstructed receptors (CA2, blue) and LigandSeek with deposited receptors (GT, teal). "
        "a, Per-PDB mean completion across all ligands (179 PDB entries; 2,502 instances) for Find only (dashed lines, open circles) and Find + Match (solid lines, filled circles). "
        "Error bars show percentile 95% confidence intervals from 10,000 PDB bootstrap resamples. "
        "b, Find + Build completion with correct SMILES at 100% (dark lines) and 300% (light lines) budgets. "
        "Filled and open circles indicate Top-1 and Top-5 completion, respectively. "
        "c, d, Small-molecule Find–Match–Build completion with CA2 (c) and GT (d) receptors at 100% and 300% budgets. "
        "Pale dashed bars show Find-only and Find + Match completion. Dark solid bars show Top-1 completion; light caps show the additional Top-5 gain. "
        "The two modelling bars in each budget group require heavy-atom RMSD <3 Å and <2 Å, respectively. "
        "Panels b–d include 77 PDB entries and 446 eligible small-molecule instances, defined as single-residue organic small molecules with no atoms missing relative to their templates. "
        "Top-5 uses the lowest RMSD among the five highest-ranked poses. All completion values are PDB-equal means. "
        r"For $N$ target instances per PDB, relative budget $\rho$ permits $\lfloor\rho N\rfloor$ charged attempts; completion is the fraction of distinct target instances successfully processed."
    )
    main_zh = (
        "配体检测、化学身份识别与小分子构象重建的端到端表现。各面板统一使用棕色表示Emap2lig、蓝色表示CryoAtom2重建受体（CA2）条件下的LigandSeek、青色表示沉积受体（GT）条件下的LigandSeek。"
        "a，全配体范围（179个PDB、2,502个实例）中仅Find（虚线、空心圆）与Find＋Match（实线、实心圆）的逐PDB平均完成度；误差线为10,000次PDB bootstrap重采样的百分位95%置信区间。"
        "b，给定正确SMILES时100%（深色线）与300%（浅色线）预算下的Find＋Build完成度；实心圆和空心圆分别表示Top-1和Top-5。"
        "c、d，CA2（c）和GT（d）受体条件下100%与300%预算的Find–Match–Build完成度。浅色虚线柱表示仅Find与Find＋Match；深色实线柱表示Top-1，浅色顶段表示Top-5带来的额外完成度。每个预算组的两个建模柱依次要求重原子RMSD严格小于3Å和2Å。"
        r"b–d包含77个PDB、446个合格小分子实例，即单残基、相对于模板无缺失原子的有机小分子。Top-5为模型原排名前五构象中的最低RMSD；全部完成度按PDB等权平均。每PDB含$N$个目标实例，相对预算$\rho$允许$\lfloor\rho N\rfloor$次计费尝试，完成度为成功处理的不同目标实例比例。"
    )
    manifest = [{"id": "e2e-main-top5", "stem": "e2e-main-top5", "width": geometry["width_mm"] / 25.4 * 72, "height": geometry["height_mm"] / 25.4 * 72, "notes": main_zh + "\nENGLISH:\n" + main_en}]
    handles = [Line2D([], [], color=MEAN_COLOR, linewidth=1.8, marker="o", markersize=3.2, label="Mean"), Line2D([], [], color=MEDIAN_COLOR, linewidth=1.05, marker="D", markerfacecolor="none", markersize=3.5, label="Median"), Line2D([], [], color="#7F8C97", marker="o", linestyle="none", markersize=3, label="Individual PDB")]
    base_en = (
        "Every panel contains the same 77 PDBs and 446 eligible small-molecule instances. Eligible small molecules are single-residue organic small molecules with no atoms missing relative to their templates. "
        r"a,b, Top-1 poses. c,d, Top-5 poses. e,f, Best-of-50 poses. Left and right columns require heavy-atom RMSD strictly $<2\,\mathrm{Å}$ and $<3\,\mathrm{Å}$, respectively. "
        "Top-5 and best-of-50 use the lowest RMSD among the first five and all 50 model-ranked poses, respectively. "
        "Every blob corresponding to an eligible small molecule receives the correct SMILES. {build} "
        "Background blobs are charged, and out-of-scope foreground blobs are skipped. Undetected and failed instances remain in the denominator. "
        r"For $N$ target instances per PDB, relative budget $\rho$ allows $\lfloor\rho N\rfloor$ charged attempts. Completion is the number of distinct successful instances divided by $N$. "
        r"Green lines and circles show the PDB-equal mean, and blue lines and diamonds show the median. Grey points and violins show PDB distributions at $50\%$, $100\%$, $200\%$ and $300\%$ budgets."
    )
    base_zh = (
        r"各面板包含相同的77个PDB、446个合格小分子实例，即单残基、相对于模板无缺失原子的有机小分子。a、b，Top-1；c、d，Top-5；e、f，best-of-50。左、右列分别要求重原子RMSD严格$<2\,\mathrm{Å}$和$<3\,\mathrm{Å}$。Top-5与best-of-50分别使用模型原排名前五和全部50个构象中的最低RMSD。"
        r"所有对应合格小分子的blob均给定正确SMILES。{build}背景计费，真实范围外前景免费；未检出与失败实例保留分母。每PDB含$N$个目标实例，相对预算$\rho$允许$\lfloor\rho N\rfloor$次计费尝试，完成度为成功的不同实例数除以$N$。绿线与圆点、蓝线与菱形分别表示PDB等权均值和中位数；灰点和小提琴表示$50\%$、$100\%$、$200\%$及$300\%$预算下的PDB分布。"
    )
    for domain, suffix, title, en_condition, zh_condition, en_build, zh_build in (
        ("Emap2lig", "emap2lig", "Emap2lig", "with Emap2lig", "Emap2lig", "Emap2lig uses its native guiding blob.", "Emap2lig使用原生blob引导。"),
        ("CA2", "ca2", "LigandSeek, CryoAtom2 receptor", "with CryoAtom2 receptors", "CryoAtom2重建受体条件下LigandSeek", "LigandSeek uses single-pass DG-PocketXMol centre docking.", "LigandSeek使用DG-PocketXMol单次中心对接。"),
        ("GT", "gt", "LigandSeek, deposited receptor", "with deposited receptors", "沉积受体条件下LigandSeek", "LigandSeek uses single-pass DG-PocketXMol centre docking.", "LigandSeek使用DG-PocketXMol单次中心对接。"),
    ):
        figure_id = "supp-find-correct-match-build-" + suffix
        fig = plt.figure(figsize=(159.262 / 25.4, 162 / 25.4))
        grid = fig.add_gridspec(3, 2, left=0.11, right=0.97, bottom=0.085, top=0.855, wspace=0.28, hspace=0.64)
        for index in range(6):
            pose = (1, 5, 50)[index // 2]
            threshold = (2.0, 3.0)[index % 2]
            panel = master["panels"][f"assume_{domain}_pose{pose}_rmsd{threshold}"]
            ax = fig.add_subplot(grid[index // 2, index % 2])
            pose_label = {1: "Top-1", 5: "Top-5", 50: "Best-of-50"}[pose]
            draw_panel(ax, panel, f"{pose_label}, RMSD <{threshold:g} Å", chr(97 + index), True)
            ax.texts[-1].set_position((-0.14, 1.26))
            if index % 2 == 0:
                ax.set_ylabel("Completion (%)", fontsize=7.5)
            if index >= 4:
                ax.set_xlabel("Relative attempt budget (%)", fontsize=8)
            else:
                ax.tick_params(axis="x", labelbottom=False)
        fig.text(0.11, 0.973, title, fontsize=9.3, fontweight="bold", va="top")
        fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.10, 0.94), ncol=3, frameon=False, fontsize=7.5)
        caption_en = f"Find–Build completion of small molecules {en_condition}, assuming correct ligand identities. " + base_en.replace("{build}", en_build)
        caption_zh = f"假定配体身份正确时{zh_condition}的小分子Find–Build完成度。" + base_zh.replace("{build}", zh_build)
        save_figure(fig, figure_id, figure_id, caption_zh, caption_en, manifest, figures)
    (BUILD / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Prepared 4 figures and bilingual notes")


if __name__ == "__main__":
    main()
