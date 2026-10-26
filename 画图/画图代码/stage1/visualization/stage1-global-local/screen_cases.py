"""筛查七个已有完整 map 的全局误报与局部预测，保留每个原生 blob 的身份。

从 sources.json 的冻结来源读取；输出目录由命令行指定，不接触稿件和 PPT。
真值与预测体素为全局 ZYX 整数索引，原子为 XYZ Å；体素中心为
origin_xyz + (index_xyz + 0.5) * voxel_size_xyz。受体距离使用沉积受体重原子，
1.5 Å 邻近比例仅描述空间形态。实例身份及 tau=0.3 的判定直接读冻结评价。
"""

from pathlib import Path
import argparse
import csv
import json

import numpy as np
from scipy.spatial import cKDTree


def spatial_features(voxels, corner_xyz, spacing_xyz, receptor_tree):
    """描述 (N,3) ZYX 体素中心到受体原子的距离；输出单位 Å 及邻近比例。"""
    xyz = corner_xyz + (voxels[:, ::-1] + 0.5) * spacing_xyz
    distances = receptor_tree.query(xyz, workers=1)[0]
    return {
        "receptor_min_A": float(distances.min()),
        "receptor_median_A": float(np.median(distances)),
        "receptor_within_1p5A_fraction": float(np.mean(distances <= 1.5)),
        "receptor_within_2A_fraction": float(np.mean(distances <= 2.0)),
        "centroid_xyz_A": xyz.mean(axis=0).tolist(),
    }


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
project = root.parents[4]
sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
args.output.mkdir(parents=True, exist_ok=True)
cases, flat_rows, local_pairs = [], [], []
current = json.loads((project / "画图/画图代码/stage1/output/stage1-main-sixpanel/v5/data/plot_data.json").read_text(encoding="utf-8"))["cohorts"]["full"]
cohort_checks = []

