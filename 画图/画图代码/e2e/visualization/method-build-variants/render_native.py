"""从冻结分子坐标渲染Build四种布局的共用素材.

FIGURE_BUILD_ROOT指定本次目录. render/保存透明PNG及同名PyMOL会话;
render_manifest.json保存逐图相机、坐标、原子数及真实/示意来源.
输入为9BJJ受体、ATP参考和同身份的50个原候选; 不重新运行预测或评价.
"""
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
import pymol2


def sdf_records(source):
    """读取V2000记录, 返回mol字符串与(N,3) XYZ坐标; N为该记录原子数, 单位Å."""
    records = []
    for record in source.read_text(encoding='utf-8').split('$$$$'):
        if not record.strip():
            continue
        lines = record.splitlines()
        counts = next(i for i, value in enumerate(lines[:8]) if 'V2000' in value)
        atom_count = int(lines[counts][:3])
        xyz = np.array([[float(line[j:j + 10]) for j in (0, 10, 20)] for line in lines[counts + 1:counts + 1 + atom_count]])
        records.append({'mol': '\n'.join(lines[counts - 3:]) + '\n', 'xyz': xyz})
    return records


def display(cmd, faint):
    """统一受体cartoon、配体元素色及透明光追; faint控制去噪背景受体的透明度."""
    cmd.set_color('receptor_tint', [0.48, 0.61, 0.67])
    cmd.set_color('ligand_tint', [0.12, 0.53, 0.45])
    cmd.color('receptor_tint', 'receptor')
    cmd.color('ligand_tint', 'ligand')
    for element, colour in [('O', 'red'), ('N', 'blue'), ('P', 'orange'), ('S', 'yelloworange')]:
        cmd.color(colour, 'ligand and elem ' + element)
    cmd.set('cartoon_transparency', 0.79 if faint else 0.24)
    cmd.set('cartoon_loop_radius', 0.13)
    cmd.set('cartoon_fancy_helices', 1)
    cmd.set('stick_radius', 0.22, 'ligand')
    cmd.set('orthoscopic', 1)
    cmd.set('ray_shadows', 0)
    cmd.set('specular', 0.12)
    cmd.set('ambient', 0.58)
    cmd.set('direct', 0.65)
    cmd.set('antialias', 2)
    cmd.set('ray_opaque_background', 0)
    cmd.bg_color('white')


def load_ligand(cmd, record, xyz):
    """替换配体, 保留V2000拓扑与原子顺序, 使用(N,3) XYZ坐标."""
    current_view = list(cmd.get_view())
    cmd.set('auto_zoom', 0)
    cmd.delete('ligand')
    cmd.read_molstr(record['mol'], 'ligand')
    cmd.remove('ligand and hydro')
    cmd.load_coords(xyz, 'ligand', state=1)
    cmd.set_view(current_view)


def export_scene(cmd, name, view, pixels, origin, xyz):
    """保存原生PNG、PSE和逐图记录; pixels=(宽,高), xyz为当前配体的(N,3)世界坐标."""
    cmd.set_view(view)
    cmd.png(str(render / (name + '.png')), pixels[0], pixels[1], dpi=400, ray=1, quiet=1)
    cmd.save(str(render / (name + '.pse')))
    manifest['images'][name] = {'view': list(cmd.get_view()), 'canvas_px': list(pixels), 'source': origin,
                                'ligand_xyz_A': np.round(xyz, 5).tolist(), 'atom_count': len(xyz)}
    print('Rendered ' + name, flush=True)


# ================================================================================================
root = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
build = Path(os.environ['FIGURE_BUILD_ROOT'])
render = build / 'render'
render.mkdir(parents=True, exist_ok=True)
views = root / '画图/画图代码/e2e/output/e2e-flow/views/9bjj'
source = root / '画图/画图代码/e2e/output/e2e-flow/source/source/9bjj'
reference = sdf_records(views / 'assets/reference.sdf')[0]
prediction = sdf_records(views / 'assets/prediction.sdf')[0]
candidates = sdf_records(source / 'poses.sdf')
source_files = [views / 'assets/reference.sdf', views / 'assets/prediction.sdf', views / 'assets/gt_receptor.cif',
                views / 'assets/ca2_receptor.cif', source / 'poses.sdf']
