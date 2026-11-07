"""Fig7持有CA2作者病例的科学原子转换, 三个BACKUP以同一原Top1选择重建.

receptor_cif/reference_sdf保持原世界XYZ和原化学模板; materialize把选择模块已经确认的原姿态写入本次temp. 不读取作者PNG/CXS中的坐标, 不向服务器写入.
"""

from io import BytesIO
import numpy as np
from rdkit import Chem

RESIDUES = "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL A C G U DA DC DG DT UNK".split()


def receptor_cif(path, arrays):
    """将原受体tokens写为本次原生CIF, 不补原子、不叠合.

    path为本次CIF地址. arrays.coords为(R,3)世界XYZ/Å; element为(R,)原子序数,
    atom_name为(R,)字节原子名, res_type为(R,)残基类别索引,
    chain_index/res_index为(R,)原token链与残基编号, 均与coords原子轴对齐.
    输出atom_site每行一个原子, 坐标保持原世界系; 用token编号供应显示连接,
    不把它们声称为沉积结构的auth编号. 函数只写path, 不返回派生科学对象.
    """
    coords = arrays["coords"]
    fields = [
        "group_PDB",
        "id",
        "type_symbol",
        "label_atom_id",
        "label_alt_id",
        "label_comp_id",
        "label_asym_id",
        "label_entity_id",
        "label_seq_id",
        "pdbx_PDB_ins_code",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
        "occupancy",
        "B_iso_or_equiv",
        "auth_seq_id",
        "auth_asym_id",
        "pdbx_PDB_model_num",
    ]
    symbols = {
        int(number): Chem.GetPeriodicTable().GetElementSymbol(int(number))
        for number in np.unique(arrays["element"])
    }
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "data_"
            + path.stem
            + "\n#\nloop_\n"
            + "".join("_atom_site." + name + "\n" for name in fields)
        )
        for index, (xyz, element, name, residue, chain, resid) in enumerate(
            zip(
                coords,
                arrays["element"],
                arrays["atom_name"],
                arrays["res_type"],
                arrays["chain_index"],
                arrays["res_index"],
            ),
            1,
        ):
            # 原token链/残基编号用于绘制连接, 不是沉积auth标识; 原float32世界坐标以8位小数无损往返.
            atom_name = name.decode().strip()
            chain_name = "C" + str(int(chain))
            residue_number = str(int(resid) + 1)
            handle.write(
                f'ATOM {index} {symbols[int(element)]} "{atom_name}" . {RESIDUES[int(residue)]} {chain_name} 1 {residue_number} ? {xyz[0]:.8f} {xyz[1]:.8f} {xyz[2]:.8f} 1 0 {residue_number} {chain_name} 1\n'
            )
        handle.write("#\n")


def reference_sdf(path, occurrence, coordinates, template):
    """按沉积present掩码写一个真实实例的SDF, 保留原世界坐标与实际缺失状态.

    occurrence.candidate_id为PDB内真实实例编号, components[*].ccd_id用于分子显示名.
    coordinates的present_<id>为bool(T,), coords_<id>为(T,3)世界XYZ/Å, 二者同属模板原子轴.
    template.atoms为长度T的结构化数组, element为原子序数, charge为形式电荷.
    template.bonds为长度B的结构化数组, atom_1/atom_2是模板原子下标,
    type为5维键类别掩码, 首个True按原转换规则映射为SINGLE/DOUBLE/TRIPLE/SINGLE/AROMATIC.
    只保留present原子及两端均存在的键, 将模板原子轴压缩为SDF原子轴后写path.
    不补原子、不根据距离推键, 不返回新的参考坐标定义.
    """
    oid = occurrence["candidate_id"]
    atoms = template["atoms"]
    mol = Chem.RWMol()
    # dict[int,int], 模板原子下标到当前SDF紧凑原子下标; 未present的模板原子不入字典.
    mapping = {}
    for index in np.flatnonzero(coordinates[f"present_{oid}"]):
        atom = Chem.Atom(int(atoms[index]["element"]))
        atom.SetFormalCharge(int(atoms[index]["charge"]))
        mapping[int(index)] = mol.AddAtom(atom)
    bond_types = [
        Chem.BondType.SINGLE,
        Chem.BondType.DOUBLE,
        Chem.BondType.TRIPLE,
        Chem.BondType.SINGLE,
        Chem.BondType.AROMATIC,
    ]
    for bond in template["bonds"]:
        a, b = int(bond["atom_1"]), int(bond["atom_2"])
        if a in mapping and b in mapping:
            mol.AddBond(mapping[a], mapping[b], bond_types[int(np.flatnonzero(bond["type"])[0])])
    molecule = mol.GetMol()
    conformer = Chem.Conformer(len(mapping))
    for old, new in mapping.items():
        conformer.SetAtomPosition(new, coordinates[f"coords_{oid}"][old].tolist())
    molecule.AddConformer(conformer)
    molecule.SetProp(
        "_Name", "+".join(c["ccd_id"] for c in occurrence["components"]) + " occurrence " + str(oid)
    )
    path.write_text(
        Chem.MolToMolBlock(molecule, kekulize=False, forceV3000=True) + "\n$$$$\n", encoding="utf-8"
    )


