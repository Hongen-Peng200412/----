"""按旧实跑的原子映射与 RMSD 定义评价新条件 Build.

先读三个坐标工具, 再读 evaluate_one 和 run_evaluation. 24 个 CPU 进程生成 build_occurrences.jsonl、build_summary.json 以及保留全部 446 实例的 build_all_occurrences.jsonl; 原 consistency_iou 决定姿态排名, 真值只用于不做刚体对齐的 RMSD.
"""

import csv
import json
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from pathlib import Path

import gemmi
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolAlign

from emap2lig.data.types import LigandObject

from paths import INPUT_ROOT, RESULT_ROOT, TRUTH_COORDS


def load_truth(record: dict) -> tuple[Chem.Mol, np.ndarray]:
    """从精确 SMILES 和冻结坐标包构造同序重原子真值分子.

    输入参数:
        - record: dict, 通过 pdb_id 定位坐标包, occurrence_id 定位实例, prepared_smiles 核对原子身份, 如 9llg/0.
    返回值:
        - molecule: RDKit Mol, 从精确 SMILES 构造且移除氢的 N 原子分子.
        - xyz: float64, (N, 3), 与 molecule 原子轴对齐的 XYZ 世界坐标, 单位 Å.

    SMILE_coords/v1/<pdb_id>.npz 的 candidate_ids 为 (I,) 实例编号, prepared_smiles 为 (I,) 精确字符串, coord_offsets 为 (I+1,) 的坐标分段边界, coords 为 (总重原子数, 3) XYZ 世界坐标. 找到 candidate_ids[index]=occurrence_id 后用 coord_offsets[index:index+2] 切出该实例的 N 个重原子.
    """
    # 原冻结坐标包, 每个 PDB 一份; 本函数只读, 不把坐标送回 Build.
    with np.load(TRUTH_COORDS / f"{record['pdb_id']}.npz", allow_pickle=False) as asset:
        # 在坐标包的实例轴上寻找冻结 occurrence 编号, 不使用 Find 的 blob 编号索引真值.
        index = int(np.flatnonzero(asset["candidate_ids"] == record["occurrence_id"])[0])
        assert str(asset["prepared_smiles"][index]) == record["prepared_smiles"]
        # offsets 的两个端点同步切出该实例所有重原子, 首尾值分别为坐标包 0 和总原子数.
        start, stop = asset["coord_offsets"][index:index + 2]
        xyz = asset["coords"][start:stop].astype(np.float64)
    molecule = Chem.RemoveHs(Chem.MolFromSmiles(record["prepared_smiles"]))
    assert molecule.GetNumAtoms() == len(xyz)
    return molecule, xyz


def read_cif_xyz(path: Path, atom_names: list[str]) -> np.ndarray:
    """按 LigandObject.atom_names 顺序读取某个官方输出姿态的 CIF.

    输入参数:
        - path: Path, Build 写出的单个配体姿态 CIF, 不是沉积结构.
        - atom_names: list[str], 长度 N 的官方 LigandObject 重原子名顺序.
    返回值:
        - xyz: (N, 3), 按 atom_names 对齐的 XYZ 世界坐标, 单位 Å.
    """
    block = gemmi.cif.read_file(str(path)).sole_block()
    # 每行一个输出原子, 四列依次为原子名和 XYZ 世界坐标; 单位 Å.
    table = block.find(["_atom_site.label_atom_id", "_atom_site.Cartn_x",
                        "_atom_site.Cartn_y", "_atom_site.Cartn_z"])
    # 原子名 -> (3,) 世界坐标, 按官方 LigandObject 的名字恢复精确 SMILES 的原子轴.
    by_name = {row[0]: np.array([float(row[1]), float(row[2]), float(row[3])])
               for row in table}
    return np.stack([by_name[name] for name in atom_names])


def rmsd_without_alignment(molecule: Chem.Mol, predicted: np.ndarray,
                           truth: np.ndarray) -> tuple[float, bool]:
    """用 RDKit CalcRMS 计算对称原子映射下的最低 RMSD, 不做刚体对齐.

    predicted 和 truth 均为 (N, 3) XYZ 世界坐标, 单位 Å, 原子顺序与 molecule 一致.
    返回 (RMSD Å, 是否退回恒等映射); 沿用旧评价, CalcRMS 抛出 RuntimeError 时采用恒等映射并标记.
    """
    predicted_mol = deepcopy(molecule)
    truth_mol = deepcopy(molecule)
    for target, xyz in ((predicted_mol, predicted), (truth_mol, truth)):
        conformer = Chem.Conformer(target.GetNumAtoms())
        for index, point in enumerate(xyz):
            conformer.SetAtomPosition(index, point)
        target.AddConformer(conformer)
    try:
        return float(rdMolAlign.CalcRMS(predicted_mol, truth_mol, maxMatches=30000)), False
    except RuntimeError:
        identity = [[(index, index) for index in range(molecule.GetNumAtoms())]]
        return float(rdMolAlign.CalcRMS(predicted_mol, truth_mol, map=identity)), True


