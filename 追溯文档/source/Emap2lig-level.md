# 显式 EMDB level 的 Emap2lig Find 与 Build

服务器产物根：`/storage/penghongen/Emap2lig/contour_level_20261026`。本地副本：`追溯文档/source/Emap2lig-level.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 输入、条件与原命令

`inputs/maps.json` 固定179 PDB的原始压缩地图、EMDB推荐值L、来源元数据与散列。L显式交给官方入口，官方有效阈值为L/2（contour_ratio=.5）；这与旧“不显式传level”的实验是不同条件，不能视为同一结果的重复副本。

正式命令 `bash 训练与运行/sh/with_level.sh`，实际源码提交 `37b0d9e7ad2a1b18fa096d91f154619085cee907`，冻结release `/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig`。实际launch `/home/penghongen/Feedback/Emap2lig/launches/423330/build_gate_job423330_20261026T202139_a2/`，A800/24CPU；run_cmd明确执行with_level，不能按build_gate前缀误认为门控。当前主仓同入口仍在 `/home/penghongen/My_Project/Map_Ligand/Emap2lig/训练与运行/sh/with_level.sh`。原程序和模型保持不动。

## 原件布局与身份连接

- `find/held_out_test_0/evaluation/official_find_li.{metrics.json,jsonl}`：全配体汇总及逐PDB指标。
- `find/held_out_test_0/evaluation/per_pdb/<pdb>.npz`：候选×真实实例交集、原分数、selected、体素数及原source_blob_index。
- `find/held_out_test_0/mapped/<pdb>/{official_blobs.npz,mapping.json}`：映射回共同实验网格的完整blob和原官方概率图路径。
- `build/find_hit_subset.jsonl`、`build_occurrences.jsonl`、`build_all_occurrences.jsonl`、`build_summary.json`：请求资格、逐姿态RMSD、完整446实例状态和汇总。
- `build/build/<pdb>/<occurrence>/<launch>/build_struct/blob_*/`：原CIF与评分；`preprocess/ligands/LIG.npz` 是化学输入，不是参考/预测姿态。

全Find为179 PDB/2502真实实例、2474 blob，其中15 PDB零blob；全部小分子94/821。Build候选是446合格实例中的260 Find命中，9个因官方前景体素/重原子比例不在[5,25]而过滤，251完成。当前实际文件系统枚举有12,550候选CIF（251×50），另有251份best目录导出，总CIF数12,801。过滤资格不能在新统计中改作Build失败或从全Find分母删除。

连接预测与真实实例必须用PDB+occurrence；blob编号只在其本方法中定位。保留原 `consistency_iou` 排名，Top-5为原评分前五的最小RMSD，best-of-50为全部50的最小；不按真实距离重排Top-1。坐标为原实验世界XYZ、Å，不叠合。

## 当前论文如何使用

Stage1主图及补充分析读取本条件原评价；小分子semanticDice从原映射blob并集与 `/storage/penghongen/AdaLigand/Ori_Data/density/<pdb>/ligand_area.npz` 的小分子GT并集本地计算。类别归属先对全部真实类别以双向覆盖0.3确定，非小分子归属候选忽略，其余背景保留。

Match–Build联图与GT/CA2预测结果取PDB+occurrence三方共同合格交集235；标准446实例消融不套用235分母。9WUP原Top-1 CIF为 `build/build/9wup/2/build_gate_job423330_20261026T202139_a2/build_struct/blob_4/blob_4_LIG_27.cif`，RMSD1.788314456 Å；其LIG输入按原子名连接，密度覆盖和碰撞按原GT受体/实验图定义，不能用新截断密度替换覆盖度原地图。
