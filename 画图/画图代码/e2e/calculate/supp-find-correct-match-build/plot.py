"""绘制给定正确身份的Find–Build完成度, 只读取冻结汇总, 不运行模型或重定科学条件.

入口main读取e2e/output/find-build-shared/data.json, 在temp/supp-find-correct-match-build写同源SVG/PDF/PNG和单图manifest.json. 图元沿用共享完成度函数, 当前PPT不自动覆盖.
"""
import os
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
sys.path.insert(0, str(ROOT / "画图/画图代码/e2e/calculate/find-build-shared"))
from completion_plot import DATA, INK, MEAN_COLOR, MEDIAN_COLOR, draw_panel, save_figure
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/supp-find-correct-match-build"

# ================================================================================================
def main():
    """按本图固定的面板选择和布局生成候选图稿; 统计输入和原图保持一致."""
    BUILD.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA.read_text(encoding='utf-8'))
    panels = {item['id']: item for item in data['panels']}
    manifest = []
    handles = [Line2D([], [], color=MEAN_COLOR, linewidth=1.8, marker='o', markersize=3.2, label='Mean'), Line2D([], [], color=MEDIAN_COLOR, linewidth=1.05, marker='D', markerfacecolor='none', markersize=3.5, label='Median'), Line2D([], [], color='#7F8C97', marker='o', linestyle='none', markersize=3, label='Individual PDB')]
    base_zh = r'每个PDB包含$N$个目标实例，相对预算$\rho$允许$\lfloor\rho N\rfloor$次计费尝试，完成度为成功的不同实例数除以$N$。绿线与圆点、蓝线与菱形分别表示PDB等权均值和中位数；灰点和小提琴表示$50\%$、$100\%$、$200\%$及$300\%$预算下的PDB分布。'
    base_en = r'For $N$ target instances per PDB, relative budget $\rho$ allows $\lfloor\rho N\rfloor$ charged attempts. Completion is the number of distinct successful instances divided by $N$. Green lines and circles show the PDB-equal mean, and blue lines and diamonds show the median. Grey points and violins show PDB distributions at $50\%$, $100\%$, $200\%$ and $300\%$ budgets.'

    fig = plt.figure(figsize=(180 / 25.4, 222 / 25.4))
    grid = fig.add_gridspec(6, 2, left=0.11, right=0.97, bottom=0.065, top=0.87, wspace=0.28, hspace=0.80)
    domains = ('Emap2lig', 'CA2', 'GT')  # 每种方法占相邻四面板, 从上向下按作者指定顺序.
    for index in range(12):
        domain = domains[index // 4]
        pose = 1 if index % 4 < 2 else 50
        threshold = 2.0 if index % 2 == 0 else 3.0
        panel = panels[f'assume_{domain}_pose{pose}_rmsd{threshold}']
        ax = fig.add_subplot(grid[index // 2, index % 2])
        draw_panel(ax, panel, f"{'Top-1' if pose == 1 else 'Best of 50'}, RMSD <{int(threshold)} Å", chr(97 + index), True)
        # 矮面板的字母与竖向轴标题错开; 仅调整标题位置, 不改变数据或坐标轴大小.
        ax.texts[-1].set_position((-0.14, 1.45))
        if index % 2 == 0:
            ax.set_ylabel('Completion (%)', fontsize=7.5)
        if index >= 10:
            ax.set_xlabel('Relative attempt budget (%)', fontsize=8)
        else:
            ax.tick_params(axis='x', labelbottom=False)
        if index % 4 == 0:
            fig.text(0.11, ax.get_position().y1 + 0.043, {'Emap2lig': 'Emap2lig', 'CA2': 'LigandSeek, CryoAtom2 receptor', 'GT': 'LigandSeek, deposited receptor'}[domain], fontsize=9.0, fontweight='bold', va='bottom')
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.10, 0.955), ncol=3, frameon=False, fontsize=7.5)
    captions = (r'假定身份匹配正确时单残基无缺失原子有机小分子的定位与建模完成度。各面板包含相同的77个PDB、446个实例。a–d，Emap2lig；e–h，CryoAtom2受体下的LigandSeek；i–l，沉积受体下的LigandSeek。每组上行为首选构象，下行为best-of-50；左、右列分别要求重原子RMSD严格$<2\,\mathrm{Å}$和$<3\,\mathrm{Å}$。所有已对应合格小分子的blob均给定正确SMILES；LigandSeek使用DG-PocketXmol单次中心对接，Emap2lig使用原生blob引导。背景计费，真实范围外前景免费；未检出与失败实例保留分母。' + base_zh, r'Find–Build completion of single-residue organic small molecules with no missing atoms, assuming correct ligand identities. Every panel contains the same 77 PDBs and 446 instances. a–d, Emap2lig. e–h, LigandSeek with CryoAtom2 receptors. i–l, LigandSeek with deposited receptors. Within each group, top and bottom rows show top-1 and best-of-50 poses; left and right columns require heavy-atom RMSD strictly $<2\,\mathrm{Å}$ and $<3\,\mathrm{Å}$. Every blob corresponding to an eligible small molecule receives the correct SMILES. LigandSeek uses single-pass DG-PocketXmol centre docking, whereas Emap2lig uses its native guiding blob. Background blobs are charged, and out-of-scope foreground blobs are skipped. Undetected and failed instances remain in the denominator.' + ' ' + base_en)
    save_figure(fig, '03_assume_matched', 'supp-find-correct-match-build', *captions, manifest, BUILD)
    (BUILD / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Prepared '+manifest[0]['id'])


if __name__ == '__main__':
    main()
