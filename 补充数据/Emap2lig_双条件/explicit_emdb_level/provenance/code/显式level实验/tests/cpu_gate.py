"""只读核对旧请求选择等价性与 RMSD 坐标定义, 不运行模型、不写旧产物."""

import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from rdkit import Chem

from evaluate import rmsd_without_alignment
from paths import FROZEN_TEST, SOURCE_INPUTS
from prepare_build import prepare_pdb


if __name__ == '__main__':
    # 原无 level 产物仅用于读取既有交集事实和已验收请求, 所有函数在内存比较.
    old_find = Path('/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0')
    old_subset = Path('/storage/penghongen/Emap2lig/stage3_find_hit_build/find_hit_subset.jsonl')
    frozen = [json.loads(line) for line in FROZEN_TEST.read_text(encoding='utf-8').splitlines()]
    grouped = defaultdict(list)
    for row in frozen:
        grouped[row['pdb_id']].append(row)
    jobs = [(old_find / 'evaluation/per_pdb' / f'{pdb}.npz', old_find / 'raw_find_outputs', rows) for pdb, rows in sorted(grouped.items())]
    with ProcessPoolExecutor(max_workers=24) as pool:
        actual = [row for rows in pool.map(prepare_pdb, jobs) for row in rows]
    expected = [json.loads(line) for line in old_subset.read_text(encoding='utf-8').splitlines()]
    assert actual == expected
    assert len(actual) == 243 and sum(row['status'] == 'ready' for row in actual) == 237
    maps = json.loads((SOURCE_INPUTS / 'maps.json').read_text(encoding='utf-8'))
    pdbs = json.loads((SOURCE_INPUTS / 'test_0.json').read_text(encoding='utf-8'))['pdb_ids']
    assert [row['pdb_id'] for row in maps] == pdbs and len(maps) == 179
    assert all(row['level'] > 0 and row['effective_threshold'] == row['level'] * 0.5 for row in maps)
    # 构造的 CCO 坐标整体平移 1 Å, 不做刚体对齐的 RMSD 应为 1, 不能退化为 0.
    molecule = Chem.MolFromSmiles('CCO')
    xyz = np.asarray([[0., 0., 0.], [1.5, 0., 0.], [2., 1., 0.]])
    rmsd, fallback = rmsd_without_alignment(molecule, xyz + [0., 0., 1.], xyz)
    assert abs(rmsd - 1.0) < 1e-12 and not fallback
    print(json.dumps({'old_request_records_equal': len(actual), 'old_ready_equal': 237, 'maps_with_level': len(maps), 'translation_rmsd_A': rmsd}), flush=True)

