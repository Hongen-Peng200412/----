"""读取统一管线的最终结果, 为三组论文图固定数据.

入口main读取画图/formal/fmb_20261015/sources内三个域的原始结果,
写出同目录data.json、paired_pose.csv和summary.json. 不执行模型、姿态排名或体素交集重算; Emap2lig的对应决策直接复用原函数.
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np

# 只复用既有对应决策和精确预算汇总, 不导入Find、Match或Build模型.
PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT.parent / 'AdaLigand'))
sys.path.insert(0, str(PROJECT.parent / 'Matcher'))
from ligandseek_pipeline.completion import make_panel
from test_smallmolecule.build_manifest import _target_from_intersections


# ================================================================================================
def main():
    """连接原blob对应和姿态结果, 保留完整分母及有数值的配对分布.

    输入:
        - sources/{GT,CA2,Emap2lig}/docking_results.jsonl: 每blob一条, matched_occurrence_id连接真实实例; pose_min_rmsd_A的1/50为原模型Top-1和best-of-50距离, 单位Å, 失败为None.
        - completion.json: 原24个panels, 逐PDB分母、精确预算曲线和分布不再重算.
        - sources/Emap2lig/find_metadata: inventory.json固定179/2502分母; per_pdb的原交集、区域大小、概率及选择标志沿用原对应; identities.jsonl与emap2lig_candidates.jsonl固定77/446小分子视图.
        - 画图/formal/Stage1_find_completion_20261017/panels.json: Stage1全部小分子的94/821统计; 只追加论文面板, 不覆盖原Stage3视图.
    产物:
        - data.json: dict, panels为三域面板列表; pairs[GT/CA2]含共同实例数、配对数值实例及两模型统计.
        - paired_pose.csv: 共同命中的全部实例, 含两种模型的Top-1和best距离, 缺失为空, 不填替代数值.
        - summary.json: 各比较的统计及完整面板的原预算分布摘要, 用于图注、结果和表格.
    """
    root = Path(__file__).resolve().parents[4] / '画图/formal/fmb_20261015'
    direct, panels = {}, []  # direct按域保存既有对应实例; panels保留原预算事件和逐PDB分布.
    for domain in ('GT', 'CA2', 'Emap2lig'):
        source = root / 'sources' / domain
        records = [json.loads(line) for line in (source / 'docking_results.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        # 实例编号只在同一PDB内有效; 冻结候选中每个合格实例只对应一个blob.
        direct[domain] = {(item['pdb_id'], item['matched_occurrence_id']): item for item in records}
        panels.extend(json.loads((source / 'completion.json').read_text(encoding='utf-8'))['panels'])
    # Emap2lig的两个Find-only面板从原交集与候选清单派生, 原24个面板保持逐项不变.
    source = root / 'sources/Emap2lig/find_metadata'
    inventory = json.loads((source / 'inventory.json').read_text(encoding='utf-8'))
    full_counts = {item['pdb_id']: item['occurrence_count'] for item in inventory['rows']}
    full_successes = {pdb: {} for pdb in full_counts}  # 每个PDB内真实实例到首次检出序号的映射; 未检出的PDB仍保留.
    full_candidates = {}
    for pdb in full_counts:
        with np.load(source / 'per_pdb' / f'{pdb}.npz', allow_pickle=False) as arrays:
            blob_ids = arrays['source_blob_index']  # (N_blob,), N_blob是当前PDB的候选blob数; 原编号用于概率并列时排序.
            scores, selected = arrays['candidate_score'], arrays['candidate_selected']  # 均为(N_blob,); 原概率均值及bool选择标志, True表示selected.
            occurrence_ids = arrays['occurrence_id']  # (N_ligand,), N_ligand是当前PDB的真实实例数; 编号与交集矩阵第二轴对齐.
            intersections = arrays['intersections']  # (N_blob,N_ligand), 元素为共享体素数; 一次解压后逐候选读取, 不反复解压NPZ.
            blob_sizes, ligand_sizes = arrays['pred_sizes'], arrays['gt_sizes']  # (N_blob,)、(N_ligand,), 两类完整区域的体素数.
        # (N_blob,), 按selected优先、原概率均值降序和blob编号升序排列, 与原端到端候选顺序一致.
        order = sorted(range(len(blob_ids)), key=lambda i: (not selected[i], -scores[i], blob_ids[i]))
        full_candidates[pdb] = len(order)
        for rank, index in enumerate(order, 1):
            # 直接调用原对应函数, 保留双向覆盖>=0.3、最大几何均值和原并列处理规则.
            occurrence, _, _, _ = _target_from_intersections(occurrence_ids, intersections[index], int(blob_sizes[index]), ligand_sizes)
            if occurrence is not None:
                full_successes[pdb].setdefault(occurrence, rank)
    full = make_panel('find_full_Emap2lig', 'find_full', 'Emap2lig', full_counts, full_successes, full_candidates, full_candidates, None, None)

    identities = [json.loads(line) for line in (source / 'identities.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    small_ids = {}
    for item in identities:
        small_ids.setdefault(item['pdb_id'], set()).update(item['stage3_occurrence_ids'])
    small_counts = {pdb: len(ids) for pdb, ids in small_ids.items() if ids}
    candidates = [json.loads(line) for line in (source / 'emap2lig_candidates.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    grouped = {pdb: [] for pdb in small_counts}
    for item in candidates:
        grouped[item['pdb_id']].append(item)
    small_successes = {pdb: {} for pdb in small_counts}
    small_candidates, examined_counts = {}, {}
    for pdb, values in grouped.items():
        ordered = sorted(values, key=lambda item: (not item['candidate_selected'], -item['source_probability_mean'], item['source_blob_index']))
        small_candidates[pdb] = len(ordered)
        examined = 0
        for item in ordered:
            if item['target_scope'] == 'non_stage3_foreground':
                continue  # 小分子视图沿用原范围, 仅排除对应范围外真实配体的候选; 背景继续占用候选序号.
            examined += 1
            if item['target_scope'] == 'stage3_foreground':
                small_successes[pdb].setdefault(int(item['matched_occurrence_id']), examined)
        examined_counts[pdb] = examined
    small = make_panel('find_small_Emap2lig', 'find_small', 'Emap2lig', small_counts, small_successes, small_candidates, examined_counts, None, None)
    panels.extend([full, small])
    panels.extend(json.loads((PROJECT / '画图/formal/Stage1_find_completion_20261017/panels.json').read_text(encoding='utf-8'))['panels'])
    pairs, table = {}, []
    for domain in ('GT', 'CA2'):
        common = sorted(direct[domain].keys() & direct['Emap2lig'].keys())  # 两套Find均命中的实例, 保留失败分母.
        rows = []
        for key in common:
            tuned, emap = direct[domain][key], direct['Emap2lig'][key]
            record = {'domain': domain, 'pdb_id': key[0], 'occurrence_id': key[1], 'tuned_blob': tuned['source_blob_index'], 'emap_blob': emap['source_blob_index'], 'tuned_top1': tuned['pose_min_rmsd_A']['1'], 'tuned_best': tuned['pose_min_rmsd_A']['50'], 'emap_top1': emap['pose_min_rmsd_A']['1'], 'emap_best': emap['pose_min_rmsd_A']['50']}
            rows.append(record)
            table.append(record)
        # 同一分布比较使用两边均有Top-1与best距离的实例, 不用失败替代距离.
        numeric = [item for item in rows if all(item[field] is not None for field in ('tuned_top1', 'tuned_best', 'emap_top1', 'emap_best'))]
        stats = {}
        for model in ('tuned', 'emap'):
            for pose, limit in (('top1', '1'), ('best', '50')):
                values = np.asarray([item[f'{model}_{pose}'] for item in numeric])  # (N_pair,), 世界坐标重原子RMSD, Å; N_pair为四项距离均有效的配对实例数.
                successes = {str(threshold): sum(direct[domain if model == 'tuned' else 'Emap2lig'][key]['success'][str(threshold)][limit] for key in common) for threshold in (2.0, 3.0)}
                stats[f'{model}_{pose}'] = {'n_numeric': len(values), 'median_A': float(np.median(values)), 'mean_A': float(np.mean(values)), 'quantiles_A': np.quantile(values, [0.05, 0.25, 0.5, 0.75, 0.95]).tolist(), 'success_count': successes, 'success_denominator': len(common)}
        paired = {pose: {'tuned_lower_count': sum(item[f'tuned_{pose}'] < item[f'emap_{pose}'] for item in numeric), 'median_difference_A': float(np.median([item[f'tuned_{pose}'] - item[f'emap_{pose}'] for item in numeric]))} for pose in ('top1', 'best')}
        pairs[domain] = {'common_count': len(common), 'numeric_count': len(numeric), 'all_rows': rows, 'numeric_rows': numeric, 'statistics': stats, 'paired_differences': paired}
    # CSV保留所有共同命中实例; JSON另列有数值的配对子集, 不以失败替代距离.
    with (root / 'paired_pose.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    data = {'panels': panels, 'pairs': pairs}
    (root / 'data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {'pairs': {key: {field: value for field, value in pair.items() if field not in ('all_rows', 'numeric_rows')} for key, pair in pairs.items()}, 'budgets': {panel['id']: {budget: {'mean': float(np.mean([item['completion'] for item in records])), 'median': float(np.median([item['completion'] for item in records]))} for budget, records in panel['distributions'].items()} for panel in panels}}
    (root / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'pairs': summary['pairs'], 'panel_count': len(panels)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
