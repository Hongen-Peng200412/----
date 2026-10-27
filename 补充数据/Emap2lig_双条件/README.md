# Emap2lig：无 level 与显式推荐 level 的结果资产

这里把两次合法的 Emap2lig 测试分开索引。`no_level` 是10.27之前的图文使用的原实验；`explicit_emdb_level` 是显式提供 EMDB 推荐密度 level 的已完成实验。新实验的元数据实物已复制到论文仓库，旧实验原件保留原位。当前正文、PPT、图注和 Word 尚未切换数据源。————————————注意，后续 Emap2lig-level 版本的数据和可视化要进入正文，no_level版本仍保留，但放到补充材料里。

先读 [实验索引](实验索引.json) 确定条件和位置，再读对应科学文件。后续正文拟使用 `explicit_emdb_level`，`no_level` 拟进入补充材料；顺序与已确认版面见 [后续安排](后续安排.md)，复制与验收见 [接入记录](接入记录.md)。这些是资产索引，不替代八份 `图表追溯.md` 对实际展示的逐图登记。

## 条件与测试范围

| 固定条件名 | 实际预处理 | 本地入口 | 当前展示状态 |
| --- | --- | --- | --- |
| `no_level` | 未显式传入推荐值，原实跑入口的清零阈值为 0 | [旧归档](../Find-Match-Build_20261018/README.md)，其他原位缓存列于索引 | 仍为当前图文数据 |
| `explicit_emdb_level` | 向官方入口传入推荐值 L；官方 `contour_ratio=0.5`，实际清零阈值 L/2 | 本目录 `explicit_emdb_level/` | 元数据已接入，尚未绘图替换 |

L 是原图尺度的 EMDB 推荐密度值；178 份来源为 AUTHOR，1 份为 EMDB。它不是原子坐标真值，也不是给 Build 的真实结合区域。Find 仍自行预测 blob；Build 使用选中的预测 blob 与冻结的正确 SMILES。负密度置零、官方 1 Å 重采样、第 98 百分位归一化与内容裁剪沿用原管线。原地图与真值网格不同，评价时按世界坐标插值，而不是按数组下标叠合。

| 范围键 | PDB／真实实例数 | 身份依据 | 用途 |
| --- | --- | --- | --- |
| `find_all` | 179／2,502 | 旧归档 `provenance/find/inventory.json`，与新 `inputs/test_0.json` 对齐 | 全配体检出 |
| `find_all_small` | 94／821 | 旧归档 `provenance/stage1_all_small/occurrences/` 的 94 份文件中 `type_tag="small_molecule"` 的原实例 | 全部小分子检出，不限制残基数或缺失原子 |
| `build_eligible` | 77／446 | 新 `inputs/test.jsonl`，与原冻结清单逐字节一致 | 合格小分子对接及相应端到端评价 |

两条件共享上述测试定义。新 Find 共 2,474 个原生 blob，15 个 PDB 合法零候选仍保留在 179 的分母中。446 个 Build 测试实例中，260 个被 Find 命中，251 个通过体素数／重原子数比例筛选并各生成 50 个姿态，9 个筛选失败，186 个 Find 未命中。完整文件保留全部 446 个实例。旧条件相应为 243 个命中、237 个生成姿态、6 个筛选失败；旧共同命中配对数不适用于新条件。

## 本地目录

以下两棵树表示同一物理目录，分别列出科学接口和来源、诊断文件。`<pdb>` 的 179 个取值来自 `inputs/test_0.json`；Build 的 `<occurrence>` 是 77 个 PDB 中的原实例编号，不连续。`<launch>` 保留原运行目录名；251 个成功实例各有一份 `LIG.npz` 和一份原评分 CSV，N 是该实例选中的原生 blob 编号。

