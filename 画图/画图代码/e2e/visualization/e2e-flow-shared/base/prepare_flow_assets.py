"""为本次端到端图集转换基础资产并生成纯原生 ChimeraX 命令.

入口为顺序流程, --case 指定一个已下载完整地图的 PDB. 复制冻结 Top1、参考和受体基础资产, 把完整 exp.npy 以及全部冻结 blob 转成 MRC; 采样值、XYZ spacing 与首体素中心保持不变. 输出 assets、geometry.json 与 <pdb>_reproduce.cxc. Python 不构造三维图形、不修改相机或配色, 外观和导图全部写入可读原生命令.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import numpy as np
import mrcfile

CODE = Path(__file__).resolve().parent
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
OLD = PROJECT / '画图/画图代码/e2e/output/e2e-flow/source'
FROZEN_VIEWS = PROJECT / '画图/画图代码/e2e/output/e2e-flow/views'
OUTPUT = FROZEN_VIEWS/'regenerated'
parser = argparse.ArgumentParser()
parser.add_argument('--case', required=True)
pdb = parser.parse_args().case
old = OLD / pdb
source = OLD / 'source' / pdb
full_source = FROZEN_VIEWS / 'source' / pdb
destination = OUTPUT / pdb
assets = destination / 'assets'
renders = destination / 'renders'
assets.mkdir(parents=True, exist_ok=True)
renders.mkdir(exist_ok=True)
facts = json.loads((old / 'data.json').read_text(encoding='utf-8'))
for name in ['density.mrc', 'ca2_receptor.cif', 'reference.sdf', 'prediction.sdf', 'gt_area.mrc', 'gt_receptor.cif']:
    shutil.copy2(old / 'assets' / name, assets / name)
meta = np.load(full_source / 'exp.npz')
spacing = meta['voxel_size'].astype(float)
first_center = meta['origin'].astype(float) + .5 * spacing
# (Z, Y, X), 完整服务器规范化实验图; 下列 squeeze 只去掉已有单例轴, 不裁图.
full = np.load(full_source / 'exp.npy', mmap_mode='r').squeeze()
with mrcfile.new(assets / 'full_density.mrc', overwrite=True) as handle:
    handle.set_data(np.asarray(full, dtype=np.float32))
    handle.voxel_size = tuple(spacing)
    handle.header.origin = tuple(first_center)
with mrcfile.open(assets / 'full_density.mrc', permissive=True) as handle:
    assert np.array_equal(handle.data, full)
    assert np.allclose(handle.header.origin.tolist(), first_center, atol=2e-5)
blob_archive = np.load(source / 'blobs.npz')
path_trace = {x['source_blob_index']: x for x in facts['trace']}
blob_records = []
for position, bid in enumerate(blob_archive['blob_index']):
    bid = int(bid)
    lo, hi = blob_archive['voxel_offsets'][position:position + 2]
    # (N, 3), 当前冻结 blob 的全局 ZYX 整数索引; N=hi-lo, 不重新分割.
    voxels = blob_archive['voxel_index_global_zyx'][lo:hi]
    lower = np.maximum(voxels.min(0) - 2, 0)
    upper = np.minimum(voxels.max(0) + 3, full.shape)
    sparse = np.zeros(tuple(upper - lower), dtype=np.int8)
    sparse[tuple((voxels - lower).T)] = 1
    name = f'blob_{bid}.mrc'
    with mrcfile.new(assets / name, overwrite=True) as handle:
        handle.set_data(sparse)
        handle.voxel_size = tuple(spacing)
        handle.header.origin = tuple(first_center + lower[::-1] * spacing)
    trace = path_trace.get(bid)
    color = '#cbd0d2'
    if trace:
        color = '#e9983c' if trace['target_scope'] == 'stage3_foreground' else '#9f87a9' if trace['target_scope'] == 'background' else '#b3a290'
    blob_records.append({'source_blob_index': bid, 'model_id': 7 + position, 'file': name, 'voxel_count': len(voxels), 'source_probability_mean': float(blob_archive['source_probability_mean'][position]), 'centroid_world_xyz_A': (first_center + voxels[:, ::-1].mean(0) * spacing).tolist(), 'path_scope': trace['target_scope'] if trace else None, 'color': color})
full_id = 7 + len(blob_records)
target_id = next(x['model_id'] for x in blob_records if x['source_blob_index'] == facts['case']['blob'])
background = next((x for x in blob_records if x['path_scope'] == 'background'), None)
anchor_id = full_id + 1 if background else None
if background:
    xyz = background['centroid_world_xyz_A']
    (assets / 'background_anchor.pdb').write_text(f'ATOM      1  CA  GLY A   1    {xyz[0]:8.3f}{xyz[1]:8.3f}{xyz[2]:8.3f}  1.00  0.00           C  \nEND\n', encoding='ascii')
geometry = {'pdb': pdb, 'full_source_shape_zyx': list(full.shape), 'full_source_dtype': str(full.dtype), 'full_source_corner_xyz_A': meta['origin'].tolist(), 'spacing_xyz_A': spacing.tolist(), 'mrc_first_voxel_center_xyz_A': first_center.tolist(), 'contour_canonical': float(meta['contour_canonical']), 'global_display_grid_step': 1, 'global_camera_fit_entities': {'global_density': 'complete full map array bounds', 'global_structure': 'all CA2 and GT receptor atoms', 'global_find': 'all CA2 and GT receptor atoms plus all frozen blob bounds'}, 'blob_count_original': len(blob_records), 'blobs': blob_records, 'models': {'1': 'local density crop (old frozen data, 16 A margin)', '2': 'complete CA2 receptor tokens', '3': 'deposited target reference', '4': 'same frozen self-ranking Top1 coordinates in all Dock views', '5': 'GT target occurrence area', '6': 'complete GT receptor tokens', str(full_id): 'full server exp.npy converted to MRC'}, 'target_blob_model_id': target_id, 'background_anchor_model_id': anchor_id, 'global_find_annotation': {'kind': 'native ChimeraX model label', 'target_blob_model_id': target_id, 'text': str(facts['handoff']['raw_rank']), 'scientific_coordinates_changed': False}, 'dock_density_style': {'color': '#516773', 'transparency': 0.12}, 'prediction_sha256': hashlib.sha256((assets / 'prediction.sdf').read_bytes()).hexdigest(), 'full_density_source_sha256': next(x['sha256'] for x in json.loads((full_source / 'source.json').read_text()) if x['name'] == 'exp.npy'), 'background_scientific_actions': {'Match': False, 'Dock': False} if background else None}
(destination / 'geometry.json').write_text(json.dumps(geometry, ensure_ascii=False, indent=2), encoding='utf-8')
(destination / 'data.json').write_text(json.dumps(dict(facts, visualization_geometry=geometry), ensure_ascii=False, indent=2), encoding='utf-8')
files = ['density.mrc', 'ca2_receptor.cif', 'reference.sdf', 'prediction.sdf', 'gt_area.mrc', 'gt_receptor.cif'] + [x['file'] for x in blob_records] + ['full_density.mrc'] + (['background_anchor.pdb'] if background else [])
commands = [f'# {pdb.upper()}: 每个视图为一个端到端行动, 所有三维显示均使用 ChimeraX 1.10.1 原生命令.', '# #1-6 沿用旧固定模型顺序, #7起为全部原 blob, 最后为完整实验图.', 'close all']
commands += [f'open "{(assets / name).as_posix()}"' for name in files]
commands += ['set bgColor white', 'camera ortho', 'windowsize 960 720', 'lighting soft', 'material dull', 'graphics silhouettes false', 'hide models', 'hide #2,6 atoms', 'cartoon #2,6', 'color #2,6 #81a58b target c', 'color #2,6 #81a58b target ab', 'transparency #2,6 20 target c', 'hide #3,4 cartoons', 'style #3,4 stick', 'size #3,4 stickRadius 0.20', 'color #3 #26a6a1 target ab', 'color #4 #3169b3 target ab', f'volume #1 style mesh step 1 level {geometry["contour_canonical"]} color #a0a9ad transparency 0.55 squareMesh true meshLighting false', 'volume #5 style mesh step 1 level 0.5 color #26a6a1 transparency 0.20', f'volume #{full_id} style surface step 1 level {geometry["contour_canonical"]} color #8e9ca5 transparency 0.15 surfaceSmoothing false', f'volume #{full_id} region all', f'volume unzone #{full_id}']
commands += [f'volume #{x["model_id"]} style surface step 1 level 0.5 color {x["color"]} transparency 0.05 surfaceSmoothing false' for x in blob_records]
all_blob_spec = '#' + ','.join(str(x['model_id']) for x in blob_records)
commands += ['# 全局相机由完整实验图确定, 不以16A旧裁图代替全图.', f'show #{full_id} models', f'view #{full_id} orient', 'turn y 25', 'turn x -20', f'view #{full_id} pad 0.06', 'clip off', 'view name global', 'view matrix', 'zoom']
commands += ['view name global_density', 'show #2,6 models', 'show #2,6 atoms', 'view #2,6 orient', 'turn y 25', 'turn x -20', 'view #2,6 pad 0.07', 'clip off', 'view name global_structure', 'view matrix', 'zoom', f'view #2,6,' + ','.join(str(x['model_id']) for x in blob_records) + ' pad 0.07', 'clip off', 'view name global_find', 'view matrix', 'zoom', 'hide #2,6 atoms']
for name, specification in [('global_density', f'#{full_id}'), ('global_ca2', '#2'), ('global_gt', '#6,3'), ('global_find', f'#{full_id},2,' + ','.join(str(x['model_id']) for x in blob_records))]:
    commands += ['hide models', f'show {specification} models', f'view {"global_density" if name == "global_density" else "global_structure" if name in ["global_ca2", "global_gt"] else "global_find"}']
    if name == 'global_ca2':
        commands += ['transparency #2 0 target c']
    if name == 'global_find':
        commands += [f'volume #{full_id} transparency 0.78', 'transparency #2 0 target c']
        commands += [f'label #{target_id} models text "{facts["handoff"]["raw_rank"]}" color #ad6515 bgColor white height fixed size 24 offset 4,4,0 onTop true']
    commands += ['wait 2', f'save "{(renders / (name + ".png")).as_posix()}" width 1440 height 1080 supersample 2']
commands += [f'save "{(destination / "global_session.cxs").as_posix()}" includeMaps false', f'label delete #{target_id} models', '# 完整地图保留独立MRC及全局会话外部引用, 局部CXS嵌入所需局部图和所有blob.', f'close #{full_id}', 'hide models', 'hide #2,6 cartoons', 'hide #2,6 atoms', 'show (#2,6 & (#3 :< 6)) atoms', 'style #2,6 stick', 'size #2,6 stickRadius 0.055', 'transparency #2,6 45 target ab', f'show #3,4,{target_id} models', 'view #3 orient', 'turn y 35', 'turn x -25', f'view #3,4,{target_id} pad 0.25', 'clip off', 'view name local', 'view matrix', 'zoom', 'volume zone #1 nearAtoms #3 range 4 newMap false minimalBounds true']
for name, specification in [('local_gt', '#3,5,6'), ('local_find', f'#1,2,{target_id}'), ('blob_alone', f'#{target_id}')]:
    commands += ['hide models', f'show {specification} models', 'view local', 'wait 2', f'save "{(renders / (name + ".png")).as_posix()}" width 1440 height 1080 supersample 2']
commands += ['# Dock三种视图共用冻结Top1和local相机, 不对齐或重新优化.', 'hide models', 'hide #2 atoms', 'cartoon (#2 & (#3 :< 8))', 'transparency #2 68 target c', 'surface (#2 & (#3 :< 6)) enclose (#2 & (#3 :< 6)) color #81a58b transparency 78', 'show #2,4 models', 'view local', 'wait 2', f'save "{(renders / "dock_receptor.png").as_posix()}" width 1440 height 1080 supersample 2', 'hide #2 surfaces', 'hide #2 cartoons', 'hide models', 'volume #1 color #516773 transparency 0.12', 'show #1,4 models', 'view local', 'wait 2', f'save "{(renders / "dock_density.png").as_posix()}" width 1440 height 1080 supersample 2', 'hide models', 'show #3,4 models', 'view local', 'wait 2', f'save "{(renders / "dock_gt_overlay.png").as_posix()}" width 1440 height 1080 supersample 2']
if background:
    background_id = background['model_id']
    commands += ['# 背景先位仅展示GT邻域和CA2+blob, 没有真实Match或Dock调用.', 'hide models', 'hide #2,6 atoms', 'hide #2,6 cartoons', f'show (#2,6 & (#{anchor_id} :< 8)) atoms', 'transparency #2,6 35 target ab', f'show #{background_id} models', f'view #{background_id} orient', 'turn y 35', 'turn x -25', f'view (#2,6 & (#{anchor_id} :< 8)) pad 0.15', 'clip off', 'view name background', 'view matrix', 'zoom', f'volume zone #1 nearAtoms #{anchor_id} range 8 newMap false minimalBounds true']
    for name, specification in [('background_gt', '#6'), ('background_find', f'#1,2,{background_id}'), ('background_blob', f'#{background_id}')]:
        commands += ['hide models', f'show {specification} models', 'view background', 'wait 2', f'save "{(renders / (name + ".png")).as_posix()}" width 1440 height 1080 supersample 2']
commands += ['# 回到目标局部并嵌入所需地图, session.cxs可直接学习/编辑.', 'hide models', 'hide #2,6 atoms', 'show (#2,6 & (#3 :< 6)) atoms', 'volume zone #1 nearAtoms #3 range 4 newMap false minimalBounds true', 'volume #1 transparency 0.55', 'show #1,2,3,4 models', 'view local', f'save "{(destination / "session.cxs").as_posix()}" includeMaps true', f'log save "{(destination / "commands.html").as_posix()}"']
command_dir = PROJECT/'temp/e2e_flow/commands'
command_dir.mkdir(parents=True,exist_ok=True)
(command_dir / f'{pdb}_reproduce.cxc').write_text('\n'.join(commands) + '\n', encoding='utf-8')
print(f'{pdb}: assets and native commands prepared, full shape={full.shape}, {len(blob_records)} blobs', flush=True)
