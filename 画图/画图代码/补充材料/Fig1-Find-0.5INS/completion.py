"""计算补Fig1独有的100%/300%候选预算完成度, 不建立其他图的预算曲线.

prepare_completion从本次prepare_find给出的原候选、交集及真实成员构造六个面板. 固定类别归属由正文Fig3的matching.py唯一提供. 输出各PDB的完整分母、预算和去重成功数, 以及本图使用的PDB bootstrap均值区间.
"""

from pathlib import Path
import numpy as np
from TOOLS.runtime.paths import load_module

ROOT = Path(__file__).resolve().parents[4]
MATCHING = load_module(ROOT / "画图/画图代码/正文/Fig3-result-Find/matching.py", "fig3_find_matching")
FIXED_BUDGET = load_module(
    ROOT / "画图/画图代码/正文/Fig6-result-E2E/completion.py", "fig6_completion_records"
).fixed_budget_records


# ================================================================================================
def prepare_completion(data, inputs):
    """组装两个范围乘三个方法的预算分布与均值区间.

    输入参数:
        - data: dict, 本次显式level的plot_data, cohorts.full/small.ids分别是179/94个PDB的原顺序.
        - inputs: dict, facts[method,pdb]为原交集NPZ, types[pdb]为真实实例类别, original_candidates为GT/CA2完整原Find候选.

    返回值:
        - panels: list[dict], 长度6, 各含scope/domain/pdb_count/occurrence_count及distributions的100/300两份完整PDB记录.
            - distributions[预算][*]: dict, pdb_id、target_count、attempt_budget、success_count、completion; budget为100或300, 预算为budget*target_count//100, completion=去重成功数/完整目标数, 如3目标、100%预算为3次尝试.
        - summary: dict, 键(cohort,method,budget), mean/lower/upper为PDB等权完成比例和10,000次PDB bootstrap的95%区间, 不是实例合并比例.
    """
    facts, types, candidate_tables = inputs["facts"], inputs["types"], inputs["original_candidates"]
    panels, summary = [], {}
    for cohort, scope in (("full", "find_full"), ("small", "find_stage1_small")):
        ids = data["cohorts"][cohort]["ids"]
        # int64,(10000,N_pdb), 重采样轴索引与当前cohort.ids对齐, 所有方法/预算共用同一索引.
        indices = np.random.default_rng(20260922).integers(0, len(ids), size=(10000, len(ids)))
        for method in ("GT", "Cryo", "Emap"):
            denominators, successes = {}, {}
            for pdb in ids:
                arrays = facts[method, pdb]
                members = (
                    set(int(x) for x in arrays["occurrence_id"])
                    if cohort == "full"
                    else {identifier for identifier, tag in types[pdb].items() if tag == "small_molecule"}
                )
                denominators[pdb] = len(members)
                if method == "Emap":
                    candidates = []
                    for index in range(len(arrays["source_blob_index"])):
                        matched, _, _, _ = MATCHING.target_from_intersections(
                            arrays["occurrence_id"],
                            arrays["intersections"][index],
                            int(arrays["pred_sizes"][index]),
                            arrays["gt_sizes"],
                        )
                        candidates.append(
                            {
                                "candidate_selected": bool(arrays["candidate_selected"][index]),
                                "source_probability_mean": float(arrays["candidate_score"][index]),
                                "source_blob_index": int(arrays["source_blob_index"][index]),
                                "matched_occurrence_id": matched,
                                "foreground_target": matched is not None,
                            }
                        )
                else:
                    receptor = "real_receptor" if method == "GT" else "cryoatom2_receptor"
                    candidates = candidate_tables[receptor].get(pdb, [])
                # 原selected段优先, 再按原source_probability_mean降序和原blob编号升序; 不能把GT/CA2的Gaussian candidate_score用作原管线排序.
                ordered = sorted(
                    candidates,
                    key=lambda item: (
                        not item["candidate_selected"],
                        -item["source_probability_mean"],
                        item["source_blob_index"],
                    ),
                )
                success, examined = {}, 0
                for candidate in ordered:
                    matched = int(candidate["matched_occurrence_id"]) if candidate["foreground_target"] else None
                    if matched is not None and matched not in members:
                        continue
                    examined += 1
                    if matched is not None:
                        success.setdefault(matched, examined)
                successes[pdb] = success
            distributions = {}
            for budget in (100, 300):
                records = FIXED_BUDGET(denominators, successes, budget)
                distributions[str(budget)] = records
                by_pdb = {record["pdb_id"]: record for record in records}
                values = np.asarray([by_pdb[pdb]["completion"] for pdb in ids])
                lower, upper = np.percentile(values[indices].mean(axis=1), [2.5, 97.5])
                summary[cohort, method, budget] = {
                    "mean": float(values.mean()),
                    "lower": float(lower),
                    "upper": float(upper),
                }
            panels.append(
                {
                    "scope": scope,
                    "domain": {"GT": "GT", "Cryo": "CA2", "Emap": "Emap2lig"}[method],
                    "pdb_count": len(ids),
                    "occurrence_count": sum(denominators.values()),
                    "distributions": distributions,
                }
            )
    return panels, summary
