"""按本图明确面板列表组装E2E科学输入, 不默认建立全阶段40面板."""

from pathlib import Path
from TOOLS.runtime.paths import load_module

HERE = Path(__file__).resolve().parent
COHORTS = load_module(HERE / "cohorts.py", "fig6_cohorts")
CONTROLLED = load_module(HERE / "controlled_inputs.py", "fig6_controlled")
ACTUAL = load_module(HERE / "actual_inputs.py", "fig6_actual")
COMPLETION = load_module(HERE / "completion.py", "fig6_completion")


# ================================================================================================
def prepare_panels(store, requested):
    """只返回requested具名面板, 每个面板保持完整目标、候选与失败.

    store: SourceStore, 本次原件供应. requested: tuple[str,...], 本图真实使用的完整面板ID, 如actual_CA2_pose5_rmsd3.0. 返回dict[ID,panel], 输入范围由full_*与find_full_*前缀决定是否需179-PDB, actual_*与find_match_small_*触发全身份计费, assume_*触发给定身份构象; 不计算未请求的pose或阈值.
    """
    with_full = any(pid.startswith(("full_", "find_full_")) for pid in requested)
    full_counts, members, identities = COHORTS.read_cohorts(store, with_full)
    small_counts = {p: len(ids) for p, ids in members.items()}
    domains = tuple(
        d
        for d in ("GT", "CA2")
        if any(
            pid in ("find_full_" + d, f"find_small_{d}_poseNone_rmsdNone") or pid.startswith("assume_" + d + "_")
            for pid in requested
        )
    )
    need_controlled_poses = any(pid.startswith("assume_") and "_Emap2lig_" not in pid for pid in requested)
    controlled = CONTROLLED.read_controlled(store, domains, with_full, need_controlled_poses)
    need_actual = any(pid.startswith(("actual_", "find_match_small_")) for pid in requested)
    need_full_match = any(pid.startswith("full_") for pid in requested)
    full = {}
    if need_actual or need_full_match:
        # 原件 /storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json, predictions.real_receptor/cryoatom2_receptor按PDB保留原blob、source_probability_mean和完整身份argmax. 真实键matched_occurrence_id, 预测键source_blob_index, 两者不能互换.
        # 原生产说明 /home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md; 本地 C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md.
        full = store.json("/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json")
    actual = ACTUAL.read_actual(store, full, identities) if need_actual else {}
    emap_ids = [pid for pid in requested if "Emap2lig" in pid]
    emap = {}
    if emap_ids:
        poses = tuple(sorted({int(pid.split("_pose")[1].split("_")[0]) for pid in emap_ids if "_pose" in pid}))
        thresholds = tuple(sorted({float(pid.split("_rmsd")[1]) for pid in emap_ids if "_rmsd" in pid}))
        emap = CONTROLLED.read_emap(store, full_counts, members, poses, thresholds)
    panels = {}
    for pid in requested:
        if pid.startswith("find_full_") and not pid.endswith("Emap2lig"):
            panels[pid] = controlled[pid.split("_")[-1]]["full"]
            continue
        if pid.startswith("find_small_"):
            domain = pid.split("_")[2]
            panels[pid] = controlled[domain]["small"]
            continue
        if pid.startswith("full_"):
            domain = pid.split("_")[1]
            condition = {"GT": "real_receptor", "CA2": "cryoatom2_receptor"}[domain]
            steps = {p: {} for p in full_counts}
            counts = {}
            for pdb in full_counts:
                candidates = sorted(
                    full["predictions"][condition].get(pdb, []),
                    key=lambda r: (not r["candidate_selected"], -r["source_probability_mean"], r["source_blob_index"]),
                )
                counts[pdb] = len(candidates)
                for rank, row in enumerate(candidates, 1):
                    if (
                        row["foreground_target"]
                        and row["identity_supported"]
                        and row["predicted_smiles"] == row["target_smiles"]
                    ):
                        steps[pdb].setdefault(row["matched_occurrence_id"], rank)
            panels[pid] = COMPLETION.make_panel(
                pid, "full", domain, full_counts, steps, sum(counts.values()), sum(counts.values()), None, None
            )
            continue
        if pid == "find_full_Emap2lig":
            count = sum(emap["all_counts"].values())
            panels[pid] = COMPLETION.make_panel(
                pid, "find_full", "Emap2lig", full_counts, emap["full_success"], count, count, None, None
            )
            continue
        domain = pid.split("_")[1] if not pid.startswith("find_match_small_") else pid.split("_")[-1]
        if pid.startswith("find_match_small_"):
            traces = actual[domain]["traces"]
            steps = {p: {} for p in small_counts}
            for pdb, trace in traces.items():
                for candidate in trace:
                    if candidate["target_scope"] == "stage3_foreground" and candidate["identity_correct"]:
                        steps[pdb].setdefault(candidate["matched_occurrence_id"], candidate["attempt_index"])
            raw_count = sum(map(len, traces.values()))
            charged = sum(max((c["attempt_index"] or 0 for c in trace), default=0) for trace in traces.values())
            panels[pid] = COMPLETION.make_panel(
                pid, "find_match_small", domain, small_counts, steps, raw_count, charged, None, None
            )
            continue
        pose = int(pid.split("_pose")[1].split("_")[0])
        threshold = float(pid.split("_rmsd")[1])
        steps = {p: {} for p in small_counts}
        if domain == "Emap2lig":
            steps = emap["pose_success"][pose, threshold]
            raw_count = sum(emap["raw_counts"].values())
            charged = sum(emap["charged_counts"].values())
            scope = "assume"
        elif pid.startswith("assume_"):
            detection = controlled[domain]["small"]
            first = {
                p: {r["occurrence_id"]: r["first_success_attempt"] for r in rows}
                for p, rows in detection["success_events"].items()
            }
            for row in controlled[domain]["direct"]:
                value = row["pose_min_rmsd_A"][str(pose)]
                assert row["success"][str(threshold)][str(pose)] == (value is not None and value < threshold)
                if row["status"] == "success" and value is not None and value < threshold:
                    steps[row["pdb_id"]][row["matched_occurrence_id"]] = first[row["pdb_id"]][
                        row["matched_occurrence_id"]
                    ]
            raw_count = detection["all_candidates_final"]["raw_candidate_count"]
            charged = detection["all_candidates_final"]["charged_attempt_count"]
            scope = "assume"
        else:
            traces = actual[domain]["traces"]
            direct = {(r["pdb_id"], r["source_blob_index"]): r for r in actual[domain]["direct"]}
            for pdb, trace in traces.items():
                for candidate in trace:
                    if candidate["target_scope"] != "stage3_foreground" or not candidate["identity_correct"]:
                        continue
                    result = direct[pdb, candidate["source_blob_index"]]
                    method = result["methods"]["local_cov-C"]
                    value = method["pose_min_rmsd_A"][str(pose)]
                    assert (
                        candidate["attempt_index"] == result["attempt_index"]
                        and method == candidate["docking_stage"]["methods"]["local_cov-C"]
                    )
                    assert method["success"][str(threshold)][str(pose)] == (value is not None and value < threshold)
                    if method["status"] == "success" and value is not None and value < threshold:
                        steps[pdb].setdefault(candidate["matched_occurrence_id"], candidate["attempt_index"])
            raw_count = sum(map(len, traces.values()))
            charged = sum(max((c["attempt_index"] or 0 for c in trace), default=0) for trace in traces.values())
            scope = "actual"
        panels[pid] = COMPLETION.make_panel(
            pid, scope, domain, small_counts, steps, raw_count, charged, threshold, pose
        )
    return panels
