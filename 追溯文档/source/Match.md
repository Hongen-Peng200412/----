# Match 身份预测、输入消融与 EMERALD-ID

服务器产物根：`/storage/penghongen/Matcher`。本地副本：`追溯文档/source/Match.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 直接读取的原件

`evaluation/final_smiles/{strongest-1,density_only-106,density_only-0,pocket_only-0}/frozen_test.json` 分别对应完整模型、体素输入、密度输入和口袋输入变体，每份保存完整预测、原模型身份和测试条件。`manifests/test0_real_smiles_v1/` 与 `test0_cryoatom2_smiles_v1/` 的 `manifest.json`、`held_out_test_0_candidates.jsonl` 和 `held_out_test_0_identities.jsonl` 给出179 PDB候选与精确SMILES身份。身份必须按PDB+精确字符串连接，不从预测标签反推未命中身份。

正式strongest-1原运行根为 `runs/strongest-1/train_strongest1_revised_job378587_20260920T230727`，其 `BEST.pt` 与配置指定该模型。训练release为 `/home/penghongen/Feedback/Matcher/releases/Matcher_a67eb7f830e0/Matcher`，BEST SHA-256为 `4d1109c403b2b5f64c0f220d3ee8643298bf66f74590bee799871bcffa404058`。当前总体准确率GT1087/1238、CA21004/1160；9ian/9oq7退出身份准确率分母，但保留前景评价，不因隐藏肽类显示轴改变Overall分母。

## 实际生产入口和模型选择

正式短命令为 `bash 训练与运行/sh/final_smiles/train_strongest.sh` 与 `bash 训练与运行/sh/final_smiles/evaluate_strongest_1.sh`。通用测试由 `Matcher_cab21d9ceea5` release执行，原launch `/home/penghongen/Feedback/Matcher/launches/378587/evaluate_full_strongest1_revised_job378587_20260921T151639/` 的真实run_cmd明确绑定该release和入口。模型代码/配置/加载器来自原训练release；不自动采用当前主仓源码重解释旧checkpoint。

BEST指标为 `(0.3*foreground PRAUC+SMILES accuracy)/1.3`；前景阈值0.359375仅由BEST validation拟合。Match使用原提供身份集合做argmax，不生成新SMILES；不得用真实RMSD参与身份选择。输入消融各自原frozen_test的模型/配置字段决定原变体，不用strongest结果模拟其他行。

## 样本和计时

训练manifest源PDB1650，实际selected_usable覆盖1590 PDB、44,643个候选；这两个PDB数表达不同筛选层级，不能互相改写。validation同样按候选真实支持和精确身份过滤；完整源manifest位于 `manifests/final_train_validation_shards01_06_v1/`。

原测试launch创建时间为2026-09-21T15:16:53+0800，原frozen_test文件修改时间为15:23:44，间隔411秒，涵盖加载、读取、推理、统计和冻结发布。两受体候选2251+2407=4658，摊销0.0882352941秒/候选；不是逐候选延迟的独立测量，也没有逐候选中位数。

## EMERALD-ID 原查询

`evaluation/test_EMERALD-ID/{EMERALD-ID,CryoAtom2/EMERALD-ID}/nxu/<pdb>/<occurrence>/result.json` 保存714次实际查询；相同目录 `input.pdb` 的原mtime与resultmtime决定已报告时间差。595次有有效评分、84次无可准备身份、35次无有效评分；有效观测的分钟均值166.6747619048、中位75.05。计时含input.pdb写出后的密度解压、单核Rosetta、排名和写出，不含更早化学准备/受体转换；不是纯CPU时间。不能复制文件后的新mtime替代原mtime。

本地最终图读取完整frozen_test及身份清单后按原规则重汇总；原查询结果和文件属性直接来自服务器，不把旧本地分类/计时摘录当独立输入。
