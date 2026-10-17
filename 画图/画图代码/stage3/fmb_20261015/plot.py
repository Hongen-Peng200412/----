"""从统一管线的冻结汇总绘制Find-only、预测位点对接和已知身份完成度.

main读取画图/formal/fmb_20261015/data.json, 在temp/fmb_20261015输出三组SVG/PDF/PNG与manifest.json.
完成度的阶梯、小提琴和散点复用completion_plot, 不重新计算预算或成功事件.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from completion_plot import BUILD, DATA, INK, MEAN_COLOR, MEDIAN_COLOR, draw_panel, save_figure


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
    ax.set(xlim=(0.45, 2.55), ylim=bounds, xticks=[1, 2], xticklabels=['PocketXMol-tuned', 'Emap2lig-Build'], ylabel='RMSD (Å)')
    ticks = [value for value in (0.1, 0.2, 0.5, 1, 2, 3, 5, 10, 20, 50, 100, 200) if bounds[0] <= value <= bounds[1]]
    ax.set_yticks(ticks, labels=[str(value) for value in ticks])
    ax.minorticks_off()
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=7, length=3, pad=3)
    ax.set_title(title, loc='left', fontsize=8.5, pad=10)
    ax.text(-0.18, 1.10, letter, transform=ax.transAxes, fontsize=10, fontweight='bold', va='top')


# ================================================================================================
def main():
    """按论文证据顺序生成三页同源图, 所有点、文字和线条随后转换成原生PPT形状.

    manifest.json为list[dict], 每页包含stem、id、width/height(pt)和中英notes, 不含手写图号.
    第1页Find-only为2行3列, 同列比较全配体与小分子; 第2页GT和CA2公平对接各两个面板; 第3页2列6行依次Emap2lig、CA2、GT.
    """
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
    save_figure(fig, '01_find_only', 'find-only-instance-completion', *captions, manifest)

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
    captions = (rf"预测配体区域引导下的PocketXMol-tuned与Emap2lig-Build对接比较。a,b，沉积受体(GT)条件下LigandSeek2-Find与Emap2lig-Find共同命中的{gt['common_count']}个实例；c,d，CryoAtom2重建受体(CA2)条件下共同命中的{ca2['common_count']}个实例。RMSD分布分别包含{gt['numeric_count']}和{ca2['numeric_count']}个配对实例。PocketXMol-tuned以LigandSeek2-Find完整blob的质心选取$15\,\mathrm{{Å}}$中心口袋；Emap2lig-Build使用其Find产生的原生三维blob。两者均给定正确SMILES，以100步生成50个候选。左列为模型评分首选构象，右列为50个候选中的最低重原子RMSD。散点表示实例，箱体为25–75百分位，中线为中位数，须为5–95百分位。纵轴为对数刻度；细虚线表示$2\,\mathrm{{Å}}$和$3\,\mathrm{{Å}}$。", rf"Docking performance of PocketXMol-tuned and Emap2lig-Build using predicted ligand regions. a,b, Deposited receptor (GT) comparison, comprising {gt['common_count']} instances detected by both LigandSeek2-Find and Emap2lig-Find. c,d, CryoAtom2-reconstructed receptor (CA2) comparison, comprising {ca2['common_count']} instances detected by both methods. The RMSD distributions contain {gt['numeric_count']} and {ca2['numeric_count']} paired instances, respectively. PocketXMol-tuned uses the full LigandSeek2-Find blob centroid to define a $15\,\mathrm{{Å}}$ centre pocket; Emap2lig-Build uses its native predicted three-dimensional blob. Both receive the correct SMILES and generate 50 candidates over 100 sampling steps. Left, model-ranked top-1 poses. Right, lowest heavy-atom RMSD among 50 candidates. Points represent instances, boxes span the 25th–75th percentiles, centre lines show medians and whiskers span the 5th–95th percentiles. The y-axis is logarithmic. Dashed lines mark $2\,\mathrm{{Å}}$ and $3\,\mathrm{{Å}}$.")
    save_figure(fig, '02_predicted_pose', 'stage3-predicted-region-head-to-head', *captions, manifest)

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
    fig.text(0.11, 0.98, 'Find–Build completion with correct ligand identities', fontsize=10.5, weight='bold', va='top')
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(0.10, 0.955), ncol=3, frameon=False, fontsize=7.5)
    captions = (r'假定身份匹配正确时单残基无缺失原子有机小分子的定位与建模完成度。各面板包含相同的77个PDB、446个实例。a–d，Emap2lig；e–h，CryoAtom2受体下的LigandSeek；i–l，沉积受体下的LigandSeek。每组上行为首选构象，下行为best-of-50；左、右列分别要求重原子RMSD严格$<2\,\mathrm{Å}$和$<3\,\mathrm{Å}$。所有已对应合格小分子的blob均给定正确SMILES；LigandSeek使用PocketXMol-tuned单次中心对接，Emap2lig使用原生blob引导。背景计费，真实范围外前景免费；未检出与失败实例保留分母。' + base_zh, r'Find–Build completion of single-residue organic small molecules with no missing atoms, assuming correct ligand identities. Every panel contains the same 77 PDBs and 446 instances. a–d, Emap2lig. e–h, LigandSeek with CryoAtom2 receptors. i–l, LigandSeek with deposited receptors. Within each group, top and bottom rows show top-1 and best-of-50 poses; left and right columns require heavy-atom RMSD strictly $<2\,\mathrm{Å}$ and $<3\,\mathrm{Å}$. Every blob corresponding to an eligible small molecule receives the correct SMILES. LigandSeek uses single-pass PocketXMol-tuned centre docking, whereas Emap2lig uses its native guiding blob. Background blobs are charged, and out-of-scope foreground blobs are skipped. Undetected and failed instances remain in the denominator.' + ' ' + base_en)
    save_figure(fig, '03_assume_matched', 'supp-find-correct-match-build', *captions, manifest)
    (BUILD / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Prepared three editable-source figure pages.')


if __name__ == '__main__':
    main()
