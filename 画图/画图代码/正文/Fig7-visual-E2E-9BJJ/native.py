"""在独立ChimeraX进程按服务器材料绘制一个完整复合物, 不重算科学评价或修改坐标.

task_scene由正式构建入口传入, 指向本次temp的scene.json. complex.png与内嵌原子模型的complex.cxs写入其output目录; 相机仅采用明确保存的显示参数. 受体CIF与配体SDF均由同次服务器读取生成, 不读取旧作者会话或旧PNG.
"""

import json
import faulthandler
import sys
import os
import runpy
from pathlib import Path
from chimerax.core.commands import run
from chimerax.geometry import Place

diagnostic_root = Path(task_scene).parent
diagnostic_stream = (diagnostic_root / "native-stack.txt").open("w", encoding="utf-8")
faulthandler.dump_traceback_later(90, repeat=True, file=diagnostic_stream)
(diagnostic_root / "native-started.json").write_text(
    json.dumps({"python": sys.version, "scene": task_scene}), encoding="utf-8"
)
if os.environ.get("FIGURE_VERIFY_ROOT"):
    runpy.run_path(
        str(Path(os.environ["FIGURE_VERIFY_ROOT"]) / "TOOLS/figure_runner/guards/sitecustomize.py")
    )
scene = json.loads(Path(task_scene).read_text(encoding="utf-8"))
output = Path(scene["output"])
output.mkdir(parents=True, exist_ok=True)
run(session, "close all")
run(
    session,
    "set bgColor white; camera ortho; lighting soft; lighting depthCue false; graphics silhouettes false; windowsize 1000 760",
)
for model in scene["loads"]:
    run(session, f'open "{model["file"]}" id #{model["id"]}')
    run(session, f'rename #{model["id"]} "{model["name"]}"')
    (diagnostic_root / "native-progress.json").write_text(
        json.dumps({"phase": "loading", "model_id": model["id"]}), encoding="utf-8"
    )
run(session, "hide atoms; hide cartoons; cartoon #1; color #1 #c6cfdb; transparency #1 30 target c")
for model in scene["loads"]:
    if model["kind"] == "receptor":
        continue
    color = (
        "#e69f00" if model["kind"] == "reference" else "#009e73" if model["success"] else "#b56b47"
    )
    run(
        session,
        f'show #{model["id"]} atoms; style #{model["id"]} stick; size #{model["id"]} stickRadius 0.21; color #{model["id"]} {color}',
    )
# 原生窗口尺寸先稳定, 再设定正交相机, 避免加载期间GUI重排重缩放field_width.
(diagnostic_root / "native-progress.json").write_text(
    json.dumps({"phase": "setting_camera"}), encoding="utf-8"
)
run(session, "windowsize 1000 760; wait 2")
view = session.main_view
view.camera.position = Place(matrix=scene["display"]["camera_matrix"])
view.camera.field_width = scene["display"]["field_width"]
run(session, "clip off; wait 2")
run(
    session,
    f'save "{(output/"complex.png").as_posix()}" width {scene["display"]["image_width"]} height {scene["display"]["image_height"]} supersample 2',
)
run(session, f'save "{(output/"complex.cxs").as_posix()}" includeMaps true')
faulthandler.cancel_dump_traceback_later()
diagnostic_stream.close()
(diagnostic_root / "native-progress.json").write_text(
    json.dumps({"phase": "complete"}), encoding="utf-8"
)
