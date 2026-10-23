"""只读提取候选案例的冻结姿态、受体和局部实验密度，保存本地筛选副本。"""
import base64,io,json,subprocess,tarfile
from pathlib import Path

project=Path(__file__).resolve().parents[6]
root=project/'temp/stage3-case-sources'
root.mkdir(parents=True,exist_ok=True)
rows=json.loads((root/'screen.json').read_text(encoding='utf-8'))
selected={}
for field in ['official','build']:
    seen=set()
    for r in sorted(rows,key=lambda r:r[field]-r['tuned'],reverse=True):
        if r['pdb_id'] not in seen and r[field]<20:
            selected[(r['pdb_id'],r['occurrence_id'])]=r;seen.add(r['pdb_id'])
        if len(seen)==18:break
keys=list(selected)
(root/'shortlist.json').write_text(json.dumps(list(selected.values()),indent=2),encoding='utf-8')
code='''import base64,io,json,tarfile,hashlib
from pathlib import Path
import numpy as np,gemmi
from rdkit import Chem
ROOT=Path('/storage/penghongen/AdaLigand/Ori_Data')
FROZEN={ (r['pdb_id'],r['candidate_id']):r for r in map(json.loads,open('/storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl')) }
BUILD={ (r['pdb_id'],r['occurrence_id']):r for r in map(json.loads,open('/storage/penghongen/Emap2lig/stage3_find_hit_build/build_occurrences.jsonl')) }
keys=KEYS_PLACEHOLDER
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as archive:
 for pdb,occ in keys:
  rec=FROZEN[(pdb,occ)];smiles=rec['prepared_smiles'];mol=Chem.RemoveHs(Chem.MolFromSmiles(smiles))
  a=np.load(ROOT/'smiles_assets/SMILE_coords/v1'/f'{pdb}.npz',allow_pickle=False)
  ix=int(np.flatnonzero(a['candidate_ids']==occ)[0]);start,stop=a['coord_offsets'][ix:ix+2];gt=a['coords'][start:stop];a.close()
  poses={'gt':gt};sources=[];metrics={}
  for name,model in [('official','official-SMILES'),('tuned','local_cov-C-T0-RA')]:
   folder=Path('/storage/penghongen/PocketXMol/sampling')/model/'test/C0'/pdb/str(occ)
   assessment=json.loads((folder/'assessment.json').read_text());metric=json.loads((folder/'candidate_metrics.json').read_text())
   occurrence=next(r for r in json.loads((folder.parents[1]/'occurrences.json').read_text()) if r['pdb_id']==pdb and r['occurrence_id']==occ)
   idx=occurrence['top1_sample_index'];supplier=Chem.SDMolSupplier(str(folder/'poses.sdf'),removeHs=False)
   pose=next(m for m in supplier if m is not None and m.GetIntProp('sample_index')==idx)
   poses[name]=Chem.RemoveHs(pose).GetConformer().GetPositions()
   metrics[name]=dict(sample_index=idx,rmsd=occurrence['top1_rmsd_A'],assessment=assessment,metrics=metric)
   sources.append(str(folder/'poses.sdf'))
  b=BUILD[(pdb,occ)];lig=np.load(Path(b['result_dir'])/'preprocess/ligands/LIG.npz',allow_pickle=False)
  names=lig['atom_names'].astype(str);lig.close()
  block=gemmi.cif.read_file(b['poses'][0]['cif']).sole_block()
  table=block.find(['_atom_site.label_atom_id','_atom_site.Cartn_x','_atom_site.Cartn_y','_atom_site.Cartn_z'])
  coords={r[0]:[float(r[j]) for j in (1,2,3)] for r in table};poses['build']=np.array([coords[n] for n in names]);sources.append(b['poses'][0]['cif'])
  receptor=np.load(ROOT/'parse'/pdb/'receptor_tokens.npz',allow_pickle=False)
  rc=receptor['coords'];keep=receptor['res_type']<28
  allpose=np.concatenate(list(poses.values()));keep &= np.linalg.norm(rc[:,None,:]-allpose[None,:,:],axis=2).min(axis=1)<8
  ids=np.flatnonzero(keep);mapping=np.full(len(rc),-1);mapping[ids]=np.arange(len(ids));bi=receptor['bond_index'];bk=keep[bi].all(axis=0)
  payload={**poses,'element':np.array([at.GetAtomicNum() for at in mol.GetAtoms()]),'bonds':np.array([[b.GetBeginAtomIdx(),b.GetEndAtomIdx(),b.GetBondTypeAsDouble()] for b in mol.GetBonds()]),'receptor_xyz':rc[keep],'receptor_element':receptor['element'][keep],'receptor_bonds':mapping[bi[:,bk]].T,'receptor_res_index':receptor['res_index'][keep],'receptor_atom_name':receptor['atom_name'][keep]}
  meta=np.load(ROOT/'density'/pdb/'exp.npz');density=np.load(ROOT/'density'/pdb/'exp.npy',mmap_mode='r').squeeze();origin=meta['origin'];d=meta['voxel_size']
  lo=np.maximum(np.floor((allpose.min(0)-9-origin)/d).astype(int),0);hi=np.minimum(np.ceil((allpose.max(0)+9-origin)/d).astype(int),np.array(density.shape[::-1]));s=tuple(slice(l,h) for l,h in zip(lo[::-1],hi[::-1]));payload.update(density=np.array(density[s]),origin=origin+lo*d,voxel_size=d,contour=float(meta['contour_canonical']))
  occrow=next(json.loads(l) for l in (ROOT/'parse'/pdb/'occurrences.jsonl').open() if json.loads(l)['candidate_id']==occ)
  metadata=dict(pdb_id=pdb,occurrence_id=occ,smiles=smiles,occurrence=occrow,metrics=metrics,build=b['poses'][0],sources=sources,density_source=str(ROOT/'density'/pdb/'exp.npy'),density_slice_xyz=[lo.tolist(),hi.tolist()],source_map_sha256=str(meta['source_map_sha256']))
  for filename,data in [(f'{pdb}_{occ}/arrays.npz',None),(f'{pdb}_{occ}/metadata.json',json.dumps(metadata).encode())]:
   if data is None:
    f=io.BytesIO();np.savez_compressed(f,**payload);data=f.getvalue()
   info=tarfile.TarInfo(filename);info.size=len(data);archive.addfile(info,io.BytesIO(data))
print(base64.b64encode(buf.getvalue()).decode())
'''.replace('KEYS_PLACEHOLDER',repr(keys))
request=root/'fetch_readonly.sh';request.write_text('/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/python - <<\'PY\'\n'+code+'\nPY\n',encoding='utf-8',newline='\n')
result=subprocess.run(['powershell.exe','-NoProfile','-File','C:/Users/15919/.codex/tools/Invoke-ProjectSsh.ps1','-Command','bash -s','-InputFile',str(request)],capture_output=True)
if result.returncode:
    print(result.stderr.decode(errors='replace'));raise SystemExit(result.returncode)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(result.stdout)),mode='r:gz') as archive:
    archive.extractall(root/'source',filter='data')
print('Fetched',len(keys),'frozen cases')
