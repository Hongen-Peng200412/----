# Emap2lig-Build 实验日志

状态：2026-09-29 已完成 Emap2lig-Build 在 243 个 Find 命中小分子实例上的正式推理和 CPU 姿态评价。237 个实例生成并评价 50 个姿态，六个原 Build 输入筛选失败保留于分母；H200 JobId `390405` 在 `hnode03` 成功结束本轮命令，保留 `after_lock` 并返回 `try_lock`。冻结 Find 来源是 `/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0/` 的 `evaluation/per_pdb/*.npz` 和 `raw_find_outputs/<pdb>/find_blobs/blob_*.npz`；精确化学输入来自 `/storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl`。Build 官方权重是 Hugging Face `KiharaLab/Emap2lig` 的 `emap2lig-build-v0.0.1.safetensors`，官方响应声明 115,242,996 字节、SHA-256 `e9af59c83fe5d5d5b63c4c6edb6cf2002d8e576b9c96490ab08d2fa14dcf968b`。服务器直连 Hugging Face 失败，第一次门控已从 `hf-mirror.com` 下载同一仓库文件，在移入 `/home/penghongen/.emap2lig/models/` 前后均通过该哈希校验；正式运行再次复核通过。

本轮输入构造验收确认 446 条冻结实例中有 243 条 Find 命中；Top-1 为 39/446，Top-5 为 128/446，best 为 243/446。原 Build 比例筛选未通过且保持在分母内的六条为 `9llg/3`、`9lw1/2`、`9o8p/0`、`9q05/4`、`9ui6/5`、`9uwi/3`。其它输入或采样失败也保留分母；不改变 Build 过滤规则。有效实例使用精确 `prepared_smiles`，50 姿态、100 步，`consistency_iou` 排序。真实坐标包 `SMILE_coords/v1` 仅供评价。

## 当前产物与结果

结果根目录 `/storage/penghongen/Emap2lig/stage3_find_hit_build/`；`find_hit_subset.jsonl` 和 `find_hit_summary.json` 记录 Find→Build 输入；`build/<pdb>/<occurrence>/<launch_id>/` 保存原始 CIF、评分 CSV 和掩码；`build_status.jsonl` 记录 243 个构造与推理状态及产物目录；`build_occurrences.jsonl` 记录 243 个实例的逐姿态 RMSD；`build_summary.json` 保存共同分母下的指标。六个小文件的本地副本位于 `测试Find出来的Build/结果与日志/正式产物/`，完整姿态文件留在服务器。此次测试不使用 W&B；任务身份由 JobId、release、launch、冻结状态与文件路径共同确定。

| Find 命中子集 | 分母 | Top-1 <2 Å | Top-1 <3 Å | Top-5 <2 Å | Top-5 <3 Å | best <2 Å | best <3 Å |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Build `consistency_iou` 排序 | 243 | 134 (55.1%) | 200 (82.3%) | 166 (68.3%) | 211 (86.8%) | 194 (79.8%) | 219 (90.1%) |

Top-1 是原 `consistency_iou` 最高姿态；Top-5 是该排序前五姿态至少一个达阈值；best 是全部 50 姿态的最低 RMSD 事后上界。两种阈值均为严格小于；真实坐标仅供完成采样后的评价，未用于姿态排序。最终 243 条状态为 `complete=237`、`build_filter_failed=6`，无其它输入、采样、评分或评价失败。逐实例复核确认 237 条成功记录各有 50 个按原评分降序的姿态，六条失败记录均无姿态且 RMSD 为 `null`；九项对比的实例键和顺序完全一致。

正式结果的小文件副本及逐文件 SHA-256 见 [`正式产物/README.md`](正式产物/README.md) 和 [`正式产物/SHA256SUMS`](正式产物/SHA256SUMS)；六个副本均与服务器同名文件一致。独立结果复核重新计算了 237 条成功记录的 Top-1、Top-5、best 与两种阈值计数，并核对 243 条输入、状态及顺序，以及八条 PocketXMol 汇总；均与正式汇总相符。此复核读取冻结评价记录，不替代服务器上原始 CIF 与评分 CSV 的逐项生成检查。

## 正式运行命令

```bash
bash 训练与运行/sh/stage3_build.sh
```

此行已通过同一 JobId 的动态 `run_cmd_390405.sh` 执行并返回成功。正式 release 为 `/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_d1e46744d92e/Emap2lig`，launch 为 `/home/penghongen/Feedback/Emap2lig/launches/390405/build_gate_job390405_20260929T020535_a3`，控制目录为 `/home/penghongen/Feedback/Emap2lig/allocations/390405/`。launch 名称沿用原作业任务名 `build_gate`，但冻结的 `run_cmd.sh` 明确执行正式 `stage3_build.sh`；首个正式姿态位于结果根目录 `build/11jb/0/build_gate_job390405_20260929T020535_a3/`。同一作业内的 24 核 CPU 评价读取这些冻结姿态，没有重复 Find 或 Build 推理。

## 测试、门控与只读核查

非测试 GPU 门控采用仓库教程 `examples/tutorial_output/find_blobs/blob_1.npz`。已执行的门控资源提交命令：

```bash
bash 训练与运行/submit_task.sh --sh build_gate.sh --resource h200 --gpus 1 --cpus 24 --pre_hold --after_hold
```

CPU 输入构造预核查首次发现 Find 逐 PDB 评价包含不在 446 条 Stage3 清单中的实例；筛选现已限定为冻结 `(pdb_id, occurrence_id)`。2026-09-29 使用仓库教程 blob 与 `CCCCCCCCCCCC` 完成非测试 CPU 门控：12 个重原子、一条有效配对、`prompt_points=(50,3)`，原 Build 体素／重原子比值 20.25。第二次 GPU 门控使用 release `Emap2lig_848972f93304`、launch `build_gate_job390405_20260929T015537_a2`，完成 50 个各 100 步的姿态，50 个 CIF 与原始评分一一对应，峰值 GPU 显存 32,274,936,832 字节（约 30.1 GiB），输出仅在 `/storage/penghongen/tmp/emap2lig_build_gate/`。此处的门控不能代替正式 243 条结果。

## 之前的尝试与异常

2026-09-29 第一次教程 blob GPU 门控使用 release `Emap2lig_39b82b183901`、launch `build_gate_job390405_20260929T015111_a1`。权重哈希通过，Dataset 生成有效输入；官方模型的 torch.compile 调用 Triton 时选择 `/usr/bin/gcc`，该 GCC 4.8.5 缺少 `stdatomic.h`，导致 `predict_step` 返回 `None`、姿态数为 0，门控退出码 1。这不是正式 243 条测试尝试。随后在门控及正式脚本中指定 conda GCC 11.4.0，第二次门控验证了修复；旧 release、launch、日志和教程产物均保留。
