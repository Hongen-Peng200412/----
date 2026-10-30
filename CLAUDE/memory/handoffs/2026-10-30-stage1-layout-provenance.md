# Handoff: Stage1 间距与作者版本追溯

Date: 2026-10-30

## Current State

本轮按作者授权压缩两张 Stage1 补图空白, 并落实作者版本与退役页面的追溯。原 18 条检查提示已收口, 全仓追溯现为99条记录／86张图、0错误。四份正式补充Word已写回, 每份实际仅两张PNG变化, document.xml逐字节相同；四份均9页且第2／3页独立视觉核查通过。结果及正式命令见本轮[执行记录](../../../talk/stage1_layout_provenance_20261030/执行记录.md)。

## Completed

- 第30页2×3、第31页2×2保持完整内容, 只压缩间距；按作者追加反馈, 2×3的b/e整体左移画布宽度1.8%, 有明确的横向等间距检查豁免, 其他对齐与碰撞仍严格通过。
- 作者中途另行保存了Stage1 PPT, 已以最新文件为底只更换两页的原生形状树。其他页面图形、媒体和备注保留。全部正式图集的Figure Editor占位批注归并为现有Hongen Peng（HP）, 没有增加不明作者。
- `(v数字)` 自动继承去掉末尾后缀的科学来源, 保留NO_LEVEL。重建返回基础科学候选, 手工作者版保留在正式PPT。颜色版逐条记录author_origin, 五个失效图名已撤下, 冻结代码与素材未删。
- 六张颜色示意图的最新原生对象分别冻存在e2e/output/overview-redesign-20261028与method-ab-variants的source/author-colors-20261030.pptx。author_native只用于示意图作者对象重开, 不能代替真实数据重算。
- 三项独立审查及问题窄核通过, 17项针对测试通过, 两张数据图屏蔽旧temp完整重建通过, 两个示意图来源家族原生重开通过。872个非目标作者科学部件和1,428份冻结元数据未变。

## Decisions

作者已暂存上一轮修改, 本轮不执行Git暂存、提交或恢复索引。期间作者独立修改并暂存draft.md和supplementary.md, 必须保留；不能用最初index.before覆盖当前作者索引。

本轮Word仅替换现有四份补充Word的两张图, 全部文字、图注和表格XML保持原样, 不把其他作者Markdown修改一并写入Word。临时两图Markdown经唯一Word编译入口取得新图片；该临时输入不是长期科学来源。

## Open Questions

作者当前英文补稿含跨正文图stage1-overall-performance(v1)的引用, 但补稿中没有该图定义, 直接全稿编译会被现转换器拒绝。本轮未改该文字、未扩展跨稿引用功能；后续若要求全稿编译, 应按作者届时意图处理。

## Next Actions

作者审查工作区叠加修改后手动提交。再次工作前读取最新HEAD、暂存区及PPT, 保护作者并发编辑。不要恢复已删除的历史页或重写未授权章节。

## Files To Reopen

- [本轮执行记录](../../../talk/stage1_layout_provenance_20261030/执行记录.md)
- [版本与来源规则](../../../RULES/图表追溯规则.md)
- [重建及来源工具契约](../../../转换工具/ops/README.md)
- [补图代码与统计契约](../../../画图/画图代码/stage1/calculate/stage1-additional-analysis/README.md)
