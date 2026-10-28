# Stage1 显式 level 全局到局部病例

本目录准备五个 PDB 的两行三列候选图，比较 LigandSeek-CA2 与显式提供 EMDB 推荐 level 的 Emap2lig-Find。保护病例 9BJJ、11JB、30GA 不进入候选。每套六视角来自同一个 PDB，a–c 为完整全局预测，d 为受体上的 Emap2lig 假阳性，e、f 为双方实际匹配到同一小分子的完整预测。

先读 `cases.json` 与病例输出的 `来源与模型.md`，再读任一 `tutorials/*.md`。代码按 `screen_test_set.py` → `screen_cases.py` → `prepare_assets.py` → `make_scenes.py` → `render_native.py` → `build_deck.mjs` 阅读；逐体素筛查与转换在相邻 `stage1-global-local/` 共用，旧 no_level 的默认来源与初始化快照保留。

## 五套案例入口

以下路径相对本 README；每个来源页均连接六份教程与六份最终会话。先打开初始会话，再按任一教程调节，即可学习该子图的完整形成过程。

| 病例 | 用途／当前 PPT 页 | 初始会话 | 原件追溯及六幅教程 |
| --- | --- | --- | --- |
| 9NVS | 正文 Fig. 3／第 9 页 | [initial.cxs](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9nvs/initial.cxs) | [来源与模型](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9nvs/来源与模型.md) |
| 9NAL | 备选／第 10 页 | [initial.cxs](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9nal/initial.cxs) | [来源与模型](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9nal/来源与模型.md) |
| 9UJF | 备选／第 11 页 | [initial.cxs](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9ujf/initial.cxs) | [来源与模型](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9ujf/来源与模型.md) |
| 9WFU | 备选／第 12 页 | [initial.cxs](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9wfu/initial.cxs) | [来源与模型](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9wfu/来源与模型.md) |
| 9X0X | 备选／第 13 页 | [initial.cxs](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9x0x/initial.cxs) | [来源与模型](../../output/stage1-level-global-local/explicit_emdb_level/scenes/9x0x/来源与模型.md) |

## 文件及科学产物

下列目录都相对论文仓库根。`<pdb>` 为 cases.json 中五个小写 PDB；`<view>` 为 a_reference、b_emap_global、c_ca2_global、d_receptor_fp、e_emap_local、f_ca2_local。

```text
## <科学产物>
画图/画图代码/stage1/visualization/stage1-level-global-local/
├─ cases.json                  # 五例的 occurrence、原生blob、角色与原生旋转角
├─ sources.json                # 五例在论文仓库中的显式条件来源目录
├─ screen_test_set.py           # 完整179-PDB元数据初筛，不局限已有可视化原件
├─ make_scenes.py               # 明文CXC及逐视角教程，不设置Python相机属性
├─ render_native.py             # ChimeraX执行CXC并读取显示状态
├─ build_deck.mjs               # 六张原生图与可编辑文字、框线、比例尺装配
└─ rebuild.ps1                 # 五套原件到会话的完整重建入口
画图/画图代码/stage1/output/stage1-level-global-local/explicit_emdb_level/
├─ sources/<pdb>/{data,cryo,emap,real}/ # GT公共材料、CA2/GT原预测及新level预测
├─ screening/                  # 每个保留blob的交集、匹配与受体距离证据
├─ screening_all.json           # 完整179条初筛与41候选，不等同最终合格病例
├─ prepared/<pdb>/assets/       # 全密度、完整掩码MRC、GT/CA2受体和沉积配体CIF
├─ prepared/<pdb>/evidence.json # 科学身份、局部指标、全部候选计数和所选FP
└─ scenes/<pdb>/
   ├─ initial.cxs              # 初始材料与固定模型编号，嵌入地图
   ├─ initial.cxc              # 初始加载及基础外观的原生命令
   ├─ 来源与模型.md             # 本例材料说明与编号表
   ├─ evidence.json            # prepared证据的同内容副本
   ├─ commands/<view>.cxc      # 从初始会话一步步到该子图的原生命令
   ├─ tutorials/<view>.md      # 同一命令块及逐步骤中文解释
   └─ views/<view>.{cxs,png}   # 最终原生会话与对应三维图

## <其他文件>
上述同一个output条件目录/
├─ metadata_source_receipt.json # 远端原件、大小与SHA256（来源证据）
├─ density_source_receipt.json  # 连续密度的原始身份（来源证据）
├─ local_reuse_receipt.json     # 只复用旧GT/CA2公共原件，不复用旧Emap（来源证据）
├─ session_reopen_verification.json # 35份嵌入地图会话的独立重开结果（验收）
├─ delivery_verification.json  # 病例身份、指标、完整重建、成图QA及旧资产保护（验收）
├─ word_publish_verification.json # 四份正文发布、Word标记/页面及最终旧资产保护（验收）
└─ scenes/<pdb>/
   ├─ view_state.json          # 相机、像素尺度、PPT定位框与完成状态（运行统计）
   ├─ chimerax.html            # 实际原生命令与错误（运行诊断）
   └─ my_sessions/             # 作者个人另存目录，重建不写（作者素材）
```

