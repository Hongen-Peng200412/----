#!/usr/bin/env bash
set -euo pipefail

# 当前 Job 本次执行前冻结的源码 release, 不是服务器可变工作目录.
project_root="${TASK_PROJECT_ROOT:?}"
# 原来实际运行 Emap2lig 的 Conda Python, 保持原依赖版本和编译器.
emap_python="/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/python"
# 原 Find 评价的不可变 Pocket Plus release, 只读取评价代码, 所有新结果写到新条件目录.
pocket_root="/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_5570cf8a0b7a/Pocket_Plus"
# 原 Find 评价使用的 Pocket Plus Conda Python, 执行固定 release 的空间映射和指标计算.
pocket_python="/home/penghongen/anaconda3/envs/Pocket_Plus_centos7_cu121_allgpu/bin/python"
# 原始地图和标签的只读数据根, 不把旧推理产物作为新输入.
data_root="/storage/penghongen/AdaLigand/Ori_Data"
# 本次显式 level 的独立科学产物根, 不写旧 official_find_li 或 stage3_find_hit_build.
experiment_root="/storage/penghongen/Emap2lig/contour_level_20261026"

export PYTHONPATH="${project_root}/src:${project_root}/显式level实验"
export PYTHONDONTWRITEBYTECODE=1
# 评价和请求选择由 24 个进程并行, 各进程内部使用一个线程; 单进程 Find/Build 在命令处使用 24 线程.
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
# Conda 内可被当前 Triton 使用的 GCC; 系统旧 GCC 不具备所需 stdatomic 支持.
export CC="/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/x86_64-conda-linux-gnu-gcc"

printf '[stage] Find begin %s\n' "$(date --iso-8601=seconds)"
OMP_NUM_THREADS=24 MKL_NUM_THREADS=24 "${emap_python}" -u "${project_root}/显式level实验/find.py"
printf '[stage] Find evaluation begin %s\n' "$(date --iso-8601=seconds)"
PYTHONPATH="${pocket_root}" "${pocket_python}" -u "${project_root}/显式level实验/evaluate_find.py" \
    --test0-json "${experiment_root}/inputs/test_0.json" \
    --test1-json "${experiment_root}/inputs/test_1.json" \
    --data-root "${data_root}" --output-root "${experiment_root}/find" \
    --workers 24 --chunk-depth 8
printf '[stage] Build preparation begin %s\n' "$(date --iso-8601=seconds)"
"${emap_python}" -u "${project_root}/显式level实验/prepare_build.py"
printf '[stage] Build begin %s\n' "$(date --iso-8601=seconds)"
OMP_NUM_THREADS=24 MKL_NUM_THREADS=24 "${emap_python}" -u "${project_root}/显式level实验/build.py"
printf '[stage] Build evaluation begin %s\n' "$(date --iso-8601=seconds)"
"${emap_python}" -u "${project_root}/显式level实验/evaluate.py"
printf '[stage] Complete %s\n' "$(date --iso-8601=seconds)"

