"""本图唯一短命令入口; --build仅指定本次temp中的新输出目录."""

from pathlib import Path
from datetime import datetime, timezone
import argparse, json, os, sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from TOOLS.runtime.paths import configure_runtime, load_module

configure_runtime(ROOT)
from TOOLS.ppt.captions import preserve_notes
from TOOLS.figure_runner.provenance import annotate_candidate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path)
    args = parser.parse_args()
    output = (
        args.build
        if args.build
        else ROOT
        / "temp/figure-build"
        / Path(__file__).parent.name
        / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    ).resolve()
    output.relative_to(ROOT / "temp")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("本图只使用新的空构建目录: " + str(output))
    os.environ["MPLCONFIGDIR"] = str(output / "matplotlib")
    result = load_module(Path(__file__).with_name("build.py"), "current_figure_build").build(output)
    figure = json.loads(Path(__file__).with_name("figure.json").read_text(encoding="utf-8"))
    preserve_notes(result, ROOT / figure["pptx"], figure["figures"])
    annotate_candidate(result, Path(__file__).parent)
    print(result)
