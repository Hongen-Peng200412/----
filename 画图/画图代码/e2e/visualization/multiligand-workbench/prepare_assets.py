"""把 D 盘冻结原件转换为原生 ChimeraX 资产与 load.cxc, 不控制三维显示.

运行入口为文件末尾. 每例 scene.json 记录材料、原始编号、官方模型编号、显示阈值、姿态样本与
SDF 记录的连接; assets/maps 中大地图保留原值, areas/blobs 是逐区域的二值包围盒.
原 NPY 轴为 CZYX, MRC 轴为 ZYX; MRC 首采样世界坐标为 origin + spacing/2.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import mrcfile
import numpy as np
from Bio.PDB.mmcifio import MMCIFIO

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").exists())
sys.path.insert(0, str(ROOT / ".manuscript_deps/figure_runtime"))
from rdkit import Chem

RESIDUES = "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL A C G U DA DC DG DT UNK".split()
ELEMENTS = {
    1: "H",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    11: "Na",
    12: "Mg",
    15: "P",
    16: "S",
    17: "Cl",
    19: "K",
    20: "Ca",
    26: "Fe",
    30: "Zn",
    34: "Se",
}


def write_mrc(path, array, origin, spacing):
    """写原值 float32 (Z,Y,X) 地图, 采样中心 origin 和 XYZ spacing 均为 Å; 分层写入避免复制整图."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with mrcfile.new_mmap(path, shape=array.shape, mrc_mode=2, overwrite=False) as m:
        for z in range(0, array.shape[0], 32):
            m.data[z : z + 32] = array[z : z + 32]
        m.voxel_size = tuple(float(v) for v in spacing)
        m.header.origin = tuple(float(v) for v in origin)
        # 显示用头统计由固定抽样计算; 科学体素不变, 原统计/来源另保留在 NPZ.
        sample = np.asarray(array[::4, ::4, ::4], dtype=np.float64)
        m.header.dmin = float(sample.min())
        m.header.dmax = float(sample.max())
        m.header.dmean = float(sample.mean())
        m.header.rms = float(sample.std())


