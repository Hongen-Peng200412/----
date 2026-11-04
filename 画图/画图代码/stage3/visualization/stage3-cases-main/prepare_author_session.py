"""准备9WUP原Top-1的ChimeraX初始材料, 不重新评价构象.

入口为模块末尾主流程; --output指定作者会话目录, --work指定本次运行日志目录.
读取explicit_emdb_level的arrays.npz、metadata.json和selected_case_metrics.json,
以及D盘同源完整GT受体与实验密度. 冻结输入与转换材料写入同阶段output的
author-session目录; 初始材料_9WUP.cxs嵌入地图, 材料索引.json连接模型编号与文件.
四个SDF各含53个重原子; 原子顺序沿arrays中的配体顺序. 碰撞只读原14对索引,
转换为完整受体的原子选择式, 由原生pbond命令显示, 不调用clashes重新判定.
加载后仅通过原生命令设置显隐、命名、基础取景并保存会话.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import mrcfile
import numpy as np
from scipy.spatial import cKDTree

root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(root / '.manuscript_deps/figure_runtime'))
from rdkit import Chem


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--work', type=Path, required=True)
args = parser.parse_args()
destination = args.output.resolve()
work = args.work.resolve()
destination.mkdir(parents=True, exist_ok=True)
work.mkdir(parents=True, exist_ok=True)
frozen = root / '画图/画图代码/stage3/output/stage3-cases-main/explicit_emdb_level'
bundle = frozen / 'author-session'
source = bundle / 'source'
materials = bundle / 'materials'
source.mkdir(parents=True, exist_ok=True)
materials.mkdir(parents=True, exist_ok=True)
for filename in ['arrays.npz', 'metadata.json']:
    shutil.copy2(frozen / 'assets/9wup_2' / filename, source / filename)
shutil.copy2(frozen / 'selected_case_metrics.json', source / 'selected_case_metrics.json')
original = Path('D:/AdaLigand_Visualization/9wup')
for filename in ['GT_receptor.npz', 'exp.npy', 'exp.npz']:
    shutil.copy2(original / 'source' / filename, source / filename)
shutil.copy2(original / 'assets/receptor_GT.cif', materials / 'receptor_GT.cif')
shutil.copy2(original / '本例材料来源.csv', source / 'D盘材料来源.csv')

arrays = np.load(source / 'arrays.npz', allow_pickle=False)
metadata = json.loads((source / 'metadata.json').read_text(encoding='utf-8'))
case = next(row for row in json.loads((source / 'selected_case_metrics.json').read_text(encoding='utf-8')) if row['pdb_id'] == '9wup' and row['occurrence_id'] == 2)
map_metadata = np.load(source / 'exp.npz', allow_pickle=False)
# (Z,Y,X)为原实验密度; 元数据origin是XYZ边界, MRC原点须写首体素中心, 单位Å.
density = np.load(source / 'exp.npy', mmap_mode='r').squeeze()
spacing = map_metadata['voxel_size']
with mrcfile.new(materials / 'experimental_density.mrc', overwrite=True) as handle:
    handle.set_data(np.asarray(density, dtype=np.float32))
    handle.voxel_size = tuple(spacing)
    handle.header.origin = tuple(map_metadata['origin'] + 0.5 * spacing)

commands = ['set bgColor white', 'open "' + (materials / 'receptor_GT.cif').as_posix() + '" id #1 name "GT_receptor_full"', 'open "' + (materials / 'experimental_density.mrc').as_posix() + '" id #2 name "Experimental_density"']
models = [{'id': '1', 'name': 'GT_receptor_full', 'file': 'receptor_GT.cif'}, {'id': '2', 'name': 'Experimental_density', 'file': 'experimental_density.mrc'}]
for model_id, key, name in [(3, 'gt', 'Reference_FAD_A1103'), (4, 'official', 'PocketXMol_Top1_sample22'), (5, 'tuned', 'DG_PocketXMol_Top1_sample18'), (6, 'build', 'Emap2lig_Top1_rank1')]:
    molecule = Chem.RemoveHs(Chem.MolFromSmiles(metadata['smiles']))
    conformer = Chem.Conformer(molecule.GetNumAtoms())
    # (53,3), 原重原子世界XYZ坐标Å; 仅转换文件格式, 不对齐、补原子或优化.
    for atom_index, xyz in enumerate(arrays[key]):
        conformer.SetAtomPosition(atom_index, tuple(float(value) for value in xyz))
    molecule.AddConformer(conformer)
    molecule.SetProp('_Name', name)
    (materials / (key + '.sdf')).write_text(Chem.MolToMolBlock(molecule, forceV3000=True, kekulize=False) + '\n$$$$\n', encoding='utf-8')
    commands.append(f'open "{(materials / (key + ".sdf")).as_posix()}" id #{model_id} name "{name}"')
    models.append({'id': str(model_id), 'name': name, 'file': key + '.sdf', 'source_key': key})

tokens = np.load(source / 'GT_receptor.npz', allow_pickle=False)
# (421,)为原局部受体原子到完整token原子的索引; 精确对应由独立验收检查.
_, local_to_full = cKDTree(tokens['coords']).query(arrays['receptor_xyz'])
pairs = []
for ligand_index, local_index in case['build']['clash_indices']:
    full_index = int(local_to_full[local_index])
    atom_name = tokens['atom_name'][full_index].decode().strip()
    receptor_spec = f'#1/C{int(tokens["chain_index"][full_index])}:{int(tokens["res_index"][full_index])+1}@{atom_name}'
    ligand_spec = f'#6@@serial_number={ligand_index+1}'
    commands.append(f'pbond {receptor_spec} {ligand_spec} name "Original_Emap_clashes_14_pairs" color red radius 0.06 dashes 6 showDist false reveal false')
    pairs.append({'ligand_index': ligand_index, 'local_receptor_index': local_index, 'full_receptor_index': full_index, 'receptor_spec': receptor_spec, 'ligand_spec': ligand_spec})
commands += ['name clashRec ' + '|'.join(sorted({pair['receptor_spec'] for pair in pairs})), 'name clashLig ' + '|'.join(sorted({pair['ligand_spec'] for pair in pairs}))]
# 5Å只定义共同显示邻域; 按整残基保留, 不参与原碰撞或密度覆盖的评价.
all_poses = np.concatenate([arrays[key] for key in ['gt', 'official', 'tuned', 'build']])
near = cKDTree(all_poses).query(tokens['coords'])[0] < 5.0
residues = sorted({(int(chain), int(residue)) for chain, residue in zip(tokens['chain_index'][near], tokens['res_index'][near])})
commands += ['name pocket ' + '|'.join(f'#1/C{chain}:{residue+1}' for chain, residue in residues)]
commands += ['hide #4-7 models', 'hide #2 models', 'view #3-6', 'clip off', f'save "{(destination / "初始材料_9WUP.cxs").as_posix()}" includeMaps true', f'log save "{(work / "native_load.html").as_posix()}"']
(bundle / 'load.cxc').write_text('\n'.join(commands) + '\n', encoding='utf-8')
(work / 'load.py').write_text('from chimerax.core.commands import run\nrun(session, ' + repr('open "' + (bundle / 'load.cxc').as_posix() + '"') + ')\n', encoding='utf-8')
index = {'pdb': '9wup', 'occurrence_id': 2, 'ligand': 'FAD A:1103', 'condition': 'explicit_emdb_level', 'PocketXMol_and_DG_input': 'GT/C0', 'models': models, 'clash_group_id': '7', 'pairs': pairs, 'saved_metrics': {key: case[key] for key in ['official', 'tuned', 'build']}, 'density_contour': float(arrays['contour']), 'display_neighbourhood_A': 5.0, 'residue_numbering': 'token chain C<chain_index>, residue res_index+1; not deposited auth numbering'}
(bundle / 'materials.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
shutil.copy2(bundle / 'materials.json', destination / '材料索引.json')
subprocess.run(['powershell.exe', '-NoProfile', '-File', str(root / '转换工具/ops/rebuild_support/run_chimerax.ps1'), '-CxcPath', str(work / 'load.py'), '-LogPrefix', str(work / 'load')], check=True)
print('9WUP原生初始会话已保存: ' + str(destination / '初始材料_9WUP.cxs'))
