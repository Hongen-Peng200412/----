> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Match 六轴图的稳定入口

`ops/render.py` 默认读取当前新口径，复用相邻共享模块的 `plot_radar_pair()`，生成六轴双面板图的 PDF、SVG、PNG、TIFF 和布局核查；默认输出在 `stage2/output/stage2-results/regenerated/stage2-radar-pair/`。指定 `--output temp/<本次任务>/radar` 可生成检查候选，显式 `--profile old` 才采用旧口径。

`ops/export_selected.py` 从本地四模型完整 `frozen/<model>.json` 恢复 selected 候选摘录，核对原件散列及摘录逐值等价。原 `export_selected.sh` 是同一字段契约的服务器只读导出命令，不在日常本地重绘中执行。

`aggregate.py::aggregate()` 读取旧冻结数据、selected 摘录和已保全的 Matcher 指标函数快照，复现旧前景指标，再排除不支持身份的真前景。默认只在 `regenerated/aggregation/` 写新 JSON、两口径统计和核查收据，不覆盖冻结输入。输入的候选、阈值和源身份契约见 [阶段追溯](../图表追溯.md)。推荐先读 `aggregate()` 的排除条件和分母，再读共享绘图函数；历史 PPT 局部修补已归档，不进入当前生成链。
