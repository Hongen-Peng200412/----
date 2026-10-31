# Find 与 Find–Build 比较使用各自的合格候选定义

Type: decision
Date: 2026-10-30
Tags: manuscript, build, emap2lig, eligibility, denominator, author-confirmed

## Context

作者在 2026-10-30 明确纠正 AI 对 Build 比较分母的解释。下列定义是作者确认的科学契约，优先于旧追溯文字、汇总字段名和 AI 对“失败应保留分母”的一般推断。

## Memory

- 当前正文的 Emap2lig 合格 Build 集合为 251 个实例。预测 blob 必须满足双向覆盖均至少 30%，并通过 Emap2lig 的体素数／配体重原子数比例筛选；正式实现保留比例在闭区间 [5,25] 的 blob。
- 被该比例筛选排除的 blob，即使覆盖真实配体，也不属于本次 Find–Build 对接比较的合格候选；不得把它们重新作为 Build 失败放回论文比较分母。当前论文两组共同检出且可评价的集合为 GT 241、CA2 237。
- 内部“筛选前共同命中”数 247、243 只可保留在内部实验与审计记录中，绝不可作为另一套分母写入正文、图注或结果图，也不可用它们重算并替换作者确认的 Build 成功率。
- 单独评价 Find 时，Build 专属比例过滤不生效；这些预测 blob 仍可作为合法 Find 预测参与原有区域检出评价。不能把 Build 的排除规则传播到独立 Find 指标。
- 作者本轮提出的新主图使用 DG(GT)、DG(CA2)、Emap2lig-Build 三方共同的合格且可评价实例：先执行上述 Emap2lig 合格筛选，再按 (pdb_id, occurrence_id) 求三方交集。全部姿态选择条件共用同一实例集合，不按 RMSD 好坏或某个成功阈值挑选。具体新分母须由冻结结果核查并在作者允许实施后同步替换对应图文。
- 2026-10-30 当前仅授权记忆保存与只读核查、讨论；尚未授权修改正文、正式图表、统计生成程序或启动新实验。

## When To Use

审阅或修改 Match–Build 合图、Build 条件成功率、Emap2lig 对照、共同实例集合及中英图注时。先区分独立 Find 评价与 Find–Build 比较，再应用各自纳入规则；不得再次把作者已排除的不合格 blob 混回 Build 分母。

## Related Files

- [英文正文](../../../draft.md)
- [中文正文](../../../论文草稿.md)
- [Build 计算追溯](../../../画图/画图代码/stage3/calculate/图表追溯.md)
- [Emap2lig 双条件资产](../../../补充数据/Emap2lig_双条件/README.md)
- [正式比例筛选实现](../../../补充数据/Emap2lig_双条件/explicit_emdb_level/provenance/code/显式level实验/prepare_build.py)
