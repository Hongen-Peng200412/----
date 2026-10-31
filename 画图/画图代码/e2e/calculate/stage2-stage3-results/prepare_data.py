"""重建 Match–Build 合图及消融图的逐实例绘图输入。

本程序只读取本地冻结结果，不运行模型或重新评价候选。主图使用预测 blob
对应配体身份的三方交集；标准口袋消融保留完整 446 实例及缺失值。输出未截断
的连续 RMSD、准确率分子分母和分位统计，显示范围由绘图程序单独决定。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def read_json(path: Path):
    """读取一个 UTF-8 冻结 JSON；不搜索替代文件或猜测输入版本。"""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path):
    """读取一个 UTF-8 JSONL；每个对象保留原始身份与实验状态字段。"""
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def rmsd_statistics(values: list, denominator: int):
    """从完整有效 RMSD 计算分布；成功率始终使用传入的固定分母。

    values: list[float | None]，每个元素对应一项原始配体实例，单位 Å。
    denominator: int，完整评价集合的实例数；缺失值不贡献成功计数。
    """
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    assert np.isfinite(arr).all()
    quantiles = np.percentile(arr, [10, 25, 50, 75, 85])
    counts = {f"lt{threshold}": int(np.count_nonzero(arr < threshold)) for threshold in [1, 2, 3, 4]}
    return {
        "denominator": denominator,
        "valid_count": int(arr.size),
        "missing_count": denominator - int(arr.size),
        "q10": float(quantiles[0]),
        "q25": float(quantiles[1]),
        "median": float(quantiles[2]),
        "q75": float(quantiles[3]),
        "q85": float(quantiles[4]),
        "success_counts": counts,
        "success_pct": {key: count * 100 / denominator for key, count in counts.items()},
    }


# ================================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    frozen_dir = repo_root / "画图/画图代码/e2e/output/stage2-stage3-results"
    source_paths = {
        "match": "画图/画图代码/stage2/output/stage2-results/data_忽视2+2例子.json",
        "GT_predicted": "画图/画图代码/e2e/output/find-build-shared/sources/GT/docking_results.jsonl",
        "CA2_predicted": "画图/画图代码/e2e/output/find-build-shared/sources/CA2/docking_results.jsonl",
        "emap_prepared": "补充数据/Emap2lig_双条件/explicit_emdb_level/build/find_hit_subset.jsonl",
        "emap_build": "补充数据/Emap2lig_双条件/explicit_emdb_level/build/build_occurrences.jsonl",
    }

    # Match：保持原始评价支持集合，只改变展示轴，不因隐藏肽类改写 Overall。
    match_raw = read_json(repo_root / source_paths["match"])
    match = {"categories": {}, "by_candidate_count": {}, "ablation": {}, "foreground_f1": {}, "low_competition": {}}
    categories = ["overall", "small", "metal", "sugar"]
    model_names = {"strongest": "strongest-1", "voxel": "density_only-106", "density": "density_only-0", "pocket": "pocket_only-0"}
    for receptor, original_receptor in [("GT", "real"), ("CA2", "cryo")]:
        match["categories"][receptor] = {}
        match["ablation"][receptor] = {}
        for model, original_model in model_names.items():
            model_data = {}
            for category in categories:
                correct, total = match_raw["radar"][original_receptor][original_model][category]
                model_data[category] = {"correct": correct, "total": total, "accuracy_pct": correct * 100 / total}
            match["ablation"][receptor][model] = model_data
            if model == "strongest":
                match["categories"][receptor] = model_data
                match["foreground_f1"][receptor] = match_raw["radar"][original_receptor][original_model]["f1"][0]
        candidate_groups = match_raw["strongest_by_candidate_smiles_count"][original_receptor]
        overall_counts = np.sum(np.asarray(list(candidate_groups.values()), dtype=int), axis=0)
        curves = {}
        for category in categories:
            counts = overall_counts if category == "overall" else np.asarray(candidate_groups[category], dtype=int)
            curves[category] = {
                "correct": counts[:, 0].tolist(),
                "total": counts[:, 1].tolist(),
                "accuracy_pct": (counts[:, 0] * 100 / counts[:, 1]).tolist(),
            }
        match["by_candidate_count"][receptor] = curves
        low_count = int(overall_counts[:3, 1].sum())
        total_count = int(overall_counts[:, 1].sum())
        match["low_competition"][receptor] = {"candidate_smiles_max": 3, "supported_blobs": low_count, "total_supported_blobs": total_count, "fraction": low_count / total_count}
    match["candidate_group_labels"] = ["1", "2", "3", "4", "≥5"]

    # 主 Build：资格来自 Find 命中准备清单，而不是把被筛掉的 blob 算作建模失败。
    prepared = read_jsonl(repo_root / source_paths["emap_prepared"])
    emap_ready = {(item["pdb_id"], int(item["occurrence_id"])) for item in prepared if item["status"] == "ready" and 5 <= item["voxel_atom_ratio"] <= 25}
    assert len(emap_ready) == 251
    emap_rows = read_jsonl(repo_root / source_paths["emap_build"])
    emap_by_key = {(item["pdb_id"], int(item["occurrence_id"])): item for item in emap_rows if (item["pdb_id"], int(item["occurrence_id"])) in emap_ready}
    assert len(emap_by_key) == 251
    predicted = {}
    for receptor in ["GT", "CA2"]:
        records = read_jsonl(repo_root / source_paths[f"{receptor}_predicted"])
        predicted[receptor] = {(item["pdb_id"], int(item["matched_occurrence_id"])): item for item in records if item["matched_occurrence_id"] is not None and item["status"] == "success"}
        assert len(predicted[receptor]) == sum(item["matched_occurrence_id"] is not None and item["status"] == "success" for item in records)
    shared_keys = sorted(emap_ready & predicted["GT"].keys() & predicted["CA2"].keys())
    assert len(shared_keys) == 235
    main_build = {"keys": [list(key) for key in shared_keys], "denominator": 235, "pdb_count": len({key[0] for key in shared_keys}), "series": {}, "win_pct": {}}
    prepared_by_key = {(item["pdb_id"], int(item["occurrence_id"])): item for item in prepared}
    main_build["selected_blobs"] = {
        "GT": [predicted["GT"][key]["source_blob_index"] for key in shared_keys],
        "CA2": [predicted["CA2"][key]["source_blob_index"] for key in shared_keys],
        "Emap2lig": [prepared_by_key[key]["blob_id"] for key in shared_keys],
    }
    for method in ["Emap2lig", "CA2", "GT"]:
        series = {}
        for pose, raw_field, dg_field in [("top1", "top1_rmsd_A", "1"), ("top5", "top5_rmsd_A", "5"), ("best50", "oracle_rmsd_A", "50")]:
            values = [float(emap_by_key[key][raw_field]) if method == "Emap2lig" else float(predicted[method][key]["pose_min_rmsd_A"][dg_field]) for key in shared_keys]
            assert np.isfinite(values).all()
            series[pose] = values
        assert np.all(np.asarray(series["best50"]) <= np.asarray(series["top5"]))
        assert np.all(np.asarray(series["top5"]) <= np.asarray(series["top1"]))
        main_build["series"][method] = series
    for receptor in ["GT", "CA2"]:
        main_build["win_pct"][receptor] = {}
        for pose in ["top1", "top5", "best50"]:
            wins = np.asarray(main_build["series"][receptor][pose]) < np.asarray(main_build["series"]["Emap2lig"][pose])
            main_build["win_pct"][receptor][pose] = float(wins.mean() * 100)

    # 标准消融：所有条件使用同一 446 身份集合，失败值保留为 null。
    ablation = {"C0": {}, "E": {}}
    reference_keys = None
    for protocol in ["C0", "E"]:
        for receptor in ["GT", "CA2"]:
            ablation[protocol][receptor] = {}
            for model in ["official", "nodensity", "DG"]:
                if model == "nodensity":
                    source = frozen_dir / f"sources/nodensity/{receptor}_{protocol}.json"
                else:
                    original_model = "official" if model == "official" else "local_cov"
                    source = repo_root / f"画图/画图代码/stage3/output/stage3-official-tuned/frozen/{original_model}_{receptor}_{protocol}.json"
                source_paths[f"{model}_{receptor}_{protocol}"] = source.relative_to(repo_root).as_posix()
                records = read_json(source)
                by_key = {(item["pdb_id"], int(item["occurrence_id"])): item for item in records}
                keys = sorted(by_key)
                assert len(keys) == len(records) == 446
                if reference_keys is None:
                    reference_keys = keys
                assert keys == reference_keys
                series = {"keys": [list(key) for key in keys], "denominator": 446, "pdb_count": len({key[0] for key in keys})}
                for pose, raw_field in [("top1", "top1_rmsd_A"), ("top5", "top5_rmsd_A"), ("best50", "oracle_rmsd_A")]:
                    series[pose] = [by_key[key][raw_field] for key in keys]
                    assert all(value is None or np.isfinite(value) for value in series[pose])
                ablation[protocol][receptor][model] = series

    summary = {"main_build": {}, "ablation": {}, "match_low_competition": match["low_competition"], "main_win_pct": main_build["win_pct"]}
    for method, series in main_build["series"].items():
        summary["main_build"][method] = {pose: rmsd_statistics(series[pose], 235) for pose in ["top1", "top5", "best50"]}
    for protocol in ["C0", "E"]:
        summary["ablation"][protocol] = {}
        for receptor in ["GT", "CA2"]:
            summary["ablation"][protocol][receptor] = {}
            for model, series in ablation[protocol][receptor].items():
                summary["ablation"][protocol][receptor][model] = {pose: rmsd_statistics(series[pose], 446) for pose in ["top1", "top5", "best50"]}
    data = {
        "schema_version": 1,
        "source_paths": source_paths,
        "contract": {"rmsd_unit": "Å", "success_operator": "<", "main_blob_selection": "each pipeline's original selected predicted blob; join only by pdb_id and occurrence_id", "emap_build_eligibility": "bidirectional coverage >= 0.30 and inclusive voxel/heavy-atom ratio [5,25]", "main_denominator": 235, "ablation_denominator": 446, "top5": "minimum RMSD among the original ranked first five candidates", "best50": "minimum RMSD among all fifty candidates", "box_whisker_percentiles": [10, 85], "display_clipping_changes_statistics": False},
        "match": match,
        "main_build": main_build,
        "ablation": ablation,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, contents in [("data.json", data), ("summary.json", summary)]:
        (output_dir / name).write_text(json.dumps(contents, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Written {output_dir / 'data.json'} and {output_dir / 'summary.json'}")
