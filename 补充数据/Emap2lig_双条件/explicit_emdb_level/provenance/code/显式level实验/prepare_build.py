"""从新 Find 交集事实选择每个命中实例的原生 Build 输入.

先读 select_find_hits 的唯一归属规则, 再读 prepare_pdb 和 prepare_build. 24 个 CPU 进程读取逐 PDB 评价, 写出 RESULT_ROOT/find_hit_subset.jsonl 与 find_hit_summary.json; 真实坐标不参与输入选择或写出.
"""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from paths import FIND_BLOBS, FIND_EVALUATION, INPUT_ROOT, RESULT_ROOT


def select_find_hits(evaluation: np.lib.npyio.NpzFile) -> list[tuple[int, int, int]]:
    """先唯一归属 blob, 再为命中实例选覆盖几何均值最大的 blob.

    输入参数:
        - evaluation: NPZ, 一个 PDB 的原评价事实; P 是按均值概率排序的预测数, G 是该 PDB 全类别真实实例数.
            - intersections: (P, G), 每个预测与真实实例交集的体素数.
            - pred_sizes: (P,), 与 intersections 第一轴对齐的预测体素数.
            - gt_sizes: (G,), 与 intersections 第二轴对齐的真实体素数.
            - occurrence_id: int, (G,), 真值原实例编号, 如 3, 不等于数组下标.
            - source_blob_index: int, (P,), 预测数组下标对应的官方 blob_N 编号 N.
    返回值:
        - hits: list[tuple[int, int, int]], 每项为 occurrence_id、原 blob 编号、从 1 开始的 Find 排名.
    """
    # (P, G), 交集与双向覆盖; 任一方向低于 0.3 都不构成命中.
    intersections = evaluation['intersections'].astype(np.float64)
    pred_sizes = evaluation['pred_sizes'].astype(np.float64)
    gt_sizes = evaluation['gt_sizes'].astype(np.float64)
    pred_coverage = intersections / pred_sizes[:, None]
    gt_coverage = intersections / gt_sizes[None, :]
    valid = (pred_coverage >= 0.3) & (gt_coverage >= 0.3)
    geometric_mean = np.sqrt(pred_coverage * gt_coverage)
    # 真实实例数组下标 -> (覆盖几何均值, 预测数组下标), 一个 blob 只能归属一个真实实例.
    assigned = {}
    for blob_index in range(len(pred_sizes)):
        eligible = np.flatnonzero(valid[blob_index])
        if not len(eligible):
            continue
        best_gt = min(eligible, key=lambda gt: (-geometric_mean[blob_index, gt], int(evaluation['occurrence_id'][gt])))
        score = geometric_mean[blob_index, best_gt]
        if best_gt not in assigned or score > assigned[best_gt][0]:
            assigned[best_gt] = (score, blob_index)
    return [(int(evaluation['occurrence_id'][gt]), int(evaluation['source_blob_index'][blob]), blob + 1) for gt, (_, blob) in sorted(assigned.items())]


