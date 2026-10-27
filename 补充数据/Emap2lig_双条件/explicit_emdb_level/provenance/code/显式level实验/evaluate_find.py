"""复用固定 Pocket Plus Find 评价器, 让合法空候选保留在完整测试集中.

主要入口 evaluate_find_pdb 逐图写出原映射与评价文件; main 将原进程池的逐图入口替换为本函数, 聚合、149-PDB 派生评价与命令行仍由原 release 执行. 仅放开非空候选前置条件, 不修改原概率、插值、匹配、排名或指标. 输入输出字段见本目录 README.
"""

from pathlib import Path

import numpy as np
from src.inference.baseline import emap2lig_find as original


# ================================================================================================
def evaluate_find_pdb(
    pdb_id: str,
    raw_find_root: str,
    data_root: str,
    split_root: str,
    chunk_depth: int,
) -> str:
    """沿用固定评价器的逐图映射, 接受完成推断后的零个候选.

    输入参数:
        - pdb_id: str, 当前测试 PDB, 如 9llg.
        - raw_find_root: str, 本条件逐 PDB 原生产物的父路径.
        - data_root: str, 原标签根, 从 density/<pdb>/ 只读网格、实例和并集.
        - split_root: str, 本条件 held_out_test_0 的映射和评价产物根.
        - chunk_depth: int, 概率线性插值按 Z 轴分块的层数, 正式为 8.
    返回值:
        - pdb_id: str, 完成当前 PDB 后返回原标识.

    mapped/<pdb>/ 写 probability_map.npz、official_blobs.npz、mapping.json; evaluation/per_pdb/<pdb>.npz 写原交集及指标事实, 完整字段见 README 的原生与评价网格. 候选为零时仍写 (0,G) 交集, 原语义 PRAUC 继续消费真实概率, G 是该 PDB 全部真实实例数. 除删除“必须有 mask_N”这一前置条件外, 本函数与固定 release 的 _evaluate_one_pdb 保持相同可执行语句.
    """

    # source_root: 当前 PDB 的原始 Emap2lig 官方输出目录.
    source_root = Path(raw_find_root) / pdb_id
    # probability_path: 官方完整 ligand probability MRC.
    probability_path = source_root / "find_maps" / "ligand.mrc"
    # mask_paths: 按官方编号排序的全部 >=32 体素实例 MRC.
    mask_paths = original._numbered_mask_paths(source_root / "find_blobs")
    if not probability_path.is_file():
        raise FileNotFoundError(probability_path)

    # density_root: 当前 PDB 的 Pocket Plus V3 真值目录.
    density_root = Path(data_root) / "density" / pdb_id
    with np.load(density_root / "ligand_area.npz", allow_pickle=False) as ligand_area:
        # target_shape_zyx: int64 (3,), 真值完整图 ZYX 形状.
        target_shape_zyx = np.asarray(ligand_area["grid_shape_zyx"], dtype=np.int64)
        # target_voxel_size_xyz: float32 (3,), 真值网格世界 XYZ 体素尺寸.
        target_voxel_size_xyz = np.asarray(
            ligand_area["voxel_size_xyz"], dtype=np.float32
        )
        # target_origin_xyz: float32 (3,), 真值网格角点世界坐标.
        target_origin_xyz = np.asarray(ligand_area["origin_xyz"], dtype=np.float32)

    # source_probability: float32 (D_src,H_src,W_src), 官方原生 ligand probability.
    source_probability, source_voxel_size_xyz, source_origin_xyz = original._read_official_mrc(
        probability_path
    )
    # mapped_probability: float32 (D,H,W), 目标 V3 网格上的线性插值概率.
    mapped_probability = original._map_probability(
        source_probability,
        source_voxel_size_xyz,
        source_origin_xyz,
        target_shape_zyx,
        target_voxel_size_xyz,
        target_origin_xyz,
        chunk_depth,
    )
    if not np.isfinite(mapped_probability).all():
        raise ValueError(f"{pdb_id}: 映射概率含非有限值.")
    # candidates: 官方实例身份不变的目标稀疏坐标与原生平均概率.
    candidates = original._map_official_candidates(
        mask_paths,
        source_probability,
        source_voxel_size_xyz,
        source_origin_xyz,
        target_shape_zyx,
        target_voxel_size_xyz,
        target_origin_xyz,
    )

    # mapped_root: 当前 PDB 的目标网格概率与稀疏实例目录.
    mapped_root = Path(split_root) / "mapped" / pdb_id
    original.publish_stage1_artifact(
        mapped_root / "probability_map.npz",
        {
            "probability_map": mapped_probability,
            "origin_xyz": target_origin_xyz,
            "voxel_size_xyz": target_voxel_size_xyz,
        },
        None,
    )
    original.publish_stage1_artifact(
        mapped_root / "official_blobs.npz",
        {
            **candidates,
            "origin_xyz": target_origin_xyz,
            "voxel_size_xyz": target_voxel_size_xyz,
            "grid_shape_zyx": target_shape_zyx,
        },
        None,
    )

    occurrence_id, occurrence_rows, full_shape = original.load_occurrence_voxels(
        density_root / "ligand_area.npz"
    )
    # centered: evaluate_centered_pdb 消费的完整图稀疏候选视图.
    centered = {
        "source_blob_index": candidates["source_blob_index"],
        "score": candidates["score"],
        "selected": candidates["selected"],
        "prauc_eligible": candidates["prauc_eligible"],
        "voxel_offsets": candidates["voxel_offsets"],
        "voxel_index_local_zyx": candidates["voxel_index_global_zyx"],
        "box_start_zyx": np.zeros(
            (candidates["source_blob_index"].size, 3), dtype=np.int32
        ),
    }
    # evaluation: 当前 PDB 的完整语义、交集、匹配和 top-K 事实.
    evaluation = original.evaluate_centered_pdb(
        pdb_id=pdb_id,
        centered=centered,
        occurrence_id=occurrence_id,
        occurrence_voxel_zyx=occurrence_rows,
        full_shape_zyx=full_shape,
        coverage_thresholds=original.COVERAGE_THRESHOLDS,
        topk_values=original.TOPK_VALUES,
    )
    # union_mask: bool (D,H,W), 所有真实 occurrence 的体素并集.
    union_mask = np.load(
        density_root / "union_mask.npy",
        mmap_mode="r",
        allow_pickle=False,
    )[0]
    # histogram: int64 (2,1024), 完整概率图的语义 PRAUC 计数.
    histogram = original.semantic_prauc_histogram(mapped_probability, union_mask)
    original.publish_stage1_artifact(
        Path(split_root) / "evaluation" / "per_pdb" / f"{pdb_id}.npz",
        original._evaluation_arrays(evaluation, histogram),
        None,
    )
    original.publish_stage1_json(
        mapped_root / "mapping.json",
        {
            "pdb_id": pdb_id,
            "official_probability": str(probability_path),
            "official_blob_count": len(mask_paths),
            "mapped_blob_count": int(candidates["source_blob_index"].size),
            "source_shape_zyx": list(source_probability.shape),
            "source_voxel_size_xyz": source_voxel_size_xyz.tolist(),
            "source_origin_xyz": source_origin_xyz.tolist(),
            "target_shape_zyx": target_shape_zyx.tolist(),
            "target_voxel_size_xyz": target_voxel_size_xyz.tolist(),
            "target_origin_xyz": target_origin_xyz.tolist(),
        },
    )
    return pdb_id

if __name__ == '__main__':
    # 原进程池仍用原 _evaluate_one_pdb_star 展开参数; 只把其逐图函数换为支持零候选的同义实现.
    original._evaluate_one_pdb = evaluate_find_pdb
    original.run_evaluation(original.parse_args())
