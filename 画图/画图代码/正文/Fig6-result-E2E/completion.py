"""完整PDB分母上的精确预算与去重首次成功统计."""

import bisect
import statistics
import numpy as np
from fractions import Fraction

PERCENTAGES = (0, 50, 100, 200, 300)


def fixed_budget_records(denominators, success_steps, percentage):
    """按整数百分比预算计算每个 PDB 的完成度, 保留所有零完成目标.

    输入参数:
        - denominators: dict[str, int], 每个 PDB 的全部本项合格目标实例数 N.
        - success_steps: dict[str, dict[int, int]], PDB 内 occurrence_id 到首次成功计费次数 K 的映射; 同一实例只保留最早成功.
        - percentage: int, 相对尝试预算的百分数, 如 50 表示每个 PDB 允许 floor(N/2) 次计费尝试.
    返回值:
        - records: list[dict], 按 PDB 字典序排列, 每个 PDB 一项.
            - pdb_id: str, 冻结 PDB 标识.
            - success_count: int, 预算内成功完成的不同配体实例数.
            - target_count: int, 该 PDB 完整目标实例分母 N.
            - attempt_budget: int, percentage*N//100, 不以浮点运算取整.
            - completion: float, success_count/target_count, 范围 [0, 1].
    """
    records = []
    for pdb_id, target_count in sorted(denominators.items()):
        attempt_budget = percentage * target_count // 100
        success_count = sum(step <= attempt_budget for step in success_steps[pdb_id].values())
        records.append(
            {
                "pdb_id": pdb_id,
                "success_count": success_count,
                "target_count": target_count,
                "attempt_budget": attempt_budget,
                "completion": success_count / target_count,
            }
        )
    return records


