"""汇总正文运行时间所用的冻结计时记录.

直接运行本文件并指定 --output. 输入来自 e2e/output/running-time-analysis,
以及既有 Stage 2、Stage 3 冻结原件. 本程序只重算描述统计, 不执行模型.
输出 JSON 的 find、build_h100、build_a800、emerald 包含 n、mean、median、
minimum、maximum、total 和 unit; match 保存批量总时间、候选数和摊销均值,
median 为 None, 表示没有逐候选独立计时. 字段与计时边界见同目录 README.md.
"""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import statistics


def describe(values, unit):
    """汇总同一计时单位的完整观测序列.

    values 是一维秒数或分钟数列表, 每项对应一次既有运行观测; 不在此筛选失败.
    unit 是输出单位, 如 s/map. 返回的 n 为观测数, mean、median、minimum、
    maximum、total 分别为均值、中位数、最小值、最大值和逐观测时间之和.
    total 是计时区间之和, 不表示并行作业从启动到结束的墙钟时间.
    """
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
        "total": sum(values),
        "unit": unit,
    }


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
arguments = parser.parse_args()
root = Path(__file__).resolve().parents[5]
evidence = root / "画图/画图代码/e2e/output/running-time-analysis"
stage2 = root / "画图/画图代码/stage2/output/stage2-results"
stage3 = root / "画图/画图代码/stage3/output/stage3-official-tuned/frozen"

# 每项对应一个 PDB 在一种受体条件下的两次模型前向, 原条件只用于来源定位.
find_records = json.loads((evidence / "find_per_map.json").read_text(encoding="utf-8"))
full_map_seconds = [item["performance"]["probability"]["wall_seconds"] for item in find_records]
centered_seconds = [item["performance"]["centered"]["wall_seconds"] for item in find_records]
find_seconds = [full + centered for full, centered in zip(full_map_seconds, centered_seconds)]
summary = {
    "schema": "ligandseek_runtime_summary_v1",
    "find": describe(find_seconds, "s/map"),
    "find_full_map": describe(full_map_seconds, "s/map"),
    "find_centered": describe(centered_seconds, "s/map"),
}
summary["find"]["unique_pdb_count"] = len({item["pdb_id"] for item in find_records})

# 每项对应一次标准 Centre 采样, sampling_seconds 包含实例预处理到候选写出.
for gpu, filename in [("h100", "local_cov_CA2_C0.json"), ("a800", "local_cov_GT_C0.json")]:
    records = json.loads((stage3 / filename).read_text(encoding="utf-8-sig"))
    summary[f"build_{gpu}"] = describe([item["sampling_seconds"] for item in records], "s/site")
    summary[f"build_{gpu}"]["sampling_statuses"] = dict(Counter(item["sampling_status"] for item in records))
    summary[f"build_{gpu}"]["pose_budgets"] = sorted({item["num_candidates"] for item in records})

launch = json.loads((stage2 / "provenance/runtime/launch.json").read_text(encoding="utf-8-sig"))
frozen_stat = json.loads((stage2 / "provenance/runtime/frozen_stat.json").read_text(encoding="utf-8-sig"))
finished = datetime.fromisoformat(frozen_stat["files"][0]["mtime_Asia_Shanghai"])
started = datetime.fromisoformat(launch["created_at"])
elapsed_seconds = (finished - started).total_seconds()
predictions = json.loads((stage2 / "frozen/strongest-1.json").read_text(encoding="utf-8-sig"))["predictions"]
candidate_count = sum(len(candidates) for condition in predictions.values() for candidates in condition.values())
summary["match"] = {
    "n": candidate_count,
    "elapsed_seconds": elapsed_seconds,
    "mean": elapsed_seconds / candidate_count,
    "median": None,
    "unit": "s/candidate_site",
}

# 714 次查询全部保留, 只对有有效评分且存在起止文件的查询计算条件耗时分布.
queries = json.loads((evidence / "emerald_queries.json").read_text(encoding="utf-8"))
emerald_minutes = [
    (item["result_source"]["mtime_ns"] - item["input_pdb_stat"]["mtime_ns"]) / 60_000_000_000
    for item in queries
    if item["result"]["status"] == "scored" and item["input_pdb_stat"] is not None
]
summary["emerald"] = describe(emerald_minutes, "min/site_query")
summary["emerald"]["all_query_count"] = len(queries)
summary["emerald"]["all_statuses"] = dict(Counter(item["result"]["status"] for item in queries))

arguments.output.parent.mkdir(parents=True, exist_ok=True)
arguments.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in summary.items() if key not in {"find_full_map", "find_centered"}}, ensure_ascii=False))