# ================================================================================================
def evaluate_one(item: tuple[dict, dict]) -> dict:
    """评价一条 Find 命中实例的 50 个姿态, 保留所有失败实例.

    输入参数 item 是 (record, build_status), 前者为 prepare_pdb 的请求, 后者为该实例最后一次尝试的状态; 只有 complete 才读取姿态, 筛选或采样失败不补造距离.
    返回字段:
    - pdb_id: str, PDB 结构编号.
    - occurrence_id: int, 冻结测试实例编号.
    - find_rank: int, 从 1 开始的 Find blob 排名.
    - status: str, complete 或 Build 筛选、采样、评价失败状态.
    - result_dir: str, 此次评价读取的独立 Build 产物目录绝对路径.
    - top1_rmsd_A: float | None, 原评分第一姿态的未对齐 RMSD, 单位 Å.
    - top5_rmsd_A: float | None, 原评分前五姿态的最低未对齐 RMSD, 单位 Å.
    - oracle_rmsd_A: float | None, 全部 50 姿态的最低未对齐 RMSD, 单位 Å.
    - poses: list[dict], 按 consistency_iou 降序排列的至多 50 个姿态字典.
    - poses[].rank: int, 原评分排序后从 1 开始的姿态排名.
    - poses[].consistency_iou: float, 官方 Build 的密度一致性评分.
    - poses[].cif: str, 该姿态 CIF 世界坐标文件的绝对路径.
    - poses[].rmsd_A: float | None, 未对齐 RMSD, 单位 Å; 评价失败时为 None.
    - poses[].identity_fallback: bool, RDKit 原子同构搜索失败后是否采用恒等原子映射.
    - poses[].error: str, 仅该姿态评价失败时存在的异常文字.
    - error: str | None, 失败状态可能存在的异常文字; 正常完成时不存在.
    """
    record, build_status = item
    pdb_id, occurrence_id, blob_id = (
        record["pdb_id"], record["occurrence_id"], record["blob_id"]
    )
    # 此实例最新尝试的目录; 缺少状态时仅构造预期位置, 不在这里生成或修复姿态.
    base = Path(build_status.get("result_dir", RESULT_ROOT / "build" / pdb_id /
                                 str(occurrence_id)))
    output = {"pdb_id": pdb_id, "occurrence_id": occurrence_id,
              "find_rank": record["find_rank"], "status": record["status"],
              "top1_rmsd_A": None, "top5_rmsd_A": None, "oracle_rmsd_A": None,
              "poses": [], "result_dir": str(base)}
    if record["status"] != "ready":
        return output
    if build_status.get("status") != "complete":
        output["status"] = build_status.get("status", "sampling_failed")
        output["error"] = build_status.get("error")
        return output
    blob_dir = base / "build_struct" / f"blob_{blob_id}"  # 当前原生 blob 的全部姿态目录.
    csv_path = blob_dir / f"blob_{blob_id}_results.csv"  # 决定姿态排名的原 consistency_iou 文件.
    if not csv_path.exists():
        output["status"] = "sampling_failed"
        return output
    with csv_path.open(encoding="utf-8", newline="") as handle:
        scores = list(csv.DictReader(handle))
    if len(scores) != 50:
        output["status"] = "sampling_failed"
        return output
    # 单次联合采样的 50 个姿态先按原 consistency_iou 排序, 再接触真值.
    scores.sort(key=lambda row: -float(row["consistency_iou"]))
    try:
        # 读取本次 SMILES 预处理的重原子名, 使 CIF 与坐标包的原子轴能够连接.
        ligand = LigandObject.load(base / "preprocess/ligands/LIG.npz")
        atom_names = [str(name) for name in ligand.atom_names]
        molecule, truth_xyz = load_truth(record)
    except Exception as error:
        output["status"] = "evaluation_input_failed"
        output["error"] = f"{type(error).__name__}: {error}"
        return output
    # 每个姿态保留评分、CIF 路径和 RMSD; 真实坐标不参与姿态排序.
    for rank, score in enumerate(scores, start=1):
        cif_path = blob_dir / f"{score['conformer_name']}.cif"  # 原评分当前行对应的同名世界坐标姿态.
        pose = {"rank": rank, "consistency_iou": float(score["consistency_iou"]),
                "cif": str(cif_path), "rmsd_A": None, "identity_fallback": False}
        try:
            predicted_xyz = read_cif_xyz(cif_path, atom_names)
            pose["rmsd_A"], pose["identity_fallback"] = rmsd_without_alignment(
                molecule, predicted_xyz, truth_xyz
            )
        except Exception as error:
            pose["error"] = f"{type(error).__name__}: {error}"
        output["poses"].append(pose)
    rmsds = [pose["rmsd_A"] for pose in output["poses"]]
    # Top-1 取原评分第一名; Top-5 和 best 分别取前五与全部 50 个姿态的最低 RMSD.
    output["top1_rmsd_A"] = rmsds[0]
    for key, selected in (("top5_rmsd_A", rmsds[:5]),
                          ("oracle_rmsd_A", rmsds)):
        valid = [value for value in selected if value is not None]
        output[key] = min(valid) if valid else None
    output["status"] = "complete" if all(value is not None for value in rmsds) else "pose_evaluation_failed"
    return output


