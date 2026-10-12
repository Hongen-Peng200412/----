# Handoff: LigandSeek1 官方模型 held-out 比较启动

Date: 2026-10-11

## Current State

已创建覆盖实验与论文交付全过程的 goal，并提交三项单卡资源预约：A100 Jobs `400875`、`400876`，A800 Job `400877`，每项 4 CPU、64 GiB 内存、无限时长、提交时 `pre_hold=1` 和 `after_hold=1`。三项资源均已进入正式队列：A800 在 gnode09，首项 A100 在 gnode04，第二项 A100 于 2026-10-12 10:11 在 gnode01 加入。各 after_lock 保留。

本任务不接管原发布线程的 Job。独立反馈根为 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/feedback`；正式产物根为 `/storage/penghongen/AdaLigand_stage1_inference/Ligandseek1/official_v1.0.0_pv`。

2026-10-12 发布线程已完成收口，本机与 A800 allocation 内的六项门控均通过。保存旧命令后原子替换 Job 400877 的动态命令，仅删除其 pre_lock；after_lock 保留，未触碰 kill_lock 或其他 Job。

首样本 9ter／GT 的官方参数确认 `threshold=0.79`、`seed=0`、`batch_size=1`；5 个预测实例与 2 个真实实例的评估产物完整。Python 3.10.13、PyTorch 2.4.1+cu121；所属 A800 实测 95% 利用率、约 5.3 GiB 显存，没有失败标记。接下来按静默窗口监控，不为普通 PDB 完成反复记录 handoff。

A100 启动前已有 48 项完成记录，未发现失败。allocation 内门控确认 A100-PCIE-40GB、4 CPU 和相同 PyTorch；保存旧命令与哈希后原子替换 Job 400875 动态命令，只删除 pre_lock、保留 after_lock。它领取 deposited/9nnc，未改变科学 release 或正式入口。launch 为 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/feedback/launches/400875/gpu_gate_job400875_20261012T082801_a1`；旧／新命令哈希与备份路径见执行日志。

2026-10-12 09:28 最新状态：按用户增量要求及明确 kill_lock 授权，两项运行资源已切换到新私有 release，A800 batch 12、A100 batch 6；只在 OOM 时分别考虑 8／4。保留 56 项首轮完成结果，仅备份未完成的 9o4e 双受体 native、转换密度和 claim，没有删除。备份根 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/backups/batch_switch_20261012T011503Z/` 保存 preimage 和旧运行入口。全部 56 个完成记录哈希未变。

本机／Linux 各 8 项门控通过，串行／joblib 并行的全部科学数组逐元素相同；A800 12 与 A100 6 的完整 9ter GPU 门控均无 OOM。新 worker 在前向阶段发布 native_ready，随后使用各 allocation 的 4 CPU、每 worker 一个线程并行评估；complete 仍仅表示官方产物和评估均完整。监控时区分这两种状态，不把尚未进入 CPU 阶段误当作停滞。

第二项 A100 400876 使用相同新 release、batch 6 和 evaluation_workers 4，领取 deposited/9if5；门控确认 A100-PCIE-40GB、PyTorch 2.4.1+cu121。启动 launch 为 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/feedback/launches/400876/gpu_gate_job400876_20261012T101100_a1`，旧动态命令备份及 pre／post 哈希已写入执行日志。只删除该 Job 的 pre_lock，没有接管其他任务。

## Completed

- 官方仓库 <https://github.com/Hongen-Peng200412/Ligandseek> 的 `v1.0.0` 已公开。只读克隆在论文仓库 `temp/ligandseek1_held_out_20261011/official_v1.0.0/`，commit 为 `1bc439987b5d3384db67b5a566f58f76f6d58acd`。
- 已核对当前论文、双语补充材料、Stage1 六图代码、现有 Pocket Plus 指标函数和小分子归属规则。当前论文展示的是 LigandSeek2；新比较使用官方 LigandSeek1 的预测，评价仍用当前标签和指标。
- `AdaLigand/收口の结果/Stage1/Ligandseek1/` 中四份现有文档是 Emap2lig 模板副本，不是 LigandSeek1 结果。必须先备份，不能将其中数值用于新论文比较。
- 现有四份文档、双语补充材料、术语表与参考 PPT 已备份至 `temp/ligandseek1_held_out_20261011/preimage_20261012/`。仅从 PPT 副本导出参考图，没有打开或修改作者原 PPT。
- `test_0=179`、`test_1=149` 的保序关系已核验；全部标签 2,502 个实例，小分子范围 94 PDB／821 实例。两种受体的原始 CIF、模拟密度和标签几何均已核对，CryoAtom2 使用最终 CIF。
- 评估适配器直接复用正式函数，六项隔离测试通过。私有运行包中 Pocket Plus 来自 `Learn/CUMULATIVE` 的 `5bd1593b71acef82f9f3379a4ede24c7c97b761b`；不调用工作区未提交代码，不修改服务器成熟评估模块。