## 身份与指标

`cases.json` 是列表，每项 `pdb` 如 `9nvs`，`occurrence_id=1` 为原真实实例编号。`local_blobs={"cryo":1,"emap":2}` 分别是 CA2 与新条件 Emap2lig 的原生 blob 编号，不是评价行号。`receptor_fp_blob=3` 为独立假阳性；`remote_fp_blob=null` 明确表示本图不使用远处假阳性。`role=primary/candidate` 只选择展示角色，不改变候选或预测；`global_turns`、`local_turns`、`fp_turns` 为轴与角度列表，例如 `["y",35]` 是原生 turn y 35。

筛查沿用 `candidate_selected` 和双向覆盖 0.3 的一对一匹配。`matched_occurrence_id` 记录实际匹配到的实例；局部必须双方都匹配到同一个小分子。局部 Dice 为 2I/(P+G)，IoU 为 I/(P+G−I)，其中 I 是交集体素数，P/G 为预测／真值体素数。FP 附近距离按预测体素中心到沉积受体重原子计算，1.5 Å 邻近比例只描述空间位置，不替换评价规则。病例来源与科学定义在 evidence 中逐项保留。

全局使用所有保留预测的并集；显示不再按得分删选。a、b 背景为沉积受体，c 为 CA2 实际输入受体；e、f 分别使用两者相同世界位置的受体邻域。真实区域来自评价标签，不是 GT 受体输入下的预测。掩码为 ZYX；原子 XYZ Å；体素中心为 corner_origin+(index_xyz+0.5)×spacing。MRC 写首体素中心，裁零同步 origin，0.5 等值面 step 1，关闭平滑。

完整初筛的 `screening_all.json` 有 179 条 PDB 记录和 41 个候选，保留选择条件及保护病例表；它不宣称 41 例都满足局部形状优势或受体假阳性条件。两种方法全部保留预测及所选局部实例以进一步的原始体素核验为准。初始化保留的连续密度阈值为预处理 `contour_canonical`，不是原 EMDB level；受体 CIF 中的 token 编号也不是沉积 auth 编号，各例来源页给出两者区别。

## 原生操作与显示状态

初始化后所有外观、显隐、场景旋转、裁剪和保存均在 `.cxc` 中。Python 的 run 只分发这些原生命令；`render_native.py` 读取相机和边界，不直接修改模型或相机。`turn` 未指定 atoms 或单独 models，因此旋转整个显示场景，不改变模型内部的科学坐标。所有比较从同一个初始会话重开，a–c 共用完整视野，e/f 共用真值与两预测的并集视野。

`view_state.json` 顶层 `success` 是完成布尔值，`old_temp_read_guard` 是完整重建时文件审计是否启用。`views` 以 view 名为键；`camera_matrix` 为 (3,4) 相机姿态，`window_size` 为宽高像素，`pixel_size_A` 为当前视图 Å/像素。`boxes_fraction.fp/tp` 各为 (2,2)，依次是左上／右下归一化屏幕坐标，如 `[[0.2,0.3],[0.4,0.6]]`；它们用于PPT定位框，已包含原生场景旋转。来源图未经过截图裁改；PPT字母、框线、指标和比例尺保持独立可编辑。

## 完整重建

从仓库根运行，输出必须是新 temp 目录：

```powershell
& '画图/画图代码/stage1/visualization/stage1-level-global-local/rebuild.ps1' -OutputDirectory "$PWD/temp/stage1_level_rebuild_01"
```

依赖沿用 `D:/Anaconda/python.exe` 的 NumPy、SciPy、mrcfile、Biopython，以及 `D:/ChimeraX 1.10.1/bin/ChimeraX.exe`。仅原生进程调用与旧图共用 `转换工具/ops/rebuild_support/run_chimerax.ps1`；旧temp审计共用同目录 sitecustomize。五个 view_state 必须 success=true，且完整重建 old_temp_read_guard=true。正式PPT、作者已有会话和 my_sessions 不被重建覆盖。

任务范围和实际执行见[执行记录](../../../../../talk/stage1_level_visualization_20261027/执行记录.md)。当前图、PPT页和完整重建也在[所属追溯](../图表追溯.md)登记。
