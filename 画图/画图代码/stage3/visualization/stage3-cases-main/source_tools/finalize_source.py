import json,csv,hashlib,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[6]; out=root/'画图/画图代码/stage3/output/stage3-cases-main'
new=json.loads((out/'case_metrics.json').read_text(encoding='utf8')); old={(r['pdb_id'],r['occurrence_id']):r for r in json.loads((root/'temp/stage3-case-sources/case_metrics.json').read_text(encoding='utf8'))}
assert all(r==old[r['pdb_id'],r['occurrence_id']] for r in new)
with (out/'case_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f); w.writerow(['PDB','occurrence','CCD','chain','residue','method','RMSD_A','density_percent','clash_pairs','clash_atoms','min_distance_A'])
 for r in new:
  c=r['occurrence']['components'][0]
  for m in ['official','tuned','build']:
   v=r[m]; w.writerow([r['pdb_id'],r['occurrence_id'],c['ccd_id'],c['auth_asym_id'],c['auth_seq_id'],m,v['rmsd'],100*v['density_fraction'],v['clash_pairs'],v['clash_atoms'],v['min_dist']])
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'assets').rglob('*')) if p.is_file()}
(out/'source_sha256.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
shutil.copy2(root/'temp/stage3-case-sources/case_metrics.json',out/'screening_metrics.json')
print('Offline metrics identical to screening. Saved CSV and asset hashes.')
