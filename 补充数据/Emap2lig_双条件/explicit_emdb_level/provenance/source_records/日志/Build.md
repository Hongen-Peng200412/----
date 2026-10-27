# Emap2lig显式level：Build实验日志

当前状态：**2026-10-27 正式 Find、Build、RMSD 评价及产物完整性验收全部完成**。旧无level结果未写入，本轮未修改论文正文或原图。Job423330仍保留after_lock和try_lock，没有释放资源。

依据作者已批准的论文仓库 `talk/emap2lig_level_20261026/方案.md`，本轮优先交付独立显式level运行及元数据。科学与字段契约见[实验说明](../README.md)，本日志是执行事实，不要求把私下完整筛选数字写进论文。

本日志从属于[总日志](总日志.md)。

## 产物、来源与状态

服务器独立根：`/storage/penghongen/Emap2lig/contour_level_20261026/`。原生密度、概率、掩码、blob、全部CIF与官方评分仍在该根；本地 `显式level实验/结果/` 保存输入、179份EMDB元数据、Find评价与稀疏候选、Build请求、251份化学输入、251份原评分CSV、逐姿态RMSD及运行证据，共 **1428文件／21,380,471字节**。本地逐文件身份见 `证据/metadata_inventory.json`。

旧无level Find根为 `/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0/`；旧Build根为 `/storage/penghongen/Emap2lig/stage3_find_hit_build/`。原统一比较 `/storage/penghongen/Adaligand_E2E/test/test_0/` 未写入。新旧条件以完整路径与 `normalization_mode=explicit_emdb_level` 区分，不能只按同名指标文件判断来源。

## Build输入与最终状态

原完整清单77 PDB／446实例，SHA-256 `b78a8c07b08a7c0ce9b7b519044804ea8cf0c3e5a864bfbfbfa6f329031a1ee6`。新Find在59个PDB命中260例；Find排名Top-1／Top-5／全部候选分别覆盖42／141／260例，尚未涉及姿态RMSD。原比例筛选后251例ready、9例失败；186例Find未命中。

251例全部一次联合采样50姿态、每姿态100步，使用原权重和已批准的旧attention行为，种子公式沿用旧实跑。原consistency_iou先排序，真值坐标仅用于未对齐RMSD。所有251例均完整评价，0恒等映射处理、0技术失败。原无level243／237保留原根，不复用旧CIF；论文仅需报告最终采用的关键数字。

## 姿态评价

姿态先按原consistency_iou降序排列，再计算原子对称映射下、不做刚体对齐的RMSD。以下均为严格小于阈值的实例数；完整端到端分母为446，条件分析分母另保留260，不删除筛选失败。

| 预算 | <2 Å | <3 Å |
| --- | ---: | ---: |
| Top-1 | 156 | 202 |
| Top-5 | 184 | 219 |
| best-of-50 | 207 | 230 |

原始汇总 `结果/build/build_summary.json`，全部命中实例 `build_occurrences.jsonl`，完整446实例 `build_all_occurrences.jsonl`。所有251个完成实例的50个姿态RMSD均有限；没有采样、评分、运行或评价失败。

## 正式运行命令与身份

```bash
bash 训练与运行/sh/with_level.sh
```

正式launch：`build_gate_job423330_20261026T202139_a2`；源码提交：`37b0d9e7ad2a1b18fa096d91f154619085cee907`；release：`/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig`。Job423330，gnode10，A80080GB、24CPU。历史任务名仍为build_gate，正式身份由 `runtime/formal/run_cmd.sh` 指定，不按前缀推断。没有W&B。

控制器计算节点时间：2026-10-26 20:21:39开始，2026-10-27 00:12:55全链退出0；主节点最终验收时间2026-10-27 00:19:34。节点时钟有差异，不把它们混算耗时。正式前放行主节点时间为2026-10-26 20:23:56。单进程Find／Build的OMP/MKL使用24线程，24个CPU评价进程内部各为1，OpenBLAS为1。

原控制台在 `/home/penghongen/Feedback/Emap2lig/allocations/423330/{out,err}`；本地压缩副本 `结果/inputs/runtime/allocation_{out,err}.gz` 包含a1门控与a2正式的原始分界，门控和正式命令另分别存于 `runtime/gate/` 与 `runtime/formal/`。完整模型配置、包清单、release与launch元数据均已冻结。

## 验收与旧结果保护

`结果/inputs/final_audit.json.passed=true`。逐份核对71份冻结源码／配置、179份正式输入和EMDB副本、原测试字节身份；179份评价交集与原生blob编号完全连接，真实实例总数2,502。逐例核对251份化学输入、12,550个CIF及同名有限原评分、全部逐姿态RMSD、原评分排序、Top-1／Top-5／best汇总与完整446顺序。

原Find指标、Build请求、Find命中汇总、Build汇总这4份关键旧文件的内容SHA-256、字节数和mtime_ns均与运行前完全一致；两份官方权重身份也未改变。其余旧产物没有写入路径。保护基线为 `证据/preflight.json`，具体最终记录见上述audit。

## 独立测试与门控

独立命令：`bash 训练与运行/sh/with_level_gate.sh`；门控launch `build_gate_job423330_20261026T201648_a1`，与正式使用同一release，退出0。输出只写 `/storage/penghongen/tmp/emap2lig_with_level_gate/<launch>/`，不计入正式分母。

- 旧243条命中请求逐字段一致，237条ready一致；构造的整体平移1 Å样例得到未对齐RMSD=1 Å。
- 非空Find评价各NPZ字段与固定原适配器一致；空候选保留4个真实实例及同一真实概率的PRAUC计数。
- 教程原L=0.025，实际阈值0.0125；模拟零掩码仍保存真实非零概率。
- 教程Build完整50 CIF与50原评分、100步，峰值GPU分配32,250,426,368 B。

只读部署核查、门控与最终audit均不作为正式运行命令。上传仅使用明确payload、固定主机密钥、无删除rsync；未调用含删除远端.git／accept-new的旧上传器。

## 之前的尝试与阶段事件

无正式失败、中断或重新采样；唯一正式尝试为a2。a1是成功的独立门控。Find阶段完成后自动进入Build，没有另建实验日志或换结果根。提交、Find完成、全链完成分别保存handoff，其余检查只刷新三份日志的状态快照，没有heartbeat。

## 计划与实现差异及后续范围

- 有益补齐：有效零候选原本无法保存／评价，现在保留真实概率与完整分母，不改变预测、匹配或指标定义。
- 作者后续变更：CPU从16改为实际分配24；新实现分支也按学习分支的可读要求维护。
- 有害差异：未发现。
- 本轮暂缓：补充材料整套同版式重画。按作者允许，本轮优先完成全量运行、全部元数据、审查与双线收口；未写入论文目录的新运行记录，未修改正文、原图或旧结果。补图可直接消费本轮完整元数据和服务器原件，是否进入论文由作者后续决定。
