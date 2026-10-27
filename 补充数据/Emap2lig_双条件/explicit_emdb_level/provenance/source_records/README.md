# 显式推荐 level 的 Find 与 Build

本目录在独立条件下运行 Emap2lig-Find 和命中 blob 的 Build，完整保留原生输出、空间映射、候选交集、化学身份、姿态评分与逐姿态 RMSD。原无 level 结果不变，本轮不改论文主文。推荐值记为 L，显式交给 `load_config(contour_level=L)`，由官方预处理应用 L/2 截断和原第 98 百分位归一化。

源码从 `16c31729798698feb7671ebeee9a262b82a4f191` 分叉；`main.py` 的局部裁剪及超过 100 个 blob 不退出、两个 attention 文件沿用旧实跑端点 `7a08a1246b6a19cf9be2ed7c882ab1da879c82eb` 的已批准版本。未升级模型或依赖。模型行为、50 姿态／100 步及原评分保持，新增条件是显式推荐 level。实现／学习分支独立维护，既有 `Learn/CUMULATIVE` 不移动。

为使合法零候选也保留在测试分母中，`main.py` 另保存模型已经产生的真实 ligand 概率和空掩码，并将完成推断后的零候选记为成功执行。`evaluate_find.py` 沿用固定评价器的逐图函数，仅删除“必须有 mask_N”前置条件；原函数本来就支持 `(0,G)` 交集及全部未命中。其他映射、聚合和子集派生函数仍直接调用原 release，技术错误仍终止，缺失概率图不会补成零概率图。

## 输入与输出概览

| 输入 | 固定成员与来源 |
| --- | --- |
| Find | `inputs/test_0.json` 的有序 179 个 PDB，原始地图位于 `/storage/penghongen/AdaLigand/Ori_Data/raw/emdb_maps/` |
| 推荐 level | `inputs/maps.json`，179 份原 EMDB 元数据的主图推荐值，178 个 AUTHOR、1 个 EMDB 来源 |
| Build 全集 | `/storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl`，77 个 PDB、446 个合格小分子实例 |
| 参考坐标 | `/storage/penghongen/AdaLigand/Ori_Data/smiles_assets/SMILE_coords/v1/<pdb>.npz`，只供评价 |
| Find 评价 | `/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_5570cf8a0b7a/Pocket_Plus` 的原评价实现 |

新科学产物根固定为 `/storage/penghongen/Emap2lig/contour_level_20261026/`。下面结构已由本轮正式运行生成。两棵树中的同名根是同一物理目录，分别列出科学接口与运行状态。

本地 `结果/` 镜像正式输入与 EMDB 元数据、Find 逐图状态、原生候选稀疏元数据、映射几何、评价 NPZ／JSON／JSONL，以及 Build 请求、状态和逐姿态 RMSD。字段沿用下文契约；连续密度、完整概率图、原生 blob 与 CIF 的原文件保留在上述服务器根，元数据中的绝对路径直接指向它们。`证据/` 保存部署 receipt、原结果保护基线与验收状态；两份环境包清单和逐文件源码 receipt 位于 `结果/inputs/`。Build 未完成时下载的是进行中快照，以日志和最终验收状态为准。

