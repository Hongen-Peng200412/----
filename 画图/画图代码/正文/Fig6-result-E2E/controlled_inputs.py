"""读取给定正确身份的Find-Build原件和显式level Emap定位, 不混用实际Match姿态."""

from pathlib import Path
from TOOLS.runtime.paths import load_module

ROOT = Path(__file__).resolve().parents[4]
MATCHING = load_module(ROOT / "画图/画图代码/正文/Fig3-result-Find/matching.py", "fig3_find_matching")


def read_controlled(store, domains, with_full, with_poses):
    """为明确的GT/CA2条件取原Find面板和可选正确身份姿态.

    domains: tuple[str,...], 本次所需GT/CA2. with_full/with_poses: bool, 是否需要完整Find与正确身份姿态. 返回每域的small/full原Find面板、可选direct逐候选构象记录, 不返回其他旧面板也不重算其他图.
    """
    result = {}
    for domain in domains:
        # 原件 /storage/penghongen/Adaligand_E2E/test/test_0/evaluation/GT/completion.json 和 /storage/penghongen/Adaligand_E2E/test/test_0/evaluation/CA2/completion.json, panels内find_small_<域>_poseNone_rmsdNone保留77-PDB/446目标、首次定位计费号和候选总数; find_full_<域>保存179-PDB全配体定位.
        # 历史生产说明 /home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand/ligandseek_pipeline/README.md; 本地 C:/Users/15919/Desktop/AdaLigand/ligandseek_pipeline/README.md, 原CLI仍为测评数据代码/端到端测评/sh/run.sh.
        root = "/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/" + domain
        wanted = {"small": f"find_small_{domain}_poseNone_rmsdNone"}
        if with_full:
            wanted["full"] = "find_full_" + domain
        panels = {p["id"]: p for p in store.json(root + "/completion.json")["panels"]}
        block = {key: panels[pid] for key, pid in wanted.items()}
        if with_poses:
            # 原件 /storage/penghongen/Adaligand_E2E/test/test_0/evaluation/GT/docking_results.jsonl 和 /storage/penghongen/Adaligand_E2E/test/test_0/evaluation/CA2/docking_results.jsonl; 键pdb_id+matched_occurrence_id指原真实实例, pose_min_rmsd_A['1'/'5'/'50']是原排名前1/5/50姿态的最低RMSD Å, null不补成0, status为原成功或失败.
            block["direct"] = store.json(root + "/docking_results.jsonl")
        result[domain] = block
    return result


# ================================================================================================
def read_emap(store, full_counts, members, poses, thresholds):
    """只扫描当前范围所需原交集, 返回定位事件及明确请求的正确身份构象成功事件.

    full_counts: dict[PDB,int], 非空时需全配体定位, 否则只扫描members的77-PDB. members: dict[PDB,set[int]], 合格原实例. poses: tuple[int,...], 当前图实际使用的原排名数, 如(1,5), 空tuple不读取Build请求/构象. thresholds: tuple[float,...], 当前图严格RMSD阈值Å, 如(2.0,3.0). 返回full_success/small_success为PDB到原实例首次尝试映射, pose_success[(M,t)]为固定原Build请求对应的成功步, 并保留完整raw_counts/charged_counts.
    """
    root = "/storage/penghongen/Emap2lig/contour_level_20261026"
    request_by_key, build_by_key = {}, {}
    if poses:
        # 原件 /storage/penghongen/Emap2lig/contour_level_20261026/build/find_hit_subset.jsonl, pdb_id+occurrence_id声明真实实例, blob_id如11是实际Build请求blob, 不能把成功姿态挪到同实例更早的另一候选.
        # 原生产说明 /home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md; 本地 C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md.
        request_by_key = {
            (r["pdb_id"], r["occurrence_id"]): r for r in store.json(root + "/build/find_hit_subset.jsonl")
        }
        # 原件 /storage/penghongen/Emap2lig/contour_level_20261026/build/build_occurrences.jsonl, poses按原模型排名列出, top1_rmsd_A/top5_rmsd_A/oracle_rmsd_A分别取前1/5/50最低RMSD Å; null保留无姿态, 不按当前图RMSD重排.
        build_by_key = {
            (r["pdb_id"], r["occurrence_id"]): r for r in store.json(root + "/build/build_occurrences.jsonl")
        }
    pdbs = list(full_counts or members)
    paths = [root + "/find/held_out_test_0/evaluation/per_pdb/" + pdb + ".npz" for pdb in pdbs]
    for start in range(0, len(paths), 64):
        store.read_many(paths[start : start + 64])
    full_success = {p: {} for p in full_counts}
    small_success = {p: {} for p in members}
    pose_success = {(pose, t): {p: {} for p in members} for pose in poses for t in thresholds}
    all_counts, raw_counts, charged_counts = {}, {}, {}
    for pdb, path in zip(pdbs, paths):
        # 原件例 /storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/evaluation/per_pdb/9bjj.npz. intersections:int,(N_pred,N_gt), 交集体素数; pred_sizes/gt_sizes是完整两轴体素数; occurrence_id:(N_gt,)为原真实编号, 如1; source_blob_index:(N_pred,)为原blob编号, 如11, 不是轴下标.
        # candidate_selected:bool,(N_pred,), 原selected段; candidate_score:(N_pred,), 原评分. 候选先selected, 再评分降序、原blob编号升序; 归属唯一调用正文Fig3的双向0.3实现.
        a = store.npz(path)
        blob_ids, scores, selected = a["source_blob_index"], a["candidate_score"], a["candidate_selected"]
        order = sorted(range(len(blob_ids)), key=lambda i: (not selected[i], -scores[i], blob_ids[i]))
        if full_counts:
            all_counts[pdb] = len(order)
        if pdb in members:
            raw_counts[pdb] = len(order)
        charged = 0
        for rank, index in enumerate(order, 1):
            occurrence, *_ = MATCHING.target_from_intersections(
                a["occurrence_id"], a["intersections"][index], int(a["pred_sizes"][index]), a["gt_sizes"]
            )
            if full_counts and occurrence is not None:
                full_success[pdb].setdefault(occurrence, rank)
            if pdb not in members or (occurrence is not None and occurrence not in members[pdb]):
                continue
            charged += 1
            if occurrence is None:
                continue
            small_success[pdb].setdefault(occurrence, charged)
            if not poses:
                continue
            key = (pdb, occurrence)
            request = request_by_key.get(key)
            if request is None or int(blob_ids[index]) != request["blob_id"]:
                continue
            row = build_by_key[key]
            for pose, threshold in pose_success:
                field = {1: "top1_rmsd_A", 5: "top5_rmsd_A", 50: "oracle_rmsd_A"}[pose]
                value = row[field]
                if row["poses"]:
                    assert min(p["rmsd_A"] for p in row["poses"][:pose]) == value
                if value is not None and value < threshold:
                    pose_success[pose, threshold][pdb][occurrence] = charged
        if pdb in members:
            charged_counts[pdb] = charged
    return {
        "full_success": full_success,
        "small_success": small_success,
        "pose_success": pose_success,
        "all_counts": all_counts,
        "raw_counts": raw_counts,
        "charged_counts": charged_counts,
    }
