"""将冻结首位姿态、受体原子和实验密度投影为可编辑图形. 不进行分子对齐或重新排名.

产物 geometry.json 保存 PPT 原生图形的位置、颜色和层次; cases.json 保存逐案例指标与来源.
输入为画图/画图代码/stage3/output/stage3-cases-main/assets 的只读服务器副本及 regenerated/case_metrics.json. 新几何与案例JSON只写该目录的 regenerated/.
"""
import os
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
# FROZEN 指向本次读取的科学条件目录, 其 assets 保存原排序首位坐标和原实验密度.
FROZEN = Path(os.environ['FIGURE_SOURCE_ROOT']) if 'FIGURE_SOURCE_ROOT' in os.environ else ROOT / '画图/画图代码/stage3/output/stage3-cases-main'
OUT = Path(os.environ['FIGURE_RENDER_ROOT']) if 'FIGURE_RENDER_ROOT' in os.environ else FROZEN / 'regenerated'
SOURCE = FROZEN / 'assets'
COLORS = dict(official='#CD8750', tuned='#4878B6', build='#94669C', gt='#279D98', receptor='#7B8C55', density='#A5AFB7', clash='#C43D43')


def project(xyz, center, rotation, scale, offset):
    """把世界 XYZ 坐标投影到面板坐标, 仅改变显示.

    Args:
        xyz: (N, 3), 世界坐标, Å.
        center: (3,), 显示中心, 世界 XYZ, Å.
        rotation: (3, 3), 正交相机基向量; 不用于 RMSD.
        scale: float, 每 Å 对应的画布像素数.
        offset: (2,), 面板中心, 画布像素.
    Returns:
        (N, 3), 前两列为显示 XY 像素, 第三列为显示深度 Å.
    """
    points = (xyz - center) @ rotation
    points[:, :2] = points[:, :2] * [scale, -scale] + offset
    return points


def bonds_layer(points, bonds, color, width, alpha, name):
    """将原子对转换为独立可编辑线段, 不改变其连接关系.

    Args:
        points: (N, 3), 投影坐标; 前两列为画布像素.
        bonds: (B, 2) 或 (B, 3), 前两列为原子索引; 第三列可为键级.
        color: str, 十六进制显示颜色.
        width: float, 显示线宽, 像素.
        alpha: float, 不透明度, 0 至 1.
        name: str, PPT 图层名称, 如 ReferenceLigand.
    Returns:
        dict, lines 是 (B, 2, 2) 的像素端点; color、width、alpha 和 name 控制显示.
    """
    indices = np.asarray(bonds)[:, :2].astype(int)
    order = np.argsort(points[indices, 2].mean(1))
    return dict(kind='lines',name=name,color=color,width=width,alpha=alpha,lines=points[indices[order], :2].tolist())


# 保存全部十个冻结实例的几何; 各页实际展示实例由 render_figure.py 选择.
groups = [('density', [('9q16',0),('9ub7',3),('9r3d',0)]), ('clash', [('9bjj',16),('30ga',7),('9wq3',5)]), ('alternatives', [('9llg',2),('9lfa',0),('9u7j',2),('9wup',2)])]
if 'FIGURE_SOURCE_ROOT' in os.environ:
    # 本条件 case_selection.json 的两组各五个实例均生成几何, 主图只选其中各三个.
    selection = json.loads((FROZEN / 'case_selection.json').read_text(encoding='utf-8'))
    groups = [(group, [tuple(key) for key in selection[group]]) for group in ['density', 'clash']]
