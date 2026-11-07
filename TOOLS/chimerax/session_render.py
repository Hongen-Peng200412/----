"""用独立原生进程只读重开调用方指定的会话, 渲染及诊断全部写本次temp.

本工具不选PDB、实验、会话版本、科学阈值或相机. 会话路径、图幅与可选窗口尺寸均由Figure调用者显式提供; 不保存或改写源CXS.
"""

import hashlib
import json
from pathlib import Path
import subprocess


def render_sessions(paths, output, width, height, window_size):
    """逐个重开原会话并完整读取内嵌地图, 保存PNG和显示/地图读取凭据.

    paths: list[Path], 明确的作者原件. output: Path, 本次temp目录. width/height: int, PNG像素数.
    window_size: tuple[int,int]或None, 调用者明确要求的窗口尺寸.
    本次产物:
        - sessions.json: dict, paths为原件绝对地址列表, output为本次目录, width/height为像素数, window_size为明确窗口尺寸或None.
        - opened.json: list[dict], 每项记录一个本次重开会话.
            - source/models: str/int, 原件地址与加载模型数.
            - camera_matrix: (3,4)相机Place矩阵, 前3列为旋转基、末列为世界XYZ/Å平移.
            - camera_name: str, 相机类型.
            - maps: list[dict], 每项对应完整读取的一幅地图, 图元科学语义由调用方说明.
                - id/name: str, 原模型编号与名称.
                - shape/dtype/sha256: (Z,Y,X)数组形状、原dtype及完整数组字节摘要.
                - origin/step: 各为(3,)世界XYZ/Å的网格原点与步长.
        - view_<序号>.png: 本次原生渲染, 尺寸由width/height决定.
        - source_cxs_sha256.json: dict[str,str], 原件绝对地址到前后相同摘要的映射.
    render.py及进程stdout/stderr只供本次验收; 不保存源CXS、不关闭用户窗口、不写D加工文件.
    """
    output.mkdir(parents=True, exist_ok=True)
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    config = dict(
        paths=[str(path.resolve()) for path in paths],
        output=str(output.resolve()),
        width=width,
        height=height,
        window_size=window_size,
    )
    (output / "sessions.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    script = output / "render.py"
    script.write_text(
        """from pathlib import Path
import json,hashlib
import numpy as np
from chimerax.core.commands import run
from chimerax.map import Volume
config=json.loads(Path(__CONFIG__).read_text(encoding='utf-8'))
reports=[]
for index,path in enumerate(config['paths'],1):
    run(session,'close all')
    run(session,'open "'+Path(path).as_posix()+'"')
    if config['window_size']:
        run(session,'windowsize '+' '.join(map(str,config['window_size'])))
    run(session,'wait 2')
    maps=[]
    for model in session.models.list(type=Volume):
        matrix=np.asarray(model.data.full_matrix())
        maps.append(dict(id=model.id_string,name=model.name,shape=list(matrix.shape),dtype=str(matrix.dtype),sha256=hashlib.sha256(matrix.tobytes()).hexdigest(),origin=[float(v) for v in model.data.origin],step=[float(v) for v in model.data.step]))
    target=Path(config['output'])/('view_%02d.png'%index)
    run(session,'save "'+target.as_posix()+'" width '+str(config['width'])+' height '+str(config['height'])+' supersample 1')
    reports.append(dict(source=path,models=len(session.models.list()),maps=maps,camera_matrix=session.main_view.camera.position.matrix.tolist(),camera_name=session.main_view.camera.name))
    (Path(config['output'])/'opened.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
""".replace(
            "__CONFIG__", repr(str((output / "sessions.json").resolve()))
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(__file__).with_name("run_chimerax.ps1")),
            "-CxcPath",
            str(script.resolve()),
            "-LogPrefix",
            str((output / "render").resolve()),
        ],
        check=True,
    )
    if len(list(output.glob("view_*.png"))) != len(paths) or not (output / "opened.json").is_file():
        raise RuntimeError("原生会话未全部重开并渲染: " + str(output))
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    assert before == after, "原作者会话字节发生变化"
    (output / "source_cxs_sha256.json").write_text(
        json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8"
    )
