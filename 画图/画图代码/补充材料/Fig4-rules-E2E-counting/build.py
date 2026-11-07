"""只按本图静态科学定义与作者图层构造计费规则图, 不读取服务器实验结果."""

from pathlib import Path
import json
from TOOLS.ppt.svg_native import build_static


# ================================================================================================
def build(output: Path):
    """运输本图display.json中的规则节点、箭头、文字和主题, 返回单页候选.

    output: Path, 本次根temp空目录. display.json是作者规则图的原生节点定义, canvas单位EMU; 本入口不加载模型、候选、姿态、master或任何197份科学原件, 计费规则对应正文Fig6的accounting.py.
    """
    output.mkdir(parents=True, exist_ok=True)
    layout = json.loads(Path(__file__).with_name("display.json").read_text(encoding="utf8"))
    return build_static(
        layout, output / "candidate.pptx", "e2e-accounting-rules-draft", {"name": "Hongen Peng", "initials": "HP"}
    )
