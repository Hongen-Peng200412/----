"""只读下载七例服务器完整 exp.npy, 保留源 SHA256 和原元数据.

本次图集专用顺序入口. 输出 formal/E2E_flow_20261003/source/<pdb>/exp.npy、exp.npz、source.json; 完整实验图不裁切、不重采样、不归一化. 服务器仅 tar 只读文件与计算 SHA256, 不运行模型或修改服务器.
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
OUTPUT = PROJECT / 'temp/e2e_flow/refetched'
TEMP = PROJECT / 'temp/e2e_flow'
TEMP.mkdir(parents=True, exist_ok=True)
manifest = []
for pdb in ['9bjj', '30ga', '9llg', '9rd8', '9qru', '9wup', '9xzl']:
    source = OUTPUT / 'source' / pdb
    source.mkdir(parents=True, exist_ok=True)
    if not (source / 'source.json').exists():
        script = r'''/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/python -B - <<'PY'
from pathlib import Path
import base64, hashlib, io, json, tarfile
pdb = '__PDB__'
root = Path('/storage/penghongen/AdaLigand/Ori_Data/density') / pdb
records = []
bundle = io.BytesIO()
with tarfile.open(fileobj=bundle, mode='w:gz') as archive:
    for name in ['exp.npy', 'exp.npz']:
        path = root / name
        records.append({'name': name, 'server': str(path), 'bytes': path.stat().st_size, 'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()})
        archive.add(str(path), arcname=name, recursive=False)
    value = json.dumps(records).encode()
    info = tarfile.TarInfo('source.json')
    info.size = len(value)
    archive.addfile(info, io.BytesIO(value))
print(base64.b64encode(bundle.getvalue()).decode())
PY
'''.replace('__PDB__', pdb).replace("hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()", "hashlib.sha256(path.read_bytes()).hexdigest()")
        request = TEMP / f'fetch_full_{pdb}.sh'
        request.write_text(script, encoding='utf-8', newline='\n')
        result = subprocess.run(['powershell.exe', '-NoProfile', '-File', 'C:/Users/15919/.codex/tools/Invoke-ProjectSsh.ps1', '-Command', 'bash -s', '-InputFile', str(request)], capture_output=True, check=True)
        with tarfile.open(fileobj=io.BytesIO(base64.b64decode(result.stdout)), mode='r:gz') as archive:
            archive.extractall(source, filter='data')
    records = json.loads((source / 'source.json').read_text())
    for record in records:
        path = source / record['name']
        assert path.stat().st_size == record['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
        manifest.append(dict(record, local=str(path.relative_to(OUTPUT))))
    (OUTPUT / 'full_density_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(pdb + ': full source density downloaded and SHA256 verified', flush=True)
