"""从服务器只读下载七个 PDB 的基础数据和冻结预测, 不控制 ChimeraX 显示.

输入 cases.json 的 pdb 标识和项目既有来源配置; 输出到 formal/Stage1_fourcase_20260930/source/<pdb>/.
旧六例复用冻结来源; 缺失时从服务器下载。每个 PDB 保留 data/ 的密度、GT、原子和沉积 CIF, real/cryo/emap 的 blobs.npz 与 evaluation.npz.
source_manifest.json 记录 local/server/bytes/sha256. SSH 请求临时文件统一放入仓库 temp/.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
OUTPUT = PROJECT / '画图/画图代码/stage1/output/stage1-fourcase-main/base'
TEMP = PROJECT / 'temp/stage1_chimera_v3'
PROFILE = json.loads(Path('C:/Users/15919/Desktop/AdaLigand/可视化套件/Stage1/profiles/stage1_7mode_pcv2_test0.json').read_text(encoding='utf-8'))
manifest = []
for case in json.loads((ROOT / 'cases.json').read_text(encoding='utf-8')):
    pdb = case['pdb']
    previous = PROJECT / '画图/画图代码/stage1/output/stage1-fourcase-main/source_history/source'
    source_root = previous if (previous / pdb).is_dir() else OUTPUT / 'source'
    paths = []
    for sub in (f'density/{pdb}/exp.npy', f'density/{pdb}/exp.npz', f'density/{pdb}/ligand_area.npz',
                f'parse/{pdb}/occurrences.jsonl', f'parse/{pdb}/ligand_coords.npz', f'parse/{pdb}/receptor_tokens.npz', f'raw/rcsb_mmcif/{pdb}.cif'):
        paths.append((f'{pdb}/data/{Path(sub).name}', f"{PROFILE['data_root']}/{sub}"))
    paths.append((f'{pdb}/cryo/receptor_tokens.npz', f"{PROFILE['receptor_roots']['cryoatom2']}/parse/{pdb}/receptor_tokens.npz"))
    for index, name in zip((3, 5, 6), ('real', 'cryo', 'emap')):
        mode = PROFILE['modes'][index]
        if name != 'emap':
            base = f"{mode['artifact_root']}/{mode['producer']}/{mode['split']}/{pdb}"
            blobs, evaluation = f'{base}/blobs/F2_blobs.npz', f"{base}/evaluation/{mode['evaluation_name']}.npz"
        else:
            blobs = f"{mode['result_root']}/mapped/{pdb}/official_blobs.npz"
            evaluation = f"{mode['result_root']}/evaluation/per_pdb/{pdb}.npz"
        paths.extend(((f'{pdb}/{name}/blobs.npz', blobs), (f'{pdb}/{name}/evaluation.npz', evaluation)))
    missing = [(local, remote) for local, remote in paths if not (source_root / local).exists()]
    if missing:
        remote_script = "python3 -B - <<'PY'\nimport tarfile,base64,io\nfiles=" + repr(missing) + "\nbuf=io.BytesIO()\nwith tarfile.open(fileobj=buf,mode='w:gz') as t:\n for local,remote in files: t.add(remote,arcname=local,recursive=False)\nprint(base64.b64encode(buf.getvalue()).decode())\nPY\n"
        request = TEMP / f'download_{pdb}.sh'
        request.write_text(remote_script, encoding='utf-8', newline='\n')
        result = subprocess.run(['powershell.exe', '-NoProfile', '-File', 'C:/Users/15919/.codex/tools/Invoke-ProjectSsh.ps1', '-Command', 'bash -s', '-InputFile', str(request)], capture_output=True, check=True)
        with tarfile.open(fileobj=io.BytesIO(base64.b64decode(result.stdout)), mode='r:gz') as archive:
            archive.extractall(source_root, filter='data')
    for local, remote in paths:
        file = source_root / local
        manifest.append(dict(local=local, path=file.relative_to(PROJECT).as_posix(), server=remote, bytes=file.stat().st_size, sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    print(f'{pdb}: {len(paths)} source files ready', flush=True)
    (OUTPUT / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
