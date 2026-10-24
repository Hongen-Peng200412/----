"""整理九例的冻结评价与下载清单, 不运行模型.

直接运行本文件, 先将当前论文已有的五种评价记录整理为 output/multiligand-workbench/catalog.json,
再在 --download 时调用 download.ps1 续传服务器原件. catalog.cases 每例包含 occurrences 真实实例、
domains[CA2/GT].candidates 原候选及逐模式计费号、runs 实际姿态来源、expected 冻结完成数.
计费号从 1 开始, null 表示免费跳过; before 表示到达该候选前已消耗的次数.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").exists())
CODE = Path(__file__).resolve().parent
OUTPUT = ROOT / "画图/画图代码/e2e/output/multiligand-workbench"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
parser.add_argument("--download", action="store_true")
parser.add_argument("--output-root", type=Path, default=OUTPUT, help="清单留档目录; 完整重建传入本次temp目录")
parser.add_argument(
    "--pdb", nargs="+", default=["9bjj", "11jb", "9lov", "9okp", "30ga", "9ujf", "9wup", "9lw1", "9llg"]
)
args = parser.parse_args()
OUTPUT = args.output_root
OUTPUT.mkdir(parents=True, exist_ok=True)
args.data_root.mkdir(parents=True, exist_ok=True)
plots = ROOT / "画图/画图代码"
full_path = plots / "e2e/output/e2e-accounting/sources/full_matcher.json"
full = json.loads(full_path.read_text(encoding="utf-8"))
identity_path = plots / "e2e/output/e2e-accounting/sources/identities.jsonl"
identities = [json.loads(s) for s in identity_path.read_text(encoding="utf-8").splitlines() if s]
all_panels = json.loads((plots / "e2e/output/find-build-shared/data.json").read_text(encoding="utf-8"))[
    "panels"
]
all_panels += json.loads(
    (plots / "e2e/output/e2e-instance-completion/completion.json").read_text(encoding="utf-8")
)["panels"]
panels = {p["id"]: p for p in all_panels}
catalog = {
    "schema": 1,
    "data_root": args.data_root.as_posix(),
    "cases": [],
    "evaluation_sources": [str(full_path), str(identity_path)],
}
catalog["experiment"] = {
    k: full[k] for k in ["checkpoint_path", "model_code_source", "status", "candidate_order"]
}
catalog["evaluation_sources"] += [
    str(plots / "e2e/output/find-build-shared/data.json"),
    str(plots / "e2e/output/e2e-instance-completion/completion.json"),
]
requests = []
for pdb in args.pdb:
    occurrences_path = plots / f"stage1/output/find-only-instance-completion/sources/occurrences/{pdb}.jsonl"
    occurrences = [json.loads(s) for s in occurrences_path.read_text(encoding="utf-8").splitlines() if s]
    catalog["evaluation_sources"].append(str(occurrences_path))
    eligible = {oid for i in identities if i["pdb_id"] == pdb for oid in i["stage3_occurrence_ids"]}
    small = {o["candidate_id"] for o in occurrences if o["type_tag"] == "small_molecule"}
    for o in occurrences:
        o["eligible"] = o["candidate_id"] in eligible
        o["display_name"] = "+".join(c["ccd_id"] for c in o["components"])
        o["site"] = "+".join(f"{c['auth_asym_id']}:{c['auth_seq_id']}" for c in o["components"])
    case = {
        "pdb_id": pdb,
        "occurrences": occurrences,
        "identities": [i for i in identities if i["pdb_id"] == pdb],
        "counts": {"all": len(occurrences), "small": len(small), "eligible": len(eligible)},
        "domains": {},
    }
    for remote, local in [
        (f"/storage/penghongen/AdaLigand/Ori_Data/density/{pdb}/exp.npy", f"{pdb}/source/exp.npy"),
        (f"/storage/penghongen/AdaLigand/Ori_Data/density/{pdb}/exp.npz", f"{pdb}/source/exp.npz"),
        (
            f"/storage/penghongen/AdaLigand/Ori_Data/density/{pdb}/ligand_area.npz",
            f"{pdb}/source/ligand_area.npz",
        ),
        (
            f"/storage/penghongen/AdaLigand/Ori_Data/parse/{pdb}/ligand_coords.npz",
            f"{pdb}/source/ligand_coords.npz",
        ),
        (
            f"/storage/penghongen/AdaLigand/Ori_Data/smiles_assets/SMILE_coords/v1/{pdb}.npz",
            f"{pdb}/source/smile_coords.npz",
        ),
    ]:
        requests.append({"remote": remote, "local": local})
    for key in sorted({o["object_key"] for o in occurrences}):
        name = re.sub(r"[^A-Za-z0-9_.-]+", "_", key) + ".npz"
        requests.append(
            {
                "remote": "/storage/penghongen/AdaLigand/Ori_Data/ligand_objects/" + name,
                "local": "templates/" + name,
            }
        )
    for domain, condition in [("CA2", "cryoatom2_receptor"), ("GT", "real_receptor")]:
        base = "/storage/penghongen/" + (
            "Adaligand_infered_receptor_data/cryoatom2/test_0_chain06/Ori_Data"
            if domain == "CA2"
            else "AdaLigand/Ori_Data"
        )
        blob_root = (
            "/storage/penghongen/AdaLigand_stage1_inference/Find_1/"
            + ("CryoAtom2受体" if domain == "CA2" else "真实受体")
            + "/artifacts/Find_1/held_out_test_0"
        )
        for remote, local in [
            (base + f"/density/{pdb}/sim.npy", f"{pdb}/source/{domain}_sim.npy"),
            (base + f"/density/{pdb}/sim.npz", f"{pdb}/source/{domain}_sim.npz"),
            (base + f"/parse/{pdb}/receptor_tokens.npz", f"{pdb}/source/{domain}_receptor.npz"),
            (blob_root + f"/{pdb}/blobs/F2_blobs.npz", f"{pdb}/source/{domain}_blobs.npz"),
        ]:
            requests.append({"remote": remote, "local": local})
        bank_file = plots / f"e2e/output/find-build-shared/sources/{domain}/docking_results.jsonl"
        bank = {
            r["source_blob_index"]: r
            for s in bank_file.read_text(encoding="utf-8").splitlines()
            if (r := json.loads(s))["pdb_id"] == pdb
        }
        actual_file = (
            ROOT / f"补充数据/Find-Match-Build_20261018/metadata/pipeline/{domain}/docking_results.jsonl"
        )
        actual = {
            r["source_blob_index"]: r
            for s in actual_file.read_text(encoding="utf-8").splitlines()
            if (r := json.loads(s))["pdb_id"] == pdb
        }
        evaluation_path = plots / f"e2e/output/e2e-accounting/{domain}/evaluation.json"
        catalog["evaluation_sources"] += [str(bank_file), str(actual_file), str(evaluation_path)]
        trace = {
            r["source_blob_index"]: r
            for r in json.loads(evaluation_path.read_text(encoding="utf-8"))["traces"][pdb]
        }
        candidates = sorted(
            full["predictions"][condition][pdb],
            key=lambda r: (
                not r["candidate_selected"],
                -r["source_probability_mean"],
                r["source_blob_index"],
            ),
        )
        charged = {"find_all": 0, "find_small": 0, "find_match": 0, "find_build": 0, "pipeline": 0}
        for rank, r in enumerate(candidates, 1):
            bid = r["source_blob_index"]
            oid = r["matched_occurrence_id"]
            r["rank"] = rank
            r["is_small"] = bool(r["foreground_target"] and oid in small)
            r["is_eligible"] = bool(r["foreground_target"] and oid in eligible)
            r["identity_correct"] = bool(
                r["foreground_target"]
                and r["identity_supported"]
                and r["predicted_smiles"] == r["target_smiles"]
            )
            r["attempts"] = {}
            r["before"] = {}
            for view in charged:
                r["before"][view] = charged[view]
                skip = (view == "find_small" and r["foreground_target"] and not r["is_small"]) or (
                    view == "find_build" and r["foreground_target"] and not r["is_eligible"]
                )
                if view == "pipeline":
                    skip = trace[bid]["attempt_index"] is None
                r["attempts"][view] = None if skip else charged[view] + 1
                if not skip:
                    charged[view] += 1
            if r["attempts"]["pipeline"] != trace[bid]["attempt_index"]:
                raise ValueError(f"{pdb}/{domain}/{bid}: 原计费号不一致")
            r["runs"] = []
            for role, record in [("find_build", bank.get(bid)), ("pipeline", actual.get(bid))]:
                if record is None:
                    continue
                # 共享姿态库也含给定真实身份的构象; 完整流水线只有 Match 正确才允许使用它.
                if role == "pipeline" and not (r["identity_correct"] and r["is_eligible"]):
                    continue
                same = next((x for x in r["runs"] if x["output_dir"] == record["output_dir"]), None)
                if same is not None:
                    same["views"].append(role)
                    continue
                run = {
                    **record,
                    "views": [role],
                    "local": f'{pdb}/source/{domain}/blob_{bid}/run_{len(r["runs"])}',
                }
                r["runs"].append(run)
                for name in [
                    "poses.sdf",
                    "ranking.json",
                    "evaluation_metrics.json",
                    "scientific_input.json",
                    "result.json",
                ]:
                    requests.append(
                        {"remote": record["output_dir"] + "/" + name, "local": run["local"] + "/" + name}
                    )
        view_panels = {
            "find_all": f"find_full_{domain}",
            "find_small": f"find_stage1_small_{domain}",
            "find_match": f"full_{domain}",
            "find_build": f"assume_{domain}_pose1_rmsd2.0",
            "pipeline": f"small_{domain}_pose1_rmsd2",
        }
        expected = {}
        for view, pid in view_panels.items():
            expected[view] = {
                budget: next(x for x in panels[pid]["distributions"][budget] if x["pdb_id"] == pdb)
                for budget in ["50", "100", "200", "300"]
            }
        brief_trace = [
            {
                k: r[k]
                for k in [
                    "source_blob_index",
                    "raw_rank",
                    "attempt_index",
                    "action",
                    "target_scope",
                    "identity_correct",
                    "matched_occurrence_id",
                ]
            }
            for r in trace.values()
        ]
        case["domains"][domain] = {"candidates": candidates, "expected": expected, "trace": brief_trace}
    catalog["cases"].append(case)
requests = list({r["local"]: r for r in requests}.values())
catalog["evaluation_sources"] = list(dict.fromkeys(catalog["evaluation_sources"]))
(OUTPUT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
(OUTPUT / "download_requests.json").write_text(
    json.dumps(requests, ensure_ascii=False, indent=2), encoding="utf-8"
)
(args.data_root / "catalog.json").write_text(
    json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f'{len(catalog["cases"])} cases; {len(requests)} server files', flush=True)
if args.download:
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(CODE / "download.ps1"),
            "-Manifest",
            str(OUTPUT / "download_requests.json"),
            "-DataRoot",
            str(args.data_root),
        ],
        check=True,
    )