```text
## <科学产物>
补充数据/Emap2lig_双条件/
├─ 实验索引.json                            # 两条件、共同测试范围与仓库／服务器位置
└─ explicit_emdb_level/
   ├─ inputs/
   │  ├─ maps.json                          # 179 个原图、推荐 level 及原 EMDB 元数据身份
   │  ├─ test_0.json                        # 179-PDB Find 有序清单
   │  ├─ test_1.json                        # 149-PDB 保序子集，仅派生评价
   │  ├─ test.jsonl                         # 77-PDB／446 实例的冻结 Build 身份
   │  └─ emdb_metadata/<pdb>.meta.json       # 179 份推荐值来源原件
   ├─ find/held_out_test_0/
   │  ├─ evaluation/per_pdb/<pdb>.npz       # 179 份交集、匹配、语义和实例统计事实
   │  ├─ evaluation/official_find_li.jsonl   # 179 份逐 PDB 指标，供配对／分布读取
   │  ├─ evaluation/official_find_li.metrics.json # 全集宏／微平均指标
   │  └─ mapped/<pdb>/official_blobs.npz     # 179 份原编号、分数和稀疏体素
   ├─ find/held_out_test_1/evaluation/       # 149-PDB 派生指标，无重复模型推断
   └─ build/
      ├─ find_hit_subset.jsonl              # 260 个命中实例的唯一 Build 请求
      ├─ build_occurrences.jsonl            # 260 个命中实例，含筛选失败
      ├─ build_all_occurrences.jsonl        # 完整 446 个实例，含 Find 未命中
      └─ build/<pdb>/<occurrence>/<launch>/
         ├─ preprocess/ligands/LIG.npz      # 251 份官方化学身份与原子命名
         └─ build_struct/blob_N/blob_N_results.csv # 251 份原 consistency_iou 评分

## <其他文件>
补充数据/Emap2lig_双条件/
├─ 后续安排.md                              # 已授权接入范围及后续顺序（规划）
├─ 接入记录.md                              # 复制过程、正式／核查命令与验收（执行记录）
├─ .gitattributes                           # 关闭本目录换行转换（归档配置）
└─ explicit_emdb_level/
   ├─ inputs/{emap,evaluation}_environment.txt # 两个实际 Python 环境的包清单（来源证据）
   ├─ inputs/{gpu,empty_find}_gate_report.json # 原门控结果，非测试集科学结果（运行诊断）
   ├─ inputs/{deployment_files,final_audit}.json # 投递文件身份与最终验收（来源证据）
   ├─ inputs/runtime/                      # 正式／门控 launch、命令、配置及压缩输出（运行证据）
   ├─ find/held_out_test_0/
   │  ├─ raw_find_outputs/<pdb>/status.json # 179 份原输入和完成状态（运行诊断）
   │  ├─ mapped/<pdb>/mapping.json          # 179 份源／目标网格几何（运行诊断）
   │  └─ reports/find_run_summary.json      # 179 个 PDB 的执行汇总（运行统计）
   ├─ build/{find_hit_summary,build_summary}.json # 覆盖数和 RMSD 成功数（运行统计）
   ├─ build/build_status.jsonl              # 260 个实例的尝试状态（运行诊断）
   └─ provenance/
      ├─ metadata_inventory.json           # 1,428 个镜像文件的原大小与 SHA-256（来源证据）
      ├─ deployment_files.json             # 正式投递的 71 个代码／文档文件散列（来源证据）
      ├─ preflight.json                    # 原无 level 关键文件和权重保护基线（来源证据）
      ├─ git_endpoints.json                # 原实验实现／学习端点等价记录（来源证据）
      ├─ code/                             # 66 个实际运行代码、配置和输入文件（源码证据）
      ├─ source_code_receipt.json          # 66 文件的实际部署字节与 Git blob 对应（来源证据）
      ├─ source_records/{README.md,日志/}  # 最终说明及总／Find／Build 日志原件（历史快照）
      ├─ import_receipt.json               # 本次额外副本的原位置和散列（接入证据）
      └─ import_validation.json            # 本次源、目标与保护范围核对（接入验收）
```

本地没有原始连续密度、完整概率图、原生 blob NPZ、掩码 MRC 或 CIF。它们仍在 `/storage/penghongen/Emap2lig/contour_level_20261026/`，相对布局与镜像相同；准确单文件路径见 `maps.json.input_map`、`mapping.json.official_probability`、请求的 `blob_path` 与姿态的 `cif`。`LIG.npz` 是化学输入，不是预测姿态或参考真值。后续可视化选定病例后再读取对应大型原件，不能沿用无 level 的密度或姿态冒充新病例。

## 主要产物：身份与条件

### `实验索引.json`

顶层是 JSON object。`schema_version=1` 固定本版字段；`path_base="paper_repository_root"` 表示所有 `identity_path`、`level_path` 和 `local_paths` 均相对论文仓库根，而不是相对本文件。`server_paths` 是 Linux 服务器绝对路径，不能作为本地文件读取。

