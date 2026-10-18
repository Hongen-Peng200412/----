# Emap2lig Find–Build管线实验日志

本记录执行[统一管线计划](../../test_and_pipeline.md)，由[总日志](总日志.md)汇总三个条件。当前结果、产物和命令在前；之前尝试与原来源在后。

## 当前结果与产物

| 项目 | 最终记录 |
|---|---|
| 状态 | 推理、CPU评价与完整视图汇总完成；403774保留after_lock并返回try_lock |
| 全候选与成员 | 完整Find范围179 PDB（本方法无Match模块）；Stage3视图77 PDB、446实例；本域243个合格blob |
| Build产物 | `/storage/penghongen/Adaligand_E2E/test/test_0/build/Emap2lig/` |
| 评价产物 | `/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/Emap2lig/`中的docking_results.jsonl、evaluation.json、completion.json、summary.json |
| 配置 | `/storage/penghongen/Adaligand_E2E/test/test_0/configs/Emap2lig.yml` |
| 采样预算 | 原生blob、精确SMILES、50姿态、100步、原consistency_iou排名与[5,25]筛选 |
| 最终源码 | `AdaLigand_0e2ed5a4829f`，内容SHA256 `0e2ed5a4829f6a4312dbf49c0d59536f4da364cbd8d203cb0422a6a254dffd9a` |
| 最终launch | `/home/penghongen/Feedback/AdaLigand/launches/403774/submit_task_job403774_20261016T042314_a4` |
| 本轮计算 | 全部读取243项原结果；237项有姿态、6项原输入筛选失败，分母仍243 |

## 逐blob姿态结果

成功率分母为全部合格blob，RMSD分布只对有数值的姿态统计；严格小于阈值，不做刚体对齐。

| 姿态 | 数值样本数 | 平均/中位RMSD(Å) | 严格<2 Å | 严格<3 Å |
|---|---:|---:|---:|---:|
| Top-1 | 237 | 2.488 / 1.854 | 134/243 (55.14%) | 200/243 (82.30%) |
| Top-5最低 | 237 | 2.028 / 1.529 | 166/243 (68.31%) | 211/243 (86.83%) |
| best-of-50 | 237 | 1.631 / 1.331 | 194/243 (79.84%) | 219/243 (90.12%) |

## 假定身份正确的实例完成度

均值为PDB等权宏平均；中位数在同一组77个PDB上计算。背景计费，真实范围外前景免费；未检出与失败实例保留在446个实例的分母中。

| 姿态与阈值 | 100%预算均值/中位数(%) | 300%预算均值/中位数(%) | 全候选成功实例数 |
|---|---:|---:|---:|
| pose@1，RMSD<2 Å | 23.81 / 0.00 | 26.05 / 0.00 | 134 |
| pose@1，RMSD<3 Å | 38.24 / 0.00 | 43.28 / 16.67 | 200 |
| pose@50，RMSD<2 Å | 34.16 / 0.00 | 40.48 / 22.22 | 194 |
| pose@50，RMSD<3 Å | 42.52 / 22.22 | 49.97 / 50.00 | 219 |

## 正式运行命令

```bash
bash 测评数据代码/端到端测评/sh/run.sh Emap2lig
```

作业403774的评价进程数为16，OpenMP／MKL／OpenBLAS内部线程均为1。完整入口先读取各阶段完成文件；本轮执行全部读取已有Build结果，没有加载模型或重复GPU推理。

## 测试、验收与只读核查

来源复制、非测试GPU接线与物理显存验收见共享总日志。最终统计经独立数据核对。

## 之前的尝试与原来源

原结果来自`/storage/penghongen/Emap2lig/stage3_find_hit_build/`，243个配对、逐姿态RMSD、consistency_iou与排名均保持，所有已复制CIF路径已核对。原目录与历史日志保留。

六个原Build输入筛选失败为`9llg/3`、`9lw1/2`、`9o8p/0`、`9q05/4`、`9ui6/5`、`9uwi/3`。本轮没有重新处理或赋予替代RMSD；仍纳入243项直接对接及446实例完成度的分母。
