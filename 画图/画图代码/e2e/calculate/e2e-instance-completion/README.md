> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 实例完成度的冻结数据、重汇总与绘制

本目录从既有候选、身份和构象评价生成十种完成度条件、两张正文汇总图及十二页同源候选图；不执行模型推理、姿态重排或RMSD评价。两张正文表共用相同冻结分布。

按 `aggregate.py::fixed_budget_records → make_panel → main` 阅读预算取整和实例去重，再读 `plot.py::draw_panel → make_figure → main` 阅读分布与阶梯，最后读 `svg_shapes.py` 理解同源几何转原生形状；PPT装配程序和 `ppt_metadata.py` 只操作临时候选。

冻结输入位于 `e2e/output/e2e-instance-completion/`，原轨迹在 `e2e/output/e2e-accounting/`。`completion.json.panels`每项保留精确事件曲线、完整逐PDB固定预算分布、去重首次成功事件、全部候选用尽的结果；`per_pdb.csv`与`summary.csv`分别保存逐PDB值和预算摘要。全配体179PDB／2502实例，小分子77PDB／446实例。完成比例为不同成功实例数/N，预算为floor(ρN)，均值和中位数都保留完整PDB轴。

```powershell
python 画图/画图代码/e2e/calculate/e2e-instance-completion/aggregate.py
python 画图/画图代码/e2e/calculate/e2e-instance-completion/plot.py
python 画图/画图代码/e2e/calculate/e2e-instance-completion/svg_shapes.py
python 画图/画图代码/e2e/calculate/e2e-instance-completion/ops/export_tables.py
```

第一条只读原冻结输入，新汇总写 `e2e/output/e2e-instance-completion/regenerated/`；第二、三条读取原冻结完成度，把SVG／PDF／PNG、manifest和scenes写 `temp/e2e_completion_20261011/`；第四条只读核对中英文正文两张表。正式PPT `画图/E2E实例完成度.pptx` 不被这些命令覆盖。来源、参数、计费及80个双语结果单元格核验见[阶段追溯](../图表追溯.md)。
