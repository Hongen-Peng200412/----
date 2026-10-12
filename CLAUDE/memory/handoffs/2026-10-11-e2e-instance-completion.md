# Handoff: 端到端配体实例完成度补充分析

Date: 2026-10-11

## Current State

本轮获批分析、可编辑 PPT、中英文补充材料及 Word 编译已完成。所有本轮改动留作 unstaged，未暂存或提交；工作前已有 staged Word 与 `stage1结果.pptx` 保留。当前 HEAD 为 `62add74c0826c2cb6db8122f44a9dfbf091dd07d`，Git index SHA256 仍为 `fc99b98b3cee224a00a0ba91dd3d2dbbba403194a90557d41bfa24bb4a26e0f7`。

## Completed

- 从冻结轨迹直接汇总全配体 179 个 PDB／2,502 个实例，以及单残基无缺失原子的有机小分子 77 个 PDB／446 个实例。没有重跑 Find、Match、对接或 RMSD 评价。
- `画图/E2E实例完成度.pptx` 共 12 页：十张独立图，随后两张汇总图。8,537 个 PowerPoint 原生形状，无栅格媒体；点、曲线、分布、坐标轴与文字均可编辑。两张汇总页图名为 `supp-e2e-completion-all`、`supp-e2e-completion-small`，双语图注在备注。
- 完整定义、图、结果表及说明写入 `补充材料.md`／`supplementary.md`。正文 `论文草稿.md`／`draft.md` 只各新增一段简短说明；扣除新增段落后，两个文件与工作前快照相同。
- 八份 Word 已通过现有 Nature／Operation 编译入口生成。补充稿各有两图、两表，Nature 各七页，Operation 各五页。主稿图号与十四幅旧图保留。
- 完成一次独立全面审查、仅针对问题的窄复核、实际 PowerPoint 渲染和 Word 版面核查。补充稿 24 页均检查全尺寸图；主稿 210 页检查全部概览和新增段落附近 13 页全尺寸图。证据与所有中间文件在 `temp/e2e_completion_20261011/`。

## Decisions

计数单位为配体实例，不是 SMILES 身份；预算为 `floor(ρN)`，同一实例最多完成一次，重复候选仍计费，首次成功后继续累计。均值与中位数均按 PDB 等权计算。

保留 selected 优先、unselected 追加的冻结候选顺序及排名超过 20 的候选。全配体每候选计费一次；小分子沿用真实 Match 感知免费跳过规则。小分子仅复用 PocketXMol-tuned 单次初始 C 对接，原 self-ranking top-1 与 best-of-50 严格 RMSD <2／<3 Å 均不改变。

图的预算范围为 0–300%；300% 只是显示截点，不是候选上限。曲线为精确预算事件的阶梯线，不插值或平滑。小提琴只表达逐 PDB 的分布，不参与统计计算。

新补充材料与正文沿用同一 PPT 引用、双语图注和自动图号系统，每份补充稿独立从图 1 编号。没有修改转换器或事后单独加工 Word。中文 Operation 表 2 跨两页，续页重复表头；Nature 表格单独分页，图 2 与图注同页。旧正文的大图分页留白保持原样。

## Next Actions

等待作者审阅本轮补充分析与图稿；没有自动扩展分析或改写正文的后续任务。需要更新图注时回到所属 PPT 备注，再编译对应中英文稿。正式生成命令与门控命令已分别记录在 `RULES/执行记录.md`，不在本交接重复流水账。

## Files To Reopen

- `补充材料.md`、`supplementary.md`：完整补充分析源稿。
- `画图/E2E实例完成度.pptx`：唯一正式图稿。
- `画图/formal/E2E_completion_20261011/README.md`：数据字段、来源和有效科学口径。
- `RULES/执行记录.md`：本轮生成、编译、发布与检查记录。
- `temp/e2e_completion_20261011/final-audit.json`：来源、作者内容与 index 保全，以及正式 PPT／八份 Word 散列。
- `temp/e2e_completion_20261011/independent_review.md`、`narrow-review.md`、`main-word-visual-review.md`：审查证据与观察范围。
