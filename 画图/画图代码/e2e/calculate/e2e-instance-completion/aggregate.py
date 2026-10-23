"""从冻结候选与姿态评价汇总每个 PDB 的配体实例完成度.

入口为 main, 运行 `python 画图/画图代码/e2e/calculate/e2e-instance-completion/aggregate.py` 即可复现本轮汇总.
本脚本只读取既有评价, 不运行 Find、Match、对接或 RMSD 计算.
新汇总位于 `画图/画图代码/e2e/output/e2e-instance-completion/regenerated/`, 原冻结产物只读:
    - completion.json: dict, panels 为 2 个全配体与 8 个合格小分子面板; 各面板含完整 PDB 分母、精确事件阶梯、固定预算分布及全部候选完成度.
    - per_pdb.csv: 每个面板、固定预算、PDB 一行, 保存分子、分母、整数预算及完成比例.
    - summary.csv: 每个面板、固定预算一行, 保存 PDB 等权均值、中位数、零完成与全部完成的 PDB 数.
    - source_manifest.json: dict, 保存输入路径、SHA256、来源规则与分母定义.
验收产物 audit.json 写入仓库 temp/e2e_completion_20261011/, 不作为新实验结果.
"""

import bisect
import csv
import hashlib
import json
import statistics
from fractions import Fraction
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
FROZEN = ROOT / "画图/画图代码/e2e/output/e2e-accounting"
OUTPUT = ROOT / "画图/画图代码/e2e/output/e2e-instance-completion/regenerated"
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
        records.append({"pdb_id": pdb_id, "success_count": success_count, "target_count": target_count, "attempt_budget": attempt_budget, "completion": success_count / target_count})
    return records