## Decisions

独立保留官方包，不修改其模型或预处理；一次任务评估代码放在论文仓库 `temp/ligandseek1_held_out_20261011/`，调用现有 Pocket Plus 聚合和匹配函数，不把指标公式复制到官方包。主测试清单为 `test_0=179`；`test_1=149` 从同批逐 PDB 事实保序派生。

用户已明确确认官方完整 `ligandseek_pv`、GT／CA2 双受体和默认阈值 `0.79/0.88`，`seed=0`；不在当前 calibration 或测试集重新调参。按其最新要求，A800 batch 12、A100 batch 6；56 项初始 batch 1 结果复用。各项实际批量留在 launch 和官方 run_metadata 中，最终文档必须准确记录混合运行批量。

已验收的私有运行 release 为 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/releases/ready_20261012_d5b97cf4d9b9/ready_20261012`，内容 SHA-256 `d5b97cf4d9b906448f9bddd79ed295613ef1c8ce5a66425e136629bc24ff2899`。仅通过新 release 运行，不修改任何旧 release；保留 pending 候选包作为准备证据。

当前实际使用的是批量与 CPU 并行更新 release：`/storage/penghongen/tmp/ligandseek1_held_out_20261011/releases/batch_20261012_49a0be631421/batch_20261012`，内容 SHA-256 `49a0be631421627f21a018b83ce9936ff3ee22328a095569a46bf231fe2ed2bb`。旧 release 只读保留。第二次 launches 分别为 `gpu_gate_job400877_20261012T092126_a2` 和 `gpu_gate_job400875_20261012T092803_a2`，完整路径及配置／入口哈希见执行日志。

正式命令固定为 `exec bash /storage/penghongen/tmp/ligandseek1_held_out_20261011/run.sh`。Job 400877 外层 launch 为 `/storage/penghongen/tmp/ligandseek1_held_out_20261011/feedback/launches/400877/gpu_gate_job400877_20261012T012349_a1`。逐 PDB 官方命令、输入和产物哈希保存在正式根的 `运行记录/queue/`；完整 pre／post 哈希见执行日志。

作者已有 staged／unstaged 主稿、补充材料、PPT 和 Word 修改必须保留，不自行纳入提交。新六图使用独立 PPT，并通过现有 `pptfig` 插入双语补充材料。

## Open Questions

目前没有阻止正式运行的科学性问题。发布已完成，尚未完成的是 179-PDB 双受体推理、指标与实例产物验收，以及论文／文档交付。

## Next Actions

核验新加入第二项 A100 的推理与 GPU 活动；稳定后按 30／60／120 分钟静默窗口守护三项资源，不重复已完成前向、不释放 after_hold。native_ready 增长表示预测正常进行，complete 在后续 CPU 评估阶段增长。

验收后生成 AdaLigand 四份文档、双语补充材料、六图可编辑 PPT 和 Word；按作者要求完成来源、路径、正式命令与哈希记录。稳定排队或运行时以连续 `Start-Sleep -Seconds 300` 组成静默窗口，不创建 heartbeat。

## Files To Reopen

- [执行日志](../../../实验记录/LigandSeek1/执行日志.md)：资源、来源、正式命令、门控与验收证据。
- `画图/画图代码/stage1/main_sixpanel_20260929/`：既有六图的科学统计和可编辑 PPT 装配代码。
- `补充材料.md`、`supplementary.md`：只增加新比较，保留已有实例完成度分析。
- `temp/ligandseek1_held_out_20261011/official_v1.0.0/README.md`：官方模型、阈值、输入和输出契约。
