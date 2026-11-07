# 补充Fig3的来源与统计

完整标识`stage3-ablation-envelope`, 正式图集`画图/PPT/stage2-stage3结果.pptx`。a/b显示GT/CA2下标准Envelope口袋的Build三模型完整分布。本图来源总览见[Build](../../../../追溯文档/source/Build.md)、[Match](../../../../追溯文档/source/Match.md)和[CryoAtom2受体](../../../../追溯文档/source/CryoAtom2受体.md); 本图唯一重建命令与阅读顺序见[README](README.md)。

## 标准Envelope Build

本图协议为`E`。GT逐实例原评价在`/storage/penghongen/PocketXMol/sampling/<model>/test/E/occurrences.json`; CA2为`/storage/penghongen/PocketXMol/final_evaluation/standard/ca2/<model>/test/E/occurrences.json`。本图只读以下六份, 不读取另一口袋协议:

| 图内模型 | GT目录model | CA2目录model |
| --- | --- | --- |
| PocketXMol-official | official-SMILES | official |
| PocketXMol–simple fine-tune | B-E-T0-RA-SMILES | B-E-T0-RA-SMILES |
| DG-PocketXMol | local_cov-E-T0-RA | local_cov-E |

每份必须保留全部446个`(pdb_id,occurrence_id)`唯一原键, 统一排序后六组轴一致。`top1_rmsd_A/top5_rmsd_A/oracle_rmsd_A`为原排名前1/5/全部50的最低参考RMSD, 单位Å。缺失仍留446分母; 原始模型GT组有445个有限值, 其他组446。这里是标准真实Envelope口袋, 不是预测blob的235交集, 不代入Fig5共同检出分母。

小提琴KDE使用全部有限RMSD, 长尾参与拟合与归一化; 25/50/75百分位为箱体/中位数, 须为10/85百分位。分位数从完整分布独立计算, 无离群散点。图内仅显示0–10Å, 参考线1/2Å; 成功统计严格小于阈值, 不将无姿态补0。

## 原实验身份与说明

实际配置、checkpoint和历史运行保存在各原结果目录的`test/run.json`及release/launch。官方checkpoint是`/storage/penghongen/PocketXMol_official_test/extracted/data/trained_models/pxm/checkpoints/pocketxmol.ckpt`; DG本协议对应`/storage/penghongen/PocketXMol/training/local_cov-E-T0-RA-b72/checkpoints/step=24800.ckpt`; 无密度模型对应`/storage/penghongen/PocketXMol/training/B-E-T0-RA-SMILES/checkpoints/step=21600.ckpt`。本次不训练、采样或评价, 只读取已存在原件。

历史标准入口为`bash 训练与运行/sh/sample_docking.sh <精确配置名>`、`evaluate_docking.sh <精确配置名>`以及CA2的`final_standard.sh <精确配置名>`。标准说明原件为`C:/Users/15919/Desktop/PocketXMol/docking/README.md`; 现存冻结release说明包括`/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/docking/README.md`和`/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_9322032b81bd/PocketXMol/docking/README.md`。无密度CA2实际命令为`final_standard.sh B-E-T0-RA-SMILES-CA2`, release为`PocketXMol_4a962d616ccd`, launch为`/home/penghongen/Feedback/PocketXMol/launches/438200/formal_B-E-T0-RA-SMILES-CA2_20261030T184401/`。不能用当前默认checkpoint冒称这些历史原件。

本图的完整科学读取与分布函数唯一归属正文Fig5, 本图显式引用这些函数, 只传本协议数据。本图作者显示定义与正式PPT备注独立保存; SSH、SVG及PPT容器操作均由不含实验规则的TOOLS承担。独立正文数字的claim解释不进入本图绘图入口。
