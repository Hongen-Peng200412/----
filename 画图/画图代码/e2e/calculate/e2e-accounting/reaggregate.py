"""从冻结预测和构象指标重汇总 Match 感知的 Stage3 计费轨迹.

从论文仓库运行本文件. 全身份 argmax 来自完整 Matcher 测试, 类别来自冻结 identities.jsonl, Stage3 资格来自原候选清单. 本入口不加载模型、不读取或重算原子坐标.
新汇总保存到画图/画图代码/e2e/output/e2e-accounting/regenerated; 原始服务器文件从冻结根的 sources 独立副本只读. 每个输入域保存完整 evaluation.json 和原顺序 docking_results.jsonl, 并写出供原生 PowerPoint 制图使用的 plot_data.json.
"""

import copy
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
FROZEN = ROOT / "画图/画图代码/e2e/output/e2e-accounting"
OUTPUT = FROZEN / "regenerated"
SOURCES = FROZEN / "sources"
METHODS = ("official-C", "local_cov-C", "C-C", "C-C-E")
RULE = "match-aware-stage3-v2"


def read_jsonl(path):
    """读取一个冻结 JSONL 文件并保留物理记录顺序.

    输入参数:
        - path: Path, 每个非空行保存一条候选或 SMILES 身份记录的 UTF-8 文件.
    返回值:
        - records: list[dict], 与非空行逐项对齐, 不按分数或 PDB 重新排序.
    """
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, value):
    """把具有明确字段契约的汇总对象保存为 UTF-8 JSON.

    输入参数:
        - path: Path, 本轮正式结果目录内的目标文件路径.
        - value: dict 或 list, 调用方构造的完整对象; 数值和记录顺序原样保留.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def accounting_action(candidate, predicted_smiles, predicted_category):
    """按用户确认的真实归属与 Match 输出确定单个 blob 的计费动作.

    输入参数:
        - candidate: dict, target_scope 为 background/non_stage3_foreground/stage3_foreground, target_category 为原类别, target_smiles 为目标精确字符串.
        - predicted_smiles: str, 对当前 PDB 全身份范围取 argmax 后得到的精确 SMILES.
        - predicted_category: str, predicted_smiles 在冻结身份清单中的原类别, 如 small_molecule 或 ion.
    返回值:
        - action: str, charge_ 开头表示消耗一次, skip_ 开头表示免费跳过; Stage3 合格目标即使被预测成非小分子也计费.
    """
    if candidate["target_scope"] == "background":
        return "charge_background"
    if candidate["target_category"] != "small_molecule":
        return "charge_non_small_as_small" if predicted_category == "small_molecule" else "skip_non_small_prediction"
    if candidate["target_scope"] == "non_stage3_foreground":
        return "skip_correct_small_outside_stage3" if predicted_smiles == candidate["target_smiles"] else "charge_wrong_small_outside_stage3"
    return "charge_stage3"


def localization_diagnostic(traces):
    """假定身份匹配完全正确, 在完整冻结候选顺序上重建定位诊断.

    输入参数:
        - traces: dict[str,list[dict]], 同一组 77 个 PDB 的全候选序列; target_scope 为 background/non_stage3_foreground/stage3_foreground, raw_rank 是包含免费项的原始排名.
    返回值:
        - diagnostic: dict, 含 traces 和 hit_count; 不读取实际 Match 答案, 非 Stage3 前景一律免费.
            - traces: dict[str,list[dict]], 原始记录及顺序保留, attempt_index 为本定位诊断的计费号或 None, success 仅表示 Stage3 覆盖命中.
            - hit_count: list[int], 长度 20, 第 k 个值为前 k+1 次定位计费尝试命中的 PDB 数, 零候选 PDB 仍进入固定分母.
    """
    diagnostic_traces = {}
    for pdb, items in traces.items():
        spent = 0
        records = []
        for item in items:
            scope = item["target_scope"]
            if scope != "non_stage3_foreground":
                spent += 1
            records.append({**item, "attempt_index": spent if scope != "non_stage3_foreground" else None, "action": "skip_non_stage3_foreground" if scope == "non_stage3_foreground" else "charge_" + scope, "success": scope == "stage3_foreground"})
        diagnostic_traces[pdb] = records
    # 同一 PDB 在预算内有一次合格覆盖命中即成功; 不按命中 occurrence 数加权.
    counts = [sum(any(item["success"] and item["attempt_index"] <= limit for item in items) for items in diagnostic_traces.values()) for limit in range(1, 21)]
    return {"traces": diagnostic_traces, "hit_count": counts}


def summarize(traces, direct_results):
    """在实际 Match 感知计费轨迹上计算匹配及四种构象结果的逐 K 成功数.

    输入参数:
        - traces: dict[str,list[dict]], 固定 77 个 PDB 的完整候选序列; attempt_index 为计费编号或 None, target_scope 定义 Stage3 资格, success 表示身份正确.
        - direct_results: list[dict], 身份正确候选的冻结姿态指标; methods[method].success[threshold][pose_limit] 是原 self-ranking 后的成功布尔值.
    返回值:
        - summary: dict, pdb_count 为固定分母, find/match 暂保存实际轨迹的 K=1..20 计数; 调用方另将 find 替换为独立定位诊断, 并以 find_actual_accounting 保留原值.
        - summary.methods: dict, methods[method][K][M][threshold] 保存 success_count 与 success_rate, K 为计费尝试数, M 为原 self-ranking 前 M 个姿态, threshold 为严格 RMSD 阈值 2.0 或 3.0 Å.
    """
    # (pdb_id, source_blob_index) 唯一定位同一输入域的 blob; 不使用局部排名作为连接键.
    poses = {(record["pdb_id"], record["source_blob_index"]): record for record in direct_results}
    result = {"pdb_count": len(traces), "top_k": list(range(1, 21)), "find": [], "match": [], "methods": {method: {} for method in METHODS}}
    for limit in result["top_k"]:
        # 每个 PDB 保留独立候选列表, 零候选 PDB 的空列表仍进入分母.
        eligible = {
            pdb: [item for item in items if item["target_scope"] == "stage3_foreground" and item["attempt_index"] <= limit]
            for pdb, items in traces.items()
        }
        result["find"].append(sum(bool(items) for items in eligible.values()))
        result["match"].append(sum(any(item["success"] for item in items) for items in eligible.values()))
        for method in METHODS:
            result["methods"][method][str(limit)] = {}
            for pose_limit in (1, 5, 50):
                entry = {}
                for threshold in ("2.0", "3.0"):
                    hits = sum(
                        any(
                            item["success"] and (pdb, item["source_blob_index"]) in poses
                            and poses[(pdb, item["source_blob_index"])]["methods"][method]["success"].get(threshold, {}).get(str(pose_limit), False)
                            for item in items
                        )
                        for pdb, items in eligible.items()
                    )
                    entry[threshold] = {"success_count": hits, "success_rate": hits / len(traces)}
                result["methods"][method][str(limit)][str(pose_limit)] = entry
    return result


def reaggregate_domain(domain, condition, candidates, full_predictions, identities, small):
    """重建一个受体条件的轨迹, 复用原姿态指标并核对历史结果.

    输入参数:
        - domain: str, GT 或 CA2, 定位本轮 sources 中对应的冻结 docking 文件.
        - condition: str, real_receptor 或 cryoatom2_receptor, 定位 Matcher 的受体条件.
        - candidates: list[dict], 当前 77-PDB 候选清单, 保存真实类别和冻结 Stage3 归属.
        - full_predictions: dict[str,list[dict]], 完整测试的逐 PDB 预测, 每项 predicted_smiles 为全身份 argmax.
        - identities: dict[tuple[str,str],str], PDB 与精确 SMILES 到原类别的映射.
        - small: dict, 原小分子专用 evaluation.json, 提供完整候选顺序及有完整 logits 的重叠记录.
    返回值:
        - current: dict, 新 evaluation.json 对象, 含 accounting_rule、summary、traces.
        - comparison: dict, 新旧计费数、候选编号变化和逐 K 诊断计数, 供执行记录及审核使用.
    """
    candidate_by_key = {(item["pdb_id"], item["source_blob_index"]): item for item in candidates}
    predicted_by_key = {(pdb, item["source_blob_index"]): item for pdb, items in full_predictions.items() for item in items}
    small_by_key = {(item["pdb_id"], item["source_blob_index"]): item for item in small["predictions"][condition]}
    source_traces = small["traces"]["source_probability_mean"][condition]["small_molecule"]
    original = json.loads((SOURCES / f"{domain}.evaluation.json").read_text(encoding="utf-8"))
    direct_results = read_jsonl(SOURCES / f"{domain}.docking_results.jsonl")
    direct_by_key = {(item["pdb_id"], item["source_blob_index"]): item for item in direct_results}
    # 重叠 Stage3 候选复用同一个模型与身份轴, 完整测试和专用测试的全身份答案应一致.
    assert all(predicted_by_key[key]["predicted_smiles"] == item["predicted_smiles_all_ligand"] for key, item in small_by_key.items())
    actions = Counter()
    new_traces = {}
    newly_charged = []
    for pdb, items in source_traces.items():
        spent = 0
        new_items = []
        for item in items:
            key = (pdb, item["source_blob_index"])
            candidate, prediction = candidate_by_key[key], predicted_by_key[key]
            assert all(candidate[field] == prediction[field] for field in ("centered_box_index", "matched_occurrence_id", "target_smiles", "candidate_selected"))
            predicted_smiles = prediction["predicted_smiles"]
            predicted_category = identities[(pdb, predicted_smiles)]
            action = accounting_action(candidate, predicted_smiles, predicted_category)
            if action.startswith("charge_"):
                spent += 1
            attempt = spent if action.startswith("charge_") else None
            # identity_correct 仅比较精确字符串; success 进一步要求目标属于冻结 Stage3 范围.
            identity_correct = predicted_smiles == candidate["target_smiles"]
            success = candidate["target_scope"] == "stage3_foreground" and identity_correct
            docking = copy.deepcopy(original["traces"][pdb][len(new_items)]["docking_stage"])
            if key not in direct_by_key:
                docking = {"required": False, "reason": action}
            record = {
                **item, "previous_attempt_index": item["attempt_index"], "previous_action": item["action"],
                "attempt_index": attempt, "action": action, "candidate_selected": candidate["candidate_selected"],
                "target_category": candidate["target_category"], "predicted_smiles": predicted_smiles,
                "predicted_category": predicted_category, "identity_correct": identity_correct,
                "success": success, "docking_stage": docking,
            }
            if success:
                assert key in direct_by_key, f"冻结姿态未覆盖身份正确候选: {key}"
            if item["attempt_index"] is None and attempt is not None:
                newly_charged.append({"pdb_id": pdb, "source_blob_index": key[1], "raw_rank": item["raw_rank"], "action": action})
            actions[action] += 1
            new_items.append(record)
        new_traces[pdb] = new_items
    trace_by_key = {(pdb, item["source_blob_index"]): item for pdb, items in new_traces.items() for item in items}
    new_direct = []
    for original_record in direct_results:
        record = copy.deepcopy(original_record)
        trace = trace_by_key[(record["pdb_id"], record["source_blob_index"])]
        record["previous_attempt_index"] = record["attempt_index"]
        record["attempt_index"] = trace["attempt_index"]
        record["predicted_smiles"] = trace["predicted_smiles"]
        new_direct.append(record)
    old_summary, new_summary = summarize(source_traces, direct_results), summarize(new_traces, new_direct)
    # 从逐候选布尔值复算历史主表, 再与正式 evaluation.json 比较; 科学指标不重新计算.
    assert all(old_summary["methods"][method][k] == entries for method, table in original["summary"]["methods"].items() for k, entries in table.items())
    current = {
        "accounting_rule": RULE, "answer_scope": "all_ligand", "sorting": "source_probability_mean",
        "receptor_condition": condition, "model_name": "strongest-1", "summary": new_summary,
        "direct_result_file": str(OUTPUT / domain / "docking_results.jsonl"), "traces": new_traces,
    }
    (OUTPUT / domain).mkdir(parents=True, exist_ok=True)
    (OUTPUT / domain / "docking_results.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in new_direct), encoding="utf-8")
    comparison = {
        "candidate_count": len(candidates), "pdb_count": len(source_traces), "direct_count": len(new_direct),
        "old_free_count": sum(item["attempt_index"] is None for items in source_traces.values() for item in items),
        "new_free_count": sum(action_count for action, action_count in actions.items() if action.startswith("skip_")),
        "actions": dict(actions), "newly_charged": newly_charged,
        "changed_direct_attempt_count": sum(item["attempt_index"] != item["previous_attempt_index"] for item in new_direct),
        "docking_curves_unchanged": old_summary["methods"] == new_summary["methods"],
        "find_actual_accounting_old": old_summary["find"], "find_actual_accounting_new": new_summary["find"],
        "match_old": old_summary["match"], "match_new": new_summary["match"],
    }
    return current, comparison


def main():
    """依次重汇总 GT/CA2, 写出曲线源数据与完整审计记录.

    落盘文件:
        - GT/evaluation.json 与 CA2/evaluation.json: dict, 保存完整 77-PDB 新计费轨迹和四种方法的 K=1..20、pose@1/5/50、严格 2/3 Å 主表.
        - GT/docking_results.jsonl 与 CA2/docking_results.jsonl: 原顺序的候选记录, methods 原指标不变, 增加 previous_attempt_index 并更新 attempt_index.
        - comparison.json: dict, 保存两个输入域的新旧计费动作数、新增计费项及逐 K 诊断曲线.
        - plot_data.json: dict, full/small_find/small_match/build 对应正文原生 PPT 图的十个整数计数; small_find 包含同一定位诊断口径的 GT、CA2、Emap2lig-Find.
        - localization_diagnostics.json: dict, coverage_threshold、pdb_count 和 GT/CA2/emap2lig 的完整定位诊断轨迹及 K=1..20 成功数; 此文件不使用实际 Match 输出计费.
        - source_data.csv: 逐 K 计数表, domain、stage、method、pose_limit、threshold_A、K、success_count、pdb_count 定义每行的科学口径.
    """
    full = json.loads((SOURCES / "full_matcher.json").read_text(encoding="utf-8"))
    small = json.loads((SOURCES / "small_matcher.json").read_text(encoding="utf-8"))
    stage1 = json.loads((SOURCES / "stage1_only.json").read_text(encoding="utf-8"))
    identities = {(item["pdb_id"], item["smiles"]): item["type_tag"] for item in read_jsonl(SOURCES / "identities.jsonl")}
    plot = {"accounting_rule": RULE, "full": {name: curve["hit_count"][:10] for name, curve in full["curves"]["source_probability_mean"].items()}, "small_find": {}, "small_match": {}, "build": {}}
    diagnostics = {"protocol": "perfect-match-localization", "pdb_count": 77, "coverage_threshold": stage1["coverage_threshold"]}
    comparison, source_rows = {}, []
    for domain, condition, candidate_file in (("GT", "real_receptor", "real_candidates.jsonl"), ("CA2", "cryoatom2_receptor", "cryoatom2_candidates.jsonl")):
        current, comparison[domain] = reaggregate_domain(domain, condition, read_jsonl(SOURCES / candidate_file), full["predictions"][condition], identities, small)
        summary = current["summary"]
        diagnostics[domain] = localization_diagnostic(stage1["traces"]["source_probability_mean"][condition])
        assert set(diagnostics[domain]["traces"]) == set(current["traces"])
        assert all([item["source_blob_index"] for item in diagnostics[domain]["traces"][pdb]] == [item["source_blob_index"] for item in items] for pdb, items in current["traces"].items())
        assert diagnostics[domain]["hit_count"] == stage1["curves"]["source_probability_mean"][condition]["hit_count"]
        summary["find_actual_accounting"], summary["find"] = summary["find"], diagnostics[domain]["hit_count"]
        comparison[domain]["find_diagnostic"] = diagnostics[domain]["hit_count"]
        current["localization_diagnostic_rule"] = "perfect-match-localization"
        for pdb, items in current["traces"].items():
            for item, diagnostic in zip(items, diagnostics[domain]["traces"][pdb]):
                item["localization_attempt_index"] = diagnostic["attempt_index"]
        write_json(OUTPUT / domain / "evaluation.json", current)
        plot["small_find"][condition], plot["small_match"][condition] = summary["find"][:10], summary["match"][:10]
        plot["build"][domain] = {}
        for stage in ("find", "match"):
            source_rows.extend([domain, stage, "strongest-1", "", "", k, hits, 77] for k, hits in enumerate(summary[stage], 1))
        for method in METHODS:
            plot["build"][domain][method] = {}
            for pose in (1, 5, 50):
                for threshold in ("2.0", "3.0"):
                    counts = [summary["methods"][method][str(k)][str(pose)][threshold]["success_count"] for k in range(1, 21)]
                    plot["build"][domain][method][f"pose{pose}_lt{int(float(threshold))}"] = counts[:10]
                    source_rows.extend([domain, "build", method, pose, threshold, k, hits, 77] for k, hits in enumerate(counts, 1))
    diagnostics["emap2lig"] = localization_diagnostic(stage1["traces"]["emap2lig"])
    assert set(diagnostics["emap2lig"]["traces"]) == set(diagnostics["GT"]["traces"])
    assert diagnostics["emap2lig"]["hit_count"] == stage1["emap2lig"]["hit_count"]
    plot["small_find"]["emap2lig"] = diagnostics["emap2lig"]["hit_count"][:10]
    source_rows.extend(["density_only", "find", "emap2lig", "", "", k, hits, 77] for k, hits in enumerate(diagnostics["emap2lig"]["hit_count"], 1))
    for name, curve in full["curves"]["source_probability_mean"].items():
        source_rows.extend(["full_179", "match" if "matcher" in name else "find", name, "", "", k, hits, curve["pdb_count"]] for k, hits in enumerate(curve["hit_count"], 1))
    write_json(OUTPUT / "localization_diagnostics.json", diagnostics)
    write_json(OUTPUT / "plot_data.json", plot)
    write_json(OUTPUT / "comparison.json", comparison)
    with (OUTPUT / "source_data.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["domain", "stage", "method", "pose_limit", "threshold_A", "K", "success_count", "pdb_count"])
        writer.writerows(source_rows)
    print(json.dumps({domain: {key: value for key, value in values.items() if key not in ("find_actual_accounting_old", "find_actual_accounting_new", "find_diagnostic", "match_old", "match_new", "newly_charged")} for domain, values in comparison.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
