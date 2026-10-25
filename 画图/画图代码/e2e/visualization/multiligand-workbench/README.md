# 多配体画图工程：材料与字段

本工程将九个测试复合物的既有实验结果整理为 ChimeraX 1.10.1 可编辑会话。日常操作从[开始使用](开始使用.md)和[交互命令速查](交互命令速查.md)开始；本文件供核对材料、编号和科学来源。

九例原件、MRC/CIF/SDF、初始会话、56组示范视图和材料索引已生成；五种模式的科学计数、GUI保存恢复及旧temp屏蔽的九例完整重建均已通过。第一版为[十页可编辑候选图](../../../../多配体交互候选图_20261023.pptx)，完成证据见[执行记录](执行记录.md)。

当前面板和九例initial为1.0.7，增加参考身份/位置名称，区域默认橙色网格，聚焦不添加裁剪，初始关闭深度淡化。D盘原有 `views/*.cxs`、`exports/*.png` 和作者PPT图像保留10月23日版本；`views/*.cxc` 已更新为当前命令。新一轮56视图只用于独立重建验收；既有个人edit会话不覆盖。

## 文件实际位置

下面两段列出同一物理目录中的不同用途文件。案例目录实际为 `9bjj`、`11jb`、`9lov`、`9okp`、`30ga`、`9ujf`、`9wup`、`9lw1`、`9llg`。

```text
## <科学产物>
D:/AdaLigand_Visualization/
├─ catalog.json                 # 九例原评价、实例、候选、预算及实际构象来源
├─ _server/storage/penghongen/   # 服务器原件的本地唯一缓存, 保持原有相对目录
├─ templates/*.npz              # 去重配体模板的硬链接, 含原子与键
└─ 9bjj/                        # 其余八例结构相同
   ├─ source/                   # 原数组、逐候选50-pose SDF及排名/评价; 硬链接到缓存
   ├─ assets/maps/*.mrc          # 完整实验、GT模拟、CA2模拟密度, 三图均保持原值
   ├─ assets/references/*.sdf    # 每个真实实例一个文件, 只保留实际沉积原子
   ├─ assets/areas/occ_16.mrc    # 真实实例16的裁剪0/1掩码; 其余实例同名规则
   ├─ assets/blobs/CA2_blob_0.mrc # CA2候选0的裁剪0/1掩码; GT以GT开头
   ├─ assets/receptor_*.cif      # GT/CA2受体世界坐标, token链名用于显示
   ├─ assets/poses/*.sdf         # 原top-1与原评价best-of-50的原SDF记录
   ├─ scene.json                # 本例科学记录与所有显示资产编号
   └─ poses.csv                 # 逐显示构象的样本、SDF记录、RMSD及服务器连接

## <其他文件>
D:/AdaLigand_Visualization/
├─ tools/*.whl                  # ChimeraX工具的固定安装副本（运行依赖）
├─ _temp/                       # 指向仓库本轮temp的ASCII路径入口（工具临时目录）
├─ view_index.json              # 56个示范视图及局部实例/构象连接（可再生工具输入）
└─ 9bjj/
   ├─ assets/labels/*.cif        # 标签位置的小标记, 不表示预测原子（可再生工具输入）
   ├─ load.cxc                  # 从全部资产建立本例的官方命令（可再生工具输入）
   ├─ views/*.cxc               # 在已载入本例上应用示范参数（可再生工具输入）
   ├─ initial.cxs               # 由load.cxc及示范参数保存的初始会话（可再生辅助导出）
   ├─ edit_001.cxs              # 作者点保存后产生的个人修改, 编号递增
   ├─ exports/*.png             # 官方原生导图（可再生辅助导出）
   ├─ exports/load_commands.html # 本例全部加载命令
   ├─ exports/*.commands.html  # 各视图实际官方命令、相机矩阵与导图日志
   ├─ 对象索引.csv              # 全材料名称、模型编号及姿态连接（可再生辅助导出）
   ├─ 候选索引.csv              # blob、真实实例、预算和构象的对照（可再生辅助导出）
   └─ 本例参数.md               # 三图阈值、局部示例及冻结完成数（可再生辅助导出）
```

仓库的 `e2e/output/multiligand-workbench/` 保存同源 `catalog.json`、`download_requests.json`、`source_receipt.json` 和安装包。程序位于本目录，运行日志、测试和打包中间文件位于仓库 `temp/multiligand-workbench/`。长期运行不读取旧 archive 或旧 temp。