```text
## <科学产物>
/storage/penghongen/Emap2lig/contour_level_20261026/
├── inputs/
│   ├── maps.json                         # 实际使用的 179 个原图、推荐值与元数据身份
│   ├── test_0.json                       # 本轮 179-PDB Find 顺序
│   ├── test_1.json                       # 原 149-PDB 保序子集，仅派生评价，不重跑 Find
│   └── test.jsonl                        # 本轮冻结的 446 个 Build 测试身份
├── find/held_out_test_0/
│   ├── raw_find_outputs/<pdb>/
│   │   ├── preprocess/unified.mrc        # 本轮应用 level 后的连续密度、原点与体素尺寸
│   │   ├── find_maps/ligand.mrc          # 原生网格的配体概率
│   │   ├── find_maps/ligand_mask.mrc     # 原 Li 二值配体掩码
│   │   └── find_blobs/{blob_N.npz,mask_N.mrc} # 所有不少于 32 体素的原生连通域
│   ├── mapped/<pdb>/probability_map.npz  # 映射到原真值网格的概率
│   ├── mapped/<pdb>/official_blobs.npz   # 保留原编号的稀疏候选、分数与几何
│   └── evaluation/per_pdb/<pdb>.npz     # 预测与真值交集、匹配和原指标事实
└── build/
    ├── find_hit_subset.jsonl             # 新 Find 命中实例的唯一 Build 请求
    ├── build/<pdb>/<occurrence>/<launch>/
    │   ├── preprocess/ligands/LIG.npz    # 精确 SMILES 生成的官方 LigandObject
    │   └── build_struct/blob_N/
    │       ├── blob_N_LIG_<n>.cif        # 第 n 个生成姿态的世界坐标
    │       └── blob_N_results.csv        # 全部 50 个姿态的原 consistency_iou
    ├── build_occurrences.jsonl           # 全部新 Find 命中实例的逐姿态 RMSD
    └── build_all_occurrences.jsonl       # 全部 446 实例，保留未检出与失败

## <其他文件>
/storage/penghongen/Emap2lig/contour_level_20261026/
├── find/held_out_test_0/raw_find_outputs/<pdb>/status.json # 单 PDB 输入及完成状态（运行诊断）
├── find/held_out_test_0/reports/find_run_summary.json     # 按正式顺序累计的状态（运行统计）
├── find/held_out_test_0/mapped/<pdb>/mapping.json         # 原生与真值网格的几何记录（运行诊断）
├── find/held_out_test_0/evaluation/official_find_li.{metrics.json,jsonl} # 原口径全局与逐 PDB 指标（运行统计）
├── find/held_out_test_1/evaluation/official_find_li.*     # 149-PDB 子集的指标与父来源记录（运行统计）
├── build/find_hit_summary.json                         # 完整 446 实例中的覆盖与输入筛选计数（运行统计）
├── build/build_status.jsonl                            # 每次实例尝试与实际目录（运行诊断）
└── build/build_summary.json                            # 命中分母、完整分母与严格 RMSD 成功数（运行统计）
```

`<pdb>` 从固定 179 个测试标识选择；Build 只涉及原 77 个 PDB。`occurrence` 是该 PDB 的冻结实例编号，不连续也不等于 blob 编号。`N` 从 1 开始按官方保留顺序编号；`n` 为同一请求内 1 至 50 个姿态。模型配置中其余五类预测通道的非空预测也在 `find_maps` 写出对应概率与掩码；Build 的官方写出器还保存预测实例掩码及 best 副本，它们不是参考真值。

## 主要产物

### 输入与身份

#### `inputs/maps.json`

顶层为长度 179 的列表，顺序与 `test_0.json.pdb_ids` 一致，每项对应一个 PDB 的实际原图。

| 字段 | 类型 | 含义与真实形式示例 |
| --- | --- | --- |
| `pdb_id`、`emdb_id` | string | 配对标识，如 `9ter`、`EMD-55834` |
| `input_map` | string | 原始压缩地图的绝对路径，如 `/storage/penghongen/AdaLigand/Ori_Data/raw/emdb_maps/emd_55834.map.gz` |
| `level` | float | 原图尺度的推荐值，如 `0.011` |
| `contour_ratio` | float | 固定 `0.5`；不再额外减半 |
| `effective_threshold` | float | 进入官方归一化的清零阈值，如 `0.0055` |
| `metadata_path` | string | 原 EMDB 主图记录的位置，如 `/storage/penghongen/AdaLigand/Ori_Data/reports/meta/9ter.meta.json` |
| `metadata_sha256` | string | 核查时已冻结的原元数据身份，正式代码只携带，不计算散列 |
| `source` | string | 推荐值来源，如 `AUTHOR`；9w7x 为 `EMDB` |

#### `inputs/test_0.json`、`inputs/test_1.json`

沿用原清单对象，核心字段 `pdb_ids` 为有序小写 PDB 列表，如 `["9ter","30yu"]`。前者 179 项，后者为前者的 149 项保序子集。后者不新增模型前向。

#### `inputs/test.jsonl`

