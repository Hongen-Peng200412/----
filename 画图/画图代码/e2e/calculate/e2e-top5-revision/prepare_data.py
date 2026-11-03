"""从冻结候选和原姿态评价准备 E2E 主图及三张 Find–Build 补图的同源输入.

入口 prepare_data 读取论文内的显式 level 比较、实际 Match 轨迹和原排名 RMSD, 不运行模型或坐标评价.
输出根由 FIGURE_BUILD_ROOT 指定, 未指定时为 temp/e2e_top5_20261102/build.
data/master.json 保存按稳定面板名索引的 panels、summaries 和统计 metadata; panels 内保留完整逐 PDB 分母、首次成功事件、精确预算阶梯和固定预算分布.
data/source_data.csv 每行对应一个面板、预算和 PDB, completion 为 0–1 比例; data/verification.json 保存旧事件复现及输入规模核对.
"""

import copy
import csv
import importlib.util
import json
import os
from pathlib import Path

import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
CODE = ROOT / "画图/画图代码"
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/e2e_top5_20261102/build"


def read_json(path):
    """读取一个 UTF-8 JSON 原件, 保留其字段和值."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    """逐行读取冻结评价; 返回顺序与源文件一致的记录列表."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


# ================================================================================================
def prepare_data(build):
    """组装同源输入并复现原 Top-1 / best-of-50, 只新增原排名 Top-5 与小分子 Find+Match 视图.

    输入参数:
        - build: Path, 本次可清空构建目录; 新 data 子目录全部在此生成.
    写出文件:
        - data/master.json: object, panels[panel_id] 为原面板及新增面板; summaries[panel_id]["100"] 含 mean、ci_low、ci_high、median, 单位百分比.
        - metadata: object, condition 固定 explicit_emdb_level, bootstrap_replicates=10000, bootstrap_seed=20261020; full_cohort 与 small_cohort 固定完整分母.
        - panels[panel_id].polyline: object, is_step=true, budget_percent 与 mean_percent 逐事件对齐; 原 curve 的 Fraction 分子分母同时保留.
        - data/source_data.csv: panel_id、budget_percent、pdb_id、target_count、attempt_budget、success_count、completion; 一行是一个 PDB 的一次固定预算观察.
        - data/verification.json: object, original_event_checks=20, 原成功事件及逐 PDB 分布必须完全相同; top5_reference_correction 明确原排名与计费号的区别.
    """
    (build / "data").mkdir(parents=True, exist_ok=True)
    shared_root = CODE / "e2e/output/find-build-shared"
    shared = read_json(shared_root / "explicit_emdb_level/data.json")
    assert shared["condition"] == "explicit_emdb_level"
    # 原 Stage1 全部小分子视图不进入本次主图; 本次建模分母固定为 77/446.
    panels = {p["id"]: copy.deepcopy(p) for p in shared["panels"] if p["scope"] != "find_stage1_small"}
    completed = read_json(CODE / "e2e/output/e2e-instance-completion/completion.json")
    panels.update({p["id"]: copy.deepcopy(p) for p in completed["panels"] if p["scope"] == "full"})
    reference = panels["find_small_GT_poseNone_rmsdNone"]
    # PDB -> 全部目标实例数, 包括零完成、未检出和没有有效姿态的实例.
    denominators = {r["pdb_id"]: r["target_count"] for r in reference["distributions"]["100"]}
    assert (len(denominators), sum(denominators.values())) == (77, 446)
    aggregate_path = CODE / "e2e/calculate/e2e-instance-completion/aggregate.py"
    specification = importlib.util.spec_from_file_location("e2e_frozen_completion_aggregate", aggregate_path)
    aggregate = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(aggregate)
    # 仅复用已有纯统计函数; 不调用 aggregate.main, 不写其原结果目录.
    make_panel = aggregate.make_panel
    additions = []
    old_checks = []
    for domain in ("GT", "CA2"):
        evaluation = read_json(CODE / f"e2e/output/e2e-accounting/{domain}/evaluation.json")
        docking = {(r["pdb_id"], r["source_blob_index"]): r for r in read_jsonl(CODE / f"e2e/output/e2e-accounting/{domain}/docking_results.jsonl")}
        assert set(evaluation["traces"]) == set(denominators)
        candidate_counts = {pdb: len(trace) for pdb, trace in evaluation["traces"].items()}
        charged_counts = {pdb: max((c["attempt_index"] or 0 for c in trace), default=0) for pdb, trace in evaluation["traces"].items()}
        find_match = {pdb: {} for pdb in denominators}
        for pdb, trace in evaluation["traces"].items():
            for candidate in trace:
                if candidate["target_scope"] == "stage3_foreground" and candidate["identity_correct"]:
                    find_match[pdb].setdefault(candidate["matched_occurrence_id"], candidate["attempt_index"])
        additions.append(make_panel(f"find_match_small_{domain}", "find_match_small", domain, denominators, find_match, candidate_counts, charged_counts, None, None))
        for pose in (1, 5, 50):
            for threshold in (2.0, 3.0):
                steps = {pdb: {} for pdb in denominators}
                for pdb, trace in evaluation["traces"].items():
                    for candidate in trace:
                        if candidate["target_scope"] != "stage3_foreground" or not candidate["identity_correct"]:
                            continue
                        result = docking[(pdb, candidate["source_blob_index"])]
                        method = result["methods"]["local_cov-C"]
                        value = method["pose_min_rmsd_A"][str(pose)]
                        assert candidate["attempt_index"] == result["attempt_index"]
                        assert method == candidate["docking_stage"]["methods"]["local_cov-C"]
                        assert method["success"][str(threshold)][str(pose)] == (value is not None and value < threshold)
                        if method["status"] == "success" and value is not None and value < threshold:
                            steps[pdb].setdefault(candidate["matched_occurrence_id"], candidate["attempt_index"])
                panel_id = f"actual_{domain}_pose{pose}_rmsd{threshold}"
                fresh = make_panel(panel_id, "actual", domain, denominators, steps, candidate_counts, charged_counts, threshold, pose)
                if pose == 5:
                    additions.append(fresh)
                else:
                    assert fresh["success_events"] == panels[panel_id]["success_events"]
                    assert fresh["distributions"] == panels[panel_id]["distributions"]
                    old_checks.append(panel_id)
        direct = {(r["pdb_id"], r["matched_occurrence_id"]): r for r in read_jsonl(shared_root / f"sources/{domain}/docking_results.jsonl")}
        detection = panels[f"find_small_{domain}_poseNone_rmsdNone"]
        first_detected = {pdb: {r["occurrence_id"]: r["first_success_attempt"] for r in events} for pdb, events in detection["success_events"].items()}
        assume_charged = {pdb: sum(c["target_scope"] != "non_stage3_foreground" for c in trace) for pdb, trace in evaluation["traces"].items()}
        for pose in (1, 5, 50):
            for threshold in (2.0, 3.0):
                steps = {pdb: {} for pdb in denominators}
                for (pdb, occurrence), result in direct.items():
                    value = result["pose_min_rmsd_A"][str(pose)]
                    assert result["success"][str(threshold)][str(pose)] == (value is not None and value < threshold)
                    if result["status"] == "success" and value is not None and value < threshold:
                        steps[pdb][occurrence] = first_detected[pdb][occurrence]
                panel_id = f"assume_{domain}_pose{pose}_rmsd{threshold}"
                fresh = make_panel(panel_id, "assume", domain, denominators, steps, candidate_counts, assume_charged, threshold, pose)
                if pose == 5:
                    # 不改变原候选总数和计费范围; 总计字段继承同一方法的原 Find-only 容器.
                    for field in ("raw_candidate_count", "charged_attempt_count"):
                        fresh["all_candidates_final"][field] = detection["all_candidates_final"][field]
                    additions.append(fresh)
                else:
                    assert fresh["success_events"] == panels[panel_id]["success_events"]
                    assert fresh["distributions"] == panels[panel_id]["distributions"]
                    old_checks.append(panel_id)
    emap_root = ROOT / "补充数据/Emap2lig_双条件/explicit_emdb_level/build"
    emap_rows = {(r["pdb_id"], r["occurrence_id"]): r for r in read_jsonl(emap_root / "build_occurrences.jsonl")}
    events = read_json(shared_root / "explicit_emdb_level/selected_blob_events.json")
    for row in emap_rows.values():
        if row["poses"]:
            for field, count in (("top1_rmsd_A", 1), ("top5_rmsd_A", 5), ("oracle_rmsd_A", 50)):
                assert min(p["rmsd_A"] for p in row["poses"][:count]) == row[field]
    emap_detection = panels["find_small_Emap2lig"]
    # 计数总数已由冻结 Find-only 面板完整保存; Top-5 不重新改变候选或免费跳过集合.
    zero_counts = dict.fromkeys(denominators, 0)
    correction = {}
    for pose, field in ((1, "top1_rmsd_A"), (5, "top5_rmsd_A"), (50, "oracle_rmsd_A")):
        for threshold in (2.0, 3.0):
            steps = {pdb: {} for pdb in denominators}
            wrong_steps = {pdb: {} for pdb in denominators}
            for event in events:
                pdb, occurrence = event["pdb_id"], event["occurrence_id"]
                value = emap_rows[(pdb, occurrence)][field]
                if value is not None and value < threshold:
                    steps[pdb][occurrence] = event["charged_attempt"]
                    wrong_steps[pdb][occurrence] = event["find_rank"]
            panel_id = f"assume_Emap2lig_pose{pose}_rmsd{threshold}"
            fresh = make_panel(panel_id, "assume", "Emap2lig", denominators, steps, zero_counts, zero_counts, threshold, pose)
            if pose == 5:
                for key in ("raw_candidate_count", "charged_attempt_count"):
                    fresh["all_candidates_final"][key] = emap_detection["all_candidates_final"][key]
                additions.append(fresh)
                correction[str(threshold)] = {"correct_percent": 100 * np.mean([r["completion"] for r in fresh["distributions"]["100"]]), "find_rank_percent": 100 * np.mean([r["completion"] for r in aggregate.fixed_budget_records(denominators, wrong_steps, 100)])}
            else:
                assert fresh["success_events"] == panels[panel_id]["success_events"]
                assert fresh["distributions"] == panels[panel_id]["distributions"]
                old_checks.append(panel_id)
    panels.update({p["id"]: p for p in additions})
    summaries, source_rows = {}, []
    bootstrap_indices = {n: np.random.default_rng(20261020).integers(0, n, size=(10000, n)) for n in (77, 179)}
    for panel_id, panel in panels.items():
        panel["polyline"] = {"is_step": True, "budget_percent": panel["curve"]["budget_percent"], "mean_percent": [100 * x for x in panel["curve"]["mean"]]}
        summaries[panel_id] = {}
        for budget, records in panel["distributions"].items():
            records = sorted(records, key=lambda row: row["pdb_id"])
            assert len(records) == panel["pdb_count"]
            assert sum(r["target_count"] for r in records) == panel["occurrence_count"]
            # (P,), 完整 PDB 轴上的完成百分比; 所有同范围方法共享 (10000,P) 重采样索引.
            values = np.array([r["completion"] for r in records]) * 100
            low, high = np.quantile(values[bootstrap_indices[len(records)]].mean(axis=1), [0.025, 0.975])
            summaries[panel_id][budget] = {"mean": float(values.mean()), "median": float(np.median(values)), "ci_low": float(low), "ci_high": float(high)}
            source_rows.extend({"panel_id": panel_id, "budget_percent": int(budget), **r} for r in records)
    metadata = {"condition": "explicit_emdb_level", "bootstrap_replicates": 10000, "bootstrap_seed": 20261020, "full_cohort": {"pdb_count": 179, "occurrence_count": 2502}, "small_cohort": {"pdb_count": 77, "occurrence_count": 446}, "ranking": "Original model ranking: minimum RMSD among first 1, 5 or 50 poses", "completion_unit": "PDB-equal mean of distinct successful instances / full eligible instances"}
    master = {"metadata": metadata, "panels": panels, "summaries": summaries}
    (build / "data/master.json").write_text(json.dumps(master, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (build / "data/source_data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]))
        writer.writeheader()
        writer.writerows(source_rows)
    verification = {"passed": True, "original_event_checks": len(old_checks), "original_panels_reproduced": old_checks, "emap_pose_records_checked": len(emap_rows), "top5_reference_correction": correction, "panel_count": len(panels), "source_rows": len(source_rows)}
    assert len(old_checks) == 20
    (build / "data/verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False))
    return master


if __name__ == "__main__":
    prepare_data(BUILD)