## 查看真实配体与预测材料

### catalog.json 与 scene.json

`catalog.json` 是一个 JSON 字典，含 `schema=1`、D盘 `data_root`、九项 `cases`、`evaluation_sources` 原评价文件路径和 `experiment` 原模型证据。`experiment` 原样记录 checkpoint_path、model_code_source、status、candidate_order；这些是实际冻结实验的字段，不用当前代码HEAD替代。

每个 case 含 `pdb_id`（如 `9bjj`）、`counts`、`occurrences`、`identities`、`domains`。`scene.json` 保存单个case，并增加 `models`、`contour`、`folder`、`schema`、`local_examples`。

| 字段 | 含义与例子 |
|---|---|
| `counts.all/small/eligible` | 全部配体、全部小分子、Build合格实例数；9BJJ为19/11/11 |
| `occurrences[].candidate_id` | 原真实实例编号, 从0开始；如16，不是blob编号 |
| `display_name/site` | 从原components构成的名称/沉积位置；如A1AP0、E:1001 |
| `type_tag/eligible` | 原类别及是否满足单残基、完整、有机的Build条件；如small_molecule/true |
| `components` | 原组成残基；每项含index、ccd_id、auth_asym_id、auth_seq_id、icode、label_asym_id、label_seq_id；如原链E、序号1001、组分A1AP0 |
| `object_key/kind/polymer_length` | 原模板键、模板来源类型、残基数；如CCD:MG/CCD/1 |
| `n_heavy_atoms/is_covalent/inter_bonds` | 原重原子数、是否共价连接及原跨残基键；孤立Mg为1/false/空列表 |
| `identities` | 原身份记录；smiles连接该身份的occurrence_ids；stage3_occurrence_ids是其Build合格实例；语言特征相对路径与allowed_as_small_molecule_answer原样保留 |
| `domains.CA2/GT` | 两套各自的candidates、expected及简要trace，CA2与GT的同号blob不保证对应同一实例 |
| `contour` | 实验密度原单位的起始等值面阈值；9BJJ为0.021095575764775276 |
| `local_examples` | 示范局部的真实实例编号列表；9BJJ选择每种合格身份的首个预算内成功实例，按原候选次序，不重新选pose |

`occurrences` 中还保留原pdb_id。`identities` 中的type_tag使用同一类别定义，SMILES保持精确字符串，不按图片名称做身份判等。

例如，9BJJ 的实例16是一份完整的小分子记录：

```json
{"candidate_id":16,"pdb_id":"9bjj","display_name":"A1AP0","site":"E:1001",
 "type_tag":"small_molecule","eligible":true,"object_key":"CCD:A1AP0",
 "kind":"CCD","polymer_length":1,"n_heavy_atoms":28,"is_covalent":false,"inter_bonds":[],
 "components":[{"index":1,"ccd_id":"A1AP0","auth_asym_id":"E","auth_seq_id":1001,
                "icode":"","label_asym_id":"X","label_seq_id":1001}]}
```

`candidate_id/index/polymer_length/n_heavy_atoms/auth_seq_id` 是整数，`eligible/is_covalent` 是布尔值，其余命名字段是字符串；`components` 和 `inter_bonds` 是列表。空 `icode` 表示没有插入码，空 `inter_bonds` 表示没有跨残基键。`identities` 的每条记录含字符串 `pdb_id/smiles/type_tag/language_relative_path`、布尔 `allowed_as_small_molecule_answer`、整数列表 `occurrence_ids/stage3_occurrence_ids`。例如一条 ATP 身份对应实例 `[0,1,4,5,8,9,12,13,17]`，而非九种身份。身份的精确 SMILES 可以直接在 `scene.json` 查到。

### domains 中的候选与构象来源

每个 `candidates` 元素对应一份原Find候选，如CA2 blob 0。原 `source_blob_index`、`centered_box_index` 为零基候选/切块编号；`rank` 是本工程按冻结规则排序后的1基位置。`candidate_selected`、`source_probability_mean`、`gaussian_score` 保留原值。排序是selected优先，每段内平均概率降序、原blob编号升序破并列。

