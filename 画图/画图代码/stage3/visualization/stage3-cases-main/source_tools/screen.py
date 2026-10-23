"""从冻结首位姿态指标筛选两类可视化案例，不改变推理或排名。"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[6]
data = json.loads((root/'画图/画图代码/stage3/output/stage3-official-tuned/data.json').read_text(encoding='utf-8'))
series = {f"{s['model']}/{s['receptor']}/{s['protocol']}": {(r['pdb_id'], r['occurrence_id']):r for r in s['rows']} for s in data['series']}
build = {(r['pdb_id'],r['occurrence_id']):r for r in data['build']}
rows=[]
for key,b in build.items():
    o=series['official/GT/C0'][key]['top1']
    t=series['local_cov/GT/C0'][key]['top1']
    if b['top1'] is not None and o is not None and t is not None and t<1.5:
        rows.append(dict(pdb_id=key[0],occurrence_id=key[1],official=o,tuned=t,build=b['top1']))
rows.sort(key=lambda r:r['official']-r['tuned'], reverse=True)
(root/'temp/stage3-case-sources').mkdir(parents=True,exist_ok=True)
(root/'temp/stage3-case-sources/screen.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('OFFICIAL FAILURE SHORTLIST')
seen=set()
for r in rows:
    if r['pdb_id'] not in seen and r['official']<20:
        print(r);seen.add(r['pdb_id'])
    if len(seen)==14:break
print('BUILD FAILURE SHORTLIST')
seen=set()
for r in sorted(rows,key=lambda r:r['build']-r['tuned'],reverse=True):
    if r['pdb_id'] not in seen and r['build']<10:
        print(r);seen.add(r['pdb_id'])
    if len(seen)==14:break
