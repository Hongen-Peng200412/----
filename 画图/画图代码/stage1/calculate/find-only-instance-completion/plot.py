"""绘制Find实例完成度, 只读取冻结汇总, 不运行模型或重定科学条件.

入口main读取e2e/output/find-build-shared/data.json, 在temp/find-only-instance-completion写同源SVG/PDF/PNG和单图manifest.json. 图元沿用共享完成度函数, 当前PPT不自动覆盖.
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
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/find-only-instance-completion"

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

    fig = plt.figure(figsize=(180 / 25.4, 145 / 25.4))
    grid = fig.add_gridspec(2, 3, left=0.085, right=0.99, bottom=0.13, top=0.79, wspace=0.31, hspace=0.47)
    # 上排全配体、下排Stage1全部小分子94/821; 原Stage3的find_small面板仍保留, 本图不再选择它.
    for index, (scope, domain) in enumerate((('find_full', 'GT'), ('find_full', 'CA2'), ('find_full', 'Emap2lig'), ('find_stage1_small', 'GT'), ('find_stage1_small', 'CA2'), ('find_stage1_small', 'Emap2lig'))):
        panel = next(item for item in data['panels'] if item['scope'] == scope and item['domain'] == domain)
        ax = fig.add_subplot(grid[index // 3, index % 3])
        draw_panel(ax, panel, f"{'All ligands' if scope == 'find_full' else 'Small molecules'}, {domain}", chr(97 + index), True)
        if index % 3 == 0:
            ax.set_ylabel('Detected instances (%)', fontsize=8)
        if index >= 3:
            ax.set_xlabel('Relative candidate count (%)', fontsize=7.5)
        else:
            ax.tick_params(axis='x', labelbottom=False)
    fig.text(0.085, 0.97, 'Ligand detection across ranked candidates', fontsize=10.5, weight='bold', va='top')
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.075, 0.91), ncol=3, frameon=False, fontsize=7.5)
    # Find-only使用候选数量解释, 不引入端到端测评的尝试计费术语; 数值与取整仍沿用冻结统计.
    captions = (r'LigandSeek2-Find与Emap2lig-Find的配体实例检出比较。a–c，全配体，179个PDB、2,502个实例；d–f，全部小分子，94个PDB、821个实例。左、中列分别为LigandSeek2-Find使用沉积受体(GT)和CryoAtom2重建受体(CA2)，右列为Emap2lig-Find。候选与真实实例的双向覆盖均不低于$0.3$，并取几何平均最大的对应。横轴为依序考察的候选数相对于该PDB真实实例数的比例；$100\%$表示两者数量相同。全配体考察全部候选；小分子仅排除对应范围外真实配体的候选，保留背景候选。纵轴为检出的不同实例比例。绿线与圆点、蓝线与菱形分别表示PDB等权均值和中位数；灰点和小提琴表示$50\%$、$100\%$、$200\%$及$300\%$候选数量下的PDB分布。', r'Ligand-instance detection by LigandSeek2-Find and Emap2lig-Find. a–c, All ligands, comprising 179 PDBs and 2,502 instances. d–f, All small molecules, comprising 94 PDBs and 821 instances. Left and middle, LigandSeek2-Find with deposited receptors (GT) and CryoAtom2-reconstructed receptors (CA2), respectively. Right, Emap2lig-Find. Each candidate is assigned to the instance with maximal geometric-mean coverage among pairs with bidirectional coverage of at least $0.3$. The x-axis shows the number of candidates examined relative to the reference instance count per PDB; $100\%$ denotes equal counts. All candidates are examined for all ligands. For small molecules, candidates corresponding to out-of-scope ligands are omitted, while background candidates remain. The y-axis shows the fraction of distinct instances detected. Green lines and circles show the PDB-equal mean, and blue lines and diamonds show the median. Grey points and violins show PDB distributions at relative candidate counts of $50\%$, $100\%$, $200\%$ and $300\%$.')
    save_figure(fig, '01_find_only', 'find-only-instance-completion', *captions, manifest, BUILD)

    (BUILD / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Prepared '+manifest[0]['id'])


if __name__ == '__main__':
    main()