`foreground_target` 使用原双向覆盖均至少0.3的唯一对应，`matched_occurrence_id` 为对应真实实例或null；`target_smiles/target_category` 为真值身份/类别，无对应时可为null。`predicted_smiles/foreground_probability/identity_supported` 是原Match结果；`predicted_name` 仅为其SMILES的显示简称，如ATP或MG。`identity_correct` 要求原前景对应、身份受支持且精确SMILES相同；`is_small/is_eligible` 按命中的真实实例判断，背景两者均false。

`attempts` 和 `before` 都有五个键：`find_all`、`find_small`、`find_match`、`find_build`、`pipeline`。例如9BJJ CA2 blob 0在各模式的 `attempts` 为1，`before` 为0。“计费”指消耗一次尝试额度；“免费跳过”指按该模式规则考察但不扣额度，`attempts` 为 null。`before=11`表示考察该候选前已经用了11次，不表示原排名11。给定K次预算，仅纳入before<K的考察过程；all档纳入全部候选。

100% 的基数为该模式评价的真实实例数 N：`find_all/find_match` 用 `counts.all`，`find_small` 用 `counts.small`，`find_build/pipeline` 用 `counts.eligible`。百分比 p 的尝试上限是 `floor(p*N/100)`；9BJJ 全配体50%为9次，两个Build模式50%为5次。先按预算截取原候选考察过程，再按类别过滤，不补候选。

`runs` 是实际已生成的构象来源列表。每项的 `views` 如 `["find_build","pipeline"]` 表示该输入可用于这两个视图；Match错误时，给定正确身份的构象仅属于find_build。`output_dir/local/status` 为字符串，分别表示原服务器输出、本地原件目录和原运行状态；`top1_sample_index` 为原首选样本的零基整数编号。`pose_min_rmsd_A` 的字符串键1/5/50分别是原排序前1、5、50个构象中的最小RMSD，值为 Å 单位的浮点数或null。`success["2.0"或"3.0"]["1"或"5"或"50"]` 是相应范围是否达到该RMSD阈值的原布尔结果。默认完成数使用 top-1、2 Å；面板的 best 用50构象中的最优者，属于借助真值的回顾性比较。不同输出目录的构象保持分开。

9BJJ／CA2／blob 0 的实际 run 记录为：

```json
{"pdb_id":"9bjj","source_blob_index":0,"matched_occurrence_id":4,"status":"success",
 "output_dir":"/storage/penghongen/Adaligand_E2E/test/test_0/build/PocketXMol-tuned/CA2/test/local-c1/9bjj/0",
 "local":"9bjj/source/CA2/blob_0/run_0","views":["find_build","pipeline"],
 "top1_sample_index":21,
 "pose_min_rmsd_A":{"1":0.8045425274739195,"5":0.5801109820537201,"50":0.5786663808306773},
 "success":{"2.0":{"1":true,"5":true,"50":true},"3.0":{"1":true,"5":true,"50":true}}}
```

没有对应的 CA2 blob 10 则含 `foreground_target=false, matched_occurrence_id=null, target_smiles=null, target_category=null, is_small=false, is_eligible=false, identity_correct=false, runs=[]`；它仍有一个预测身份 ATP，但不能当作真实ATP实例。`runs=[]` 也可能表示某候选没有既有建模输出，不能将其RMSD写成0。`sample_index/sdf_index` 的0是有效编号；只有null表示缺少编号。`expected` 的一条完整记录如 `expected.find_match["100"]={"pdb_id":"9bjj","success_count":10,"target_count":19,"attempt_budget":19,"completion":0.5263157894736842}`；计数及预算为整数，completion为success_count/target_count的浮点数。

`trace` 只保留source_blob_index、raw_rank、attempt_index、action、target_scope、identity_correct、matched_occurrence_id，供核对原完整流水线计费；原完整记录仍由evaluation_sources定位。原流程中的 `continue` 表示本次考察后跳到下一候选；是否免费以 `attempt_index=null` 为准，不能只看英文动作名。画面仍纳入预算耗尽前遇到的免费跳过候选；假阳性消耗尝试额度。`expected[模式][50/100/200/300]` 是原冻结的pdb_id、success_count、target_count、attempt_budget、completion；例如9BJJ GT Find+Match 100%为10/19，完成度10/19。

### models 与 poses.csv