字节复制原 446 实例清单，每行一个小分子实例。核心键为 `pdb_id`、`candidate_id`、`prepared_smiles` 和 `n_heavy_atoms`，如 `{"pdb_id":"9llg","candidate_id":0}` 是键的片段，不代表整行。其余原采样字段完整保留。`candidate_id` 与参考坐标包 `candidate_ids` 相连，不能用 `blob_id` 替代。

### 原生与评价网格

#### `raw_find_outputs/<pdb>/preprocess/unified.mrc`、`find_maps/*.mrc`

每个 MRC 一个三维 ZYX 数组。header 的 origin、voxel size 按 XYZ 排列，长度单位 Å；概率无量纲，掩码为 0/1。`unified.mrc` 已先做官方 1 Å 重采样，再应用原推荐值的一半、归一化和内容裁剪。不同条件的裁剪尺寸和原点可以不同，不能仅按数组下标叠合。

#### `raw_find_outputs/<pdb>/find_blobs/blob_N.npz` 与 `mask_N.mrc`

每个 NPZ 对应一个原生 26 连通域，面积至少 32。`density_grid` 与 `instance_grid` 为同形 `(D_crop,H_crop,W_crop)` ZYX 数组，分别为连续密度和 0/1 掩码；`global_origin` 与 `voxel_size` 为 `(3,)` XYZ，单位 Å；`object_id` 为 N。每轴至少 48 体素。MRC 掩码与 NPZ 的实例掩码和物理网格相同。

#### `mapped/<pdb>/probability_map.npz`、`official_blobs.npz` 与 `mapping.json`

由原 Pocket Plus 评价器生成。概率按世界坐标线性插值，实例按最近体素映射并保留原编号。候选按原生平均概率排序，所有官方保留候选都参与评价，不重新选分数阈值。`probability_map.npz.probability_map` 为真值网格 `(D,H,W)` 概率，`origin_xyz`、`voxel_size_xyz` 为 `(3,)` XYZ、单位 Å。

`official_blobs.npz` 的 `source_blob_index`、`score`、`selected`、`prauc_eligible` 按候选轴 P 对齐；`voxel_offsets` 长度 P+1，将 `voxel_index_global_zyx` 的第一轴切成各预测的稀疏体素，区间为 `[offsets[i],offsets[i+1])`，首值 0、末值为总稀疏体素数。整数坐标最后一轴按 ZYX。原网格形状、原点与体素尺寸一同保留，映射后的不同实例允许重叠。

`mapping.json` 保存源／目标 `shape_zyx`、`voxel_size_xyz`、`origin_xyz` 及映射前后候选数。它记录几何，不重新定义实例匹配。

#### `evaluation/per_pdb/<pdb>.npz`

一个 PDB 一份，核心连接字段为 `intersections` `(P,G)`、`pred_sizes` `(P,)`、`gt_sizes` `(G,)`、`occurrence_id` `(G,)`、`source_blob_index` `(P,)`。G 含所有真实类别，避免先去掉非小分子而改变候选归属。交集和大小的单位是体素数。`semantic_prauc_histogram` 为整数 `(2,1024)` 计数，其余字段完整沿用固定 release 的 `PdbEvaluation`；源码与参数不在本目录重定义。

### Build 请求与构象

#### `build/find_hit_subset.jsonl`

每个命中测试实例一行，先在全部真实类别中将每个 blob 唯一归属，再为该实例取双向覆盖均至少 0.3 且覆盖几何均值最大的 blob；归属并列按 occurrence 编号，实例内并列保留前一 Find 排名。字段为：`pdb_id`、`occurrence_id`、`blob_id`、`find_rank`、`prepared_smiles`、`n_heavy_atoms`、`foreground_voxels`、`voxel_atom_ratio`、`status`、`blob_path`。排名从 1 开始；体素／重原子比值在 `[5,25]` 内为 `ready`，否则为 `build_filter_failed`。

