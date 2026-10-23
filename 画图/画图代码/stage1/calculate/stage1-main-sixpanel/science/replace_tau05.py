"""从已保存的逐 PDB 结果，将六面板第三组柱图的阈值换成 0.5。

输入是原始评估摘要和上一版 plot_data.json；输出到指定新版本的 data/。
其他指标、P/R、小提琴密度及配对图数据逐字段沿用上一版，不访问服务器。
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


MODELS = ('GT', 'Cryo', 'Emap')
BOOTSTRAP_N = 10000
SEED = 20260922


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='冻结的 server_metrics_and_pr.json')
    parser.add_argument('--previous', type=Path, required=True, help='上一版 plot_data.json')
    parser.add_argument('--output', type=Path, required=True, help='新版本的 data 目录')
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding='utf-8-sig'))
    plot = json.loads(args.previous.read_text(encoding='utf-8'))
    checks = {'replaced': 'one-to-one PRAUC@0.6 → @0.5', 'samples': {}, 'max_source_mean_difference': 0.0}
    plot['high_metric'] = 'oto05'
    for cohort in ('full', 'small'):
        block = plot['cohorts'][cohort]
        ids = block['ids']
        assert len(ids) == (179 if cohort == 'full' else 94)
        checks['samples'][cohort] = len(ids)
        source_field = 'one_to_one_macro_prauc_0p5' if cohort == 'full' else 'one_to_one_prauc_0p5'
        for method in MODELS:
            rows = source['models'][method][cohort + '_rows']
            assert [row['pdb_id'] for row in rows] == ids
            values = np.asarray([row[source_field] for row in rows], dtype=float)
            assert np.isfinite(values).all() and ((0 <= values) & (values <= 1)).all()
            reported = source['models'][method][cohort + '_metrics']['one_to_one_macro_prauc_0p5']
            difference = abs(float(values.mean()) - reported)
            checks['max_source_mean_difference'] = max(checks['max_source_mean_difference'], difference)
            assert difference < 1e-12
            # 新旧阈值只在一个指标槽位替换；其余绘图值保持原 JSON 内容。
            model = block['models'][method]
            del model['values']['oto06']
            model['values']['oto05'] = values.tolist()
            del model['bars']['oto06']

        # 与上一版采用相同种子、相同 PDB 顺序、每次 250 个索引的 bootstrap。
        rng = np.random.default_rng(SEED)
        matrix = np.column_stack([block['models'][method]['values'][metric]
                                  for method in MODELS for metric in ('dice', 'oto03', 'oto05')])
        means = np.concatenate([matrix[rng.integers(0, len(ids), size=(250, len(ids)))].mean(axis=1)
                                for _ in range(BOOTSTRAP_N // 250)])
        bounds = np.quantile(means, [.025, .975], axis=0)
        for i, method in enumerate(MODELS):
            index = i * 3 + 2
            block['models'][method]['bars']['oto05'] = {
                'mean': float(matrix[:, index].mean()),
                'lower': float(bounds[0, index]),
                'upper': float(bounds[1, index]),
            }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'plot_data.json').write_text(json.dumps(plot, ensure_ascii=False), encoding='utf-8')
    (args.output / 'science_checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.output / 'source_data.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['cohort', 'method', 'pdb_id', 'resolution_angstrom',
                         'dice', 'oto03', 'oto05', 'precision', 'recall'])
        for cohort in ('full', 'small'):
            block = plot['cohorts'][cohort]
            for method in MODELS:
                values = block['models'][method]['values']
                for i, pdb in enumerate(block['ids']):
                    writer.writerow([cohort, method, pdb, block['resolution'][i]]
                                    + [values[key][i] for key in ('dice', 'oto03', 'oto05', 'precision', 'recall')])
    with (args.output / 'bar_statistics.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['cohort', 'method', 'metric', 'n', 'mean', 'ci95_lower', 'ci95_upper'])
        for cohort in ('full', 'small'):
            block = plot['cohorts'][cohort]
            for method in MODELS:
                for metric in ('dice', 'oto03', 'oto05'):
                    item = block['models'][method]['bars'][metric]
                    writer.writerow([cohort, method, metric, block['n'], item['mean'], item['lower'], item['upper']])
    print(json.dumps(checks, ensure_ascii=False))