`models` 每项描述一个可独立显隐的材料：`key` 如CA2_blob_0，`id` 如10.1（命令中写#10.1），`file` 为案例目录相对文件名，`kind` 为receptor/density/reference/area/blob/pose/identity/correctness。`domain` 仅在材料属于CA2或GT时出现，`blob`与`occurrence_id`分别表示候选与真实实例编号。reference和area另有字符串 `display_name`，如 `ref_0_ATP_A901`、`area_0_ATP_A901`，作为Models中显示名；原 `key=ref_0/area_0` 与编号不变。名字中的A901取原 `components[].auth_asym_id/auth_seq_id/icode`，不取导出SDF的临时残基编号。多残基短名仅列首组分及位置，以 `plus2` 表示另有两个残基；完整组成仍在 `components`。

密度项含浮点 `level`、三整数列表 `shape_zyx`、三浮点列表 `origin_xyz_A/spacing_xyz_A`。这里 `origin_xyz_A` 是 MRC 的首个采样中心，已包含下文的半体素修正。受体项含整数 `atoms`。姿态项另含字符串列表 `views`、`pose`（top1或best）、整数 `sample_index`（原零基采样号）、整数 `sdf_index`（原零基SDF记录号）、`rmsd_A`（Å单位浮点数或null）、字符串 `output_dir`。标签项含字符串 `text`；其CTR标记是注字位置，不是预测原子。

`poses.csv` 每个显示构象一项，列为key、id、file、kind、domain、blob、views、pose、sample_index、sdf_index、rmsd_A、output_dir，与上述定义一致；`views` 用竖线分隔，例如 `find_build|pipeline`。CSV缺失RMSD为空；0是有效样本/记录号。best从原有效评价中取最小RMSD，不能从缺少RMSD的ranking.json自行猜测。

### 两份索引CSV

`对象索引.csv` 列model_id/key/name/kind/condition对应models的id/key/显示名/kind/domain。name优先取display_name，没有时取key；例如 `#3.1,ref_0,ref_0_ATP_A901` 连接同一个实例。reference_name/reference_site在真实配体及其区域中填原身份与沉积位置，如 `ATP,A:901`；其他材料留空。其余blob_id、occurrence_id、pose、sample_index、sdf_index、rmsd_A、file保持同义；views用竖线分隔。与该材料无关的列为空。

`候选索引.csv` 每项对应一个条件的一份blob，**condition 与 blob_id 共同标识候选**；同号CA2/GT不是同一个对象。blob_id、blob_model、rank、probability_mean、selected连接原候选；reference_instance/name/site连接真实实例；foreground/small/eligible及identity_correct是布尔值，predicted_identity是显示名称。full_attempt/small_find_attempt/find_build_attempt/pipeline_attempt分别是该模式计费号，空值为免费跳过。top1_model/best_model用竖线列出关联模型号，空值表示该候选没有相应已存构象。完整表头及实际首行为：

```csv
condition,blob_id,blob_model,rank,probability_mean,selected,reference_instance,reference_name,reference_site,foreground,small,eligible,predicted_identity,identity_correct,full_attempt,small_find_attempt,find_build_attempt,pipeline_attempt,top1_model,best_model
CA2,0,#10.1,1,0.9821481704711914,True,4,ATP,B:901,True,True,True,ATP,True,1,1,1,1,#20.1.1.1,#20.1.1.2
```

### 原始数组与模板

`source/exp.npy`、`GT_sim.npy`、`CA2_sim.npy` 为 float32 `(1,Z,Y,X)`；完整MRC写成 `(Z,Y,X)` float32。`exp.npz` 的 `origin/voxel_size` 是 float32 `(3,)` XYZ Å，`contour_canonical` 是实验图实际使用的标量阈值。`ligand_area.npz` 的 `mask_16` 是实例16的 `(V,3)` int32 全图ZYX体素索引；不是密集三维数组。`ligand_coords.npz` 的 `coords_16` 是 `(N,3)` float32 世界XYZ Å，`present_16` 是 `(N,)` bool，逐项对应模板原子。模板中的原子可能未沉积，实际保留以这个实例的present为准。

`CA2_blobs.npz/GT_blobs.npz` 的 `blob_index` 为 `(B,)` int32候选编号，`voxel_offsets` 为 `(B+1,)` int64切片边界；候选i的体素来自 `voxel_index_global_zyx[offsets[i]:offsets[i+1]]`，为 `(V_i,3)` int32全图ZYX索引。同长的 `source_probability` 是float32逐体素概率，`source_probability_mean`为 `(B,)` float32原均值。`blob_index`与数组下标不同，转换通过编号查表。

