"""从本地受体坐标渲染清晰的 cartoon 图示，不改动坐标。"""
import os
from pathlib import Path
from collections import Counter
import json
import pymol2

root = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
b = Path(os.environ["FIGURE_RENDER_ROOT"]) / "receptor-9llg" if "FIGURE_RENDER_ROOT" in os.environ else root / 'temp/fig-method-v8/rendered/receptor-9llg'
b.mkdir(parents=True, exist_ok=True)
assets = root / '画图/画图代码/e2e/output/e2e-flow/views/9llg/assets'
with pymol2.PyMOL() as pm:
    c=pm.cmd
    c.load(str(assets/'ca2_receptor.cif'),'receptor')
    c.load(str(assets/'prediction.sdf'),'ligand')
    nearby=Counter(a.chain for a in c.get_model('receptor within 7 of ligand').atom)
    chain=nearby.most_common(1)[0][0]
    print('Chain near ligand:',nearby,'selected:',chain)
    c.select('shown',f'receptor and chain {chain} and polymer.protein')
    c.hide('everything');c.show('cartoon','shown')
    c.set_color('receptor_blue',[.39,.53,.61]);c.color('receptor_blue','shown')
    c.set('cartoon_fancy_helices',1);c.set('cartoon_smooth_loops',1)
    c.set('cartoon_flat_sheets',1);c.set('cartoon_loop_radius',.20)
    c.set('cartoon_sampling',24);c.set('cartoon_discrete_colors',1)
    c.set('antialias',2);c.set('ray_trace_mode',0);c.set('ray_shadows',0)
    c.set('ambient',.38);c.set('direct',.75);c.set('specular',.22)
    c.set('orthoscopic',1);c.bg_color('white');c.set('ray_opaque_background',0)
    c.viewport(1400,1600)
    c.orient('shown');c.zoom('shown',3)
    v=c.get_view()
    views={}
    for tag,y,x in [('a',0,0),('b',45,10),('c',-35,-10)]:
        c.set_view(v);c.turn('y',y);c.turn('x',x)
        c.png(str(b/f'receptor_{tag}.png'),1400,1600,dpi=600,ray=1)
        views[tag]=list(c.get_view())
    c.viewport(1400,1800)
    c.set_view(views['b']);c.turn('z',35);c.zoom('shown',3)
    c.png(str(b/'receptor_final.png'),1400,1800,dpi=600,ray=1)
    views['final']=list(c.get_view())
    c.save(str(b/'receptor.pse'))
    (b/'receptor_views.json').write_text(json.dumps({'source':'9llg/ca2_receptor.cif','chain':chain,'views':views},indent=2),encoding='utf8')
