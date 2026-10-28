"""在独立 ChimeraX 进程核对交付 CXS、教程命令和移动配体后的同步导出.

仅用于本图验收. FIGURE_BUILD_ROOT/editing-package 为输入, validation/ 保存结果和本次试导出.
"""
import json
import os
from pathlib import Path
import runpy
import sys
import traceback

import numpy as np
from chimerax.core.commands import run


def main(session):
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    package = build / 'editing-package'
    validation = build / 'validation'
    validation.mkdir(exist_ok=True)
    report = {'passed':False, 'sessions':[], 'commands':[], 'external_map_reads':[]}
    # 会话必须内嵌地图; 禁止通过生成时的外部 MRC 恢复, 但允许读取当前交付的身份模板.
    def block_external_maps(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0]))
            if path.suffix.lower() == '.mrc':
                report['external_map_reads'].append(str(path))
                raise FileNotFoundError('CXS 验收禁止读取外部 MRC: ' + str(path))
    sys.addaudithook(block_external_maps)
    try:
        scene = json.loads((package / 'assets/scene.json').read_text(encoding='utf8'))
        run(session,'windowsize 1200 800')
        for filename in ['A_完整受体.cxs', 'B_局部剖切.cxs', 'C_密度网格.cxs','D35_完整受体半透明.cxs','D55_完整受体半透明.cxs','D70_完整受体半透明.cxs']:
            run(session, f'open "{(package / filename).as_posix()}"')
            models = {m.id[0]:m for m in session.models.list() if len(m.id) == 1}
            assert models[1].num_atoms == 3604
            assert all(models[i].display for i in range(1,7))
            assert all(not models[i].display for i in range(7,12))
            assert len(models[6].data.full_matrix().shape) == 3
            points=session.main_view.camera.position.inverse()*models[1].atoms.scene_coords
            fw=session.main_view.camera.field_width
            assert np.max(np.abs(points[:,0])) < fw/2
            assert np.max(np.abs(points[:,1])) < fw/2*800/1200
            error = max(float(np.max(np.abs(models[number].atoms.scene_coords-np.array(pose['xyz'])))) for number,pose in enumerate(scene['bound_poses'],2))
            assert error < 0.001
            report['sessions'].append({'file':filename, 'pose_max_coordinate_error_A':error, 'receptor_atoms':models[1].num_atoms, 'density_embedded':True})
        run(session, f'open "{(package / "D55_完整受体半透明.cxs").as_posix()}"')
        commands = [
            'volume #6 transparency 0.90', 'transparency #6 90 target s', 'volume #6 transparency 0.88',
            'transparency #1 30 target c', 'transparency #1 0 target c', 'transparency #2-5 0 target a',
            'color #1 #93AABA target c', 'color #1 #6E8DA2 target c',
            'volume #6 style mesh step 2 meshLighting false color #A8B2BC transparency 0.45',
            'volume #6 style surface step 1 level 0.17 color #CAD0D6 transparency 0.88',
            'surface #1', 'color #1 #7795A3 target s', 'transparency #1 85 target s', 'hide #1 surfaces', 'cartoon #1',
            'turn y 10', 'turn x -8', 'turn z 5', 'zoom 1.10', 'view slender', 'view taller', 'view open', 'view Fig1',
            'move x 1 models #2', 'move y -0.5 models #2', 'move z 1 models #2', 'move x 1 models #2 coordinateSystem #1',
            'turn y 15 models #2 center #2', 'turn z -10 models #2 center #2',
            'select #2', 'mousemode rightMode "translate selected models"', 'mousemode rightMode "rotate selected models"',
            'select clear', 'mousemode rightMode translate', 'move x 1 models #2,7', 'turn y 10 models #2,7 center #2',
            'view Fig1', 'hide #6 models', 'show #6 models', 'hide #2-5 models', 'show #7-11 models', 'hide #7-11 models', 'show #2-5 models',
            'select #1/A:24', 'hide sel cartoons', 'show sel cartoons', 'select clear', 'view name MyEdit', 'view MyEdit', 'view Fig1'
        ]
        for command in commands:
            run(session, command)
            report['commands'].append(command)
        run(session, f'open "{(package / "D55_完整受体半透明.cxs").as_posix()}"')
        models = {m.id[0]:m for m in session.models.list() if len(m.id) == 1}
        ribbon_alpha = models[1].residues.ribbon_colors[:,3].copy()
        before = {i:models[i].atoms.scene_coords.copy() for i in range(1,6)}
        run(session, 'move x 1 models #2')
        run(session, 'turn y 12 models #2 center #2')
        after = {i:models[i].atoms.scene_coords.copy() for i in range(1,6)}
        assert all(np.array_equal(before[i],after[i]) for i in [1,3,4,5])
        assert np.linalg.norm(before[2].mean(0)-after[2].mean(0)) > 0.99
        internal_before = np.linalg.norm(before[2][:,None]-before[2][None,:],axis=-1)
        internal_after = np.linalg.norm(after[2][:,None]-after[2][None,:],axis=-1)
        assert np.max(np.abs(internal_before-internal_after)) < 1e-5
        export_root = validation / 'manual-export'
        os.environ['FIGURE_EXPORT_DIR'] = str(export_root)
        runpy.run_path(str(package / '同步导出.py'), run_name='__main__', init_globals={'session':session})
        manifest = json.loads((export_root / 'export_manifest.json').read_text(encoding='utf8'))
        assert manifest['schematic_density_regenerated']
        for name in ['Input-density.png','Input-receptor.png','Candidate.png','Ligand-poses.png','Edited-global.cxs']:
            assert (export_root/name).stat().st_size > 2000
        run(session, f'open "{(export_root / "Edited-global.cxs").as_posix()}"')
        new_models = {m.id[0]:m for m in session.models.list() if len(m.id) == 1}
        assert np.array_equal(new_models[1].residues.ribbon_colors[:,3],ribbon_alpha)
        error = max(float(np.max(np.abs(new_models[i].atoms.scene_coords-after[i]))) for i in range(1,6))
        assert error < 0.001
        volume = new_models[7]
        data = volume.data.full_matrix().astype(float)
        zyx = np.indices(data.shape)
        mean_zyx = np.array([(axis*data).sum()/data.sum() for axis in zyx])
        centre = volume.data.ijk_to_xyz(mean_zyx[::-1])
        blob_error = float(np.linalg.norm(centre-after[2].mean(0)))
        assert blob_error < 0.25
        report.update(passed=True, updated_pose_coordinate_error_A=error, updated_B1_blob_centre_error_A=blob_error, edited_pose_internal_distance_error_A=float(np.max(np.abs(internal_before-internal_after))), unrelated_models_unchanged=True)
    except Exception:
        report['error'] = traceback.format_exc()
    (validation / 'native-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    run(session, f'log save "{(validation / "commands.html").as_posix()}"')


main(session)
