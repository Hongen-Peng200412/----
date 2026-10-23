"""由冻结selected候选恢复Stage2新口径数据, 不触碰正式PPT或原稿.

aggregate() 读取output/stage2-results中的旧data.json、provenance/selected_predictions.json和保存的Matcher指标实现快照. 输出目录由--output指定, 保存当前data_忽视2+2例子.json、两种口径统计.json和aggregation_receipt.json; 默认在regenerated下, 不覆盖冻结输入.
"""
import argparse
import ast
import copy
import json
import sys
from pathlib import Path

import numpy as np

PROJECT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").is_file() and (parent / "论文草稿.md").is_file())
SOURCE = PROJECT / "画图/画图代码/stage2/output/stage2-results"


def aggregate(source_root: Path, output: Path, source: Path) -> None:
    """按已冻validation阈值排除不支持身份真前景, 保持其他所有科学字段.

    source_root保存旧data.json和provenance/selected_predictions.json; source为原Matcher/evaluation/metrics.py的只读完整副本. 从其AST仅提取foreground_counts和foreground_average_precision, 不加载模型. output写新绘图JSON、包含old/new/excluded的逐模型统计JSON及逻辑核对收据. 数据轴为模型×受体条件×selected候选, 每项通过pdb_id/source_blob_index/matched_occurrence_id定位.
    """
    work = source_root / "provenance"
    output.mkdir(parents=True, exist_ok=True)
    tree = ast.parse(source.read_text(encoding="utf-8"))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {"foreground_counts", "foreground_average_precision"}]
    namespace = {"np": np}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), namespace)
    counts = namespace["foreground_counts"]
    average_precision = namespace["foreground_average_precision"]
    frozen = json.loads((work / "selected_predictions.json").read_text(encoding="utf-8-sig"))
    data_path = source_root / "data.json"
    data_text = data_path.read_text(encoding="utf-8")
    data = json.loads(data_text)
    report = {"schema": "stage2_exclude_unparseable_v1", "default_profile": "new",
              "exclusion": "foreground_target and not identity_supported",
              "metric_implementation": str(source), "end_to_end_changed": False, "models": {}}
    excluded_by_condition = {}
    for model, record in frozen.items():
        result = {key: record[key] for key in ["source", "sha256", "threshold_source"]}
        result["conditions"] = {}
        for condition, panel in [("real_receptor", "real"), ("cryoatom2_receptor", "cryo")]:
            entry = record["conditions"][condition]
            old_rows = entry["rows"]
            excluded = [row for row in old_rows if row["foreground_target"] and not row["identity_supported"]]
            rows = [row for row in old_rows if not (row["foreground_target"] and not row["identity_supported"])]
            keys = {(row["pdb_id"], row["centered_box_index"], row["source_blob_index"], row["matched_occurrence_id"]) for row in excluded}
            assert len(excluded) == 2
            assert {key[0] for key in keys} == {"9ian", "9oq7"}
            if condition in excluded_by_condition:
                assert keys == excluded_by_condition[condition]
            excluded_by_condition[condition] = keys
            metrics = entry["metrics"]
            assert len(old_rows) == metrics["candidate_count"]
            threshold = metrics["foreground_threshold"]
            truth = np.array([row["foreground_target"] for row in old_rows])
            score = np.array([row["foreground_probability"] for row in old_rows])
            assert counts(truth, score, threshold) == metrics["foreground"]
            assert abs(average_precision(truth, score) - metrics["foreground_prauc"]) < 1e-14
            assert data["radar"][panel][model]["f1"] == [metrics["foreground"]["f1"], 1]
            supported = [row for row in rows if row["foreground_target"] and row["identity_supported"]]
            for category, saved in metrics["smiles_match"].items():
                group = supported if category == "overall" else [row for row in supported if row["target_category"] == category]
                assert len(group) == saved["eligible_count"]
                assert sum(row["identity_correct"] for row in group) == saved["correct_count"]
            new_metrics = copy.deepcopy(metrics)
            new_metrics["candidate_count"] = len(rows)
            truth = np.array([row["foreground_target"] for row in rows])
            score = np.array([row["foreground_probability"] for row in rows])
            new_metrics["foreground"] = counts(truth, score, threshold)
            new_metrics["foreground_prauc"] = average_precision(truth, score)
            # 原始报告中的不可解析列表不属于新统计范围; 另在 excluded 留存来源.
            new_metrics["unsupported_identity_target_candidate_count"] = 0
            new_metrics["unsupported_identity_targets"] = []
            assert sum(not row["foreground_target"] for row in rows) == (413 if panel == "real" else 489)
            assert len(rows) == (1651 if panel == "real" else 1649)
            data_text = data_text.replace(str(metrics["foreground"]["f1"]), str(new_metrics["foreground"]["f1"]), 1)
            result["conditions"][condition] = {"old": metrics, "new": new_metrics, "excluded": excluded}
            print(model, panel, "F1", f'{100*metrics["foreground"]["f1"]:.8f}', "->",
                  f'{100*new_metrics["foreground"]["f1"]:.8f}', "threshold", threshold)
        report["models"][model] = result
    new_data = json.loads(data_text)
    comparison = copy.deepcopy(new_data)
    for panel in ["real", "cryo"]:
        for model in frozen:
            comparison["radar"][panel][model]["f1"] = data["radar"][panel][model]["f1"]
    assert comparison == data
    (output / "data_忽视2+2例子.json").write_text(data_text, encoding="utf-8")
    (output / "两种口径统计.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "aggregation_receipt.json").write_text(json.dumps({"old_metrics_reproduced": True,
        "excluded_ids_equal_across_models": True, "matching_and_stratified_data_unchanged": True,
        "only_eight_f1_values_changed": True}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=SOURCE)
    parser.add_argument("--metric-source", type=Path, default=SOURCE / "source_code/matcher_metrics.py")
    parser.add_argument("--output", type=Path, default=SOURCE / "regenerated/aggregation")
    args = parser.parse_args()
    aggregate(args.source_root, args.output, args.metric_source)
