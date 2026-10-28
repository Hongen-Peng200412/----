"""保存完整179-PDB病例初筛, 不读取截图或运行模型.

--output 写JSON对象: protected_pdbs 是排除名单, rows 保存原实例数、双方检出计数、全PDB语义Dice、小分子命中身份和 eligible 布尔值. CA2计数由冻结P/R恢复并核对整数一致性; TP为0时不能据P/R恢复总预测数, 因而预测/FP计数保留null. 初筛不代替局部同实例和受体FP核查.
eligible 需同时满足: 非保护PDB、Emap命中至少一个 small_molecule 实例、CA2预测数可恢复、Emap FP多于CA2、CA2全PDB语义Dice高于Emap. eligible_count 是 rows 中 eligible=True 的记录数.
"""
from pathlib import Path
import argparse
import json
import numpy as np


# ================================================================================================
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
# project 是论文仓库; full 是冻结逐PDB统计; archive 只指向显式level评价原件.
project=Path(__file__).resolve().parents[5]
full=json.loads((project/'画图/画图代码/stage1/output/stage1-results-revision/explicit_emdb_level/data/plot_data.json').read_text(encoding='utf-8'))['cohorts']['full']
archive=project/'补充数据/Emap2lig_双条件/explicit_emdb_level/find/held_out_test_0/evaluation/per_pdb'
# occurrences 保留原实例类别; 全部小分子不缩成77-PDB的Build合格子集.
occurrences=project/'补充数据/Find-Match-Build_20261018/provenance/stage1_all_small/occurrences'
protected={'9bjj','11jb','30ga'}
rows=[]
for i,pdb in enumerate(full['ids']):
    source=occurrences/(pdb+'.jsonl')
    small={int(o['candidate_id']) for o in map(json.loads,source.read_text(encoding='utf-8').splitlines()) if o['type_tag']=='small_molecule'} if source.exists() else set()
    with np.load(archive/(pdb+'.npz')) as ev:
        threshold=int(np.flatnonzero(np.isclose(ev['coverage_thresholds'],0.3))[0])
        start,stop=ev['one_to_one_match_offsets'][threshold:threshold+2]
        tp=int(stop-start);predicted=int(ev['candidate_selected'].sum())
        # (N_GT,), 真实实例身份; 配对GT列号经此轴映射为原 occurrence_id.
        gt=ev['occurrence_id']
        hits=[int(gt[g]) for g in ev['one_to_one_match_gt_index'][start:stop] if int(gt[g]) in small]
        ca2=full['models']['Cryo']['values'];emap=full['models']['Emap']['values']
        ca2_tp=round(ca2['recall'][i]*len(gt))
        ca2_pred=round(ca2_tp/ca2['precision'][i]) if ca2['precision'][i]>0 else None
        if ca2_pred is not None:
            np.testing.assert_allclose(ca2_tp,ca2['recall'][i]*len(gt),atol=1e-7,rtol=0)
            np.testing.assert_allclose(ca2_pred,ca2_tp/ca2['precision'][i],atol=1e-7,rtol=0)
        ca2_fp=ca2_pred-ca2_tp if ca2_pred is not None else None
        eligible=pdb not in protected and bool(hits) and ca2_pred is not None and predicted-tp>ca2_fp and ca2['dice'][i]>emap['dice'][i]
        rows.append({'pdb':pdb,'gt_instances':len(gt),'ca2_predicted':ca2_pred,'ca2_tp':ca2_tp,'ca2_fp':ca2_fp,'emap_predicted':predicted,'emap_tp':tp,'emap_fp':predicted-tp,'semantic_dice_ca2':ca2['dice'][i],'semantic_dice_emap':emap['dice'][i],'emap_hit_small_occurrences':hits,'eligible':eligible})
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps({'condition':'explicit_emdb_level','protected_pdbs':sorted(protected),'rows':rows,'eligible_count':sum(r['eligible'] for r in rows)},ensure_ascii=False,indent=2),encoding='utf-8')
print(f"完整测试集 {len(rows)} PDB, 非保护初筛候选 {sum(r['eligible'] for r in rows)} 个.")