旧 243／237 不作为新实验要求。失败请求仍保留，未检出实例则保留在完整 446 实例文件中。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `pdb_id` | string | 小写 PDB 标识，如 `9llg` |
| `occurrence_id` | int | 原冻结 `candidate_id`，标识真实实例 |
| `blob_id` | int | 被选原生 `blob_N.npz` 的 N |
| `find_rank` | int | 从 1 开始的原生平均概率排名 |
| `prepared_smiles` | string | 冻结精确化学身份，作为 Build 的化学输入 |
| `n_heavy_atoms` | int | 该化学身份的重原子数 |
| `foreground_voxels` | int | 选中原生实例掩码的非零体素数 |
| `voxel_atom_ratio` | float | 前景体素数除以重原子数，无量纲 |
| `status` | string | `ready` 或 `build_filter_failed`；后者仍保留在命中分母 |
| `blob_path` | string | 本条件原生密度与实例掩码 NPZ 的绝对路径 |

下面是完整的构造请求，用于说明格式，不代表实跑结果：

```json
{"pdb_id":"1abc","occurrence_id":0,"blob_id":1,"find_rank":2,"prepared_smiles":"CCO","n_heavy_atoms":3,"foreground_voxels":60,"voxel_atom_ratio":20.0,"status":"ready","blob_path":"/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/raw_find_outputs/1abc/find_blobs/blob_1.npz"}
```

#### `build/<pdb>/<occurrence>/<launch>/`

一个目录是一条请求的一次启动。`preprocess/ligands/LIG.npz` 是官方 SMILES 参考分子，原子名用于连接后续 CIF；它不含沉积参考姿态。`build_struct/blob_N/blob_N_results.csv` 有 50 个姿态的 `conformer_name` 与 `consistency_iou`。评分越高排名越靠前，不能用真值 RMSD 重排 top-1。

原生 CIF 保存世界 XYZ 坐标，单位 Å。50 个姿态由同一次 Dataset 读取与联合采样产生，每个姿态 100 步，保持原种子公式 `20260928 + 100 * sum(ord(char) for char in pdb_id) + occurrence_id`。

#### `build_occurrences.jsonl` 与 `build_all_occurrences.jsonl`

前者每行一个新 Find 命中实例，后者按冻结测试顺序保留全部 446 实例。共同字段为 `pdb_id`、`occurrence_id`、`find_rank`、`status`、`result_dir`、`top1_rmsd_A`、`top5_rmsd_A`、`oracle_rmsd_A`、`poses`；失败可有 `error`。距离单位 Å，失败值为 `null`。未检出为 `status="find_miss"`，排名、结果目录和距离均为 `null`，姿态数组为空。

`poses` 按原 consistency_iou 降序，正常为 50 项；每项包含 `rank`、`consistency_iou`、`cif`、`rmsd_A`、`identity_fallback`，单姿态失败时另有 `error`。下面仅展示一个构造的 `poses[0]` 片段，省略父对象和其他 49 个姿态：

```json
{"rank":1,"consistency_iou":0.72,"cif":"/storage/penghongen/Emap2lig/contour_level_20261026/build/build/1abc/0/example/build_struct/blob_1/blob_1_LIG_1.cif","rmsd_A":1.8,"identity_fallback":false}
```

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `pdb_id`、`occurrence_id` | string、int | 与请求和原冻结清单连接的实例键 |
| `find_rank` | int 或 null | 原 Find 排名；完整文件中的未检出实例为 null |
| `status` | string | `complete`、`find_miss` 或原筛选、采样、评分、运行、评价失败状态 |
| `result_dir` | string 或 null | 该实例本次尝试的产物目录；未检出为 null |
| `top1_rmsd_A` | float 或 null | 原评分第一姿态的未对齐 RMSD，单位 Å |
| `top5_rmsd_A` | float 或 null | 原评分前五个姿态的最低有效 RMSD，单位 Å |
| `oracle_rmsd_A` | float 或 null | 全部 50 个姿态的最低有效 RMSD，单位 Å |
| `poses` | list[object] | 与原评分降序对齐的姿态；未进入评价时为空 |
| `poses[].rank` | int | 从 1 开始的原评分排名 |
| `poses[].consistency_iou` | float | 官方密度一致性评分，无量纲 |
| `poses[].cif` | string | 当前姿态的世界坐标 CIF 绝对路径 |
| `poses[].rmsd_A` | float 或 null | 当前姿态未对齐 RMSD，单位 Å；评价失败为 null |
| `poses[].identity_fallback` | bool | RDKit 的 RuntimeError 是否触发旧恒等映射处理 |
| `poses[].error` | string，可缺省 | 单姿态异常文字；正常时不写该字段 |
| `error` | string、null 或可缺省 | 整个实例的异常文字；失败而无异常文字时可为 null，正常时不写该字段 |

