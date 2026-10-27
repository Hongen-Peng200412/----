"""只读旧 Find 输入, 比较非空评价等价与空候选的完整分母; 全部新文件只写门控 tmp."""

import json
import os
import shutil
from pathlib import Path

import numpy as np
from src.inference.baseline import emap2lig_find as original

from evaluate_find import evaluate_find_pdb


if __name__ == '__main__':
    # 旧无 level 的原生输出只读, 使用一个现成 PDB 核对适配器逐字段一致.
    old_raw = Path('/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0/raw_find_outputs')
    # 原始真值网格, 只参与门控评价, 不向模型提供.
    data_root = '/storage/penghongen/AdaLigand/Ori_Data'
    # 本次 launch 专属门控目录, 不属于新旧正式实验根.
    gate_root = Path('/storage/penghongen/tmp/emap2lig_with_level_gate') / os.environ['TASK_RUN_STAMP'] / 'find_evaluation'
    pdb = '9llg'
    original._evaluate_one_pdb(pdb, str(old_raw), data_root, str(gate_root / 'original'), 8)
    evaluate_find_pdb(pdb, str(old_raw), data_root, str(gate_root / 'adapted'), 8)
    relative_paths = [f'evaluation/per_pdb/{pdb}.npz', f'mapped/{pdb}/probability_map.npz', f'mapped/{pdb}/official_blobs.npz']
    for relative in relative_paths:
        with np.load(gate_root / 'original' / relative, allow_pickle=False) as expected, np.load(gate_root / 'adapted' / relative, allow_pickle=False) as actual:
            assert set(expected.files) == set(actual.files)
            assert all(np.array_equal(expected[key], actual[key], equal_nan=True) for key in expected.files)
    # 空候选仅移除 mask 输入, 仍保留同一真实概率图, 以验证语义 PRAUC 不被伪造.
    empty_raw = gate_root / 'empty_raw'
    probability = empty_raw / pdb / 'find_maps/ligand.mrc'
    probability.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(old_raw / pdb / 'find_maps/ligand.mrc', probability)
    evaluate_find_pdb(pdb, str(empty_raw), data_root, str(gate_root / 'empty'), 8)
    with np.load(gate_root / 'empty' / f'evaluation/per_pdb/{pdb}.npz', allow_pickle=False) as empty, np.load(gate_root / 'original' / f'evaluation/per_pdb/{pdb}.npz', allow_pickle=False) as full:
        assert empty['intersections'].shape == (0, len(full['occurrence_id']))
        assert np.array_equal(empty['occurrence_id'], full['occurrence_id'])
        assert np.array_equal(empty['semantic_prauc_histogram'], full['semantic_prauc_histogram'])
        report = {'nonempty_fields_equal': True, 'empty_pred_count': 0, 'retained_gt_count': len(empty['occurrence_id']), 'real_probability_prauc_preserved': True}
    (gate_root / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)
