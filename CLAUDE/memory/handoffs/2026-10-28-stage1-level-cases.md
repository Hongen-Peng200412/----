# Handoff: Stage1 显式 level 六面板与教学会话

Date: 2026-10-28

## Current State

作者已批准本轮端到端制作 Stage1 全局到局部病例；五套科学素材、PPT、教学会话及双语源稿插入已完成。**四份正文 Word 尚未重编译**，等待作者处理总览与 Method 图中基线已有的不同内容重复定位名。补充材料源稿及四份补充 Word 没有变化。不要把当前 Word 当成已包含新 Fig. 3。

Git 保持作者最新 `main@bf6b96234745c22320ff320591ac3506e31b3c27`，未提交、未暂存、未切分支。论文仓库本轮不创建 Learn 分支；不能把 Emap2lig 实验仓库的双线要求迁移来改写作者论文历史。

## Completed

- 从完整 179-PDB 测试集初筛 41 例，再核原体素、实际一对一实例匹配和受体邻近证据，保留 **9NVS（主选）、9NAL、9UJF、9WFU、9X0X**。9BJJ、11JB、30GA 均未选。没有推理、训练、Find/Build 或服务器作业。
- `画图/stage1可视化.pptx` 第 9–13 页为五套两行三列图，前 8 页保留。9NVS 新图稳定名为 `stage1-level-global-local-9nvs`，在源稿总体性能 Fig. 2 后插入，将显示为 Fig. 3。每套 a–c 全局、d 受体 FP、e/f 同实例；面板字母、指标、定位框和比例尺原生可编辑。
- 五套共 5 份初始 CXS、30 份最终 CXS、30 张 PNG、30 份独立教程及 CXC。全部 35 份会话在屏蔽旧 temp 后重开成功，均有 15 个顶层模型，30 个最终视角相机恢复一致。教程从 initial 重新开始，以明文 ChimeraX 命令调节，不使用预存最终视角恢复捷径。Python 只取材、转换、生成命令和读取相机状态。
- 初始会话包含预处理连续密度、两种受体、全部配体与真实区域、全部保留预测及局部材料。连续密度使用 `contour_canonical`，不能说成原 EMDB L；二值区域用 0.5 等值面，无平滑。受体 CIF 的 C<n>/res_index+1 为 token 编号，配体使用沉积 auth 标识，来源说明已解释。
- 新 Emap2lig 只使用 `explicit_emdb_level` 原件，源实验 `37b0d9e7ad2a1b18fa096d91f154619085cee907`：显式输入 EMDB 推荐 L，官方实际阈值 L/2。旧 no_level 仅复用公共 GT/CA2 材料；104 份来源回执文件独立核对。全部科学原件在长期 output，无 temp 依赖。
- 9NVS 为 A1B32 B:1001、occurrence 1；CA2/Emap blob 1/2，局部区域 Dice 0.792373/0.468521。全局 TP/FP 为 CA2 5/0、Emap 1/5；受体 FP blob 3 与全部真值零交集。局部实例 Dice 不等于全 PDB 语义 Dice。双语正文只新增这一例的一段及图引用；去掉插入后与基线逐字节一致。
- 主代理先自查，再完成三路独立审查；函数布局由受委托 reviewer 批准。相机共同视野、索引方向、CA2 邻域及路径说明的发现均关闭；新增装配／初筛尾链完成窄复核。
- 统一完整重建通过：从冻结原件重新筛查、转换、渲染五套并装配 PPT，旧 temp 被屏蔽。最后定位标号的显示间距修改仅重做装配，不重跑模型。五页以 Office PDF 检查最终 6.2 英寸宽度，图区对齐通过、最小实际字号约 6.81 pt、碰撞零 FAIL；白边上的标题提示已目视检查。
- 最终核验 24 份其他根文件、22 份旧 CXS、13 份作者备份散列一致；旧 8 页及其备注、媒体字节一致，旧第 1 页 Office 导出像素一致。

## Decisions

保护已有 no_level 与所有作者手工编辑。本轮不润色已有正文；仅新增局部结果段，机制解释衔接既有内部消融表 4，不将跨模型病例作为唯一因果证明。四个其他候选完整保留供作者选择。

长期代码位于 `画图/画图代码/stage1/visualization/stage1-level-global-local/`，共用邻目录 `stage1-global-local/screen_cases.py`、`prepare_assets.py` 的科学取数和 MRC/CIF 转换，旧默认入口仍可用。新 CLI 显式传 sources/cohort/cases，禁止把新旧 blob 编号互换。

冻结与教学产物位于 `画图/画图代码/stage1/output/stage1-level-global-local/explicit_emdb_level/`；按仓库固定规则忽略但必须保留。`session_reopen_verification.json`、`delivery_verification.json` 保存长期验收。`temp/stage1_level_cases_20261027/` 为可清空的门控、候选、检查和渲染；不能以清理 temp 为由删除 output。

## Open Questions

基线 `画图/总览图.pptx` 第 2/3 页均名 `fig-overview_v3`，`画图/Method总图.pptx` 第 3/4 页均名 `fig-method-v9`，两者均有不同内容。正式转换要求涉及图集的独立图名唯一；全局追溯目前仅报这两项，73 条记录／61 图中新增五图定向同步通过。**未改这两份作者图集，未强行选择后一页。**

已向作者询问：沿用当前 Word 的总览第 2 页、Method 第 3 页，并把另外两页定位名标为编辑稿（推荐）；或者选总览第 3 页、Method 第 4 页，把旧页定位名改为备份。等待回答，不能以时间经过视作批准。只调整未选页定位名与必要的复制来源元数据，保留图形和图注。

## Next Actions

1. 得到上述图源选择后，最小处理重复定位名，保留作者所有图形；再做全局来源同步与检查。
2. 使用现有工具将四份正文 Word 编译到本轮 temp，保留四份补充 Word 原字节。检查新 Fig. 3 顺序及后续自动图号，保留原正文公式 XML（英文 Operation 基线存在减号/ell 字形差异）和作者标记“改到这里”的变体。渲染、检查后才发布。
3. Word 原生 PDF 导出可复用旧任务 `temp/emap2lig_switch_20261027/render_word_one.py` 的操作方式，但不要建立长期 temp 依赖。避免 Word.Repaginate/ComputeStatistics；此前会长时间阻塞。新编译前读取转换说明与 documents skill。
4. 更新同一任务执行记录和覆盖映射；仅在这一剩余阶段结束再写交接。不要提交或暂存。

## Files To Reopen

- [五例与教学入口](../../../画图/画图代码/stage1/visualization/stage1-level-global-local/README.md)。
- [任务执行记录](../../../talk/stage1_level_visualization_20261027/执行记录.md)、[方案](../../../talk/stage1_level_visualization_20261027/方案.md)、[覆盖映射](../../../talk/stage1_level_visualization_20261027/映射.md)。
- [正式 PPT](../../../画图/stage1可视化.pptx)、[中文源稿](../../../论文草稿.md)、[英文源稿](../../../draft.md)。
- [Stage1 可视化追溯](../../../画图/画图代码/stage1/visualization/图表追溯.md)。
- [转换工具说明](../../../转换工具/README.md)。
