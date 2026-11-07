# EMERALD-ID 已知位点的身份准确率

本项对应补充材料“EMERALD-ID identity matching at deposited ligand sites”中的独立文字数字。固定查询集合是 **84 个 PDB 的 357 个沉积小分子位点**，两种受体使用相同位点和候选身份。

| 受体条件 | 有至少一个有效候选评分的位点 | 精确身份正确位点 | 有效评分位点中的准确率 |
| --- | ---: | ---: | ---: |
| 沉积受体（GT） | 282 | 233 | 233/282 = 82.6241%，显示为 82.6% |
| CryoAtom2 重建受体（CA2） | 313 | 263 | 263/313 = 84.0256%，显示为 84.0% |

这些分母按“至少一个候选得到有效评分”限定，属于有有效输出条件下的逐位点准确率。固定实验范围始终是每种受体 357 个位点；若将无有效输出也计入固定分母，分别为 233/357 = 65.2661% 和 263/357 = 73.6695%。失败位点没有从原查询清单删除。

## 原文件与连接方式

以下文件都位于已经核对的服务器根 `/storage/penghongen/Matcher/evaluation/test_EMERALD-ID/`：

```text
manifest/
├─ manifest.json                       # 输入来源、截尾百分比及各任务范围
└─ nxu/
   ├─ pdbs.jsonl                       # 保留的84个PDB与各自完整小分子候选身份
   ├─ queries.jsonl                    # 357个沉积真实查询位点及评估答案
   └─ excluded_pdbs.jsonl              # 按成本排除的10个完整PDB
EMERALD-ID/nxu/<pdb>/<occurrence>/
└─ result.json                         # GT条件下该位点的官方身份预测和失败状态
CryoAtom2/EMERALD-ID/nxu/<pdb>/<occurrence>/
└─ result.json                         # CA2条件下相同位点的独立原结果
```

查询键为 `queries.jsonl` 中的 `pdb_id + occurrence_id`，两者共同定位一个沉积真实配体实例。例如 `10tu + 0` 是一个真实查询位点；`occurrence_id` 不表示预测 blob 的行号或编号。`target_smiles` 是该实例用于评价的原精确 SMILES 字符串。`center_xyz_angstrom` 为三元素数组，给出沉积 present 原子的世界 XYZ 质心，单位 Å；它确定已知位点的查询位置。

`pdbs.jsonl` 的一行对应一个保留 PDB。`identity_smiles` 是该 PDB 内全部小分子身份的精确字符串去重、排序列表，长度就是候选身份数 K；`occurrence_count` 是小分子查询点数 N_g，`docking_count=N_g×K`。例如 `10tu` 有 2 个查询点、1 个身份，原 `docking_count=2`。身份在同一 PDB 内去重，相同身份在不同 PDB 分别计数。

## 最高10%成本怎样截去

`manifest.json` 指定源 `/storage/penghongen/Matcher/manifests/test0_real_smiles_v1/manifest.json`、原始输入 `/storage/penghongen/AdaLigand/Ori_Data` 和 `trim_percent=10.0`。本项选择小分子任务 `nxu`：从有小分子查询点的 94 个 PDB 开始，按 `docking_count` 降序排序；成本相同按小写 `pdb_id` 升序排列。

排除数取 **ceil(94×10/100)=10 个完整 PDB**，不是取整到 9 个，也不是删去最高成本的若干查询点。原排除清单为 `9hyu`、`9z6w`、`9zkm`、`11jb`、`9w0x`、`9eeq`、`9ub7`、`9nvn`、`9ryn`、`9lw1`。保留的 `pdbs.jsonl` 与排除清单合起来是 94 个 PDB、821 个小分子实例；保留部分为 84 个 PDB、357 个实例和 114 个按 PDB 计数的候选身份槽。

截尾在化学准备和对接评分之前完成。后续某身份准备失败或某位点无有效评分，都不会重新挑选 PDB、缩小原候选身份清单或改变该位点的 N_g、K。另一个大小写不同的任务 `NxU` 使用全类别身份和查询点，其 161-PDB/995点范围单独保存；本项数字只读取小写 `nxu`。

## 逐位点结果怎样计数

每份 `result.json` 保存 `pdb_id`、`occurrence_id`、`status`、`predicted_smiles`、`scored_smiles`、`failed_smiles` 和 `rosetta_exit_code`。其中：

- `status="scored"`：本位点至少一个身份得到有效评分，`predicted_smiles` 非空，并等于原 `scored_smiles` 官方排名中的第一项；此位点进入上述 282／313 分母。
- `status="no_prepared_identity"`：原候选身份均无法完成化学准备，预测为 null、成功评分列表为空。例如 `10tu/0` 原记录报告 MOL2 回读未产生 SMILES，`rosetta_exit_code=null`。
- `status="no_valid_score"`：没有可用于原官方排名的有效评分，预测为 null、成功评分列表为空。退出码为零本身不构成有效身份输出。

| 原状态 | GT位点数 | CA2位点数 |
| --- | ---: | ---: |
| scored | 282 | 313 |
| no_prepared_identity | 42 | 42 |
| no_valid_score | 33 | 2 |
| 合计 | 357 | 357 |

正确数通过同一个查询键，将 `predicted_smiles` 与原 `queries.jsonl::target_smiles` **逐字符串精确比较**得到。统计不另做化学等价合并，不按真实 RMSD 挑选身份，也不把未评分的候选身份伪造成一次错误排名。有至少一个有效身份即可进入本项有效输出分母；其中只有 GT 190 个、CA2 222 个位点的全部原候选均成功评分。全部候选成功评分子集的范围与本项分母不同。

