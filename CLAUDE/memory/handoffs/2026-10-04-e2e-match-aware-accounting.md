# Handoff: 端到端计费重汇总与论文图表

Date: 2026-10-04

## Current State

本轮已完成新计费规则的冻结数据重汇总、原版折线图更新、七页案例图集同步和 Nature/Operation Word 编译。服务器只读下载，不重跑推理或 CPU 科学计算，不修改服务器文件或作业。

## Completed

- 派生结果位于画图/formal/E2E_accounting_20261004，含 GT/CA2 的 evaluation.json、docking_results.jsonl、独立定位诊断、绘图计数、CSV 与验收结果。sources 保存冻结原文件和原 PPT/正文副本。
- GT 598、CA2 632 个候选各对应 77 个 PDB。新增计费分别 12、9 条，免费数由 85/76 变为 73/67。原 280/268 条直接对接记录的计费编号均未变，四种方法的全部 K/M/阈值构象曲线不变。
- 179-PDB 全配体曲线和 77-PDB 三联图保留作者原 PPT 的形状、颜色、位置、字号，只改横轴为 Charged attempts (K) 与图注。三联图 a 保留 Emap2lig-Find。
- E2E案例可视化-端到端流程版_v3.pptx 保留七页，前三主例为 9LLG、9BJJ、30GA。公开页及图注没有 Stage3/local_cov 标签。规则图另存 E2E评价计费规则-草稿.pptx，暂不进入论文。
- 当前作者 Results 叙事保留，只适配诊断段落与必要事实、范围措辞。过程中作者提交 4a3aa17，之后正文仅两行范围名称变更；未操作 Git index 或提交。
- 本轮 Word 为论文草稿.nature.E2E新计费规则.docx（51页）、论文草稿.operation.E2E新计费规则.docx（39页）。图10–14均与完整图注同页。原默认 Word 保留。
- PocketXMol 端到端总体日志及 official、local_cov_C、CC、CCE 四份既有日志前部已加入当前计费口径；原完整结果表与历史不改写。

## Decisions

实际 Match/Build 采用全身份 Top-1：背景计费；真实非小分子预测为非小分子时免费，即使具体身份错误，预测为小分子则计费。真实小分子身份错误时计费，正确但不在单残基无缺失原子的有机小分子清单时免费；合格目标计费并继续判断姿态。selected 段优先，各段按冻结分数排序；未入选和原排名超过20的候选保留。

Find-only/Emap2lig-Find 独立诊断假定 Match 完全正确：背景计费、真实范围外前景免费、合格目标覆盖命中计费且成功。两者用同一77PDB与双向覆盖均≥0.3的规则，各自保留冻结候选顺序。实际 attempt_index 和 localization_attempt_index 分开，不得把实际 Match 计费覆盖数误作 Find-only 曲线。

图表和图注沿用原 E2E结果_小分子三联图.pptx 的版式和生成风格。用户明确不要把计费流程草稿插入论文，不恢复弃用的十页整合版。公开表述为“单残基无缺失原子的有机小分子”；内部字段保留原名以连接冻结数据。

## Next Actions

当前任务无剩余执行步骤。后续若作者修改图注或案例，回到 PPT 修改，并按执行记录中的短命令编译和运行 fit_word_layout.py。不得恢复旧 Results 叙事，也不得把本地重汇总误当成新增 W&B 实验；原 W&B 记录对应原运行口径。

## Files To Reopen

- 论文草稿.md
- 画图/formal/E2E_accounting_20261004/README.md
- 画图/formal/E2E_accounting_20261004/执行记录.md
- 画图/画图代码/e2e_accounting_20261004/reaggregate.py
- 画图/画图代码/e2e_accounting_20261004/build_ppt.py
- 画图/画图代码/e2e_accounting_20261004/fit_word_layout.py
- 画图/E2E结果_全配体.pptx
- 画图/E2E结果_小分子三联图.pptx
- 画图/E2E案例可视化-端到端流程版_v3.pptx
- 画图/E2E评价计费规则-草稿.pptx

正式重汇总、制图、Word 命令与验收/只读命令均分开保存在执行记录。独立科学核查通过；公开措辞与 pPr 标准序列的问题已窄复核闭环。全部图形原生可编辑，Word 中五图回转标记保持。
