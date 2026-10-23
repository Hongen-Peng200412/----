"""从八份冻结 PocketXMol 逐实例评价及 Build 评价组装三张 Stage3 图的数据。

入口 ``main`` 读取本地只读副本, 核对完整测试的 446 个实例和 Find 命中的 243 个实例,
并写出 ``data.json``。每个 ``series`` 保留原实例编号、Top-1 / best RMSD 和输入状态;
``build`` 额外保留六个没有姿态的实例。RMSD 单位均为 Å。
"""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    """将 446 实例的八组对接结果与 243 实例的 Build 结果合并为绘图输入。

    ``--pocket-dir`` 内须有按 ``模型_受体_协议.json`` 命名的八份 ``occurrences.json`` 副本。
    ``--build-dir`` 内须有 ``build_occurrences.jsonl`` 和 ``pocket_comparison.json``。
    输出 ``--output`` 是 JSON 对象: ``series`` 为八组完整实例数组, ``build`` 为 243 个
    Find 命中实例, ``sources`` 为原始评价路径和 SHA-256, ``subset_keys`` 固定三组共同顺序。
    每个实例以 ``pdb_id`` 和 ``occurrence_id`` 对齐; 未能计算的 RMSD 使用 JSON null。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--pocket-dir", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # 这八组键分别确定受体输入、定位条件和冻结模型; C0 与 E 不交换定位信息。
    groups = [
        (model, receptor, protocol)
        for receptor in ("GT", "CA2")
        for protocol in ("C0", "E")
        for model in ("official", "local_cov")
    ]
    comparison_path = args.build_dir / "pocket_comparison.json"
    comparisons = json.loads(comparison_path.read_text(encoding="utf-8"))
    comparison_by_group = {
        (item["model"], item["receptor"], item["protocol"]): item
        for item in comparisons
    }
    series = []
    for model, receptor, protocol in groups:
        source_path = args.pocket_dir / f"{model}_{receptor}_{protocol}.json"
        source_bytes = source_path.read_bytes()
        source_rows = json.loads(source_bytes)
        comparison = comparison_by_group[(model, receptor, protocol)]

        # (446,), 每个元素为同一冻结测试实例的编号、两个 RMSD 和正式评价状态。
        rows = [
            {
                "pdb_id": row["pdb_id"],
                "occurrence_id": row["occurrence_id"],
                "top1": row["top1_rmsd_A"],
                "best": row["oracle_rmsd_A"],
                "status": row["evaluation_status"],
            }
            for row in source_rows
        ]
        keys = [(row["pdb_id"], row["occurrence_id"]) for row in rows]
        assert len(rows) == len(set(keys)) == 446
        by_key = dict(zip(keys, rows))
        for compared in comparison["occurrences"]:
            original = by_key[(compared["pdb_id"], compared["occurrence_id"])]
            assert compared["top1"] == original["top1"]
            assert compared["best"] == original["best"]

        series.append(
            {
                "model": model,
                "receptor": receptor,
                "protocol": protocol,
                "source": comparison["source"],
                "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
                "rows": rows,
            }
        )

    build_path = args.build_dir / "build_occurrences.jsonl"
    build_rows = [json.loads(line) for line in build_path.read_text(encoding="utf-8").splitlines()]
    build = [
        {
            "pdb_id": row["pdb_id"],
            "occurrence_id": row["occurrence_id"],
            "top1": row["top1_rmsd_A"],
            "best": row["oracle_rmsd_A"],
            "status": row["status"],
        }
        for row in build_rows
    ]
    subset_keys = [[row["pdb_id"], row["occurrence_id"]] for row in build]
    assert len(build) == len({tuple(key) for key in subset_keys}) == 243
    assert sum(row["status"] == "complete" for row in build) == 237
    for group in series:
        by_key = {(row["pdb_id"], row["occurrence_id"]): row for row in group["rows"]}
        assert all(tuple(key) in by_key for key in subset_keys)

    output = {
        "metric_unit": "Å",
        "full_count": 446,
        "subset_count": 243,
        "subset_keys": subset_keys,
        "series": series,
        "build": build,
        "build_source": str(build_path),
        "build_source_sha256": hashlib.sha256(build_path.read_bytes()).hexdigest(),
        "comparison_source_sha256": hashlib.sha256(comparison_path.read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
