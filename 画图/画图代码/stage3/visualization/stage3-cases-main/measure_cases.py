"""计算展示用 Top-1 的密度覆盖及受体碰撞, 不重新评价或排序 RMSD.

输入画图/画图代码/stage3/output/stage3-cases-main/assets/<PDB>_<occurrence>/ 的 arrays.npz 和 metadata.json.
输出 stage3/output/stage3-cases-main/regenerated/case_metrics.json, 顶层为实例列表. 每个实例含身份及四种构象的
density_fraction(0–1)、clash_pairs(原子对数)、clash_indices(配体/受体索引对)
和 min_dist(Å). 三种预测的 rmsd 直接取冻结评价值; gt 为沉积参考构象.
"""
import os
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial.distance import cdist

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
# SOURCE 指向当前条件的冻结案例资产; 未指定时保持原无 level 输入目录.
SOURCE = Path(os.environ['FIGURE_SOURCE_ROOT']) if 'FIGURE_SOURCE_ROOT' in os.environ else ROOT/'画图/画图代码/stage3/output/stage3-cases-main'
OUTPUT = Path(os.environ['FIGURE_RENDER_ROOT']) if 'FIGURE_RENDER_ROOT' in os.environ else SOURCE/'regenerated'
OUTPUT.mkdir(parents=True,exist_ok=True)
# 已与服务器 RDKit GetRvdw 逐项核对; 键为原子序数, 值为范德华半径 Å.
VDW = {5:1.8, 6:1.7, 7:1.6, 8:1.55, 9:1.5, 15:1.95, 16:1.8, 17:1.8, 34:1.9, 35:1.9, 53:2.1}
rows = []
for folder in sorted((SOURCE/'assets').iterdir()):
    arrays = np.load(folder/'arrays.npz', allow_pickle=False)
    metadata = json.loads((folder/'metadata.json').read_text(encoding='utf8'))
    row = dict(pdb_id=metadata['pdb_id'], occurrence_id=metadata['occurrence_id'], occurrence=metadata['occurrence'])
    # (N,) 和 (R,), 与各自世界坐标原子顺序一致, N/R 为配体/受体重原子数.
    ligand_radii = np.array([VDW[int(e)] for e in arrays['element']])
    receptor_radii = np.array([VDW[int(e)] for e in arrays['receptor_element']])
    for method in ['gt', 'official', 'tuned', 'build']:
        xyz = arrays[method]  # (N, 3), XYZ 世界坐标 Å; 不进行刚体叠合.
        # [N, XYZ] -> [N, ZYX], 源图原点为边界角点, -0.5 转为体素中心索引.
        index = ((xyz-arrays['origin'])/arrays['voxel_size']-0.5)[:, ::-1]
        values = map_coordinates(arrays['density'], index.T, order=1, mode='constant', cval=np.nan)
        distance = cdist(xyz, arrays['receptor_xyz'])  # (N, R), 真实三维原子对距离 Å.
        clash = distance < 0.75*(ligand_radii[:, None]+receptor_radii[None, :])
        row[method] = dict(
            density_fraction=float(np.mean(values >= arrays['contour'])),
            density_mean=float(np.mean(values)), clash_pairs=int(clash.sum()),
            clash_atoms=int(clash.any(1).sum()), min_dist=float(distance.min()),
            clash_indices=np.argwhere(clash).tolist())
        if method in ['official', 'tuned']:
            row[method]['rmsd'] = metadata['metrics'][method]['rmsd']
        elif method == 'build':
            row[method]['rmsd'] = metadata['build']['rmsd_A']
    rows.append(row)
(OUTPUT/'case_metrics.json').write_text(json.dumps(rows, indent=2), encoding='utf8')
print(f'Measured {len(rows)} frozen cases')
