"""Fig5拥有Match与Build的科学读取, Fig9和补图3显式复用标准Build规则.

read_match按main/ablation只读本图必要模型; read_main_build读取235共同实例; read_standard_build只读调用者指定Centre或Envelope的六组446原始实例. 缺失、原排序、实例轴和分母保持服务器定义, 不训练或重评价模型.
"""

from collections import defaultdict
import numpy as np


def describe_rmsd(values, denominator):
    """计算未截断RMSD分位数与严格阈值成功率; 缺失不贡献成功但保留完整分母."""
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    quantiles = np.percentile(arr, [10, 25, 50, 75, 85])
    counts = {f"lt{t}": int(np.count_nonzero(arr < t)) for t in [1, 2, 3, 4]}
    return {
        "denominator": denominator,
        "valid_count": int(arr.size),
        "missing_count": denominator - int(arr.size),
        **dict(zip(["q10", "q25", "median", "q75", "q85"], map(float, quantiles))),
        "success_counts": counts,
        "success_pct": {k: v * 100 / denominator for k, v in counts.items()},
    }


def read_match(store, mode):
    """读取本图Match计数; mode为main类别及候选身份分组, 或ablation四变体雷达."""
    matcher = "/storage/penghongen/Matcher"
    model_names = {
        "strongest": "strongest-1",
        "voxel": "density_only-106",
        "density": "density_only-0",
        "pocket": "pocket_only-0",
    }
    categories = {"overall": "overall", "small": "small_molecule", "metal": "ion", "sugar": "sugar"}
    match = {
        "categories": {},
        "by_candidate_count": {},
        "ablation": {},
        "candidate_group_labels": ["1", "2", "3", "4", "≥5"],
    }
    if mode == "main":
        model_names = {"strongest": model_names["strongest"]}
    # /storage/penghongen/Matcher/evaluation/final_smiles/{strongest-1,density_only-106,density_only-0,pocket_only-0}/frozen_test.json: metrics按受体/类别保存correct_count与eligible_count, predictions按PDB保存候选选择/前景/身份支持及精确SMILES; 例9wup.
    # 生产说明: C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md; /home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md; 模型配置见C:/Users/15919/Desktop/Matcher/configs/experiments/final_smiles/README.md.
    frozen = {
        name: store.json(f"{matcher}/evaluation/final_smiles/{name}/frozen_test.json")
        for name in model_names.values()
    }
    for receptor, condition, folder in [
        ("GT", "real_receptor", "test0_real_smiles_v1"),
        ("CA2", "cryoatom2_receptor", "test0_cryoatom2_smiles_v1"),
    ]:
        match["ablation"][receptor] = {}
        for model, original in model_names.items():
            metrics = frozen[original]["metrics"][condition]["smiles_match"]
            match["ablation"][receptor][model] = {
                category: {
                    "correct": metrics[key]["correct_count"],
                    "total": metrics[key]["eligible_count"],
                    "accuracy_pct": metrics[key]["correct_count"]
                    * 100
                    / metrics[key]["eligible_count"],
                }
                for category, key in categories.items()
            }
        match["categories"][receptor] = match["ablation"][receptor]["strongest"]
        if mode == "ablation":
            continue
        # /storage/penghongen/Matcher/manifests/{test0_real_smiles_v1,test0_cryoatom2_smiles_v1}/manifest.json给出held_out_test_0.identities的原JSONL名; 行含pdb_id/smiles, 每PDB不同精确字符串数定义1/2/3/4/≥5分组, 不是候选构象数. 生产说明同上evaluation/README.md.
        manifest = store.json(f"{matcher}/manifests/{folder}/manifest.json")
        identities = store.json(
            f"{matcher}/manifests/{folder}/" + manifest["splits"]["held_out_test_0"]["identities"]
        )
        smiles = defaultdict(set)
        for row in identities:
            smiles[row["pdb_id"]].add(row["smiles"])
        grouped = {category: [[0, 0] for _ in range(5)] for category in categories}
        reverse = {value: key for key, value in categories.items() if key != "overall"}
        for pdb, candidates in frozen["strongest-1"]["predictions"][condition].items():
            column = min(5, len(smiles[pdb])) - 1
            for row in candidates:
                if (
                    row["candidate_selected"]
                    and row["foreground_target"]
                    and row["identity_supported"]
                ):
                    correct = int(row["predicted_smiles"] == row["target_smiles"])
                    for category in (
                        ("overall", reverse[row["target_category"]])
                        if row["target_category"] in reverse
                        else ("overall",)
                    ):
                        grouped[category][column][0] += correct
                        grouped[category][column][1] += 1
        match["by_candidate_count"][receptor] = {
            category: {
                "correct": [r[0] for r in counts],
                "total": [r[1] for r in counts],
                "accuracy_pct": [r[0] * 100 / r[1] if r[1] else 0.0 for r in counts],
            }
            for category, counts in grouped.items()
        }
    return match


