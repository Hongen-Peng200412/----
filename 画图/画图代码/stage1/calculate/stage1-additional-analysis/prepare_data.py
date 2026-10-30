"""从冻结评价补齐两种 level 条件的 0.5 P/R, 不运行模型或改写原结果.

从仓库根执行本脚本. 主流程先读取原有逐 PDB 指标, 再沿用固定类别归属与最大一对一匹配补算小分子 P/R, 最后保存绘图输入和逐 PDB CSV. 所有统计使用最终 selected 候选, 不改变 PRAUC 的分数扫描.
输出 conditions.json 是 dict, 顶层为 explicit_emdb_level/no_level; 各条件的 cohorts.full/small 保存固定 ids、逐方法 values、bars 和 distribution, 0.5 P/R 使用 precision05/recall05 字段.
source_data.csv 每行对应条件、范围、方法及 PDB, 七项指标为 dice/oto03/oto05/precision/recall/precision05/recall05, 均为 0-1 比例.
verification.json 是 dict, rows 为 CSV 行数, comparisons 保存12组条件/范围/方法的 PDB 数、原 0.3 最大复现误差和新 0.5 均值.
"""

import copy
import csv
import json
import os
from pathlib import Path
import sys

import numpy as np
from scipy.stats import gaussian_kde


if __name__ == "__main__":
    # root 是论文仓库; code 下保存各阶段的长期代码和冻结统计.
    root = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").is_file())
    code = root / "画图/画图代码"
    # original 保存原无 level 绘图统计、GT/CA2 评价与小分子交集来源清单.
    original = code / "stage1/output/stage1-main-sixpanel"
    # science 是原小分子一对一评价函数的长期位置; 归属与最大匹配只维护这一份实现.
    science = code / "stage1/calculate/stage1-main-sixpanel/science"
    sys.path.insert(0, str(science))
    from compute_small_pr import evaluate_selected
    # level_plot 保存显式 level 的现有指标; level_evaluation 保存同次实验原始交集和全配体评价.
    level_plot = code / "stage1/output/stage1-results-revision/explicit_emdb_level/data"
    level_evaluation = root / "补充数据/Emap2lig_双条件/explicit_emdb_level/find/held_out_test_0/evaluation"
    # 完整重建只写本次 build/data; 未指定构建目录时, 保存本组长期统计留档, 两套原始结果始终只读.
    output = Path(os.environ["FIGURE_BUILD_ROOT"]) / "data" if "FIGURE_BUILD_ROOT" in os.environ else code / "stage1/output/stage1-additional-analysis/data"
    output.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((original / "data/server_metrics_and_pr.json").read_text(encoding="utf-8"))
    receipt = json.loads((original / "evaluation_metadata/source_receipt.json").read_text(encoding="utf-8"))
    # occurrence_paths 按 PDB 指向原类别文件; facts_paths 按方法、PDB 指向候选 x 真实实例的交集 NPZ.
    occurrence_paths = {Path(row["local"]).stem: root / row["local"] for row in receipt["occurrences"]}
    facts_paths = {(row["model"], row["pdb_id"]): root / row["local"] for row in receipt["npz"]}
    sources = {"explicit_emdb_level": level_plot / "plot_data.json", "no_level": original / "v5/data/plot_data.json"}
    result = {}
    csv_rows = []
    checks = []
    for condition, source in sources.items():
        data = copy.deepcopy(json.loads(source.read_text(encoding="utf-8")))
        for cohort in ("full", "small"):
            block = data["cohorts"][cohort]
            for model in ("Emap", "Cryo", "GT"):
                values05 = []  # 最终为 (N_pdb, 2) 列表, 沿 block.ids 排列; 两列依次为 0.5 precision、recall.
                maximum_error = 0.0
                if cohort == "full":
                    full_rows = [json.loads(line) for line in (level_evaluation / "official_find_li.jsonl").read_text(encoding="utf-8").splitlines()] if condition == "explicit_emdb_level" and model == "Emap" else frozen["models"][model]["full_rows"]
                    by_pdb = {row["pdb_id"]: row for row in full_rows}
                    values05 = [[by_pdb[pdb]["one_to_one_macro_precision_0p5"], by_pdb[pdb]["one_to_one_macro_recall_0p5"]] for pdb in block["ids"]]
                    maximum_error = max(abs(by_pdb[pdb]["one_to_one_macro_" + metric + "_0p3"] - block["models"][model]["values"][metric][index]) for index, pdb in enumerate(block["ids"]) for metric in ("precision", "recall"))
                else:
                    for index, pdb in enumerate(block["ids"]):
                        # fact_path 是当前条件的原始交集; 类型文件始终来自同一冻结真实实例清单.
                        fact_path = level_evaluation / "per_pdb" / (pdb + ".npz") if condition == "explicit_emdb_level" and model == "Emap" else facts_paths[(model, pdb)]
                        types = {int(row["candidate_id"]): row["type_tag"] for row in [json.loads(line) for line in occurrence_paths[pdb].read_text(encoding="utf-8").splitlines() if line.strip()]}
                        with np.load(fact_path, allow_pickle=False) as archive:
                            # (N_pred, N_gt), 候选与全部类别真实实例的交集体素数; sizes 分别对齐两轴.
                            intersections = archive["intersections"]
                            pred_sizes, gt_sizes = archive["pred_sizes"], archive["gt_sizes"]
                            # (N_gt,), 原真实实例编号; selected 为 (N_pred,) 最终选择掩码.
                            occurrence_ids, selected = archive["occurrence_id"], archive["candidate_selected"].astype(bool)
                        gt_types = [types[int(item)] for item in occurrence_ids]
                        # 先复现原 0.3 结果, 再仅提高匹配阈值; 两次调用共享冻结候选与固定类别归属.
                        original_pr = evaluate_selected(intersections, pred_sizes, gt_sizes, occurrence_ids, gt_types, selected, 0.3)
                        strict_pr = evaluate_selected(intersections, pred_sizes, gt_sizes, occurrence_ids, gt_types, selected, 0.5)
                        maximum_error = max(maximum_error, abs(original_pr["one_to_one_precision_0p3"] - block["models"][model]["values"]["precision"][index]), abs(original_pr["one_to_one_recall_0p3"] - block["models"][model]["values"]["recall"][index]))
                        values05.append([strict_pr["one_to_one_precision_0p5"], strict_pr["one_to_one_recall_0p5"]])
                assert maximum_error < 1e-12, "原 0.3 P/R 必须逐 PDB 复现后才使用补算的 0.5 结果"
                model_data = block["models"][model]
                for metric, column in (("precision05", 0), ("recall05", 1)):
                    # (N_pdb,), 当前条件与方法的严格阈值指标, 对齐 block.ids 的固定顺序.
                    values = np.asarray(values05)[:, column]
                    model_data["values"][metric] = values.tolist()
                    grid = np.linspace(0, 1, 161)
                    # 在 0/1 两端反射 KDE, 保留所有取值为 0 或 1 的 PDB; 带宽沿用原图.
                    density = gaussian_kde(np.r_[values, -values, 2 - values], bw_method=data["kde_bandwidth"])(grid)
                    model_data["distribution"][metric] = {"grid": grid.tolist(), "density": (density / density.max()).tolist(), "quartiles": np.quantile(values, [0.25, 0.5, 0.75]).tolist()}
                for index, pdb in enumerate(block["ids"]):
                    csv_rows.append({"condition": condition, "cohort": cohort, "method": model, "pdb_id": pdb, **{metric: model_data["values"][metric][index] for metric in ("dice", "oto03", "oto05", "precision", "recall", "precision05", "recall05")}})
                checks.append({"condition": condition, "cohort": cohort, "method": model, "pdb_count": len(block["ids"]), "original_precision_recall_max_error": maximum_error, "precision05_mean": float(np.asarray(values05)[:, 0].mean()), "recall05_mean": float(np.asarray(values05)[:, 1].mean())})
        result[condition] = data
    (output / "conditions.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    with (output / "source_data.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    (output / "verification.json").write_text(json.dumps({"passed": True, "rows": len(csv_rows), "comparisons": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"两条件逐 PDB 统计已保存: {output}, {len(csv_rows)} rows")
