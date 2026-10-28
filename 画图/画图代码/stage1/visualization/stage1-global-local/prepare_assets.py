"""把选定病例的完整冻结数据转换为可编辑的 ChimeraX 本地素材。

输入 sources.json、cases.json 及 screen_cases.py 的筛选产物；输出目录显式指定。
保留全 map 和全部 candidate_selected 掩码；局部模型额外复制选定的原生 blob。
MRC 为 ZYX，origin 是首体素中心 XYZ Å，裁零时同步 origin，绝不移动或平滑数据。
"""

from pathlib import Path
import argparse
import json

import mrcfile
import numpy as np
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB.mmcifio import MMCIFIO
from scipy.spatial import cKDTree


def write_volume(path, array, origin_center, spacing):
    """写出 (Z,Y,X) 数组并回读核对体素、间距及首体素世界坐标。"""
    with mrcfile.new(path, overwrite=True) as handle:
        handle.set_data(array)
        handle.voxel_size = tuple(spacing)
        handle.header.origin = tuple(origin_center)
    with mrcfile.open(path) as handle:
        np.testing.assert_array_equal(handle.data, array)
        np.testing.assert_allclose(handle.header.origin.tolist(), origin_center, atol=2e-5, rtol=0)
        np.testing.assert_allclose(handle.voxel_size.tolist(), spacing, atol=2e-6, rtol=0)


def write_sparse(path, voxels, origin_center, spacing, shape):
    """裁掉掩码的外围零值；两格边界让等值面闭合，非零体素坐标保持不变。"""
    lower = np.maximum(voxels.min(axis=0) - 2, 0)
    upper = np.minimum(voxels.max(axis=0) + 3, shape)
    array = np.zeros(tuple(upper - lower), dtype=np.int8)
    array[tuple((voxels - lower).T)] = 1
    write_volume(path, array, origin_center + lower[::-1] * spacing, spacing)
    assert int(array.sum()) == len(np.unique(voxels, axis=0))


