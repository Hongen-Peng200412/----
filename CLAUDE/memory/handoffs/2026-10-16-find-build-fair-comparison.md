# Handoff: Find–Build公平比较图文完成

Date: 2026-10-16

## Current State

获准的三组新增结果已进入中英文正文和补充材料；八份Word完成编译与249页逐页可视核查。本轮原始统计、运行和服务器来源统一记录于AdaLigand仓库`测评数据代码/端到端测评/结果与日志/总日志.md`，论文编译与版面事实记入`RULES/执行记录.md`。

## Completed

- `画图/Find-Match-Build公平对比.pptx`三页依次为Find-only 2×2、预测blob引导的GT／CA2姿态比较2×2、假定身份正确的完成度2列6行。第三页从上到下为Emap2lig／CA2／GT各4个条件。8325个原生形状、文字和路径可编辑；三页双语图注在PPT备注，图名在传统@@批注。
- 所有正式绘图代码位于`画图/画图代码/stage3/fmb_20261015/`；输入和配对统计位于`画图/formal/fmb_20261015/`，后者依现有规则不入Git。服务器最终科学结果实际统一到`/storage/penghongen/Adaligand_E2E/test/test_0`，不是仅保存旧路径索引。
- Find-only进入`论文草稿.md`／`draft.md`的Stage1，预测区域公平对接进入Stage3，假定正确身份分析进入`补充材料.md`的指定小节并同步`supplementary.md`。旧真实中心对接图及图注未修改；237例旧Results仅澄清为有可评估姿态的范围。
- 最终中文正文Nature／Operation为52／46页，英文为57／50页；中文补充为12／9页，英文为13／10页。四份正文各17图、补充材料各4图／4表，无未解析图号。十二面板图宽5.5in，四份图注均完整同页。英文末表以已有data-page-break语法单独起页，数值和表注未改。

## Decisions

共同命中GT235例／CA2230例分别比较；RMSD箱图使用231／228个数值配对，严格成功率仍用235／230分母。正式候选次序、对应和评价沿用冻结来源。图注、正文和曲线均从同一统计文件取得数值，不为作图重跑推理。

两个英文Operation原文件被作者Word占用，保持原文件及窗口不动。新完整稿保存为`draft.operation.fmb.docx`和`supplementary.operation.fmb.docx`，后续不得误用旧标准文件名作为本轮新稿。其他六份输出使用标准文件名。

## Next Actions

本轮无待跑计算。作者若要将两个英文阅读版恢复为标准文件名，需在保存并关闭原文件后明确处理。未扩大修正旧正文的列表编号、Methods长公式或案例留白；实际页码见本轮执行记录。

## Files To Reopen

- `画图/画图代码/stage3/fmb_20261015/README.md`
- `画图/Find-Match-Build公平对比.pptx`
- `RULES/执行记录.md`
- `temp/fmb_20261015/final-structure.json`：最终八份Word和PPT的SHA256及结构计数。
