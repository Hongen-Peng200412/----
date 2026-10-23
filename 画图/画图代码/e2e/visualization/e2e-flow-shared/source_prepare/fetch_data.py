"""只读提取冻结端到端资产, 不执行推理或设置任何绘图属性.

读取 cases.json 的七个 CA2 实例, 入口是本文件的顺序流程. 输出到画图/画图代码/e2e/output/e2e-flow/source/source/<pdb>/：密度数组及原元数据、GT/CA2受体NPZ、原blob与GT区域NPZ、完整坐标包、冻结SDF和排名评价JSON；facts.json保留实例、身份与轨迹. source_manifest.json逐文件记录server来源、字节数与SHA256. 仅密度exp.npy在只读mmap后切出包括所展示blob的显示范围, 原采样值不变; exp_crop.json记录ZYX起点和源形状. 参考SDF只把公共SMILES图与已有世界XYZ坐标组合, 不对齐、不优化、不排序.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import subprocess
import tarfile

CODE = Path(__file__).resolve().parent
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
OUTPUT = PROJECT / 'temp/e2e_cases/refetched'
TEMP = PROJECT / 'temp/e2e_cases'
TEMP.mkdir(parents=True, exist_ok=True)
manifest = []

for case in json.loads((CODE / 'cases.json').read_text(encoding='utf-8')):
    # 每次只下载一个PDB, 避免压缩包和源图的内存叠加; Python不参与图形制备.
    request = TEMP / f"download_{case['pdb']}.sh"
    script = r'''/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/python -B - <<'PY'
from pathlib import Path
import base64,io,json,tarfile
import numpy as np
from rdkit import Chem

CASE = __CASE__
pdb,blob=CASE['pdb'],CASE['blob']
data=Path('/storage/penghongen/AdaLigand/Ori_Data')
ca2=Path('/storage/penghongen/Adaligand_infered_receptor_data/cryoatom2/test_0_chain06/Ori_Data')
root=Path('/storage/penghongen/PocketXMol/final_evaluation/end_to_end/CA2')
matcher_root=Path('/storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/strongest-1/train_strongest1_revised_job378587_20260920T230727')
blobs_path=Path('/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1/held_out_test_0')/pdb/'blobs/F2_blobs.npz'
evaluation=json.loads((root/'evaluation.json').read_text())
trace=evaluation['traces'][pdb]
hit=next(x for x in trace if x['source_blob_index']==blob)
record=next(json.loads(s) for s in (root/'inputs/base.jsonl').read_text().splitlines() if json.loads(s)['pdb_id']==pdb and json.loads(s)['source_blob_index']==blob)
folder=root/'local_cov/test/local-c1'/pdb/str(blob)
ranking=json.loads((folder/'ranking.json').read_text())
top=next(x for x in ranking['candidate_metrics'] if x['sample_index']==ranking['top1_sample_index'])
matcher=json.loads((matcher_root/'evaluation.json').read_text())
prediction=next(x for x in matcher['predictions']['cryoatom2_receptor'] if x['pdb_id']==pdb and x['source_blob_index']==blob)
# 全配体冻结预测只用于说明备选图的非Stage3身份, 不拼接进小分子推理或成功统计.
full=json.loads(Path('/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json').read_text())
full_predictions=full['predictions']['cryoatom2_receptor'][pdb]
occurrences=[json.loads(s) for s in (data/'parse'/pdb/'occurrences.jsonl').read_text().splitlines()]
target=next(x for x in occurrences if int(x['candidate_id'])==record['matched_occurrence_id'])
facts=dict(case=CASE,handoff=record,trace=trace[:hit['raw_rank']],prediction=prediction,target_occurrence=target,top1=top,method=hit['docking_stage']['methods']['local_cov-C'],full_matcher_predictions=[x for x in full_predictions if x['source_blob_index']<=blob],source_paths={'docking':str(folder),'matcher':str(matcher_root/'evaluation.json'),'full_matcher':'/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json','evaluation':str(root/'evaluation.json')})
bundle=io.BytesIO()
with tarfile.open(fileobj=bundle,mode='w:gz') as tar:
 def add_bytes(name,value):
  info=tarfile.TarInfo(pdb+'/'+name);info.size=len(value);tar.addfile(info,io.BytesIO(value))
 paths={'exp.npz':data/'density'/pdb/'exp.npz','blobs.npz':blobs_path,'gt_area.npz':data/'density'/pdb/'ligand_area.npz','gt_receptor.npz':data/'parse'/pdb/'receptor_tokens.npz','ca2_receptor.npz':ca2/'parse'/pdb/'receptor_tokens.npz','coords.npz':data/'smiles_assets/SMILE_coords/v1'/f'{pdb}.npz','occurrences.jsonl':data/'parse'/pdb/'occurrences.jsonl'}
 for name in ['poses.sdf','result.json','candidates.json','ranking.json','evaluation_metrics.json','scientific_input.json']:
  paths[name]=folder/name
 for name,path in paths.items():tar.add(str(path),arcname=pdb+'/'+name,recursive=False)
 meta=np.load(data/'density'/pdb/'exp.npz')
 density=np.load(data/'density'/pdb/'exp.npy',mmap_mode='r').squeeze()
 b=np.load(blobs_path)
 voxels=[]
 for t in trace[:hit['raw_rank']]:
  j=int(np.flatnonzero(b['blob_index']==t['source_blob_index'])[0]);lo,hi=b['voxel_offsets'][j:j+2]
  voxels.append(b['voxel_index_global_zyx'][lo:hi])
 voxels=np.concatenate(voxels)
 # 显示裁图保留所展示候选周围16Å; 不重采样、不改归一化、不改变世界坐标.
 padding=np.ceil(16/np.asarray(meta['voxel_size'])[::-1]).astype(int)
 lower=np.maximum(voxels.min(0)-padding,0);upper=np.minimum(voxels.max(0)+padding+1,density.shape)
 array=io.BytesIO();np.save(array,np.asarray(density[tuple(slice(a,z) for a,z in zip(lower,upper))],dtype=np.float32))
 add_bytes('exp_crop.npy',array.getvalue())
 add_bytes('exp_crop.json',json.dumps({'source':str(data/'density'/pdb/'exp.npy'),'start_zyx':lower.tolist(),'source_shape_zyx':list(density.shape),'shape_zyx':(upper-lower).tolist(),'margin_A':16}).encode())
 archive=np.load(data/'smiles_assets/SMILE_coords/v1'/f'{pdb}.npz')
 j=int(np.flatnonzero(archive['candidate_ids']==record['matched_occurrence_id'])[0]);lo,hi=archive['coord_offsets'][j:j+2]
 reference=Chem.RemoveAllHs(Chem.MolFromSmiles(record['target_smiles']))
 conf=Chem.Conformer(reference.GetNumAtoms())
 for i,xyz in enumerate(archive['coords'][lo:hi]):conf.SetAtomPosition(i,xyz.tolist())
 reference.AddConformer(conf);reference.SetProp('_Name',pdb+' deposited reference')
 add_bytes('reference.sdf',(Chem.MolToMolBlock(reference)+'\n$$$$\n').encode())
 add_bytes('facts.json',json.dumps(facts,ensure_ascii=False,indent=2).encode())
 add_bytes('paths.json',json.dumps({name:str(path) for name,path in paths.items()},ensure_ascii=False).encode())
print(base64.b64encode(bundle.getvalue()).decode())
PY
'''.replace('__CASE__', repr(case))
    request.write_text(script, encoding='utf-8', newline='\n')
    result = subprocess.run(['powershell.exe','-NoProfile','-File','C:/Users/15919/.codex/tools/Invoke-ProjectSsh.ps1','-Command','bash -s','-InputFile',str(request)], capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(result.stdout)), mode='r:gz') as archive:
        archive.extractall(OUTPUT / 'source', filter='data')
    sources = json.loads((OUTPUT/'source'/case['pdb']/'paths.json').read_text(encoding='utf-8'))
    for name, server in sources.items():
        file = OUTPUT/'source'/case['pdb']/name
        manifest.append(dict(local=str(file.relative_to(OUTPUT)),server=server,bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    print(case['pdb']+': frozen inputs downloaded', flush=True)
    (OUTPUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
