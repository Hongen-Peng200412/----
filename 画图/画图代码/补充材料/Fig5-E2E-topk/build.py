"""只构造补Fig5的18条整数曲线及一页作者候选."""

from pathlib import Path
import json
from TOOLS.runtime.paths import load_module
from TOOLS.server_io.source import SourceStore
from TOOLS.ppt.svg_native import build_candidate

DATA = load_module(Path(__file__).with_name("data.py"), "supp5_topk_data")
PLOT = load_module(Path(__file__).with_name("plot.py"), "supp5_topk_plot")


# ================================================================================================
def build(output: Path):
    """读取原件, 只汇总本图K1到10, 返回候选PPT路径.

    output: Path, 本次根temp空目录. data/topk_data.json为本图18条整数计数, plotted_series.json为实际画线数值, server_reads.json为原件读取记录; 不建立master或预算完成度面板.
    """
    output.mkdir(parents=True, exist_ok=True)
    data_dir = output / "data"
    data_dir.mkdir()
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    try:
        data = DATA.prepare_topk(store)
        (data_dir / "server_reads.json").write_text(
            json.dumps(store.reads, ensure_ascii=False, indent=2), encoding="utf8"
        )
    finally:
        store.close()
    (data_dir / "topk_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8")
    PLOT.draw(output)
    pages = json.loads((output / "manifest.json").read_text(encoding="utf8"))
    display = json.loads(Path(__file__).with_name("display.json").read_text(encoding="utf8"))
    return build_candidate(output, pages, display["canvas"], {"name": "Hongen Peng", "initials": "HP"}, display)
