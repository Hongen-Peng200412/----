# 正文完成度表的只读核对

`export_tables.py` 从冻结 `completion.json` 生成两张正文表的40个结果值，并逐格核对中文和英文正文。它不修改 Markdown、PPT 或冻结科学数据。

先读模块说明及 `export_tables`，再读 `TableValues` 的 HTML 单元格收集。输入按面板稳定 `id` 定位，100%／300% 的 `distributions` 保留完整 PDB 轴；均值为 PDB 等权宏平均，中位数使用相同轴，显示百分数保留一位小数。表1固定GT／CA2两行，表2固定四种姿态／阈值条件、先CA2后GT。

从仓库根执行：

```powershell
python 画图/画图代码/e2e/calculate/e2e-instance-completion/ops/export_tables.py
python 画图/画图代码/e2e/calculate/e2e-instance-completion/ops/export_tables.py --output-dir temp/figure-provenance/table-export
```

第一条只向终端输出核对 JSON；第二条另写辅助 `completion_tables.csv` 和 `completion_tables.md`。CSV 一条对应一个结果单元格，`value_percent` 保留完整百分数，`display` 为正文显示字符串，`table/condition/domain/budget_percent/statistic` 联合定位单元格，`pdb_count` 保存均值或中位数的完整样本数。任何单元格或结果数量不同均返回非零退出码；不自动用导出覆盖作者表格。
