# Handoff：9BJJ建模能力定量扩写

Date: 2026-11-02

## Current State

作者鼓励依据真实结果突出建模能力，并要求增加篇幅。中英文9BJJ小节已扩为两段，报告两类配体、多位点任务与成功实例、Top-1 RMSD范围和亚埃精度，最后归纳重复出现及化学身份不同配体的端到端建模能力。

## Completed

原合格实例为9个ATP和2个A1AP0，原成功实例为9个ATP和1个A1AP0。十个有参考Top-1 RMSD的范围为0.5034656632565824–1.1161003298413592Å，正文为0.50–1.12Å，其中8个低于1Å。背景ATP仍保留，原RMSD为空。没有重算原子RMSD、重新选择姿态、修改原评价或引入新的precision/recall指标。

独立数字追溯为e2e/calculate/图表追溯.md中的9bjj-top1-capability；summarize_9bjj_top1.py只摘录冻结JSON并给出范围和计数。来源、原sample_index及服务器路径保存于author_9bjj/performance_source.json，结果为performance_summary.json。独立窄审已批准数值、表述与模块布局。

作者2026-11-02优化的全流程小分子案例_作者9BJJ.pptx及双语图注整文件保持，正文其他小节不变。四版Word同步至本轮编译记录指定的完整文件；若原文件被占用则旁存为9bjj-capability后缀，不关闭作者窗口。精简核验及实际输出路径见author_9bjj/capability_20261102/。

## Files To Reopen

- [英文正文](../../../draft.md)
- [中文正文](../../../论文草稿.md)
- [执行记录](../../../RULES/执行记录.md)
- [数字追溯](../../../画图/画图代码/e2e/calculate/图表追溯.md)
- [本轮证据](../../../画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/capability_20261102/validation.json)