`templates/CCD_ATP.npz` 等文件名由 `object_key` 将冒号等非文件名字符换为下划线得到。`atoms` 为长度N的结构数组，`element/charge` 为int8元素原子序数及形式电荷；`bonds` 为长度M的结构数组，`atom_1/atom_2` 为int32零基原子下标，`type`为bool `(5,)` 原键类别。显示转换只使用这些字段及实例坐标。原模板还含：字符串标量 `smiles/name`、`(N,)` 字符串 `atom_names`、残基名字符串数组 `residue_names`、原始 `symmetries` 数组和object标量 `blobs`（可为None）；atoms内原编码 `name(4), chirality(7), in_ring(4)`、float32 `coords/ref_pos(3)`、bool `is_present`、int32 `residue_id`，bonds内bool `in_ring(4)`。这些原模板辅助字段保留原样，不用于本工程的实例完整性、身份判等或RMSD。

`assets/areas/occ_16.mrc` 和 `assets/blobs/CA2_blob_0.mrc` 是上述体素集合的**裁剪0/1掩码**：只把集合中的体素置1，其余置0，外围加一体素零边框；不是把整个包围盒填满。文件分别通过真实实例编号、条件加blob编号连接。

## 坐标与图像完整性

原NPY为(1,Z,Y,X) float32，MRC为(Z,Y,X)。原 `exp.npz.origin` 是全图体素边界下角的世界XYZ Å，记作o；`voxel_size`是XYZ Å/体素，记作s。完整地图的MRC头origin及scene的 `origin_xyz_A` 均为 `o+0.5*s`，表示首个采样中心。

裁剪图的起点t是全图中的**ZYX整数体素索引**，取掩码最小索引减1。裁剪图局部下标j也按ZYX排列，反序成XYZ后，世界采样中心为 `o + (reverse(t) + reverse(j) + 0.5) * s`；因此裁剪MRC的头origin为 `o+(reverse(t)+0.5)*s`。`*`是逐分量乘法，最终单位为Å。所有原子保持世界XYZ Å，不做平移或配准。

受体CIF写五位小数，C0等链名是token显示编号。参考SDF的present掩码去掉模板中未沉积的原子，只保留现有原子和现有键；不补原子、对齐或优化。RMSD直接引用原评价，不用显示文件重算。地图保持原采样值，网格、透明度、局部范围和step只用于显示；模拟地图起始阈值是固定抽样正值的85%分位数。

## 状态、来源与检查

“与预设一致”只检查面板管理的blob、pose、身份和正误标注的对象层级显隐，考虑父组。颜色、透明度、表示方式、相机和密度阈值不参与这个提示。受体、完整地图、真实配体和真实区域由用户独立控制。

`ligwork status` 返回pdb_id、config、status、extra、hidden、visible、manual_overrides。config含view/condition/budget/filter/pose及identity/correctness两个布尔标注开关；extra/hidden/visible是models.key列表；manual_overrides把手动改过的key映射为显隐布尔值。例：手动关闭CA2_blob_0后，manual_overrides含`{"CA2_blob_0":false}`，hidden含该key，status为“含手动显隐调整”。配置内过滤保留手动隐藏；切换模式/条件/预算清除当前人工显隐例外；CXS重开恢复实际保存状态。

`download_requests.json` 是remote/local字符串字典列表；source_receipt.json含passed、files、evaluation_metadata、map_checks。files逐项记录remote/local、bytes/sha256及server_bytes/server_sha256和passed；evaluation_metadata记录原评价文件、大小、散列；map_checks记录各图的ZYX形状、原值抽样相同及原点匹配。它证明输入复制与地图抽样，不代表可见界面或全部图片已经检查。

`view_index.json` 每项含pdb、view、command_file、image；局部另含occurrence_id、prediction_model、rmsd_A。prediction_model为null表示该条件在该预算下没有可展示的合法完整流水线构象，图片不得据此声称建模成功。

程序职责与阅读顺序见[代码阅读](代码阅读.md)，完整命令见[准备与重建](准备与重建.md)，完成范围见[执行记录](执行记录.md)。
