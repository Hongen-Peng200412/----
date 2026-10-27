#!/usr/bin/env bash
set -euo pipefail

# 本次非测试门控使用与正式任务相同的源码 release 和 Conda, 输出只进入服务器临时目录.
project_root="${TASK_PROJECT_ROOT:?}"
# 原 Emap2lig Conda Python, 与正式 Find 和 Build 使用相同依赖.
emap_python="/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/python"
export PYTHONPATH="${project_root}/src:${project_root}/显式level实验"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
# Conda 内兼容当前 Triton 的 GCC, 避免系统旧编译器缺少 stdatomic.
export CC="/home/penghongen/anaconda3/envs/Emap2lig_find_py310_cu121/bin/x86_64-conda-linux-gnu-gcc"
"${emap_python}" -u "${project_root}/显式level实验/tests/cpu_gate.py"
# 原评价 release 提供固定算法, 本轮适配只接纳空候选; 下述 Python 属于原 Pocket Plus Conda 环境.
pocket_root="/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_5570cf8a0b7a/Pocket_Plus"
pocket_python="/home/penghongen/anaconda3/envs/Pocket_Plus_centos7_cu121_allgpu/bin/python"
PYTHONPATH="${pocket_root}:${project_root}/显式level实验" "${pocket_python}" -u "${project_root}/显式level实验/tests/empty_find_gate.py"
# 与正式单进程 Find/Build 相同, 教程 GPU 门控允许 CPU 算子使用 24 线程.
OMP_NUM_THREADS=24 MKL_NUM_THREADS=24 "${emap_python}" -u "${project_root}/显式level实验/tests/gpu_gate.py"
