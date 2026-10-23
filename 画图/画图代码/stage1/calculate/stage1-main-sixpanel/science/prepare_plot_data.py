"""将来源指标变成不可混淆的绘图数据: 均值、CI、分位数和小提琴密度.

本轮脚本只做统计与数据导出, 不导入 Matplotlib/PPT 库. 输入 --source 为
compute_small_pr.py 的 stdout JSON; 输出目录含 plot_data.json、逐 PDB CSV、
bar_statistics.csv 和科学核查. 绘图端只消费这些已计算字段.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy.stats import gaussian_kde

MODELS = ['GT', 'Cryo', 'Emap']
METRICS = ['dice', 'oto03', 'oto06', 'precision', 'recall']
BOOTSTRAP_N = 10000  # 改变区间计算精度的入口, 不能在绘图脚本另算一套.
SEED = 20260922
KDE_BANDWIDTH = .045

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    source = json.loads(raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-8-sig'))
    args.output.mkdir(parents=True, exist_ok=True)
    result = {'bootstrap_replicates': BOOTSTRAP_N, 'bootstrap_seed': SEED,
              'kde_bandwidth': KDE_BANDWIDTH, 'cohorts': {}}
    long_rows, bar_rows = [], []
    checks = {'sample_counts': {}, 'maximum_aggregate_difference': 0.0, 'small_pr_counts': {}}
    for cohort in ['full', 'small']:
        ids = [r['pdb_id'] for r in source['models']['GT'][cohort + '_rows']]
        n = len(ids)
        assert n == (179 if cohort == 'full' else 94)
        block = {'ids': ids, 'n': n, 'resolution': [float(source['resolution'][p]) for p in ids], 'models': {}}
        mapping = dict(zip(METRICS, ['semantic_macro_f1', 'one_to_one_macro_prauc_0p3', 'one_to_one_macro_prauc_0p6',
                    'one_to_one_macro_precision_0p3', 'one_to_one_macro_recall_0p3'] if cohort == 'full' else
                    ['semantic_dice', 'one_to_one_prauc_0p3', 'one_to_one_prauc_0p6', 'one_to_one_precision_0p3', 'one_to_one_recall_0p3']))
        for model in MODELS:
            data = source['models'][model]
            rows = data[cohort + '_rows']
            assert [r['pdb_id'] for r in rows] == ids
            values = {key: [float(r[field]) for r in rows] for key, field in mapping.items()}
            assert np.isfinite(list(values.values())).all()
            assert np.min(list(values.values())) >= 0 and np.max(list(values.values())) <= 1
            # 均值逐项对照原汇总. 小分子新补 P/R 没有旧汇总, 由匹配计数校验.
            for metric in METRICS[:3]:
                summary_field = mapping[metric] if cohort == 'full' else {'dice':'semantic_macro_dice','oto03':'one_to_one_macro_prauc_0p3','oto06':'one_to_one_macro_prauc_0p6'}[metric]
                diff = abs(np.mean(values[metric]) - data[cohort + '_metrics'][summary_field])
                checks['maximum_aggregate_difference'] = max(checks['maximum_aggregate_difference'], float(diff))
                assert diff < 1e-12
            distribution = {}
            for metric in ['precision','recall']:
                v = np.asarray(values[metric])
                grid = np.linspace(0,1,161)
                # 在 0/1 边界反射, 不删去大量恰好为 0 或 1 的 PDB.
                density = gaussian_kde(np.r_[v, -v, 2-v], bw_method=KDE_BANDWIDTH)(grid)
                distribution[metric] = {'grid': grid.tolist(), 'density': (density/density.max()).tolist(),
                                         'quartiles': np.quantile(v,[.25,.5,.75]).tolist()}
            block['models'][model] = {'values': values, 'distribution': distribution, 'bars': {}}
            for i,pdb in enumerate(ids):
                long_rows.append([cohort,model,pdb,block['resolution'][i]]+[values[m][i] for m in METRICS])
            if cohort == 'small':
                checks['small_pr_counts'][model] = {'selected': sum(r['selected_count'] for r in rows),
                    'matched': sum(r['matched_count_0p3'] for r in rows), 'small_gt': sum(r['small_gt_count'] for r in rows)}
                for r in rows:
                    assert r['matched_count_0p3'] <= min(r['selected_count'],r['small_gt_count'])
        # (N_PDB,9), 所有方法与三项指标共用重采样索引, 保留 PDB 配对关系.
        keys = [(m,k) for m in MODELS for k in METRICS[:3]]
        matrix = np.column_stack([block['models'][m]['values'][k] for m,k in keys])
        rng = np.random.default_rng(SEED)
        boot = np.concatenate([matrix[rng.integers(0,n,size=(250,n))].mean(axis=1) for _ in range(BOOTSTRAP_N//250)])
        bounds = np.quantile(boot,[.025,.975],axis=0)
        for i,(model,metric) in enumerate(keys):
            stats = {'mean': float(matrix[:,i].mean()), 'lower': float(bounds[0,i]), 'upper': float(bounds[1,i])}
            block['models'][model]['bars'][metric] = stats
            bar_rows.append([cohort,model,metric,n,stats['mean'],stats['lower'],stats['upper']])
        delta = np.array(block['models']['Cryo']['values']['oto03']) - block['models']['Emap']['values']['oto03']
        block['paired_counts'] = {'find_higher': int((delta>1e-12).sum()), 'equal': int((abs(delta)<=1e-12).sum()), 'emap_higher': int((delta< -1e-12).sum())}
        result['cohorts'][cohort] = block
        checks['sample_counts'][cohort] = n
    for name, header, rows in [('source_data.csv',['cohort','method','pdb_id','resolution_angstrom']+METRICS,long_rows),
                               ('bar_statistics.csv',['cohort','method','metric','n','mean','ci95_lower','ci95_upper'],bar_rows)]:
        with (args.output/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(header);writer.writerows(rows)
    (args.output/'plot_data.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
    (args.output/'science_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))