这是完整文件中未检出实例的完整构造示例，命中子集文件不含这类实例：

```json
{"pdb_id":"1abc","occurrence_id":0,"find_rank":null,"status":"find_miss","top1_rmsd_A":null,"top5_rmsd_A":null,"oracle_rmsd_A":null,"poses":[],"result_dir":null}
```

Build 筛选失败的完整构造示例如下；其请求留在命中子集，未生成姿态，目录可以尚不存在：

```json
{"pdb_id":"1abc","occurrence_id":0,"find_rank":2,"status":"build_filter_failed","top1_rmsd_A":null,"top5_rmsd_A":null,"oracle_rmsd_A":null,"poses":[],"result_dir":"/storage/penghongen/Emap2lig/contour_level_20261026/build/build/1abc/0/example"}
```

RMSD 不做刚体对齐，保留原 RDKit `CalcRMS(maxMatches=30000)`；原子映射异常时的恒等映射处理同旧程序，并由 `identity_fallback` 留证。top-1 为原评分第一名，top-5 与 oracle 分别取原评分前五和全部 50 姿态的最低 RMSD。

### 统计与完成状态

#### Find 状态与指标

`status.json` 是单 PDB 输入记录加 `normalization_mode="explicit_emdb_level"`、`output_dir`、`blobs_dir`、`blob_count`、`status_code`、`status`，状态为 `ok` 或 `failed`。有序汇总 `find_run_summary.json` 每完成一项刷新；只有同条件且 `ok` 的 PDB 可续跑复用。

`official_find_li.metrics.json` 和 JSONL 保留原字段，包含逐 PDB 宏平均、实例级 P/R 与 PRAUC、语义指标、覆盖 0.3／0.5／0.6 档及 top-k。文件名沿用原评价器，但其完整路径始终位于本轮独立根。不能从相同文件名推断条件相同。

#### `find_hit_summary.json`

输入汇总记录 `full_occurrences=446`、`find_hit_pdbs`、`find_top1`、`find_top5`、`find_best`、`build_ready`、`build_filter_failed` 和 `subset_path`。`find_best` 是区域命中数，不是 RMSD 成功数。

顶层为 object：`full_occurrences`、`find_hit_pdbs`、`find_top1`、`find_top5`、`find_best`、`build_ready` 均为整数计数；依次表示完整测试实例数、至少有一个命中的 PDB 数、排名不超过 1／5／全部候选的命中实例数、通过 Build 比例筛选的实例数。`build_filter_failed` 是 `list[string]`，每项按 `PDB/occurrence` 标识失败实例；`subset_path` 是请求 JSONL 的绝对路径。

#### `build_status.jsonl`

`build_status.jsonl` 追加每次请求的状态，不因重试删除旧记录。正常含实例键、`generated`、`result_dir`，成功含 `seed`；运行异常含 `error`。筛选、输入、采样、评分和运行失败分别保留。

每行 object：`pdb_id` 为 string、`occurrence_id` 为 int；`status` 为 `complete`、`build_filter_failed`、`build_input_failed`、`sampling_failed`、`scoring_failed` 或 `runtime_failed`。正常返回的 `generated` 为整数 CIF 数，`result_dir` 为本次目录的绝对路径；成功时 `seed` 为整数。捕获的运行异常写 string 类型的 `error`，不补造 `generated` 和 `result_dir`。同一实例最后一行决定后续评价读取哪次尝试。

#### `build_summary.json`

`build_summary.json.denominator` 为全部新 Find 命中数，`full_test_denominator` 为 446，`statuses` 是状态到数量的映射。`top1/top5/best_lt{2,3}A` 是严格低于对应 Å 阈值的成功数，不能把命中子集成功率直接称为 446 实例完成度。

顶层为 object：两个分母均为 int，`statuses` 为 `dict[string,int]`；六个阈值计数字段均为 int。单姿态评价失败保留 null；top-5 和 best 在各自预算内取仍有有效 RMSD 的姿态，全部失败时为 null，实例状态同时保留 `pose_evaluation_failed`。