逐点选择沿原官方 `rank_ligand_identity.py` 的排名。每个成功查询目录保留 `identity_map.json` 的短名称到精确 SMILES 映射，以及 `official_rank.txt` 和原评分文件；当前核算读取原 `result.json`，不按裸 zscore 另行重排或再次运行 Rosetta。

## 生产说明和核算范围

已核对可读的冻结生产说明与对应实现：

- `/home/penghongen/Feedback/Matcher/releases/Matcher_491e58a92021/Matcher/test_真实场景(Structure)/known_site/README.md`，同目录 `build_manifest.py` 明确 `ceil`、成本降序和并列 PDB 升序的截尾实现。
- `/home/penghongen/Feedback/Matcher/releases/Matcher_efecbf567afe/Matcher/test_真实场景(Structure)/known_site/README.md`，同目录 `run_emerald_query.py` 明确查询输入、准备失败、有效评分及官方排名的解释。
- 本地阅读入口为 `C:/Users/15919/Desktop/Matcher/test_真实场景(Structure)/known_site/README.md`。

### 实际启动、参数与补跑记录

以下是服务器现存的实际启动记录目录。每个目录内的 `run_cmd.sh` 保存该次实际调用；`launch.json` 保存 `release_project_root`（代码快照绝对位置）、`created_at`、`slurm_job_id`、`array_spec` 及资源配置。调用的 shell 入口位于所绑定 release 内，完整参数可以沿它直接读取。

| 实际步骤 | 启动记录的完整目录 | 绑定的 Matcher release |
| --- | --- | --- |
| 原查询清单构建 | `/home/penghongen/Feedback/Matcher/launches/388464/build_manifest_job388464_20260925T214201_a1/` | `42d32da3a160` |
| GT 小分子查询 | `/home/penghongen/Feedback/Matcher/launches/388458/run_emerald_job388458_20260926T095228_a3/` | `491e58a92021` |
| CA2 小分子查询 | `/home/penghongen/Feedback/Matcher/launches/390207/run_emerald_all_job390207_20260928T232032_a4/` | `6e7096a3a92c` |
| CA2 链名兼容补跑 | `/home/penghongen/Feedback/Matcher/launches/390383/gate_cryo_density106_nxu_job390383_20260929T040637_a6/` | `efecbf567afe` |
| CA2 最后一个链名案例补跑 | `/home/penghongen/Feedback/Matcher/launches/390216/run_emerald_all_job390216_20260929T055125_a3/` | `83d392d0ed9a` |
| GT 原结果汇总 | `/home/penghongen/Feedback/Matcher/launches/388458/run_emerald_job388458_20260928T180709_a4/` | `09b9eb624d78` |
| CA2 原结果汇总 | `/home/penghongen/Feedback/Matcher/launches/390207/run_emerald_all_job390207_20260929T103801_a5/` | `2351adf02d9c` |

清单实际入口是绑定 release 的 `训练与运行/sh/known_site/build_manifest.sh`，明确传入原 `test0_real_smiles_v1/manifest.json`、原 `Ori_Data`、本根 `manifest/` 和 `--trim-percent 10`。GT 的上述 `run_cmd.sh` 直接执行 `run_emerald_shard.py`；CA2 的上述 `run_cmd.sh` 执行绑定 release 内的 `训练与运行/sh/known_site/run_emerald_cryo_small.sh`。两者使用 `/home/penghongen/anaconda3/envs/pxm_phase1/bin/python`、`--task-name nxu`、相同的原查询清单和 `--shard-count 12 --workers 8`；GT 输出本根 `EMERALD-ID/`，CA2 额外传入 `--receptor-root /storage/penghongen/Adaligand_infered_receptor_data/cryoatom2/test_0_chain06/Ori_Data`，输出本根 `CryoAtom2/EMERALD-ID/`。原参数及对应 release 的 shell 文件均已实际读取，不将当前 README 的示例命令当作运行记录。

两次链名补跑的实际 `run_cmd.sh` 分别执行 `retry_cryo_chain_names.sh`、`retry_cryo_chain_names_last.sh`。其查询清单分别为 `/storage/penghongen/Matcher/evaluation/test_EMERALD-ID/CryoAtom2/retry_chain_names_manifest/nxu/queries.jsonl`（3 PDB、21点）和 `/storage/penghongen/Matcher/evaluation/test_EMERALD-ID/CryoAtom2/retry_chain_names_last_manifest/nxu/queries.jsonl`（1 PDB、1点）。两清单逐项都是原357点的完全相同记录，结果仍写回该 CA2 实验的既定输出根，最终统计继续以原357点为固定范围。

有些启动目录及 `launch.json::task_script` 沿用旧任务名。例如目录名含 `run_emerald_all` 的 CA2 原运行，其实际 `run_cmd.sh` 已明确执行 `run_emerald_cryo_small.sh`；链名补跑也使用了名称含 `gate_cryo_density106` 的启动目录。应连读 `run_cmd.sh` 与其绑定 release 的入口确定实际动作。

全部714份 `result.json` 仅保存上述七个结果字段，没有逐点的 launch编号、release 或完整 argv。现有启动记录能定位原构建、原查询、补跑和汇总的命令与代码快照；单份结果不提供逐点到某次初跑或补跑的独立版本映射。因此，这批最终原结果不能统一标成由某一个 release 一次性产生。

本项已读取两受体全部 714 份原查询结果，与原查询清单逐键连接；保留范围、截尾规则、原精确身份及上述计数均已核对。原 `summary/nxu/all_retained/summary.json` 与 `CryoAtom2/summary/nxu/all_retained/summary.json` 只作交叉检查。正文说明由本页维护，不增加长期 claim 程序或统计 JSON。运行时间的独立起止边界见 [运行时间.md](运行时间.md)，实验总入口见 [EMERALD-ID 来源说明](../source/EMERALD-ID.md)。
