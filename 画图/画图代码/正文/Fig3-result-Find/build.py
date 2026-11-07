"""只从服务器原件重建本目录对应的一张Find图, 不覆盖正式作者PPT.

build装配本图的输入要求、科学数据和显示, 输出candidate.pptx及本次data/scenes. 科学共用定义由正文Fig3显式拥有, 通用容器和传输只调用TOOLS.
"""

from pathlib import Path
import json
import subprocess
from TOOLS.runtime.paths import load_module
from TOOLS.server_io.source import SourceStore

ROOT = Path(__file__).resolve().parents[4]
DATA = load_module(ROOT / "画图/画图代码/正文/Fig3-result-Find/data.py", "fig3_find_data")
PLOT = load_module(Path(__file__).with_name("plot.py"), "current_find_plot")


# ================================================================================================
def build(output: Path):
    """从原件到单页候选, output是调用方指定的本次空temp目录.

    data/plot_data.json保存本图需要的逐PDB字段; source_reads.json记录本次地址/摘要; scenes.json为本图原生几何; candidate.pptx是本图唯一可编辑候选, 不用于下一次科学读取.
    """
    output.mkdir(parents=True, exist_ok=True)
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    try:
        data, completion_inputs = DATA.prepare_find(
            store, "explicit_emdb_level", ("dice", "oto03", "precision", "recall"), False, True
        )
        data_dir = output / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "plot_data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        (output / "source_reads.json").write_text(
            json.dumps({"reads": store.reads}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    finally:
        store.close()
    PLOT.render(data, output)
    subprocess.run(
        ["node", str(ROOT / "TOOLS/ppt/build_scene.mjs"), str(output), str(Path(__file__).with_name("display.json"))],
        check=True,
    )
    return output / "candidate.pptx"
