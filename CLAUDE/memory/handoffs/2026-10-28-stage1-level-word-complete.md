# Handoff: Stage1 六面板与四份正文 Word 完成

Date: 2026-10-28

## Current State

本轮 Stage1 显式 level 六面板病例、原生教学会话、PPT、最小双语源稿与四份正文 Word 全部完成。此交接接续并关闭[上一阶段交接](2026-10-28-stage1-level-cases.md)中等待示意图选择和 Word 编译的事项。当前正文 15 图，9NVS 为新 Fig. 3；补充源稿及四份补充 Word 保持原字节。

Git 保持 `main@bf6b96234745c22320ff320591ac3506e31b3c27`，未暂存、未提交、未切分支。后续由作者审查 diff 并决定提交；不要自动提交或丢弃本轮未提交内容。

## Completed

- 五套完整病例为 9NVS 主选和 9NAL、9UJF、9WFU、9X0X 备选，当前 `画图/stage1可视化.pptx` 第 9–13 页；原 8 页保留。9BJJ、11JB、30GA 未作为本轮新例选择。
- 5 份初始 CXS、30 份最终 CXS、30 份独立教程及 CXC、30 张 PNG 与完整来源齐备；35 份会话屏蔽旧 temp 后离线重开通过。科学身份、筛选、坐标、共享相机与实际 blob 匹配见前阶段交接及长期 README，不重跑模型。
- 新科学原件只属于 `explicit_emdb_level`。原 EMDB 推荐 L 显式传入，原官方实际阈值 L/2；原实跑代码为 `37b0d9e7ad2a1b18fa096d91f154619085cee907`。局部实例 Dice 不等同逐 PDB 语义 Dice，旧 Emap2lig 无 level 掩码没有复用。
- 作者选定正文沿用总览第 2 页、Method 第 3 页。总览第 3/4 页、Method 第 4/5 页的同名编辑页改为 `-EDITING-页码`，复制来源标记改为普通编辑稿来源副本并保留全文；所有图形、备注、媒体均与作者基线相同。
- 全局检查进一步发现四张已移出当前图集的历史示意页，原件在作者 10-27 备份中。冻结副本保存在 `画图/画图代码/e2e/output/fig12-revision/historical_diagrams_20261027/`，仅分离副本来源管理权，科学组件及图注与备份字节相同。E2E 追溯修正四图路径和八条相关页码，不把旧页恢复进当前图集，不改作者备份。最终全局追溯通过 73 条记录／61 图。
- 四份正文已发布：`draft.nature.docx`、`draft.operation.docx`、`论文草稿.nature.docx`、`论文草稿.operation.docx`。各含 15 图，新增 Fig. 3 的图像和完整图注同页；位置分别为第 11、10、9、8 页。四份原生 PDF 共 211 页，检查了全篇联系表及新图全尺寸页面，无页外文字或缺字，60 套图片/图注回转标记全部吻合。
- 原 14 张图保留各自 Word 基线的媒体字节、像素与 EMU 尺寸；原 14 图图注只随自动编号顺延。原正文文字除图号和新增段之外保留，英文各 223 个、中文各 216 个正文公式 XML 及作者标记保留。英文阅读版原有减号/ell 字形没有被编译器替换。
- 一次主代理自查、三项独立代码审查及必要窄复核完成；最后 Word 独立契约复核通过。旧 22 份 CXS、13 份作者 PPT 备份、四份补充 Word 和 18 份其余根文件散列一致；原 Stage1 的旧幻灯片、关系、备注及媒体字节一致。

## Decisions

最小修改边界继续有效：不润色已完成正文，不重新组织其他章节，不顺带执行老师剩余意见或系统格式调整。本轮双语 Markdown 各只增加一个 9NVS 段落和一个图引用，移除插入后与作者基线逐字节一致。

**有两类任务前已有的文字差异，不要误认成本轮遗漏后直接改写。** 英文 Markdown 的 Find 首段已有 `which additionally supplied`，旧 Word 使用逗号后 `supplied`；总览/Method 的 PPT 备注与旧 Word 也已有两处图注差异。本轮保留旧 Word 原句、原图注与格式，Markdown 与 PPT 备注均不顺带修改。后续要统一时，作为独立文字修改先核对，不因重新编译擅自带入大片图注变化。

冻结产物在 `画图/画图代码/stage1/output/stage1-level-global-local/explicit_emdb_level/`，固定规则忽略但必须保留。`session_reopen_verification.json` 为离线会话验收，`delivery_verification.json` 为病例/绘图验收，`word_publish_verification.json` 为最终四稿、页面、保护与发布散列。临时目录 `temp/stage1_level_cases_20261027/` 可清空，最终正式 Word 和科学原件不依赖它。

Word 转换仍使用现有唯一入口，没有修改转换器。Windows 缺少 LibreOffice 的 soffice.exe，实际采用独立隐藏 Word COM 只读导出 PDF；不要调用 Repaginate/ComputeStatistics。候选编译用 bundled Python；Windows COM 与 PDF 核查使用现有 Anaconda 和固定 `figure_runtime`，没有安装新依赖。

## Next Actions

本轮没有剩余实施事项。等待作者审查当前 Word、PPT、学习材料与未提交 diff，并决定后续策略性修改或提交。不要自动继续其他章节重构。

## Files To Reopen

- [最终任务记录](../../../talk/stage1_level_visualization_20261027/执行记录.md)、[覆盖映射](../../../talk/stage1_level_visualization_20261027/映射.md)。
- [五例与教学入口](../../../画图/画图代码/stage1/visualization/stage1-level-global-local/README.md)、[正式 PPT](../../../画图/stage1可视化.pptx)。
- [英文阅读版](../../../draft.operation.docx)、[中文阅读版](../../../论文草稿.operation.docx)、[英文 Nature 版](../../../draft.nature.docx)、[中文 Nature 版](../../../论文草稿.nature.docx)。
- [Stage1 可视化追溯](../../../画图/画图代码/stage1/visualization/图表追溯.md)、[E2E 可视化追溯](../../../画图/画图代码/e2e/visualization/图表追溯.md)。
