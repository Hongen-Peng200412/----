"""用既有完成度绘图函数生成两张完整Find–Match–Build补图。

先由同组prepare_data.py生成本次master.json，再运行本入口和原生PPT运输入口。
actual面板对应自动身份匹配；不改动assume面板、既有补图或top-k汇报。
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
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"])
sys.path.insert(0, str(ROOT / "画图/画图代码/e2e/calculate/find-build-shared"))
from completion_plot import draw_panel, save_figure, MEAN_COLOR, MEDIAN_COLOR

# ================================================================================================
def main():
    """读取完整自动匹配面板，输出两张六面板图及双语图注，不修改正式PPT。"""
    master = json.loads((BUILD / "data/master.json").read_text(encoding="utf-8"))
    figures = BUILD / "figures"
    figures.mkdir(exist_ok=True)
    manifest = []
    handles = [Line2D([], [], color=MEAN_COLOR, linewidth=1.8, marker="o", markersize=3.2, label="Mean"), Line2D([], [], color=MEDIAN_COLOR, linewidth=1.05, marker="D", markerfacecolor="none", markersize=3.5, label="Median"), Line2D([], [], color="#7F8C97", marker="o", linestyle="none", markersize=3, label="Individual PDB")]
    base_en = (
        "Every panel contains the same 77 PDBs and 446 eligible small-molecule instances. Eligible small molecules are single-residue organic small molecules with no atoms missing relative to their templates. "
        r"a,b, Top-1 poses. c,d, Top-5 poses. e,f, Best-of-50 poses. Left and right columns require heavy-atom RMSD strictly $<2\,\mathrm{Å}$ and $<3\,\mathrm{Å}$, respectively. "
        "Top-5 and best-of-50 use the lowest RMSD among the first five and all 50 model-ranked poses, respectively. "
        "Match assigns each candidate blob an identity before Build. {build} "
        "Attempts follow the complete Find–Match–Build accounting protocol. Undetected and failed instances remain in the denominator. "
        r"For $N$ target instances per PDB, relative budget $\rho$ allows $\lfloor\rho N\rfloor$ charged attempts. Completion is the number of distinct successful instances divided by $N$. "
        r"Green lines and circles show the PDB-equal mean, and blue lines and diamonds show the median. Grey points and violins show PDB distributions at $50\%$, $100\%$, $200\%$ and $300\%$ budgets."
    )
    base_zh = (
        r"各面板包含相同的77个PDB、446个合格小分子实例，即单残基、相对于模板无缺失原子的有机小分子。a、b，Top-1；c、d，Top-5；e、f，best-of-50。左、右列分别要求重原子RMSD严格$<2\,\mathrm{Å}$和$<3\,\mathrm{Å}$。Top-5与best-of-50分别使用模型原排名前五和全部50个构象中的最低RMSD。"
        r"Match自动为候选blob指派身份，再交由Build构建。{build}按完整Find–Match–Build协议计费；未检出与失败实例保留分母。每PDB含$N$个目标实例，相对预算$\rho$允许$\lfloor\rho N\rfloor$次计费尝试，完成度为成功的不同实例数除以$N$。绿线与圆点、蓝线与菱形分别表示PDB等权均值和中位数；灰点和小提琴表示$50\%$、$100\%$、$200\%$及$300\%$预算下的PDB分布。"
    )
    for domain, suffix, title, en_condition, zh_condition, en_build, zh_build in (
        ("CA2", "ca2", "LigandSeek, CryoAtom2 receptor", "with CryoAtom2 receptors", "CryoAtom2重建受体条件下LigandSeek", "LigandSeek uses single-pass DG-PocketXMol centre docking.", "LigandSeek使用DG-PocketXMol单次中心对接。"),
        ("GT", "gt", "LigandSeek, deposited receptor", "with deposited receptors", "沉积受体条件下LigandSeek", "LigandSeek uses single-pass DG-PocketXMol centre docking.", "LigandSeek使用DG-PocketXMol单次中心对接。"),
    ):
        figure_id = "supp-find-match-build-" + suffix
        fig = plt.figure(figsize=(159.262 / 25.4, 162 / 25.4))
        grid = fig.add_gridspec(3, 2, left=0.11, right=0.97, bottom=0.085, top=0.855, wspace=0.28, hspace=0.64)
        for index in range(6):
            pose = (1, 5, 50)[index // 2]
            threshold = (2.0, 3.0)[index % 2]
            panel = master["panels"][f"actual_{domain}_pose{pose}_rmsd{threshold}"]
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
        caption_en = f"Find–Match–Build completion of small molecules {en_condition} with automated identity assignment. " + base_en.replace("{build}", en_build)
        caption_zh = f"自动身份匹配时{zh_condition}的小分子Find–Match–Build完成度。" + base_zh.replace("{build}", zh_build)
        save_figure(fig, figure_id, figure_id, caption_zh, caption_en, manifest, figures)
    (BUILD / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

if __name__ == "__main__":
    main()
