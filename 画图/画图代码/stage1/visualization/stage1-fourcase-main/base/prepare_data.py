"""将只读源文件转换为 MRC/mmCIF 基础模型, 不设置颜色、透明度或相机.

输入 cases.json 和 formal/Stage1_fourcase_20260930/source/. 输出每 PDB 的 assets/ 与 data.json.
MRC 数据按 ZYX 储存, header.origin 为首体素中心 XYZ, 单位 Å; 局部 mask 裁去外围全零体素, 非零体素不变.
receptor.cif 使用实际推理 token 的原子坐标; 其受体编号是 token 编号, 不用于报告沉积残基编号.
ligand.cif 和 small_ligands.cif 保留沉积原子的身份与坐标. data.json 保存坐标契约和已核对的候选事实.
"""
from pathlib import Path
import json
import numpy as np
import mrcfile
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.PDB.mmcifio import MMCIFIO

ROOT = Path(__file__).resolve().parent
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
OUTPUT = PROJECT / '画图/画图代码/stage1/output/stage1-fourcase-main/base'
RESIDUES = 'ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL A C G U DA DC DG DT UNK'.split()
ELEMENTS = {1:'H',6:'C',7:'N',8:'O',9:'F',11:'Na',12:'Mg',15:'P',16:'S',17:'Cl',19:'K',20:'Ca',26:'Fe',30:'Zn',34:'Se'}


def write_volume(path, array, origin, spacing):
    """写出并回读 MRC, 核对数组和首采样点; array 为 (Z,Y,X), origin/spacing 为 XYZ Å."""
    with mrcfile.new(path, overwrite=True) as handle:
        handle.set_data(array)
        handle.voxel_size = tuple(spacing)
        handle.header.origin = tuple(origin)
    with mrcfile.open(path) as handle:
        assert np.array_equal(handle.data, array)
        assert np.allclose(list(handle.header.origin.tolist()), origin, atol=2e-5)


def write_sparse(path, voxels, origin, spacing, full_shape):
    """将 (N,3) ZYX 非零体素导出为紧致 MRC; 通过调整 origin 保持世界坐标完全不变."""
    lower = np.maximum(voxels.min(0) - 2, 0)
    upper = np.minimum(voxels.max(0) + 3, full_shape)
    data = np.zeros(tuple(upper - lower), dtype=np.int8)
    data[tuple((voxels - lower).T)] = 1
    write_volume(path, data, origin + lower[::-1] * spacing, spacing)
    assert int(data.sum()) == len(np.unique(voxels, axis=0))


def write_atom_subset(path, cif, indices):
    """从沉积 CIF 的 atom_site 表抽取原子, 保留全套原子字段和 auth 编号."""
    atom_dict = {'data_': path.stem}
    atom_dict.update({key: [values[i] for i in indices] for key, values in cif.items() if key.startswith('_atom_site.')})
    writer = MMCIFIO()
    writer.set_dict(atom_dict)
    writer.save(str(path))