def write_cif(path, coords, elements, names, residues, chains, resids):
    """写 (N,3) 世界 XYZ 原子为 CIF, 保留五位小数; 其余长度 N 属性与原子逐项对齐."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    n = len(coords)
    fields = {
        "group_PDB": ["ATOM"] * n,
        "id": [str(i + 1) for i in range(n)],
        "type_symbol": list(elements),
        "label_atom_id": list(names),
        "label_alt_id": ["."] * n,
        "label_comp_id": list(residues),
        "label_asym_id": list(chains),
        "label_entity_id": ["1"] * n,
        "label_seq_id": list(resids),
        "pdbx_PDB_ins_code": ["?"] * n,
        "occupancy": ["1"] * n,
        "B_iso_or_equiv": ["0"] * n,
        "auth_seq_id": list(resids),
        "auth_asym_id": list(chains),
        "pdbx_PDB_model_num": ["1"] * n,
    }
    fields.update({f"Cartn_{axis}": [f"{x:.5f}" for x in coords[:, i]] for i, axis in enumerate("xyz")})
    out = MMCIFIO()
    out.set_dict({"data_": path.stem, **{"_atom_site." + k: v for k, v in fields.items()}})
    out.save(str(path))


def reference_sdf(path, occurrence, arrays, template):
    """从模板图与 present=True 的沉积原子写一个实例; 不补齐缺失原子、不优化或叠合坐标."""
    if path.exists():
        return
    oid = occurrence["candidate_id"]
    atoms = template["atoms"]
    bonds = template["bonds"]
    xyz = arrays[f"coords_{oid}"]
    present = arrays[f"present_{oid}"]
    molecule = Chem.RWMol()
    mapping = {}
    for i in np.flatnonzero(present):
        atom = Chem.Atom(int(atoms[i]["element"]))
        atom.SetFormalCharge(int(atoms[i]["charge"]))
        mapping[int(i)] = molecule.AddAtom(atom)
    types = [
        Chem.BondType.SINGLE,
        Chem.BondType.DOUBLE,
        Chem.BondType.TRIPLE,
        Chem.BondType.SINGLE,
        Chem.BondType.AROMATIC,
    ]
    for b in bonds:
        a, bidx = int(b["atom_1"]), int(b["atom_2"])
        if a in mapping and bidx in mapping:
            flags = np.flatnonzero(b["type"])
            kind = int(flags[0]) if len(flags) else 0
            molecule.AddBond(mapping[a], mapping[bidx], types[kind])
    mol = molecule.GetMol()
    conf = Chem.Conformer(len(mapping))
    for old, new in mapping.items():
        conf.SetAtomPosition(new, xyz[old].tolist())
    mol.AddConformer(conf)
    mol.SetProp("_Name", f"{occurrence['display_name']} {occurrence['site']} occurrence {oid}")
    # 缺失原子可能使芳香子图不完整; 输出现有连接而不要求补原子或强制芳香化.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(Chem.MolToMolBlock(mol, kekulize=False) + "\n$$$$\n", encoding="utf-8")


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
parser.add_argument("--pdb", nargs="+")
args = parser.parse_args()
catalog = json.loads((args.data_root / "catalog.json").read_text(encoding="utf-8"))
for case in catalog["cases"]:
    pdb = case["pdb_id"]
    if args.pdb and pdb not in args.pdb:
        continue
    folder = args.data_root / pdb
    source = folder / "source"
    assets = folder / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (folder / "exports").mkdir(exist_ok=True)
    meta = np.load(source / "exp.npz")
    spacing = meta["voxel_size"].astype(float)
    origin = meta["origin"].astype(float) + spacing / 2
    contour = float(meta["contour_canonical"])
    models = []
    commands = [
        "ligwork clear",
        "close",
        "view delete all",
        "volume defaultvalues showOnOpen false",
        "set bgColor white",
        "camera ortho",
        "lighting soft",
        "graphics silhouettes true width 1",
        "windowsize 1000 760",
    ]
    for domain, child in [("GT", 1), ("CA2", 2)]:
        t = np.load(source / f"{domain}_receptor.npz")
        f = assets / f"receptor_{domain}.cif"
        write_cif(
            f,
            t["coords"],
            [ELEMENTS[int(x)] for x in t["element"]],
            [x.decode().strip() for x in t["atom_name"]],
            [RESIDUES[int(x)] for x in t["res_type"]],
            [f"C{int(x)}" for x in t["chain_index"]],
            [str(int(x) + 1) for x in t["res_index"]],
        )
        models.append(
            {
                "key": "receptor_" + domain,
                "id": f"1.{child}",
                "file": f.relative_to(folder).as_posix(),
                "kind": "receptor",
                "domain": domain,
                "atoms": len(t["coords"]),
            }
        )
    for name, child in [("exp", 1), ("GT_sim", 2), ("CA2_sim", 3)]:
        array = np.load(source / f"{name}.npy", mmap_mode="r").squeeze()
        f = assets / "maps" / f"{name}.mrc"
        write_mrc(f, array, origin, spacing)
        if name == "exp":
            level = contour
        else:
            sample = np.asarray(array[::4, ::4, ::4])
            positive = sample[sample > 0]
            level = float(np.quantile(positive, 0.85))
        models.append(
            {
                "key": name,
                "id": f"2.{child}",
                "file": f.relative_to(folder).as_posix(),
                "kind": "density",
                "level": level,
                "shape_zyx": list(array.shape),
                "origin_xyz_A": origin.tolist(),
                "spacing_xyz_A": spacing.tolist(),
            }
        )
    area = np.load(source / "ligand_area.npz")
    coords = np.load(source / "ligand_coords.npz")
    for o in case["occurrences"]:
        oid = o["candidate_id"]
        f = assets / "references" / f"occ_{oid}.sdf"
        template = np.load(
            args.data_root / "templates" / (re.sub(r"[^A-Za-z0-9_.-]+", "_", o["object_key"]) + ".npz"),
            allow_pickle=True,
        )
        reference_sdf(f, o, coords, template)
        models.append(
            {
                "key": f"ref_{oid}",
                "id": f"3.{oid+1}",
                "file": f.relative_to(folder).as_posix(),
                "kind": "reference",
                "occurrence_id": oid,
            }
        )
        vox = area[f"mask_{oid}"]
        start = vox.min(0) - 1
        end = vox.max(0) + 2
        binary = np.zeros(tuple(end - start), dtype=np.float32)
        local = vox - start
        binary[tuple(local.T)] = 1
        f = assets / "areas" / f"occ_{oid}.mrc"
        write_mrc(f, binary, origin + start[::-1] * spacing, spacing)
        models.append(
            {
                "key": f"area_{oid}",
                "id": f"4.{oid+1}",
                "file": f.relative_to(folder).as_posix(),
                "kind": "area",
                "occurrence_id": oid,
            }
        )
    identities = []
    for o in case["occurrences"]:
        for d in case["domains"].values():
            for r in d["candidates"]:
                if r["matched_occurrence_id"] == o["candidate_id"] and r["target_smiles"]:
                    identities.append((r["target_smiles"], o["display_name"]))
    smiles_names = {
        i["smiles"]: next(
            o["display_name"] for o in case["occurrences"] if o["candidate_id"] in i["occurrence_ids"]
        )
        for i in case["identities"]
    }
    pose_rows = []
    for domain, bgroup, pgroup, igroup, mgroup in [("CA2", 10, 20, 40, 41), ("GT", 11, 21, 42, 43)]:
        blob = np.load(source / f"{domain}_blobs.npz")
        lookup = {int(v): i for i, v in enumerate(blob["blob_index"])}
        for r in case["domains"][domain]["candidates"]:
            bid = r["source_blob_index"]
            i = lookup[bid]
            lo, hi = blob["voxel_offsets"][i : i + 2]
            vox = blob["voxel_index_global_zyx"][lo:hi]
            start = vox.min(0) - 1
            end = vox.max(0) + 2
            binary = np.zeros(tuple(end - start), dtype=np.float32)
            local = vox - start
            binary[tuple(local.T)] = 1
            f = assets / "blobs" / f"{domain}_blob_{bid}.mrc"
            write_mrc(f, binary, origin + start[::-1] * spacing, spacing)
            models.append(
                {
                    "key": f"{domain}_blob_{bid}",
                    "id": f"{bgroup}.{bid+1}",
                    "file": f.relative_to(folder).as_posix(),
                    "kind": "blob",
                    "domain": domain,
                    "blob": bid,
                }
            )
            r["predicted_name"] = smiles_names.get(r["predicted_smiles"], "Unknown")
            centre = origin + vox[:, ::-1].mean(0) * spacing
            f = assets / "labels" / f"{domain}_blob_{bid}.cif"
            write_cif(f, np.asarray([centre]), ["C"], ["CTR"], ["CTR"], ["M"], ["1"])
            for kind, group in [("identity", igroup), ("correctness", mgroup)]:
                models.append(
                    {
                        "key": f"{domain}_{kind}_{bid}",
                        "id": f"{group}.{bid+1}",
                        "file": f.relative_to(folder).as_posix(),
                        "kind": kind,
                        "domain": domain,
                        "blob": bid,
                        "text": (
                            r["predicted_name"]
                            if kind == "identity"
                            else (
                                "correct"
                                if r["identity_correct"]
                                else "wrong" if r["foreground_target"] else "background"
                            )
                        ),
                    }
                )
            for run_index, run in enumerate(r["runs"]):
                rf = args.data_root / run["local"]
                ranking = json.loads((rf / "ranking.json").read_text(encoding="utf-8"))
                metrics = json.loads((rf / "evaluation_metrics.json").read_text(encoding="utf-8"))
                top = next(m for m in metrics if m["sample_index"] == ranking["top1_sample_index"])
                good = [m for m in metrics if m["rmsd_A"] is not None and m["sdf_index"] is not None]
                best = min(good, key=lambda m: (m["rmsd_A"], m["sample_index"])) if good else None
                blocks = (rf / "poses.sdf").read_text(encoding="utf-8").split("$$$$")
                for pose, metric, child in [("top1", top, 1), ("best", best, 2)]:
                    if metric is None or metric["sdf_index"] is None:
                        continue
                    f = assets / "poses" / f"{domain}_blob_{bid}_run{run_index}_{pose}.sdf"
                    f.parent.mkdir(parents=True, exist_ok=True)
                    block = blocks[metric["sdf_index"]]
                    block = block.removeprefix("\n") if metric["sdf_index"] > 0 else block
                    f.write_text(block + "$$$$\n", encoding="utf-8")
                    entry = {
                        "key": f"{domain}_pose_{bid}_{run_index}_{pose}",
                        "id": f"{pgroup}.{bid+1}.{run_index+1}.{child}",
                        "file": f.relative_to(folder).as_posix(),
                        "kind": "pose",
                        "domain": domain,
                        "blob": bid,
                        "views": run["views"],
                        "pose": pose,
                        "sample_index": metric["sample_index"],
                        "sdf_index": metric["sdf_index"],
                        "rmsd_A": metric["rmsd_A"],
                        "output_dir": run["output_dir"],
                    }
                    models.append(entry)
                    pose_rows.append(entry)
                assert top["sample_index"] == run["top1_sample_index"]
                if run["pose_min_rmsd_A"]["1"] is not None:
                    assert abs(top["rmsd_A"] - run["pose_min_rmsd_A"]["1"]) < 1e-8
                if best is not None and run["pose_min_rmsd_A"]["50"] is not None:
                    assert abs(best["rmsd_A"] - run["pose_min_rmsd_A"]["50"]) < 1e-8
    for m in models:
        commands.append(f'open "{(folder/m["file"]).as_posix()}" id #{m["id"]}')
        commands.append(f'rename #{m["id"]} "{m["key"]}"')
        if m["kind"] in ["density", "area", "blob"]:
            commands.append(
                f'volume #{m["id"]} step {2 if pdb=="11jb" and m["kind"]=="density" else 1} level {m.get("level",0.5):.10g} style {"mesh" if m["kind"] in ["area","density"] else "surface"}'
            )
        elif m["kind"] in ["identity", "correctness"]:
            color = (
                "#3d3d3d" if m["kind"] == "identity" else ("#009e73" if m["text"] == "correct" else "#b56b47")
            )
            commands.extend(
                [
                    f'style #{m["id"]} sphere',
                    f'size #{m["id"]} atomRadius 0.001',
                    f'label #{m["id"]} atoms text "{m["text"]}" color {color} height fixed size 14 offset 0,{12 if m["kind"]=="identity" else -12},0',
                ]
            )
    groups = {
        1: "Receptors",
        2: "Density",
        3: "Reference_ligands",
        4: "Reference_regions",
        10: "CA2_Find_blobs",
        11: "GT_Find_blobs",
        20: "CA2_Build_poses",
        21: "GT_Build_poses",
        40: "CA2_identity_labels",
        41: "CA2_match_labels",
        42: "GT_identity_labels",
        43: "GT_match_labels",
    }
    commands.extend(
        [
            f'rename #{i} "{name}"'
            for i, name in groups.items()
            if any(m["id"].split(".")[0] == str(i) for m in models)
        ]
    )
    commands.extend(
        [
            "hide models",
            "show #1.2|#3 models",
            "hide #1 atoms",
            "cartoon #1",
            "color #1 #c6c9cd",
            "style #3 stick",
            "size #3 stickRadius 0.22",
            "color #3 #e69f00",
            "color #2 #a5a9ad",
            "color #4 #8d9299",
            "color #10,11 #009e73",
            "style #20,21 stick",
            "size #20,21 stickRadius 0.25",
            "color #20,21 #009e73",
        ]
    )
    commands.extend(
        [f"name recGT #1.1", f"name recCA2 #1.2", f"name exp #2.1", f"name simGT #2.2", f"name simCA2 #2.3"]
    )
    commands.extend([f'name ref{o["candidate_id"]} #3.{o["candidate_id"]+1}' for o in case["occurrences"]])
    commands.extend(
        [
            "view #1.2 orient",
            "zoom 0.9",
            "view name overview",
            f'ligwork open "{(folder/"scene.json").as_posix()}"',
        ]
    )
    scene = {**case, "models": models, "contour": contour, "folder": folder.as_posix(), "schema": 1}
    (folder / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / "load.cxc").write_text("\n".join(commands) + "\n", encoding="utf-8")
    with (folder / "poses.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pose_rows[0]))
        writer.writeheader()
        writer.writerows({**r, "views": "|".join(r["views"])} for r in pose_rows)
    print(pdb, "models", len(models), "poses", len(pose_rows), "prepared", flush=True)
