"""定义显式 level 实验的固定输入和独立产物位置.

先阅读 EXPERIMENT_ROOT, 再按 Find -> Build -> RMSD 的顺序查看路径. 本模块不读写文件, 无 level 原产物不属于任何写出路径.
"""

from pathlib import Path

# 本轮显式 level 的唯一科学产物根, 与旧 official_find_li 和 stage3_find_hit_build 分开.
EXPERIMENT_ROOT = Path('/storage/penghongen/Emap2lig/contour_level_20261026')
# AdaLigand 原始实验地图、冻结元数据和参考标签的共同根, 本轮只读.
DATA_ROOT = Path('/storage/penghongen/AdaLigand/Ori_Data')
# 本源码目录中的冻结 PDB 顺序与逐图推荐 level, 随每次 release 一起保存.
SOURCE_INPUTS = Path(__file__).resolve().parent / 'inputs'
# 正式输入副本目录, 保存本次真正使用的 maps.json、test_0.json 和 446 实例 test.jsonl.
INPUT_ROOT = EXPERIMENT_ROOT / 'inputs'
# 新 Find 的父目录, 官方逐 PDB 产物位于其 held_out_test_0/raw_find_outputs 下.
FIND_ROOT = EXPERIMENT_ROOT / 'find'
# 新 Find 在同一 179-PDB 测试集上的空间映射、交集和匹配事实.
FIND_EVALUATION = FIND_ROOT / 'held_out_test_0/evaluation/per_pdb'
# 新 Find 的原生 blob 目录, 每个 PDB 内保留 find_blobs/blob_N.npz.
FIND_BLOBS = FIND_ROOT / 'held_out_test_0/raw_find_outputs'
# 原 77-PDB、446 个合格小分子实例及其精确 SMILES, 本轮只读并复制为输入快照.
FROZEN_TEST = Path('/storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl')
# 原沉积配体的重原子世界坐标包, 只由 RMSD 评价读取, 不进入 Find 或 Build.
TRUTH_COORDS = DATA_ROOT / 'smiles_assets/SMILE_coords/v1'
# 新 Build 的请求、CIF、原评分、状态和逐姿态 RMSD 的共同根.
RESULT_ROOT = EXPERIMENT_ROOT / 'build'

