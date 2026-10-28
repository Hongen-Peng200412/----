"""在独立 ChimeraX 中执行明文 CXC, 保存六视角的只读相机与边界记录. 

命令: runscript 本脚本 案例输出目录. 科学材料和外观均由 initial.cxc 与 commands/*.cxc 控制; Python 只分发原生命令并读取场景状态, 不直接设置相机或模型属性. view_state.json 保存相机矩阵、窗口大小、Å/像素和归一化定位框. 
"""
from pathlib import Path
import json
import os
import runpy
import sys
import traceback

import numpy as np
from chimerax.core.commands import run


# ================================================================================================
# destination 是 make_scenes.py 生成的单例原生命令及最终会话目录. 
destination=Path(sys.argv[1])
guard_active=False
if os.environ.get('FIGURE_VERIFY_ROOT'):
    # ChimeraX 内置解释器显式启用同一文件审计, 使完整重建不能偷读旧 temp. 
    audit=runpy.run_path(str(Path(os.environ['FIGURE_VERIFY_ROOT'])/'转换工具/ops/rebuild_support/sitecustomize.py'))
    guard_active='workspace' in audit
states={}
try:
    run(session,f'open "{(destination/"initial.cxc").as_posix()}"')
    for script in sorted((destination/'commands').glob('*.cxc')):
        run(session,f'open "{script.as_posix()}"')
        camera=session.main_view.camera.position.matrix
        window=list(session.main_view.window_size)
        pixel=float(session.main_view.pixel_size())
        boxes={}
        if script.stem in ('a_reference','b_emap_global','c_ca2_global'):
            # 定位框必须应用 native turn 的显示变换, 不能把未旋转的科学坐标直接投到截图. 
            for tag,ids in [('fp',(12,)),('tp',(9,10,11))]:
                corners=[]
                for model in session.models.list():
                    if model.id not in [(i,) for i in ids]: continue
                    # 隐藏地图的 bounds() 为空; 从完整MRC网格的八角读取边界, 再应用原生显示变换. 
                    size=model.data.size
                    # indices 为 (8, 3) 的 XYZ 网格角点索引; xyz 为模型局部坐标, 单位 Å.
                    indices=np.array([[x,y,z] for x in (0,size[0]-1) for y in (0,size[1]-1) for z in (0,size[2]-1)])
                    xyz=np.asarray(model.data.origin)+indices*np.asarray(model.data.step)
                    transform=model.scene_position.matrix
                    # transform 为 (3, 4); 三维局部点乘旋转矩阵再加平移, 得到 native turn 后的场景坐标.
                    corners.append(xyz@transform[:,:3].T+transform[:,3])
                corners=np.concatenate(corners)
                # (N_corner, 3), 场景坐标到相机坐标; 归一化 uv 为 (N_corner, 2), 左上原点且 y 向下.
                camera_xyz=(corners-camera[:,3])@camera[:,:3]
                uv=np.column_stack((0.5+camera_xyz[:,0]/(pixel*window[0]),0.5-camera_xyz[:,1]/(pixel*window[1])))
                boxes[tag]=[uv.min(axis=0).tolist(),uv.max(axis=0).tolist()]
        states[script.stem]={'camera_matrix':camera.tolist(),'window_size':window,'pixel_size_A':pixel,'boxes_fraction':boxes}
    # 共同比较的相机是本图科学契约; 显隐变化不能使自动 fit 悄悄改变视角或尺度. 
    for group in [('a_reference','b_emap_global','c_ca2_global'),('e_emap_local','f_ca2_local')]:
        for name in group[1:]:
            np.testing.assert_allclose(states[name]['camera_matrix'],states[group[0]]['camera_matrix'],atol=1e-7,rtol=0)
            np.testing.assert_allclose(states[name]['pixel_size_A'],states[group[0]]['pixel_size_A'],atol=1e-9,rtol=0)
            assert states[name]['window_size']==states[group[0]]['window_size']
    report={'success':True,'shared_cameras_verified':True,'old_temp_read_guard':guard_active,'views':states,'models':[{ 'id':m.id_string,'name':m.name} for m in session.models.list() if len(m.id)==1]}
except Exception:
    report={'success':False,'views':states,'traceback':traceback.format_exc()}
finally:
    (destination/'view_state.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    run(session,f'log save "{(destination/"chimerax.html").as_posix()}"')
if not report['success']: raise RuntimeError(report['traceback'])
