"""在 ChimeraX 中加载一个 PDB 并保存含密度的会话; 不设置任何绘图风格或相机.

使用: runscript "本文件绝对路径" 9wq3
模型编号按 data.json::files 顺序为 #1 至 #12. 会话保存为每 PDB 的 session.cxs.
重新运行会覆盖该生成会话; 手动调整后的版本请先另存.
"""
from pathlib import Path
import json
import sys
from chimerax.core.commands import run

ROOT = Path(__file__).resolve().parent
PROJECT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file() and (p / "论文草稿.md").is_file())
destination = PROJECT / '画图/画图代码/stage1/output/stage1-fourcase-main/display' / sys.argv[1]
config = json.loads((destination / 'data.json').read_text(encoding='utf-8'))
run(session, 'close all')
for filename in config['files']:
    run(session, f'open "{(PROJECT / "画图/画图代码/stage1/output/stage1-fourcase-main/base" / sys.argv[1] / "assets" / filename).as_posix()}"')
rebuild = destination.parent / "regenerated" / destination.name
rebuild.mkdir(parents=True, exist_ok=True)
run(session, f'save "{(rebuild / "session.cxs").as_posix()}" includeMaps true')
