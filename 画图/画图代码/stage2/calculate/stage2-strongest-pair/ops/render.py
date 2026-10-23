"""仅重绘Stage2按竞争身份数分组图, 不修改正式PPT或稿件.

--output 保存PDF/SVG/PNG/TIFF及布局核查, --profile默认new, old必须显式选择. 复用共享plot_categories_pair, 不重新定义分组或复制科学算法.
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
    parser.add_argument("--output", type=Path, default=plot_stage2.SOURCE / "regenerated/stage2-strongest-pair")
    args = parser.parse_args()
    plot_stage2.configure(args.profile, args.output)
    plot_stage2_pairs.main("categories")