def read_main_build(store):
    """按原实例键取235交集, GT/CA2/Emap2lig共用同一顺序与完整分母."""
    emap = "/storage/penghongen/Emap2lig/contour_level_20261026"
    # /storage/penghongen/Emap2lig/contour_level_20261026/build/find_hit_subset.jsonl: 原检出行含pdb_id/occurrence_id/status/voxel_atom_ratio/blob_id; 只取ready且体素/原子比5–25, 保留251成员. build_occurrences.jsonl含原Top1/5/all RMSD及poses原排名. 生产说明: C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md; 产生它的release为/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md, 实际入口与launch见trace.md.
    prepared = store.json(emap + "/build/find_hit_subset.jsonl")
    ready = {
        (r["pdb_id"], int(r["occurrence_id"]))
        for r in prepared
        if r["status"] == "ready" and 5 <= r["voxel_atom_ratio"] <= 25
    }
    emap_rows = {
        (r["pdb_id"], int(r["occurrence_id"])): r
        for r in store.json(emap + "/build/build_occurrences.jsonl")
        if (r["pdb_id"], int(r["occurrence_id"])) in ready
    }
    direct = {}
    for receptor in ["GT", "CA2"]:
        # /storage/penghongen/Adaligand_E2E/test/test_0/evaluation/{GT,CA2}/docking_results.jsonl: matched_occurrence_id/source_blob_index/status/pose_min_rmsd_A; '1'/'5'/'50'保持原排名前k最小值, 单位Å. 这是受控test0, 不是标准446或全身份端到端; 生产说明: /home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand/ligandseek_pipeline/README.md; 当前阅读说明C:/Users/15919/Desktop/AdaLigand/ligandseek_pipeline/README_Build.md, 历史命令见trace.md.
        rows = store.json(
            f"/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/{receptor}/docking_results.jsonl"
        )
        direct[receptor] = {
            (r["pdb_id"], int(r["matched_occurrence_id"])): r
            for r in rows
            if r["matched_occurrence_id"] is not None and r["status"] == "success"
        }
    keys = sorted(ready & direct["GT"].keys() & direct["CA2"].keys())
    assert len(keys) == 235 and len(ready) == len(emap_rows) == 251
    selected_emap = {(r["pdb_id"], int(r["occurrence_id"])): r for r in prepared}
    main = {
        "keys": [list(k) for k in keys],
        "denominator": len(keys),
        "pdb_count": len({k[0] for k in keys}),
        "series": {},
        "win_pct": {},
        "selected_blobs": {
            "GT": [direct["GT"][k]["source_blob_index"] for k in keys],
            "CA2": [direct["CA2"][k]["source_blob_index"] for k in keys],
            "Emap2lig": [selected_emap[k]["blob_id"] for k in keys],
        },
    }
    for method in ["Emap2lig", "CA2", "GT"]:
        main["series"][method] = {
            pose: [
                (
                    float(emap_rows[k][field])
                    if method == "Emap2lig"
                    else float(direct[method][k]["pose_min_rmsd_A"][rank])
                )
                for k in keys
            ]
            for pose, field, rank in [
                ("top1", "top1_rmsd_A", "1"),
                ("top5", "top5_rmsd_A", "5"),
                ("best50", "oracle_rmsd_A", "50"),
            ]
        }
    for receptor in ["GT", "CA2"]:
        main["win_pct"][receptor] = {
            pose: float(
                np.mean(
                    np.asarray(main["series"][receptor][pose])
                    < np.asarray(main["series"]["Emap2lig"][pose])
                )
                * 100
            )
            for pose in ["top1", "top5", "best50"]
        }

    return main


def read_standard_build(store, protocol):
    """只读取C0(Centre)或E(Envelope)的GT/CA2三模型六文件, 返回同轴原值."""
    ablation = {protocol: {}}
    all_keys = None
    for receptor in ["GT", "CA2"]:
        ablation[protocol][receptor] = {}
        for model in ["official", "nodensity", "DG"]:
            original = {
                "official": "official-SMILES",
                "nodensity": f'B-{ "C" if protocol == "C0" else "E" }-T0-RA-SMILES',
                "DG": f'local_cov-{ "C" if protocol == "C0" else "E" }-T0-RA',
            }[model]
            if receptor == "GT":
                remote = f"/storage/penghongen/PocketXMol/sampling/{original}/test/{protocol}/occurrences.json"
            else:
                original = {
                    "official": "official",
                    "nodensity": original,
                    "DG": f'local_cov-{ "C" if protocol == "C0" else "E" }',
                }[model]
                remote = f"/storage/penghongen/PocketXMol/final_evaluation/standard/ca2/{original}/test/{protocol}/occurrences.json"
            # /storage/penghongen/PocketXMol/sampling/{official-SMILES,B-C-T0-RA-SMILES,local_cov-C-T0-RA,B-E-T0-RA-SMILES,local_cov-E-T0-RA}/test/{C0,E}/occurrences.json为GT; /storage/penghongen/PocketXMol/final_evaluation/standard/ca2/{official,B-C-T0-RA-SMILES,local_cov-C,B-E-T0-RA-SMILES,local_cov-E}/test/{C0,E}/occurrences.json为CA2.
            # 每文件446实例行, (pdb_id,occurrence_id)为键, top1_rmsd_A/top5_rmsd_A/oracle_rmsd_A为原排序前1/5/50最小RMSD(Å), 缺失None仍留在446分母. 生产说明: C:/Users/15919/Desktop/PocketXMol/docking/README.md; /home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/docking/README.md和/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_9322032b81bd/PocketXMol/docking/README.md. 例9wup/2.
            rows = store.json(remote)
            by_key = {(r["pdb_id"], int(r["occurrence_id"])): r for r in rows}
            current = sorted(by_key)
            assert len(current) == len(rows) == 446
            if all_keys is None:
                all_keys = current
            assert current == all_keys
            ablation[protocol][receptor][model] = {
                "keys": [list(k) for k in current],
                "denominator": 446,
                "pdb_count": len({k[0] for k in current}),
                **{
                    pose: [by_key[k][field] for k in current]
                    for pose, field in [
                        ("top1", "top1_rmsd_A"),
                        ("top5", "top5_rmsd_A"),
                        ("best50", "oracle_rmsd_A"),
                    ]
                },
            }
    return ablation
