# 实际 Match 感知计费与四种原构象链

服务器产物根：`/storage/penghongen/PocketXMol/final_evaluation/end_to_end`。本地副本：`追溯文档/source/E2E-实际计费.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 本根的角色与原文件

本根的 `GT/CA2/evaluation.json` 和 `docking_results.jsonl` 是原端到端四方法构象评价，GT保留280个、CA2保留268个原正确身份请求。`evaluation.json` 的原 `answer_scope` 为 `small_molecule`，模型 `strongest-1`，排序字段 `source_probability_mean`；这份原文不因当前改用完整身份Match计费而被改写。当前实际曲线只在本地按完整原候选与全身份argmax重计费，不能把本地 `match-aware-stage3-v2` 派生JSON上传替代本根原评价。

`inputs/base.jsonl` 与原Matcher handoff固定真实请求；`official/test/local-c1/`、`local_cov/test/{local-c1,local-c2,local-e}/` 保存四阶段原姿态、ranking及逐姿态评价。每个输入域的 `local_cov/test/local-c1/run.json` 直接保存原模型、训练config、checkpoint、受体根、RA分支、Centre口袋、knn32、50姿态、100步和input_count。原权重为相应Centre/Envelope的 `step=24800.ckpt`，官方分支为原 `pocketxmol.ckpt`。各请求原 `sample_index`、成功SDF位置及rank不改动。

## 原实际评价命令和现存生产入口

两域 `wandb/latest-run/files/wandb-metadata.json` 是原程序直接写出的运行元数据：GT在2026-09-23T08:38:30.770818Z、CA2在08:45:29.971801Z启动评价，实际program均为 `/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/scripts/evaluate_end_to_end.py`，args分别为 `configs/docking/end-to-end-GT.yml` 与 `end-to-end-CA2.yml`，解释器为 `/storage/penghongen/PocketXMol/runtime/venv/bin/python`。两份W&B元数据和上述原release程序、配置均已直接读取。

现存完整生产入口为 `/home/penghongen/My_Project/PocketXMol/训练与运行/sh/final_end_to_end.sh`，短命令 `bash 训练与运行/sh/final_end_to_end.sh end-to-end-GT` 或 `end-to-end-CA2`。它依次执行 `prepare_end_to_end.py ... initial`、官方Centre、DG Centre1、Centre2、Envelope及最终 `evaluate_end_to_end.py`；CPU准备/评价阶段明确关闭CUDA。现存脚本是生产入口，原实际评价代码版本以上述f4d72bbea387记录为准；本轮不重新提交或修改服务器源码。

## 当前全身份计费如何恢复

本地读取 `/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json` 的完整身份预测、`manifests/test_smallmolecule_v1/{identities,real_candidates,cryoatom2_candidates}.jsonl` 的精确身份/真实范围、原小分子Matcher evaluation/stage1_only以及本根两份原evaluation和docking。连接键是domain+PDB+source_blob_index，身份比较使用PDB内精确SMILES，不根据RMSD选身份。

原候选selected优先，然后按 `source_probability_mean`降序、blob编号升序。背景计费；非小分子被预测为非小分子时跳过、被预测为小分子时计费；范围外真实小分子只有身份完全正确时跳过；合格目标无论Match对错都计费。错误身份不能因没运行构象而从预算分母消失。零候选PDB、输入失败、无姿态和缺失距离保留原失败语义；不填0 RMSD，不缩小77-PDB/446实例的完整目标范围。

`official-C/local_cov-C/C-C/C-C-E` 四方法各自使用其原methods字段：`local_cov-C`是第一轮DG Centre，`C-C`继续到第二次Centre，`C-C-E`再继续Envelope；不能把末轮结果写入第一轮。当前 `actual_{CA2,GT}_pose50_rmsd3.0` 明确取 `methods.local_cov-C`，仅在 `target_scope=stage3_foreground` 且精确身份正确的请求上，读取 `status=success`、`pose_min_rmsd_A["50"]<3.0` 并与原 `success["3.0"]["50"]` 一致。首次成功步使用重算的candidate.attempt_index，50是原self-ranking全部50的best-of-50，不是Top-5。

300%预算为每PDB完整真实实例数的三倍，先逐PDB计算不同成功实例/完整目标数，再等权求均值；CA2/GT分别显示62.8%/66.9%。各 Figure 只生成本图请求的面板和汇总，分别在对应图目录说明。与原采用容器的逐字段比较用于一致性验收，不把旧容器当重算输入。

## 与受控oracle和作者病例的边界

`/storage/penghongen/Adaligand_E2E/test/test_0` 提供给定身份Find–Build原构象和作者病例科学文件，见 `追溯文档/source/E2E-受控身份.md`；该根与本根均保持原位、原条件。实际预测补充构象另在 `Adaligand_E2E/actual_display_20261101`，见 `追溯文档/source/E2E-作者构象.md`，特别是背景无合法参考RMSD的构象不能借本根正确身份评价补出成功数。不同实验根不因都叫local-c1而合并或删去。
