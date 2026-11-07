# 受控 Find–Build、原实际展示与逐候选结果

服务器产物根：`/storage/penghongen/Adaligand_E2E/test/test_0`。本地副本：`追溯文档/source/E2E-受控身份.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 与实际 Match 计费实验分开

本根提供当前受控Find–Build比较、给定正确身份的oracle构象、原逐候选模型姿态及作者病例/BACKUP科学原件。当前论文实际Find–Match–Build曲线另从 `/storage/penghongen/PocketXMol/final_evaluation/end_to_end/{GT,CA2}` 的原四方法姿态评价，结合完整Matcher身份预测重新计费，见本地 `追溯文档/source/E2E-实际计费.md` 与该独立根的同字节说明。不能用本根oracle姿态和计费直接冒充该实际曲线。

## 原运行命令与已有结果

实际正式短命令为 `bash 测评数据代码/端到端测评/sh/run.sh GT`、同入口 `CA2` 与 `Emap2lig`。原release为 `/home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand`；GT launch在 `/home/penghongen/Feedback/AdaLigand/launches/403776/submit_task_job403776_20261016T043310_a4/`，CA2后接旧Emap在 `/403774/submit_task_job403774_20261016T042314_a4/`。真实run_cmd和launch已读取。现有主仓 `/home/penghongen/My_Project/AdaLigand/ligandseek_pipeline/__main__.py` 以 `python -m ligandseek_pipeline <明确配置.yml>` 调度相同阶段模块；原configs/{GT,CA2,Emap2lig}.yml保存在本根。原prepared.json/sources.json说明一次复制来源及目标，原历史`tmp/prepare.sh`不等于当前读取仍依赖旧tmp。

## 直接接口

`inputs/inventory.json` 给完整PDB实例分母；`inputs/stage3/` 给77PDB/446合格实例、typed身份和三域候选；`inputs/all_ligand/{GT,CA2}/` 给完整候选与精确SMILES清单。`find/LigandSeek2/{GT,CA2}/held_out_test_0/` 保留原Find区域与交集；`match/all_ligand/{GT,CA2}/evaluation.json` 保存原strongest-1预测。

`build/PocketXMol-tuned/{GT,CA2}/test/local-c1/<pdb>/<blob>/` 的 `scientific_input.json/result.json/candidates.json/poses.sdf/confidence.npz/ranking.json/evaluation_metrics.json` 保存实际输入、50姿态及原排名。`evaluation/{GT,CA2}/docking_results.jsonl` 是逐blob直接评价，`evaluation.json` 的traces保留原顺序、真实归属和Match回答；`completion.json/summary.json` 为该次生产的完成度与汇总。当前新Emap比较另从显式level根读取，不覆盖本根旧Emap事实。

区域键为domain+PDB+source_blob_index；真实实例键为PDB+matched_occurrence_id；sample_index是原0基采样编号，sdf_index是成功SDF中的0基位置。不能将三者互换，也不能根据当前面板字母连接。

## 预算、正确身份和失败

候选保留原selected优先、`source_probability_mean`降序和原blob编号升序，不改成评价NPZ的Gaussian评分排序。对于合格真实小分子，错身份同样消耗一次；背景也消耗一次；明确归属非合格真实类别的候选按原规则跳过。一次成功要求原身份正确且原参考RMSD严格低于阈值。每实例只记录首次成功，零候选、输入失败和无姿态保留，不能把它们填成零RMSD或删掉分母。完整候选用尽统计可超过300%预算，300%不是尝试上限。

当前主图及预算补图分别区分Find-only、给定正确身份的Find–Build和来自独立计费根的实际Find–Match–Build。62.8%/66.9%的实际曲线取独立根 `methods.local_cov-C`，在全身份Match重计费后计算300%预算、best-of-50、RMSD<3Å、77PDB/446实例的CA2/GT逐PDB均值，具体来源见 `追溯文档/source/E2E-实际计费.md`；它们不是本根oracle曲线、Top-5或实例合并比例。原排名不因展示更好构象而改动。

## 三个明确选留的 BACKUP 复合物

三例均CA2、原100%合格小分子预算、模型原Top-1：11JB预算78、成功76/78；30GA预算7、成功5/7；9LOV预算3、成功3/3（原扫描5候选，其中2个离子跳过）。读取本根 `evaluation/CA2/evaluation.json::traces` 确定候选顺序与计费，不以D盘catalog作为事实。

11JB与9LOV合格姿态来自本根原build。30GA额外背景blob5的实际预测构象来自 `../actual_display_20261101/CA2/` 原请求/显示索引；其没有合法参考RMSD，图中可展示但不计成功。blob0无可用actual构象，应保留无姿态事实。不要用GT成功率美化CA2结果。
