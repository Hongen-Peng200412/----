"""为七例 Input 实验密度生成原生 ChimeraX 同尺度重导命令, 不改变地图或推理.

入口为模块末尾的七例循环. 读取 v1 data.json/camera.json 并生成 <pdb>_global_density_same_scale.cxc; 完整地图模型编号来自 visualization_geometry.models, #1 始终是旧局部裁图.
temp/e2e_flow_v2_20261003/same_scale_density_baseline.json 是 list[dict], 每项含 pdb、v1 路径与 sha256, 用于确认完整地图、旧会话、旧相机和旧 PNG 未改.
"""
from pathlib import Path
import hashlib
import json

PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
CODE = Path(__file__).resolve().parent
V1 = PROJECT / '画图/画图代码/e2e/output/e2e-flow/views'
OUTPUT = PROJECT / '画图/画图代码/e2e/output/e2e-flow/display/regenerated'
TEMP = PROJECT / 'temp/e2e_flow_v2_20261003'

baseline = []
for pdb in ['9llg', '9bjj', '30ga', '9qru', '9rd8', '9wup', '9xzl']:
    data = json.loads((V1 / pdb / 'data.json').read_text(encoding='utf-8'))
    geometry = data['visualization_geometry']
    # 原模型编号按完整地图的来源说明定位, 例如 30GA #26; 不把 #1 的 16 Å 局部图用于 Input.
    full_model = next(int(number) for number, description in geometry['models'].items() if description == 'full server exp.npy converted to MRC')
    target_model = geometry['target_blob_model_id']
    contour = geometry['contour_canonical']
    folder = OUTPUT / pdb
    commands = f'''# {pdb.upper()}: 完整实验地图沿用受体 named view, 同朝向、同原点、同 Å/pixel.
close all
open "{(V1 / pdb / 'global_session.cxs').as_posix()}"
windowsize 960 720
label delete #{target_model} models
hide models
show #{full_model} models
volume #{full_model} style surface step 1 level {contour} color #8e9ca5 transparency 0.15 surfaceSmoothing false
volume #{full_model} region all
volume unzone #{full_model}
view global_structure
clip off
view matrix
zoom
wait 2
save "{(folder / 'renders/global_density_same_scale.png').as_posix()}" width 1440 height 1080 supersample 2
log save "{(folder / 'global_density_same_scale_commands.html').as_posix()}"
'''
    command_dir = TEMP/'commands'
    command_dir.mkdir(parents=True,exist_ok=True)
    (folder/'renders').mkdir(parents=True,exist_ok=True)
    (command_dir / f'{pdb}_global_density_same_scale.cxc').write_text(commands, encoding='utf-8')
    for relative in ['assets/full_density.mrc', 'global_session.cxs', 'camera.json', 'renders/global_density.png', 'renders/global_ca2.png', 'renders/global_gt.png', 'renders/global_find.png']:
        source = V1 / pdb / relative
        baseline.append({'pdb': pdb, 'path': source.as_posix(), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
(TEMP / 'same_scale_density_baseline.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf-8')
print('Prepared seven complete-map same-scale native commands and 49 v1 immutability checks.')
