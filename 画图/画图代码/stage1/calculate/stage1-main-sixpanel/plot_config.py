"""六面板的外观修改入口, 科学计算参数在 science/prepare_plot_data.py.

只改颜色、字号、尺寸、透明度不会改变 source_data.csv 中的科学结果.
临时输出统一进入论文根 temp/; 成品和固定数据保存在 formal/ 中.
"""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parent
WORKSPACE = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
OUT = WORKSPACE/'画图/画图代码/stage1/output/stage1-main-sixpanel'
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else WORKSPACE/'temp/stage1_main_sixpanel_20260929'
VERSION = os.environ.get('STAGE1_FIGURE_VERSION','v5')
COLORS = {'GT':'#007C83','Cryo':'#566AB4','Emap':'#8B9298'}
LABELS = {'GT':'Ligandseek-Find · deposited receptor','Cryo':'Ligandseek-Find · CryoAtom2 receptor','Emap':'Emap2lig-Find'}
# 组合图宽约 163 mm, Word 内约 147 mm. 字号按最终缩小后的 6.5–8 pt 设计.
FONT = {'body':7.8,'tick':7.0,'panel':9.5,'column':10,'legend':7.4,'metric':7.8}
COMPOSITE_SIZE = (6.4,7.0)
SINGLE_SIZE = (3.2,2.75)
DPI = 350
DOT_SIZE = {'bar':4.0,'violin':4.0,'paired':12.0}
DOT_ALPHA = .40
BAR_ALPHA = .16
COLORBAR_CMAP = 'viridis_r'
COLORBAR_LIMITS = (1.0,4.0)
