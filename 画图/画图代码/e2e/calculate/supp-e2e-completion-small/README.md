# supp-e2e-completion-small 的单图选择入口

`plot.py` 是本图的长期入口，与 `e2e-instance-completion` 共用实现；共享不代表读取临时源码。关联图、实际函数、输入字段及本图选择见[所属追溯记录](../图表追溯.md)。

完整重建从仓库根运行 `python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure supp-e2e-completion-small`，按顺序生成图稿、场景和带来源的 `rebuilt.pptx`。旧temp不可读；新产物在新的 `temp/figure_rebuild/<运行号>/supp-e2e-completion-small/`，冻结输入保存在所属output。直接运行本文件只执行绘图这一步，PPT装配请使用完整命令。

建议先读追溯记录中的共享关系，再读本入口的图名／面板选择，最后读共享绘图函数。统计分母、阈值、排序与单位以追溯记录及冻结数据为准，本入口不重新推理或定义实验结果。