def run_evaluation() -> None:
    """并行评价后按冻结顺序写出 build_occurrences.jsonl 和 build_summary.json.

    build_occurrences.jsonl 每行是 evaluate_one 返回的字典, 包含实例键、状态、Top-1/Top-5/best RMSD 与逐姿态 poses.
    build_all_occurrences.jsonl 每行字段同 evaluate_one, 未检出实例 status=find_miss, 其距离、排名、result_dir 为 None, poses 为空; 仍保留在 446 分母中.
    build_summary.json 的 denominator 是全部新 Find 命中实例, statuses 是状态字符串到实例数的映射, top1/top5/best_lt{2,3}A 是相应姿态预算下严格小于 2 Å 或 3 Å 的成功实例数.
    """
    # 新条件 Find 命中请求, 每个真实实例至多一个原生 blob.
    subset_path = RESULT_ROOT / "find_hit_subset.jsonl"
    records = [json.loads(line) for line in subset_path.read_text(encoding="utf-8").splitlines()]
    status_path = RESULT_ROOT / "build_status.jsonl"  # 新条件的追加尝试记录, 最后一条同实例记录决定本次评价输入.
    statuses = {}
    if status_path.exists():
        for line in status_path.read_text(encoding="utf-8").splitlines():
            status = json.loads(line)
            statuses[(status["pdb_id"], status["occurrence_id"])] = status
    # 每项为 (命中请求, 最新尝试状态), 与冻结请求顺序一致; 缺少尝试的实例保留失败.
    items = [(record, statuses.get((record["pdb_id"], record["occurrence_id"]), {}))
             for record in records]
    # 进程可乱序执行; map 按冻结 JSONL 顺序返回动态命中集合的实例评价.
    with ProcessPoolExecutor(max_workers=24) as pool:
        results = list(pool.map(evaluate_one, items))
    result_path = RESULT_ROOT / "build_occurrences.jsonl"  # 全部 Find 命中实例的逐姿态 RMSD, 包含 Build 失败.
    result_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n"
                                   for row in results), encoding="utf-8")
    summary = {"denominator": len(results), "statuses": {}}
    for status in sorted({row["status"] for row in results}):
        summary["statuses"][status] = sum(row["status"] == status for row in results)
    for label, field in (("top1", "top1_rmsd_A"), ("top5", "top5_rmsd_A"),
                         ("best", "oracle_rmsd_A")):
        for threshold in (2, 3):
            summary[f"{label}_lt{threshold}A"] = sum(
                row[field] is not None and row[field] < threshold for row in results
            )
    # 同时保存完整 446 实例的状态, 未检出不从后续端到端分母消失.
    frozen_path = INPUT_ROOT / "test.jsonl"  # 本轮冻结的全部测试身份, 不是只含 Find 命中的子集.
    frozen = [json.loads(line) for line in frozen_path.read_text(encoding="utf-8").splitlines()]
    # (PDB, 真值实例编号) -> 全部姿态评价, 不能以原生 blob 编号连接完整测试集.
    by_key = {(row["pdb_id"], row["occurrence_id"]): row for row in results}
    full_rows = []
    for item in frozen:
        key = (item["pdb_id"], int(item["candidate_id"]))
        full_rows.append(by_key.get(key, {
            "pdb_id": key[0], "occurrence_id": key[1], "find_rank": None,
            "status": "find_miss", "top1_rmsd_A": None, "top5_rmsd_A": None,
            "oracle_rmsd_A": None, "poses": [], "result_dir": None,
        }))
    (RESULT_ROOT / "build_all_occurrences.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in full_rows), encoding="utf-8")
    summary['full_test_denominator'] = len(full_rows)
    # 本条件的汇总指标; denominator 是 Find 命中集合, full_test_denominator 保留完整测试分母.
    (RESULT_ROOT / "build_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    run_evaluation()
