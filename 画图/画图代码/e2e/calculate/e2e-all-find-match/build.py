"""只构建全配体top-k候选；共用原生绘图逻辑，不发布正式PPT。"""

import os
from pathlib import Path
import sys

SHARED = Path(__file__).resolve().parents[1] / "e2e-top-k-shared"
sys.path.insert(0, str(SHARED))
import build_nature_figures as figures

if __name__ == "__main__":
    figures.OUTPUT_DIR = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else figures.ROOT / "temp/e2e-all-find-match"
    figures.TEMP_DIR = figures.OUTPUT_DIR
    figures.main("e2e-all-find-match")
