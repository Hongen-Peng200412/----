"""在保存的首位姿态上计算密度覆盖和原受体距离碰撞, 不参与选姿态。"""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial.distance import cdist

root=Path(__file__).resolve().parents[6]/'temp/stage3-case-sources'
vdw={5:1.8,6:1.7,7:1.6,8:1.55,9:1.5,15:1.95,16:1.8,17:1.8,34:1.9,35:1.9,53:2.1}
rows=[]
for folder in sorted((root/'source').iterdir()):
    a=np.load(folder/'arrays.npz',allow_pickle=False)
    meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    row=dict(pdb_id=meta['pdb_id'],occurrence_id=meta['occurrence_id'],occurrence=meta['occurrence'])
    # 半径与原评价的 RDKit 范德华半径表一致. 每个配体-受体原子对独立计数.
    radius=np.array([vdw[int(e)] for e in a['element']])
    rr=np.array([vdw[int(e)] for e in a['receptor_element']])
    for method in ['gt','official','tuned','build']:
        xyz=a[method]
        index=((xyz-a['origin'])/a['voxel_size']-0.5)[:,::-1]
        values=map_coordinates(a['density'],index.T,order=1,mode='constant',cval=np.nan)
        dist=cdist(xyz,a['receptor_xyz']);clash=dist<0.75*(radius[:,None]+rr[None,:])
        row[method]=dict(density_fraction=float(np.mean(values>=a['contour'])),density_mean=float(np.mean(values)),clash_pairs=int(clash.sum()),clash_atoms=int(clash.any(1).sum()),min_dist=float(dist.min()),clash_indices=np.argwhere(clash).tolist())
        if method in ['official','tuned']:
            row[method]['rmsd']=meta['metrics'][method]['rmsd']
        if method=='build':row[method]['rmsd']=meta['build']['rmsd_A']
    rows.append(row)
(root/'case_metrics.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
for r in rows:
    print(r['pdb_id'],r['occurrence_id'],str(r['occurrence'])[:150])
    print({m:{k:round(v,3) if isinstance(v,float) else v for k,v in r[m].items() if k in ['rmsd','density_fraction','clash_pairs','clash_atoms','min_dist']} for m in ['gt','official','tuned','build']})
