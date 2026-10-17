# Handoff: Fig.4小分子范围恢复为Stage1全部94／821

Date: 2026-10-17

## Current State

Fig.4下排已从误用的Stage3成员77个PDB／446实例纠正为原Stage1全部小分子94个PDB／821实例。新统计、可编辑PPT、中英Stage1 Results和四份正文Word均已完成及验收。前一轮77／446数值仍保留为Stage3结果，不能再作为Fig.4下排来源。

## Completed

- 新代码位于`画图/画图代码/stage1/find_completion_20261017/assemble_data.py`，只使用原Stage1类别及完整Find元数据；GT／CA2复用已有全配体候选中的Find字段，Emap2lig复用原全类别交集与唯一对应函数。背景保留，范围外前景跳过，重复命中占位置但不重复增加实例数。
- 正式数据独立保存于`画图/formal/Stage1_find_completion_20261017/`；`panels.json`是三份完成度面板，`summary.json`是显示数字，`sources/`保存94份类别文件与来源。原26个面板及所有姿态配对逐项完全不变。新增论文内部scope为`find_stage1_small`，没有增加端到端视图。
- Fig.4仍在`画图/Find-Match-Build公平对比.pptx`第一页，2行3列。只有第一页图形和双语备注两个XML部件改变，其余PPT部件逐字节相同；第一／二／三页原生可编辑组件数为3504／1998／4123。
- 100%相对候选数下的PDB等权均值为GT70.5%、CA259.8%、Emap2lig44.2%；300%为73.3%、68.5%、51.6%。中英文正文与图注均使用94／821。
- 四份正文Word全部17图；CN Nature／Operation为52／46页，EN为57／51页。Fig.4位于CN第11／11页、EN第14／12页，均与完整图注同页。206页中200页正文区域与上版逐像素相同，6页实际查看，无新增缺字、裁切或重叠。只有Fig.4图片改变。
- 主代理自查、三路一轮独立审查全部通过。合成非测试样例覆盖背景、零候选、非小分子全局对应及重复命中；原始候选数和忽略数逐PDB与Stage1报告一致。

## Decisions

作者已多次明确：先在全类别中确定唯一对应，再判断其类别，不能先筛小分子后重选对应。该定义沿用，不再反复请求确认。本轮仅扩展论文Stage1统计；不得据此改写`AdaLigand/ligandseek_pipeline/evaluate.py`或重跑模型。

AdaLigand当前`Learn/CUMULATIVE`为`ec91aa1`，原5份暂存注释完整保留。本轮仅修正其`测评数据代码/test_and_pipeline.md`的错误范围，作为未暂存文档修改留给作者处理。纸仓分支为`codex/fig4-stage1-small-molecules`，共同基点`c5e0b2d`；不操作其他仓库分支或远端。

## Next Actions

本轮无待跑任务或待决策事项。后续重绘Fig.4时先运行Stage1统计脚本，再运行`stage3/fmb_20261015`共享装配入口；不能恢复为旧`find_small`。Stage3、Fig.14及补充材料保持既有77／446口径。

英文阅读版仍为`draft.operation.fmb.docx`，不要把作者打开的旧`draft.operation.docx`误当成本轮输出；标准英文阅读版及作者窗口没有关闭或覆盖。

## Files To Reopen

- `RULES/执行记录.md`的2026-10-17条目：正式命令、来源、结果表及验收。
- `画图/画图代码/stage1/find_completion_20261017/README.md`
- `画图/Find-Match-Build公平对比.pptx`
- `论文草稿.md`、`draft.md`
- `temp/fig4_stage1_all_small_20261017/{result-gate,word-structure,ppt-final-preservation,visual-qa}.json`
