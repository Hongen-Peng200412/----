# 正文运行时间的冻结来源与汇总

本目录重算正文 Running time analysis 的运行时间。先读本文件的计时范围，再读 `summarize_runtime.py` 中按 Find、Build、Match、EMERALD-ID 排列的主流程。程序只读取已有计时和评价原件，执行描述统计；没有训练、推理、对接或重新计算 RMSD 的步骤。独立数字登记在[端到端计算追溯](../图表追溯.md)的 `running-time-analysis` 条目。

## 文件位置

```text
画图/画图代码/e2e/
├─ calculate/running-time-analysis/
│  ├─ README.md
│  └─ summarize_runtime.py
└─ output/running-time-analysis/
   ├─ find_per_map.json             # 358 次逐图观测及两段前向的原始计时对象
   ├─ emerald_queries.json          # 714 次正式位点查询的结果对象与原文件时间
   ├─ source_receipt.json           # 取回时间、来源文件、字节身份和既有输入身份
   ├─ source_code/                  # 历史 release 中计时代码、配置及 launch 原件
   └─ summary.json                  # 冻结时由当前入口生成的统计结果
```

Build 的两份原件复用 `stage3/output/stage3-official-tuned/frozen/local_cov_{CA2,GT}_C0.json`。Match 复用 `stage2/output/stage2-results/frozen/strongest-1.json` 和 `provenance/runtime/{launch.json,frozen_stat.json}`，完整路径及散列在 `source_receipt.json`。原受体条件用于定位来源，正文按作者决定合并 Find 和 EMERALD-ID，并按 GPU 型号报告 Build。

## Find 逐图计时

`find_per_map.json` 是列表，每项对应一个 PDB 在一种受体条件下的观测；两种条件各 179 项，共 358 项，覆盖相同的 179 个不同 PDB。`pdb_id` 如 `10ft`；`condition` 如 `真实受体`；`performance.probability` 和 `performance.centered` 保留原 `performance.json` 对象。两者的 `wall_seconds` 是浮点秒数，例如 `10ft` 沉积受体观测的完整图时间为 `108.31552633689716` 秒。`source` 中各角色记录原绝对 `path`、整数 `size`、整数纳秒 `mtime_ns` 和 `sha256`。

先对同一项的两段 `wall_seconds` 相加，再对 358 个合计值计算均值与中位数；不平均两种条件各自的中位数。完整图计时覆盖窗口准备等待、模型前向、异步传输完成及融合；局部前向计时截止于提交异步字段打包。两段均不包含外部模型加载和完整文件发布，也不包含 blob 提取的完整阶段时间。整个作业使用两张 H100 按 PDB 分片，每个 PDB 在一张卡上处理；逐图计时之和不能当作双卡作业的总墙钟时间。

## Build 标准 Centre 采样

两份既有 JSON 均为 446 项的列表，每项用 `(pdb_id, occurrence_id)` 定位实例，如 `11jb/0`。读取 `sampling_seconds`，即实例预处理到候选写出的总采样秒数；例如 CA2 原件中 `11jb/0` 为 `32.56616828404367` 秒。`inference_seconds` 只覆盖模型相关计算，不是本节所报字段；`evaluation_seconds` 含后续基准评价，本节不合入。全部实例的 `sampling_status=success`、`num_candidates=50`、`generated_count=50`。

`local_cov_CA2_C0.json` 对应 H100，`local_cov_GT_C0.json` 对应 A800；两份都是标准 Centre、50 姿态、100 步、batch size 50。它们是两种既有受体条件的实际成本，未做只改变 GPU 的硬件对照，不计算硬件加速倍数。573 项 H100 预测区域构建记录和 A6000 补齐记录不参与这套统计。

## Match 批量摊销

从冻结结果原件的 `mtime_Asia_Shanghai` 减去正式 launch 的 `created_at`，得到 411 秒；二者均带相同时区。`strongest-1.json.predictions` 的两种条件各按 PDB 保存候选列表，共 4,658 项；不是 selected 候选数。平均值为 `411/4658` 秒/候选位点，正文取 0.09 秒。该区间含模型加载、读取、前向、统计和冻结 JSON 写出，不包含后续绘图；没有逐候选独立延迟或其中位数。

## EMERALD-ID 位点查询

`emerald_queries.json` 是 714 项的列表，每项对应一种受体条件下的一次正式小分子位点查询。`result` 保留原 `result.json` 对象；`result_source` 保存该文件原绝对路径、字节数、修改时间纳秒和散列；`input_pdb_stat` 保存同目录 `input.pdb` 的原路径、字节数和修改时间，文件不存在时为 `null`。时间戳字段是整数 Unix 纳秒，例如构造值 `1789975424000000000`，不是本地复制文件的新修改时间。

完整查询为两种条件各 357 项。合并状态为 595 个 `scored`、84 个 `no_prepared_identity`、35 个 `no_valid_score`。只对 595 个有效评分查询计算 `(result_mtime_ns-input_mtime_ns)/60_000_000_000` 分钟，逐查询等权。一个查询处理该位点的候选身份集合，不是一次单身份对接。失败查询保留原记录，不补造缺失的耗时。

历史代码先准备化学身份并转换受体，再写 `input.pdb`，随后解压密度图、运行单核 Rosetta、排名并写结果。因此该区间不包含前面的身份准备及受体转换。它是原文件时间差，不是单调时钟或纯 CPU 时间；595 项是有效查询次数，不是不同物理位点的数量。旧教程四身份摊销 63.55 分钟的记录保留为历史来源，不用于当前均值。

## 汇总结果与运行

`summary.json` 顶层 `schema` 为 `ligandseek_runtime_summary_v1`。`find`、`build_h100`、`build_a800`、`emerald` 各含整数观测数 `n`、浮点 `mean/median/minimum/maximum/total` 和单位 `unit`，如 `s/map`、`s/site`、`min/site_query`；`total` 为逐观测区间之和。`find_full_map` 和 `find_centered` 保留两段诊断统计。`match` 含 `n=4658`、`elapsed_seconds=411.0`、浮点均值、`median=null` 和 `unit=s/candidate_site`。Build 另含状态计数和姿态预算；EMERALD-ID 另含完整查询数与全部状态计数。

从论文仓库根运行，输出放入可清空目录：

```powershell
python -B 画图/画图代码/e2e/calculate/running-time-analysis/summarize_runtime.py --output temp/running_time_analysis_check/summary.json
```

该入口只依赖长期目录。与冻结 `output/running-time-analysis/summary.json` 比较 JSON 数值即可复核当前统计，不需要恢复旧 temp，也不需要连接服务器。
