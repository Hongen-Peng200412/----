"""从冻结首选构象及受体坐标生成两图共用的真实结构素材。

先读模块末尾的候选循环，再读重复使用的显示配置。FIGURE_BUILD_ROOT
指定本次运行目录；poses/<病例>.png 与 .pse 保存16个独立真实实例，
pockets/{match,build}-{surface,atoms,cartoon}.png 保存三种口袋显示方式。
render_manifest.json 记录原子选择、原始自排序下标、相机及坐标核对。
"""
import json
import os
from pathlib import Path

import numpy as np
import pymol2
from chempy import Atom, Bond
from chempy.models import Indexed


def configure_display(cmd):
    """为每个实例设置相同光照与元素配色，保持真实坐标和拓扑。"""
    cmd.set_color('receptor_blue', [0.43, 0.56, 0.63])
    cmd.set_color('ligand_teal', [0.10, 0.51, 0.43])
    cmd.color('receptor_blue', 'receptor')
    cmd.color('ligand_teal', 'ligand')
    cmd.color('red', 'ligand and elem O')
    cmd.color('blue', 'ligand and elem N')
    cmd.color('orange', 'ligand and elem P')
    cmd.color('yelloworange', 'ligand and elem S')
    cmd.set('stick_radius', 0.22, 'ligand')
    cmd.set('cartoon_loop_radius', 0.15)
    cmd.set('cartoon_fancy_helices', 1)
    cmd.set('cartoon_transparency', 0.24)
    cmd.set('orthoscopic', 1)
    cmd.set('ray_shadows', 0)
    cmd.set('specular', 0.13)
    cmd.set('ambient', 0.57)
    cmd.set('direct', 0.65)
    cmd.set('antialias', 2)
    cmd.set('ray_opaque_background', 0)
    cmd.bg_color('white')


# ================================================================================================
root = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
frozen = root / '画图/画图代码/e2e/output/fig12-revision/source'
build = Path(os.environ['FIGURE_BUILD_ROOT'])
render = build / 'render'
(render / 'poses').mkdir(parents=True, exist_ok=True)
(render / 'pockets').mkdir(parents=True, exist_ok=True)
cases = json.loads((frozen / 'candidate_cases.json').read_text(encoding='utf-8'))
pool = root / '画图/画图代码/stage3/output/stage3-cases-main/screening/assets'
symbols = {1:'H',6:'C',7:'N',8:'O',9:'F',15:'P',16:'S',17:'Cl',35:'Br',53:'I'}
manifest = {'poses': [], 'pockets': []}

