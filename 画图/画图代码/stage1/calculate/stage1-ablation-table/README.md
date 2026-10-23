> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Find 消融表的导出

本目录维护补充材料表 4 的制表入口。`ops/export_table.py::export_table()` 从 `output/stage1-ablation/frozen/` 中11份原始 `.metrics.json` 读取六变体六指标，不连接服务器，不运行模型或科学评价。每份原始文件均配有179-PDB JSONL及服务器来源/散列收据。

`--output` 指定目录中的 `table.csv` 保留原始精度，`table.md` 显示三位小数。每行一个模型变体，六数列依次为 CA2 和 GT 的 Dice、PRAUC0.3、PRAUC0.5。推荐先看 [追溯文档](../图表追溯.md) 中 `stage1-ablation-table` 的证据层级，再读 `export_table()` 的指标字段读取与导出代码。该工具不修改原稿粗体、下划线或表格结构。

在论文根运行：

```powershell
D:/Anaconda/python.exe -B 画图/画图代码/stage1/calculate/stage1-ablation-table/ops/export_table.py --source 画图/画图代码/stage1/output/stage1-ablation/frozen --output temp/trace_table4
```
