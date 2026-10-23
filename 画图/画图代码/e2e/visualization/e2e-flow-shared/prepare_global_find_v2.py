"""为本次图集生成无排名标签的原生 Find 复现命令及冻结 blob 投影框.

入口为顺序流程. 七例只读取 v1 全局会话、原相机日志与冻结 blobs.npz; CXC 只删除目标模型的原生排名标签, 不设新相机、不变换模型或修改阈值. projection_boxes.json 记录 1440x1080 PNG 上的体素中心、半体素支撑包围范围与 PPT 彩框建议; 后者仅为显示关联, 不表示新 Find 检测范围.
"""
from pathlib import Path
import hashlib
import json
import numpy as np

CODE = Path(__file__).resolve().parent
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
V1 = PROJECT / '画图/画图代码/e2e/output/e2e-flow/views'
SOURCE = PROJECT / '画图/画图代码/e2e/output/e2e-flow/source/source'
OUTPUT = PROJECT / '画图/画图代码/e2e/output/e2e-flow/display/regenerated'
TEMP = PROJECT / 'temp/e2e_flow_v2_20261003'
TEMP.mkdir(parents=True, exist_ok=True)
all_boxes = []
baseline = []
for pdb in ['9bjj','30ga','9llg','9rd8','9qru','9wup','9xzl']:
    previous = V1 / pdb
    folder = OUTPUT / pdb
    (folder / 'renders').mkdir(parents=True, exist_ok=True)
    geometry = json.loads((previous / 'geometry.json').read_text(encoding='utf-8'))
    facts = json.loads((previous / 'data.json').read_text(encoding='utf-8'))
    camera = json.loads((previous / 'camera.json').read_text(encoding='utf-8'))['global_find']
    matrix = np.array([float(x) for x in camera['native_view_matrix_camera'].split(',')]).reshape(3,4)
    window_pixel_A = camera['native_zoom_pixel_size_A']
    export_ratio = 1440 / 960
    spacing = np.array(geometry['spacing_xyz_A'])
    first_center = np.array(geometry['mrc_first_voxel_center_xyz_A'])
    archive = np.load(SOURCE / pdb / 'blobs.npz')
    scopes = [('target',facts['case']['blob'],facts['handoff']['raw_rank'])]
    if pdb in ['30ga','9qru']:
        background = next(x for x in facts['trace'] if x['target_scope'] == 'background')
        scopes.append(('background',background['source_blob_index'],background['raw_rank']))
    boxes = []
    for role,bid,rank in scopes:
        position = int(np.flatnonzero(archive['blob_index'] == bid)[0])
        lo,hi = archive['voxel_offsets'][position:position+2]
        # (N,3), 原全局网格 ZYX 索引转为世界 XYZ 体素中心, N=hi-lo; spacing 保留原逐轴值.
        xyz = first_center + archive['voxel_index_global_zyx'][lo:hi,::-1] * spacing
        plane = (xyz - matrix[:,3]) @ matrix[:,:3]
        pixels = np.stack([720 + plane[:,0] / window_pixel_A * export_ratio,540 - plane[:,1] / window_pixel_A * export_ratio],axis=1)
        lower,upper = pixels.min(0),pixels.max(0)
        # 二值 blob 的 0.5 等值面包含在每个非零体素的半体素支撑包络内; 该保守包络不重新分割 blob.
        half_extent = .5 * (spacing @ np.abs(matrix[:,:2])) / window_pixel_A * export_ratio
        envelope_lower,envelope_upper = lower-half_extent,upper+half_extent
        margin = 24.0
        box_lower,box_upper = envelope_lower-margin,envelope_upper+margin
        # 80px 最小显示框便于小面板连线; 实际外扩逐边记录, 不把显示框解释成算法候选区域.
        midpoint = (box_lower+box_upper)/2
        half_size = np.maximum((box_upper-box_lower)/2,40.0)
        box_lower = np.maximum(midpoint-half_size,[0,0])
        box_upper = np.minimum(midpoint+half_size,[1440,1080])
        assert (envelope_lower > 0).all() and (envelope_upper < [1440,1080]).all()
        color = '#e9983c' if role == 'target' else '#9f87a9'
        boxes.append({'role':role,'source_blob_index':int(bid),'raw_rank':int(rank),'model_id':next(x['model_id'] for x in geometry['blobs'] if x['source_blob_index']==bid),'source_voxel_count':int(hi-lo),'color':color,'centroid_world_xyz_A':xyz.mean(0).tolist(),'centroid_export_xy_px':pixels.mean(0).tolist(),'voxel_centers_bbox_xyxy_px':lower.tolist()+upper.tolist(),'voxel_halfcell_envelope_bbox_xyxy_px':envelope_lower.tolist()+envelope_upper.tolist(),'suggested_box_xyxy_px':box_lower.tolist()+box_upper.tolist(),'requested_pixel_margin':margin,'minimum_display_box_wh_px':[80,80],'actual_margin_ltrb_px':(envelope_lower-box_lower).tolist()+(box_upper-envelope_upper).tolist(),'all_frozen_voxel_support_in_frame':True,'algorithm_detection_scope_changed':False})
    record = {'pdb':pdb,'image_size_px':[1440,1080],'window_size_px':[960,720],'source_global_session':str(previous / 'global_session.cxs'),'camera_source':str(previous / 'camera.json'),'camera_name':'global_find','camera_native_logged_values':camera,'projection_coordinates':'PNG top-left origin; x right; y down; [left,top,right,bottom]','projection_precision':'Native view matrix is printed with about 5 significant digits and zoom with 3; bounds are nominal projections from these recorded values, with explicit 24px margin and minimum 80px display box.','projection_method':'Frozen voxel centers plus conservative half-voxel support envelope projected by the unchanged orthographic camera; no Find inference or resegmentation.','rank_labels_removed_natively':True,'boxes':boxes}
    (folder / 'projection_boxes.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    all_boxes.append(record)
    commands = [f'# {pdb.upper()} v2: 仅删除原生目标排名标签, 保留完整地图/CA2/全部blob/原相机.', 'close all',f'open "{(previous / "global_session.cxs").as_posix()}"','windowsize 960 720','view global_find',f'label delete #{geometry["target_blob_model_id"]} models','view matrix','zoom','wait 2',f'save "{(folder / "renders/global_find.png").as_posix()}" width 1440 height 1080 supersample 2',f'save "{(folder / "global_session.cxs").as_posix()}" includeMaps false',f'log save "{(folder / "commands.html").as_posix()}"']
    command_dir = TEMP/'commands'
    command_dir.mkdir(parents=True,exist_ok=True)
    (command_dir / f'{pdb}_global_find.cxc').write_text('\n'.join(commands)+'\n',encoding='utf-8')
    for name in ['global_session.cxs','camera.json','renders/global_find.png']:
        path = previous / name
        baseline.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(OUTPUT / 'projection_boxes_manifest.json').write_text(json.dumps(all_boxes,ensure_ascii=False,indent=2),encoding='utf-8')
(TEMP / 'v1_readonly_baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
print('Seven native label-removal CXC and nine frozen-blob projection boxes prepared.')
