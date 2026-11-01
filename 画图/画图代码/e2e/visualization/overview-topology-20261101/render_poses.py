"""在 ChimeraX 原场景中替换四个位点的示意配体, 保持相机、受体和密度显示.

FIGURE_BUILD_ROOT 提供本次 SDF; 原生会话取自冻结 source/baseline.cxs.
poses.png 沿用原 1200×1500 画幅和 Fig1 相机, topology.cxs 打开为全局画面.
"""
import json
import os
from pathlib import Path

from chimerax.core.commands import run

if os.environ.get('FIGURE_VERIFY_ROOT'):
    import runpy
    runpy.run_path(str(Path(os.environ['FIGURE_VERIFY_ROOT']) / '转换工具/ops/rebuild_support/sitecustomize.py'))

build = Path(os.environ['FIGURE_BUILD_ROOT'])
root = Path(__file__).resolve().parents[5]
source = root / '画图/画图代码/e2e/output/overview-topology-20261101/source'
scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
run(session, f'open "{(source / "baseline.cxs").as_posix()}"')
run(session, 'windowsize 1200 1500')
run(session, 'view Fig1')
run(session, 'close #2-5')
models = []
for pose in scene['bound_poses']:
    identity = next(i for i in scene['identities'] if i['id'] == pose['identity'])
    model = run(session, f'open "{(build / (pose["blob"] + ".sdf")).as_posix()}"')[0]
    spec = model.atomspec
    run(session, f'rename {spec} {pose["blob"]}-{identity["id"]}')
    run(session, f'style {spec} ball')
    run(session, f'size {spec} stickRadius 0.26 ballScale 0.24')
    run(session, f'color {spec} {identity["color"]} target a')
    # 右侧保持原本的元素着色习惯; 身份栏则由 PyMOL 使用单一材质.
    for atom in model.atoms:
        if atom.element.name == 'O':
            atom.color = (229, 75, 75, 255)
    models.append(model.id_string)
run(session, 'wait 1')
run(session, f'save "{(build / "poses.png").as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
(build / 'native.json').write_text(json.dumps(dict(camera=session.main_view.camera.position.matrix.tolist(),
    field_width_A=session.main_view.camera.field_width, models=models)), encoding='utf8')
session.main_view.camera.field_width = 128
run(session, f'save "{(build / "topology.cxs").as_posix()}" includeMaps true')
