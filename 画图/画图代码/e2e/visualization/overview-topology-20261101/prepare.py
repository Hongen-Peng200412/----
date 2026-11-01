"""为总览图生成无环、单环、双环的三种示意配体.

读取同目录冻结 source 中的原场景, 将新配体放在原四个位点的中心与主轴附近.
FIGURE_BUILD_ROOT 接收新建目录; scene.json 保存规范 SMILES、环数、元素、键和 Å 坐标, SDF 保存游离及位点构象.
这些坐标用于流程示意, 不表示对接或实验结果.
"""
import json
import os
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolAlign

root = Path(__file__).resolve().parents[5]
source = root / '画图/画图代码/e2e/output/overview-topology-20261101/source'
build = Path(os.environ['FIGURE_BUILD_ROOT'])
build.mkdir(parents=True, exist_ok=True)
old = json.loads((source / 'scene-before.json').read_text(encoding='utf8'))
specs = [
    ('GER', 'CC(C)=CCC/C(C)=C/CO', '#36986F', 0, 'CC(C)=CCC/C(C)=…', ['B1', 'B3']),
    ('IBU', 'CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O', '#D5B439', 1, 'CC(C)Cc1ccc…', ['B2']),
    ('NAP', 'COc1ccc2cc([C@H](C)C(=O)O)ccc2c1', '#CF5558', 2, 'COc1ccc2cc…', ['B5']),
]
identities, poses = [], []
# 作者把原 B2 改为 B3, 原 B4 改为 B2, 原假阳性 B3 改为 B4.
old_labels = {'B1': 'B1', 'B3': 'B2', 'B2': 'B4', 'B5': 'B5'}
for ordinal, (name, smiles, color, rings, display, blobs) in enumerate(specs):
    molecule = Chem.MolFromSmiles(smiles)
    canonical = Chem.MolToSmiles(molecule)
    molecule = Chem.MolFromSmiles(canonical)
    assert molecule.GetRingInfo().NumRings() == rings
    hydrogenated = Chem.AddHs(molecule)
    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = 20261101 + ordinal
    conformers = list(AllChem.EmbedMultipleConfs(hydrogenated, numConfs=30, params=parameters))
    energies = AllChem.MMFFOptimizeMoleculeConfs(hydrogenated)
    molecule = Chem.RemoveHs(hydrogenated)
    ranked = sorted(conformers, key=lambda i: energies[i][1])
    ideal = ranked[0]
    # 选择有内部构象差异的低能量构象, 不把 Build 示意画成刚体平移.
    alternatives = [(rdMolAlign.GetBestRMS(Chem.Mol(molecule), molecule, prbId=i, refId=ideal), i) for i in ranked[1:]]
    alternative_rmsd, bound = max(alternatives)
    ideal_xyz = molecule.GetConformer(ideal).GetPositions()
    ideal_xyz -= ideal_xyz.mean(axis=0)
    identity = dict(id=name, smiles=canonical, display_smiles=display, color=color, rings=rings,
                    elements=[a.GetSymbol() for a in molecule.GetAtoms()],
                    atom_names=[f'{a.GetSymbol()}{a.GetIdx()+1}' for a in molecule.GetAtoms()],
                    ring_atoms=sorted({a for ring in molecule.GetRingInfo().AtomRings() for a in ring}),
                    bonds=[[b.GetBeginAtomIdx(), b.GetEndAtomIdx(), b.GetBondTypeAsDouble()] for b in molecule.GetBonds()],
                    ideal_xyz=ideal_xyz.tolist(), ideal_bound_best_rmsd_A=alternative_rmsd, blobs=blobs)
    identities.append(identity)
    (build / f'identity-{name}.sdf').write_text(Chem.MolToMolBlock(molecule, confId=ideal) + '$$$$\n', encoding='utf8')
    for blob in blobs:
        previous = next(p for p in old['bound_poses'] if p['blob'] == old_labels[blob])
        target = np.array(previous['xyz'])
        xyz = molecule.GetConformer(bound).GetPositions().copy()
        xyz -= xyz.mean(axis=0)
        _, _, ligand_axes = np.linalg.svd(xyz, full_matrices=False)
        _, _, target_axes = np.linalg.svd(target - target.mean(axis=0), full_matrices=False)
        rotation = ligand_axes.T @ target_axes
        if np.linalg.det(rotation) < 0:
            target_axes[-1] *= -1
            rotation = ligand_axes.T @ target_axes
        xyz = xyz @ rotation + target.mean(axis=0)
        pose_molecule = Chem.Mol(molecule)
        pose_molecule.RemoveAllConformers()
        pose_conformer = Chem.Conformer(molecule.GetNumAtoms())
        for i, point in enumerate(xyz):
            pose_conformer.SetAtomPosition(i, point)
        pose_molecule.AddConformer(pose_conformer)
        (build / f'{blob}.sdf').write_text(Chem.MolToMolBlock(pose_molecule) + '$$$$\n', encoding='utf8')
        parsed_pose = Chem.MolFromMolBlock((build / f'{blob}.sdf').read_text(encoding='utf8'))
        assert Chem.MolToSmiles(parsed_pose) == canonical
        poses.append(dict(blob=blob, identity=name, xyz=xyz.tolist()))
scene = dict(identities=identities, bound_poses=poses, old_labels=old_labels,
             description='Native molecular rendering for a constructed workflow schematic; not experimental or predicted poses.')
(build / 'scene.json').write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding='utf8')
print([(i['id'], i['rings'], round(i['ideal_bound_best_rmsd_A'], 3)) for i in identities])
