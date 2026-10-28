"""把本次原生会话、坐标和已维护的教程组装成可独立使用的编辑包.

主入口 main 仅写 FIGURE_BUILD_ROOT/editing-package; 不发布正式 PPT.
assets/ 保存身份和坐标轴契约, CXS 内嵌全部地图; 同步导出.py 为长期入口的本次复制品.
"""
import json
import os
from pathlib import Path
import shutil


def main():
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    code = Path(__file__).resolve().parent
    package = build / 'editing-package'
    assets = package / 'assets'
    examples = package / 'examples'
    assets.mkdir(parents=True, exist_ok=True)
    examples.mkdir(exist_ok=True)
    session_pairs=[('global-A.cxs','A_完整受体.cxs'), ('global-B.cxs','B_局部剖切.cxs'), ('global-C-mesh.cxs','C_密度网格.cxs')]+[(f'global-D{value}.cxs',f'D{value}_完整受体半透明.cxs') for value in [35,55,70]]
    for source, target in session_pairs:
        shutil.copy2(build / 'native' / source, package / target)
    for name in ['scene.json', 'receptor.pdb', 'B1.sdf', 'B2.sdf', 'B4.sdf', 'B5.sdf']:
        shutil.copy2(build / name, assets / name)
    for name in ['poses-A.png', 'poses-B.png', 'poses-C.png', 'candidate.png', 'view-taller.png', 'view-open.png','poses-D35.png','poses-D55.png','poses-D70.png','candidate-D55.png']:
        shutil.copy2(build / 'native' / name, examples / name)
    shutil.copy2(build / 'native/manifest.json', assets / 'native-manifest.json')
    shutil.copy2(code / 'export_current.py', package / '同步导出.py')
    shutil.copy2(code / '编辑教程.md', package / 'README.md')
    scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
    summary = {'sessions':[target for _,target in session_pairs], 'map_storage':'embedded in CXS', 'density_kind':scene['density_kind'], 'identity_pose_rmsd_A':{d['id']:d['ideal_bound_best_rmsd_A'] for d in scene['identities']}}
    (package / 'delivery.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
