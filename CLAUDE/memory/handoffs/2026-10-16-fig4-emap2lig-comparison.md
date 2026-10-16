# Handoff: Fig.4加入Emap2lig并完成图文比较

Date: 2026-10-16

## Current State

作者后续要求已完成：Fig.4从2×2扩为2行3列，加入Emap2lig全配体／完整小分子面板；三组新增图注均改用LaTeX数学表达；中英Stage1、Stage3和补充材料比较叙述同步。八份Word已编译及完成实际页面验收，详细来源、正式命令与结果见`RULES/执行记录.md`本日最后一节。本记录接续同日`2026-10-16-find-build-fair-comparison.md`，旧记录中的2×2和249页为前一版本事实。

## Completed

- `画图/Find-Match-Build公平对比.pptx`第一页为六面板，行对应全配体／完整小分子，列对应GT／CA2／Emap2lig。横轴`Relative candidate count (%)`；Fig.4图注及Stage1叙述没有计费措辞。其余两页图形和数据不变，全部9,421个原生组件可编辑。
- 从统一服务器根只读取得182份冻结Find来源文件，放入`画图/formal/fmb_20261015/sources/Emap2lig/find_metadata/`，附原路径、大小及SHA256。没有重跑模型、重算体素交集或控制服务器作业。直接复用原对应与统计函数，原24个面板及姿态配对完全一致。
- 100%候选数量下，全配体平均检出为GT66.4%、CA255.6%、Emap2lig25.9%；完整小分子为76.3%、64.2%、48.5%。正文据此直接说明比较优势；Stage3加入83.1%／79.4%的较低Top-1 RMSD配对比例。
- 三组双语图注在PPT备注使用`$...$`，单位为`\mathrm{Å}`，不能改回当前Pandoc不支持的`\mathrm{\AA}`。Word已核对原生公式及阅读版9pt图注格式。
- 三路独立审查通过；最终250页中218页正文区域与上版逐像素相同，32页实际查看，无新增裁切、重叠或缺字。Fig.4与完整图注均同页。

## Decisions

Find-only只用候选数量解释横轴；端到端图仍保留既有尝试预算规则。图注的科学含义、原始对应、排序、完整分母和失败口径均不变。源码及正式绘图入口仍位于`画图/画图代码/stage3/fmb_20261015/`；本轮不触碰AdaLigand双线Git或模型实现。

两个英文阅读版继续发布为`draft.operation.fmb.docx`、`supplementary.operation.fmb.docx`，标准文件和作者窗口未动。最终正文CN Nature／Operation52／46页，EN57／51页；补充CN12／9页，EN13／10页。

## Next Actions

本轮无待跑计算或待决策事项。作者若修改图或图注，仍回到共享PPT再编译Word。正式稿使用本轮上述八份输出，不误用旧英文标准阅读版。

## Files To Reopen

- `画图/Find-Match-Build公平对比.pptx`
- `论文草稿.md`、`draft.md`、`补充材料.md`、`supplementary.md`
- `画图/画图代码/stage3/fmb_20261015/README.md`
- `RULES/执行记录.md`
- `temp/fmb_fig4_20261016/final-structure.json`、`visual-qa.json`：最终散列、原生结构及版面验收。
