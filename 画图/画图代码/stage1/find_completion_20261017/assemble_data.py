"""从既有Find元数据汇总全部小分子的实例检出完成度, 供正文Fig.4下排使用.

main沿用Stage1冻结的94个PDB及实例类别, 连接GT、CA2和Emap2lig的完整候选.
只复用既有唯一对应、候选顺序及完成度函数, 不调用Match或Build, 不修改端到端结果.
"""

import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT.parent / 'AdaLigand'))
sys.path.insert(0, str(PROJECT.parent / 'Matcher'))
from ligandseek_pipeline.completion import make_panel
from test_smallmolecule.build_manifest import _target_from_intersections


# ================================================================================================
def main():
    """按原候选次序统计Stage1全部小分子的首次检出, 保留完整目标分母.

    输入文件:
        - 画图/formal/Stage1_main_sixpanel_20260929/data/server_metrics_and_pr.json: dict, small_provenance.cohort_pdb_ids是原94个PDB顺序; models保存原Stage1逐PDB统计.
        - 画图/formal/Stage1_find_completion_20261017/sources/occurrences/<pdb>.jsonl: 每项一个原实例, candidate_id是PDB内实例编号, type_tag为原类别, 如small_molecule; 不按残基数、原子完整性或SMILES可用性筛选.
        - 画图/formal/E2E_accounting_20261004/sources/full_matcher.json: dict, predictions[real_receptor/cryoatom2_receptor][pdb]保存完整Find候选; 只读原selected、概率、blob编号及唯一真实对应, 不读身份预测.
        - 画图/formal/fmb_20261015/sources/Emap2lig/find_metadata/per_pdb/<pdb>.npz: 原生Find交集、区域大小及候选信息, 轴与字段含义见下方读取位置.
    输出文件:
        - 画图/formal/Stage1_find_completion_20261017/panels.json: dict, panels含GT、CA2、Emap2lig三份原make_panel字典; scope为论文内部标识find_stage1_small, 不增加端到端视图.
        - summary.json: list[dict], 每个方法的完整分母、全候选统计及0/50/100/200/300%候选数量下的PDB等权均值、中位数, 供图注与Results取值.
    """
    formal = PROJECT / '画图/formal'
    output = formal / 'Stage1_find_completion_20261017'
    stage1 = json.loads((formal / 'Stage1_main_sixpanel_20260929/data/server_metrics_and_pr.json').read_text(encoding='utf-8'))
    # list[str], 与原Stage1小分子统计共用的完整PDB轴; 未检出和零候选PDB仍保留.
    pdb_ids = stage1['small_provenance']['cohort_pdb_ids']
    members = {}
    for pdb in pdb_ids:
        records = [json.loads(line) for line in (output / 'sources/occurrences' / f'{pdb}.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        members[pdb] = {int(item['candidate_id']) for item in records if item['type_tag'] == 'small_molecule'}
    # dict[str, int], 每个PDB全部小分子的真实实例数; 总计94个PDB、821个实例.
    denominators = {pdb: len(members[pdb]) for pdb in pdb_ids}
    find = json.loads((formal / 'E2E_accounting_20261004/sources/full_matcher.json').read_text(encoding='utf-8'))
    panels, summary = [], []
    for domain, condition in (('GT', 'real_receptor'), ('CA2', 'cryoatom2_receptor'), ('Emap2lig', None)):
        successes = {pdb: {} for pdb in pdb_ids}  # PDB内实例编号 -> 首次检出的候选序号; 一个实例只增加一次完成度.
        candidate_counts, examined_counts = {}, {}
        for pdb in pdb_ids:
            if domain == 'Emap2lig':
                with np.load(formal / 'fmb_20261015/sources/Emap2lig/find_metadata/per_pdb' / f'{pdb}.npz', allow_pickle=False) as arrays:
                    blob_ids = arrays['source_blob_index']  # (N_blob,), 当前PDB的N_blob个原生候选编号, 用于打破概率同分.
                    scores, selected = arrays['candidate_score'], arrays['candidate_selected']  # 均为(N_blob,), 原概率均值及bool选择标记; True为selected.
                    occurrence_ids = arrays['occurrence_id']  # (N_ligand,), 当前PDB全类别N_ligand个真实实例的原编号, 不先缩成小分子轴.
                    intersections = arrays['intersections']  # (N_blob, N_ligand), 各候选与各真实实例共享的体素数.
                    blob_sizes, ligand_sizes = arrays['pred_sizes'], arrays['gt_sizes']  # (N_blob,)、(N_ligand,), 两类完整区域的体素数.
                values = []
                for index, blob in enumerate(blob_ids):
                    occurrence, _, _, _ = _target_from_intersections(occurrence_ids, intersections[index], int(blob_sizes[index]), ligand_sizes)
                    values.append({'source_blob_index': int(blob), 'candidate_selected': bool(selected[index]), 'source_probability_mean': float(scores[index]), 'foreground_target': occurrence is not None, 'matched_occurrence_id': occurrence})
            else:
                values = find['predictions'][condition].get(pdb, [])  # 零候选PDB在旧预测字典中可缺省, 此时仍使用空列表及原真实分母.
            # selected在前, 各段按原概率均值降序, 同分按原blob编号升序; 不截断unselected或排名靠后的候选.
            ordered = sorted(values, key=lambda item: (not item['candidate_selected'], -item['source_probability_mean'], item['source_blob_index']))
            candidate_counts[pdb] = len(ordered)
            examined = 0
            for item in ordered:
                foreground = item['foreground_target']  # bool, 全类别唯一对应成立; 不读取Match身份正确性.
                occurrence = int(item['matched_occurrence_id']) if foreground else None
                if foreground and occurrence not in members[pdb]:
                    continue  # 只忽略已对应非小分子的候选; 不重新寻找另一个小分子对应.
                examined += 1  # 背景和小分子对应候选都占一个位置; 重复命中同样保留其位置.
                if foreground:
                    successes[pdb].setdefault(occurrence, examined)
            examined_counts[pdb] = examined
        panel = make_panel(f'find_stage1_small_{domain}', 'find_stage1_small', domain, denominators, successes, candidate_counts, examined_counts, None, None)
        panels.append(panel)
        summary.append({'domain': domain, 'pdb_count': panel['pdb_count'], 'occurrence_count': panel['occurrence_count'], 'all_candidates_final': panel['all_candidates_final'], 'relative_candidate_count': {key: {'mean': float(np.mean([item['completion'] for item in values])), 'median': float(np.median([item['completion'] for item in values]))} for key, values in panel['distributions'].items()}})
    (output / 'panels.json').write_text(json.dumps({'panels': panels}, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
