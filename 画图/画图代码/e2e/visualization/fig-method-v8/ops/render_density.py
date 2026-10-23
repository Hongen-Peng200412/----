"""从同一 9LLG 实验图渲染受体 C1 链周围的灰色密度, 保留原受体视角."""
import os
from pathlib import Path
import hashlib
import json

import pymol2
import numpy as np
from PIL import Image

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
SOURCE = ROOT / '画图/画图代码/e2e/output/fig-method-v8'
B = Path(os.environ["FIGURE_RENDER_ROOT"]) / "." if "FIGURE_RENDER_ROOT" in os.environ else ROOT / 'temp/fig-method-v8/rendered'
B.mkdir(parents=True, exist_ok=True)
CASE = ROOT / '画图/画图代码/e2e/output/e2e-flow/views/9llg'
assets = CASE / 'assets'
view_record = json.loads((SOURCE / 'receptor-9llg/receptor_views.json').read_text(encoding='utf-8'))
geometry = json.loads((CASE / 'geometry.json').read_text(encoding='utf-8'))
level = geometry['contour_canonical']
map_path = assets / 'full_density.mrc'
map_hash = hashlib.sha256(map_path.read_bytes()).hexdigest()
source_path = CASE.parent / 'source/9llg/exp.npy'
source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
assert source_hash == geometry['full_density_source_sha256']
source_grid = np.load(source_path, mmap_mode='r')[0]
mrc_grid = np.fromfile(map_path, dtype='<f4', offset=1024).reshape(geometry['full_source_shape_zyx'])
assert np.array_equal(source_grid, mrc_grid)
with pymol2.PyMOL() as pm:
    c = pm.cmd
    c.set('normalize_ccp4_maps', 0)
    c.load(str(assets / 'ca2_receptor.cif'), 'receptor')
    c.select('shown', 'receptor and chain C1 and polymer.protein')
    c.load(str(map_path), 'experimental_map')
    c.isosurface('density_surface', 'experimental_map', level, selection='shown', buffer=3.5, carve=3.5)
    c.hide('everything')
    c.show('surface', 'density_surface')
    c.set_color('density_gray', [.78, .81, .83])
    c.color('density_gray', 'density_surface')
    c.set('antialias', 2)
    c.set('ray_trace_mode', 0)
    c.set('ray_shadows', 0)
    c.set('ambient', .66)
    c.set('direct', .48)
    c.set('specular', .10)
    c.set('two_sided_lighting', 1)
    c.set('ray_interior_color', 'density_gray')
    c.set('ray_interior_shadows', 0)
    c.set('surface_smooth_edges', 1)
    c.set('orthoscopic', 1)
    c.bg_color('white')
    c.set('ray_opaque_background', 0)
    c.viewport(1800, 1800)
    c.set_view(view_record['views']['final'])
    c.png(str(B / 'density_corresponding.png'), 1800, 1800, dpi=600, ray=1)
    c.save(str(B / 'density_corresponding.pse'))
    # 与最终嵌入图一致：按透明通道外包框裁切，并在四边保留24像素。
    with Image.open(B / 'density_corresponding.png') as image:
        left, top, right, bottom = image.getchannel('A').getbbox()
        image.crop((left - 24, top - 24, right + 24, bottom + 24)).save(B / 'density_corresponding_cropped.png')
    report = {'case': '9LLG', 'receptor': 'ca2_receptor.cif', 'chain': 'C1', 'map': 'full_density.mrc', 'map_sha256': map_hash, 'source_array_sha256': source_hash, 'source_array_equals_mrc': True, 'experimental_map_native_isolevel': level, 'carve_radius_A': 3.5, 'selected_atoms': c.count_atoms('shown'), 'camera_view': list(c.get_view()), 'original_camera_view': view_record['views']['final'], 'unchanged_rotation': list(c.get_view())[:9] == view_record['views']['final'][:9], 'coordinate_changes': False, 'map_value_changes': False}
    (B / 'density_provenance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
