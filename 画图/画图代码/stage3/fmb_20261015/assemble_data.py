"""读取统一管线的最终结果, 为三组论文图固定数据.

入口main读取画图/formal/fmb_20261015/sources内三个域的原始结果,
写出同目录data.json、paired_pose.csv和summary.json. 不执行模型、姿态排名或覆盖对应计算.
"""

import csv
import json
from pathlib import Path

import numpy as np


# ================================================================================================
def main():
    """连接原blob对应和姿态结果, 保留完整分母及有数值的配对分布.

    输入:
        - sources/{GT,CA2,Emap2lig}/docking_results.jsonl: 每blob一条, matched_occurrence_id连接真实实例; pose_min_rmsd_A的1/50为原模型Top-1和best-of-50距离, 单位Å, 失败为None.
        - completion.json: 现成panels, 逐PDB分母、精确预算曲线和分布不再重算.
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