def make_panel(
    panel_id, scope, domain, denominators, success_steps, candidate_count, charged_count, threshold, pose_limit
):
    """将首次成功事件构造成可绘图面板, 均值和中位数均给每个 PDB 相同权重.

    输入参数:
        - panel_id/scope/domain: str, 完整条件ID、统计任务及方法, 如actual_CA2_pose5_rmsd3.0/actual/CA2; domain还可为GT或Emap2lig.
        - denominators、success_steps: 与 fixed_budget_records 相同的完整分母和去重首次成功事件.
        - candidate_count/charged_count: int, 当前范围原候选总数及完整候选用尽的计费总次数, 如598/513; 不受300%预算截断.
        - threshold: float 或 None, 严格 RMSD 阈值, 单位 Å; 全配体匹配面板为 None.
        - pose_limit: int 或 None, top-1 为 1、best-of-50 为 50; 全配体面板为 None.
    返回值:
        - panel: dict, 一个面板的结构化科学数据.
            - curve: dict, budget_percent、budget_numerator、budget_denominator、mean、median 为同长度列表; 每个事件处取事件已经完成后的值, 绘图须使用向右保持的阶梯.
            - distributions: dict[str, list[dict]], 百分比字符串到 fixed_budget_records 返回列表的映射.
            - all_candidates_final: dict, 全部冻结候选用尽后的宏平均、中位数、成功实例数及零完成/全完成 PDB 数, 不受 300% 绘图范围截断.
            - success_events: dict[str, list[dict]], 每个 PDB 的去重实例与首次成功次数, 供逐实例追溯.
    """
    # Fraction 保留 K/N 的精确值; 即使 N=3, 也不会因浮点 1/3 向下取整而错过事件.
    events = {Fraction(0), Fraction(3)}
    for pdb_id, steps in success_steps.items():
        events.update(
            Fraction(step, denominators[pdb_id]) for step in steps.values() if step <= 3 * denominators[pdb_id]
        )
    budgets = sorted(events)
    sorted_steps = {pdb_id: sorted(steps.values()) for pdb_id, steps in success_steps.items()}
    means, medians = [], []
    for budget in budgets:
        # (P,), 各 PDB 的实例完成比例; P 包括没有候选、身份错误及姿态失败的全部冻结 PDB.
        completion = [
            bisect.bisect_right(sorted_steps[pdb_id], budget.numerator * count // budget.denominator) / count
            for pdb_id, count in sorted(denominators.items())
        ]
        means.append(statistics.mean(completion))
        medians.append(statistics.median(completion))
    distributions = {str(p): fixed_budget_records(denominators, success_steps, p) for p in PERCENTAGES}
    final = [len(success_steps[pdb_id]) / count for pdb_id, count in sorted(denominators.items())]
    return {
        "id": panel_id,
        "scope": scope,
        "domain": domain,
        "threshold_A": threshold,
        "pose_limit": pose_limit,
        "pdb_count": len(denominators),
        "occurrence_count": sum(denominators.values()),
        "curve": {
            "budget_percent": [float(x * 100) for x in budgets],
            "budget_numerator": [x.numerator for x in budgets],
            "budget_denominator": [x.denominator for x in budgets],
            "mean": means,
            "median": medians,
        },
        "distributions": distributions,
        "all_candidates_final": {
            "mean": statistics.mean(final),
            "median": statistics.median(final),
            "success_occurrence_count": sum(len(x) for x in success_steps.values()),
            "zero_completion_pdb_count": sum(x == 0 for x in final),
            "full_completion_pdb_count": sum(x == 1 for x in final),
            "raw_candidate_count": candidate_count,
            "charged_attempt_count": charged_count,
        },
        "success_events": {
            pdb_id: [
                {"occurrence_id": occurrence_id, "first_success_attempt": step}
                for occurrence_id, step in sorted(steps.items())
            ]
            for pdb_id, steps in sorted(success_steps.items())
        },
    }


# ================================================================================================
def summarize_panels(panels):
    """只汇总调用方已经选定的面板, 返回master与逐PDB预算记录.

    panels: dict[str,dict], 每项保留完整success_events、curve、distributions和all_candidates_final. 返回master含panels/summaries/metadata; 每个summary的mean/median/ci_low/ci_high单位为百分比, 由完整PDB轴等权计算. metadata.conditions按本次实际scope/domain列出pdb_count和occurrence_count, 仅Emap2lig条目注明显式level, 不加入未请求范围. source_rows每项含panel_id/budget_percent及原逐PDB预算记录, 不再生成其他面板.
    """
    summaries, source_rows = {}, []
    indices = {
        n: np.random.default_rng(20261020).integers(0, n, size=(10000, n))
        for n in {p["pdb_count"] for p in panels.values()}
    }
    for panel_id, panel in panels.items():
        panel["polyline"] = {
            "is_step": True,
            "budget_percent": panel["curve"]["budget_percent"],
            "mean_percent": [100 * x for x in panel["curve"]["mean"]],
        }
        summaries[panel_id] = {}
        for budget, records in panel["distributions"].items():
            records = sorted(records, key=lambda r: r["pdb_id"])
            values = np.array([r["completion"] for r in records]) * 100
            low, high = np.quantile(values[indices[len(records)]].mean(axis=1), [0.025, 0.975])
            summaries[panel_id][budget] = {
                "mean": float(values.mean()),
                "median": float(np.median(values)),
                "ci_low": float(low),
                "ci_high": float(high),
            }
            source_rows.extend({"panel_id": panel_id, "budget_percent": int(budget), **r} for r in records)
    metadata = {
        "conditions": [
            {
                "scope": scope,
                "domain": domain,
                "pdb_count": pdb_count,
                "occurrence_count": occurrence_count,
                **({"emap2lig_level": "explicit_emdb_level"} if domain == "Emap2lig" else {}),
            }
            for scope, domain, pdb_count, occurrence_count in sorted(
                {(p["scope"], p["domain"], p["pdb_count"], p["occurrence_count"]) for p in panels.values()}
            )
        ],
        "bootstrap_replicates": 10000,
        "bootstrap_seed": 20261020,
        "ranking": "Original model ranking: minimum RMSD among first 1, 5 or 50 poses",
        "completion_unit": "PDB-equal mean of distinct successful instances / full eligible instances",
    }
    return {"metadata": metadata, "panels": panels, "summaries": summaries}, source_rows
