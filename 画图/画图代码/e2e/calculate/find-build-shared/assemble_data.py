"""读取统一管线的最终结果, 为三组论文图固定数据.

入口main读取画图/画图代码/e2e/output/find-build-shared/sources内三个域的原始结果,
默认写出原结果根的regenerated; --condition explicit_emdb_level只替换Emap2lig结果并写入独立的explicit_emdb_level子目录. 不执行模型、姿态排名或体素交集重算; Emap2lig的对应决策直接复用原函数.
"""

import csv
import argparse
import json
import sys
from pathlib import Path

import numpy as np

# 只复用既有对应决策和精确预算汇总, 不导入Find、Match或Build模型.
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
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
        - 画图/画图代码/stage1/output/find-only-instance-completion/panels.json: Stage1全部小分子的94/821统计; 只追加论文面板, 不覆盖原Stage3视图.
    产物:
        - data.json: dict, panels为三域面板列表; pairs[GT/CA2]含共同实例数、配对数值实例及两模型统计.
        - paired_pose.csv: 共同命中的全部实例, 含两种模型的Top-1和best距离, 缺失为空, 不填替代数值.
        - summary.json: 各比较的统计及完整面板的原预算分布摘要, 用于图注、结果和表格.
        - explicit_emdb_level/topk_data.json: 仅替换全配体179 PDB和合格小分子77 PDB中Emap2lig的十档整数检出数; 其余LigandSeek计数逐字段保留.
        - explicit_emdb_level/selected_blob_events.json: 每个实际Build请求的原blob编号、完整Find排名及范围内计费号, 包含筛选失败, 不把该姿态绑定给首次命中blob.
        - explicit_emdb_level/number_changes.json: 新旧配对分布、各固定预算均值及新top-k计数, 只供图文同步核对.
    """
    # root: 原无 level 的共享冻结结果根; 新条件只读这些 LigandSeek 原结果, 不覆盖它们.
    root = PROJECT / '画图/画图代码/e2e/output/find-build-shared'
    parser = argparse.ArgumentParser(description='按明确的 Emap2lig 条件组装论文比较数据')
    parser.add_argument('--condition', choices=('no_level', 'explicit_emdb_level'), default='no_level')
    condition = parser.parse_args().condition
    if condition == 'explicit_emdb_level':
        # source_root: 已接入论文仓库的新实验科学元数据, 包含原推荐 level、候选交集与逐姿态评价.
        source_root = PROJECT / '补充数据/Emap2lig_双条件/explicit_emdb_level'
        # publish: 新条件的长期派生输入, 与原 data.json 和原 sources 完全分开.
        publish = root / 'explicit_emdb_level'
        publish.mkdir(parents=True, exist_ok=True)
        original_data = json.loads((root / 'data.json').read_text(encoding='utf-8'))
        # panels: 原 GT/CA2 面板逐字段复用, 只替换 Emap2lig 条件; 原小分子补充面板由 Stage1 独立更新.
        panels = [panel for panel in original_data['panels'] if panel['domain'] != 'Emap2lig']
        inventory = json.loads((PROJECT / '补充数据/Find-Match-Build_20261018/provenance/find/inventory.json').read_text(encoding='utf-8'))
        full_counts = {row['pdb_id']: row['occurrence_count'] for row in inventory['rows']}
        requests = [json.loads(line) for line in (source_root / 'build/find_hit_subset.jsonl').read_text(encoding='utf-8').splitlines()]
        request_by_key = {(row['pdb_id'], row['occurrence_id']): row for row in requests}
        identities = [json.loads(line) for line in (source_root / 'inputs/test.jsonl').read_text(encoding='utf-8').splitlines()]
        # small_ids: dict[PDB, set[occurrence]], 固定 77 PDB 的完整 446 实例, 不是 Stage1 全部小分子范围.
        small_ids = {}
        for row in identities:
            small_ids.setdefault(row['pdb_id'], set()).add(row['candidate_id'])
        small_counts = {pdb: len(ids) for pdb, ids in small_ids.items()}
        build_rows = [json.loads(line) for line in (source_root / 'build/build_occurrences.jsonl').read_text(encoding='utf-8').splitlines()]
        # direct: 三域按真实实例连接的原模型结果; Emap2lig 姿态只属于本轮实际选中的 blob.
        direct = {}
        for domain in ('GT', 'CA2'):
            records = [json.loads(line) for line in (root / 'sources' / domain / 'docking_results.jsonl').read_text(encoding='utf-8').splitlines()]
            direct[domain] = {(row['pdb_id'], row['matched_occurrence_id']): row for row in records}
        direct['Emap2lig'] = {}
        for row in build_rows:
            key = (row['pdb_id'], row['occurrence_id'])
            rmsd = {'1': row['top1_rmsd_A'], '5': row['top5_rmsd_A'], '50': row['oracle_rmsd_A']}
            direct['Emap2lig'][key] = {'pdb_id': key[0], 'matched_occurrence_id': key[1], 'source_blob_index': request_by_key[key]['blob_id'], 'status': row['status'], 'pose_min_rmsd_A': rmsd, 'success': {str(threshold): {limit: value is not None and value < threshold for limit, value in rmsd.items()} for threshold in (2.0, 3.0)}}

        full_successes = {pdb: {} for pdb in full_counts}
        small_successes = {pdb: {} for pdb in small_counts}
        # pose_successes: 四种原排序姿态/阈值条件的首次成功计费号; 每个目标实例至多一次.
        pose_successes = {(pose, threshold): {pdb: {} for pdb in small_counts} for pose in (1, 50) for threshold in (2.0, 3.0)}
        full_candidates, small_candidates, charged_counts = {}, {}, {}
        selected_blob_events = []
        for pdb in full_counts:
            with np.load(source_root / 'find/held_out_test_0/evaluation/per_pdb' / f'{pdb}.npz', allow_pickle=False) as arrays:
                # 预测轴 P 按分数排序; 真值轴 G 保留全部类别, 不先删去范围外实例.
                # blob_ids/scores/selected 均为 (P,), 分别是原生编号、无量纲分数和参与选取的 bool 标志.
                blob_ids, scores, selected = arrays['source_blob_index'], arrays['candidate_score'], arrays['candidate_selected']
                # occurrence_ids 为 (G,) 原实例编号, intersections 为 (P,G) 的交集体素数.
                occurrence_ids, intersections = arrays['occurrence_id'], arrays['intersections']
                # blob_sizes 为 (P,) 候选体素数, ligand_sizes 为 (G,) 真值实例体素数.
                blob_sizes, ligand_sizes = arrays['pred_sizes'], arrays['gt_sizes']
            order = sorted(range(len(blob_ids)), key=lambda i: (not selected[i], -scores[i], blob_ids[i]))
            full_candidates[pdb] = len(order)
            if pdb in small_ids:
                small_candidates[pdb] = len(order)
            charged = 0
            for rank, index in enumerate(order, 1):
                occurrence, _, _, _ = _target_from_intersections(occurrence_ids, intersections[index], int(blob_sizes[index]), ligand_sizes)
                if occurrence is not None:
                    full_successes[pdb].setdefault(occurrence, rank)
                if pdb not in small_ids:
                    continue
                if occurrence is not None and occurrence not in small_ids[pdb]:
                    continue  # 正确身份假设下, 真实范围外前景免费; 背景和范围内重复候选仍计费.
                charged += 1
                if occurrence is None:
                    continue
                small_successes[pdb].setdefault(occurrence, charged)
                key = (pdb, occurrence)
                request = request_by_key.get(key)
                if request is None or int(blob_ids[index]) != request['blob_id']:
                    continue  # Find 首次命中不是实际 Build 输入时, 不把该实例姿态绑定给更早候选.
                selected_blob_events.append({'pdb_id': pdb, 'occurrence_id': occurrence, 'source_blob_index': int(blob_ids[index]), 'find_rank': rank, 'charged_attempt': charged, 'status': direct['Emap2lig'][key]['status']})
                for pose, threshold in pose_successes:
                    if direct['Emap2lig'][key]['success'][str(threshold)][str(pose)]:
                        pose_successes[(pose, threshold)][pdb][occurrence] = charged
            if pdb in small_ids:
                charged_counts[pdb] = charged
        panels.append(make_panel('find_full_Emap2lig', 'find_full', 'Emap2lig', full_counts, full_successes, full_candidates, full_candidates, None, None))
        panels.append(make_panel('find_small_Emap2lig', 'find_small', 'Emap2lig', small_counts, small_successes, small_candidates, charged_counts, None, None))
        for (pose, threshold), successes in pose_successes.items():
            panels.append(make_panel(f'assume_Emap2lig_pose{pose}_rmsd{threshold}', 'assume', 'Emap2lig', small_counts, successes, small_candidates, charged_counts, threshold, pose))
        # stage1_panels: Stage1 入口已冻结的 94/821 结果; 显式条件必须具备它, 不混入旧 Emap 面板.
        stage1_panels = PROJECT / '画图/画图代码/stage1/output/stage1-results-revision/explicit_emdb_level/data/completion_panels.json'
        panels = [panel for panel in panels if panel['scope'] != 'find_stage1_small']
        panels.extend(panel for panel in json.loads(stage1_panels.read_text(encoding='utf-8'))['panels'] if panel['scope'] == 'find_stage1_small')
        pairs, table = {}, []
        for domain in ('GT', 'CA2'):
            common = sorted(direct[domain].keys() & direct['Emap2lig'].keys())
            rows = []
            for key in common:
                tuned, emap = direct[domain][key], direct['Emap2lig'][key]
                rows.append({'domain': domain, 'pdb_id': key[0], 'occurrence_id': key[1], 'tuned_blob': tuned['source_blob_index'], 'emap_blob': emap['source_blob_index'], 'tuned_top1': tuned['pose_min_rmsd_A']['1'], 'tuned_best': tuned['pose_min_rmsd_A']['50'], 'emap_top1': emap['pose_min_rmsd_A']['1'], 'emap_best': emap['pose_min_rmsd_A']['50']})
            table.extend(rows)
            numeric = [row for row in rows if all(row[field] is not None for field in ('tuned_top1', 'tuned_best', 'emap_top1', 'emap_best'))]
            stats = {}
            for model in ('tuned', 'emap'):
                for pose, limit in (('top1', '1'), ('best', '50')):
                    values = np.asarray([row[f'{model}_{pose}'] for row in numeric])
                    successes = {str(threshold): sum(direct[domain if model == 'tuned' else 'Emap2lig'][key]['success'][str(threshold)][limit] for key in common) for threshold in (2.0, 3.0)}
                    stats[f'{model}_{pose}'] = {'n_numeric': len(values), 'median_A': float(np.median(values)), 'mean_A': float(np.mean(values)), 'quantiles_A': np.quantile(values, [0.05, 0.25, 0.5, 0.75, 0.95]).tolist(), 'success_count': successes, 'success_denominator': len(common)}
            paired = {pose: {'tuned_lower_count': sum(row[f'tuned_{pose}'] < row[f'emap_{pose}'] for row in numeric), 'median_difference_A': float(np.median([row[f'tuned_{pose}'] - row[f'emap_{pose}'] for row in numeric]))} for pose in ('top1', 'best')}
            pairs[domain] = {'common_count': len(common), 'numeric_count': len(numeric), 'all_rows': rows, 'numeric_rows': numeric, 'statistics': stats, 'paired_differences': paired}
        with (publish / 'paired_pose.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(table[0]))
            writer.writeheader()
            writer.writerows(table)
        data = {'condition': condition, 'panels': panels, 'pairs': pairs}
        (publish / 'data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        summary = {'condition': condition, 'pairs': {key: {field: value for field, value in pair.items() if field not in ('all_rows', 'numeric_rows')} for key, pair in pairs.items()}, 'budgets': {panel['id']: {budget: {'mean': float(np.mean([row['completion'] for row in records])), 'median': float(np.median([row['completion'] for row in records]))} for budget, records in panel['distributions'].items()} for panel in panels}}
        (publish / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (publish / 'selected_blob_events.json').write_text(json.dumps(selected_blob_events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # topk: 原 SI 计数仅替换两条 Emap Find 曲线, 其余 LigandSeek 计数保持原样.
        topk = json.loads((PROJECT / '画图/画图代码/e2e/output/e2e-top-k/data.json').read_text(encoding='utf-8'))
        topk['full']['emap2lig'] = [sum(any(step <= budget for step in full_successes[pdb].values()) for pdb in full_counts) for budget in range(1, 11)]
        topk['small_find']['emap2lig'] = [sum(any(step <= budget for step in small_successes[pdb].values()) for pdb in small_counts) for budget in range(1, 11)]
        topk['provenance']['emap2lig_condition'] = condition
        topk['provenance']['emap2lig_metadata'] = '补充数据/Emap2lig_双条件/explicit_emdb_level/find/held_out_test_0/evaluation/per_pdb'
        (publish / 'topk_data.json').write_text(json.dumps(topk, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        original_panels = {panel['id']: panel for panel in original_data['panels']}
        changes = {'pairs': {'old': original_data['pairs'], 'new': pairs}, 'budgets': {panel['id']: {budget: {'old': float(np.mean([row['completion'] for row in original_panels[panel['id']]['distributions'][budget]])), 'new': values['mean']} for budget, values in summary['budgets'][panel['id']].items()} for panel in panels if panel['id'] in original_panels}, 'topk': {'full_Emap2lig': topk['full']['emap2lig'], 'small_Emap2lig': topk['small_find']['emap2lig']}}
        (publish / 'number_changes.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'condition': condition, 'pairs': summary['pairs'], 'topk_full': topk['full']['emap2lig'], 'topk_small': topk['small_find']['emap2lig']}, ensure_ascii=False))
        return
    publish = root / 'regenerated'
    publish.mkdir(parents=True, exist_ok=True)
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
    panels.extend(json.loads((PROJECT / '画图/画图代码/stage1/output/find-only-instance-completion/panels.json').read_text(encoding='utf-8'))['panels'])
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
    with (publish / 'paired_pose.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    data = {'panels': panels, 'pairs': pairs}
    (publish / 'data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {'pairs': {key: {field: value for field, value in pair.items() if field not in ('all_rows', 'numeric_rows')} for key, pair in pairs.items()}, 'budgets': {panel['id']: {budget: {'mean': float(np.mean([item['completion'] for item in records])), 'median': float(np.median([item['completion'] for item in records]))} for budget, records in panel['distributions'].items()} for panel in panels}}
    (publish / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'pairs': summary['pairs'], 'panel_count': len(panels)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