for pdb, relative_source in sources.items():
    source = project / relative_source
    with np.load(source / "data/exp.npz") as meta:
        corner = meta["origin"].astype(float)
        spacing = meta["voxel_size"].astype(float)
        contour = float(meta["contour_canonical"])
    shape = np.load(source / "data/exp.npy", mmap_mode="r").squeeze().shape
    with np.load(source / "data/receptor_tokens.npz") as tokens:
        tree = cKDTree(tokens["coords"][tokens["element"] != 1])
    occurrences = [json.loads(line) for line in (source / "data/occurrences.jsonl").read_text(encoding="utf-8").splitlines()]
    with np.load(source / "data/ligand_area.npz") as masks:
        gt_voxels = {int(o["candidate_id"]): masks[f'mask_{o["candidate_id"]}'] for o in occurrences}
    gt_flat = {i: np.ravel_multi_index(v.T, shape) for i, v in gt_voxels.items()}
    methods = {}

    for mode in ("cryo", "emap", "real"):
        with np.load(source / mode / "blobs.npz") as archive, np.load(source / mode / "evaluation.npz") as ev:
            ids = archive["source_blob_index" if mode == "emap" else "blob_index"]
            offsets, coordinates = archive["voxel_offsets"], archive["voxel_index_global_zyx"]
            threshold_row = int(np.flatnonzero(np.isclose(ev["coverage_thresholds"], 0.3))[0])
            selected_rows = np.flatnonzero(ev["candidate_selected"])
            match_start, match_end = ev["one_to_one_match_offsets"][threshold_row:threshold_row + 2]
            matched_rows = set(ev["one_to_one_match_pred_index"][match_start:match_end].tolist())
            stats = []
            for evaluation_row in selected_rows:
                blob_id = int(ev["source_blob_index"][evaluation_row])
                blob_row = int(np.flatnonzero(ids == blob_id)[0])
                start, end = offsets[blob_row:blob_row + 2]
                voxels = coordinates[start:end]
                intersections = ev["intersections"][evaluation_row]
                gt_ids = ev["occurrence_id"].astype(int)
                # 对全部选中候选核对体素与冻结交集，不重算评价或候选选择。
                flat = np.ravel_multi_index(voxels.T, shape)
                observed = np.array([len(np.intersect1d(flat, gt_flat[int(i)])) for i in gt_ids])
                np.testing.assert_array_equal(observed, intersections)
                assert len(voxels) == int(ev["pred_sizes"][evaluation_row])
                record = {
                    "pdb": pdb, "mode": mode, "blob_id": blob_id,
                    "evaluation_row": int(evaluation_row), "score": float(ev["candidate_score"][evaluation_row]),
                    "voxels": int(len(voxels)),
                    "compatible_tau0p3": bool(ev["coverage_pred_hit_mask"][threshold_row, evaluation_row]),
                    "instance_matched_tau0p3": int(evaluation_row) in matched_rows,
                    "truth_intersection_voxels_max": int(intersections.max()),
                    "intersections_by_occurrence": {str(i): int(n) for i, n in zip(gt_ids, intersections)},
                    **spatial_features(voxels, corner, spacing, tree),
                }
                stats.append(record)
                flat_rows.append({k: v for k, v in record.items() if k not in ("intersections_by_occurrence", "centroid_xyz_A")})
            methods[mode] = {
                "selected": len(stats), "compatible": sum(r["compatible_tau0p3"] for r in stats),
                "instance_tp": len(matched_rows), "instance_fp": len(stats) - len(matched_rows),
                "noncompatible": sum(not r["compatible_tau0p3"] for r in stats),
                "zero_intersection": sum(r["truth_intersection_voxels_max"] == 0 for r in stats),
                "far_noncompatible_min_over8A": sum(not r["compatible_tau0p3"] and r["receptor_min_A"] > 8 for r in stats),
                "blobs": stats,
            }
            current_row = current["ids"].index(pdb)
            current_name = {"cryo": "Cryo", "emap": "Emap", "real": "GT"}[mode]
            expected = current["models"][current_name]["values"]
            semantic_dice = 2 * float(ev["semantic_tp"]) / (2 * float(ev["semantic_tp"]) + float(ev["semantic_fp"]) + float(ev["semantic_fn"]))
            observed_values = {"precision": len(matched_rows) / len(stats), "recall": len(matched_rows) / len(occurrences), "dice": semantic_dice}
            for metric, value in observed_values.items():
                np.testing.assert_allclose(value, expected[metric][current_row], atol=1e-12, rtol=0)
            cohort_checks.append({"pdb": pdb, "mode": mode, **observed_values, "matches_current_full_cohort": True})

    for occurrence in occurrences:
        oid = int(occurrence["candidate_id"])
        truth_size = len(gt_voxels[oid])
        candidates = {}
        for mode in ("cryo", "emap", "real"):
            overlaps = []
            for blob in methods[mode]["blobs"]:
                intersection = blob["intersections_by_occurrence"][str(oid)]
                if intersection:
                    overlaps.append({**blob, "intersection": intersection,
                                     "precision": intersection / blob["voxels"],
                                     "recall": intersection / truth_size,
                                     "dice": 2 * intersection / (blob["voxels"] + truth_size)})
            candidates[mode] = sorted(overlaps, key=lambda r: r["dice"], reverse=True)[:3]
        local_pairs.append({"pdb": pdb, "occurrence": occurrence, "truth_voxels": truth_size,
                            "truth_spatial": spatial_features(gt_voxels[oid], corner, spacing, tree),
                            "candidates": candidates})

    case = {"pdb": pdb, "source": relative_source, "truth_instances": len(occurrences),
            "shape_zyx": list(shape), "corner_xyz_A": corner.tolist(), "spacing_xyz_A": spacing.tolist(),
            "contour": contour, "methods": methods}
    cases.append(case)
    print(pdb, "truth", len(occurrences), {m: {k:v for k,v in s.items() if k != "blobs"} for m,s in methods.items()}, flush=True)

(args.output / "screening.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
(args.output / "local_pairs.json").write_text(json.dumps(local_pairs, ensure_ascii=False, indent=2), encoding="utf-8")
(args.output / "cohort_verification.json").write_text(json.dumps(cohort_checks, ensure_ascii=False, indent=2), encoding="utf-8")
with (args.output / "selected_blobs.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
    writer.writeheader()
    writer.writerows(flat_rows)