## 代码组织与入口

按 `paths.py` → `find.py` → `evaluate_find.py` → `prepare_build.py` → `build.py` → `evaluate.py` 阅读。科学计算直接显示官方 Dataset、模型、写出器与原子映射，未增加中间接口层。`tests/` 只用于门控，不进入正式主流程。单进程 Find／Build 的 CPU 算子使用 24 线程，24 个 CPU 评价进程内部各使用 1 线程。

正式命令只有：

```bash
bash 训练与运行/sh/with_level.sh
```

独立测试／门控命令为 `bash 训练与运行/sh/with_level_gate.sh`，在同一 Job 内使用教程地图，记录实际归一化阈值与 50 姿态输出，全部写 `/storage/penghongen/tmp/emap2lig_with_level_gate/<launch>/`。CPU 门控只读比较旧请求选择与原 243 条记录逐字段一致，并用整体平移验证不对齐 RMSD。两类命令、各次尝试及实际 release／launch 分开记录在[总日志](日志/总日志.md)、[Find 日志](日志/Find.md)、[Build 日志](日志/Build.md)。

## 交付元数据与验收证据

`结果/` 共镜像本轮输入、Find 元数据、Build 请求与逐姿态评价，也保存每个完成实例的原 `LIG.npz` 和评分 CSV。密度、完整概率、原生 blob、CIF 与预测掩码的原文件留在服务器独立实验根。本地不生成这些原文件的空占位；元数据中的路径可用于读取服务器原件。

| 文件 | 顶层类型与用途 |
| --- | --- |
| `结果/inputs/emdb_metadata/<pdb>.meta.json` | 原对象逐字节副本；与 `maps.json.metadata_sha256` 一一对应 |
| `结果/inputs/{emap,evaluation}_environment.txt` | 文本行列表；两份实际 Conda Python 的包版本 |
| `结果/inputs/deployment_files.json` | object；`implementation_commit` 是实际投递源码提交，`remote_root` 是可变发布源，`files` 是相对路径到冻结文件 SHA-256 的映射 |
| `结果/inputs/runtime/{formal,gate}/{launch.json,run_cmd.sh}` | 原控制器对象与 shell 文本；正式／门控命令分别保存，资源为 Job 423330、A800、24 CPU |
| `结果/inputs/runtime/release_manifest.json` | 原对象；源码 release 的完整内容身份，科学代码另有逐文件 receipt |
| `结果/inputs/runtime/emap2lig.yaml` | 原配置对象；显式 level、50 姿态／100 步与种子覆盖由正式代码直接表达 |
| `结果/inputs/runtime/allocation_{out,err}.gz` | gzip 文本；同一 allocation 的 a1 门控、a2 正式输出，按原 launch 分界，不作为单独正式实验数据 |
| `结果/inputs/runtime/job.txt` | 原 Slurm 状态文本；完成后 allocation 保留，after_lock 未删除 |
| `结果/inputs/final_audit.json` | object；`passed` 为验收布尔值，`checked_at_master` 为主节点时间，`formal_launch`、`release`、`implementation_commit` 是实际运行身份 |
| `证据/preflight.json` | object；原关键文件的 `sha256`、`size`、`mtime_ns` 和权重身份，供最终保护核对 |
| `证据/git_endpoints.json` | object；实现／学习端点、共同基点、树身份及等价结果，验收后生成并留在本地，不参与代码运行或自身提交 |

`final_audit.json` 的 `source_files_verified`、`find_pdbs`、`find_gt_instances`、`find_blobs`、`find_hit_instances`、`build_generated_instances`、`cif_poses`、`finite_scores` 均为整数计数。`empty_pdbs` 是零候选 PDB 字符串列表；`rmsd_statuses`、`full_test_statuses` 是状态到实例数的映射；`identity_fallback_poses` 是恒等原子映射处理的姿态数。`build_summary` 与上述 Build 汇总相同；`protected_old_files_unchanged` 按原绝对路径保存已核对一致的 `sha256`、字节数 `size` 和纳秒修改时间 `mtime_ns`。正式源码提交保持实际投递身份；后续日志／交接与学习历史提交不改写这次运行的源码来源。
