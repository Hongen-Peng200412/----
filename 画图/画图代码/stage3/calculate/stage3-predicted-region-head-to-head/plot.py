"""绘制预测区域引导的配对构象比较, 只读取冻结汇总, 不运行模型或重定科学条件.

入口main读取e2e/output/find-build-shared/data.json, 在temp/stage3-predicted-region-head-to-head写同源SVG/PDF/PNG和单图manifest.json. 图元沿用共享完成度函数, 当前PPT不自动覆盖.
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
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/stage3-predicted-region-head-to-head"

def draw_rmsd(ax, pair, field, title, letter, bounds):
    """在一个面板展示同一共同命中子集的两种模型逐实例RMSD.

    输入参数:
        - ax: Matplotlib Axes, 一个独立子图, 保留自己的RMSD轴、单位和刻度.
        - pair: dict, domain指定GT或CA2; numeric_rows为两边均有Top-1与best距离的配对实例列表.
        - field: str, top1或best, 读取tuned/emap的对应世界坐标RMSD, 单位Å.
        - title、letter: str, 当前受体与姿态条件标题、面板字母.
        - bounds: tuple[float,float], 四个面板共用的正值y轴范围, 单位Å.
    返回值:
        - 无. 在ax绘制全部实例散点、25–75百分位箱体、中位数和5–95百分位须; y轴为对数轴, 2/3 Å细虚线只作读数参考, 不参与成功判断.
    """
    colours = ('#2D887E' if pair['domain'] == 'GT' else '#5879BD', '#B57442')
    for position, (model, colour) in enumerate(zip(('tuned', 'emap'), colours), 1):
        values = np.asarray([item[f'{model}_{field}'] for item in pair['numeric_rows']])  # (N_pair,), 逐实例距离, Å; N_pair为四项距离均有效的配对实例数.
        jitter = np.asarray([(int.from_bytes(f"{item['pdb_id']}/{item['occurrence_id']}".encode(), 'little') % 997 / 996 - 0.5) * 0.30 for item in pair['numeric_rows']])
        ax.scatter(position + jitter, values, s=5, color=colour, alpha=0.30, edgecolor='none', zorder=2)
        p05, p25, median, p75, p95 = np.quantile(values, [0.05, 0.25, 0.5, 0.75, 0.95])
        ax.bxp([{'med': median, 'q1': p25, 'q3': p75, 'whislo': p05, 'whishi': p95}], positions=[position], widths=0.25, showfliers=False, patch_artist=True, boxprops={'facecolor': 'white', 'edgecolor': colour, 'linewidth': 1.0}, medianprops={'color': colour, 'linewidth': 1.5}, whiskerprops={'color': colour, 'linewidth': 0.7}, capprops={'color': colour, 'linewidth': 0.7}, zorder=3)
    for threshold in (2, 3):
        ax.axhline(threshold, color='#BCC5CB', linewidth=0.6, linestyle=(0, (3, 3)), zorder=0)
    ax.set_yscale('log')
    ax.set(xlim=(0.45, 2.55), ylim=bounds, xticks=[1, 2], xticklabels=['DG-PocketXmol', 'Emap2lig-Build'], ylabel='RMSD (Å)')
    ticks = [value for value in (0.1, 0.2, 0.5, 1, 2, 3, 5, 10, 20, 50, 100, 200) if bounds[0] <= value <= bounds[1]]
    ax.set_yticks(ticks, labels=[str(value) for value in ticks])
    ax.minorticks_off()
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=7, length=3, pad=3)
    ax.set_title(title, loc='left', fontsize=8.5, pad=10)
    ax.text(-0.18, 1.10, letter, transform=ax.transAxes, fontsize=10, fontweight='bold', va='top')

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
    grid = fig.add_gridspec(2, 2, left=0.11, right=0.97, bottom=0.11, top=0.85, wspace=0.32, hspace=0.50)
    # 四组同用实际数值的全范围; 所有极端值保留, 不对长尾截断或缩尾.
    distances = [item[f'{model}_{pose}'] for pair in data['pairs'].values() for item in pair['numeric_rows'] for model in ('tuned', 'emap') for pose in ('top1', 'best')]
    bounds = (min(0.2, min(distances) * 0.8), max(25, max(distances) * 1.12))
    for index, (domain, pose) in enumerate((('GT', 'top1'), ('GT', 'best'), ('CA2', 'top1'), ('CA2', 'best'))):
        pair = {**data['pairs'][domain], 'domain': domain}
        ax = fig.add_subplot(grid[index // 2, index % 2])
        draw_rmsd(ax, pair, pose, f"{domain}, {'Top-1 pose' if pose == 'top1' else 'Best of 50'}", chr(97 + index), bounds)
    fig.text(0.11, 0.98, 'Docking guided by predicted ligand regions', fontsize=10.5, weight='bold', va='top')
    gt, ca2 = data['pairs']['GT'], data['pairs']['CA2']
    captions = (rf"预测配体区域引导下的DG-PocketXmol与Emap2lig-Build对接比较。a,b，沉积受体(GT)条件下LigandSeek2-Find与Emap2lig-Find共同命中的{gt['common_count']}个实例；c,d，CryoAtom2重建受体(CA2)条件下共同命中的{ca2['common_count']}个实例。RMSD分布分别包含{gt['numeric_count']}和{ca2['numeric_count']}个配对实例。DG-PocketXmol以LigandSeek2-Find完整blob的质心选取$15\,\mathrm{{Å}}$中心口袋；Emap2lig-Build使用其Find产生的原生三维blob。两者均给定正确SMILES，以100步生成50个候选。左列为模型评分首选构象，右列为50个候选中的最低重原子RMSD。散点表示实例，箱体为25–75百分位，中线为中位数，须为5–95百分位。纵轴为对数刻度；细虚线表示$2\,\mathrm{{Å}}$和$3\,\mathrm{{Å}}$。", rf"Docking performance of DG-PocketXmol and Emap2lig-Build using predicted ligand regions. a,b, Deposited receptor (GT) comparison, comprising {gt['common_count']} instances detected by both LigandSeek2-Find and Emap2lig-Find. c,d, CryoAtom2-reconstructed receptor (CA2) comparison, comprising {ca2['common_count']} instances detected by both methods. The RMSD distributions contain {gt['numeric_count']} and {ca2['numeric_count']} paired instances, respectively. DG-PocketXmol uses the full LigandSeek2-Find blob centroid to define a $15\,\mathrm{{Å}}$ centre pocket; Emap2lig-Build uses its native predicted three-dimensional blob. Both receive the correct SMILES and generate 50 candidates over 100 sampling steps. Left, model-ranked top-1 poses. Right, lowest heavy-atom RMSD among 50 candidates. Points represent instances, boxes span the 25th–75th percentiles, centre lines show medians and whiskers span the 5th–95th percentiles. The y-axis is logarithmic. Dashed lines mark $2\,\mathrm{{Å}}$ and $3\,\mathrm{{Å}}$.")
    save_figure(fig, '02_predicted_pose', 'stage3-predicted-region-head-to-head', *captions, manifest, BUILD)

    (BUILD / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Prepared '+manifest[0]['id'])


if __name__ == '__main__':
    main()
