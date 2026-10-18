# LigandSeek2 GT 全候选管线实验日志

本记录执行[统一管线计划](../../test_and_pipeline.md)，由[总日志](总日志.md)汇总三个条件。当前结果、产物和命令在前；之前尝试与原来源在后。

## 当前结果与产物

| 项目 | 最终记录 |
|---|---|
| 状态 | 推理、CPU评价与完整视图汇总完成；403776保留after_lock并返回try_lock |
| 全候选与成员 | 完整Find／Match范围179 PDB；Stage3视图77 PDB、446实例；本域304个合格blob |
| Build产物 | `/storage/penghongen/Adaligand_E2E/test/test_0/build/PocketXMol-tuned/GT/` |
| 评价产物 | `/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/GT/`中的docking_results.jsonl、evaluation.json、completion.json、summary.json |
| 配置 | `/storage/penghongen/Adaligand_E2E/test/test_0/configs/GT.yml` |
| 采样预算 | 每blob 50候选、100步；PocketXMol FP32、batch50、RA＋T0 |
| 最终源码 | `AdaLigand_0e2ed5a4829f`，内容SHA256 `0e2ed5a4829f6a4312dbf49c0d59536f4da364cbd8d203cb0422a6a254dffd9a` |
| 最终launch | `/home/penghongen/Feedback/AdaLigand/launches/403776/submit_task_job403776_20261016T043310_a4` |
| 模型 | 冻结`PocketXMol_f4d72bbea387`，best `/storage/penghongen/PocketXMol/training/local_cov-C-T0-RA-b72/checkpoints/step=24800.ckpt` |
| 训练W&B | [db4b74gn](https://wandb.ai/pencounkdual-111/PocketXmol_density/runs/db4b74gn)；本轮不新增训练 |
| 本轮计算 | 复用280项，补齐24项；304项均有数值RMSD |

## 逐blob姿态结果

成功率分母为全部合格blob，RMSD分布只对有数值的姿态统计；严格小于阈值，不做刚体对齐。

| 姿态 | 数值样本数 | 平均/中位RMSD(Å) | 严格<2 Å | 严格<3 Å |
|---|---:|---:|---:|---:|
| Top-1 | 304 | 2.350 / 1.039 | 241/304 (79.28%) | 254/304 (83.55%) |
| Top-5最低 | 304 | 1.711 / 0.802 | 261/304 (85.86%) | 271/304 (89.14%) |
| best-of-50 | 304 | 1.259 / 0.666 | 272/304 (89.47%) | 277/304 (91.12%) |

## 假定身份正确的实例完成度

均值为PDB等权宏平均；中位数在同一组77个PDB上计算。背景计费，真实范围外前景免费；未检出与失败实例保留在446个实例的分母中。

| 姿态与阈值 | 100%预算均值/中位数(%) | 300%预算均值/中位数(%) | 全候选成功实例数 |
|---|---:|---:|---:|
| pose@1，RMSD<2 Å | 58.21 / 75.00 | 58.21 / 75.00 | 241 |
| pose@1，RMSD<3 Å | 63.22 / 100.00 | 64.20 / 100.00 | 254 |
| pose@50，RMSD<2 Å | 67.99 / 100.00 | 68.97 / 100.00 | 272 |
| pose@50，RMSD<3 Å | 70.49 / 100.00 | 71.46 / 100.00 | 277 |

## 正式运行命令

```bash
bash 测评数据代码/端到端测评/sh/run.sh GT
```

作业403776的评价进程数为4，OpenMP／MKL／OpenBLAS内部线程均为1。完整入口先读取各阶段完成文件；第二次执行未重新加载Build模型或重复GPU推理。

## 测试、验收与只读核查

来源复制、非测试GPU接线与物理显存验收见共享总日志。最终统计经独立数据核对。
实际Match的四个小分子面板与既有`E2E_completion_20261011/completion.json`在curve、distributions、success_events和all_candidates_final上完全一致。

## 之前的尝试与原来源

旧280项来自`/storage/penghongen/PocketXMol/final_evaluation/end_to_end/GT/local_cov/test/local-c1/`，完整复制且科学文件逐字节一致；原目录保留。

首次正式执行使用`AdaLigand_e0de9de04a09`，launch为`submit_task_job403776_20261016T040323_a3`。GPU缺口均成功；CPU汇总因配置指向不含type_tag的全测试语言清单而停止。仅将类别来源改回原测评使用的180项/77-PDB身份清单，不改类别或计费算法，随后从全部缓存重新汇总。所有原文件与锁资源保留。
