# Handoff：实际预测构象补齐与小分子案例

Date: 2026-11-01

## Current State

本轮已完成。77个PDB范围内，GT与CA2共1045个Match预测小分子请求；548个直接复用原结果，450个新增请求成功生成22500份构象，47个按原引擎保存输入失败。完整结果与显示索引位于`/storage/penghongen/Adaligand_E2E/actual_display_20261101/`。本轮没有重算原RMSD、完成度或其他评价。

H200作业441686已成功执行一次，停回try_lock；hnode03的单H200与16 CPU资源保留，after_lock未删除。正式命令为`bash ligandseek_pipeline/ops/run_actual.sh`，release为`AdaLigand_e15f82b50271`，launch为`actual_display_job441686_20261101T155310`。不要将正式命令与保全核查命令混写。

## Completed

- 最终服务器审计通过：4212份原文件零变化，548个复用请求的3836份复制文件逐字节一致。全部1045条请求与显示记录的身份、中心和状态连接正确；新增构象无参考RMSD。完整索引、配置、请求、运行日志与审计报告另存长期工作台output的`actual_display_20261101/full/`。
- 九例工作台升级到1.0.8，初始CXS均已重开核验；248个原Top-5和34个新增实际Top-1接入，失败请求保留blob、身份和原因。旧5400组选项与792项原完成数连接保全。个人edit会话与作者原窗口未动。
- 新增[全流程小分子案例.pptx](../../../画图/全流程小分子案例.pptx)：11JB全景、AR6局部、9BJJ全景、ATP局部、A1AP0局部。固定CA2、原100%预算、Top-1；原预算内背景输出保留。长程序与冻结来源分属`e2e/visualization/actual-small-molecule-cases/`和`e2e/output/actual-small-molecule-cases/`。
- [五面板教程入口](../../../画图/画图代码/e2e/visualization/actual-small-molecule-cases/README.md#从初始会话复现五个面板)提供每面板一份MD、完整命令和解释、逐姿态来源CSV、最终CXS。五教程实际从initial执行，五最终CXS仅打开复查通过，保留论文视角。
- 新图完整隔离重建通过，旧temp不可读；五PNG与正式发布原生图逐像素一致，字号、碰撞、对齐及PowerPoint包通过。来源批注同步及全局追溯检查通过（105记录、92图）。
- 两正文仅新增案例及Methods说明，移除精确插入块后与基线逐字节一致；补充两稿、10份既有引用PPT、268份冻结数值元数据及1488份原构象／排名／输入文件均不变。独立审查批准函数布局，一轮全面审查后仅窄复核。
- 中英四版正文Word已更新，新图与完整图注同页。作者打开的`draft.nature.docx`保留，英文Nature新稿为[draft.nature.actual-output.docx](../../../draft.nature.actual-output.docx)；其余三版沿原文件名。主代理逐一目视新图页：英文25／24页、中文23／22页。补充Word未编译。

## Decisions

原Find+Match、给定正确身份的Find+Build与Find+Match+Build评价口径和数值全部固定。新增输出只完善实际体验与显示，不改变候选顺序、对应、计费、预算、分母或成功判据。种子不作为复用门槛；错身份不复用给定身份构象。

只处理Match预测为small_molecule的身份；输入不支持时保存失败，不扩展模型化学类型。原Top-5为原评分前五的最小原RMSD；无合法参考RMSD者三个选择档均显示同一Top-1并标注。青绿色表示有参考RMSD，棕色表示无参考RMSD，不能把青绿色等同于低于2 Å。

## Next Actions

本轮计算与图文交付无未完成项。作者可从教程入口打开相应初始或最终会话继续原生命令编辑。作者原ChimeraX窗口仍加载旧模块，使用1.0.8需先保存个人工作并重启；旧个人会话按工作台说明使用`ligwork upgrade`。

11JB两张完整模拟密度MRC保留并延迟载入，所需实验密度与原子材料已经加载。不要把延迟地图误记为材料缺失，也不要直接从备份文件夹打开依赖相对assets路径的旧CXS。

## Files To Reopen

- [本轮论文执行记录](../../../RULES/执行记录.md#2026-11-01实际预测构象显示与大复合物案例)
- [新图追溯](../../../画图/画图代码/e2e/visualization/图表追溯.md#full-pipeline-small-molecule-cases11jb与9bjj的实际小分子输出)
- [工作台开始使用](../../../画图/画图代码/e2e/visualization/multiligand-workbench/开始使用.md)
- [独立审查证据](../../../画图/画图代码/e2e/output/multiligand-workbench/qa/20261101_1.0.8/independent_audit/独立收口窄核查.md)
- [教程重开核验](../../../画图/画图代码/e2e/output/actual-small-molecule-cases/tutorial_reopen_validation.json)
- [服务器全量保全报告](../../../画图/画图代码/e2e/output/multiligand-workbench/actual_display_20261101/full/control/final_audit.json)

Ada实现分支`codex/actual-build-display`从作者基点d446d30创建，学习线为`Learn/actual-build-display`；最终等价记录保存在上述full目录的`git_equivalence.json`。实现分支保留，不推送远端。论文仓库本轮修改保持未提交，供作者审阅。
