"""在 ChimeraX 内生成可重新打开的全局会话和共享相机的总览图素材.

从 FIGURE_BUILD_ROOT 读取本次 receptor.pdb、四份 SDF、六份 MRC 和 scene.json.
native/ 保存 A/B/C 三个基础 CXS(内嵌地图), 三种命名视角、全局透明 PNG 与相机、模型编号和投影中心记录; 三档受体透明度由 render_transparent.py 补充.
"""
import json
import os
from pathlib import Path

import numpy as np
from chimerax.core.commands import run
from chimerax.geometry import Place

if os.environ.get('FIGURE_VERIFY_ROOT'):
    import runpy
    runpy.run_path(str(Path(os.environ['FIGURE_VERIFY_ROOT']) / '转换工具/ops/rebuild_support/sitecustomize.py'))


def main(session):
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    native = build / 'native'
    native.mkdir(exist_ok=True)
    root = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
    source = root / '画图/画图代码/e2e/output/overview-redesign-20261028/source'
    scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
    cameras = json.loads((source / 'cameras.json').read_text(encoding='utf8'))
    run(session, 'close all')
    run(session, 'set bgColor white')
    run(session, 'lighting soft')
    run(session, 'graphics silhouettes false')
    run(session, 'camera ortho')
    run(session, 'windowsize 1200 1500')
    run(session, f'open "{(build / "receptor.pdb").as_posix()}"')
    run(session, 'hide #1 atoms')
    receptor_model = next(m for m in session.models.list() if m.id == (1,))
    run(session, 'cartoon #1')
    run(session, 'color #1 #6E8DA2 target c')
    run(session, 'transparency #1 0 target c')
    for number, pose in enumerate(scene['bound_poses'], 2):
        blob = pose['blob']
        identity = next(d for d in scene['identities'] if d['id'] == pose['identity'])
        ligand_model = run(session, f'open "{(build / (blob + ".sdf")).as_posix()}"')[0]
        run(session, f'rename #{number} {blob}-{pose["identity"]}')
        run(session, f'style #{number} ball')
        run(session, f'size #{number} stickRadius 0.26 ballScale 0.24')
        run(session, f'color #{number} {identity["color"]} target a')
        element_colours = {'O': (229, 75, 75, 255), 'N': (58, 86, 207, 255), 'S': (208, 172, 46, 255)}
        for atom in ligand_model.atoms:
            if atom.element.name in element_colours:
                atom.color = element_colours[atom.element.name]
    run(session, f'open "{(build / "maps/density.mrc").as_posix()}"')
    run(session, 'rename #6 Schematic-density')
    run(session, 'volume #6 level 0.17 step 1 style surface color #CAD0D6 transparency 0.88')
    for number, blob in enumerate(['B1', 'B2', 'B3', 'B4', 'B5'], 7):
        colour = next((d['color'] for p in scene['bound_poses'] for d in scene['identities'] if p['blob'] == blob and p['identity'] == d['id']), '#879098')
        run(session, f'open "{(build / "maps" / (blob + ".mrc")).as_posix()}"')
        run(session, f'rename #{number} Candidate-{blob}')
        run(session, f'volume #{number} level 0.20 step 1 color {colour} transparency 0')
        run(session, f'hide #{number} models')
    receptor_xyz = np.array(scene['receptor_xyz'])
    centre = receptor_xyz.mean(0)
    camera = session.main_view.camera
    for name, spec in cameras.items():
        axes = np.array(spec['axes'])
        projected = (receptor_xyz - centre) @ axes.T
        midpoint = (projected.max(0) + projected.min(0)) / 2
        target = centre + midpoint @ axes
        camera.position = Place(axes=axes, origin=target + axes[2] * 150)
        camera.field_width = max(float(np.ptp(projected[:, 0])) + 7, (float(np.ptp(projected[:, 1])) + 7) * 0.8)
        run(session, f'view name {name}')
    run(session, 'view slender')
    run(session, 'view name Fig1')
    manifest = dict(models={'receptor': 1, 'B1': 2, 'B2': 3, 'B4': 4, 'B5': 5, 'density': 6, 'candidate_B1': 7, 'candidate_B2': 8, 'candidate_B3': 9, 'candidate_B4': 10, 'candidate_B5': 11}, cameras=cameras, frame=[1200, 1500], exports={})

    def save_image(name):
        run(session, 'wait 1')
        run(session, f'save "{(native / (name + ".png")).as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
        manifest['exports'][name] = dict(camera_matrix=camera.position.matrix.tolist(), field_width_A=camera.field_width)

    run(session, 'hide #2-5 models')
    run(session, 'hide #1 cartoons')
    run(session, 'volume #6 transparency 0.14')
    save_image('input-density')
    run(session, 'hide #6 models')
    run(session, 'show #1 cartoons')
    save_image('input-receptor')
    run(session, 'show #6 models')
    run(session, 'volume #6 transparency 0.88')
    run(session, 'show #7-11 models')
    save_image('candidate')
    run(session, 'hide #7-11 models')
    run(session, 'show #2-5 models')
    save_image('poses-A')
    run(session, f'save "{(native / "global-A.cxs").as_posix()}" includeMaps true')
    # 原生局部剖切: 只隐藏投影上遮住配体的少量前景 ribbon, 不删除受体原子或移动配体.
    full_ribbons = receptor_model.residues.ribbon_displays.copy()
    camera_inverse = camera.position.inverse()
    ligand_camera = camera_inverse * np.concatenate([np.array(p['xyz']) for p in scene['bound_poses']])
    hidden = []
    residues = list(receptor_model.residues)
    for index, residue in enumerate(residues):
        ca = residue.find_atom('CA')
        if ca is None:
            continue
        point = camera_inverse * ca.scene_coord
        radial = np.linalg.norm(ligand_camera[:, :2] - point[:2], axis=1)
        if np.any((radial < 2.4) & (point[2] > ligand_camera[:, 2] + 0.6)):
            hidden.extend(j for j in range(max(0, index-1), min(len(residues), index+2)) if residues[j].chain_id == residue.chain_id)
    hidden = sorted(set(hidden))
    cutaway_ribbons = full_ribbons.copy()
    cutaway_ribbons[hidden] = False
    receptor_model.residues.ribbon_displays = cutaway_ribbons
    manifest['cutaway_residues'] = [f'{residues[i].chain_id}:{residues[i].number}' for i in hidden]
    save_image('poses-B')
    run(session, f'save "{(native / "global-B.cxs").as_posix()}" includeMaps true')
    # 提供网格表示作为第三个原生会话, 便于作者更明确地区分密度和受体.
    receptor_model.residues.ribbon_displays = full_ribbons
    run(session, 'volume #6 style mesh step 2 meshLighting false color #A8B2BC transparency 0.45')
    save_image('poses-C')
    run(session, f'save "{(native / "global-C-mesh.cxs").as_posix()}" includeMaps true')
    run(session, 'volume #6 style surface step 1 color #CAD0D6 transparency 0.88')
    for name in ['taller', 'open']:
        run(session, f'view {name}')
        save_image('view-' + name)
    run(session, 'view Fig1')
    view = camera.position.inverse()
    points = {blob: view * np.array(xyz) for blob, xyz in scene['blob_centres'].items()}
    fw = camera.field_width
    manifest['projected_blob_centres'] = {blob: [float(600 + xyz[0] / fw * 1200), float(750 - xyz[1] / fw * 1200)] for blob, xyz in points.items()}
    manifest['camera_matrix'] = camera.position.matrix.tolist()
    manifest['field_width_A'] = fw
    for m in session.models.list():
        if len(m.id) == 1:
            m.display = False
    for number, blob in enumerate(['B1', 'B2', 'B3', 'B4', 'B5'], 7):
        run(session, f'show #{number} models')
        destination = build / 'render'
        destination.mkdir(exist_ok=True)
        run(session, f'save "{(destination / ("blob-" + blob + ".png")).as_posix()}" width 1200 height 1500 supersample 2 transparentBackground true')
        run(session, f'hide #{number} models')
    (native / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
    run(session, f'log save "{(native / "chimerax.html").as_posix()}"')
    (build / 'native-completion.json').write_text(json.dumps({'passed':True}), encoding='utf8')


try:
    Path(os.environ['FIGURE_BUILD_ROOT'], 'native-error.txt').unlink(missing_ok=True)
    main(session)
except Exception:
    import traceback
    error = traceback.format_exc()
    Path(os.environ['FIGURE_BUILD_ROOT'], 'native-error.txt').write_text(error, encoding='utf8')
    Path(os.environ['FIGURE_BUILD_ROOT'], 'native-completion.json').write_text(json.dumps({'passed':False, 'error':error}), encoding='utf8')
    raise
