"""在作者当前 ChimeraX 会话内, 同步重建示意密度并用当前视角导出三个面板.

在 ChimeraX 命令行 runscript 本文件. 脚本旁的 assets/scene.json 和四份 SDF 是身份及原子轴契约.
输出至本仓库 temp/overview_manual/<时间>/; FIGURE_EXPORT_DIR 可指定验证用目录.
输出包含 Input-density、Input-receptor、Candidate、Ligand-poses 四张同相机 PNG, 五张 blob 缩略图、世界坐标 SDF、编辑后 CXS 及 export_manifest.json.
"""
from datetime import datetime
import json
import os
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter
from chimerax.core.commands import run
from chimerax.geometry import Place
from chimerax.map_data import ArrayGridData


def export_current(session, package, destination):
    """从当前模型矩阵读取世界坐标; 不改变配体内部构象, 不自动重新构图或缩放相机."""
    scene = json.loads((package / 'assets/scene.json').read_text(encoding='utf8'))
    models = {m.id[0]: m for m in session.models.list() if len(m.id) == 1}
    receptor = models[1]
    density = models[6]
    camera = session.main_view.camera
    camera_position, field_width = camera.position.copy(), camera.field_width
    ribbons = receptor.residues.ribbon_displays.copy()
    density_style = 'mesh' if density.surfaces[0].display_style == density.surfaces[0].Mesh else 'surface'
    density_rgba = tuple(density.surfaces[0].rgba)
    density_step = tuple(density.region[2])
    destination.mkdir(parents=True, exist_ok=True)
    run(session, f'save "{(destination / "before-export.cxs").as_posix()}" includeMaps true')
    coords = {pose['blob']: np.array(models[number].atoms.scene_coords, dtype=float) for number, pose in enumerate(scene['bound_poses'], 2)}
    receptor_xyz = np.array(receptor.atoms.scene_coords, dtype=float)
    false_xyz = models[9].scene_position * np.array(scene['false_positive_xyz_A'])
    all_xyz = np.vstack([receptor_xyz] + list(coords.values()) + [false_xyz])
    spacing = 0.7
    origin = np.floor(all_xyz.min(0)-7)
    shape = np.ceil((all_xyz.max(0)+7-origin)/spacing).astype(int)+1
    blob_xyz = dict(coords, B3=false_xyz)
    # 移动配体后, 对应 blob 和示意密度从新世界坐标同时生成; 不沿用旧位置的密度.
    for number, label in [(6, 'density'), (7, 'B1'), (8, 'B2'), (9, 'B3'), (10, 'B4'), (11, 'B5')]:
        xyz = all_xyz if label == 'density' else blob_xyz[label]
        grid = np.zeros(tuple(shape[::-1]), dtype=np.float32)
        indices = np.rint((xyz-origin)/spacing).astype(int)[:, ::-1]
        np.add.at(grid, tuple(indices.T), 1)
        sigma = 1.8 if label == 'density' else {'B1':1.10, 'B2':1.34, 'B3':1.35, 'B4':1.10, 'B5':1.08}[label]
        grid = gaussian_filter(grid, sigma/spacing)
        grid /= grid.max()
        volume = models[number]
        volume.replace_data(ArrayGridData(grid, origin=tuple(origin), step=(spacing,)*3, name=volume.name))
        volume.position = Place()
        volume.set_parameters(surface_levels=[0.17 if number == 6 else 0.20])
    run(session, 'windowsize 1200 1500')
    camera.position, camera.field_width = camera_position, field_width
    run(session, 'view name Edited')
    manifest = {'camera_matrix':camera.position.matrix.tolist(), 'field_width_A':field_width, 'frame':[1200,1500], 'ligand_centres_world_xyz_A':{key:value.mean(0).tolist() for key,value in coords.items()}, 'files':[], 'schematic_density_regenerated':True}
    for number, pose in enumerate(scene['bound_poses'], 2):
        blob = pose['blob']
        template = (package / 'assets' / (blob+'.sdf')).read_text(encoding='ascii').splitlines()
        for i, xyz in enumerate(coords[blob]):
            template[4+i] = ''.join(f'{v:10.4f}' for v in xyz)+template[4+i][30:]
        (destination / (blob+'.sdf')).write_text('\n'.join(template)+'\n', encoding='ascii')
    run(session, 'hide #7-11 models')
    run(session, 'hide #2-5 models')
    run(session, 'hide #1 cartoons')
    run(session, 'hide #1 surfaces')
    run(session, 'show #6 models')
    if density_style == 'mesh':
        run(session,f'volume #6 style mesh step {density_step[0]} transparency {1-density_rgba[3]}')
    else:
        run(session, 'volume #6 style surface step 1 transparency 0.14')
    phases = ['Input-density', 'Input-receptor', 'Candidate', 'Ligand-poses']
    for phase in phases:
        if phase == 'Input-receptor':
            run(session, 'hide #6 models')
            receptor.residues.ribbon_displays = True
        elif phase == 'Candidate':
            run(session, 'show #6 models')
            run(session, f'volume #6 style {density_style} step {density_step[0]} transparency {1-density_rgba[3]}')
            run(session, 'show #7-11 models')
        elif phase == 'Ligand-poses':
            run(session, 'hide #7-11 models')
            run(session, 'show #2-5 models')
            receptor.residues.ribbon_displays = ribbons
        run(session, 'wait 1')
        path = destination / (phase+'.png')
        run(session, f'save "{path.as_posix()}" width 1200 height 1500 supersample 3 transparentBackground true')
        manifest['files'].append(path.name)
    run(session, f'save "{(destination / "Edited-global.cxs").as_posix()}" includeMaps true')
    # 缩略图同样由本次世界坐标和当前相机生成; 用于 Match 的轮廓替换.
    for number in range(1, 7):
        models[number].display = False
    for number, blob in [(7,'B1'), (8,'B2'), (9,'B3'), (10,'B4'), (11,'B5')]:
        run(session, f'show #{number} models')
        run(session, f'save "{(destination / ("blob-"+blob+".png")).as_posix()}" width 1200 height 1500 supersample 2 transparentBackground true')
        run(session, f'hide #{number} models')
    for number in range(1, 7):
        models[number].display = True
    camera.position, camera.field_width = camera_position, field_width
    inverse = camera.position.inverse()
    centres = {key:value.mean(0) for key,value in blob_xyz.items()}
    projected = {key:inverse*value for key,value in centres.items()}
    manifest['blob_label_centres_pixels'] = {key:[float(600+value[0]/field_width*1200), float(750-value[1]/field_width*1200)] for key,value in projected.items()}
    (destination / 'export_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
    session.logger.info(f'同相机面板、示意密度和当前会话已保存: {destination}')
    return destination


if __name__ == '__main__':
    package = Path(__file__).resolve().parent
    explicit = os.environ.get('FIGURE_EXPORT_DIR')
    if explicit:
        destination = Path(explicit)
    else:
        workspace = next((p for p in package.parents if (p / '论文草稿.md').exists()), package)
        destination = workspace / 'temp/overview_manual' / datetime.now().strftime('%Y%m%d_%H%M%S')
    export_current(session, package, destination)
