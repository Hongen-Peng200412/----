"""从当前采用的作者设计源码组合本图, 输出本次 temp 的单页可编辑 PPT.

drawing.xml 保存图内对象及组合关系, design/package 只供应本页主题、图注和必要媒体.
本入口不生成实验预测, 不读取旧 PPT 或已退出的总览生成流程.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from TOOLS.runtime.paths import configure_runtime
configure_runtime(ROOT)
from TOOLS.ppt.author_display import build_display
from TOOLS.ppt.captions import preserve_notes
from TOOLS.figure_runner.provenance import annotate_candidate

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build', type=Path, required=True)
args = parser.parse_args()
HERE = Path(__file__).resolve().parent
candidate = build_display(HERE / 'design', args.build)
preserve_notes(candidate, ROOT / '画图/PPT/Method总图.pptx', ['fig-method-color3'])
annotate_candidate(candidate, HERE)
print(candidate, flush=True)
