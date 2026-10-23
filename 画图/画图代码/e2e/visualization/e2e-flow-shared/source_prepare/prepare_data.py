"""把冻结数组与SDF转成ChimeraX能直接打开的基础文件, 不设置相机、颜色或显示风格.

入口为本文件顺序流程, 读取formal/E2E_cases_20261003/source/<pdb>/. 每例输出assets/density.mrc（原值显示裁图）、blob_<编号>.mrc（二值原blob）、gt_area.mrc（二值沉积区域）、ca2_receptor.cif/gt_receptor.cif（完整受体token原子）、reference.sdf（沉积参考）、prediction.sdf（原self-ranking首位世界坐标）和data.json（模型文件顺序、坐标规则与冻结事实）. MRC数组ZYX, header.origin为首体素中心XYZ Å, spacing逐轴读取源元数据. 本文件不重新推理、排序、拟合或计算RMSD.
"""
from pathlib import Path
import json
import numpy as np
import mrcfile
from Bio.PDB.mmcifio import MMCIFIO

CODE = Path(__file__).resolve().parent
FROZEN = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file()) / '画图/画图代码/e2e/output/e2e-flow/source'
OUTPUT = FROZEN/'regenerated'
RESIDUES = 'ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL A C G U DA DC DG DT UNK'.split()
ELEMENTS = {1:'H',6:'C',7:'N',8:'O',9:'F',11:'Na',12:'Mg',15:'P',16:'S',17:'Cl',19:'K',20:'Ca',26:'Fe',30:'Zn',34:'Se'}


def write_volume(path, array, first_center_xyz, spacing_xyz):
    """写一个原采样网格的MRC文件, 不插值、不变换采样值.

    path为输出文件; array为float32/int8 (Z,Y,X); first_center_xyz和spacing_xyz均(3,), 世界XYZ Å. header.origin保存数组[0,0,0]的采样点中心, voxel_size保存XYZ间距. 回读同时核对采样值和首中心, 防止轴顺序或半体素偏移错误.
    """
    with mrcfile.new(path, overwrite=True) as handle:
        handle.set_data(array)
        handle.voxel_size = tuple(spacing_xyz)
        handle.header.origin = tuple(first_center_xyz)
    with mrcfile.open(path) as handle:
        assert np.array_equal(handle.data, array)
        assert np.allclose(handle.header.origin.tolist(), first_center_xyz, atol=2e-5)


def write_sparse(path, voxels_zyx, first_center_xyz, spacing_xyz, source_shape_zyx):
    """将原网格非零体素(N,3)导出为紧致二值MRC, 每个体素及其世界位置不变.

    voxels_zyx是整数ZYX索引, 如[100,110,120]; source_shape_zyx是完整源图(Z,Y,X). 输出外围保留两个零体素, 非零值为1, origin随裁取起点逐轴平移. 这只是格式导出, 不重新分割区域.
    """
    lower = np.maximum(voxels_zyx.min(0) - 2, 0)
    upper = np.minimum(voxels_zyx.max(0) + 3, source_shape_zyx)
    array = np.zeros(tuple(upper - lower), dtype=np.int8)
    array[tuple((voxels_zyx - lower).T)] = 1
    write_volume(path, array, first_center_xyz + lower[::-1] * spacing_xyz, spacing_xyz)
    assert int(array.sum()) == len(np.unique(voxels_zyx, axis=0))


def write_receptor(path, token_path):
    """把实际GT/CA2受体token逐原子写成mmCIF, 不补原子、不改坐标.

    token_path中的coords为(N,3)世界XYZ Å; element、res_type、atom_name、res_index、chain_index均(N,), 与原子一一对应. CIF保留标准残基与原子名称, 以token链编号C0等和res_index+1表示残基; 这些是可视化编号, 不是沉积auth编号. 输出不含配体, 供ChimeraX根据标准残基建立cartoon.
    """
    token = np.load(token_path)
    count = len(token['coords'])
    chains = [f'C{int(x)}' for x in token['chain_index']]
    residues = [str(int(x)+1) for x in token['res_index']]
    names = [x.decode().strip() for x in token['atom_name']]
    fields = {'group_PDB':['ATOM']*count,'id':[str(i+1) for i in range(count)],'type_symbol':[ELEMENTS[int(x)] for x in token['element']], 'label_atom_id':names,'label_alt_id':['.']*count,'label_comp_id':[RESIDUES[int(x)] for x in token['res_type']], 'label_asym_id':chains,'label_entity_id':[str(int(x)+1) for x in token['chain_index']],'label_seq_id':residues,'pdbx_PDB_ins_code':['?']*count,'occupancy':['1']*count,'B_iso_or_equiv':['0']*count,'auth_seq_id':residues,'auth_asym_id':chains,'pdbx_PDB_model_num':['1']*count}
    fields.update({f'Cartn_{axis}':[f'{x:.5f}' for x in token['coords'][:,i]] for i,axis in enumerate('xyz')})
    writer = MMCIFIO()
    writer.set_dict({'data_':path.stem,**{'_atom_site.'+key:value for key,value in fields.items()}})
    writer.save(str(path))