def make_panel(panel_id, scope, domain, denominators, success_steps, candidate_counts, charged_counts, threshold, pose_limit):
    """将首次成功事件构造成可绘图面板, 均值和中位数均给每个 PDB 相同权重.

    输入参数:
        - panel_id、scope、domain: str, 面板标识、full/small 范围及 GT/CA2 受体条件.
        - denominators、success_steps: 与 fixed_budget_records 相同的完整分母和去重首次成功事件.
        - candidate_counts、charged_counts: dict[str, int], 每个 PDB 的原始候选总数及全部计费尝试数.
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
        events.update(Fraction(step, denominators[pdb_id]) for step in steps.values() if step <= 3 * denominators[pdb_id])
    budgets = sorted(events)
    sorted_steps = {pdb_id: sorted(steps.values()) for pdb_id, steps in success_steps.items()}
    means, medians = [], []
    for budget in budgets:
        # (P,), 各 PDB 的实例完成比例; P 包括没有候选、身份错误及姿态失败的全部冻结 PDB.
        completion = [bisect.bisect_right(sorted_steps[pdb_id], budget.numerator * count // budget.denominator) / count for pdb_id, count in sorted(denominators.items())]
        means.append(statistics.mean(completion))
        medians.append(statistics.median(completion))
    distributions = {str(p): fixed_budget_records(denominators, success_steps, p) for p in PERCENTAGES}
    final = [len(success_steps[pdb_id]) / count for pdb_id, count in sorted(denominators.items())]
    return {
        "id": panel_id, "scope": scope, "domain": domain, "threshold_A": threshold, "pose_limit": pose_limit,
        "pdb_count": len(denominators), "occurrence_count": sum(denominators.values()),
        "curve": {"budget_percent": [float(x * 100) for x in budgets], "budget_numerator": [x.numerator for x in budgets], "budget_denominator": [x.denominator for x in budgets], "mean": means, "median": medians},
        "distributions": distributions,
        "all_candidates_final": {"mean": statistics.mean(final), "median": statistics.median(final), "success_occurrence_count": sum(len(x) for x in success_steps.values()), "zero_completion_pdb_count": sum(x == 0 for x in final), "full_completion_pdb_count": sum(x == 1 for x in final), "raw_candidate_count": sum(candidate_counts.values()), "charged_attempt_count": sum(charged_counts.values())},
        "success_events": {pdb_id: [{"occurrence_id": occurrence_id, "first_success_attempt": step} for occurrence_id, step in sorted(steps.items())] for pdb_id, steps in sorted(success_steps.items())},
    }


def main():
    """读取既有全候选轨迹、复核旧成功数并写出本轮 10 面板数据.

    输入文件:
        - stage1 metadata.json: rows[*].pdb_id 与 occurrence_count 定义 179 个 PDB 的 2,502 实例完整分母.
        - identities.jsonl: stage3_occurrence_ids 定义 77 个 PDB 的 446 个合格小分子实例, 同身份不同实例分别计数.
        - full_matcher.json: predictions 按受体条件和 PDB 保存全部候选, 保留 selected 段优先的排序.
        - GT/CA2 evaluation.json: traces 提供 Match 感知计费的 attempt_index、identity_correct 和 target_scope.
        - GT/CA2 docking_results.jsonl: methods.local_cov-C.success 提供原 self-ranking top-1 与 best-of-50 的严格 RMSD 判定.
    输出文件:
        - completion.json: schema、contract、panels; 每个面板字段见 make_panel.
        - per_pdb.csv: panel_id、scope、domain、threshold_A、pose_limit、budget_percent 及 fixed_budget_records 的逐 PDB 字段.
        - summary.csv: 面板与预算标识、mean、median、success_occurrence_count、zero_completion_pdb_count、full_completion_pdb_count.
        - source_manifest.json: contract 与 sources 列表; 每个来源保存相对路径、SHA256 和字节数.
        - temp/e2e_completion_20261011/audit.json: 旧成功数复现、固定分母、零候选、整数预算、去重和单调性核查.
    """
    metadata_path = ROOT / "画图/画图代码/stage1/output/stage1-source-metrics/metadata.json"
    full_path = FROZEN / "sources/full_matcher.json"
    identity_path = FROZEN / "sources/identities.jsonl"
    source_paths = [metadata_path, full_path, identity_path]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    full_counts = {row["pdb_id"]: row["occurrence_count"] for row in metadata["rows"]}
    full = json.loads(full_path.read_text(encoding="utf-8"))
    # 每个 PDB 一个实例集合; 不以预测命中数或唯一 SMILES 数作为分母.
    small_ids = {}
    for line in identity_path.read_text(encoding="utf-8").splitlines():
        identity = json.loads(line)
        if identity["stage3_occurrence_ids"]:
            small_ids.setdefault(identity["pdb_id"], set()).update(identity["stage3_occurrence_ids"])
    small_counts = {pdb_id: len(ids) for pdb_id, ids in small_ids.items()}
    assert (len(full_counts), sum(full_counts.values())) == (179, 2502)
    assert (len(small_counts), sum(small_counts.values())) == (77, 446)
    panels, legacy = [], {}
    for domain, condition in (("GT", "real_receptor"), ("CA2", "cryoatom2_receptor")):
        success_steps = {pdb_id: {} for pdb_id in full_counts}
        candidate_counts, charged_counts = {}, {}
        for pdb_id in full_counts:
            # False 在第二段; 并列 Find 分数以原 blob 编号升序, 不重排 selected 与 unselected 的整体优先级.
            candidates = sorted(full["predictions"][condition].get(pdb_id, []), key=lambda row: (not row["candidate_selected"], -row["source_probability_mean"], row["source_blob_index"]))
            candidate_counts[pdb_id] = charged_counts[pdb_id] = len(candidates)
            for attempt, candidate in enumerate(candidates, 1):
                if candidate["foreground_target"] and candidate["identity_supported"] and candidate["predicted_smiles"] == candidate["target_smiles"]:
                    # 同一实例的后续成功候选仍计费, 只不重复增加完成分子.
                    success_steps[pdb_id].setdefault(candidate["matched_occurrence_id"], attempt)
        old_counts = [sum(any(step <= k for step in steps.values()) for steps in success_steps.values()) for k in (1, 10)]
        assert old_counts == ({"GT": [142, 165], "CA2": [120, 157]}[domain])
        legacy[f"full_{domain}"] = {"K1": old_counts[0], "K10": old_counts[1]}
        panels.append(make_panel(f"full_{domain}", "full", domain, full_counts, success_steps, candidate_counts, charged_counts, None, None))

    for domain in ("GT", "CA2"):
        evaluation_path = FROZEN / domain / "evaluation.json"
        docking_path = FROZEN / domain / "docking_results.jsonl"
        source_paths.extend((evaluation_path, docking_path))
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        direct = [json.loads(line) for line in docking_path.read_text(encoding="utf-8").splitlines()]
        # (PDB, blob) 唯一定位一条已完成的 GPU 推理与 CPU 科学评价, 不重新选姿态.
        direct_lookup = {(row["pdb_id"], row["source_blob_index"]): row for row in direct}
        assert len(direct_lookup) == len(direct)
        assert set(evaluation["traces"]) == set(small_counts)
        candidate_counts = {pdb_id: len(trace) for pdb_id, trace in evaluation["traces"].items()}
        charged_counts = {pdb_id: max((row["attempt_index"] or 0 for row in trace), default=0) for pdb_id, trace in evaluation["traces"].items()}
        for pose_limit in (1, 50):
            for threshold in (2.0, 3.0):
                success_steps = {pdb_id: {} for pdb_id in small_counts}
                for pdb_id, trace in evaluation["traces"].items():
                    for candidate in trace:
                        if candidate["target_scope"] != "stage3_foreground" or not candidate["identity_correct"]:
                            continue
                        result = direct_lookup[(pdb_id, candidate["source_blob_index"])]
                        assert candidate["attempt_index"] == result["attempt_index"]
                        method = result["methods"]["local_cov-C"]
                        assert candidate["docking_stage"]["methods"]["local_cov-C"] == method
                        occurrence = candidate["matched_occurrence_id"]
                        assert occurrence in small_ids[pdb_id]
                        assert method["success"][str(threshold)][str(pose_limit)] == (method["pose_min_rmsd_A"][str(pose_limit)] < threshold)
                        if method["status"] == "success" and method["success"][str(threshold)][str(pose_limit)]:
                            success_steps[pdb_id].setdefault(occurrence, candidate["attempt_index"])
                old_counts = {}
                for k in (1, 10):
                    observed = sum(any(step <= k for step in steps.values()) for steps in success_steps.values())
                    expected = evaluation["summary"]["methods"]["local_cov-C"][str(k)][str(pose_limit)][str(threshold)]["success_count"]
                    assert observed == expected
                    old_counts[f"K{k}"] = observed
                panel_id = f"small_{domain}_pose{pose_limit}_rmsd{int(threshold)}"
                legacy[panel_id] = old_counts
                panels.append(make_panel(panel_id, "small", domain, small_counts, success_steps, candidate_counts, charged_counts, threshold, pose_limit))

    # 合成核查仅验证预算与去重规则, 不参与任何科学结果.
    synthetic = fixed_budget_records({"one": 1, "three": 3, "zero": 2}, {"one": {0: 1}, "three": {0: 1}, "zero": {}}, 50)
    assert synthetic[0]["attempt_budget"] == synthetic[0]["success_count"] == 0
    assert synthetic[1]["attempt_budget"] == synthetic[1]["success_count"] == 1
    assert synthetic[2]["success_count"] == 0
    exact_event = Fraction(1, 3)
    assert exact_event.numerator * 3 // exact_event.denominator == 1
    duplicate = {}
    for occurrence, step in ((7, 1), (7, 4), (8, 5)):
        duplicate.setdefault(occurrence, step)
    assert duplicate == {7: 1, 8: 5}
    for panel in panels:
        assert all(a <= b for a, b in zip(panel["curve"]["mean"], panel["curve"]["mean"][1:]))
        assert all(a <= b for a, b in zip(panel["curve"]["median"], panel["curve"]["median"][1:]))
        fractions = [Fraction(n, d) for n, d in zip(panel["curve"]["budget_numerator"], panel["curve"]["budget_denominator"])]
        for percentage, records in panel["distributions"].items():
            assert len(records) == panel["pdb_count"]
            assert all(0 <= row["success_count"] <= row["target_count"] for row in records)
            index = bisect.bisect_right(fractions, Fraction(int(percentage), 100)) - 1
            values = [row["completion"] for row in records]
            assert panel["curve"]["mean"][index] == statistics.mean(values)
            assert panel["curve"]["median"][index] == statistics.median(values)
    contract = {"relative_budget": "rho=K/N; fixed percentages use K=percentage*N//100", "completion": "distinct completed GT occurrences / all eligible GT occurrences within each PDB", "statistics": "PDB-equal macro mean and median", "candidate_order": "selected first, then unselected; each segment descending source_probability_mean, ascending source_blob_index on ties", "full_accounting": "every candidate charged once", "small_accounting": "reuse frozen match-aware-stage3-v2 attempt_index", "small_method": "PocketXMol-tuned single centre docking; original local_cov-C result key", "pose_ranking": "original self-ranking; best-of-50 is retrospective minimum RMSD", "threshold": "strict RMSD <2.0 or <3.0 Angstrom", "zero_candidate_pdb": "retained in denominator", "repeat_occurrence": "charged candidate retained; completion counted once at earliest success", "curve": "exact Fraction event budgets, right-continuous post-step; no smoothing or interpolation"}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "completion.json").write_text(json.dumps({"schema": "pdb-completion-v1", "contract": contract, "panels": panels}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    per_pdb_rows, summary_rows = [], []
    for panel in panels:
        tags = {key: panel[key] for key in ("scope", "domain", "threshold_A", "pose_limit")}
        for percentage, records in panel["distributions"].items():
            common = {"panel_id": panel["id"], **tags, "budget_percent": int(percentage)}
            per_pdb_rows.extend({**common, **record} for record in records)
            values = [row["completion"] for row in records]
            summary_rows.append({**common, "pdb_count": panel["pdb_count"], "occurrence_count": panel["occurrence_count"], "mean": statistics.mean(values), "median": statistics.median(values), "success_occurrence_count": sum(row["success_count"] for row in records), "zero_completion_pdb_count": sum(x == 0 for x in values), "full_completion_pdb_count": sum(x == 1 for x in values)})
    for filename, rows in (("per_pdb.csv", per_pdb_rows), ("summary.csv", summary_rows)):
        with (OUTPUT / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    sources = [{"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size} for path in source_paths]
    (OUTPUT / "source_manifest.json").write_text(json.dumps({"contract": contract, "sources": sources, "full_occurrence_inventory_provenance": {"source": metadata["source"], "sha256": metadata["sha256"]}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {"passed": True, "legacy_binary_success_counts": legacy, "full_denominator": {"pdb_count": 179, "occurrence_count": 2502}, "small_denominator": {"pdb_count": 77, "occurrence_count": 446}, "small_single_target_pdb_count": sum(count == 1 for count in small_counts.values()), "checks": ["zero-budget and singleton 50% remain zero", "integer percentage floors", "Fraction event floors", "duplicate occurrence counted once", "all PDB and occurrence denominators retained", "all legacy K1/K10 exact counts reproduced", "direct and embedded method results identical", "saved strict boolean equals saved RMSD threshold", "mean and median nondecreasing", "no model inference or RMSD recomputation"]}
    audit_dir = ROOT / "temp/e2e_completion_20261011"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "panel_count": len(panels), "per_pdb_rows": len(per_pdb_rows), "summary_rows": len(summary_rows), "legacy": legacy}, ensure_ascii=False))


if __name__ == "__main__":
    main()
