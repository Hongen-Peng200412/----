# PocketXMol 既有结果的 243 条同子集汇总

状态：八条既有结果已在 Find 命中的 243 条共同子集上完成只读汇总。四个协议是 official-C0、official-E、local_cov-C0、local_cov-E；每个协议分别使用 GT 与 CryoAtom2（CA2）受体，共八条结果。只读取现有测试评价，不重跑 PocketXMol，也不读取 C5 指标。

GT 来源：`/storage/penghongen/PocketXMol/sampling/official-SMILES/test/{C0,E}/occurrences.json`、`/storage/penghongen/PocketXMol/sampling/local_cov-{C,E}-T0-RA/test/{C0,E}/occurrences.json`。CA2 来源：`/storage/penghongen/PocketXMol/final_evaluation/standard/ca2/{official,local_cov-C,local_cov-E}/test/{C0,E}/occurrences.json`，实际八条完整路径写在独立汇总脚本中。共同键是 `(pdb_id, occurrence_id)`；筛选只依赖冻结 Find 命中清单。

## 当前产物与结果

汇总输出为 `/storage/penghongen/Emap2lig/stage3_find_hit_build/pocket_comparison.json`，本地副本为 `测试Find出来的Build/结果与日志/正式产物/pocket_comparison.json`。每个模型记录保留源文件、243 个逐实例 RMSD 和严格 `<2 Å`、`<3 Å` 的 Top-1／Top-5／best 计数。所有单元都是成功数／243（成功率）；best 是原测试 50 候选的事后最低 RMSD。该文件与 Build 逐实例结果采用完全相同的 `(pdb_id, occurrence_id)` 键和顺序，原八份 PocketXMol 测试文件未修改。

| 模型及条件 | 受体 | Top-1 <2 Å | Top-1 <3 Å | Top-5 <2 Å | Top-5 <3 Å | best <2 Å | best <3 Å |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Official C0 | GT | 155/243 (63.8%) | 186/243 (76.5%) | 174/243 (71.6%) | 209/243 (86.0%) | 196/243 (80.7%) | 223/243 (91.8%) |
| Official E | GT | 185/243 (76.1%) | 213/243 (87.7%) | 205/243 (84.4%) | 228/243 (93.8%) | 222/243 (91.4%) | 236/243 (97.1%) |
| local_cov C0 | GT | 209/243 (86.0%) | 221/243 (90.9%) | 226/243 (93.0%) | 235/243 (96.7%) | 235/243 (96.7%) | 240/243 (98.8%) |
| local_cov E | GT | 208/243 (85.6%) | 223/243 (91.8%) | 224/243 (92.2%) | 233/243 (95.9%) | 240/243 (98.8%) | 243/243 (100.0%) |
| Official C0 | CA2 | 156/243 (64.2%) | 181/243 (74.5%) | 166/243 (68.3%) | 199/243 (81.9%) | 192/243 (79.0%) | 215/243 (88.5%) |
| Official E | CA2 | 185/243 (76.1%) | 211/243 (86.8%) | 204/243 (84.0%) | 227/243 (93.4%) | 219/243 (90.1%) | 234/243 (96.3%) |
| local_cov C0 | CA2 | 203/243 (83.5%) | 222/243 (91.4%) | 224/243 (92.2%) | 234/243 (96.3%) | 231/243 (95.1%) | 238/243 (97.9%) |
| local_cov E | CA2 | 208/243 (85.6%) | 221/243 (90.9%) | 221/243 (90.9%) | 233/243 (95.9%) | 235/243 (96.7%) | 241/243 (99.2%) |

## 正式运行命令

此汇总由本轮规范入口 `训练与运行/sh/stage3_build.sh` 在 Build 评价之后调用；独立程序为 `测试Find出来的Build/PocketXmol的同等子集汇总/summarize_existing.py`。它不发起 GPU 推理。

## 测试、门控与只读核查

执行前只读核对过八条 `occurrences.json` 每份都包含冻结清单的 446 个实例；9qkz/0 等原有失败记录仍按原状态保留，同子集指标不强行填零坐标。

## 之前的尝试与异常

暂无本轮汇总尝试。
