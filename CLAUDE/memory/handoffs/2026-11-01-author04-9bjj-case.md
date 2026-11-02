# Handoff：作者author04替换正文案例

Date: 2026-11-01

## Current State

正文采用作者最终指定的`画图/古法Chimera/E2E/9bjj/author04.cxs/png`，替代此前11JB／9BJJ五面板。旧图、PPT及教程保留为基础设施。新PPT为`画图/全流程小分子案例_作者9BJJ.pptx`，图名`full-pipeline-small-molecule-author-9bjj`。

## Completed

英文小节改为“Small-molecule modelling in a large complex”，中文同步。正文报告原10/11重建、分散位点的ATP／A1AP0及背景预测与遗漏；图注补充原11次计费预算、Top-1、颜色、坐标系和原成功判据，避免重复数量报告。没有新实验、评价重算或原统计变更。

原生重开author04保留作者相机、颜色和显隐，所有32个显示结构的场景变换为单位阵。11个显示构象含无参考RMSD的背景blob10。单页PPT仅等比放置并加可编辑图例；新程序和隔离重建路由已经接通。原生重建图逐像素一致，图的字体／碰撞和107条追溯记录、94图的来源检查通过。独立窄审批准代码布局和科学表述。

四版正文Word均已成功写入原文件名；本轮应使用`draft.nature.docx`，早先的actual-output旁存稿不再是最新。英文Nature25页／Operation23页、中文Nature23页／Operation22页，新图及完整图注同页并逐一目视通过。

## Decisions

author04是最终指定版本；01／03只在本轮早期核对中出现，不作为发布来源。原始作者文件保留，采用时的副本冻结到`e2e/output/actual-small-molecule-cases/author_9bjj/source/`。正式制图、门控重建与Word命令分别保存在RULES执行记录与本轮精简证据。论文改动保持未提交，未接触服务器或AdaLigand Git。

## Files To Reopen

- [正式PPT](../../../画图/全流程小分子案例_作者9BJJ.pptx)
- [原生命令教程](../../../画图/画图代码/e2e/visualization/actual-small-molecule-cases/author_9bjj教程.md)
- [作者视角最终会话](../../../画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/author_final.cxs)
- [验收证据](../../../画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/validation.json)
- [执行记录](../../../RULES/执行记录.md)
