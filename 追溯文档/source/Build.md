# 标准口袋 Build、密度消融与采样时间

服务器产物根：`/storage/penghongen/PocketXMol`。本地副本：`追溯文档/source/Build.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 测试轴和真实评价文件

`data/summary.json` 及 `{train,validation,calibration,test}.jsonl` 保存共同冻结实例。原计数分别为65,290/781/361/446；test为77 PDB，只有合格的单残基、无缺失重原子小分子。校准集361不是训练或验证输入。

GT官方与DG逐实例评价是 `sampling/{official-SMILES,local_cov-C-T0-RA,local_cov-E-T0-RA}/test/{C0,E}/occurrences.json`。CA2对应 `final_evaluation/standard/ca2/{official,local_cov-C,local_cov-E}/test/{C0,E}/occurrences.json`。无密度微调为GT `sampling/{B-C-T0-RA-SMILES,B-E-T0-RA-SMILES}/test/{C0,E}/occurrences.json` 与CA2同名模型的 `final_evaluation/standard/ca2/` 原评价。每份446实例，官方GT有1例无有效连续RMSD；成功率分母仍为446，分布只取445个有限值，不补0。

每个 `test/run.json` 保存 `science_config/configuration/training_config`。已直接读取确认：官方权重为 `/storage/penghongen/PocketXMol_official_test/extracted/data/trained_models/pxm/checkpoints/pocketxmol.ckpt`；DG Centre和Envelope分别采用对应 `training/local_cov-{C,E}-T0-RA-b72/checkpoints/step=24800.ckpt`；无密度两模型采用对应 `training/B-{C,E}-T0-RA-SMILES/checkpoints/step=21600.ckpt`。不能猜测最新checkpoint。

## 现有正式入口与历史绑定

现有主仓 `/home/penghongen/My_Project/PocketXMol` 保留 `训练与运行/sh/{train_docking,sample_docking,evaluate_docking,final_standard}.sh`；正式命令格式是 `bash 训练与运行/sh/sample_docking.sh <精确配置名>`、`bash 训练与运行/sh/evaluate_docking.sh <精确配置名>`，CA2完整入口为 `bash 训练与运行/sh/final_standard.sh <精确配置名>`。GT官方配置名为 `official-SMILES-test`，DG原配置与run.json相互绑定；不能拿当前默认参数覆盖旧run.json。

原DG72×1正式训练使用 `PocketXMol_ef9dd39`，随后标准H100采样沿各原launch绑定代码；原标准CA2计时release为 `PocketXMol_9322032b81bd`。无密度CA2的实际命令为 `final_standard.sh B-C-T0-RA-SMILES-CA2` 和 `B-E-T0-RA-SMILES-CA2`，release `PocketXMol_4a962d616ccd`，实际launch分别 `/home/penghongen/Feedback/PocketXMol/launches/438245/formal_B-C-T0-RA-SMILES-CA2_20261030T183919/` 与 `/438200/formal_B-E-T0-RA-SMILES-CA2_20261030T184401/`。这两份run_cmd已实读；本轮不重跑。

## 原排序和科学统计

C0是真实配体中心口袋，E是真实包络口袋；它们与预测blob中心的235共同实例比较属于不同协议。每实例50个姿态、100步、原self-ranking。原评分为 `cfd_traj + no_clashes指示 + stereo指示`，同分按sample_index升序；Top-1是原评分首位，Top-5是原前五的最低参考RMSD，best-of-50才是全部50的最低参考RMSD。`sample_index` 与成功SDF中的 `sdf_index` 分开使用。RMSD在实验世界坐标计算，不作刚体叠合；成功阈值严格小于。

当前箱体25–75百分位、中心中位数、须10–85百分位；长尾保留参与分位数与KDE，图内裁显示范围不裁统计。GT+Envelope中位数1.5549794162→1.1370062913 Å，CA2+Envelope为1.8133578631→1.2123998082 Å。冻结英文稿的1.55→1.14只能解释为GT+Envelope；不为迎合其CA2语境改写原文件。

Build计时读取两份Centre DG原评价的 `sampling_seconds`，各446观测，50姿态/100步/batch50/FP32；H100均值26.0914395200秒，A800为39.8039594334秒。它们不是仅改变GPU的配对实验，不报告硬件加速倍数；不得混入 `inference_seconds/evaluation_seconds`。

正文 Fig5 原生9WUP视图g–i的官方/DG构象来自GT/C0的9wup occurrence2、FAD A:1103，原sample分别22/18；不能用端到端预测blob构象替换。其完整poses.sdf、ranking/evaluation及受体/密度从相应服务器原根读取。
