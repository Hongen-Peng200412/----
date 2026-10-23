"""仅重绘Stage2六轴图, 默认当前新口径, 不修改正式PPT或稿件.

--output 指定PDF/SVG/PNG/TIFF及布局核查的目标目录, --profile old显式选择旧口径. 所有图形仍由共享plot_radar_pair生成, 本文件不复制统计或绘图算法.
"""
import argparse
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE / "stage2-results-shared"))
import plot_stage2
import plot_stage2_pairs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["new", "old"], default="new")
    parser.add_argument("--output", type=Path, default=plot_stage2.SOURCE / "regenerated/stage2-radar-pair")
    args = parser.parse_args()
    plot_stage2.configure(args.profile, args.output)
    plot_stage2_pairs.main("radar")