# ================================================================================================
all_cases = []
for case in json.loads((CODE/'cases.json').read_text(encoding='utf-8')):
    pdb = case['pdb']
    source, destination = FROZEN/'source'/pdb, OUTPUT/pdb
    assets = destination/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    (destination/'renders').mkdir(exist_ok=True)
    facts = json.loads((source/'facts.json').read_text(encoding='utf-8'))
    meta = np.load(source/'exp.npz')
    crop = json.loads((source/'exp_crop.json').read_text())
    # (3,), 源元数据的角点原点和实际XYZ间距; +0.5仅用于MRC采样中心, 原子不移动.
    spacing = meta['voxel_size'].astype(float)
    first_center = meta['origin'].astype(float) + .5*spacing
    start_zyx = np.asarray(crop['start_zyx'])
    write_volume(assets/'density.mrc', np.load(source/'exp_crop.npy'), first_center+start_zyx[::-1]*spacing, spacing)
    blob_archive = np.load(source/'blobs.npz')
    blob_files, blob_details = [], []
    for trace in facts['trace']:
        bid = trace['source_blob_index']
        pos = int(np.flatnonzero(blob_archive['blob_index']==bid)[0])
        lo, hi = blob_archive['voxel_offsets'][pos:pos+2]
        # (N,3), 该blob的原网格ZYX索引; 区间同时对齐source_probability等逐体素字段.
        voxels = blob_archive['voxel_index_global_zyx'][lo:hi]
        filename = f'blob_{bid}.mrc'
        write_sparse(assets/filename, voxels, first_center, spacing, np.asarray(crop['source_shape_zyx']))
        blob_files.append(filename)
        blob_details.append({'source_blob_index':bid,'raw_rank':trace['raw_rank'],'attempt_index':trace['attempt_index'],'scope':trace['target_scope'],'probability_mean':float(blob_archive['source_probability_mean'][pos]),'voxel_count':len(voxels)})
    area = np.load(source/'gt_area.npz')[f"mask_{facts['handoff']['matched_occurrence_id']}"]
    write_sparse(assets/'gt_area.mrc', area, first_center, spacing, np.asarray(crop['source_shape_zyx']))
    write_receptor(assets/'ca2_receptor.cif', source/'ca2_receptor.npz')
    write_receptor(assets/'gt_receptor.cif', source/'gt_receptor.npz')
    (assets/'reference.sdf').write_bytes((source/'reference.sdf').read_bytes())
    # sdf_index索引原poses.sdf中的成功构象顺序, 不等同于sample_index; 使用冻结ranking里的对应字段.
    blocks = (source/'poses.sdf').read_text().split('$$$$')
    top_block = blocks[facts['top1']['sdf_index']]
    # 分隔符之后仅去掉一个记录分隔换行; RDKit空白标题行仍必须保留, 否则counts行会错位.
    if facts['top1']['sdf_index'] > 0:
        top_block = top_block.removeprefix('\n')
    (assets/'prediction.sdf').write_text(top_block+'$$$$\n',encoding='utf-8')
    files = ['density.mrc','ca2_receptor.cif','reference.sdf','prediction.sdf','gt_area.mrc','gt_receptor.cif']+blob_files
    facts.update({'files':files,'blobs':blob_details,'contour':float(meta['contour_canonical']),'density_grid':{'source_corner_xyz_A':meta['origin'].tolist(),'spacing_xyz_A':spacing.tolist(),'crop_start_zyx':start_zyx.tolist(),'first_center_xyz_A':(first_center+start_zyx[::-1]*spacing).tolist()},'predicted_sdf_index':facts['top1']['sdf_index']})
    (destination/'data.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
    all_cases.append({'pdb':pdb,'blob':case['blob'],'group':case['group'],'role':case['role'],'rmsd_A':facts['method']['pose_min_rmsd_A']['1'],'identity_count':len(facts['prediction']['identity_smiles']),'small_identity_count':sum(facts['prediction']['small_molecule_answer_mask']),'components':facts['target_occurrence']['components']})
    print(pdb+': standard assets prepared',flush=True)
(OUTPUT/'cases_summary.json').write_text(json.dumps(all_cases,ensure_ascii=False,indent=2),encoding='utf-8')
