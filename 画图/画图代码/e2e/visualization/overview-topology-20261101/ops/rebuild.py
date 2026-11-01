"""在全新的 temp 目录依次执行拓扑准备、两种原生渲染和第13页装配.

--build-root 指定新目录; 回执 receipt.json 记录各步骤及旧 temp 屏蔽状态.
仅生成候选, 不写正式 PPT, 不更新稿件或 Git.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--build-root', type=Path, required=True)
args = parser.parse_args()
code = Path(__file__).resolve().parents[1]
root = code.parents[4]
build = args.build_root.resolve()
build.mkdir(parents=True, exist_ok=False)
support = root / '转换工具/ops/rebuild_support'
environment = dict(os.environ, FIGURE_VERIFY_ROOT=str(root), FIGURE_BUILD_ROOT=str(build),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
commands = [
    ['D:/Anaconda/python.exe', '-X', 'utf8', '-B', str(code / 'prepare.py')],
    ['D:/Pymol/python.exe', '-B', str(code / 'render_identities.py')],
    ['powershell.exe', '-NoProfile', '-File', str(support / 'run_chimerax.ps1'), '-CxcPath', str(code / 'render_poses.py'), '-LogPrefix', str(build / 'chimerax')],
    ['D:/Anaconda/python.exe', '-X', 'utf8', '-B', str(code / 'assemble.py')],
]
steps = []
for number, command in enumerate(commands, 1):
    dependencies = [support, root / '.manuscript_deps/figure_runtime'] if command[0].startswith('D:/Anaconda') else [support]
    environment['PYTHONPATH'] = os.pathsep.join(map(str, dependencies))
    with (build / f'step-{number}.log').open('w', encoding='utf8') as log:
        result = subprocess.run(command, cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT)
    steps.append(dict(command=command, exit_code=result.returncode))
    (build / 'receipt.json').write_text(json.dumps(dict(steps=steps, passed=result.returncode == 0 and number == 4, old_temp_blocked=True), indent=2), encoding='utf8')
    if result.returncode:
        raise RuntimeError(f'生成步骤{number}失败, 详见本次 step-{number}.log')
print(build / 'candidate.pptx')
