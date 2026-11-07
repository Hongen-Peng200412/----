"""把原预测blob和真实小分子实例投到同一全图网格, 计算语义并集TP/FP/FN.

semantic_counts只负责区域并集, 输入候选已经由调用方完成固定归属过滤与选择. 本文件不决定候选排序、实例匹配阈值或PDB范围, 不读取显示图片推断科学区域.
"""

import numpy as np


# ================================================================================================
def semantic_counts(
    blob_arrays: dict,
    source_blob_index: np.ndarray,
    selected: np.ndarray,
    small_gt_rows: list[np.ndarray],
    full_shape: tuple[int, int, int],
) -> tuple[int, int, int]:
    """由原全图稀疏区域求已选预测并集与小分子真实并集的TP/FP/FN.

    输入参数:
        - blob_arrays: dict, 原blob NPZ具名数组, 不用显示图的像素推断区域.
            - source_blob_index或blob_index: int数组, (N_blob,), 来源blob编号, 如11; 不等于紧凑轴下标.
            - voxel_offsets: int数组, (N_blob+1,), 相邻两个offset切分voxel_index_global_zyx的当前blob行段, 首值0, 末值等于总坐标行数.
            - voxel_index_global_zyx: int数组, (N_voxel,3), 所有blob的全图ZYX体素坐标, 各段由voxel_offsets切分.
        - source_blob_index: int数组, (N_pred,), 已按本图科学规则保留的原blob编号.
        - selected: bool数组, (N_pred,), 与上述原编号对齐的最终选择掩码.
        - small_gt_rows: list[np.ndarray], 每项(K_gt,3)为一个小分子真实实例的全图ZYX体素坐标.
        - full_shape: tuple[int,int,int], 完整实验网格的Z/Y/X尺寸, 如(128,128,128), 用于C-order线性索引.
    返回值:
        - tp: int, 预测并集与真实并集的交集体素数.
        - fp: int, 只在预测并集中的体素数.
        - fn: int, 只在真实并集中的体素数.
    同一体素在重叠实例中只计一次, 不改变原世界坐标或网格约定."""
    archive = blob_arrays
    blob_ids = np.asarray(
        archive["source_blob_index" if "source_blob_index" in archive else "blob_index"], dtype=np.int32
    )
    offsets = np.asarray(archive["voxel_offsets"], dtype=np.int64)
    coordinates = np.asarray(archive["voxel_index_global_zyx"], dtype=np.int64)
    # 原始 blob 编号 -> 来源 NPZ 的紧凑候选位置; 例如 Emap2lig 的 blob_11 对应 source_blob_index=11.
    blob_position = {int(blob_id): index for index, blob_id in enumerate(blob_ids)}
    # 列表元素均为一维 C-order 线性体素编号; 只纳入最终 selected 且未被忽略的 blob.
    pred_parts = []
    for blob_id in source_blob_index[selected]:
        index = blob_position[int(blob_id)]
        rows = coordinates[int(offsets[index]) : int(offsets[index + 1])]
        pred_parts.append(np.ravel_multi_index(rows.T, full_shape))
    # (K_pred_union,), 已选且未忽略 blob 的唯一全图 C-order 线性体素编号.
    pred_union = np.unique(np.concatenate(pred_parts)) if pred_parts else np.empty(0, dtype=np.int64)
    gt_parts = [np.ravel_multi_index(rows.T, full_shape) for rows in small_gt_rows]
    # (K_gt_union,), 全部小分子真实实例的唯一全图 C-order 线性体素编号.
    gt_union = np.unique(np.concatenate(gt_parts))
    tp = int(np.intersect1d(pred_union, gt_union, assume_unique=True).size)
    return tp, int(pred_union.size - tp), int(gt_union.size - tp)
