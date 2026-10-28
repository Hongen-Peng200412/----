"""为总览图生成一致的四位点分子场景和三种 RDKit 游离构象.

主入口 main 从冻结的 RCSB mmCIF 和化学组分字典制备本次构建目录.
scene.json 保存 identities 的 SMILES、原子名、键、游离构象与 bound_poses 的 XYZ 坐标(Å), receptor.pdb 保存四聚体原始蛋白坐标.
所有候选密度、相机和 PPT 均由后续入口从本次 scene.json 生成, 不读取旧 temp.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from Bio.Align import PairwiseAligner
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.SeqUtils import seq1
from scipy.ndimage import gaussian_filter
import mrcfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
sys.path.insert(0, str(ROOT / '.manuscript_deps/figure_runtime'))
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolAlign


def read_atoms(path):
    """读取一份 mmCIF 的首个模型, 返回保留原子名、链、残基号和 XYZ(Å) 的字典列表."""
    data = MMCIF2Dict(str(path))
    atoms = []
    count = len(data['_atom_site.id'])
    for i in range(count):
        if data['_atom_site.pdbx_PDB_model_num'][i] != '1' or data['_atom_site.label_alt_id'][i] not in ('.', 'A'):
            continue
        atoms.append(dict(name=data['_atom_site.label_atom_id'][i], element=data['_atom_site.type_symbol'][i], resn=data['_atom_site.label_comp_id'][i], chain=data['_atom_site.auth_asym_id'][i], label_chain=data['_atom_site.label_asym_id'][i], resi=data['_atom_site.auth_seq_id'][i], protein=data['_atom_site.group_PDB'][i] == 'ATOM', xyz=[float(data[f'_atom_site.Cartn_{axis}'][i]) for axis in 'xyz']))
    return atoms


def sequence_alignment(donor, target):
    """按蛋白序列对应的 CA 原子作 Kabsch 叠合, 返回行向量 XYZ 的旋转、平移和 CA RMSD(Å)."""
    ca_d = [a for a in donor if a['protein'] and a['name'] == 'CA']
    ca_t = [a for a in target if a['protein'] and a['name'] == 'CA']
    aligner = PairwiseAligner(mode='global', match_score=2, mismatch_score=-1, open_gap_score=-8, extend_gap_score=-0.2)
    alignment = aligner.align(''.join(seq1(a['resn']) for a in ca_d), ''.join(seq1(a['resn']) for a in ca_t))[0]
    pairs = [(i, j) for ds, ts in zip(*alignment.aligned) for i, j in zip(range(*ds), range(*ts))]
    x = np.array([ca_d[i]['xyz'] for i, _ in pairs])
    y = np.array([ca_t[j]['xyz'] for _, j in pairs])
    u, _, vt = np.linalg.svd((x - x.mean(0)).T @ (y - y.mean(0)))
    rotation = u @ np.diag([1, 1, np.linalg.det(u @ vt)]) @ vt
    shift = y.mean(0) - x.mean(0) @ rotation
    return rotation, shift, float(np.sqrt(np.mean(np.sum((x @ rotation + shift - y) ** 2, axis=1))))


def molecule_from_ccd(path):
    """按 CCD 的真实键表构造重原子分子, 返回 RDKit 分子、CCD 顺序原子名和立体 SMILES."""
    data = MMCIF2Dict(str(path))
    names = data['_chem_comp_atom.atom_id']
    elements = data['_chem_comp_atom.type_symbol']
    rw = Chem.RWMol()
    index = {}
    for name, element in zip(names, elements):
        if element != 'H':
            index[name] = rw.AddAtom(Chem.Atom(element))
    orders = {'SING': Chem.BondType.SINGLE, 'DOUB': Chem.BondType.DOUBLE, 'TRIP': Chem.BondType.TRIPLE, 'AROM': Chem.BondType.AROMATIC}
    for a, b, order in zip(data['_chem_comp_bond.atom_id_1'], data['_chem_comp_bond.atom_id_2'], data['_chem_comp_bond.value_order']):
        if a in index and b in index:
            rw.AddBond(index[a], index[b], orders[order])
    ccd = rw.GetMol()
    Chem.SanitizeMol(ccd)
    ideal = Chem.Conformer(ccd.GetNumAtoms())
    for name, j in index.items():
        i = names.index(name)
        ideal.SetAtomPosition(j, [float(data[f'_chem_comp_atom.pdbx_model_Cartn_{axis}_ideal'][i]) for axis in 'xyz'])
    ccd.AddConformer(ideal)
    Chem.AssignStereochemistryFrom3D(ccd)
    smiles = next(v for t, p, v in zip(data['_pdbx_chem_comp_descriptor.type'], data['_pdbx_chem_comp_descriptor.program'], data['_pdbx_chem_comp_descriptor.descriptor']) if t == 'SMILES_CANONICAL' and p == 'CACTVS')
    smiles = Chem.MolToSmiles(Chem.MolFromSmiles(smiles), isomericSmiles=True)
    mol = Chem.MolFromSmiles(smiles)
    match = ccd.GetSubstructMatch(mol, useChirality=True)
    ccd_names = list(index)
    return mol, [ccd_names[i] for i in match], Chem.MolToSmiles(mol, isomericSmiles=True)


def main():
    """制备可清空 temp 后重建的场景; 所有写入仅进入 FIGURE_BUILD_ROOT."""
    source = ROOT / '画图/画图代码/e2e/output/overview-redesign-20261028/source/rcsb'
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    build.mkdir(parents=True, exist_ok=True)
    base = read_atoms(source / '1stp-assembly1.cif')
    chains = ['A', 'A-2', 'A-3', 'A-4']
    receptor = [a for a in base if a['protein']]
    lines = []
    for serial, a in enumerate(receptor, 1):
        x, y, z = a['xyz']
        chain = 'ABCD'[chains.index(a['chain'])]
        lines.append(f"ATOM  {serial:5d} {a['name']:>4s} {a['resn']:3s} {chain}{int(a['resi']):4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00          {a['element']:>2s}")
    (build / 'receptor.pdb').write_text('\n'.join(lines) + '\nEND\n', encoding='ascii')
    identities = []
    poses = []
    specs = [('BTN', 'Biotin', '#36986F', '1stp-assembly1.cif', [0, 1]), ('DTB', 'Desthiobiotin', '#C49B32', '3rdq.cif', [2]), ('IMI', 'Iminobiotin', '#CB627F', '2rtl.cif', [3])]
    for ccd, name, color, donor_file, targets in specs:
        mol, atom_names, smiles = molecule_from_ccd(source / f'{ccd}.cif')
        donor = read_atoms(source / donor_file)
        donor_chain = [a for a in donor if a['chain'] == 'A']
        ligand = {a['name']: a for a in donor_chain if a['resn'] == ccd}
        bound_xyz = np.array([ligand[a]['xyz'] for a in atom_names])
        comparisons = []
        for target in targets:
            rotation, shift, rmsd = sequence_alignment(donor_chain, [a for a in base if a['chain'] == chains[target]])
            xyz = bound_xyz @ rotation + shift
            blob = [1, 2, 4, 5][target]
            poses.append(dict(blob=f'B{blob}', identity=ccd, chain='ABCD'[target], source=donor_file, ca_alignment_rmsd_A=rmsd, xyz=xyz.tolist()))
            conformer = Chem.Conformer(mol.GetNumAtoms())
            for i, point in enumerate(xyz):
                conformer.SetAtomPosition(i, point)
            bound = Chem.Mol(mol)
            bound.AddConformer(conformer)
            comparisons.append(bound)
        hydrogenated = Chem.AddHs(mol)
        parameters = AllChem.ETKDGv3()
        parameters.randomSeed = 20261028
        parameters.numThreads = 4
        ids = list(AllChem.EmbedMultipleConfs(hydrogenated, numConfs=80, params=parameters))
        optimised = AllChem.MMFFOptimizeMoleculeConfs(hydrogenated, numThreads=4, maxIters=500)
        free = Chem.RemoveHs(hydrogenated)
        energies = np.array([energy for status, energy in optimised])
        choices = []
        for conf_id in ids:
            rmsds = [rdMolAlign.GetBestRMS(Chem.Mol(free), Chem.Mol(bound), prbId=conf_id, refId=0) for bound in comparisons]
            choices.append((conf_id, float(energies[conf_id]), min(rmsds)))
        eligible = [c for c in choices if c[1] <= float(energies.min()) + 4.0]
        selected = max(eligible, key=lambda c: c[2])
        ideal_xyz = free.GetConformer(selected[0]).GetPositions()
        identities.append(dict(id=ccd, name=name, color=color, smiles=smiles, elements=[a.GetSymbol() for a in mol.GetAtoms()], atom_names=atom_names, bonds=[[b.GetBeginAtomIdx(), b.GetEndAtomIdx(), b.GetBondTypeAsDouble()] for b in mol.GetBonds()], ideal_xyz=ideal_xyz.tolist(), ideal_conformer_id=selected[0], mmff_energy_kcal_mol=selected[1], mmff_min_energy_kcal_mol=float(energies.min()), ideal_bound_best_rmsd_A=selected[2]))
        print(ccd, 'free/bound RMSD', round(selected[2], 3), 'SMILES', smiles, flush=True)
        for pose in [p for p in poses if p['identity'] == ccd]:
            bound = Chem.Mol(mol)
            conformer = Chem.Conformer(bound.GetNumAtoms())
            for i, point in enumerate(pose['xyz']):
                conformer.SetAtomPosition(i, point)
            bound.AddConformer(conformer)
            bound.SetProp('_Name', pose['blob'] + '-' + ccd)
            with (build / (pose['blob'] + '.sdf')).open('w', encoding='ascii') as handle:
                writer = Chem.SDWriter(handle)
                writer.write(bound)
                writer.close()
    # 所有地图采用同一 XYZ 原点和 0.7 Å 间距; MRC 数组按 ZYX 保存.
    receptor_xyz = np.array([a['xyz'] for a in receptor])
    spacing = 0.7
    origin = np.floor(receptor_xyz.min(0) - 7)
    shape = np.ceil((receptor_xyz.max(0) + 7 - origin) / spacing).astype(int) + 1
    maps = build / 'maps'
    maps.mkdir(exist_ok=True)
    fields = {}
    for pose in poses:
        fields[pose['blob']] = np.array(pose['xyz'])
    # B3 是示意假阳性, 不借用真实配体坐标; 非对称三叶轮廓区别于其余四个区域.
    cameras = json.loads((source.parent / 'cameras.json').read_text(encoding='utf8'))
    axes = np.array(cameras['slender']['axes'])
    false_centre = receptor_xyz.mean(0) - axes[0]*17 + axes[2]*18
    fields['B3'] = false_centre + np.array([[0, 0, 0], [-2, 0, 1], [-3, -1, 1], [0, 0, 3], [0, 1, -3]])
    for label, xyz in list(fields.items()) + [('density', np.vstack([receptor_xyz] + list(fields.values())))]:
        grid = np.zeros(tuple(shape[::-1]), dtype=np.float32)
        indices = np.rint((xyz - origin) / spacing).astype(int)[:, ::-1]
        np.add.at(grid, tuple(indices.T), 1)
        sigma = 1.8 if label == 'density' else {'B1': 1.10, 'B2': 1.34, 'B3': 1.35, 'B4': 1.10, 'B5': 1.08}[label]
        grid = gaussian_filter(grid, sigma / spacing)
        grid /= grid.max()
        with mrcfile.new(maps / f'{label}.mrc', overwrite=True) as mrc:
            mrc.set_data(grid.astype(np.float32))
            mrc.voxel_size = spacing
            mrc.header.origin.x, mrc.header.origin.y, mrc.header.origin.z = origin
    result = dict(receptor_source='1stp-assembly1.cif', density_kind='schematic Gaussian density from atomic coordinates', identities=identities, bound_poses=poses, receptor_xyz=receptor_xyz.tolist(), false_positive_xyz_A=fields['B3'].tolist(), blob_centres={key: value.mean(0).tolist() for key, value in fields.items()}, map_origin_xyz_A=origin.tolist(), map_spacing_A=spacing, provenance='Schematic mixed occupancy. BTN poses retain deposited coordinates; DTB and IMI use deposited ligand coordinates after CA alignment of their donor protein. No model inference or experimental cryo-EM map is asserted.')
    (build / 'scene.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
