"""按每图声明运行单个或全部图表入口, 候选只写本次temp.

单个目录是一个执行单元. 多图与表的范围完全由该目录figure.json声明, 不推导stage组、不去掉图名版本、不读取旧构建. 科学读取、计算和绘图均由图目录负责.
"""

from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from TOOLS.runtime.paths import configure_runtime

configure_runtime(ROOT)
from TOOLS.figure_runner.catalog import discover
from TOOLS.ppt.deck import Deck


def main():
    """解析明确的图目录或完整图名, 逐单元调用其正式run.py并核对声明产物."""
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--all", action="store_true")
    choice.add_argument("--figure", action="append")
    parser.add_argument("--build-root", type=Path)
    arguments = parser.parse_args()
    entries = discover(ROOT)
    selected = list(entries) if arguments.all else []
    for name in arguments.figure or []:
        keys = [
            key
            for key, item in entries.items()
            if key == name or name in item["figures"]
        ]
        if len(keys) != 1:
            raise ValueError("没有唯一声明的图目录或完整图名: " + name)
        if keys[0] not in selected:
            selected.append(keys[0])
    base = (
        arguments.build_root
        or ROOT
        / "temp/figures"
        / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    ).resolve()
    base.relative_to(ROOT / "temp")
    receipts = []
    for key in selected:
        item = entries[key]
        build = base / key
        if build.exists() and any(build.iterdir()):
            raise FileExistsError("不复用非空构建目录: " + str(build))
        build.mkdir(parents=True, exist_ok=True)
        logs = base / "logs" / key
        logs.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            "-X",
            "utf8",
            "-B",
            str(item["directory"] / item["entry"]),
            "--build",
            str(build),
        ]
        environment = dict(os.environ)
        environment.update(
            {
                "FIGURE_VERIFY_ROOT": str(ROOT),
                "FIGURE_BUILD_ROOT": str(build),
                "FIGURE_GUARD_ROOT": str(build),
                "FIGURE_AUDIT_LOG": str(logs / "python-reads.jsonl"),
                "MPLCONFIGDIR": str(build / "matplotlib"),
                "PYTHONPATH": os.pathsep.join(
                    [
                        str(Path(__file__).with_name("guards")),
                        str(ROOT),
                        str(ROOT / "TOOLS/runtime/.manuscript_deps/figure_runtime"),
                    ]
                ),
                "NODE_OPTIONS": "--require="
                + str(Path(__file__).with_name("guards") / "node_guard.cjs"),
            }
        )
        with (logs / "command.log").open("w", encoding="utf-8") as log:
            subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
        for output in item["outputs"]:
            path = build / output
            if not path.is_file() or path.stat().st_size == 0:
                raise FileNotFoundError("图表声明的产物未生成: " + str(path))
            if path.suffix.lower() == ".pptx" and set(Deck(path).figures) != set(
                item["figures"]
            ):
                raise ValueError("候选页范围不等于本图单元: " + key)
        receipts.append(
            {
                "unit": key,
                "figures": item["figures"],
                "kind": item["kind"],
                "build": str(build),
                "command": command,
                "old_temp_blocked": True,
                "passed": True,
            }
        )
        (base / "summary.json").write_text(
            json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("通过图表单元: " + key, flush=True)


if __name__ == "__main__":
    main()