`paper_state` 的 `current_emap2lig_condition="no_level"` 表示现有展示；`planned_main_condition="explicit_emdb_level"` 与 `planned_supplement_condition="no_level"` 表示已决定的后续方向；`manuscript_and_slides_switched=false` 表示此次没有完成图文替换。

`cohorts` 按上述三个范围键保存整数 `pdb_count`、`instance_count` 及身份位置 `identity_path`；小分子另有 `category_field="type_tag"`、`category="small_molecule"`，分别指原文件分类字段及所取类别。`conditions` 只含两个固定条件键；每项的 `label_zh` 为中文名称，`normalization` 描述是否显式传入 level。旧条件的 `explicit_level=false`、`effective_threshold=0`；新条件的 `explicit_level=true`、`contour_ratio=0.5`、`effective_threshold_expression="level * contour_ratio"` 与 `level_path` 定义逐图阈值。`local_paths` 的键说明本地文件用途，如 `build_full_test` 指向 446 行完整结果；旧条件没有该键，不意味着其余未命中被算作成功。`server_paths` 定位原 Find／Build／统一比较或新科学根／release。新条件 `executed_source_commit` 是真正运行的源码提交，`counts` 都是整数观察计数，如 `find_blobs=2474`、`build_complete_instances=251`，不代表百分比或宏平均。

### `explicit_emdb_level/inputs/maps.json`

长度 179 的列表，与 `test_0.json.pdb_ids` 同序，每项完整实际示例如下。`level` 与 `effective_threshold` 使用原始地图密度单位；其余路径是服务器原件位置，`metadata_sha256` 对应本地同 PDB 的原 EMDB 元数据字节。

```json
{"pdb_id":"9ter","emdb_id":"EMD-55834","level":0.011,"effective_threshold":0.0055,"source":"AUTHOR","metadata_path":"/storage/penghongen/AdaLigand/Ori_Data/reports/meta/9ter.meta.json","metadata_sha256":"b583c6e490937e402eeaf8672ee5e784d2b6ecc0eae8553febd37b338e9672e7","contour_ratio":0.5,"input_map":"/storage/penghongen/AdaLigand/Ori_Data/raw/emdb_maps/emd_55834.map.gz"}
```

### `inputs/test_0.json`、`inputs/test_1.json` 与 `inputs/test.jsonl`

路径在本节及下文省略共同前缀 `explicit_emdb_level/`。两个 JSON 的 `pdb_ids` 是小写 PDB 有序列表，如 `test_0` 起始为 `["9ter","30yu"]`；149 项子集不参与主 179 分母的替换。JSONL 每行一个冻结 Build 实例，键为 `(pdb_id,candidate_id)`；如 `11jb/0`，`candidate_id` 与下游 `occurrence_id` 同义，`prepared_smiles` 是化学输入，`n_heavy_atoms` 是重原子数。保留原清单其余字段原样，不根据当前图重新筛选。

## 主要产物：区域几何与评价

P 是一个 PDB 的预测 blob 数，G 是该 PDB 的全部真实实例数。数组中的实例索引都从 0 开始；原生 `blob_N` 的 N 从 1 开始且不等于数组下标。所有下游连接须带条件键和 PDB；不要只按 `occurrence_id` 或相同文件名连接。

### `find/held_out_test_0/mapped/<pdb>/official_blobs.npz`

每 PDB 一份，整数 `source_blob_index` `(P,)` 是保留的原生 N；`source_probability_mean` 与 `score` 为 float32 `(P,)`，如 11jb 的首个 `source_blob_index=189`，其顺序按原生平均概率降序。`selected`、`prauc_eligible` 是 bool `(P,)`，分别表示纳入原选取与 PRAUC 候选集合；本轮保留全部官方候选。`voxel_count` 是 int32 `(P,)`，保存各候选映射后的体素数。

`voxel_offsets` 为 int64 `(P+1,)`，同时切分 int32 `(V,3)` 的 `voxel_index_global_zyx` 第一轴；第 i 个 blob 的稀疏整数坐标为 `[offsets[i],offsets[i+1])`，首值 0、末值 V；末轴顺序 ZYX。不同候选允许重叠。`grid_shape_zyx` 为 int64 `(3,)`，`origin_xyz` 与 `voxel_size_xyz` 为 float32 `(3,)`，后两者单位 Å，按 XYZ 排列；世界坐标由整数网格索引与原点、体素尺寸计算。

