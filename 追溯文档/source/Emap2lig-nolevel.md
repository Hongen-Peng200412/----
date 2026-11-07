# 无显式 level 的原 Emap2lig Find 条件

服务器产物根：`/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li`。本地副本：`追溯文档/source/Emap2lig-nolevel.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

本根是旧实验，不是新level目录的镜像。当前英文补充 `stage1-no-level-comparison-NO_LEVEL` 仍使用它，因此不能因正文改用新条件就删除或改名冒充新条件。

原件位于 `held_out_test_0/evaluation/official_find_li.{metrics.json,jsonl}`、`evaluation/per_pdb/<pdb>.npz`、`mapped/<pdb>/official_blobs.npz` 和 `raw_find_outputs/<pdb>/`。原输入未显式传EMDB推荐level，原官方阈值条件与新L/2实验分开；score、source_blob_index和selected均使用本根事实，不从新条件回填。当前主仓读取/推理入口 `/home/penghongen/My_Project/Pocket_Plus/训练与运行/sh/infer/emap2lig_official_find_li.sh` 仍存在，短命令为 `bash 训练与运行/sh/infer/emap2lig_official_find_li.sh`。

本根实际保留 `held_out_test_0/reports/find_run_summary.json` 和每PDB的 `raw_find_outputs/<pdb>/status.json`，字段为原 `input_map/output_dir/blobs_dir/status_code/blob_count`；这些记录没有完整argv或release字段，不能用当前主仓HEAD补写旧实验版本。9NVS原输入明确为 `/storage/penghongen/AdaLigand/Ori_Data/raw/emdb_maps/emd_49849.map.gz`，原status_code为0、55个blob；`mapped/9nvs/mapping.json` 将原1.0 Å体素图映射到共同实验网格的1.0017391443252563 Å体素图。实际科学读取使用保存的原区域、交集和指标。

小分子原统计另在 `/storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/emap_official_li.{metrics.json,per_pdb.jsonl}`，原provenance固定94 PDB/821实例。当前制图对两种level条件采用同一逐PDB范围、PRAUC/P/R类别忽略规则与bootstrap参数；只切换明确的实验根。它不采用Build过滤后的251实例，也不使用旧Stage3请求数243作为Find分母。

原无level Build结果 `/storage/penghongen/Emap2lig/stage3_find_hit_build/` 和旧E2E副本继续原样保留，但退出当前英文展示的旧Build页不自动获得持续重绘义务。本说明不授权删除任何原始结果。
