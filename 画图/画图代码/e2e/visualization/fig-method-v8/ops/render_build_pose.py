"""对完整坐标选取连续局部片段，比较真实口袋在小幅面中的可读性。"""
import os
from pathlib import Path
import json
import pymol2

workspace = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
base = Path(os.environ["FIGURE_RENDER_ROOT"]) / "build-pose-9bjj" if "FIGURE_RENDER_ROOT" in os.environ else workspace / 'temp/fig-method-v8/rendered/build-pose-9bjj'
base.mkdir(parents=True, exist_ok=True)
root = workspace / '画图/画图代码/e2e/output/e2e-flow/views'
with pymol2.PyMOL() as pm:
    c=pm.cmd
    records={}
    for case in ['9bjj']:
        c.reinitialize()
        c.load(str(root/case/'assets/ca2_receptor.cif'),'receptor')
        c.load(str(root/case/'assets/prediction.sdf'),'ligand')
        c.remove('hydro')
        atoms=c.get_model('byres (receptor within 7 of ligand)').atom
        residues={}
        for a in atoms:residues.setdefault(a.chain,set()).add(int(a.resi))
        chunks=[]
        for chain,nums in residues.items():
            groups=[]
            for n in sorted(nums):
                if not groups or n-groups[-1][-1]>3:groups.append([n])
                else:groups[-1].append(n)
            chunks.extend(f'(chain {chain} and resi {g[0]-2}-{g[-1]+2})' for g in groups if len(g)>=3)
        c.select('pocket','receptor and ('+' or '.join(chunks)+')')
        c.hide('everything')
        c.show('cartoon','pocket')
        c.set_color('pocket_gray',[0.71,0.77,0.79]);c.color('pocket_gray','receptor')
        c.set_color('ligand_teal',[0.10,0.51,0.43]);c.color('ligand_teal','ligand')
        c.show('sticks','ligand')
        c.color('red','ligand and elem O');c.color('blue','ligand and elem N');c.color('orange','ligand and elem P')
        c.set('stick_radius',0.28,'ligand')
        c.set('cartoon_loop_radius',0.16)
        c.set('cartoon_fancy_helices',1)
        c.set('cartoon_transparency',0.27,'receptor')
        c.set('orthoscopic',1);c.set('ray_shadows',0);c.set('specular',0.10)
        c.set('ambient',0.56);c.set('direct',0.65);c.set('antialias',2)
        c.bg_color('white');c.set('ray_opaque_background',0)
        c.orient('ligand');c.zoom('pocket or ligand',1.5)
        view=c.get_view()
        for tag,y,x in [('a',0,0),('b',-50,25),('c',45,-30)]:
            c.set_view(view);c.turn('y',y);c.turn('x',x)
            c.png(str(base/f'{case}_{tag}.png'),1400,950,dpi=300,ray=1)
            records[case+'_'+tag]={'selection':chunks,'view':list(c.get_view())}
        c.save(str(base/f'{case}.pse'))
    (base/'refined_views.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