`origin_xyz` 是零索引体素的网格角点，不是体素中心。整数索引 `(z,y,x)` 对应的体素中心世界 XYZ 为 `origin_xyz + ([x,y,z] + 0.5) * voxel_size_xyz`，乘法逐轴进行。反向映射先算 `(world_xyz-origin_xyz)/voxel_size_xyz - 0.5`；实例映射按原实现 `np.rint` 取最近整数，再换回 ZYX；概率则在这个连续索引位置线性插值。不能漏掉半体素项，也不能把 XYZ 直接当成 ZYX。

真实空候选例 9ter：`source_blob_index=[]`、`voxel_offsets=[0]`、`voxel_index_global_zyx.shape=(0,3)`、`grid_shape_zyx=[282,282,282]`、`origin_xyz=[0,0,0]`、`voxel_size_xyz=[1.000851,1.000851,1.000851]`。这仍是合法执行，不能从后续分母删除。

### `find/held_out_test_0/mapped/<pdb>/mapping.json`

记录同 PDB 原生与真值网格，必需字段为 `pdb_id`、`official_probability`、`official_blob_count`、`mapped_blob_count`、`source_shape_zyx`、`source_voxel_size_xyz`、`source_origin_xyz` 及三个对应的 `target_*` 数组。shape 为三个整数；origin 与 voxel_size 为三个数，分别按 XYZ、单位 Å。9ter 的 `source_shape_zyx=[129,175,123]`、`source_origin_xyz=[91,58,85]`、`source_voxel_size_xyz=[1,1,1]`，目标几何见上一节，两个候选计数均为 0。概率用线性插值，实例用最近体素映射，原生编号保留。

### `find/held_out_test_0/evaluation/per_pdb/<pdb>.npz`

以下是全部字段族。T 是阈值数 3，K 是 top-k 档数 3，M 是三个阈值的匹配对总数。交集、大小和语义计数均以体素为单位；概率、覆盖率和分数无量纲。

| 字段 | dtype／形状 | 语义及例子 |
| --- | --- | --- |
| `occurrence_id` | int32 `(G,)` | 真值实例编号，9ter 为 `[0,1]`；G 保留全部类别 |
| `source_blob_index` | int32 `(P,)` | 原生编号；11jb 首项 189；不是候选下标 |
| `candidate_score` | float32 `(P,)` | 与候选轴逐项对齐的原排序分数 |
| `candidate_selected`、`candidate_prauc_eligible` | bool `(P,)` | 相应为候选参与选取／PRAUC 的掩码；空候选时都是 `[]` |
| `intersections` | int64 `(P,G)` | 候选 i 与真值 j 的交集；9ter 为 `(0,2)` |
| `pred_sizes`、`gt_sizes` | int64 `(P,)`、`(G,)` | 两轴各自体素数；9ter 真值 `[40,42]` |
| `candidate_semantic_tp` | int64 `(P,)` | 每个候选与全部真值并集的交集数；空时 `[]` |
| `semantic_tp`、`semantic_fp`、`semantic_fn` | int64 scalar | 预测与真值并集的 TP／FP／FN；9ter 为 0／0／82 |
| `coverage_thresholds` | float32 `(T,)` | `[0.3,0.5,0.6]`，第 0 档为 0.3 |
| `topk_values` | int32 `(K,)` | `[3,4,5]`，第 0 档为前 3 个候选 |
| `coverage_pred_hit_mask`、`coverage_gt_hit_mask` | bool `(T,P)`、`(T,G)` | 双向覆盖达到该档阈值的命中掩码；9ter 真值掩码每档 `[false,false]` |
| `coverage_pred_hit`、`coverage_gt_hit` | int64 `(T,)` | 上述掩码沿候选／真值轴求和；9ter 都为 `[0,0,0]` |
| `one_to_one_match_offsets` | int64 `(T+1,)` | 将以下两个匹配索引数组同时按阈值切片；11jb 为 `[0,78,156,234]`，首档 `[0,78)` |
| `one_to_one_match_pred_index`、`one_to_one_match_gt_index` | int32 `(M,)` | 分别索引候选轴 P 与真值轴 G；11jb 首对为候选下标 0／真值下标 65，需再经编号数组获取身份 |
| `one_to_one_tp` | int64 `(T,)` | 各阈值的一对一匹配对数；11jb 为 `[78,78,78]` |
| `topk_success` | int64 `(K,T)` | 第一轴是 top-k 预算，第二轴是覆盖阈值；是否至少命中一个真值，1／0；11jb 首格为 1 |
| `topk_winning_candidate_rank` | int32 `(K,T)` | 首次成功候选在已选候选序列中从 0 开始的位置；11jb 首格 0；无成功为 -1 |
| `topk_winning_occurrence_index` | int32 `(K,T)` | 获胜真值在 G 轴的下标；11jb 首格 65；无成功为 -1 |
| `semantic_prauc_histogram` | int64 `(2,1024)` | 第一轴依次是负／正真值体素，第二轴是 0 至 1 的 1,024 个升序阈值档，包含两端；每体素计入其概率能通过的最高阈值档 |