manifest = {'case': '9BJJ ATP B:901', 'candidate_count': len(candidates), 'images': {},
            'inputs': [{'path': str(p.relative_to(root)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_files],
            'denoising': {'kind': 'schematic_coordinate_perturbations', 'seed': 20261028, 'sigma_A': [4.0, 2.1, 0.9, 0.30, 0.0], 'structure_fraction': [0.0, 0.45, 0.75, 0.95, 1.0],
                           'meaning': 'Illustrative noise levels, not measured model sampling timesteps; atom identities and count remain fixed.'}}

with pymol2.PyMOL() as pm:
    cmd = pm.cmd
    # 整体与局部采用同一真实GT受体和ATP; 全局仅显示配体邻近的一条完整受体链.
    cmd.load(str(views / 'assets/gt_receptor.cif'), 'receptor')
    load_ligand(cmd, reference, reference['xyz'])
    near = cmd.get_model('receptor within 6 of ligand').atom
    chain = Counter(atom.chain for atom in near).most_common(1)[0][0]
    cmd.select('global_context', 'receptor and chain ' + chain)
    cmd.hide('everything'); cmd.show('cartoon', 'global_context'); cmd.show('sticks', 'ligand')
    display(cmd, False)
    cmd.orient('global_context'); cmd.turn('x', 12); cmd.turn('y', -14); cmd.zoom('global_context', 3)
    global_view = list(cmd.get_view())
    export_scene(cmd, 'complex', global_view, (1800, 1400), 'Deposited receptor chain ' + chain + ' with reference ATP', reference['xyz'])
    residues = {}
    for atom in cmd.get_model('byres (receptor within 7 of ligand)').atom:
        residues.setdefault(atom.chain, set()).add(int(atom.resi))
    clauses = []
    for local_chain, numbers in residues.items():
        groups = []
        for number in sorted(numbers):
            if not groups or number - groups[-1][-1] > 3:
                groups.append([number])
            else:
                groups[-1].append(number)
        clauses.extend('(chain ' + local_chain + ' and resi ' + str(g[0] - 2) + '-' + str(g[-1] + 2) + ')' for g in groups if len(g) >= 3)
    cmd.select('local_context', 'receptor and (' + ' or '.join(clauses) + ')')
    cmd.dss('local_context')
    cmd.hide('cartoon', 'receptor'); cmd.show('cartoon', 'local_context')
    cmd.orient('ligand'); cmd.turn('x', 14); cmd.turn('y', -18); cmd.zoom('ligand', 6.2)
    gt_view = list(cmd.get_view())
    export_scene(cmd, 'reference-pose', gt_view, (1800, 1300), 'Deposited receptor and reference ATP; local view', reference['xyz'])
    cmd.hide('sticks', 'ligand'); cmd.show('sticks', 'byres (receptor within 4 of ligand)')
    cmd.color('receptor_tint', 'receptor'); cmd.set('stick_radius', 0.12, 'receptor')
    export_scene(cmd, 'reference-pocket', gt_view, (1800, 1300), 'Same GT pocket, ligand hidden', reference['xyz'])

    # 原预测与多候选采用其实际CA2受体, 所有局部输出和Pocket固定相机、画幅及上下文.
    cmd.reinitialize()
    scene = root / '画图/画图代码/e2e/output/method-build-variants/source/author-output-9bjj.pse'
    cmd.load(str(scene))
    manifest['inputs'].append({'path': str(scene.relative_to(root)), 'sha256': hashlib.sha256(scene.read_bytes()).hexdigest()})
    load_ligand(cmd, prediction, prediction['xyz'])
    cmd.select('local_context', 'context')
    cmd.hide('everything'); cmd.show('cartoon', 'local_context'); cmd.show('sticks', 'ligand')
    display(cmd, False)
    local_view = list(cmd.get_view())
    export_scene(cmd, 'prediction', local_view, (1800, 1300), 'Frozen CA2 top-1 ATP pose', prediction['xyz'])
    cmd.hide('sticks', 'ligand'); cmd.show('sticks', 'byres (receptor within 4 of ligand)')
    cmd.color('receptor_tint', 'receptor'); cmd.set('stick_radius', 0.12, 'receptor')
    export_scene(cmd, 'prediction-pocket', local_view, (1800, 1300), 'Corresponding CA2 input pocket, ligand hidden', prediction['xyz'])
    cmd.hide('sticks', 'receptor')

    # 用候选间坐标差异选三个可辨识的同身份输出; 不使用真值RMSD或改变原模型排序.
    seed = int(np.argmin([np.mean((r['xyz'] - prediction['xyz']) ** 2) for r in candidates]))
    selected = [seed]
    for _ in range(2):
        scores = [min(np.sqrt(np.mean(np.sum((r['xyz'] - candidates[j]['xyz']) ** 2, axis=1))) for j in selected) for r in candidates]
        for index in selected:
            scores[index] = -1
        selected.append(int(np.argmax(scores)))
    manifest['selected_candidate_indices'] = selected
    for slot, index in enumerate(selected):
        record = candidates[index]
        load_ligand(cmd, record, record['xyz'])
        cmd.hide('everything', 'ligand'); cmd.show('sticks', 'ligand'); display(cmd, False)
        export_scene(cmd, 'pose-' + str(slot + 1), local_view, (1800, 1300), 'Original candidate index ' + str(index), record['xyz'])

    # 同一批31个ATP重原子的五个示意噪声状态; 不生成新的原子或化学身份.
    rng = np.random.default_rng(manifest['denoising']['seed'])
    noise = rng.normal(size=prediction['xyz'].shape)
    centre = prediction['xyz'].mean(axis=0)
    initial = centre + manifest['denoising']['sigma_A'][0] * noise
    load_ligand(cmd, prediction, initial)
    cmd.set_view(local_view); cmd.zoom('ligand', 2.0)
    denoising_view = list(cmd.get_view())
    for index, sigma in enumerate(manifest['denoising']['sigma_A']):
        fraction = manifest['denoising']['structure_fraction'][index]
        xyz = centre + fraction * (prediction['xyz'] - centre) + sigma * noise
        load_ligand(cmd, prediction, xyz)
        cmd.hide('everything', 'ligand'); display(cmd, True)
        if index < 3:
            cmd.show('spheres', 'ligand'); cmd.set('sphere_scale', 0.27 if index == 0 else 0.23, 'ligand')
        else:
            cmd.show('sticks', 'ligand')
        export_scene(cmd, 'denoise-' + str(index), denoising_view, (1800, 1300), 'Schematic noise sigma=' + str(sigma) + ' A', xyz)

(build / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
