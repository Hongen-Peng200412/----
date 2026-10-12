# Handoff: LigandSeek1 正式代码归属与等价验收

Date: 2026-10-12

## Current State

LigandSeek1 完整 PV 的 test_0 双受体任务仍在三卡上运行：A800 Job 400877／gnode09 使用 batch 12；A100 Jobs 400875／gnode04、400876／gnode01 使用 batch 6，均 4 CPU。after_lock 保留。正式科学产物全部位于 `/storage/penghongen/AdaLigand_stage1_inference/Ligandseek1/official_v1.0.0_pv`。

用户否定把长期科学代码留在论文临时目录的组织方式。本轮已将适配、评估、模拟密度输入转换和稳定队列入口正式纳入 `C:/Users/15919/Desktop/Ligandseek`，并同步到 `/home/penghongen/My_Project/Ligandseek`。现有服务器进程继续使用原冻结版本，不热修改源码，不中断已有前向；用户明确允许复用这些任务与产物。

正式维护端点是 `Learn/CUMULATIVE=ac49e8a8f31bba6a6fc236002e1a724c88c3a49a`。新科学 release 为 `/storage/penghongen/tmp/ligandseek1_reorganization_20261012/releases/Ligandseek_7d698093e938/Ligandseek`；当前三卡仍使用旧 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/releases/batch_20261012_49a0be631421/batch_20261012`，不要混淆维护源码、验收快照与正在运行的快照。

## Completed

- 正式 `evaluation/adaligand.py` 保留原生身份、float64 均分排序、最近体素独立映射、完整概率线性映射和固定小分子归属；所有指标仍调用 Pocket Plus 成熟函数。
- `evaluation/simulation.py` 保留已有模拟密度及官方历史 MRC 原点处理，`evaluation/held_out.py` 只汇总冻结事实，`execution/held_out.py` 只管理官方 CLI、原子队列与每核一 CPU worker。
- 主代理完成结构／Docstring／科学行注释自查；一轮三角色独立全面审查，修复后只窄复核，全部通过。六个函数的布局由用户委托的独立审查者批准。
- 实现端点 `09526e44687da58fd1348c0ed6ab6ecd6c1b4558` 与学习端点完整 tree 都为 `6f8ce4794caeae00fd74438b9f202270adc480f8`。学习线顺序为文档、科学适配、汇总、运行组合、独立 ops、最后测试；CUMULATIVE 快进到唯一最新提交，main/origin 未改，没有 push。
- 两端本机全量各 25 测试通过；新正式冻结 release 的 Linux 全量 25 测试和 bash -n 通过。冻结 Pocket Plus 依赖来自 5bd1593，其 evaluation.py 与旧运行依赖逐字节相同。
- 真实四组合 `9ter/9lfa × deposited/inferred` 的旧／新／正式已完成产物，220 个 NPZ 科学字段和 12 个 metrics/JSONL 完全一致；42 个正式文件 pre/post SHA 不变。证据 `/storage/penghongen/tmp/ligandseek1_formal_gate_20261012/equivalence.json`，SHA `eff6c9137cfe5cb21693a3f2f790f1fccc171f2c3cc23b9a8f1cb9e33ca9f962`。不把四样本门控冒充全179结果验收。
- 绘图规格与 `prepare_plot_data.py` 已归属论文 `画图/画图代码/stage1/ligandseek1_comparison/`。唯一公共入口仅生成只读统计，6 项测试和一轮三角色独审及问题窄复核通过；四方法×三柱图指标共享 bootstrap，P/R 只计算分布与分位数。不得重新计算掩码、匹配、PRAUC 或资格，没有生成占位图或正式全量统计。
- 旧本地 `temp/ligandseek1_held_out_20261011` 已不存在。全部 831 文件经逐内容校验归档至 `temp/ligandseek1_reorganization_20261012/legacy_recovery_utf8.zip`，SHA 为 `9def3c074a16bb0e5a8c0b70aa4dee4b3cb0c67490fa8e645157a70cfae36e64`。递归删除被工具安全策略拒绝，原文件可恢复移至同处 `recovery_files_inactive/`，只作退役材料，不是入口或源码依赖。

## Decisions

用户允许从官方发布提交 1bc4399 建立双线；正式源码与入口不能继续留在 temp。哈希仅在独立 ops／临时校验工具中计算，不参与科学逻辑、任务选择或默认入口。旧运行记录已有哈希保留；新正式运行记录不实时计算摘要，最终独立校验报告记录内容完整性。

保持完整 PV、官方 GT 0.79／CA2 0.88、seed 0，不重新校准；原初 batch 1 已完成产物继续复用。记录实际逐 PDB 批量，不把全轮写为统一批量。test_0=179、test_1=149 保序派生；小分子范围为冻结 94 PDB／821 实例。

未来正式入口为 `exec bash "${TASK_PROJECT_ROOT}/训练与运行/sh/infer/ligandseek1_held_out.sh"`，POCKET_PLUS_ROOT 显式绑定冻结依赖。当前实际旧命令继续为 `exec bash /storage/penghongen/tmp/ligandseek1_held_out_20261011/run.sh`；测试／门控不是正式命令。原 controller 根与新科学代码根可能不同，须分别留证。

## Next Actions

继续守护三个真实 Job，不创建 heartbeat，以连续 300 秒睡眠构成稳定静默窗口。native_ready 仅表示前向完成，complete 才表示评估完成，不重复前向；不得重新创建旧本地临时目录或使用退役恢复代码作为生产入口。

全部结果完成后验收 179/149/94 的成员、顺序、完整指标、实例坐标与交集，生成 AdaLigand 四份文档、双语补充材料、六图可编辑 PPT 和 Word。绘图统计程序已就绪，需先只读下载验收的真实 L1 JSONL 再运行，不使用测试夹具或退役代码生成论文图。

论文作者已自行提交至 main `eb5c825`，本轮未提交作者内容或整理其历史。只为 `ligandseek1_comparison` 增加 .gitignore 窄例外使正式源文件可审阅，其他旧 Stage1 代码仍忽略，本目录 __pycache__、pyc 和 pytest 缓存继续排除；新增代码、规则和记录都保持未暂存。

若未来切换遇到 aggregate_claim 已存在但总 complete 缺失，先核验汇总者是否仍运行；只有已经终止才非破坏性备份孤立领取目录，不提前加恢复逻辑。未经新指令不释放 after_hold，不 scancel。

## Files To Reopen

- [任务执行日志](../../../实验记录/LigandSeek1/执行日志.md)与[索引](../../../实验记录/LigandSeek1/索引.md)。
- `C:/Users/15919/Desktop/Ligandseek/src/ligandseek/evaluation/README.md` 与 `talk/refactor/2026-10-12_held_out正式归属.md`。
- [独立绘图规格](../../../画图/画图代码/stage1/ligandseek1_comparison/规格.md)。
- [中文补充材料](../../../补充材料.md)、[英文补充材料](../../../supplementary.md)，保留既有实例完成度内容。