正常一对一匹配不重复使用候选或真实实例。覆盖命中与一对一匹配不同，不能混用其计数。按范围计算时先在全部 G 中确定候选归属，再判断实例类别；不能先删除非小分子后重新选匹配。

候选唯一归属用于完成度轨迹与 Build 输入选择，不是把 NPZ 中的一对一匹配重新定义一遍。对候选 i 和真值 j，令 `a=intersections[i,j]/pred_sizes[i]`、`b=intersections[i,j]/gt_sizes[j]`；仅 `a>=0.3` 且 `b>=0.3` 的 j 可归属，选 `sqrt(a*b)` 最大者，分数完全相同时选较小的 `occurrence_id`。没有合格真值的候选是背景。先在全部真实类别中完成这一步，之后才按 `type_tag` 或 446 实例清单判断目标范围。

### `evaluation/official_find_li.jsonl` 与 `official_find_li.metrics.json`

逐 PDB 文件有 179 行，`pdb_id` 是连接键；汇总 JSON 为相同指标的全集统计。语义 Dice 对应 `semantic_macro_f1`，不是 `one_to_one_macro_f1_0p3`。逐 PDB 9ter 的 Dice 为 0，语义 PRAUC `semantic_macro_prauc=0.000003656508`，说明零候选仍消费真实概率。

`semantic_{macro,micro}_{precision,recall,f1,f2,prauc}` 描述语义并集；`coverage_` 和 `one_to_one_` 前缀分别描述覆盖命中与实例一对一匹配，后接 `{macro,micro}_{precision,recall,f1,f2,prauc}_{0p3,0p5,0p6}`。macro 为逐 PDB 等权平均，micro 为累计计数后求指标。`pdb_count` 是实际 PDB 数；`semantic_tp/fp/fn` 是累计体素计数。`top{3,4,5}_success_{count,ratio}_{0p3,0p5,0p6}` 与 `topk_eligible_pdb_count` 是对应预算成功数／比例及可评价 PDB 数。逐图文件 `pdb_count=1`。新小分子范围需从 NPZ 和原类别文件派生，不能把 77／446 或 149-PDB 子集文件当成 94／821 结果。

## 主要产物：请求、原子身份与姿态

### `build/find_hit_subset.jsonl`

每行一个命中实例，以 `(pdb_id,occurrence_id)` 连接冻结 `candidate_id`。完成上述候选唯一归属后，对同一实例选择 `sqrt(a*b)` 最大的 blob；分数完全相同时保留原 Find 排序较靠前的 blob。两步不能互换，也不能用“首次命中 blob”代替本次实际 Build 输入。`blob_id` 是 N，`find_rank` 从 1 开始；它们不是同一个编号。`prepared_smiles`、`n_heavy_atoms` 定义化学身份；`foreground_voxels` 是原生 blob 前景体素数，`voxel_atom_ratio` 是其除以重原子数；比例在 `[5,25]` 时 `status="ready"`，否则为 `build_filter_failed`。`blob_path` 是服务器原生 NPZ 的完整路径。

