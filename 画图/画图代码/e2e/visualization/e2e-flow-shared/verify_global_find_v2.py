"""核对旧资产未改、v2相机不变和原生排名标签删除产物完整."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
from PIL import Image

PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
V1 = PROJECT / '画图/画图代码/e2e/output/e2e-flow/views'
OUTPUT = PROJECT / '画图/画图代码/e2e/output/e2e-flow/display'
TEMP = PROJECT / 'temp/e2e_flow_v2_20261003'
TEMP.mkdir(parents=True,exist_ok=True)
for record in json.loads((OUTPUT / 'provenance/v1_readonly_baseline.json').read_text(encoding='utf-8')):
    local = record['path'].replace('\\','/').replace('画图/formal/E2E_flow_20261003/','画图/画图代码/e2e/output/e2e-flow/views/')
    assert hashlib.sha256(Path(local).read_bytes()).hexdigest() == record['sha256']
summary = []
for pdb in ['9bjj','30ga','9llg','9rd8','9qru','9wup','9xzl']:
    folder = OUTPUT / pdb
    projection = json.loads((folder / 'projection_boxes.json').read_text(encoding='utf-8'))
    html = (folder / 'commands.html').read_text(encoding='utf-8')
    assert 'class="error"' not in html and 'Unknown command' not in html
    matrix = re.findall(r'view matrix camera ([^<]+)<br>',html)[-1]
    pixel_A = float(re.findall(r'Pixel size at center of rotation is ([^<]+)<br>',html)[-1])
    original = projection['camera_native_logged_values']
    assert matrix == original['native_view_matrix_camera']
    assert pixel_A == original['native_zoom_pixel_size_A']
    old = np.asarray(Image.open(V1 / pdb / 'renders/global_find.png').convert('RGB'))
    new = np.asarray(Image.open(folder / 'renders/global_find.png').convert('RGB'))
    assert old.shape == new.shape == (1080,1440,3)
    difference = np.any(old != new,axis=2)
    positions = np.stack(np.nonzero(difference),axis=1)
    assert len(positions) > 0
    significant = np.max(np.abs(old.astype(int)-new.astype(int)),axis=2) > 16
    significant_positions = np.stack(np.nonzero(significant),axis=1)
    summary.append({'pdb':pdb,'rank_label_deleted_by_native_command':True,'camera_unchanged':True,'camera_native_view_matrix':matrix,'pixel_size_A':pixel_A,'image_wh_px':[1440,1080],'changed_pixel_count':len(positions),'changed_pixels_bbox_xyxy':positions.min(0)[::-1].tolist()+positions.max(0)[::-1].tolist(),'image_sha256':hashlib.sha256((folder / 'renders/global_find.png').read_bytes()).hexdigest(),'v1_inputs_unchanged':True,'projection_box_count':len(projection['boxes'])})
    summary[-1].update({'significant_difference_threshold_per_channel':16,'significant_changed_pixel_count':len(significant_positions),'significant_changed_pixels_bbox_xyxy':significant_positions.min(0)[::-1].tolist()+significant_positions.max(0)[::-1].tolist()})
(TEMP / 'global_find_v2_revalidated.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
