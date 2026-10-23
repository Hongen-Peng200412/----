import json
from pathlib import Path
root=Path(__file__).resolve().parents[6]
rows=json.loads((root/'画图/画图代码/stage3/output/stage3-cases-main/cases.json').read_text(encoding='utf8'))
for r in rows:
 for m in ['official','tuned']:
  a=r['metadata']['metrics'][m]; saved=next(x for x in a['metrics'] if x['sample_index']==a['sample_index'])
  assert saved['rmsd_A']==r[m]['rmsd']
  assert saved['num_clashes']==r[m]['clash_pairs'],(r['pdb_id'],m,saved['num_clashes'],r[m]['clash_pairs'])
print('All 20 PocketXMol Top-1 RMSD and clash pair counts match frozen metrics')
