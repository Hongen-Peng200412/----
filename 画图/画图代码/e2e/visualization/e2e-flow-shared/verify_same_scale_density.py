"""核对完整地图重导的原生日志、相机与旧源哈希, 记录 Input 三图同尺度事实.

入口为七例循环. 不控制三维场景或修改源数据, 仅读取 PNG、原生命令日志和旧相机.
<v2>/<pdb>/same_scale_density_camera.json 与 <v2>/same_scale_density_manifest.json 保存 dict 与 list[dict]: pdb、full_map_model_id、camera_native_logged_values、matches_global_ca2_gt_camera、full_map_region、scientific_geometry_unchanged、旧源哈希核查、1440×1080 PNG 尺寸和路径.
"""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
V1 = PROJECT / '画图/画图代码/e2e/output/e2e-flow/views'
OUTPUT = PROJECT / '画图/画图代码/e2e/output/e2e-flow/display'
TEMP = PROJECT / 'temp/e2e_flow_v2_20261003'
TEMP.mkdir(parents=True,exist_ok=True)
for record in json.loads((OUTPUT / 'provenance/same_scale_density_baseline.json').read_text(encoding='utf-8')):
    local = record['path'].replace('\\','/').replace('画图/formal/E2E_flow_20261003/','画图/画图代码/e2e/output/e2e-flow/views/')
    assert hashlib.sha256(Path(local).read_bytes()).hexdigest() == record['sha256']

summary = []
for pdb in ['9llg', '9bjj', '30ga', '9qru', '9rd8', '9wup', '9xzl']:
    folder = OUTPUT / pdb
    data = json.loads((V1 / pdb / 'data.json').read_text(encoding='utf-8'))
    geometry = data['visualization_geometry']
    camera = json.loads((V1 / pdb / 'camera.json').read_text(encoding='utf-8'))['global_structure']
    full_model = next(int(number) for number, description in geometry['models'].items() if description == 'full server exp.npy converted to MRC')
    html = (folder / 'global_density_same_scale_commands.html').read_text(encoding='utf-8')
    assert 'class="error"' not in html and 'Unknown command' not in html
    matrix = re.findall(r'view matrix camera ([^<]+)<br>', html)[-1]
    pixel_A = float(re.findall(r'Pixel size at center of rotation is ([^<]+)<br>', html)[-1])
    assert matrix == camera['native_view_matrix_camera']
    assert pixel_A == camera['native_zoom_pixel_size_A']
    image = folder / 'renders/global_density_same_scale.png'
    assert Image.open(image).size == (1440, 1080)
    record = {'pdb': pdb, 'full_map_model_id': full_model, 'full_source_shape_zyx': geometry['full_source_shape_zyx'], 'full_source_sha256': geometry['full_density_source_sha256'], 'full_map_asset_path': (V1 / pdb / 'assets/full_density.mrc').as_posix(), 'full_map_region': 'all; unzone; step 1; unchanged source contour_canonical', 'contour_canonical': geometry['contour_canonical'], 'camera_native_logged_values': {'native_view_matrix_camera': matrix, 'native_zoom_pixel_size_A': pixel_A, 'window_wh_pixels': [960, 720], 'export_wh_pixels': [1440, 1080]}, 'matches_global_ca2_gt_camera': True, 'scientific_geometry_unchanged': True, 'v1_49_source_hash_checks_passed': True, 'png_path': image.as_posix(), 'png_sha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'native_log_path': (folder / 'global_density_same_scale_commands.html').as_posix(), 'same_input_ppt_crop_required': 'use same structureCrop and frame dimensions for density, CA2 and GT; presentation crop may omit peripheral speckles'}
    report_dir=TEMP/'revalidated'/pdb
    report_dir.mkdir(parents=True,exist_ok=True)
    (report_dir / 'same_scale_density_camera.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    summary.append(record)
(TEMP / 'same_scale_density_revalidated.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{'pdb': x['pdb'], 'full_model': x['full_map_model_id'], 'same_A_per_pixel': x['camera_native_logged_values']['native_zoom_pixel_size_A'], 'camera_match': x['matches_global_ca2_gt_camera']} for x in summary], ensure_ascii=False, indent=2))
