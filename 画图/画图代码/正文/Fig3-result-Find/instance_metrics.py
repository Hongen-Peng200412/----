"""用指定双向覆盖阈值建立实例匹配边, 计算一对一PRAUC和最终候选P/R.

coverage_edges只建立当前阈值的边, prauc按原资格和分数组扫描断点, evaluate_selected只评估原最终选择. 非小分子忽略掩码唯一引用同目录matching.py, 不在本文件复制0.3归属实现.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
from TOOLS.runtime.paths import load_module

MATCHING = load_module(Path(__file__).with_name("matching.py"), "fig3_find_matching")


def coverage_edges(fact: dict[str, object], threshold: float) -> np.ndarray:
    """返回本次指定双向覆盖阈值的最大匹配候选边, 不重定类别归属.

    输入参数:
        - fact: dict, 当前单个PDB由调用方指定的同轴原数组; 可以是完整候选/全部真实实例, 也可以是调用方已经筛选的两轴.
            - intersections: int数组, (P,G), 当前候选轴与真实实例轴的体素交集数.
            - pred_sizes/gt_sizes: (P,)/(G,), 与上述两轴对齐的完整体素数, 不以交集数代替分母.
        - threshold: float, 当前图匹配阈值, 如0.5.
    返回值:
        - edges: bool数组, (P,G), True表示两向覆盖均达到threshold; 零体素分母没有有效边, 本函数不筛selected或真实类别."""
    intersections = fact["intersections"]
    pred_sizes = fact["pred_sizes"]
    gt_sizes = fact["gt_sizes"]
    pred_cover = np.divide(
        intersections,
        pred_sizes[:, None],
        out=np.zeros(intersections.shape, dtype=np.float64),
        where=pred_sizes[:, None] > 0,
    )
    gt_cover = np.divide(
        intersections,
        gt_sizes[None, :],
        out=np.zeros(intersections.shape, dtype=np.float64),
        where=gt_sizes[None, :] > 0,
    )
    return (pred_cover >= threshold) & (gt_cover >= threshold)


def prauc(facts: list[dict[str, object]], edges: list[np.ndarray], mode: str) -> float:
    """按原float32分数组扫描阶梯PRAUC, 一对一模式保持最大二分匹配数.

    输入参数:
        - facts: list[dict], 每项一个PDB, 与edges逐PDB对齐.
            - pdb_id: str, 如9nvs, 用于相同评分下的稳定PDB顺序.
            - score: float32数组, (N_kept,), 原候选评分, 精确相等的float32值在同一断点处理.
            - eligible: bool数组, (N_kept,), True表示可进入PRAUC扫描, 不等于最终selected.
            - gt_sizes: (N_small_gt,), 小分子真实实例轴, 其长度确定该PDB真实分母.
        - edges: list[np.ndarray], 每项bool(N_kept,N_small_gt), 与对应fact两轴对齐.
        - mode: str, one_to_one为最大一对一匹配, coverage为有任意边的覆盖计数; 本组图使用one_to_one.
    返回值:
        - area: float, 0-1阶梯PRAUC, 每个分数断点贡献为新增recall乘该点precision; 无合格候选时为0.
    不把最终selected的单点P/R代替整条PRAUC扫描."""
    # 每项是实际 float32 候选分数、PDB 轴下标、保留候选轴下标; 非合格候选和已忽略候选均不进入扫描.
    ranked = [
        (float(score), pdb_index, candidate_index)
        for pdb_index, fact in enumerate(facts)
        for candidate_index, score in enumerate(fact["score"])
        if fact["eligible"][candidate_index]
    ]
    ranked.sort(key=lambda item: (-item[0], facts[item[1]]["pdb_id"], item[2]))
    if not ranked:
        return 0.0
    # 长度 N_pdb 的列表, 每项 bool (N_small_gt_i,), True 表示当前分数断点之前该小分子 GT 已被至少一个扫描候选覆盖.
    covered_gt = [np.zeros(fact["gt_sizes"].size, dtype=np.bool_) for fact in facts]
    # 长度 N_pdb 的列表, 每项 int64 (N_small_gt_i,), 每个小分子 GT 当前匹配的保留候选轴下标; -1 表示未匹配.
    matched_gt = [np.full(fact["gt_sizes"].size, -1, dtype=np.int64) for fact in facts]
    # adjacency[i][j] 是第 i 个 PDB 的第 j 个保留候选能匹配的小分子 GT 轴下标数组.
    adjacency = [[np.flatnonzero(row) for row in matrix] for matrix in edges]

    def augment(pdb_index: int, candidate_index: int, visited: np.ndarray) -> bool:
        """为一个候选寻找一条增广路, 原地更新当前PDB的匹配轴.

        pdb_index和candidate_index分别为facts及该PDB候选的紧凑下标. visited为bool(N_small_gt,), 防止本次递归重复访问真实实例; matched_gt同轴记录候选下标, -1表示未匹配. 返回bool说明是否新增一次成功匹配.
        """
        for gt_index in adjacency[pdb_index][candidate_index]:
            if visited[gt_index]:
                continue
            visited[gt_index] = True
            previous = matched_gt[pdb_index][gt_index]
            if previous < 0 or augment(pdb_index, int(previous), visited):
                matched_gt[pdb_index][gt_index] = candidate_index
                return True
        return False

    # total_gt 是本次 micro 扫描中的小分子 GT 总数, 作为所有分数断点的 recall 分母.
    total_gt = sum(int(fact["gt_sizes"].size) for fact in facts)
    # total_pred 是当前断点前已扫描的 PRAUC 合格候选数, 包括未命中小分子的假阳性.
    total_pred = 0
    # pred_hit 是当前阈值下有有效覆盖边或已进入一对一匹配的已扫描候选数.
    pred_hit = 0
    # gt_hit 是已覆盖或已进入一对一匹配的小分子 GT 数, 作为 recall 分子.
    gt_hit = 0
    previous_recall = 0.0
    area = 0.0
    offset = 0
    while offset < len(ranked):
        score = ranked[offset][0]
        end = offset + 1
        while end < len(ranked) and ranked[end][0] == score:
            end += 1
        for _, pdb_index, candidate_index in ranked[offset:end]:
            total_pred += 1
            neighbors = adjacency[pdb_index][candidate_index]
            if mode == "coverage":
                pred_hit += bool(neighbors.size)
                new_gt = neighbors[~covered_gt[pdb_index][neighbors]]
                covered_gt[pdb_index][new_gt] = True
                gt_hit += int(new_gt.size)
            else:
                visited = np.zeros(matched_gt[pdb_index].size, dtype=np.bool_)
                if augment(pdb_index, candidate_index, visited):
                    pred_hit += 1
                    gt_hit += 1
        recall = gt_hit / total_gt if total_gt else 0.0
        area += (recall - previous_recall) * (pred_hit / total_pred)
        previous_recall = recall
        offset = end
    return float(area)


# ================================================================================================
def evaluate_selected(intersections, pred_sizes, gt_sizes, occurrence_ids, gt_types, selected, threshold):
    """在固定类别归属和原最终选择下计算小分子最大一对一P/R.

    输入参数:
        - intersections: int数组, (N_pred,N_gt), 原完整候选与全部真实类别实例的交集体素数.
        - pred_sizes/gt_sizes: (N_pred,)/(N_gt,), 分别与交集第一/第二轴对齐的完整体素数.
        - occurrence_ids/gt_types: (N_gt,), 原真实实例编号和类别, 如1与small_molecule, 不以数组位置当原编号.
        - selected: bool数组, (N_pred,), True为原最终选中候选, 不按本次阈值重新选择.
        - threshold: float, 当前P/R的匹配覆盖下限, 如0.5; 固定非小分子归属仍按0.3.
    返回值:
        - ignored_candidate_count: int, 固定归属其他类别而不计入小分子分析的候选数.
        - selected_count: int, 已选且未被忽略的候选数, 包含背景假阳性.
        - small_gt_count: int, 完整小分子真实分母.
        - matched_count_<suffix>: int, 当前最大一对一匹配数, suffix如0p5.
        - one_to_one_precision_<suffix>/one_to_one_recall_<suffix>: float, 匹配数除以selected_count/small_gt_count, 零分母记0."""
    # bool, (N_pred,), 与所有阈值共用的固定非小分子归属; True 的候选不计入本图小分子P/R.
    ignored = MATCHING.ignored_candidates(intersections, pred_sizes, gt_sizes, occurrence_ids, gt_types)
    # bool,(N_gt,), True表示该原真实轴位置是小分子, 与occurrence_ids逐项对齐.
    small_axis = np.array([t == "small_molecule" for t in gt_types], dtype=bool)
    # bool,(N_pred,), True表示原最终已选且未被固定归属忽略的预测候选.
    kept_selected = np.asarray(selected, bool) & ~ignored
    # bool,(N_selected,N_small), 唯一覆盖边规则先作用于完整两轴, 再沿预测/真实掩码切片.
    edges = coverage_edges(
        {"intersections": intersections, "pred_sizes": pred_sizes, "gt_sizes": gt_sizes}, threshold
    )[np.ix_(kept_selected, small_axis)]
    n_pred, n_gt = edges.shape
    matched = (
        int((maximum_bipartite_matching(csr_matrix(edges), perm_type="column") >= 0).sum()) if n_pred and n_gt else 0
    )
    suffix = str(threshold).replace(".", "p")
    return {
        "ignored_candidate_count": int(ignored.sum()),
        "selected_count": n_pred,
        f"matched_count_{suffix}": matched,
        "small_gt_count": n_gt,
        f"one_to_one_precision_{suffix}": matched / n_pred if n_pred else 0.0,
        f"one_to_one_recall_{suffix}": matched / n_gt if n_gt else 0.0,
    }
