> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 按竞争身份数分组图的稳定入口

`ops/render.py` 复用相邻共享模块 `plot_categories_pair()`，默认当前新口径，默认产物进入 `stage2/output/stage2-results/regenerated/stage2-strongest-pair/`；`--output` 指定检查目录，显式 `--profile old` 才读取旧口径。

冻结 JSON 的 `strongest_by_candidate_smiles_count` 保存两受体、四类别、五身份数组的正确数／支持数，五组为 1、2、3、4、≥5。每类计数加和等于六轴主图分类总数。这里不从预测目标反推未命中身份，不重新定义分组；原两受体179-PDB manifest及其完整身份/候选轴已保全到output。`ops/rebuild_groups.py` 从实际身份轴和冻结预测重建所有计数，已与当前图JSON逐值一致，完整来源见 [阶段追溯](../图表追溯.md)。先读稳定入口，再读共享的 `plot_categories_pair()` 即可沿同一条数值到图形的链阅读。
