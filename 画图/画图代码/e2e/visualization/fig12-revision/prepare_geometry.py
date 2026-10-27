"""构造两图的化学结构坐标与冻结 blob 世界坐标。

直接执行模块，写 FIGURE_BUILD_ROOT/geometry.json：molecules 按 SMILES
保存二维原子坐标及真实键型；pocket_blob_xyz_A 为9BJJ原Find候选中
非零体素中心的XYZ世界坐标。这里只进行显示几何转换，不重算模型。
"""
import json
import os
import sys
from pathlib import Path

root=next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').exists())
sys.path.insert(0,str(root/'.manuscript_deps/figure_runtime'))
import numpy as np
import mrcfile
from rdkit import Chem
from rdkit.Chem import rdDepictor

build=Path(os.environ['FIGURE_BUILD_ROOT']);build.mkdir(parents=True,exist_ok=True)
result={'molecules':[]}
for smiles in ['CCO','CC(=O)O','Cc1ccccc1','CC(N)=O']:
    mol=Chem.MolFromSmiles(smiles);Chem.Kekulize(mol,clearAromaticFlags=True);rdDepictor.Compute2DCoords(mol)
    conformer=mol.GetConformer()
    result['molecules'].append({'smiles':smiles,'atoms':[{'x':conformer.GetAtomPosition(i).x,'y':conformer.GetAtomPosition(i).y,'element':a.GetSymbol(),'hydrogens':a.GetTotalNumHs()} for i,a in enumerate(mol.GetAtoms())],
        'bonds':[{'start':b.GetBeginAtomIdx(),'stop':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble()} for b in mol.GetBonds()]})
blob=root/'画图/画图代码/e2e/output/e2e-flow/views/9bjj/assets/blob_0.mrc'
with mrcfile.open(blob,permissive=True) as m:
    zyx=np.argwhere(m.data>0)
    spacing=np.array([m.voxel_size.x,m.voxel_size.y,m.voxel_size.z],dtype=float)
    origin=np.array([m.header.origin.x,m.header.origin.y,m.header.origin.z],dtype=float)
    result['pocket_blob_xyz_A']=(zyx[:,::-1]*spacing+origin).tolist()
    result['blob_source']=str(blob.relative_to(root))
(build/'geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
