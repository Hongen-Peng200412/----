> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 两张 top-k success 图的共享原生制图

`build_nature_figures.py::main` 读取 `e2e/output/e2e-top-k/data.json` 的冻结整数计数，调用 `panel` 绘制全配体和小分子两页PowerPoint原生曲线。当前两页已归并到 `画图/E2E结果.pptx`，由补充材料按 `e2e-all-find-match`、`e2e-small-pipeline` 引用。

先读 `panel` 的坐标与整数到百分数转换，再读 `main` 的曲线选择；`save_deck` 只保存候选与检查预览。默认输出到 `temp/e2e-top-k/`，不覆盖当前图集。运行需要Windows PowerPoint与pywin32，本轮没有启动PowerPoint重建。

冻结 `data.json` 的 `full` 保存179个PDB的Find／Find+Match计数；`small_find`、`small_match`、`build`固定77个PDB。数组位置依次对应K=1…10，值为至少成功一次的PDB数。`build[domain]["local_cov-C"]`是当前单次中心对接；`C-C`／`C-C-E`是历史附加字段，不混入当前两页。姿态阈值为严格 `<2`／`<3 Å`，top-1沿原模型自评分，best-of-50为评价上界。

全配体每候选计费一次，小分子实际Match和Build采用Match感知计费，Find-only采用独立理想身份定位诊断。完整原轨迹和计费重汇总位于 `e2e/output/e2e-accounting/` 与 `e2e/calculate/e2e-accounting/`。字段、原服务器来源、正文数值和两种计费的区别见[阶段追溯](../图表追溯.md)。
