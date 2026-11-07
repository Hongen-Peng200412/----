"""从原服务器结构、原排名与密度生成9WUP当前病例的绘图数组.

prepare(store, output)只产生本次temp中的arrays.npz和metadata.json. 不读取旧PPT几何或旧D加工文件; 原排名首位由原occurrences.json选择, RMSD不参与重新选样.
"""

from io import BytesIO, StringIO
import json
from pathlib import Path

import numpy as np

from rdkit import Chem
from Bio.PDB.MMCIF2Dict import MMCIF2Dict


def prepare(store, output: Path):
    """恢复当前9WUP/FAD(A:1103)的53重原子及共享局部受体/密度.

    返回arrays和metadata, 同时写output/arrays.npz、metadata.json, 全部只供本次构建.
        - arrays.gt/official/tuned/build: 各为(53,3)世界XYZ/Å, 依次为真实、官方、DG、Emap2lig坐标.
        - arrays.element: (53,)原子序数, 与四份配体坐标同轴.
        - arrays.bonds: (B,3), 两端为该配体原子轴下标, 第三列为键阶.
        - arrays.receptor_xyz: (R_local,3)世界XYZ/Å, 保存原邻近受体原子.
        - arrays.receptor_element/receptor_res_index/receptor_atom_name: 各为(R_local,)原属性, 与局部受体坐标同轴.
        - arrays.receptor_bonds: (B_local,2)局部受体原子下标, 已从完整受体轴重映射.
        - arrays.density: (Z_local,Y_local,X_local)原体素值, 裁切后不重新采样.
        - arrays.origin/voxel_size: (3,)XYZ/Å, 为裁后网格边界与步长, 体素中心需加0.5个voxel.
        - arrays.contour: float, 原密度等值面标量.
        - metadata.pdb_id/occurrence_id/occurrence: 原PDB、真实实例编号及完整原实例记录.
        - metadata.metrics: dict, official/tuned各保存原sample_index及世界坐标RMSD.
        - metadata.build: dict, Emap原Top1记录, 不按真实RMSD重选.
        - metadata.sources: list[dict], 本次实际原件地址、摘要与大小.
        - metadata.density_slice_xyz: [low,high], 两个(3,)XYZ网格下标, 低端含、高端不含.
    """
    pdb, occurrence = "9wup", 2
    raw = "/storage/penghongen/AdaLigand/Ori_Data"
    pocket = "/storage/penghongen/PocketXMol"
    emap = "/storage/penghongen/Emap2lig/contour_level_20261026"
    # /storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl: 一行一个冻结实例, prepared_smiles定义重原子/键顺序; 本图只取pdb_id=9wup,candidate_id=2. 生产说明: C:/Users/15919/Desktop/PocketXMol/docking/README.md; /home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/docking/README.md.
    rec = next(
        r
        for r in store.json(pocket + "/data/smiles-v1/frozen/test.jsonl")
        if r["pdb_id"] == pdb and r["candidate_id"] == occurrence
    )
    mol = Chem.RemoveHs(Chem.MolFromSmiles(rec["prepared_smiles"]))
    # /storage/penghongen/AdaLigand/Ori_Data/smiles_assets/SMILE_coords/v1/9wup.npz: candidate_ids(K,),coord_offsets(K+1,),coords(sum_N,3)世界XYZÅ; offset切片取FAD A:1103的53重原子. 生产说明: C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/PocketXmol_compat/README.md及上述docking/README.md.
    reference = store.npz(raw + f"/smiles_assets/SMILE_coords/v1/{pdb}.npz")
    index = int(np.flatnonzero(reference["candidate_ids"] == occurrence)[0])
    start, stop = reference["coord_offsets"][index : index + 2]
    poses = {"gt": reference["coords"][start:stop]}
    metrics = {}
    for name, model in [("official", "official-SMILES"), ("tuned", "local_cov-C-T0-RA")]:
        folder = pocket + f"/sampling/{model}/test/C0"
        # /storage/penghongen/PocketXMol/sampling/{official-SMILES,local_cov-C-T0-RA}/test/C0/occurrences.json含实例原top1_sample_index及top1_rmsd_A; 对应/9wup/2/poses.sdf按sample_index选原首位, 不是按参考RMSD重挑. 原sample为official=22,DG=18; 生产说明同上述docking/README.md.
        row = next(
            r
            for r in store.json(folder + "/occurrences.json")
            if r["pdb_id"] == pdb and r["occurrence_id"] == occurrence
        )
        supplier = Chem.ForwardSDMolSupplier(
            BytesIO(store.read_bytes(folder + f"/{pdb}/{occurrence}/poses.sdf")), removeHs=False
        )
        pose = next(
            m
            for m in supplier
            if m is not None and m.GetIntProp("sample_index") == row["top1_sample_index"]
        )
        poses[name] = Chem.RemoveHs(pose).GetConformer().GetPositions()
        metrics[name] = {"sample_index": row["top1_sample_index"], "rmsd": row["top1_rmsd_A"]}
    # /storage/penghongen/Emap2lig/contour_level_20261026/build/build_occurrences.jsonl: 取9wup occurrence2的poses[0]及result_dir, 原评分Top1为blob_4_LIG_27.cif, 不改排名. 生产说明: C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md; 原release/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md.
    result = next(
        r
        for r in store.json(emap + "/build/build_occurrences.jsonl")
        if r["pdb_id"] == pdb and r["occurrence_id"] == occurrence
    )
    # /storage/penghongen/Emap2lig/contour_level_20261026/build/build/9wup/2/build_gate_job423330_20261026T202139_a2/preprocess/ligands/LIG.npz的atom_names为化学原子轴; 同launch/build_struct/blob_4/blob_4_LIG_27.cif的_atom_site.label_atom_id连接XYZÅ, 不按CIF行序猜测, 生产说明同上.
    ligand = store.npz(result["result_dir"] + "/preprocess/ligands/LIG.npz")
    cif = MMCIF2Dict(StringIO(store.read_bytes(result["poses"][0]["cif"]).decode("utf-8")))
    coordinates = {
        name: [
            float(cif[field][i])
            for field in ["_atom_site.Cartn_x", "_atom_site.Cartn_y", "_atom_site.Cartn_z"]
        ]
        for i, name in enumerate(cif["_atom_site.label_atom_id"])
    }
    poses["build"] = np.asarray([coordinates[name] for name in ligand["atom_names"].astype(str)])
    # /storage/penghongen/AdaLigand/Ori_Data/parse/9wup/receptor_tokens.npz: coords(R,3)XYZÅ, element/res_type/res_index/atom_name(R,),bond_index(2,B). 仅取res_type<28且距任一展示构象8Å内, 原键索引同步映射; 生产说明: C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/Ori_Data/README.md.
    receptor = store.npz(raw + f"/parse/{pdb}/receptor_tokens.npz")
    all_pose = np.concatenate(list(poses.values()))
    rc = receptor["coords"]
    keep = (receptor["res_type"] < 28) & (
        np.linalg.norm(rc[:, None, :] - all_pose[None, :, :], axis=2).min(axis=1) < 8
    )
    ids = np.flatnonzero(keep)
    # int(R_all,), 原完整受体原子下标映射到局部原子轴; -1表示不保留, ids给保留的原轴位置.
    mapping = np.full(len(rc), -1)
    mapping[ids] = np.arange(len(ids))
    bonds = receptor["bond_index"]
    bond_keep = keep[bonds].all(axis=0)
    arrays = {
        **poses,
        "element": np.asarray([atom.GetAtomicNum() for atom in mol.GetAtoms()]),
        "bonds": np.asarray(
            [
                [bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), bond.GetBondTypeAsDouble()]
                for bond in mol.GetBonds()
            ]
        ),
        "receptor_xyz": rc[keep],
        "receptor_element": receptor["element"][keep],
        # int(B_local,2), 两端均保留的键已转为receptor_xyz的局部原子下标.
        "receptor_bonds": mapping[bonds[:, bond_keep]].T,
        "receptor_res_index": receptor["res_index"][keep],
        "receptor_atom_name": receptor["atom_name"][keep],
    }
    # /storage/penghongen/AdaLigand/Ori_Data/density/9wup/exp.npz给origin/voxel_size(3,)XYZÅ及contour_canonical; 同目录exp.npy原密度squeeze后为ZYX. 只裁全部展示构象±9Å, 不改像素值或阈值, 生产说明同上述Ori_Data/README.md和docking/README.md.
    density_meta = store.npz(raw + f"/density/{pdb}/exp.npz")
    density = np.load(store.local_file(raw + f"/density/{pdb}/exp.npy"), mmap_mode="r").squeeze()
    origin, spacing = density_meta["origin"], density_meta["voxel_size"]
    low = np.maximum(np.floor((all_pose.min(0) - 9 - origin) / spacing).astype(int), 0)
    high = np.minimum(
        np.ceil((all_pose.max(0) + 9 - origin) / spacing).astype(int),
        np.asarray(density.shape[::-1]),
    )
    # low/high为XYZ网格区间[low,high), 反转轴后按ZYX切片, 不重新采样体素.
    slices = tuple(slice(l, h) for l, h in zip(low[::-1], high[::-1]))
    arrays.update(
        density=np.asarray(density[slices]),
        origin=origin + low * spacing,
        voxel_size=spacing,
        contour=float(density_meta["contour_canonical"]),
    )
    # /storage/penghongen/AdaLigand/Ori_Data/parse/9wup/occurrences.jsonl: candidate_id=2的原链/残基/配体身份记录, 供metadata显示FAD A:1103, 不用于更换成员, 生产说明同上述Ori_Data/README.md.
    instance = next(
        r
        for r in store.json(raw + f"/parse/{pdb}/occurrences.jsonl")
        if r["candidate_id"] == occurrence
    )
    metadata = {
        "condition": "explicit_emdb_level",
        "pdb_id": pdb,
        "occurrence_id": occurrence,
        "occurrence": instance,
        "metrics": metrics,
        "build": result["poses"][0],
        "sources": list(store.reads),
        "density_slice_xyz": [low.tolist(), high.tolist()],
    }
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "arrays.npz", **arrays)
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return arrays, metadata
