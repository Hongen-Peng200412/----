"""用 PyMOL 原生光线追踪渲染三种 RDKit 游离构象.

直接执行 main. FIGURE_BUILD_ROOT/scene.json 提供同一原子轴的元素、CCD 原子名、键和 ideal_xyz(Å).
render/identity-<CCD>.png 为透明球棍图, 同名 PSE 保存可重新编辑的原生场景; identity_manifest.json 保存三个显示相机.
全局密度、受体、候选和结合构象统一交给 render_chimerax.py, 避免跨软件混用全局相机.
"""
import json
import os
from pathlib import Path

import pymol2
from chempy import Atom, Bond
from chempy.models import Indexed


def load_ligand(cmd, identity):
    """按规范 SMILES 的原子轴加载理想 XYZ 和真实键, 设置碳的身份色及杂原子的元素色."""
    model = Indexed()
    for i, (element, point) in enumerate(zip(identity['elements'], identity['ideal_xyz'])):
        atom = Atom()
        atom.coord = list(map(float, point))
        atom.symbol = element
        atom.name = identity['atom_names'][i]
        atom.resn, atom.resi, atom.chain, atom.hetatm = identity['id'], '1', 'L', 1
        model.atom.append(atom)
    for start, stop, order in identity['bonds']:
        bond = Bond()
        bond.index = [start, stop]
        bond.order = int(order)
        model.bond.append(bond)
    cmd.load_model(model, 'identity')
    cmd.set_color('identity_carbon', [int(identity['color'][i:i+2], 16)/255 for i in (1,3,5)])
    cmd.color('identity_carbon', 'identity')
    cmd.color('oxygen', 'identity and elem O')
    cmd.color('nitrogen', 'identity and elem N')
    cmd.color('sulfur', 'identity and elem S')


def setup(cmd):
    """三种配体共用透明白底、正交投影、原生球棍和相同光照."""
    cmd.bg_color('white')
    settings = dict(orthoscopic=1, ray_opaque_background=0, ray_shadows=0, specular=0.18, shininess=40, ambient=0.50, direct=0.68, antialias=2, depth_cue=0, ray_trace_fog=0, sphere_quality=3, stick_quality=16, valence=1, valence_size=0.10, sphere_scale=0.25, stick_radius=0.21)
    for name, value in settings.items():
        cmd.set(name, value)


# ================================================================================================
def main():
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    render = build / 'render'
    render.mkdir(exist_ok=True)
    scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
    manifest = {}
    with pymol2.PyMOL() as pm:
        cmd = pm.cmd
        for identity in scene['identities']:
            cmd.reinitialize()
            setup(cmd)
            load_ligand(cmd, identity)
            cmd.hide('everything')
            cmd.show('sticks', 'identity')
            cmd.show('spheres', 'identity')
            cmd.orient('identity')
            cmd.turn('x', 24)
            cmd.turn('y', -18)
            cmd.viewport(900, 620)
            cmd.zoom('identity', 0.7, complete=1)
            name = 'identity-' + identity['id']
            cmd.png(str(render / (name+'.png')), 900, 620, dpi=300, ray=1)
            cmd.save(str(render / (name+'.pse')))
            manifest[identity['id']] = {'view':list(cmd.get_view()), 'smiles':identity['smiles'], 'ideal_bound_best_rmsd_A':identity['ideal_bound_best_rmsd_A']}
            print(name, flush=True)
    (render / 'identity_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
