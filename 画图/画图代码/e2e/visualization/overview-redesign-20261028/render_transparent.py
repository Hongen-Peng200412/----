"""在相同相机下比较 35/55/70% 受体透明度, 密度使用浅灰原生网格.

在 ChimeraX 内执行, 读取本次 native/global-A.cxs; 不读取旧 temp.
native/poses-D*.png、candidate-D*.png 与 global-D35/D55/D70.cxs 为完整受体的半透明备选.
"""
import json
import os
from pathlib import Path
import traceback

from chimerax.core.commands import run

if os.environ.get('FIGURE_VERIFY_ROOT'):
    import runpy
    runpy.run_path(str(Path(os.environ['FIGURE_VERIFY_ROOT']) / '转换工具/ops/rebuild_support/sitecustomize.py'))

build = Path(os.environ['FIGURE_BUILD_ROOT'])
native = build / 'native'
try:
    run(session, f'open "{(native / "global-A.cxs").as_posix()}"')
    # ChimeraX 只显示每像素最前面的透明模型; 密度改成不透明但浅色的疏网格, 受体为唯一透明实体.
    run(session, 'volume #6 style mesh step 3 meshLighting false color #BFC7CF transparency 0')
    manifest = json.loads((native / 'manifest.json').read_text(encoding='utf8'))
    for value in [35,55,70]:
        run(session, f'transparency #1 {value} target c')
        run(session, 'wait 1')
        run(session, f'save "{(native / ("poses-D"+str(value)+".png")).as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
        run(session, f'save "{(native / ("global-D"+str(value)+".cxs")).as_posix()}" includeMaps true')
        camera=session.main_view.camera
        manifest['exports']['poses-D'+str(value)]={'camera_matrix':camera.position.matrix.tolist(),'field_width_A':camera.field_width,'receptor_transparency_percent':value}
        run(session, 'hide #2-5 models')
        run(session, 'show #7-11 models')
        run(session, 'wait 1')
        run(session, f'save "{(native / ("candidate-D"+str(value)+".png")).as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
        run(session, 'hide #7-11 models')
        run(session, 'show #2-5 models')
        if value == 55:
            run(session, 'hide #2-5 models')
            run(session, 'hide #1 cartoons')
            run(session, f'save "{(native / "input-density-D.png").as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
            run(session, 'hide #6 models')
            run(session, 'show #1 cartoons')
            run(session, f'save "{(native / "input-receptor-D.png").as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
            run(session, 'show #6 models')
            run(session, 'show #2-5 models')
    (native / 'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    # CXS 起始缩放适配通常较宽的桌面窗口; Fig1 命名视图仍保存 PPT 的瘦长画布缩放.
    for filename in ['global-A.cxs','global-B.cxs','global-C-mesh.cxs','global-D35.cxs','global-D55.cxs','global-D70.cxs']:
        run(session,f'open "{(native / filename).as_posix()}"')
        session.main_view.camera.field_width=128.0
        run(session,f'save "{(native / filename).as_posix()}" includeMaps true')
    (build / 'native-completion.json').write_text(json.dumps({'passed':True}),encoding='utf8')
except Exception:
    error=traceback.format_exc()
    (build / 'native-completion.json').write_text(json.dumps({'passed':False,'error':error}),encoding='utf8')
    raise