metrics = {(r['pdb_id'],r['occurrence_id']): r for r in json.loads((OUT/'case_metrics.json').read_text(encoding='utf-8'))}
cases = []
geometry = []
for group, keys in groups:
    for pdb, occurrence in keys:
        directory = SOURCE/f'{pdb}_{occurrence}'
        metadata = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
        arrays = np.load(directory/'arrays.npz',allow_pickle=False)
        # 全部方法共享同一个由三种预测与真值构象确定的视角; PCA 只用于显示方向.
        all_points = np.concatenate([arrays[m] for m in ['gt','official','tuned','build']])
        center = (all_points.min(0)+all_points.max(0))/2
        _, _, basis = np.linalg.svd(all_points-all_points.mean(0),full_matrices=False)
        rotation = basis.T
        if np.linalg.det(rotation)<0: rotation[:,2]*=-1
        projected = (all_points-center)@rotation
        # 每例三格共享尺度. 不同案例独立取景, 物理比例尺单独记录.
        scale = min(248/np.ptp(projected[:,0]),118/np.ptp(projected[:,1]))
        offset = np.array([140.,70.])
        # 密度等值面来自作者推荐 contour_canonical; 仅保留距沉积配体 2 Å 内的已有面片.
        vertices, faces, _, _ = marching_cubes(arrays['density'],level=float(arrays['contour']),step_size=1)
        world = arrays['origin']+(vertices[:,::-1]+0.5)*arrays['voxel_size']
        near = cKDTree(arrays['gt']).query(world)[0]<2.0
        faces = faces[near[faces].all(1)]
        edges = np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[0,2]]]),axis=1),axis=0)
        mesh = project(world,center,rotation,scale,offset)
        # 背景保留接近真值或涉及碰撞的残基; 只显示已取景范围中的原子与键.
        rc = arrays['receptor_xyz'];res = arrays['receptor_res_index']
        selected_res = set(res[cKDTree(arrays['gt']).query(rc)[0]<3.5].tolist())
        for method in ['official','tuned','build']:
            selected_res.update(res[[p[1] for p in metrics[(pdb,occurrence)][method]['clash_indices']]].tolist())
        keep = np.isin(res,list(selected_res))
        rb = arrays['receptor_bonds'];rb = rb[keep[rb].all(1)]
        rp = project(rc,center,rotation,scale,offset)
        # 越出统一视野的背景键不画; 配体与密度区域没有按方法裁剪.
        in_frame = ((rp[:,:2]>[0,0])&(rp[:,:2]<[280,140])).all(1)
        rb = rb[in_frame[rb].all(1)]
        row = dict(pdb_id=pdb,occurrence_id=occurrence,group=group,center=center.tolist(),rotation=rotation.tolist(),pixels_per_A=float(scale),contour=float(arrays['contour']),methods={})
        for method in ['official','tuned','build']:
            points = project(arrays[method],center,rotation,scale,offset)
            gt = project(arrays['gt'],center,rotation,scale,offset)
            layers = [bonds_layer(rp,rb,COLORS['receptor'],1.05,0.85,'Receptor'),bonds_layer(mesh,edges,COLORS['density'],0.45,0.65,'ExperimentalDensity'),bonds_layer(gt,arrays['bonds'],COLORS['gt'],1.30,0.78,'ReferenceLigand'),bonds_layer(points,arrays['bonds'],COLORS[method],2.5,1.0,'PredictedLigand')]
            # 全部预测原子使用方法颜色, 红色只由下面的真实碰撞标记使用.
            atoms = [dict(x=float(p[0]),y=float(p[1]),radius=1.7,color=COLORS[method]) for p in points]
            layers.append(dict(kind='atoms',name='PredictedAtoms',atoms=atoms))
            pairs = metrics[(pdb,occurrence)][method]['clash_indices']
            # 红色线段定位所有满足原 0.75 半径和阈值的原子对, 计数不依赖二维投影.
            if pairs:
                lines = [[points[i,:2].tolist(),rp[j,:2].tolist()] for i,j in pairs]
                layers.append(dict(kind='lines',name='Clashes',color=COLORS['clash'],width=1.1,alpha=1.0,lines=lines,dashed=True))
                involved = sorted(set(j for _,j in pairs))
                layers.append(dict(kind='atoms',name='ClashingReceptorAtoms',atoms=[dict(x=float(rp[j,0]),y=float(rp[j,1]),radius=2.5,color=COLORS['clash']) for j in involved]))
            row['methods'][method]=layers
        geometry.append(row)
        case = dict(metrics[(pdb,occurrence)])
        case.update(group=group,metadata=metadata,view={k:row[k] for k in ['center','rotation','pixels_per_A','contour']})
        cases.append(case)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'geometry.json').write_text(json.dumps(dict(tile_size=[280,140],colors=COLORS,cases=geometry)),encoding='utf-8')
(OUT/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared',len(cases),'cases with editable geometric layers')