def prepare_pdb(arguments: tuple[Path, Path, list[dict]]) -> list[dict]:
    """读取一个 PDB 的新评价和原生 blob, 构造该 PDB 的命中请求.

    输入参数:
        - arguments: tuple, 依次为当前 PDB 的评价 NPZ、全部原生 PDB 目录的父路径、该 PDB 的冻结测试实例列表.
    返回值:
        - records: list[dict], 每个命中测试实例一项, 按 occurrence_id 排序.
            - pdb_id: str, 小写 PDB 标识, 如 9llg.
            - occurrence_id: int, 冻结 test.jsonl 的 candidate_id, 如 0.
            - blob_id: int, 该实例选中的原生 blob_N 编号 N.
            - find_rank: int, 从 1 开始的预测概率排名.
            - prepared_smiles: str, 冻结测试身份的精确化学字符串, 如 CCO.
            - n_heavy_atoms: int, 精确身份的重原子数.
            - foreground_voxels: int, 原生 blob.instance_grid 中的前景体素数.
            - voxel_atom_ratio: float, foreground_voxels / n_heavy_atoms.
            - status: str, 比值在 [5,25] 内为 ready, 否则 build_filter_failed.
            - blob_path: str, 原生 NPZ 的绝对路径, 只指向本轮新 Find.
    """
    evaluation_path, blob_root, frozen_rows = arguments
    pdb_id = evaluation_path.stem
    frozen = {int(row['candidate_id']): row for row in frozen_rows}
    with np.load(evaluation_path, allow_pickle=False) as evaluation:
        hits = select_find_hits(evaluation)
    records = []
    for occurrence_id, blob_id, rank in hits:
        if occurrence_id not in frozen:
            continue
        item = frozen[occurrence_id]
        # 本轮官方 Find 为该 PDB 写出的局部密度与掩码, 不是映射后的标签文件.
        blob_path = blob_root / pdb_id / 'find_blobs' / f'blob_{blob_id}.npz'
        with np.load(blob_path, allow_pickle=False) as blob:
            foreground_voxels = int(np.count_nonzero(blob['instance_grid']))
        heavy_atoms = int(item['n_heavy_atoms'])
        ratio = foreground_voxels / heavy_atoms
        records.append({
            'pdb_id': pdb_id, 'occurrence_id': occurrence_id, 'blob_id': blob_id,
            'find_rank': rank, 'prepared_smiles': item['prepared_smiles'],
            'n_heavy_atoms': heavy_atoms, 'foreground_voxels': foreground_voxels,
            'voxel_atom_ratio': ratio, 'status': 'ready' if 5 <= ratio <= 25 else 'build_filter_failed',
            'blob_path': str(blob_path),
        })
    return records


def prepare_build() -> None:
    """用 24 个进程生成动态命中集合, 不固定为旧 243/237 个实例.

    落盘文件:
        - <RESULT_ROOT>/find_hit_subset.jsonl: 每行是 prepare_pdb 定义的一个命中实例请求.
        - <RESULT_ROOT>/find_hit_summary.json: object, full_occurrences 为完整测试实例数, find_hit_pdbs 为命中 PDB 数, find_top1/find_top5/find_best 为相应排名覆盖数, build_ready 为有效输入数, build_filter_failed 为 PDB/实例编号字符串列表, subset_path 为上述 JSONL 的绝对路径.
    """
    # 本次已冻结的 446 个化学身份输入, 不重新筛选测试成员.
    frozen_path = INPUT_ROOT / 'test.jsonl'
    frozen_rows = [json.loads(line) for line in frozen_path.read_text(encoding='utf-8').splitlines()]
    assert len(frozen_rows) == 446
    grouped = {}
    for item in frozen_rows:
        grouped.setdefault(item['pdb_id'], []).append(item)
    # 一个进程处理一个 PDB, map 按 PDB 顺序返回, 与进程完成先后无关.
    jobs = [(FIND_EVALUATION / f'{pdb}.npz', FIND_BLOBS, rows) for pdb, rows in sorted(grouped.items())]
    with ProcessPoolExecutor(max_workers=24) as pool:
        records = [row for group in pool.map(prepare_pdb, jobs) for row in group]
    assert len({(row['pdb_id'], row['occurrence_id']) for row in records}) == len(records)
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    # 每个命中实例的唯一 Build 请求, 包含保留在分母中的输入筛选失败.
    subset_path = RESULT_ROOT / 'find_hit_subset.jsonl'
    subset_path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records), encoding='utf-8')
    summary = {
        'full_occurrences': len(frozen_rows), 'find_hit_pdbs': len({row['pdb_id'] for row in records}),
        'find_top1': sum(row['find_rank'] <= 1 for row in records),
        'find_top5': sum(row['find_rank'] <= 5 for row in records), 'find_best': len(records),
        'build_ready': sum(row['status'] == 'ready' for row in records),
        'build_filter_failed': [f"{row['pdb_id']}/{row['occurrence_id']}" for row in records if row['status'] == 'build_filter_failed'],
        'subset_path': str(subset_path),
    }
    (RESULT_ROOT / 'find_hit_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    prepare_build()
