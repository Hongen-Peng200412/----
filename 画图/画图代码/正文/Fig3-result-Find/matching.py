"""按Find原规则确定候选的唯一真实归属及小分子分析的固定忽略掩码.

target_from_intersections由Find和显式引用的E2E预算逻辑共同调用. ignored_candidates把这一唯一归属映射成非小分子忽略标记. 两函数均只处理内存数组, 不读取服务器、不重定0.5评估的类别归属.
"""

from __future__ import annotations
import numpy as np

COVERAGE_THRESHOLD = 0.3


def target_from_intersections(
    occurrence_ids: np.ndarray,
    intersections: np.ndarray,
    candidate_size: int,
    occurrence_sizes: np.ndarray,
) -> tuple[int | None, float, float, float]:
    """按固定双向覆盖0.3和几何平均选择一个预测候选的唯一真实实例.

    输入参数:
        - occurrence_ids: int数组, (N_occurrence,), 原真实实例编号, 如7, 不等于NPZ第二轴位置.
        - intersections: int数组, (N_occurrence,), 当前预测候选与各真实实例的交集体素数.
        - candidate_size: int, 当前预测blob完整体素数.
        - occurrence_sizes: (N_occurrence,), 与occurrence_ids逐项对应的真实实例完整体素数.
    返回值:
        - matched_occurrence_id: int或None, 几何平均最大的合格原实例编号, 并列取较小编号; 无合格实例为None.
        - candidate_coverage/occurrence_coverage: float, 所选交集占预测/真实体素数比例, 背景为0.
        - overlap_score: float, 两项覆盖的几何平均, 背景为0.
    本规则由Find图、关联补图和显式引用的完成度逻辑共用, 不因0.5显示阈值而改动."""
    candidate_coverage = intersections.astype(np.float64) / float(candidate_size)
    occurrence_coverage = intersections.astype(np.float64) / occurrence_sizes.astype(np.float64)
    eligible = (candidate_coverage >= COVERAGE_THRESHOLD) & (occurrence_coverage >= COVERAGE_THRESHOLD)
    if not bool(np.any(eligible)):
        return None, 0.0, 0.0, 0.0
    overlap_score = np.sqrt(candidate_coverage * occurrence_coverage)
    eligible_positions = np.flatnonzero(eligible)
    # 整数紧凑下标,(K,), 先按几何平均降序、原真实编号升序排序; order索引eligible_positions, 后者再映回occurrence_ids的原真实轴位置.
    order = np.lexsort(
        (
            occurrence_ids[eligible_positions],
            -overlap_score[eligible_positions],
        )
    )
    position = int(eligible_positions[int(order[0])])
    return (
        int(occurrence_ids[position]),
        float(candidate_coverage[position]),
        float(occurrence_coverage[position]),
        float(overlap_score[position]),
    )


def ignored_candidates(
    intersections: np.ndarray,
    pred_sizes: np.ndarray,
    gt_sizes: np.ndarray,
    occurrence_id: np.ndarray,
    gt_type: list[str],
) -> np.ndarray:
    """按固定0.3归属标记属于其他真实类别的预测候选.

    输入参数:
        - intersections: int数组, (N_pred,N_gt), 预测blob与全部真实实例的体素交集数; N_pred为完整候选数, N_gt为原真实实例数.
        - pred_sizes: (N_pred,), 每个预测blob的完整体素数, 与intersections第一轴对齐.
        - gt_sizes: (N_gt,), 每个真实实例体素数, 与intersections第二轴对齐.
        - occurrence_id: int数组, (N_gt,), 原真实实例编号, 如1; 不是第二轴紧凑位置.
        - gt_type: list[str], (N_gt,), 原实例类别, 如small_molecule; 与occurrence_id逐项对齐.
    返回值:
        - ignored: bool数组, (N_pred,), True表示候选固定归属于非小分子, 后续0.3和0.5分析都整项忽略; 无有效归属的背景为False.
    归属先要求两向覆盖均至少0.3, 再取覆盖率几何平均最大者, 并列取较小occurrence_id. 不随之后P/R阈值改动."""
    # bool,(N_pred,), True表示固定归属为非小分子; 归属只调用同文件唯一target_from_intersections规则.
    ignored = np.zeros(pred_sizes.size, dtype=np.bool_)
    # 原实例编号映射回真实轴位置, 不是以编号直接索引gt_type; 如occurrence_id=7可位于第二轴下标0.
    position = {int(identifier): index for index, identifier in enumerate(occurrence_id)}
    for pred_index in range(pred_sizes.size):
        if pred_sizes[pred_index] <= 0:
            continue
        matched, _, _, _ = target_from_intersections(
            occurrence_id, intersections[pred_index], int(pred_sizes[pred_index]), gt_sizes
        )
        if matched is not None:
            ignored[pred_index] = gt_type[position[matched]] != "small_molecule"
    return ignored