def materialize(store, case, build, display):
    """把本例CA2受体、全部沉积配体和所选原Top1转成ChimeraX同次输入.

    输入参数:
        - case: dict, selection.read_case(...,True)的单PDB记录.
            - poses: list[dict], 每项保留原sample_index、成功SDF内sdf_index、source_blob_index、server_output及身份/成功标记, 原编号不能互换.
        - build: Path, 本次temp科学输入目录.
        - display: dict, 本图明确给定的camera_matrix/field_width/输出像素.
    返回scene: dict, 交本图native.py读取.
        - loads: list[dict], 每项file为本次CIF/SDF绝对地址, kind为receptor/reference/prediction, name为显示名, id为本次ChimeraX模型编号; prediction另有success及eligible_identity布尔标记.
        - display: dict, 调用方原显示定义, 不从构象成功率重设相机或配色.
        - output: str, build/native-output绝对目录; 原生脚本只在这里写本次PNG/CXS.
    本次还写receptor.cif、reference_<真实编号>.sdf和prediction_<blob编号>.sdf, 不改作者原件.
    """
    pdb = case["pdb"]
    build.mkdir(parents=True, exist_ok=True)
    # /storage/penghongen/AdaLigand/Ori_Data/parse/<pdb>/occurrences.jsonl: candidate_id/object_key/components定位全部沉积配体, 不限合格小分子, 如30ga. 同目录ligand_coords.npz用coords_<id>(N,3)XYZÅ与present_<id>(N,)保留缺原子状态.
    # 生产说明: C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/Ori_Data/README.md; /home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand/Data_Preprocessing/Ori_Data/README.md.
    occurrences = store.json(
        f"/storage/penghongen/AdaLigand/Ori_Data/parse/{pdb}/occurrences.jsonl"
    )
    # /storage/penghongen/Adaligand_infered_receptor_data/cryoatom2/test_0_chain06/Ori_Data/parse/<pdb>/receptor_tokens.npz: coords(R,3)XYZÅ; element/atom_name/res_type/chain_index/res_index(R,)为同轴原属性. 使用原token链/残基编号绘制连接, 不声称其为沉积auth编号.
    # 原Adapter生产版本为c209bedb1883, 说明: /home/penghongen/Feedback/AdaLigand/releases/AdaLigand_c209bedb1883/AdaLigand/测评数据代码/cryoatom2_受体Adapter/README.md; 本地C:/Users/15919/Desktop/AdaLigand/测评数据代码/cryoatom2_受体Adapter/README.md.
    receptor = store.npz(
        f"/storage/penghongen/Adaligand_infered_receptor_data/cryoatom2/test_0_chain06/Ori_Data/parse/{pdb}/receptor_tokens.npz"
    )
    receptor_cif(build / "receptor.cif", receptor)
    coordinates = store.npz(f"/storage/penghongen/AdaLigand/Ori_Data/parse/{pdb}/ligand_coords.npz")
    loads = [
        dict(
            file=str((build / "receptor.cif").resolve()),
            kind="receptor",
            name="CryoAtom2 receptor",
            id=1,
        )
    ]
    templates = {}
    for index, occurrence in enumerate(occurrences, 100):
        key = occurrence["object_key"]
        if key not in templates:
            name = key.replace(":", "_") + ".npz"
            # /storage/penghongen/AdaLigand/Ori_Data/ligand_objects/<object_key替换冒号>.npz: atoms结构化数组给元素/电荷, bonds给原子索引和键类别; 只连接present掩码中已有原子, 不补原子. 生产说明同上Ori_Data/README.md.
            with np.load(
                BytesIO(
                    store.read_bytes(
                        "/storage/penghongen/AdaLigand/Ori_Data/ligand_objects/" + name
                    )
                ),
                allow_pickle=False,
            ) as data:
                templates[key] = {field: data[field] for field in ["atoms", "bonds"]}
        target = build / f'reference_{occurrence["candidate_id"]}.sdf'
        reference_sdf(target, occurrence, coordinates, templates[key])
        loads.append(
            dict(
                file=str(target.resolve()),
                kind="reference",
                name="Deposited " + str(occurrence["candidate_id"]),
                id=index,
            )
        )
    # 路径由selection.py从受控/actual原索引确定, 不是凭本地编号推测: 原目录例/storage/penghongen/Adaligand_E2E/test/test_0/build/PocketXMol-tuned/CA2/test/local-c1/30ga/1/poses.sdf. 成功SDF位置用metrics.sdf_index, 原采样编号用ranking.top1_sample_index, 二者不可互换. 生产说明见selection.py中两个实际release README.
    store.read_many([pose["server_output"] + "/poses.sdf" for pose in case["poses"]])
    for pose in case["poses"]:
        supplier = Chem.ForwardSDMolSupplier(
            BytesIO(store.read_bytes(pose["server_output"] + "/poses.sdf")),
            removeHs=False,
            sanitize=False,
        )
        molecule = next(mol for index, mol in enumerate(supplier) if index == pose["sdf_index"])
        target = build / f'prediction_{pose["source_blob_index"]}.sdf'
        target.write_text(
            Chem.MolToMolBlock(molecule, kekulize=False, forceV3000=True) + "\n$$$$\n",
            encoding="utf-8",
        )
        loads.append(
            dict(
                file=str(target.resolve()),
                kind="prediction",
                name=f'Top-1 blob {pose["source_blob_index"]}',
                id=200 + pose["source_blob_index"],
                success=pose["success"],
                eligible_identity=pose["eligible_identity"],
            )
        )
    return dict(loads=loads, display=display, output=str((build / "native-output").resolve()))
