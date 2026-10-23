"""只读服务器产物, 补算三个方法的小分子 one-to-one P/R, 向 stdout 输出 JSON.

这是本轮六面板的一次补算脚本, 可通过 SSH 标准输入执行, 不在服务器写文件.
先读 evaluate_selected() 的固定归属与一对一匹配, 再读下方来源装配流程.
输出包含 full/small 两种 cohort 的逐 PDB 指标、原始汇总、来源路径与摘要.
P/R 只使用冻结的最终 selected; PRAUC/Dice 直接读取既有正式结果.
"""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching


def evaluate_selected(intersections, pred_sizes, gt_sizes, occurrence_ids, gt_types, selected):
    """返回忽略数、入选数、最大匹配数及 P/R; 输入轴为预测 blob × 全类别 GT.

    intersections: int (N_pred,N_gt), 交集体素数; sizes 对应两轴体素数.
    occurrence_ids/gt_types: (N_gt,), 原编号与类型. selected: bool (N_pred,),
    冻结最终选择. 非小分子归属先按双向覆盖 >=0.30 确定, 不依赖 selected.
    完全并列取较小 occurrence 编号; 无归属预测保留, 空预测的 P 记为 0.
    """
    pred_cover = np.divide(intersections, pred_sizes[:, None], out=np.zeros(intersections.shape, float), where=pred_sizes[:, None] > 0)
    gt_cover = np.divide(intersections, gt_sizes[None, :], out=np.zeros(intersections.shape, float), where=gt_sizes[None, :] > 0)
    valid = (pred_cover >= .30) & (gt_cover >= .30)
    ignored = np.zeros(len(pred_sizes), dtype=bool)
    for i in range(len(pred_sizes)):
        candidates = np.flatnonzero(valid[i])
        if candidates.size:
            best = max(candidates, key=lambda j: (float(np.sqrt(pred_cover[i,j] * gt_cover[i,j])), -int(occurrence_ids[j])))
            ignored[i] = gt_types[best] != 'small_molecule'
    # (N_selected,N_small), 只保留最终已选且未被忽略的预测, 真实侧只保留小分子.
    small_axis = np.array([t == 'small_molecule' for t in gt_types], dtype=bool)
    kept_selected = np.asarray(selected, bool) & ~ignored
    edges = valid[np.ix_(kept_selected, small_axis)]
    n_pred, n_gt = edges.shape
    matched = int((maximum_bipartite_matching(csr_matrix(edges), perm_type='column') >= 0).sum()) if n_pred and n_gt else 0
    return {'ignored_candidate_count': int(ignored.sum()), 'selected_count': n_pred,
            'matched_count_0p3': matched, 'small_gt_count': n_gt,
            'one_to_one_precision_0p3': matched / n_pred if n_pred else 0.0,
            'one_to_one_recall_0p3': matched / n_gt if n_gt else 0.0}


if __name__ == '__main__':
    base = Path('/storage/penghongen/AdaLigand_stage1_inference')
    small_root = base / 'small_molecule_only/test_0'
    gt_root = Path('/storage/penghongen/AdaLigand/Ori_Data')
    prov = json.loads((small_root / 'provenance.json').read_text())
    models = {'GT': 'find_real_f2_gaussian', 'Cryo': 'find_cryo_f2_gaussian', 'Emap': 'emap_official_li'}
    output = {'small_provenance': prov, 'models': {}, 'sources': []}
    for model, pipeline in models.items():
        rootrel, stem, _, _ = prov['pipelines'][pipeline]
        root = base / rootrel
        full_eval = root / 'evaluation' if model == 'Emap' else root / 'held_out_test_0/evaluation'
        full_stem = 'official_find_li' if model == 'Emap' else stem
        paths = {'full_metrics': full_eval / (full_stem + '.metrics.json'),
                 'full_rows': full_eval / (full_stem + '.jsonl'),
                 'small_metrics': small_root / (pipeline + '.metrics.json'),
                 'small_rows': small_root / (pipeline + '.per_pdb.jsonl')}
        data = {}
        for kind, path in paths.items():
            raw = path.read_bytes()
            data[kind] = [json.loads(line) for line in raw.splitlines() if line.strip()] if kind.endswith('rows') else json.loads(raw)
            output['sources'].append({'model': model, 'kind': kind, 'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()})
        for row in data['small_rows']:
            pdb = row['pdb_id']
            facts = root / 'evaluation/per_pdb' / (pdb + '.npz') if model == 'Emap' else root / 'held_out_test_0' / pdb / 'evaluation' / (stem + '.npz')
            types_path = gt_root / 'parse' / pdb / 'occurrences.jsonl'
            types = {int(r['candidate_id']): r['type_tag'] for r in map(json.loads, types_path.read_text().splitlines())}
            with np.load(facts, allow_pickle=False) as archive:
                ids = archive['occurrence_id']
                computed = evaluate_selected(archive['intersections'], archive['pred_sizes'], archive['gt_sizes'],
                                             ids, [types[int(i)] for i in ids], archive['candidate_selected'])
                assert len(archive['pred_sizes']) == row['candidate_count']
            # 对照既有小分子报告, 确保补算没有改变 cohort 或非小分子忽略规则.
            assert computed['ignored_candidate_count'] == row['ignored_candidate_count']
            assert computed['small_gt_count'] == row['small_gt_count']
            row.update(computed)
            output['sources'].append({'model': model, 'kind': 'pr_facts', 'pdb_id': pdb,
                'path': str(facts), 'sha256': hashlib.sha256(facts.read_bytes()).hexdigest(),
                'types_path': str(types_path), 'types_sha256': hashlib.sha256(types_path.read_bytes()).hexdigest()})
        assert [r['pdb_id'] for r in data['small_rows']] == prov['cohort_pdb_ids']
        output['models'][model] = data
        print(model + ': 94 PDBs checked', file=sys.stderr)
    quality = Path(prov['quality_manifest'])
    ids = {r['pdb_id'] for r in output['models']['GT']['full_rows']}
    output['resolution'] = {r['pdb_id']: r['quality']['map_resolution'] for r in map(json.loads, quality.read_text().splitlines()) if r['pdb_id'] in ids}
    print(json.dumps(output, ensure_ascii=True))
