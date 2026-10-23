"""从当前 ChimeraX 视角导出绘图几何, 只读冻结9HJX资产, 新几何和会话写temp/fig-overview_v2/."""
import os
from pathlib import Path
import json
import numpy as np
from chimerax.core.commands import run
from chimerax.map import Volume

paper = next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file() and (p/'论文草稿.md').is_file())
root = paper/'画图/画图代码/e2e/output/fig-overview_v2'
build = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else paper/'temp/fig-overview_v2'
build.mkdir(parents=True,exist_ok=True)
run(session, 'open "' + str(root / '素材/raw/rcsb_mmcif/9hjx.cif') + '"')
run(session, 'hide #2 atoms; cartoon #2; color #2 #94a3ad; volume #1 transparency 65; lighting simple')
run(session, 'view #1; wait 2')
camera = session.main_view.camera.position.inverse()
volume = next(m for m in session.models.list() if isinstance(m, Volume))
surface = volume.surfaces[0]
vertices = camera.transform_points(surface.scene_position.transform_points(surface.vertices))
triangles = surface.triangles
normals = camera.transform_vectors(surface.scene_position.transform_vectors(surface.normals))
chains = []
for model in session.models.list():
    if not hasattr(model, 'atoms'):
        continue
    for chain in model.chains:
        ca = []
        for residue in chain.existing_residues:
            atom = residue.find_atom('CA') or residue.find_atom('P')
            if atom is not None:
                point = camera.transform_points(np.array([atom.scene_coord]))[0]
                ca.append([*point.tolist(), int(residue.ss_type)])
        if len(ca) > 2:
            chains.append(ca)
result = {'vertices': vertices.tolist(), 'triangles': triangles.tolist(),
          'normals': normals.tolist(), 'chains': chains,
          'source': '9hjx, AdaLigand experimental density, Gaussian sigma 1.5 voxels, level 2.6, step 3'}
(build / 'geometry.json').write_text(json.dumps(result), encoding='utf-8')
run(session, 'save "' + str(build / 'chimerax_reference.png') + '" width 1400 height 1100 supersample 2')
run(session, 'save "' + str(build / 'figure_a_scene.cxs') + '"')
session.logger.info('Figure A geometry exported: %d triangles, %d chains' % (len(triangles), len(chains)))