def write_atom_subset(path, cif, indices):
    """抽取 atom_site 原子表，沉积配体保留 auth 链和残基身份。"""
    writer = MMCIFIO()
    writer.set_dict({"data_": path.stem, **{k: [v[i] for i in indices] for k, v in cif.items() if k.startswith("_atom_site.")}})
    writer.save(str(path))


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--screening", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--sources", type=Path)
parser.add_argument("--cases", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
project = root.parents[4]
# 配置未传入时保留旧 no_level 用法; 新条件使用独立来源、病例清单和输出目录. 
source_file = args.sources if args.sources is not None else root / "sources.json"
case_file = args.cases if args.cases is not None else root / "cases.json"
sources = json.loads(source_file.read_text(encoding="utf-8"))
cases = json.loads(case_file.read_text(encoding="utf-8"))
screening = {c["pdb"]: c for c in json.loads((args.screening / "screening.json").read_text(encoding="utf-8"))}
local_pairs = json.loads((args.screening / "local_pairs.json").read_text(encoding="utf-8"))
residues = "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL A C G U DA DC DG DT UNK".split()
elements = {1:"H",6:"C",7:"N",8:"O",9:"F",11:"Na",12:"Mg",15:"P",16:"S",17:"Cl",19:"K",20:"Ca",26:"Fe",30:"Zn",34:"Se"}

for case in cases:
    pdb, oid = case["pdb"], case["occurrence_id"]
    src, dest = project / sources[pdb], args.output / pdb
    assets = dest / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (dest / "my_sessions").mkdir(exist_ok=True)
    evidence = screening[pdb]
    shape = np.array(evidence["shape_zyx"])
    spacing = np.array(evidence["spacing_xyz_A"])
    center_origin = np.array(evidence["corner_xyz_A"]) + spacing * 0.5
    density = np.load(src / "data/exp.npy", mmap_mode="r").squeeze()
    write_volume(assets / "density.mrc", np.asarray(density, dtype=np.float32), center_origin, spacing)
    occurrences = [json.loads(line) for line in (src / "data/occurrences.jsonl").read_text(encoding="utf-8").splitlines()]
    occurrence = next(o for o in occurrences if o["candidate_id"] == oid)
    with np.load(src / "data/ligand_area.npz") as masks:
        truth_all = np.unique(np.concatenate([masks[f'mask_{o["candidate_id"]}'] for o in occurrences]), axis=0)
        truth_local = masks[f"mask_{oid}"]
    write_sparse(assets / "truth_all.mrc", truth_all, center_origin, spacing, shape)
    write_sparse(assets / "truth_local.mrc", truth_local, center_origin, spacing, shape)

    for mode in case["local_blobs"]:
        with np.load(src / mode / "blobs.npz") as blobs, np.load(src / mode / "evaluation.npz") as ev:
            ids = blobs["source_blob_index" if mode == "emap" else "blob_index"]
            offsets, coords = blobs["voxel_offsets"], blobs["voxel_index_global_zyx"]
            retained = []
            for row in np.flatnonzero(ev["candidate_selected"]):
                bid = int(ev["source_blob_index"][row])
                j = int(np.flatnonzero(ids == bid)[0])
                start, end = offsets[j:j+2]
                voxels = coords[start:end]
                retained.append(voxels)
                if bid == case["local_blobs"][mode]:
                    write_sparse(assets / f"{mode}_local.mrc", voxels, center_origin, spacing, shape)
                    if mode == "emap":
                        local_emap = voxels.copy()
                if mode == "emap" and bid == case["receptor_fp_blob"]:
                    receptor_fp = voxels.copy()
                    write_sparse(assets / "emap_receptor_fp.mrc", voxels, center_origin, spacing, shape)
                if mode == "emap" and bid == case["remote_fp_blob"]:
                    write_sparse(assets / "emap_remote_fp.mrc", voxels, center_origin, spacing, shape)
            union = np.unique(np.concatenate(retained), axis=0)
            write_sparse(assets / f"{mode}_all.mrc", union, center_origin, spacing, shape)

    # token 受体保留推理坐标，C<n>/res_index+1 是 token 编号，并非沉积编号。
    token_structures = {}
    for mode, token_path in (("reference", "data/receptor_tokens.npz"), ("ca2", "cryo/receptor_tokens.npz")):
        with np.load(src / token_path) as t:
            n = len(t["coords"])
            fields = {
                "group_PDB": ["ATOM"] * n, "id": [str(i+1) for i in range(n)],
                "type_symbol": [elements[int(x)] for x in t["element"]],
                "label_atom_id": [x.decode().strip() if isinstance(x, bytes) else str(x).strip() for x in t["atom_name"]],
                "label_alt_id": ["."] * n, "label_comp_id": [residues[int(x)] for x in t["res_type"]],
                "label_asym_id": [f"C{int(x)}" for x in t["chain_index"]],
                "label_entity_id": [str(int(x)+1) for x in t["chain_index"]],
                "label_seq_id": [str(int(x)+1) for x in t["res_index"]],
                "auth_seq_id": [str(int(x)+1) for x in t["res_index"]],
                "auth_asym_id": [f"C{int(x)}" for x in t["chain_index"]],
                "pdbx_PDB_ins_code": ["?"]*n, "occupancy": ["1"]*n,
                "B_iso_or_equiv": ["0"]*n, "pdbx_PDB_model_num": ["1"]*n,
                **{f"Cartn_{a}":[f"{v:.5f}" for v in t["coords"][:, i]] for i,a in enumerate("xyz")},
            }
            atom_dict = {"_atom_site." + k:v for k,v in fields.items()}
            token_structures[mode] = (atom_dict, t["coords"].copy())
            write_atom_subset(assets / f"{mode}_receptor.cif", atom_dict, list(range(n)))

    cif = MMCIF2Dict(str(src / f"data/{pdb}.cif"))
    all_components = {(c["auth_asym_id"], str(c["auth_seq_id"]), c["ccd_id"]) for o in occurrences for c in o["components"]}
    target_components = {(c["auth_asym_id"], str(c["auth_seq_id"]), c["ccd_id"]) for c in occurrence["components"]}
    atom_keys = list(zip(cif["_atom_site.auth_asym_id"], cif["_atom_site.auth_seq_id"], cif["_atom_site.label_comp_id"]))
    all_indices = [i for i,k in enumerate(atom_keys) if k in all_components and cif["_atom_site.type_symbol"][i] not in ("H","D")]
    target_indices = [i for i in all_indices if atom_keys[i] in target_components]
    target_xyz = np.array([[float(cif[f"_atom_site.Cartn_{a}"][i]) for a in "xyz"] for i in target_indices])
    with np.load(src / "data/ligand_coords.npz") as ligand_coords:
        expected = ligand_coords[f"coords_{oid}"][ligand_coords[f"present_{oid}"]]
    atom_error = float(cKDTree(expected).query(target_xyz)[0].max())
    assert len(target_xyz) == len(expected) and atom_error < 0.002
    write_atom_subset(assets / "ligands_all.cif", cif, all_indices)
    write_atom_subset(assets / "ligand_target.cif", cif, target_indices)
    reference_dict, reference_xyz = token_structures["reference"]
    pocket_indices = np.flatnonzero(cKDTree(target_xyz).query(reference_xyz)[0] <= 6).tolist()
    write_atom_subset(assets / "receptor_pocket.cif", reference_dict, pocket_indices)
    # CA2 局部图使用实际输入受体, 不重对齐坐标; ca2_xyz 为 (N_CA2, 3) 的 XYZ Å 原子坐标. 
    ca2_dict, ca2_xyz = token_structures["ca2"]
    # (K,), 索引 CA2 原子表; 保留到任一沉积配体重原子的最近距离不超过 6 Å 的原子. 
    ca2_pocket = np.flatnonzero(cKDTree(target_xyz).query(ca2_xyz)[0] <= 6).tolist()
    write_atom_subset(assets / "ca2_pocket.cif", ca2_dict, ca2_pocket)
    fp_xyz = center_origin + receptor_fp[:, ::-1] * spacing
    fp_neighbours = np.flatnonzero(cKDTree(fp_xyz).query(reference_xyz)[0] <= 5).tolist()
    write_atom_subset(assets / "receptor_fp_neighbours.cif", reference_dict, fp_neighbours)
    emap_xyz = center_origin + local_emap[:, ::-1] * spacing
    core = local_emap[cKDTree(reference_xyz).query(emap_xyz)[0] <= 1.5]
    if len(core):
        write_sparse(assets / "emap_local_near_receptor.mrc", core, center_origin, spacing, shape)
    local = next(x for x in local_pairs if x["pdb"] == pdb and x["occurrence"]["candidate_id"] == oid)
    case_evidence = {"pdb":pdb, "role":case["role"], "source":sources[pdb], "contour":evidence["contour"],
                     "shape_zyx":shape.tolist(), "origin_center_xyz_A":center_origin.tolist(), "spacing_xyz_A":spacing.tolist(),
                     "occurrence":occurrence, "local_evidence":local,
                     "global_counts":{m:{k:v for k,v in s.items() if k != "blobs"} for m,s in evidence["methods"].items()},
                     "receptor_fp":next(r for r in evidence["methods"]["emap"]["blobs"] if r["blob_id"] == case["receptor_fp_blob"]),
                     "remote_fp":next((r for r in evidence["methods"]["emap"]["blobs"] if r["blob_id"] == case["remote_fp_blob"]), None),
                     "ligand_atom_max_error_A":atom_error, "selection":case}
    (dest / "evidence.json").write_text(json.dumps(case_evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{pdb}: full map, all selected masks, atomic coordinates and local identities verified", flush=True)