真实 11jb/0 请求的数值为：`blob_id=56`、`find_rank=50`、`n_heavy_atoms=36`、`foreground_voxels=363`、`voxel_atom_ratio=10.0833333333`、`status="ready"`。完整请求与无省略的格式示例见冻结 [源产物契约](explicit_emdb_level/provenance/source_records/README.md#build-请求与构象)。

### `build/build_occurrences.jsonl` 与 `build/build_all_occurrences.jsonl`

前者 260 行，后者 446 行。共同字段是 `pdb_id`、`occurrence_id`、`find_rank`、`status`、`result_dir`、`top1_rmsd_A`、`top5_rmsd_A`、`oracle_rmsd_A`、`poses`。距离是未作刚体叠合的重原子 RMSD，单位 Å。Top-1 按原 `consistency_iou` 降序取第一名，Top-5／oracle 分别是该排序前 5／全部 50 个姿态的最小有效 RMSD。原排序不使用真值距离。

正常 `status="complete"`、`poses` 长度 50，每项有整数 `rank`、浮点 `consistency_iou`、服务器路径 `cif`、浮点或 null 的 `rmsd_A`、布尔 `identity_fallback`；异常可附 `error`。真实 11jb/0 的 `top1_rmsd_A=1.2487411450`、`oracle_rmsd_A=1.2355828908`；排名 1 的文件是 `blob_56_LIG_11.cif`，可见采样编号不等于评分排名。

未检出的完整构造示例（仅用于格式）：

```json
{"pdb_id":"1abc","occurrence_id":0,"find_rank":null,"status":"find_miss","top1_rmsd_A":null,"top5_rmsd_A":null,"oracle_rmsd_A":null,"poses":[],"result_dir":null}
```

筛选失败状态为 `build_filter_failed`，保留实际 `find_rank` 和可能尚不存在的 `result_dir`，三种 RMSD 均 null、`poses=[]`。null 不当作 0 Å；成功阈值严格 `<2` 或 `<3` Å，相等不算。9 个筛选失败和 186 个 Find 未命中均留在完整 446 分母中。命中分母成功率和逐 PDB 等权完成度是不同统计。

### `build/build/<pdb>/<occurrence>/<launch>/preprocess/ligands/LIG.npz`

官方化学输入包，11jb/0 有 36 个重原子、39 个键。`smiles`、`name` 是 Unicode scalar，后者为 `LIG`；`atom_names` 为 Unicode `(A,)`，如首项 `O4`，按重原子轴 A 与后续 CIF 的原子名相连；`residue_names` 如 `["LIG"]`。`atoms` 是 `(A,)` 结构数组，含 int8 编码名 `name (4,)`、int8 元素原子序数 `element`／电荷 `charge`、float32 三维 `coords/ref_pos`、bool `is_present`、bool 手性 `chirality (7,)`、bool 环标志 `in_ring (4,)` 和 int32 残基编号 `residue_id`；`bonds` 是 `(B,)` 结构数组，int32 `atom_1/atom_2` 从 0 开始索引 A 轴，bool `type (5,)` 依次编码单／双／三／配位／芳香键，bool `in_ring (4,)` 依次表示 3／4／5／6 元环。手性字典见证据源码 `provenance/code/src/emap2lig/data/const.py`，它按 one-hot 表示该原子的手性类型；`ref_pos` 是化学生成参考构象、单位 Å，不是沉积位姿；本例 `coords` 为零。`symmetries` 本例为空数组；`blobs` 为整数数组，本例 `[56]`。这些官方内部编码原样保存，论文统计直接读逐姿态 JSONL。

### `build/build/<pdb>/<occurrence>/<launch>/build_struct/blob_N/blob_N_results.csv`

原评分文件每份 50 行，`conformer_name` 对应 CIF 的采样名称，`consistency_iou` 为无量纲评分，越大越靠前；最终顺序由上述 `poses[].rank` 固定。CSV 原始行序不应直接当成排名。251 份 CSV 保留原 CRLF 字节。

## 来源、统计与验收

### `provenance/metadata_inventory.json`、`import_receipt.json` 与 `source_code_receipt.json`

原清单顶层含 `server_root`、源仓库的 `local_root="显式level实验/结果"`、`file_count=1428`、`byte_count=21380471`、`files`。`files` 以相对科学根路径为键，每项是 `size` 字节数和 64 位十六进制 `sha256`。接入后从 `explicit_emdb_level/` 开始拼接这些键，不能按历史 `local_root` 在论文仓库寻找。它不覆盖新增的 `provenance/`。

接入 receipt 记录源仓库、最终说明的端点 `source_document_endpoint`、实际运行提交 `executed_source_commit`、复制文件／字节数、代码数及 `additional_copies` 列表；每项含原绝对路径 `source`、相对本资产根的 `destination`、`size` 和 `sha256`。源码 receipt 的 `files` 按源代码相对路径保存 `size`、部署字节 `sha256`、`git_blob_sha256` 和 `export_source`。65 项为 `git_blob`；配置一项为 `frozen_runtime_config_CRLF`，只在换行上与 Git blob 不同。实际运行提交始终为 `37b0d9e7ad2a1b18fa096d91f154619085cee907`，不能用后来的日志／学习线提交冒充实验源码。

### `build/find_hit_summary.json`、`build/build_summary.json` 与 `inputs/final_audit.json`

前者的 `full_occurrences=446`、`find_best=260`、`build_ready=251` 是输入计数，`build_filter_failed` 是 9 个 `PDB/occurrence` 字符串列表，不是姿态误差。Build 汇总的 `denominator=260`、`full_test_denominator=446`，`statuses={"build_filter_failed":9,"complete":251}`；`top1/top5/best_lt2A/lt3A` 是严格阈值成功计数，如 `top1_lt2A=156`、`best_lt3A=230`。不从这些计数直接声称逐 PDB 宏平均。

最终审核 `passed=true`；`find_pdbs/find_gt_instances/find_blobs` 为 179／2502／2474，`empty_pdbs` 列出 15 个合法零候选 PDB，`cif_poses=finite_scores=12550`，`identity_fallback_poses=0`。`rmsd_statuses`、`full_test_statuses` 是状态计数映射；`protected_old_files_unchanged` 以旧服务器绝对路径为键，保存一致的散列、大小及 `mtime_ns`（纳秒修改时间）。这是原实验最终核验快照，本次不重新声称核查了服务器当前状态。

### 诊断文件、原日志与本次验收

`build_status.jsonl` 按实例保存尝试状态，重试不删除旧行，最后一行决定评价读取哪个 `result_dir`；正常含 `generated`、成功含 `seed`，异常可含 `error`。原门控／正式命令、环境、状态与完整字段说明见 [源契约快照](explicit_emdb_level/provenance/source_records/README.md)；本次来源核对见 `provenance/import_validation.json`，其计数与散列用于核对接入完整性。原执行历史只保存在 `source_records/日志/`，本次过程在 [接入记录](接入记录.md)。这些记录不会自动启动运行。

本次验收 JSON 中，`cohorts` 的两元素整数列表按 `[PDB数,实例数]` 排列，如 `find_all_small=[94,821]`；`build_statuses` 是状态到实例数的映射，如 `complete=251`。`metadata_files_verified_source_and_destination`、`metadata_bytes`、`deployed_source_files_verified` 分别为核对文件数、字节数与源码证据文件数；`protected_existing_files_verified` 为旧归档与既有修改的保护文件数。`checked_at` 是带时区的本地核查时间，`passed` 表示本次核对全部通过；`same_build_identities_and_smiles_as_no_level`、`source_git_refs_and_status_unchanged` 为对应核对的布尔值。`paper_head_unchanged`、`paper_branch_unchanged` 保存未变的 Git 提交和分支；`current_display_condition="no_level"`、`manuscript_and_slides_switched=false`、`server_contacted=false` 明确此次交付范围。其余整数计数是候选、零候选 PDB、化学包、评分文件和本地链接的实际核对数量。

## 论文追溯与使用顺序

Stage1 统计从新逐 PDB NPZ／JSONL 与原类别轴派生；Stage3 配对从 `(条件,pdb_id,occurrence_id)` 重新连接；新病例需读取对应条件原始 CIF／密度，并重新计算相应几何指标；端到端图须沿完整 446 实例保留未命中与筛选失败。旧 `metadata/figure_data/data.json` 和当前绘图缓存仍全是 `no_level`，不能只改标签来切换条件。

实际图表登记仍在 [Stage1 计算](../../画图/画图代码/stage1/calculate/图表追溯.md)、[Stage3 计算](../../画图/画图代码/stage3/calculate/图表追溯.md)、[Stage3 可视化](../../画图/画图代码/stage3/visualization/图表追溯.md)、[端到端计算](../../画图/画图代码/e2e/calculate/图表追溯.md) 和 [端到端可视化](../../画图/画图代码/e2e/visualization/图表追溯.md)。后续新增缓存、图名或补充材料副本应显式带条件；共用统计代码可以，两个条件的科学输入和产物目录必须可区分。
