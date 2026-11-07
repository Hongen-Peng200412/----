"""计算当前9WUP的密度覆盖、碰撞及原生绘图几何.

入口prepare(store, build)从服务器构造53重原子原数组, 在本次temp生成assets/、case_metrics.json、geometry.json. RMSD仅取原排名评价; 密度覆盖在XYZ世界坐标上插值, 碰撞按真实三维距离计算. geometry中的二维线段及原子仅用于PPT显示, 不参与评价.
"""

import json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial.distance import cdist
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
from visual.arrays import prepare as prepare_arrays
from TOOLS.ppt.native_geometry import project, bonds_layer

VDW = {
    5: 1.8,
    6: 1.7,
    7: 1.6,
    8: 1.55,
    9: 1.5,
    15: 1.95,
    16: 1.8,
    17: 1.8,
    34: 1.9,
    35: 1.9,
    53: 2.1,
}
COLORS = dict(
    official="#CD8750",
    tuned="#4878B6",
    build="#94669C",
    gt="#279D98",
    receptor="#7B8C55",
    density="#A5AFB7",
    clash="#C43D43",
)


# ================================================================================================
def prepare(store, build: Path):
    """生成当前9WUP的三种预测视图, 不读取任何旧output或本地科学派生数据.

    assets/9wup_2/arrays.npz保存世界XYZÅ坐标、原子元素和键、局部ZYX密度及XYZ原点/体素尺寸. case_metrics.json保存原RMSD、密度阈值覆盖率和碰撞原子对. geometry.json保存共享相机、像素/Å尺度及三种方法的投影线条/原子, 供原生PPT构造读取.
    """
    build.mkdir(parents=True, exist_ok=True)
    prepare_arrays(store, build / "assets/9wup_2")
    folder = build / "assets/9wup_2"
    arrays = np.load(folder / "arrays.npz", allow_pickle=False)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf8"))
    row = dict(
        pdb_id=metadata["pdb_id"],
        occurrence_id=metadata["occurrence_id"],
        occurrence=metadata["occurrence"],
    )
    # (N,) 和 (R,), 与各自世界坐标原子顺序一致, N/R 为配体/受体重原子数.
    ligand_radii = np.array([VDW[int(e)] for e in arrays["element"]])
    receptor_radii = np.array([VDW[int(e)] for e in arrays["receptor_element"]])
    for method in ["gt", "official", "tuned", "build"]:
        xyz = arrays[method]  # (N, 3), XYZ 世界坐标 Å; 不进行刚体叠合.
        # [N, XYZ] -> [N, ZYX], 源图原点为边界角点, -0.5 转为体素中心索引.
        index = ((xyz - arrays["origin"]) / arrays["voxel_size"] - 0.5)[:, ::-1]
        values = map_coordinates(arrays["density"], index.T, order=1, mode="constant", cval=np.nan)
        distance = cdist(xyz, arrays["receptor_xyz"])  # (N, R), 真实三维原子对距离 Å.
        clash = distance < 0.75 * (ligand_radii[:, None] + receptor_radii[None, :])
        row[method] = dict(
            density_fraction=float(np.mean(values >= arrays["contour"])),
            density_mean=float(np.mean(values)),
            clash_pairs=int(clash.sum()),
            clash_atoms=int(clash.any(1).sum()),
            min_dist=float(distance.min()),
            clash_indices=np.argwhere(clash).tolist(),
        )
        if method in ["official", "tuned"]:
            row[method]["rmsd"] = metadata["metrics"][method]["rmsd"]
        elif method == "build":
            row[method]["rmsd"] = metadata["build"]["rmsd_A"]
    metrics = {("9wup", 2): row}
    (build / "case_metrics.json").write_text(
        json.dumps([row], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    SOURCE = build / "assets"
    pdb, occurrence, group = "9wup", 2, "current"
    directory = SOURCE / f"{pdb}_{occurrence}"
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    arrays = np.load(directory / "arrays.npz", allow_pickle=False)
    # 全部方法共享同一个由三种预测与真值构象确定的视角; PCA 只用于显示方向.
    all_points = np.concatenate([arrays[m] for m in ["gt", "official", "tuned", "build"]])
    center = (all_points.min(0) + all_points.max(0)) / 2
    _, _, basis = np.linalg.svd(all_points - all_points.mean(0), full_matrices=False)
    rotation = basis.T
    if np.linalg.det(rotation) < 0:
        rotation[:, 2] *= -1
    projected = (all_points - center) @ rotation
    # 每例三格共享尺度. 不同案例独立取景, 物理比例尺单独记录.
    scale = min(248 / np.ptp(projected[:, 0]), 118 / np.ptp(projected[:, 1]))
    offset = np.array([140.0, 70.0])
    # 密度等值面来自作者推荐 contour_canonical; 仅保留距沉积配体 2 Å 内的已有面片.
    vertices, faces, _, _ = marching_cubes(
        arrays["density"], level=float(arrays["contour"]), step_size=1
    )
    world = arrays["origin"] + (vertices[:, ::-1] + 0.5) * arrays["voxel_size"]
    near = cKDTree(arrays["gt"]).query(world)[0] < 2.0
    faces = faces[near[faces].all(1)]
    edges = np.unique(
        np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [0, 2]]]), axis=1),
        axis=0,
    )
    mesh = project(world, center, rotation, scale, offset)
    # 背景保留接近真值或涉及碰撞的残基; 只显示已取景范围中的原子与键.
    rc = arrays["receptor_xyz"]
    res = arrays["receptor_res_index"]
    selected_res = set(res[cKDTree(arrays["gt"]).query(rc)[0] < 3.5].tolist())
    for method in ["official", "tuned", "build"]:
        selected_res.update(
            res[[p[1] for p in metrics[(pdb, occurrence)][method]["clash_indices"]]].tolist()
        )
    keep = np.isin(res, list(selected_res))
    rb = arrays["receptor_bonds"]
    rb = rb[keep[rb].all(1)]
    rp = project(rc, center, rotation, scale, offset)
    # 越出统一视野的背景键不画; 配体与密度区域没有按方法裁剪.
    in_frame = ((rp[:, :2] > [0, 0]) & (rp[:, :2] < [280, 140])).all(1)
    rb = rb[in_frame[rb].all(1)]
    row = dict(
        pdb_id=pdb,
        occurrence_id=occurrence,
        group=group,
        center=center.tolist(),
        rotation=rotation.tolist(),
        pixels_per_A=float(scale),
        contour=float(arrays["contour"]),
        methods={},
    )
    for method in ["official", "tuned", "build"]:
        points = project(arrays[method], center, rotation, scale, offset)
        gt = project(arrays["gt"], center, rotation, scale, offset)
        layers = [
            bonds_layer(rp, rb, COLORS["receptor"], 1.05, 0.85, "Receptor"),
            bonds_layer(mesh, edges, COLORS["density"], 0.45, 0.65, "ExperimentalDensity"),
            bonds_layer(gt, arrays["bonds"], COLORS["gt"], 1.30, 0.78, "ReferenceLigand"),
            bonds_layer(points, arrays["bonds"], COLORS[method], 2.5, 1.0, "PredictedLigand"),
        ]
        # 全部预测原子使用方法颜色, 红色只由下面的真实碰撞标记使用.
        atoms = [
            dict(x=float(p[0]), y=float(p[1]), radius=1.7, color=COLORS[method]) for p in points
        ]
        layers.append(dict(kind="atoms", name="PredictedAtoms", atoms=atoms))
        pairs = metrics[(pdb, occurrence)][method]["clash_indices"]
        # 红色线段定位所有满足原 0.75 半径和阈值的原子对, 计数不依赖二维投影.
        if pairs:
            lines = [[points[i, :2].tolist(), rp[j, :2].tolist()] for i, j in pairs]
            layers.append(
                dict(
                    kind="lines",
                    name="Clashes",
                    color=COLORS["clash"],
                    width=1.1,
                    alpha=1.0,
                    lines=lines,
                    dashed=True,
                )
            )
            involved = sorted(set(j for _, j in pairs))
            layers.append(
                dict(
                    kind="atoms",
                    name="ClashingReceptorAtoms",
                    atoms=[
                        dict(
                            x=float(rp[j, 0]), y=float(rp[j, 1]), radius=2.5, color=COLORS["clash"]
                        )
                        for j in involved
                    ],
                )
            )
        row["methods"][method] = layers
    (build / "geometry.json").write_text(
        json.dumps(dict(tile_size=[280, 140], colors=COLORS, cases=[row])), encoding="utf-8"
    )
    return row, metrics[(pdb, occurrence)]
