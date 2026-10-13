# Handoff: LigandSeek1 held-out 与论文比较已收口

Date: 2026-10-13

## Current State

本项完整任务已完成：官方 v1.0.0 完整 PV 的358项双受体推理／评估、179／149／94的六套汇总、四份AdaLigand文档、中英补充小节、六单图加组合图的可编辑PPT及四份Word全部验收。正式科学根为 `/storage/penghongen/AdaLigand_stage1_inference/Ligandseek1/official_v1.0.0_pv`。不再重跑、重校准或释放资源。

A100 Jobs400875／400876、A800 Job400877均回到try_lock。锁根为 `.../ligandseek1_held_out_20261011/feedback/allocations/`：根目录的try_lock与各Job子目录的after_lock均存在，kill_lock不存在；Slurm仍RUNNING仅为保留allocation，不是模型还在运行。不要触碰这些锁或使用scancel。

## Completed

- 两种受体各179项，test_1各149项保序派生，固定小分子视图各94项；真实实例分母分别2,502／1,536／821。14份最终metrics／JSONL／provenance内容与服务器摘要一致，358个complete均ok，没有静默空预测替代失败。
- 正式科学适配、模拟输入转换、汇总与稳定运行入口已归属 `C:/Users/15919/Desktop/Ligandseek`；服务器源码 `/home/penghongen/My_Project/Ligandseek`，维护Learn/CUMULATIVE=`ac49e8a8f31bba6a6fc236002e1a724c88c3a49a`。实现端点09526e4与学习端点完整tree相同，两端及Linux25测试通过，真实四组合220字段／12汇总严格等价。
- 实际全部实验仍由旧不可变运行release生成，未热替换已有前向；新正式源码不改变其科学事实。原本地 `temp/ligandseek1_held_out_20261011` 已不存在，831文件已校验UTF-8恢复归档，仅保留退出的恢复材料，不被代码导入。
- 独立科学审查59,120区间值、208macro、11,900micro一致性、72实例池化P/R、54top-K全部通过；内容审计3,783文件和3,768旧摘要一致。正式根 `运行记录/验收/content_sha256.json` SHA为 `125c6bd0b0f2c63a8b31d51672a09f907f870ff1febbee92944928417d366b56`。
- AdaLigand四文档456行只提交文档；实现端点6c29195，学习／累计端点 `1930489877c2d357eebb21913f43cf7f7bb2a6a1`，完整tree均 `afe0c424a12e4bd3c98ce29478715ef402e027b2`。工作区干净、累计唯一最新，没有push。
- 六图长期代码位于论文 `画图/画图代码/stage1/ligandseek1_comparison/`。prepare只计算冻结指标的绘图统计，render只画图，JS只transport同一SVG；不重算交集、匹配、PRAUC或资格，不计算正式科学哈希。数据为 `画图/formal/LigandSeek2_vs_LigandSeek1/data/`，1,092行源CSV和24行柱图统计。
- 图集 `画图/LigandSeek2_vs_LigandSeek1.pptx` 七页、10,997原生形状、168文字框，无raster media；所有组件可编辑。Calibri和实际Unicode下标齐全，现代批注身份必需字段已补齐，图名／双语备注完整。实际PowerPoint七页全部查看，PDF最小8pt、对齐及碰撞门控通过。PPT SHA=`0b4e2c4e422bf0dabbacaf96acd8eb9401d0c1207e26a04427efe775e7a61218`。
- 中英补充材料保留作者原Stage3，仅追加Stage1与表3；图名 `ligandseek2-vs-ligandseek1` 自动Fig.3。48个表值与真实统计一致。中文完整Nature10页／阅读版6页，英文12页／7页，共35页逐页核验后原子发布；旧四稿备份在 `temp/ligandseek1_word_20261013/canonical_preimage/`。
- Word阅读版表行拆分已最小修复到稳定 `_apply_operation_layout()`，只改格内零缩进／单倍／3pt段后及cantSplit。正文、Nature、公式、单元格文字与数值不改；1个定向测试、17种图注边界×2语言×2版式及往返回归通过。三角色仅窄复核已提问题，实际Table3完整同页，未扩大科学范围。

## Decisions

完整PV，GT阈值0.79／CA2阈值0.88，seed0，不重新校准，保持官方预处理和后处理。初始56项batch1按授权复用，后续A800 batch12为111项、A100 batch6为191项；历史批量不写成统一值。CPU评估使用allocation自带4核，joblib每核1worker。

旧实际模型命令为 `exec bash /storage/penghongen/tmp/ligandseek1_held_out_20261011/run.sh`；正式维护入口为 `exec bash "${TASK_PROJECT_ROOT}/训练与运行/sh/infer/ligandseek1_held_out.sh"`，二者在日志区分。门控、绘图、Word编译不是模型正式命令。哈希仅在独立ops／临时校验中使用。

test_1复用同一事实，不是独立前向或统计样本。小分子94／821视图不含语义PRAUC，不与Stage3的77／446建模资格混淆。完整集LigandSeek2的三个macro图指标更高；CA2小分子PRAUC₀.₃为0.572615／0.567725，接近，不写成普遍优势或因果、显著性结论。

论文仓库按用户Git授权保持main及本轮改动unstaged；作者并行提交与RULES手工修改保留，没有提交或改写稿件历史。主稿 `论文草稿.md/draft.md` 未改，原 `stage1结果.pptx` 未改。AdaLigand仅文档提交，Ligandseek正式实现与学习历史整理完成。

## Next Actions

等待作者审阅补充小节与新图。无需再次运行模型、汇总或申请资源；若修改图形／图注，回到本图PPT及正式绘图源，再按当前转换工具编译，不导入退役临时代码。资源只在新的明确授权下接管或释放。

## Files To Reopen

- [执行日志](../../../实验记录/LigandSeek1/执行日志.md)与[索引](../../../实验记录/LigandSeek1/索引.md)：实际命令、release、launch、输入／输出哈希和全部验收。
- [中文补充材料](../../../补充材料.md)、[英文补充材料](../../../supplementary.md)、[可编辑图集](../../../画图/LigandSeek2_vs_LigandSeek1.pptx)。
- [四份结果文档入口](../../../../AdaLigand/收口の结果/Stage1/Ligandseek1/说明.md)。
- [正式绘图说明](../../../画图/画图代码/stage1/ligandseek1_comparison/README.md)，正式科学说明位于 `Ligandseek/src/ligandseek/evaluation/README.md`。
- `temp/ligandseek1_word_20261013/publication.json`：四份Word发布前后摘要、来源构建与页数；各版本渲染仅为内部QA。
