> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 两代模型比较表的导出

本目录只恢复补充材料表 3 的制表入口。`ops/export_table.py::export_table()` 直接读取两代模型共用的冻结 `plot_data.json`，不重新平均逐 PDB 指标；读取顺序是 full 后 small、第一代后第二代、CA2 三指标后 GT 三指标。

输出目录由 `--output` 指定，保存 `table.csv` 和 `table.md`。CSV 第一列为集合、第二列为模型、后六列为 CA2 与 GT 的 Dice、PRAUC0.3、PRAUC0.5；数值保留冻结精度。Markdown 同序显示三位小数。函数不改写论文、图或数据；查看数据契约与完整来源，阅读 [本阶段追溯文档](../图表追溯.md) 的 `stage1-generation-comparison-table`。

在论文根运行：

```powershell
D:/Anaconda/python.exe -B 画图/画图代码/stage1/calculate/stage1-generation-comparison-table/ops/export_table.py --source 画图/画图代码/stage1/output/ligandseek2-vs-ligandseek1/data/statistics/plot_data.json --output temp/trace_table3
```