for case in json.loads((ROOT / 'cases.json').read_text(encoding='utf-8')):
    pdb = case['pdb']
    src, dest = OUTPUT / 'source' / pdb, OUTPUT / pdb
    if not src.is_dir():
        src = PROJECT / '画图/画图代码/stage1/output/stage1-fourcase-main/source_history/source' / pdb
    if not (src / 'data/exp.npy').exists():
        print(f'{pdb}: source download pending', flush=True)
        continue
    assets = dest / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    meta = np.load(src / 'data/exp.npz')
    spacing = meta['voxel_size'].astype(float)
    origin = meta['origin'].astype(float) + .5 * spacing
    density = np.load(src / 'data/exp.npy', mmap_mode='r').squeeze()
    shape = np.array(density.shape)
    if not (assets / 'density.mrc').exists():
        write_volume(assets / 'density.mrc', np.asarray(density, dtype=np.float32), origin, spacing)
    occid = case['occurrence']['candidate_id']
    gt = np.load(src / 'data/ligand_area.npz')[f'mask_{occid}']
    gt_flat = np.ravel_multi_index(gt.T, shape)
    write_sparse(assets / 'gt_area.mrc', gt, origin, spacing, shape)
    for mode in ('real', 'cryo', 'emap'):
        blobs = np.load(src / mode / 'blobs.npz')
        ev = np.load(src / mode / 'evaluation.npz')
        ids = blobs['source_blob_index' if mode == 'emap' else 'blob_index']
        selected = []
        for i in np.flatnonzero(ev['candidate_selected']):
            bid = int(ev['source_blob_index'][i])
            pos = int(np.flatnonzero(ids == bid)[0])
            begin, end = blobs['voxel_offsets'][pos:pos+2]
            voxels = blobs['voxel_index_global_zyx'][begin:end]
            selected.append(voxels)
            if bid == case[mode]['blob']:
                intersection = len(np.intersect1d(gt_flat, np.ravel_multi_index(voxels.T, shape)))
                assert intersection == case[mode]['intersection']
                assert len(voxels) == case[mode]['pred_size']
                write_sparse(assets / f'{mode}_target.mrc', voxels, origin, spacing, shape)
        write_sparse(assets / f'{mode}_selected.mrc', np.unique(np.concatenate(selected), axis=0), origin, spacing, shape)
    for mode, filename in (('real', 'data/receptor_tokens.npz'), ('cryo', 'cryo/receptor_tokens.npz')):
        z = np.load(src / filename)
        n = len(z['coords'])
        chains = [f'C{int(v)}' for v in z['chain_index']]
        residues = [str(int(v) + 1) for v in z['res_index']]
        names = [v.decode().strip() if isinstance(v, bytes) else str(v).strip() for v in z['atom_name']]
        fields = {'group_PDB':['ATOM']*n, 'id':[str(i+1) for i in range(n)], 'type_symbol':[ELEMENTS[int(v)] for v in z['element']],
                  'label_atom_id':names, 'label_alt_id':['.']*n, 'label_comp_id':[RESIDUES[int(v)] for v in z['res_type']],
                  'label_asym_id':chains, 'label_entity_id':[str(int(v)+1) for v in z['chain_index']], 'label_seq_id':residues,
                  'pdbx_PDB_ins_code':['?']*n, 'occupancy':['1']*n, 'B_iso_or_equiv':['0']*n,
                  'auth_seq_id':residues, 'auth_asym_id':chains, 'pdbx_PDB_model_num':['1']*n}
        fields.update({f'Cartn_{axis}':[f'{v:.5f}' for v in z['coords'][:,i]] for i,axis in enumerate('xyz')})
        writer = MMCIFIO()
        writer.set_dict({'data_':mode, **{'_atom_site.'+key:value for key,value in fields.items()}})
        writer.save(str(assets / f'{mode}_receptor.cif'))
    cif = MMCIF2Dict(str(src / f'data/{pdb}.cif'))
    occurrences = [json.loads(line) for line in (src / 'data/occurrences.jsonl').read_text().splitlines()]
    small_components = {(c['auth_asym_id'],str(c['auth_seq_id']),c['ccd_id']) for o in occurrences if o['type_tag']=='small_molecule' for c in o['components']}
    target_components = {(c['auth_asym_id'],str(c['auth_seq_id']),c['ccd_id']) for c in case['occurrence']['components']}
    atom_keys = list(zip(cif['_atom_site.auth_asym_id'],cif['_atom_site.auth_seq_id'],cif['_atom_site.label_comp_id']))
    small_indices = [i for i,key in enumerate(atom_keys) if key in small_components and cif['_atom_site.type_symbol'][i] != 'H']
    target_indices = [i for i in small_indices if atom_keys[i] in target_components]
    xyz = np.array([[float(cif[f'_atom_site.Cartn_{a}'][i]) for a in 'xyz'] for i in target_indices])
    parsed = np.load(src / 'data/ligand_coords.npz')
    expected = parsed[f'coords_{occid}'][parsed[f'present_{occid}']]
    distances = np.linalg.norm(xyz[:,None,:]-expected[None,:,:],axis=2)
    assert len(xyz) == len(expected) and distances.min(1).max() < .002
    write_atom_subset(assets / 'ligand.cif', cif, target_indices)
    write_atom_subset(assets / 'small_ligands.cif', cif, small_indices)
    config = {**case, 'contour':float(meta['contour_canonical']), 'origin_center_xyz':origin.tolist(), 'spacing_xyz':spacing.tolist(),
              'shape_zyx':shape.tolist(), 'ligand_xyz':xyz.tolist(), 'gt_coordinate_max_error_angstrom':float(distances.min(1).max()),
              'files':['density.mrc','real_receptor.cif','cryo_receptor.cif','ligand.cif','real_target.mrc','cryo_target.mrc','emap_target.mrc',
                       'gt_area.mrc','real_selected.mrc','cryo_selected.mrc','emap_selected.mrc','small_ligands.cif']}
    (dest / 'data.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{pdb}: coordinate, selection and intersection checks passed', flush=True)
