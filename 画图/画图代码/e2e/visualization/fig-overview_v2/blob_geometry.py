"""为流程示意创建三个不规则候选体，不读取或改动模型预测。"""
import os
import json
from pathlib import Path
import numpy as np
from chimerax.map._map import contour_surface

z,y,x=np.mgrid[-2:2:21j,-3.3:3.3:31j,-2:2:21j]
centers=[
    [(-.3,-1.65,.1,.85),(.22,-.65,-.12,.8),(-.05,.35,.1,.77),(.35,1.4,0,.86)],
    [(-.55,-.95,0,.83),(.4,-.7,.1,.87),(.55,.35,-.1,.78),(-.35,1.1,.15,.78)],
    [(-.3,-1.6,0,.8),(.35,-.6,.15,.93),(-.32,.55,0,.85),(-.15,1.55,-.15,.68)]
]
result=[]
for cs in centers:
    density=np.zeros(x.shape)
    for cx,cy,cz,r in cs:
        density+=np.exp(-((x-cx)**2+(y-cy)**2+(z-cz)**2)/(2*(r*.68)**2))
    v,t,n=contour_surface(density.astype('f4'),.55,calculate_normals=True)
    v[:,0]=v[:,0]/20*4-2;v[:,1]=v[:,1]/30*6.6-3.3;v[:,2]=v[:,2]/20*4-2
    mid=(v.max(0)+v.min(0))/2;v-=mid;v/=np.ptp(v,axis=0)
    result.append({'v':v.tolist(),'t':t.tolist(),'n':n.tolist()})
paper=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file() and (p/'论文草稿.md').is_file())
build = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else paper/'temp/fig-overview_v2'
build.mkdir(parents=True,exist_ok=True)
(build/'blobs.json').write_text(json.dumps(result),encoding='utf-8')
print([len(a['t']) for a in result])
