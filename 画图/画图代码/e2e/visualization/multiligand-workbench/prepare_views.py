"""为九例写材料索引与原生示范命令, 不渲染图像.

每例 views/*.cxc 操作已载入的本例模型, 不重新载入资产; 示例刻意设置显示样式, 日常编辑用交互手册.
全局相机共用 overview; 每例优先选择 100% 预算内首个 top-1<2 Å 的实例, 每种合格身份最多一个局部.
"""

import argparse
import csv
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
args = parser.parse_args()
index = []
for file in sorted(args.data_root.glob("*/scene.json")):
    scene = json.loads(file.read_text(encoding="utf-8"))
    folder = file.parent
    pdb = scene["pdb_id"]
    views = folder / "views"
    views.mkdir(exist_ok=True)
    fields = [
        "model_id",
        "key",
        "name",
        "kind",
        "condition",
        "blob_id",
        "occurrence_id",
        "reference_name",
        "reference_site",
        "pose",
        "sample_index",
        "sdf_index",
        "rmsd_A",
        "views",
        "file",
    ]
    with (folder / "对象索引.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for m in scene["models"]:
            occurrence = next(
                (o for o in scene["occurrences"] if o["candidate_id"] == m.get("occurrence_id")),
                None,
            )
            w.writerow(
                {
                    "model_id": "#" + m["id"],
                    "key": m["key"],
                    "name": m.get("display_name", m["key"]),
                    "kind": m["kind"],
                    "condition": m.get("domain", ""),
                    "blob_id": m.get("blob", ""),
                    "occurrence_id": m.get("occurrence_id", ""),
                    "reference_name": occurrence["display_name"] if occurrence else "",
                    "reference_site": occurrence["site"] if occurrence else "",
                    "pose": m.get("pose", ""),
                    "sample_index": m.get("sample_index", ""),
                    "sdf_index": m.get("sdf_index", ""),
                    "rmsd_A": m.get("rmsd_A", ""),
                    "views": "|".join(m.get("views", [])),
                    "file": m["file"],
                }
            )
    fields = [
        "condition",
        "blob_id",
        "blob_model",
        "rank",
        "probability_mean",
        "selected",
        "reference_instance",
        "reference_name",
        "reference_site",
        "foreground",
        "small",
        "eligible",
        "predicted_identity",
        "identity_correct",
        "full_attempt",
        "small_find_attempt",
        "find_build_attempt",
        "pipeline_attempt",
        "top1_model",
        "best_model",
    ]
    with (folder / "候选索引.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for domain, d in scene["domains"].items():
            for r in d["candidates"]:
                oid = r["matched_occurrence_id"]
                o = next((o for o in scene["occurrences"] if o["candidate_id"] == oid), None)
                poses = [
                    m
                    for m in scene["models"]
                    if m["kind"] == "pose"
                    and m["domain"] == domain
                    and m["blob"] == r["source_blob_index"]
                ]
                w.writerow(
                    {
                        "condition": domain,
                        "blob_id": r["source_blob_index"],
                        "blob_model": f'#{10 if domain=="CA2" else 11}.{r["source_blob_index"]+1}',
                        "rank": r["rank"],
                        "probability_mean": r["source_probability_mean"],
                        "selected": r["candidate_selected"],
                        "reference_instance": oid,
                        "reference_name": o["display_name"] if o else "",
                        "reference_site": o["site"] if o else "",
                        "foreground": r["foreground_target"],
                        "small": r["is_small"],
                        "eligible": r["is_eligible"],
                        "predicted_identity": r["predicted_name"],
                        "identity_correct": r["identity_correct"],
                        "full_attempt": r["attempts"]["find_match"],
                        "small_find_attempt": r["attempts"]["find_small"],
                        "find_build_attempt": r["attempts"]["find_build"],
                        "pipeline_attempt": r["attempts"]["pipeline"],
                        "top1_model": "|".join("#" + m["id"] for m in poses if m["pose"] == "top1"),
                        "best_model": "|".join("#" + m["id"] for m in poses if m["pose"] == "best"),
                    }
                )
    local = []
    seen = set()
    for r in scene["domains"]["CA2"]["candidates"]:
        if not (
            r["identity_correct"]
            and r["is_eligible"]
            and r["before"]["pipeline"] < scene["counts"]["eligible"]
        ):
            continue
        if r["target_smiles"] in seen:
            continue
        poses = [
            m
            for m in scene["models"]
            if m["kind"] == "pose"
            and m["domain"] == "CA2"
            and m["blob"] == r["source_blob_index"]
            and m["pose"] == "top1"
            and "pipeline" in m["views"]
        ]
        if poses and poses[0]["rmsd_A"] is not None and poses[0]["rmsd_A"] < 2:
            local.append(r["matched_occurrence_id"])
            seen.add(r["target_smiles"])
    if not local:
        local = [
            r["matched_occurrence_id"]
            for r in scene["domains"]["CA2"]["candidates"]
            if r["is_eligible"] and r["runs"]
        ][:1]
    local = local[:2]
    parameter = [
        f"# {pdb.upper()}：本例参数",
        "",
        f"全部配体 {scene['counts']['all']} 个，小分子 {scene['counts']['small']} 个，合格小分子 {scene['counts']['eligible']} 个。",
        "",
        "| 地图 | 模型编号 | 起始阈值 |",
        "|---|---|---|",
    ]
    for m in scene["models"]:
        if m["kind"] == "density":
            parameter.append(f"| {m['key']} | #{m['id']} | {m['level']:.10g} |")
    parameter += [
        "",
        "实验密度阈值来自原元数据；模拟密度起始阈值取固定稀疏抽样中正值的 85% 分位数，仅作为显示起点。三张地图使用同一世界坐标和网格。",
        "",
        "| 局部示例 | 实例编号 | 参考模型 | 聚焦命令 |",
        "|---|---|---|---|",
    ]
    for oid in local:
        o = next(o for o in scene["occurrences"] if o["candidate_id"] == oid)
        parameter.append(
            f"| {o['display_name']} {o['site']} | {oid} | #3.{oid+1} | `ligwork pocket {oid}` |"
        )
    parameter += [
        "",
        "完整对象编号见 `对象索引.csv`；候选与参考的对应见 `候选索引.csv`。空的计费号表示免费跳过；背景候选没有参考实例。",
        "",
        "## 100% 预算原评价",
        "",
        "| 条件 | Find+Match 完成数 | 完整流水线 top-1<2 Å 完成数 |",
        "|---|---|---|",
    ]
    for d in ["CA2", "GT"]:
        e = scene["domains"][d]["expected"]
        parameter.append(
            f"| {d} | {e['find_match']['100']['success_count']}/{scene['counts']['all']} | {e['pipeline']['100']['success_count']}/{scene['counts']['eligible']} |"
        )
    (folder / "本例参数.md").write_text("\n".join(parameter) + "\n", encoding="utf-8")
    for domain in ["CA2", "GT"]:
        receptor = "#1.2" if domain == "CA2" else "#1.1"
        bgroup = "#10" if domain == "CA2" else "#11"
        pgroup = "#20" if domain == "CA2" else "#21"
        common = [
            f"ligwork condition {domain}",
            "ligwork budget 100",
            "ligwork filter all",
            "ligwork pose top1",
            "ligwork labels identity off",
            "ligwork labels correctness off",
            "hide #1 models",
            f"show {receptor} models",
            "hide #1 atoms",
            f"cartoon {receptor}",
            f"color {receptor} #aab2bc",
            f"transparency {receptor} 20 target c",
            "show #3 models",
            "style #3 stick",
            "size #3 stickRadius 0.18",
            "color #3 #e69f00",
            "volume unzone #2.1",
            "volume #2.1 region all",
            "hide #2 models",
            "hide #!4 models",
            "graphics silhouettes false",
            "lighting soft",
            "lighting depthCue false",
            "ligwork overview",
        ]
        for task in ["find_match", "pipeline"]:
            cmd = [f"ligwork view {task}"] + common + ["ligwork reset"]
            for r in scene["domains"][domain]["candidates"]:
                model = f'{bgroup}.{r["source_blob_index"]+1}'
                color = "#009e73" if r["identity_correct"] else "#b56b47"
                cmd.append(f"color {model} {color}")
            cmd.append(f'transparency {bgroup} {25 if task=="find_match" else 85} target s')
            if task == "pipeline":
                for m in scene["models"]:
                    if m["kind"] == "pose" and m["domain"] == domain:
                        color = (
                            "#009e73" if m["rmsd_A"] is not None and m["rmsd_A"] < 2 else "#b56b47"
                        )
                        cmd.append(f'color #{m["id"]} {color}')
            name = f"{domain}_{task}"
            (views / (name + ".cxc")).write_text("\n".join(cmd) + "\n", encoding="utf-8")
            index.append(
                {
                    "pdb": pdb,
                    "view": name,
                    "command_file": str(views / (name + ".cxc")),
                    "image": str(folder / "exports" / (name + ".png")),
                }
            )
        for oid in local:
            cmd = [
                "ligwork overview",
                f"ligwork condition {domain}",
                "ligwork view pipeline",
                "ligwork budget 100",
                "ligwork filter eligible",
                "ligwork pose top1",
                "ligwork labels identity off",
                "ligwork labels correctness off",
                "ligwork reset",
                "hide #10|#11|#20|#21 models",
                "hide #3 models",
                f"show #3.{oid+1} models",
            ]
            pose = [
                m
                for m in scene["models"]
                if m["kind"] == "pose"
                and m["domain"] == domain
                and "pipeline" in m["views"]
                and m["pose"] == "top1"
                and any(
                    r["source_blob_index"] == m["blob"]
                    and r["matched_occurrence_id"] == oid
                    and r["before"]["pipeline"] < scene["counts"]["eligible"]
                    for r in scene["domains"][domain]["candidates"]
                )
            ]
            if pose:
                cmd.append(f'show #{pose[0]["id"]} models')
            cmd += [
                f"ligwork pocket {oid}",
                f"color {receptor} #bfc3c8",
                f"size {receptor} stickRadius 0.08",
                f"color #3.{oid+1} #e69f00",
                f"size #3.{oid+1} stickRadius 0.16",
                f"color {pgroup} #009e73",
                f"size {pgroup} stickRadius 0.18",
                f'volume #2.1 level {scene["contour"]:.10g}',
                "volume #2.1 meshLighting false",
                "color #2.1 #596773",
                "transparency #2.1 0 target s",
                "graphics silhouettes false",
                "lighting soft",
                "lighting depthCue false",
                "turn y 20",
                "turn x -15",
                "zoom 0.8",
            ]
            name = f"{domain}_local_{oid}"
            (views / (name + ".cxc")).write_text("\n".join(cmd) + "\n", encoding="utf-8")
            index.append(
                {
                    "pdb": pdb,
                    "view": name,
                    "occurrence_id": oid,
                    "prediction_model": pose[0]["id"] if pose else None,
                    "rmsd_A": pose[0]["rmsd_A"] if pose else None,
                    "command_file": str(views / (name + ".cxc")),
                    "image": str(folder / "exports" / (name + ".png")),
                }
            )
    scene["local_examples"] = local
    file.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
(args.data_root / "view_index.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    "native example views",
    len(index),
    "case indexes",
    len(list(args.data_root.glob("*/scene.json"))),
)
