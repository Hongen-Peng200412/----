"""从 D 盘服务器原件完整重建一张候选图, 不读取既有 PNG、CXS 或旧 temp.

由转换工具/ops/rebuild_figures.py调用. 本工具只编排材料转换、官方原生渲染和图片装配;
原始清单来自同次 prepare_sources, 大文件用 NTFS 硬链接读取固定下载缓存.
新 ChimeraX 进程显示工作窗口, 继承旧 temp 屏蔽规则, 独立完成后退出.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--figure", required=True)
parser.add_argument("--build-root", type=Path, required=True)
parser.add_argument("--source-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
args = parser.parse_args()
code = Path(__file__).resolve().parent.parent
root = next(p for p in code.parents if (p / "论文草稿.md").exists())
build = args.build_root.resolve()
data = build / "data"
data.mkdir(parents=True)
cases = (
    ["11jb", "9bjj", "9lov", "9okp", "30ga", "9ujf", "9wup", "9lw1", "9llg"]
    if args.figure == "multiligand-workbench"
    else [args.figure.removeprefix("multiligand-workbench-")]
)
python = [sys.executable, "-X", "utf8", "-B"]
subprocess.run(
    python
    + [
        str(code / "prepare_sources.py"),
        "--data-root",
        str(data),
        "--output-root",
        str(build / "metadata"),
        "--pdb",
        *cases,
    ],
    check=True,
)
requests = json.loads((build / "metadata/download_requests.json").read_text(encoding="utf-8"))
for record in requests:
    source = args.source_root / "_server" / record["remote"].lstrip("/")
    target = data / record["local"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.drive.lower() == target.drive.lower():
        os.link(source, target)
    else:
        shutil.copyfile(source, target)
subprocess.run(python + [str(code / "prepare_assets.py"), "--data-root", str(data)], check=True)
subprocess.run(python + [str(code / "prepare_views.py"), "--data-root", str(data)], check=True)

# 原生命令行对中文参数转码; 仅给本次构建建立 ASCII 联接, 不复制或修改原件.
junction = args.source_root / ("_build_" + build.parent.name + "_" + args.figure)
subprocess.run(
    [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        "New-Item -ItemType Junction -Path '"
        + str(junction).replace("'", "''")
        + "' -Target '"
        + str(build).replace("'", "''")
        + "' | Out-Null",
    ],
    check=True,
)
master = build / "native_entry.py"
native = root / "转换工具/ops/rebuild_support/sitecustomize.py"
renderer = code / "render_native.py"
master.write_text(
    "import runpy,sys,json,traceback\nfrom pathlib import Path\n"
    + "runpy.run_path("
    + repr(str(native))
    + ")\n"
    + 'report={"passed":False}\ntry:\n'
    + "    sys.argv="
    + repr([str(renderer), "--data-root", str(data)])
    + "\n"
    + "    runpy.run_path("
    + repr(str(renderer))
    + ',init_globals={"session":session},run_name="__main__")\n'
    + '    report["passed"]=True\nexcept Exception:\n    report["error"]=traceback.format_exc()\n'
    + "finally:\n    Path("
    + repr(str(build / "native-completion.json"))
    + ').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")\n',
    encoding="utf-8",
)
with (build / "native.stdout.txt").open("w", encoding="utf-8") as log:
    subprocess.run(
        [
            "D:/ChimeraX 1.10.1/bin/ChimeraX-console.exe",
            "--exit",
            "--script",
            str(junction / "native_entry.py"),
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
report = json.loads((build / "native-completion.json").read_text(encoding="utf-8"))
assert report["passed"], report
subprocess.run(
    python
    + [
        str(code / "assemble.py"),
        "--data-root",
        str(data),
        "--build-root",
        str(build),
        "--figure",
        "all" if args.figure == "multiligand-workbench" else args.figure,
    ],
    check=True,
)
node = os.environ.get(
    "FIGURE_NODE",
    str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"),
)
subprocess.run([node, str(code / "build_deck.mjs"), str(build)], check=True)
