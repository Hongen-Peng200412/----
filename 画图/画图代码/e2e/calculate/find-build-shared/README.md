> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Find–Build 共享实现

本目录保存三张论文图共同读取的冻结结果组装、完成度图元及同源SVG转原生PPT工具。每张图的布局入口位于所属阶段的同名目录，统计定义不在多个目录复制。

| 图 | 独立绘图入口 | 临时构建目录 |
|---|---|---|
| 纯Find实例完成度 | ../../../stage1/calculate/find-only-instance-completion/plot.py | temp/find-only-instance-completion |
| 预测区域引导的对接比较 | ../../../stage3/calculate/stage3-predicted-region-head-to-head/plot.py | temp/stage3-predicted-region-head-to-head |
| 正确身份Find–Build补充曲线 | ../supp-find-correct-match-build/plot.py | temp/supp-find-correct-match-build |

`assemble_data.py`连接两种Find命中实例与原构象结果；`completion_plot.py::draw_panel`只画冻结的逐PDB分布和精确事件阶梯；`save_figure`接受调用图的构建目录，输出SVG/PDF/PNG与图名、物理尺寸和双语图注。RMSD仍为原模型排序的Top-1或best-of-50，失败保留完整成功率分母；GT共同命中235、有效配对231，CA2共同命中230、有效配对228。

冻结输入位于 `../../output/find-build-shared/`，字段和版本见所属阶段图表追溯记录及原产物README。重建数据默认写regenerated，不覆盖原件。建议依次读取冻结data.json契约、所属图plot.py，再读共用图元；场景运输不参与科学计数。

在仓库根先运行某张图的plot.py，再运行 `python -B 画图/画图代码/e2e/calculate/find-build-shared/svg_shapes.py --build-root temp/<该图名>`，随后执行 `node 画图/画图代码/e2e/calculate/find-build-shared/assemble.mjs temp/<该图名>`。场景字段保持原有pt坐标、文字、独立散点和路径；新候选位于对应output/regenerated，不自动覆盖作者图集。需要PowerPoint实际渲染时再显式调用ppt_metadata.py的同一--build-root参数。

旧三图联合生成器已归档；当前各图只生成自身布局。正式图集的来源批注通过仓库转换工具ops/figure_provenance.py同步。
