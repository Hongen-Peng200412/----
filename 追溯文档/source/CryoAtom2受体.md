# CryoAtom2 原受体与同网格适配

服务器产物根：`/storage/penghongen/Adaligand_infered_receptor_data/cryoatom2/test_0_chain06`。本地副本：`追溯文档/source/CryoAtom2受体.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 结构来源

本根的 `cryoatom2_artifact/<pdb>/<run_stamp>/<run_stamp>.cif` 是官方默认最终受体，`*_raw.cif` 是另存的较完整结构，两者不混用。`运行日志与统计/pdb/<pdb>/latest.json` 选择具体成功版本；每次尝试保存 `inputs.json/command.json/status.json`、FASTA和官方日志，`运行日志与统计/runs/<run_stamp>.json` 保存软件、权重、配置与分片身份。不能按目录名猜最新结构，也不能把失败残留CIF当成功原件。

原预测入口在服务器 `/home/penghongen/My_Project/AdaLigand/测评数据代码/cryoatom2原始预测结构/sh/predict.sh`，输入是原EMDB压缩图和完整蛋白质/RNA/DNA序列，不读取沉积受体坐标。具体每PDB的真实参数数组以本根command.json为准；它们是原生产的直接参数，不是AI handoff叙述。

## Find 与绘图直接读取

`Ori_Data/parse/<pdb>/receptor_tokens.npz` 与 `density/<pdb>/{sim.npy,sim.npz}` 由最终受体适配得到。正式Adapter入口是 `/home/penghongen/My_Project/AdaLigand/测评数据代码/cryoatom2_受体Adapter/sh/prepare.sh`，原成功release为 `/home/penghongen/Feedback/AdaLigand/releases/AdaLigand_c209bedb1883/AdaLigand`，Job368455原launch `Find_1_pdb_centric_2_job368455_20260915T135210_a14` 实际调用该release入口。calibration同构原件位于同级 `calibration/Ori_Data`。

Adapter只替换受体和模拟密度。实验图、配体身份/坐标与标签继续引用沉积主Ori_Data，不能将该共享链接误认为第二套重算真值。坐标原世界XYZ，不拟合、不平移；molmap在实验图原网格上生成sim，保持shape/voxel/origin。当前CA2 Find、Match、Build、复合物和保护会话均使用此受体分支；GT分支仍读取沉积受体，两个条件不得互换。
