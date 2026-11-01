"""为九例写材料索引与原生示范命令, 不渲染图像.

每例 views/*.cxc 操作已载入的本例模型, 不重新载入资产; 示例刻意设置显示样式, 日常编辑用交互手册.
全局相机共用 overview; 每例优先选择 100% 预算内首个 top-1<2 Å 的实例, 每种合格身份最多一个局部.
"""

import argparse
import csv
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
args = parser.parse_args()
catalog = json.loads((args.data_root / "catalog.json").read_text(encoding="utf-8"))
project = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").exists())
# 1.0.8 catalog登记本次清单; 更早catalog使用当时固定output清单, 两条来源均不由日期猜测.
source_manifest = Path(catalog["download_manifest"]) if "download_manifest" in catalog else project / "画图/画图代码/e2e/output/multiligand-workbench/download_requests.json"
material_requests = json.loads(source_manifest.read_text(encoding="utf-8"))
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
        "pose_modes",
        "note",
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
                    "pose_modes": "|".join(m.get("pose_modes", [])),
                    "note": m.get("note", ""),
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
        "top5_model",
        "actual_build_status",
        "actual_build_failure",
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
                        "best_model": "|".join("#" + m["id"] for m in poses if "best" in m.get("pose_modes", [m["pose"]])),
                        "top5_model": "|".join("#" + m["id"] for m in poses if "top5" in m.get("pose_modes", [m["pose"]])),
                        "actual_build_status": r["actual_build"]["status"] if r.get("actual_build") is not None else "",
                        "actual_build_failure": r["actual_build"]["failure_reason"] if r.get("actual_build") is not None else "",
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
    templates = {"templates/" + re.sub(r"[^A-Za-z0-9_.-]+", "_", o["object_key"]) + ".npz" for o in scene["occurrences"]}
    materials = [r for r in material_requests if r["local"].startswith(pdb + "/") or r["local"] in templates]
    by_local = {r["local"]: r["remote"] for r in materials}
    with (folder / "本例材料来源.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["local_file", "relative_file", "original_server_file"])
        writer.writeheader()
        writer.writerows({"local_file": (args.data_root/r["local"]).as_posix(), "relative_file": r["local"], "original_server_file": r["remote"]} for r in materials)
    parameter += [
        "", "## 初始会话的材料与原始来源", "",
        "从本目录 initial.cxs 开始；load.cxc 从原材料重建本例。初始为CA2、Find+Match、100%、无过滤，参考结构与预测材料分组独立。", "",
        "[本例材料来源.csv](本例材料来源.csv)逐文件列出本地原件、相对路径和原始服务器文件，包括每个run的SDF、排名、指标、输入及状态；[对象索引.csv](对象索引.csv)连接实际模型编号，[候选索引.csv](候选索引.csv)连接blob、参考实例及预算，[poses.csv](poses.csv)连接每个显示构象的原sample_index和sdf_index。", "",
        "| 材料 | 本地原件 | 原始服务器文件 |", "|---|---|---|",
    ]
    for title, name in [("实验密度", "exp.npy"), ("实验网格与阈值", "exp.npz"), ("GT模拟密度", "GT_sim.npy"), ("CA2模拟密度", "CA2_sim.npy"), ("GT受体", "GT_receptor.npz"), ("CA2受体", "CA2_receptor.npz"), ("真实区域", "ligand_area.npz"), ("沉积坐标与present掩码", "ligand_coords.npz"), ("评价用SMILES顺序坐标", "smile_coords.npz"), ("GT完整blob", "GT_blobs.npz"), ("CA2完整blob", "CA2_blobs.npz")]:
        relative = pdb + "/source/" + name
        parameter.append(f"| {title} | `{(folder/'source'/name).as_posix()}` | `{by_local[relative]}` |")
    parameter += [
        "", "完整地图由上述NPY写为assets/maps/*.mrc，保留原体素值。GT为沉积受体，CA2为CryoAtom2重建受体，分别为#1.1/#1.2；实验/GT模拟/CA2模拟密度为#2.1/#2.2/#2.3。参考配体SDF由ligand_coords的实际present原子与模板生成，模板原件及服务器来源逐项见本例材料来源CSV；模板不等于预测构象。", "",
        "参考实例oid对应#3.(oid+1)，真实区域为#4.(oid+1)；CA2/GT原blob bid分别为#10.(bid+1)/#11.(bid+1)。CA2/GT构象根为#20/#21，其后依次为blob+1、run+1、姿态child；Top-1为child1，best为child2，Top-5为child3。sample_index是原50次采样编号，sdf_index是该SDF中的记录位置，两者不可互换。所有原子为世界XYZ、Å，不做额外叠合。", "",
        "ligand_coords.npz的coords_<oid>为(N,3)世界XYZ坐标，present_<oid>为对应模板原子的存在掩码；参考SDF只写出存在的原子。ligand_area.npz的mask_<oid>为(V,3)全图ZYX体素索引。GT/CA2_blobs.npz按blob_index查找bid，再由voxel_offsets切出voxel_index_global_zyx；blob编号不等于数组位置。模板以occurrences.object_key连接templates目录，例如CCD:ATP对应CCD_ATP.npz，完整模板文件名及原server文件在本例材料来源CSV中。", "",
        "给定正确身份和实际预测身份的run分开；错误身份不借用正确身份构象。原构象池及逐姿态RMSD只读复用；新增实际输出没有合法参考RMSD时，三个姿态档共用原模型Top-1并明确标注。失败请求保留blob/身份/状态而没有替代SDF。既有expected、计费与论文数值不因显示增加而改变。",
        "", "Find/Match的冻结预测与五模式评价来源见根目录[catalog.json](../catalog.json)的experiment、evaluation_sources和display_results_sources。统一服务器的Match原件为/storage/penghongen/Adaligand_E2E/test/test_0/match/all_ligand/{GT,CA2}/evaluation.json，GT/CA2分别读取real_receptor/cryoatom2_receptor条件；其PDB与source_blob_index连接本例blob。独立实际构建索引来自/storage/penghongen/Adaligand_E2E/actual_display_20261101/{GT,CA2}/display_results.jsonl，逐项保存输入SMILES、结果目录、原排名或失败原因。",
    ]
    if scene.get("deferred_models"):
        parameter += ["", "### 11JB模拟密度按需加载", "", "initial.cxs已载实验密度；两个完整模拟密度MRC原件仍在assets/maps/，仅延迟打开。scene.models保留其原编号与来源，scene.deferred_models明确登记两项。需要它们时执行下列官方命令；它不重新计算密度：", "", "```text", f"open {folder.as_posix()}/load_simulated_density.cxc", "```", "", "若内存允许一次载入全部地图，可从论文仓库运行prepare_assets.py --pdb 11jb --eager-simulated-maps，再按load.cxc重建；不覆盖个人另存会话。"]
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
