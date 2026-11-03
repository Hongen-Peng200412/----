# Handoff：新增作者9UJF全景与追溯修复

Date: 2026-11-03

## Current State

9UJF作者author01.cxs/png已作为新病例加入英文9BJJ图后及中文对应位置，各新增两段和独立PPT引用。9BJJ作者原文、PPT、两份补充稿及其他正文逐字节保持。新图为`画图/全流程小分子案例_作者9UJF.pptx`，图名`full-pipeline-small-molecule-author-9ujf`。

## Completed

原CA2／100%／Top-1结果为10个GTP合格实例全部成功，原预算为10次计数尝试；原RMSD范围0.5364181402709665–0.8048328745384161Å，正文为0.54–0.80Å，全部亚埃。原模型排名、样本编号、对应、计费、RMSD与完成度均只读，不重新评价。ZN参考不纳入建模结论。

作者相机、显隐、颜色及结构坐标保留，新图不裁切或加标签。原生PPT、冻结输入、十构象来源CSV、逐步教程、初始材料链接及最终CXS齐备。完整旧temp屏蔽重建通过且PNG逐像素一致，教程与作者配置／十构象一致，最终CXS仅打开后相机保持。新增病例的科学表述、代码布局和注释通过一次独立窄审。

作者追加授权修复两处全局追溯问题。核实提交19391e9删除旧流程PPT，当前四稿均无图名引用；三个旧登记冻结到`e2e/output/e2e-flow/retired_20261103/历史追溯记录.md`并退出活动登记，源程序和输入保留，没有恢复已删图。

四版Word在作者追加“本轮不需要编译Word”之前已经编译完成，之后未再编译；后续不继续Word版面收口，不将此作为本轮任务要求。

## 追溯修复最终状态

作者保存关闭PPT后，已重新读取最新E2E结果.pptx并修正e2e-main-top5(v2)的继承来源标识。只改变ppt/comments/modernComment_10D_1B4861ED.xml，其余图形、数据、布局、图注及所有包部件逐字节一致；正文与Word保持。全局追溯检查112条记录／98张图全部通过，报告和单部件差异证据已归档author_9ujf/qa/。

本轮无待完成项。pending目录仅为先前文件锁失败的历史候选，已有已完成标记，不可用旧整包覆盖当前作者文件。此次未编译Word，没有修改科学结果。

## Files To Reopen

- [新PPT](../../../画图/全流程小分子案例_作者9UJF.pptx)
- [9UJF教程](../../../画图/画图代码/e2e/visualization/actual-small-molecule-cases/author_9ujf教程.md)
- [最终会话](../../../画图/画图代码/e2e/output/actual-small-molecule-cases/author_9ujf/author_final.cxs)
- [本轮核验](../../../画图/画图代码/e2e/output/actual-small-molecule-cases/author_9ujf/qa/validation.json)
- [共享执行记录](../../../RULES/执行记录.md)

作者开始时三份staged资产保持，未暂存、提交或推送任何内容。没有接触服务器、模型运行资源或AdaLigand Git。
