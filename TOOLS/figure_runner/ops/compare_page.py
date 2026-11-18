"""只读比较候选与作者图集中同一稳定图名的原生全页显示.

本运维入口不读取实验数据, 不修改图集, 不把显示一致当作科学等价. --build指定根temp内的新空目录, 产物为独立输入副本、全页PNG及comparison.json; 原始输入前后摘要必须一致.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = next(path for path in Path(__file__).resolve().parents if (path / '论文草稿.md').is_file())
sys.path.insert(0, str(ROOT))
from TOOLS.runtime.paths import configure_runtime
configure_runtime(ROOT)
from TOOLS.ppt.deck import Deck
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--author', type=Path, required=True)
parser.add_argument('--figure', required=True)
parser.add_argument('--width', type=int, required=True)
parser.add_argument('--build', type=Path, required=True)
args = parser.parse_args()
build = args.build.resolve()
build.relative_to(ROOT / 'temp')
if args.width <= 0 or (build.exists() and any(build.iterdir())):
    raise ValueError('图幅必须为正整数, 本次比较目录必须为空')
build.mkdir(parents=True, exist_ok=True)
inputs = {'candidate': args.candidate.resolve(), 'author': args.author.resolve()}
inputs['candidate'].relative_to(ROOT / 'temp')
inputs['author'].relative_to(ROOT)
before = {}
manifest = []
pages = {}
for role, path in inputs.items():
    raw = path.read_bytes()
    before[role] = hashlib.sha256(raw).hexdigest()
    copied = build / (role + '.pptx')
    copied.write_bytes(raw)
    deck = Deck(copied)
    page = deck.figures[args.figure].page
    pages[role] = page
    manifest.append({'path': str(copied), 'slides': [{'page': page, 'output': str(build / (role + '.png'))}]})
manifest_path = build / 'render.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
subprocess.run([
    'powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
    '-File', str(ROOT / 'TOOLS/ppt/export_slide.ps1'),
    '-ManifestPath', str(manifest_path), '-WidthPx', str(args.width),
], check=True)
arrays = {}
for role in inputs:
    with Image.open(build / (role + '.png')) as picture:
        arrays[role] = np.asarray(picture.convert('RGB')).astype(np.int16)
equal_shape = arrays['candidate'].shape == arrays['author'].shape
difference = np.abs(arrays['candidate'] - arrays['author']) if equal_shape else None
changed = int(np.any(difference != 0, axis=2).sum()) if equal_shape else None
maximum = int(difference.max()) if equal_shape else None
after = {role: hashlib.sha256(path.read_bytes()).hexdigest() for role, path in inputs.items()}
unchanged = before == after
passed = equal_shape and changed == 0 and unchanged
report = {
    'figure': args.figure,
    'inputs': {role: {'path': str(path), 'sha256': before[role], 'page': pages[role]} for role, path in inputs.items()},
    'shape_yxc': {role: list(value.shape) for role, value in arrays.items()},
    'different_pixels': changed, 'max_rgb_difference': maximum,
    'source_files_unchanged': unchanged, 'passed': passed,
    'meaning': '只证明本次原生全页显示一致; 科学来源与计算须另按Figure契约核验',
}
(build / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if passed else 1)
