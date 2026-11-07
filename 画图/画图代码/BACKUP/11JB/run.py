"""本图唯一入口; 所有运行产物只写本次根temp, 作者原件保持原字节."""

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
    parser.add_argument(
        "--render-sessions",
        action="store_true",
        help="在独立ChimeraX进程重开当前采用作者CXS并完整读取地图; 不保存原会话",
    )
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
    result = load_module(Path(__file__).with_name("build.py"), "current_visual_build").build(
        output, args.render_sessions
    )
    definition = json.loads(Path(__file__).with_name("figure.json").read_text(encoding="utf-8"))
    preserve_notes(result, ROOT / definition["pptx"], definition["figures"])
    annotate_candidate(result, Path(__file__).parent)
    print(result)