with pymol2.PyMOL() as pm:
    cmd = pm.cmd
    for case in cases:
        print('POSE ' + case, flush=True)
        cmd.reinitialize()
        metadata = json.loads((pool / case / 'metadata.json').read_text(encoding='utf-8'))
        arrays = np.load(pool / case / 'arrays.npz')
        cmd.load(str(frozen / 'rcsb' / (metadata['pdb_id'] + '.cif')), 'receptor')
        cmd.remove('receptor and not (polymer.protein or polymer.nucleic)')
        # (N,3) 的 tuned 是冻结模型自评分首位构象；不按参考坐标重挑候选。
        mol = Indexed()
        for index, (xyz, element) in enumerate(zip(arrays['tuned'], arrays['element'])):
            atom = Atom()
            atom.coord = list(map(float, xyz))
            atom.symbol = symbols[int(element)]
            atom.name = atom.symbol + str(index + 1)
            atom.resn, atom.resi, atom.chain, atom.hetatm = 'LIG', '1', 'Z', 1
            mol.atom.append(atom)
        for start, stop, order in arrays['bonds']:
            bond = Bond()
            bond.index = [int(start), int(stop)]
            bond.order = max(1, int(round(order)))
            mol.bond.append(bond)
        cmd.load_model(mol, 'ligand')
        cmd.remove('receptor and not (byres (receptor within 22 of ligand))')
        # 抽查原始口袋坐标与公开沉积受体；只增加展示背景，不变换受体。
        receptor_xyz = np.array([a.coord for a in cmd.get_model('receptor').atom])
        sample = arrays['receptor_xyz'][::max(1, len(arrays['receptor_xyz']) // 40)]
        max_delta = float(np.max(np.min(np.linalg.norm(sample[:,None,:] - receptor_xyz[None,:,:], axis=-1), axis=1)))
        if max_delta > 0.025:
            raise ValueError(f'{case}: 受体原始坐标不对应，最大差 {max_delta}')
        residues = {}
        for atom in cmd.get_model('byres (receptor within 6.5 of ligand)').atom:
            if atom.resi.lstrip('-').isdigit():
                residues.setdefault(atom.chain, set()).add(int(atom.resi))
        clauses = []
        for chain, numbers in residues.items():
            groups = []
            for number in sorted(numbers):
                if not groups or number - groups[-1][-1] > 3:
                    groups.append([number])
                else:
                    groups[-1].append(number)
            clauses.extend(f'(chain {chain} and resi {group[0]-2}-{group[-1]+2})' for group in groups if len(group) >= 2)
        cmd.select('context', 'receptor and (' + ' or '.join(clauses) + ')')
        cmd.hide('everything')
        cmd.dss('context')
        cmd.show('cartoon', 'context')
        cmd.show('sticks', 'ligand')
        configure_display(cmd)
        cmd.orient('ligand')
        cmd.turn('x', 14)
        cmd.turn('y', -18)
        cmd.zoom('ligand', 7.5)
        cmd.png(str(render / 'poses' / (case + '.png')), 1500, 1100, dpi=300, ray=1)
        cmd.save(str(render / 'poses' / (case + '.pse')))
        component = metadata['occurrence']['components'][0]
        manifest['poses'].append({'case':case,'pdb_id':metadata['pdb_id'],
            'ligand':component['ccd_id'],'chain':component['auth_asym_id'],
            'residue':component['auth_seq_id'],'occurrence_id':metadata['occurrence_id'],
            'source':str((pool / case).relative_to(root)),
            'sample_index':metadata['metrics']['tuned']['sample_index'],
            'receptor':'deposited','coordinate_check_max_delta_A':max_delta,
            'context_selection':clauses,'view':list(cmd.get_view())})

    # 两处 Pocket 使用同一9BJJ素材与相机，实际输入原子选择分别保存。
    cmd.reinitialize()
    base = root / '画图/画图代码/e2e/output/e2e-flow/views/9bjj'
    cmd.load(str(base / 'assets/ca2_receptor.cif'), 'receptor')
    cmd.load(str(base / 'assets/prediction.sdf'), 'ligand')
    cmd.remove('hydro')
    data = json.loads((base / 'data.json').read_text(encoding='utf-8'))
    centre = data['prediction']['blob_center_world_xyz_A']
    geometry = json.loads((build / 'geometry.json').read_text(encoding='utf-8'))
    blob_model = Indexed()
    for xyz in geometry['pocket_blob_xyz_A']:
        atom = Atom(); atom.coord = xyz; atom.symbol = 'C'; atom.name = 'X'
        blob_model.atom.append(atom)
    cmd.load_model(blob_model, 'blob_points')
    cmd.pseudoatom('site', pos=centre)
    cmd.select('match_input_atoms', 'receptor within 10 of blob_points')
    cmd.select('build_input_atoms', 'receptor within 15 of site')
    atoms = cmd.get_model('byres (receptor within 7 of ligand)').atom
    residues = {}
    for atom in atoms:
        residues.setdefault(atom.chain, set()).add(int(atom.resi))
    clauses = []
    for chain,numbers in residues.items():
        groups=[]
        for number in sorted(numbers):
            if not groups or number-groups[-1][-1]>3: groups.append([number])
            else: groups[-1].append(number)
        clauses.extend(f'(chain {chain} and resi {g[0]-2}-{g[-1]+2})' for g in groups if len(g)>=3)
    cmd.select('context','receptor and ('+' or '.join(clauses)+')')
    cmd.hide('everything'); cmd.dss('context')
    configure_display(cmd)
    cmd.orient('ligand'); cmd.turn('x',14); cmd.turn('y',-18); cmd.zoom('ligand',7.2)
    common_view=list(cmd.get_view())
    for role in ['match','build']:
        selection=role+'_input_atoms'
        cmd.select('wall_atoms', selection+' and (byres (receptor within 4.7 of ligand))')
        for mode in ['atoms','surface','cartoon']:
            cmd.hide('everything'); cmd.show('cartoon','context')
            if mode!='cartoon':cmd.show('sticks','wall_atoms')
            cmd.color('receptor_blue','receptor');cmd.color('red','wall_atoms and elem O');cmd.color('blue','wall_atoms and elem N')
            cmd.set('stick_radius',0.13,'wall_atoms');cmd.set_view(common_view)
            if mode=='surface':
                cmd.show('surface', selection+' and (byres (receptor within 6 of ligand))')
                cmd.set_color('surface_tint',[0.76,0.84,0.87]);cmd.set('surface_color','surface_tint')
                cmd.set('transparency',0.77)
            cmd.png(str(render/'pockets'/f'{role}-{mode}.png'),1500,1100,dpi=300,ray=1)
            cmd.save(str(render/'pockets'/f'{role}-{mode}.pse'))
            manifest['pockets'].append({'role':role,'mode':mode,'input_atom_count':cmd.count_atoms(selection),
                'displayed_wall_atom_count':0 if mode=='cartoon' else cmd.count_atoms('wall_atoms'),'view':common_view,
                'definition':'10 A envelope of frozen Find blob' if role=='match' else '15 A sphere around frozen Find centroid',
                'ligand_visible':False,'context_selection':clauses})
    cmd.hide('everything');cmd.show('cartoon','context');cmd.show('sticks','ligand');configure_display(cmd);cmd.set_view(common_view)
    cmd.png(str(render/'method-output.png'),1500,1100,dpi=300,ray=1)
    cmd.save(str(render/'method-output.pse'))
    manifest['method_output']={'view':common_view,'canvas_px':[1500,1100],
        'source':'e2e-flow/views/9bjj/assets/prediction.sdf','ligand_visible':True,
        'pocket_cartoon_variant':'same context, camera and canvas with ligand hidden'}

(render/'render_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
