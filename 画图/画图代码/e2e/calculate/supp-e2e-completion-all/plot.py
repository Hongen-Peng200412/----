"""只绘制全配体实例完成度；复用共享科学计算和布局，不发布正式PPT。"""

import os
from pathlib import Path
import sys

SHARED = Path(__file__).resolve().parents[1] / "e2e-instance-completion"
sys.path.insert(0, str(SHARED))
import plot as completion

if __name__ == "__main__":
    completion.BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else completion.ROOT / "temp/supp-e2e-completion-all"
    completion.main("supp-e2e-completion-all")
