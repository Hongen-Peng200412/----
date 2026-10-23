> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 端到端行动图：完整输入、Find、Match 与 Build

当前正式引用、冻结目录及图名以[阶段追溯](../../图表追溯.md)为准；本页保留基础v1的科学显示契约。当前 `prepare_flow_assets.py` 读取冻结 `e2e/output/e2e-flow/{source,views/source}/`，新资产写 `views/regenerated/`，新CXC写 `temp/e2e_flow/commands/`。`fetch_full_density.py` 的只读取数写 `temp/e2e_flow/refetched/`；这些工具不覆盖冻结来源。下述历史图集和页序不作为当前v3正式引用。

这套图将七个 CryoAtom2（CA2）受体条件下的同一批案例画成一条可阅读的行动链：**Input → Find → Match → Build**。Input 给出完整实验密度图与实际 CA2 受体；Find 在全局定位后展示局部区域；Match 独立展示所有候选 SMILES 的 RDKit 二维结构；Build 用受体、密度和沉积参考叠加三种外观展示同一个对接姿态。GT 指沉积结构和已有标注，只作为参考显示与既有评价依据。

三维图全部由 **UCSF ChimeraX 1.10.1 原生命令**制备；二维身份图由 **RDKit 2026.03.6** 制备。图中的预测始终是冻结 `local_cov-C` 第一次中心推理 `local-c1` 的原 self-ranking Top-1。图中各成功目标位点已有 50 个姿态、每姿态 100 步；本次制图不重新推理、不按 GT RMSD 重新排序。三种 Build 外观共用 `prediction.sdf` 的相同原子坐标和同一个局部相机。

本页保留基础v1的七页行动流程与科学字段。历史图集名和页序不作为当前正式路径；当前载体、图名和正文引用见[阶段追溯](../../图表追溯.md)。

## 图和数据在哪里

下列两棵树是同一组物理目录，分别列出科学图与事实、以及可再生辅助文件。`<pdb>` 仅表示七个目录：`9bjj`、`30ga`、`9llg`、`9rd8`、`9qru`、`9wup`、`9xzl`。

### 科学图与事实

```text
论文草稿/
├─ 画图/E2E案例可视化-端到端流程版.pptx         # 七页行动流程图集，图注在备注
└─ 画图/画图代码/e2e/output/e2e-flow/views/
   ├─ e2e-flow-<pdb>.png                        # 对应七页 PPT 的整页导出
   ├─ E2E案例可视化-端到端流程版.pdf             # 七页 PDF 预览
   ├─ <pdb>/
   │  ├─ data.json                            # 原冻结案例事实，附本次显示几何
   │  ├─ geometry.json                        # 完整地图网格、blob 模型号与坐标
   │  ├─ assets/
   │  │  ├─ full_density.mrc                  # 完整服务器实验图，不裁切或重采样
   │  │  ├─ density.mrc                       # 旧图保留的局部原值密度裁图
   │  │  ├─ ca2_receptor.cif                   # 实际 CA2 受体 token 原子
   │  │  ├─ gt_receptor.cif                    # 沉积受体 token 原子，仅作参考
   │  │  ├─ reference.sdf                     # 沉积目标配体重原子图与世界坐标
   │  │  ├─ prediction.sdf                    # 原 self-ranking Top-1 世界坐标姿态
   │  │  ├─ gt_area.mrc                       # 目标实例的冻结 GT 二值区域
   │  │  └─ blob_<编号>.mrc                    # 全部冻结 Find blob，各自保留原编号
   │  ├─ identities/
   │  │  ├─ identity_manifest.json            # 全身份轴、eligible 掩码与精确预测身份
   │  │  ├─ identity_XX.svg / .png             # 原身份下标 XX 的透明二维结构图
   │  │  └─ identity_XX_white.svg / .png       # 同一结构图的白底版本
   │  └─ renders/
   │     ├─ global_density.png                # Input：完整实验密度
   │     ├─ global_ca2.png                    # Input：实际 CA2 受体
   │     ├─ global_gt.png                     # 沉积受体与目标配体参考
   │     ├─ global_find.png                   # Find：完整地图、CA2 与全部冻结 blob
   │     ├─ local_gt.png                      # 沉积配体、GT 区域与 GT 受体局部参考
   │     ├─ local_find.png                    # 相同局部相机下的目标 blob、CA2 与密度
   │     ├─ blob_alone.png                    # Match 输入的目标 blob 单独显示
   │     ├─ dock_receptor.png                 # Build：同一 Top-1 与 CA2 受体环境
   │     ├─ dock_density.png                  # Build：同一 Top-1 与实验密度网格
   │     └─ dock_gt_overlay.png               # Build：同一 Top-1 与沉积参考叠加
   └─ source/<pdb>/
      ├─ exp.npy                             # 完整服务器规范化实验图，ZYX 数组
      └─ exp.npz                             # 原 origin、voxel_size、contour 元数据
```

`XX` 从 `00` 开始，严格对应 `prediction.identity_smiles` 的零基下标；七例共 22 个身份。30GA、9QRU 的 `renders` 另有 `background_gt.png`、`background_find.png`、`background_blob.png`，仅用于解释首个背景候选的邻域与计费事实。

| 页码 | 完整单例流程 | 图名批注 | 正文用途 |
| --- | --- | --- | --- |
| 1 | 9BJJ | `@@e2e-flow-9bjj` | 图12，首候选直接成功 |
| 2 | 30GA | `@@e2e-flow-30ga` | 图13，背景之后成功 |
| 3 | 9LLG | `@@e2e-flow-9llg` | 图14，多身份候选 |
| 4 | 9QRU | `@@e2e-flow-9qru` | 图15，背景之后的多身份候选 |
| 5 | 9RD8 | `@@e2e-flow-9rd8` | 备选 |
| 6 | 9WUP | `@@e2e-flow-9wup` | 备选，范围外前景免费跳过 |
| 7 | 9XZL | `@@e2e-flow-9xzl` | 备选，ion 免费跳过 |

### 辅助导出、复现与来源记录

```text
论文草稿/
├─ 画图/画图代码/e2e/visualization/e2e-flow-shared/base/
│  ├─ README.md                               # 本次图与字段契约、原生切换教程
│  ├─ 执行记录.md                             # 本次制图、文稿副本与验收状态（运行诊断）
│  ├─ <pdb>_reproduce.cxc                      # 每例完整原生加载与导图命令（可再生辅助导出）
│  ├─ fetch_full_density.py                   # 只读下载完整实验图（可再生工具输入）
│  ├─ prepare_flow_assets.py                  # 转换网格并写出明文 CXC（可再生工具输入）
│  ├─ draw_identities.py                      # 全身份 RDKit 二维绘图入口（可再生工具输入）
│  ├─ render_all.ps1                          # 隐藏窗口顺序执行七例原生制图（可再生工具输入）
│  └─ build_deck.mjs                          # 装配独立图像及可编辑流程对象（可再生工具输入）
├─ 画图/画图代码/e2e/output/e2e-flow/views/
│  ├─ full_density_manifest.json              # 七例原完整图来源、字节数与 SHA-256（运行诊断）
│  ├─ native_render_manifest.json             # 七例姿态SHA、相机和PNG完整性事实（运行诊断）
│  ├─ global_framing_manifest.json             # 全部受体原子与blob体素的全局取景核查（运行诊断）
│  ├─ source/<pdb>/source.json                 # 当前 PDB 的两个源文件校验记录（运行诊断）
│  └─ <pdb>/
│     ├─ global_session.cxs                   # 外部引用完整 MRC 的全局会话（可再生辅助导出）
│     ├─ session.cxs                          # 嵌入局部图与全部 blob 的会话（可再生辅助导出）
│     ├─ commands.html                        # 原生命令、相机矩阵与尺度日志（运行诊断）
│     ├─ global_commands.html                 # 最终全局受体与Find取景的原生记录（运行诊断）
│     ├─ camera.json                          # 原生日志中各命名视角的数值（运行诊断）
│     └─ assets/background_anchor.pdb          # 仅背景例的一点取景锚，不是真实原子（可再生工具输入）
└─ temp/
   ├─ e2e_flow/                               # 下载请求等临时文件（工具临时目录）
   └─ e2e_flow_20261003/                       # RDKit 依赖与图像检查（工具临时目录）
```

局部基础资产与冻结评价来源保存在 [旧案例产物](../../../output/e2e-flow/source)；本次 `data.json` 继承对应旧文件，新增 `visualization_geometry`，不改写已有预测与评价。

## 每个行动表达什么

| 行动 | 图中读者看到的证据 | 需要保留的科学含义 |
| --- | --- | --- |
| Input | 完整实验图与实际 CA2 受体；另列 GT 参考 | 密度与 CA2 是本案例条件；GT 参考不进入冻结推理输入 |
| Find | 完整地图中的全部冻结 blob，再看目标的局部 GT / Find 对照 | blob 形状、体素索引及原候选顺序均来自冻结产物；全图不能用旧局部裁图代替 |
| Match | 当前案例的全部 SMILES 身份，逐个 RDKit 化学图、eligible 状态及预测身份 | 身份清单来自已给定候选；Match 是独立身份选择行动；排除身份仍显示 |
| Build | 原 Top-1 的受体外观、密度外观与 GT 叠加外观 | 三张图表示同一次对接输出的显示变化；所示 RMSD 是该 Top-1 的已有评价 |

局部 GT / Find 两图和三张 Build 图共用 `local` 相机。GT 在制图时帮助确定可比较的参考显示范围，相机与透明度不会改变模型输入、分子坐标、候选排名或评价结果。

### 七个案例与候选路径

| PDB · 沉积目标 | 路径 | 目标 blob | 原候选次序 / 计费尝试 | eligible / 全身份 | Top-1 RMSD（Å） |
| --- | --- | ---: | --- | --- | ---: |
| 9BJJ · ATP，B:901 | 首候选直接成功 | 0 | 1 / 1 | 2 / 3 | 0.805 |
| 30GA · ATP，N:401 | 背景之后成功 | 1 | 2 / 2 | 1 / 2 | 1.036 |
| 9LLG · A1EKL，R:602 | 首候选直接成功 | 0 | 1 / 1 | 3 / 3 | 0.878 |
| 9RD8 · BCT，A:902 | 首候选直接成功 | 0 | 1 / 1 | 3 / 4 | 0.961 |
| 9QRU · A1JAX，B:2801 | 背景之后成功 | 1 | 2 / 2 | 2 / 3 | 0.633 |
| 9WUP · FMN，B:1103 | 两个范围外前景之后成功 | 2 | 3 / 1 | 4 / 4 | 0.524 |
| 9XZL · AGS，F:1001 | 一个范围外前景之后成功 | 1 | 2 / 1 | 1 / 3 | 0.912 |

`source_blob_index` 是从 0 开始的原 blob 编号，如 30GA 的目标为 `1`；`raw_rank` 是从 1 开始的冻结候选顺序，如该目标为 `2`；`attempt_index` 是实际计费尝试编号，如该目标也为 `2`。三者职责不同，不从模型显示编号推断候选次序。

30GA、9QRU 的首项为背景，消耗一次尝试，但本轮 Stage3 流程没有对背景实际运行 Match 或 Build。首项的参考邻域和 blob 截图是对既有事实的说明，不能画成“Matcher 识别背景再拒绝”的调用结果。9QRU 的目标 `candidate_selected=false`，仍在完整候选路径中实际进入 Match 与 Build。

9WUP 的前两项是 `small_molecule` 类别的真实前景，却不符合冻结 Stage3 的适用范围，免费跳过；不能称作非小分子。9XZL 的首项为 ion，同样免费跳过。它们的后续成功目标均是第一次计费尝试。`full_matcher_predictions` 中另有独立全配体 Matcher 对范围外身份的正确评价，不能合并成这轮 Stage3 实际执行过的调用链。

身份级 `eligible` 掩码与 blob / occurrence 级 `target_scope` 是不同的门禁。9WUP 的四个候选身份全部 `eligible=true`，仍不代表前两个候选 blob 满足这轮 Stage3 的适用范围。

30GA、9XZL 只有一个 eligible 身份，体现定位与构象重建，不能单独用于证明多身份区分能力。其余身份卡片也只呈现本例已有候选，不表示任意化学空间搜索。这些单例可视化的用途是解释具体路径；总体成功率以正文固定测试集评价为准。

## 先复现 9BJJ，再学习切换视图

启动 `D:/ChimeraX 1.10.1/bin/ChimeraX.exe`，通过 **Tools → General → Command Line** 显示命令栏。以下 `text` 代码块均在 ChimeraX 命令栏运行。

```text
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/visualization/e2e-flow-shared/base/9bjj_reproduce.cxc"
```

此命令先关闭当前模型，按固定顺序打开标准资产，生成全部三维 PNG 和两份会话。完整重建会覆盖该例可再生输出。只查看已有局部会话可用：

```text
close all
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9bjj/session.cxs"
windowsize 960 720
view local
```

`session.cxs` 使用 `includeMaps true` 嵌入局部密度与全部 blob；完整地图在生成局部会话前已关闭。查看完整地图时打开 `global_session.cxs`，该会话以 `includeMaps false` 引用独立 `assets/full_density.mrc`，因此移动文件时需一起保留资产目录。旧 UCSF Chimera 不能直接代替 ChimeraX 打开这些会话。

### 固定模型编号与配色

每例 `.cxc` 的 `close all` 与 `open` 顺序决定编号。不要在叠加其他模型后直接套用本表。

| 模型 | 文件 | 显示实体与颜色 |
| --- | --- | --- |
| #1 | `density.mrc` | 旧局部实验密度；Find 灰网格 `#a0a9ad`，Build 密度外观深灰蓝 `#516773` |
| #2 | `ca2_receptor.cif` | 完整 CA2 受体，绿 `#81a58b` |
| #3 | `reference.sdf` | 沉积目标参考，青绿 `#26a6a1` |
| #4 | `prediction.sdf` | 同一冻结 Top-1，蓝 `#3169b3` |
| #5 | `gt_area.mrc` | 目标 GT 二值区域，青绿 `#26a6a1` |
| #6 | `gt_receptor.cif` | 完整 GT 受体参考，绿 `#81a58b` |
| #7 起 | `blob_<编号>.mrc` | 按原 `blobs.npz.blob_index` 顺序加载全部 blob；目标橙 `#e9983c`，背景灰紫 `#9f87a9`，范围外前景灰褐 `#b3a290`，其余灰 `#cbd0d2` |
| #`7+B` | `full_density.mrc` | 完整原图，灰表面 `#8e9ca5`；`B` 为该例全部 blob 数 |
| #`8+B`，仅背景例 | `background_anchor.pdb` | 背景 blob 中心的一点显示锚，只用于选取邻域与取景，始终不作为结构证据 |

精确模型号见各例 `geometry.json.blobs[*].model_id`、`target_blob_model_id` 与 `models`。9BJJ 有 15 个 blob，对应 #7–#21，目标 #7，完整地图 #22。30GA 有 19 个 blob，对应 #7–#25，目标 #8，完整地图 #26，显示锚 #27。

| PDB | 全部 blob 数 B | 目标 blob 模型 | 完整地图模型 | 背景显示锚模型 |
| --- | ---: | --- | --- | --- |
| 9BJJ | 15 | #7 | #22 | 无 |
| 30GA | 19 | #8 | #26 | #27 |
| 9LLG | 3 | #7 | #10 | 无 |
| 9QRU | 4 | #8 | #11 | #12 |
| 9RD8 | 5 | #7 | #12 | 无 |
| 9WUP | 7 | #9 | #14 | 无 |
| 9XZL | 3 | #8 | #10 | 无 |

原实验密度的 `level` 使用 `contour_canonical`，如 9BJJ 为 `0.021095575764775276`；二值 blob 与 GT 区域统一 `level 0.5`。原子与键统一方法色，二维 RDKit 图保留常见元素色以便识别化学图，两种配色用途不同。

### 全局视图

9BJJ 的全局会话中，恢复输入外观并查看完整密度：

```text
hide models
volume #22 region all
volume unzone #22
volume #22 transparency 0.15
show #22 models
view global_density
```

实际 CA2 输入使用 `hide models; show #2 models; view global_structure`，GT 参考使用 `hide models; show #6,3 models; view global_structure`。二者共用围绕完整 CA2 与 GT 受体原子共同范围的相机，便于看清全结构。Find 使用：

```text
hide models
show #22,2,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21 models
volume #22 transparency 0.78
transparency #2 0 target c
view global_find
```

全局 Find 图用原生模型标签标出目标的原候选次序。9BJJ 在截图前执行：

```text
label #7 models text "1" color #ad6515 bgColor white height fixed size 24 offset 4,4,0 onTop true
```

其他案例的模型号取 `target_blob_model_id`，文本取 `handoff.raw_rank`，如 30GA 的 #8 标 `"2"`。标签是显示注释，不创建新科学模型或改变 blob 坐标。全局会话保留该标签；生成局部图前通过 `label delete #7 models` 删除，局部会话没有排名标签。

完整地图相机由 `view #22 orient` 复位，先 `turn y 25`，再 `turn x -20`，`view #22 pad 0.06` 后保存为 `global` 和 `global_density`，用于输入面板 a。受体面板 b/c 的 `global_structure` 与 Find 面板 d 的 `global_find` 都保持 Y 25° / X −20° 的朝向，但分别围绕完整受体、完整受体与全部 blob 的共同范围取景，使用 `pad 0.07`。它们与 a 的放大倍数不同，便于看清受体和目标位置。

建立后两个相机时，`.cxc` 暂时 `show #2,6 atoms` 以纳入全部受体原子范围，完成后 `hide #2,6 atoms` 恢复 cartoon 外观。显示的完整地图仍是 `region all`、`unzone`、`step 1`，没有生成新裁图；完整地图全景由 a 明确提供，d 将可视范围集中在完整受体与所有预测区域。其他案例替换完整地图模型号与全部 blob 模型号，精确命令以对应 `.cxc` 为准。

### 局部 GT 与 Find

在 9BJJ 局部会话中，先恢复受体与密度显示：

```text
hide #2,6 cartoons
hide #2,6 surfaces
hide #2,6 atoms
show (#2,6 & (#3 :< 6)) atoms
style #2,6 stick
size #2,6 stickRadius 0.055
transparency #2,6 45 target ab
volume zone #1 nearAtoms #3 range 4 newMap false minimalBounds true
volume #1 color #a0a9ad transparency 0.55
```

`#3 :< 6` 显示距离沉积参考任一原子 6 Å 内的完整受体残基，只限定制图范围；它不是正式中心口袋的残基质量中心 `<15 Å` 选袋规则。`newMap false` 不创建新地图，zone 只改变显示范围。

```text
hide models; show #3,5,6 models; view local
hide models; show #1,2,7 models; view local
hide models; show #7 models; view local
```

以上三行分别对应 `local_gt`、`local_find`、`blob_alone`。目标 blob 模型号需由各例 `target_blob_model_id` 读取。局部相机由 `view #3 orient` 复位，先绕 Y 旋转 35°，再绕 X 旋转 −25°，围绕 #3、#4 和目标 blob 的共同范围 `pad 0.25`，保存为 `local`。

### 同一个 Build 结果的三种外观

三维外观的完整命令在 `.cxc` 的 Dock 段。受体外观用实际 #2 与预测 #4，显示受体的 cartoon / surface；密度外观用 #1 与 #4；参考叠加用 #3 与 #4。执行这些切换时保持 `view local`，不对齐、不移动单个模型，也不重新优化姿态。

```text
hide models
hide #2 atoms
cartoon (#2 & (#3 :< 8))
transparency #2 68 target c
surface (#2 & (#3 :< 6)) enclose (#2 & (#3 :< 6)) color #81a58b transparency 78
show #2,4 models
view local
```

```text
hide #2 surfaces
hide #2 cartoons
hide models
volume #1 color #516773 transparency 0.12
show #1,4 models
view local
```

```text
hide models
show #3,4 models
view local
```

`hide models` 隐藏模型而不删除坐标。命名视角 `view local` 恢复相机，不恢复颜色、透明度、zone 或原子显示状态。改变 `transparency` / `volume` 后想恢复全部交付外观，重新打开会话或执行完整 `.cxc`。原子与 cartoon 的透明度用百分数，如 `68`；`volume transparency` 使用 0–1，如 `0.12`。

交付局部会话最终将密度透明度恢复为 `0.55`，保留 Build 的深灰蓝 `#516773`。重新导出 Find 局部图时，使用前文完整恢复命令显式改回 `#a0a9ad`；只输入 `view local` 不会撤销这些显示属性。

## Match 的完整身份轴与 RDKit 契约

### `identities/identity_manifest.json`

每例一个 JSON，身份数为 `I=prediction.identity_smiles` 的长度。`identities` 是长度 I 的列表，与原 `identity_smiles`、`small_molecule_answer_mask`、`identity_logits` 按下标逐项对齐。7 例共 22 个身份全部绘制，包括 `eligible=false`。

| PDB | 原身份顺序中的显示标签 | eligible 掩码 | 预测身份零基下标 |
| --- | --- | --- | ---: |
| 9BJJ | ATP / Identity2 / Identity3 | `[true,true,false]` | 0 |
| 30GA | ATP / Identity2 | `[true,false]` | 0 |
| 9LLG | Identity1 / A1EKL / Identity3 | `[true,true,true]` | 1 |
| 9QRU | A1JAX / Identity2 / Identity3 | `[true,true,false]` | 0 |
| 9RD8 | Identity1 / BCT / Identity3 / Identity4 | `[true,true,true,false]` | 1 |
| 9WUP | HEM / Identity2 / FMN / Identity4 | `[true,true,true,true]` | 2 |
| 9XZL | AGS / Identity2 / ZN | `[true,false,false]` | 0 |

| 字段 | 含义与真实示例 |
| --- | --- |
| `source_data_path` | 本例原冻结事实文件；9BJJ 指向旧目录 `9bjj/data.json` |
| `exact_predicted_smiles`、`prediction_source_field` | 原预测精确字符串，来源固定为 `prediction.predicted_smiles_small_molecule` |
| `matching_rule` | `exact_string_equality_against_prediction.identity_smiles_in_original_order`；逐字符匹配，保留原列表顺序 |
| `matched_identity_indices` | 唯一预测身份的零基下标；9BJJ 为 `[0]`，对应 `identity_00` |
| `identity_count`、`image_size_px`、`rdkit_version` | 9BJJ 分别为 `3`、`[1200,720]`、`"2026.03.6"` |
| `identity_index`、`smiles` | 原列表零基下标与未经改写的精确字符串；9BJJ 下标 `2` 是 `"[Mg+2]"` |
| `eligible` | 与 `small_molecule_answer_mask` 对齐的布尔值；9BJJ 为 `[true,true,false]`，false 身份仍绘成灰色化学图 |
| `matched` | 原预测字符串是否与当前身份完全相等；9BJJ 为 `[true,false,false]`，不使用 GT 或 RMSD 挑选 |
| `identity_logit` | 原始 logit，不是概率；9BJJ 第 0 项为 `-3.625`，第 2 项为 `-13.5625` |
| `ccd_label`、`display_label` | 可证的 CCD 标签，如 `"ATP"`；未证实标签为 `null`，显示中性名称，如 `"Identity3"` |
| `ccd_label_evidence` | 标签的精确来源关系；ATP 为 SMILES → occurrence `4` → `"CCD:ATP"`；未知身份为 `null` |
| `atom_count` | 二维展示原子数；ATP 为 `31`，`[Mg+2]` 为 `1` |
| `paths` | `transparent_svg`、`transparent_png`、`white_svg`、`white_png` 四个结构图的绝对路径 |
| `content_bbox_px` | 透明 PNG 中实际化学图的 `[left,top,right,bottom]` 像素边界，如 ATP 为 `[306,43,894,677]`；用于保持比例并去除空白，不改变分子图 |
| `chemical_graph` | 二维绘图的化学一致性审计，字段见下文 |

`chemical_graph` 的整数记录包含 `input_atom_count`、`display_atom_count`、`heavy_atom_count`、`removed_display_hydrogens`、`formal_charge`，例如 ATP 分别为 `47、31、31、16、0`；`[Mg+2]` 分别为 `1、1、1、0、2`。`input_declared_atom_stereo` / `display_declared_atom_stereo`、`input_declared_bond_stereo` / `display_declared_bond_stereo` 记录输入和展示图已声明的原子 / 键立体化学数，本批 22 个输入均未声明立体化学，不从三维结构补上手性。

以下是 9BJJ `identity_manifest.json.identities[2]` 的完整真实记录。它是 manifest 的一个身份片段，省略的是顶层元数据和另外两个身份，没有省略该身份字段：

```json
{
  "pdb": "9bjj",
  "identity_index": 2,
  "smiles": "[Mg+2]",
  "eligible": false,
  "matched": false,
  "identity_logit": -13.5625,
  "ccd_label": null,
  "display_label": "Identity3",
  "ccd_label_evidence": null,
  "atom_count": 1,
  "content_bbox_px": [555, 337, 645, 382],
  "chemical_graph": {
    "input_atom_count": 1,
    "display_atom_count": 1,
    "heavy_atom_count": 1,
    "removed_display_hydrogens": 0,
    "formal_charge": 2,
    "input_declared_atom_stereo": 0,
    "display_declared_atom_stereo": 0,
    "input_declared_bond_stereo": 0,
    "display_declared_bond_stereo": 0,
    "canonical_isomeric_smiles": "[Mg+2]",
    "remove_hs_roundtrip_isomorphic": true,
    "drawing_graph_isomorphic": true,
    "stereo_preserved": true,
    "no_new_stereo": true,
    "passed": true
  },
  "paths": {
    "transparent_svg": "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9bjj/identities/identity_02.svg",
    "transparent_png": "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9bjj/identities/identity_02.png",
    "white_svg": "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9bjj/identities/identity_02_white.svg",
    "white_png": "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9bjj/identities/identity_02_white.png"
  }
}
```

`canonical_isomeric_smiles` 是展示图的核查字符串，如 Mg 为 `"[Mg+2]"`，不替换原 `smiles`。`remove_hs_roundtrip_isomorphic` 检查标准删氢后重新加氢的双向化学图同构；`drawing_graph_isomorphic` 检查二维布局和绘图准备未改写元素、同位素、电荷、键型与已声明手性；`stereo_preserved`、`no_new_stereo` 检查立体化学保持且未新增；`passed` 是上述布尔审计均通过。本批 22 个身份的这些值均为 `true`。

RDKit 对展示分子标准移除可隐含的显式氢，再用 CoordGen 生成二维坐标；原精确字符串仍保存。二维坐标只服务结构图，不生成新三维构象。无源证据的身份保留 `IdentityN`，不根据形状猜测 CCD 名称。

七例共 88 个身份图文件，包含 44 个 SVG 与 44 个 PNG。SVG 可解析，PNG 均为 1200×720；透明与白底资产保留各自背景。HEM 的输入含两条 DATIVE 配位键，CoordGen 的提示不代表键被改写，化学图审计同时核对并保留这些输入键。

### 重绘二维身份图

在仓库根目录 PowerShell 使用本机 bundled Python 3.12 与此次已安装的 RDKit：

```powershell
$env:PYTHONPATH = 'C:/Users/15919/Desktop/论文草稿/temp/e2e_flow_20261003/rdkit_deps'
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/base/draw_identities.py' --source-root '画图/画图代码/e2e/output/e2e-flow/source' --output-root '画图/画图代码/e2e/output/e2e-flow/views/regenerated'
```

入口只绘图并核查完整身份轴。PPT 中身份标签、eligible 标记、预测边框和行动箭头是可编辑对象，结构图本体来自上述独立 SVG / PNG。

## 完整地图、局部裁图与世界坐标

### `geometry.json` 与 `data.json`

源数组按 **ZYX** 存放；原子与世界坐标按 **XYZ** 表示，单位 Å。`exp.npz.origin` 是体素边界角点，`voxel_size` 是实际 XYZ 间距。MRC 的 `header.origin` 写首采样点中心：

$$
O_{\mathrm{MRC}} = O_{\mathrm{corner}} + (s_{\mathrm{XYZ}}+0.5)\odot d_{\mathrm{XYZ}}.
$$

这里 $d$ 为逐轴 spacing，$s$ 是裁图起点，`crop_start_zyx` 重排得到 XYZ，$\odot$ 表示逐分量相乘。完整图的 $s=(0,0,0)$，没有裁图位移；原子坐标不再平移。

| PDB | 实际逐轴 spacing（Å） | 局部裁图起点 ZYX | 局部首采样点中心 XYZ（Å） |
| --- | ---: | --- | --- |
| 9BJJ | 1.001724124 | `[108,118,63]` | `[63.609482,118.704309,108.687067]` |
| 30GA | 0.997806966 | `[167,187,163]` | `[163.141439,187.088806,167.132667]` |
| 9LLG | 1.001538515 | `[102,91,79]` | `[79.622312,91.640774,102.657698]` |
| 9RD8 | 1.000806451 | `[74,106,106]` | `[106.585887,106.585887,74.560081]` |
| 9QRU | 1.001554251 | `[150,154,154]` | `[154.740132,154.740132,150.733915]` |
| 9WUP | 0.996033609 | `[71,91,77]` | `[77.192605,91.137075,71.216403]` |
| 9XZL | 0.999366522 | `[172,189,191]` | `[191.378689,189.379956,172.390725]` |

本批原 corner 均为 `[0,0,0]`。例如 9BJJ 的完整首中心为 `[0.500862062,0.500862062,0.500862062]` Å，完整 shape ZYX 为 `[232,232,232]`；30GA 为 `[456,456,456]`。原值与精度以 JSON 为准。

`geometry.json` 保存本次每例的完整显示几何：

| 字段 | 类型、单位及例子 |
| --- | --- |
| `full_source_shape_zyx`、`full_source_dtype` | 长度 3 的整数 shape 与原 dtype；9BJJ 为 `[232,232,232]`、`"float32"` |
| `full_source_corner_xyz_A`、`spacing_xyz_A`、`mrc_first_voxel_center_xyz_A` | 长度 3 的 XYZ 浮点向量，单位 Å；9BJJ 的 spacing 为 `[1.001724123954773,1.001724123954773,1.001724123954773]` |
| `contour_canonical`、`global_display_grid_step` | 原密度 level，如 `0.021095575764775276`；显示 grid step 为 `1` |
| `global_camera_fit_entities` | 三种全局相机的取景实体：`global_density` 为完整原图；`global_structure` 为全部 CA2 / GT 受体原子；`global_find` 为全部受体原子与全部冻结 blob |
| `blob_count_original`、`blobs` | 原全部 blob 数 B 与长度 B 的记录列表；9BJJ 为 `15` |
| `blobs[*].source_blob_index`、`model_id`、`file` | 原编号、ChimeraX 编号及资产名；9BJJ 首项为 `0`、`7`、`"blob_0.mrc"` |
| `voxel_count`、`source_probability_mean` | 当前 blob 的体素数与原分数；9BJJ 目标为 `384`、`0.9821481704711914` |
| `centroid_world_xyz_A` | 当前 blob 体素中心的平均 XYZ 世界坐标，单位 Å；9BJJ 目标约为 `[86.231753,141.441356,130.169357]` |
| `path_scope`、`color` | 本例路径分类和显示色；目标为 `"stage3_foreground"`、`"#e9983c"`；未进入展示路径的其他 blob 为 `null`、`"#cbd0d2"` |
| `models`、`target_blob_model_id` | 模型号字符串到显示实体的映射，以及目标 blob 的整数模型号；9BJJ 目标为 `7` |
| `background_anchor_model_id`、`background_scientific_actions` | 背景例为模型号及 `{"Match":false,"Dock":false}`；无背景时两项为 `null` |
| `global_find_annotation` | 全局目标的原生排名标签记录，包含 `kind="native ChimeraX model label"`、`target_blob_model_id`、`text` 与 `scientific_coordinates_changed=false`；9BJJ 对应 `7` 与 `"1"`，仅描述显示注释 |
| `dock_density_style` | 密度外观参数 `color="#516773"`、`transparency=0.12`；显示变化不改动密度采样值 |
| `prediction_sha256`、`full_density_source_sha256` | 预测 SDF 与原 `exp.npy` 的内容校验值，用于核查资产是否被替换 |

`data.json` 的 `prediction` 保留长度一致的候选字符串、logit 和布尔掩码；`handoff` 保留实际给 Build 的身份、中心与种子；`trace` 保留候选顺序及计费 / 跳过事实；`top1`、`predicted_sdf_index` 保留原排名首项和 SDF 索引；`method.pose_min_rmsd_A["1"]` 是所示 Top-1 的评价值，如 9BJJ 为 `0.8045425274739195` Å。`sample_index` 与 `sdf_index` 是不同字段，本批数值恰好一致也不将其混用。更详细的冻结字段说明见 [旧案例 README](../source_prepare/README.md)。

`full_density.mrc` 是原完整数组转换，`density.mrc` 是旧候选共同范围外围保留 16 Å 的原值裁图，二者没有重采样或重新归一化。二值 blob / GT MRC 外侧加零体素以形成闭合表面，不改动非零体素位置和数量。`ca2_receptor.cif` 与 `gt_receptor.cif` 保留 token 原子坐标；导出链名和残基号是可视化编号，沉积链位点以 `target_occurrence.components` 中的 `auth_asym_id` / `auth_seq_id` 为准。

### 源文件与重新准备三维资产

完整实验图来源为 `/storage/penghongen/AdaLigand/Ori_Data/density/<pdb>/exp.npy` 和 `exp.npz`。`full_density_manifest.json` 为长度 14 的列表，每项保存 `name`、`server`、`bytes`、`sha256`、`local`；例如 9BJJ `exp.npy` 为 `49948800` 字节，SHA-256 为 `5b1dd3510397d5fba15f3e619c680946cf63ee5766ee6966501e6ab80bb51d52`，`local` 指向 `source/9bjj/exp.npy`。各例 `source.json` 保存同例两个源文件的前四字段。

姿态与评价沿用 `/storage/penghongen/PocketXMol/final_evaluation/end_to_end/CA2/local_cov/test/local-c1/<pdb>/<source_blob_index>/`；Matcher 沿用旧 `data.json.source_paths.matcher`；逐文件旧资产来源与 SHA-256 见 [旧 source_manifest.json](../../../output/e2e-flow/source/source_manifest.json)。

日常打开交付会话无需下载。确需重新准备时，在仓库根目录 PowerShell 使用以下入口；它们只读冻结文件并转换格式：

```powershell
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/base/fetch_full_density.py'
& 'D:/Anaconda/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/base/prepare_flow_assets.py' --case 9bjj
```

七例分别准备后用 ChimeraX 打开对应 `<pdb>_reproduce.cxc`。Python 只加载、复制或转换科学资产，三维显示、相机和颜色继续由明文原生命令执行。

已有完整源图时，可批量准备并执行七例原生制图：

```powershell
powershell -NoProfile -File '画图/画图代码/e2e/visualization/e2e-flow-shared/base/render_all.ps1'
```

此入口检查每例应有的 PNG、两份会话与日志：背景例各 13 张，其余例各 10 张，共 76 张。控制台记录及启动用 CXC 统一保存在 `temp/e2e_flow/`。

### `camera.json` 与 `native_render_manifest.json`

每例 `camera.json` 以 `global_density`、`global_structure`、`global_find`、`local` 为视角键，`global` 保留为 `global_density` 的别名，30GA / 9QRU 另有 `background`。各键包含 `native_view_matrix_camera`（原生命令导出的 12 数字符串）、`native_zoom_pixel_size_A`（窗口像素的 Å/像素尺度）、`window_wh_pixels=[960,720]` 与 `export_wh_pixels=[1440,1080]`。各例实际尺度如下。

| PDB | global_density | global_structure | global_find | local | background |
| --- | ---: | ---: | ---: | ---: | ---: |
| 9BJJ | 0.473 | 0.284 | 0.284 | 0.0387 | 无 |
| 30GA | 0.888 | 0.468 | 0.468 | 0.0363 | 0.0466 |
| 9LLG | 0.359 | 0.176 | 0.176 | 0.0322 | 无 |
| 9QRU | 0.329 | 0.255 | 0.255 | 0.0483 | 0.0545 |
| 9RD8 | 0.195 | 0.200 | 0.200 | 0.0182 | 无 |
| 9WUP | 0.333 | 0.240 | 0.240 | 0.0356 | 无 |
| 9XZL | 0.229 | 0.283 | 0.283 | 0.0416 | 无 |

表中单位均为 Å/窗口像素；数值越小，单位世界距离在图中越大。9RD8、9XZL 的完整 CA2 / GT 受体共同范围比密度等值面原范围更大，因此结构相机尺度较大。各页 b/c 和 d 分别保留完整受体和全部 blob。

9BJJ 的 global / global_density 和 local 相机矩阵摘录如下：

```text
global: 0.90631,-0.14454,-0.39713,-111.51,-1.677e-09,0.93969,-0.34202,-79.487,0.42262,0.30998,0.85165,606.33
local:  0.81915,-0.2424,-0.51984,67.412,2.1727e-09,0.90631,-0.42262,126.38,0.57358,0.34619,0.7424,156.68
```

背景相机先以背景 blob `orient` 复位并旋转 Y 35° / X −25°，再围绕背景中心 8 Å 内的真实 CA2 / GT 受体残基取景，`pad 0.15`。三张背景图共用该相机，GT 背景图不显示目标配体。

根目录 `native_render_manifest.json` 是七例记录列表，每项有 `pdb`、`original_blob_count`、`same_frozen_top1_sha256`、`full_source_shape_zyx`、`camera`、`renders`。例如 9BJJ 的 Top-1 SHA-256 为 `a5ca297b29d739e3f5b6b860563be6360f2767cbf565a679e183208d1ff11e18`，与三种外观共同读取的 `prediction.sdf` 对应。`renders` 按文件名保存 `name`、`bytes`、`nonwhite_fraction` 与 `nonwhite_bbox_xyxy`，后者是 `[left,top,right,bottom]` 像素边界。9BJJ `blob_alone.png` 为 `42848` 字节，非白比例约 `0.104714`，边界 `[404,280,953,843]`。这些图像完整性事实用于制图检查，不作为模型质量指标。

`commands.html` 与 `global_commands.html` 分别保留完整 / 局部制图与最终全局取景的原生记录；`camera.json` 合并真实 `view matrix` 与 `zoom` 输出。当前 `<pdb>_reproduce.cxc` 和 `prepare_flow_assets.py` 已包含最终三种全局相机，完整复现仍只需一个 CXC 入口，不依赖增量检查脚本。

### `global_framing_manifest.json`

这是七例的数值取景核查。每项有 `pdb`、`camera_A_per_window_pixel` 和 `checks`。`checks` 的键指出相机与被核查实体，如 `"global_structure/ca2_receptor"`、`"global_find/all_blob_voxels"`；每个键保存 `window_bbox_xyxy`（960×720 窗口中的 `[left,top,right,bottom]` 投影像素边界）、`all_source_points_in_frame`（全部源点是否位于窗口）及 `source_point_count`（核查的原子或体素中心数）。

9BJJ 的 `global_structure/ca2_receptor` 核查 `26516` 个原子，边界约为 `[250.781425,97.969195,714.833149,613.652899]`；`global_find/all_blob_voxels` 核查全部 `5604` 个 blob 体素中心，边界约为 `[330.239878,210.005467,642.391295,541.735334]`。七例各项 `all_source_points_in_frame` 均为 `true`，用于核查完整受体 / 全部 blob 的取景，没有修改科学坐标或生成三维图形。

## 调整视角、导出与替换 PPT 图片

先回到交付视角，再做一个相机调整，并为自己的视角命名：

```text
view local
turn y 15
turn x -10
zoom 0.85
clip off
view name my_local
```

`turn` 单位为度；`zoom 0.85` 拉远，`zoom 1.15` 拉近，重复输入会累积。比较用局部图应统一切换到 `view my_local` 后导出。不要单独旋转、fit 或平移某个模型，这会改变预测、受体和密度的世界坐标关系。

```text
view matrix
zoom
wait 2
save "C:/Users/15919/Desktop/论文草稿/temp/my_e2e_flow.png" width 1440 height 1080 supersample 2
save "C:/Users/15919/Desktop/论文草稿/temp/my_e2e_flow.cxs" includeMaps true
```

`view matrix` 与 `zoom` 的实际输出在各例 `commands.html` 中留证。相机矩阵按行包含 12 个数字，第 4、8、12 项是平移；精确重建还需要正交相机、窗口尺寸与 Å/像素尺度，打开 `.cxs` 并调用命名视角会一起恢复。三维输出为 4:3、1440×1080 像素、两倍超采样。

在 PPT 选中对应独立视图，使用 **图片格式 → 更改图片 → 来自文件** 替换 PNG，保留比例。结构图可用 SVG 或 PNG；行动名称、箭头、身份框、身份标签与指标在 PPT 中直接编辑。全局 Find 的目标排名标签由 ChimeraX 原生命令生成，若要改其字体或偏移，修改 `.cxc` 的 `label` 命令后重新导出。标签附着于实际 blob 模型，会随相机一起重新投影；本版 PPT 的连接线仅表示行动顺序，不定位三维原子或体素。

已完成科学视图后，可在仓库根目录重建完整图集：

```powershell
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/base/build_deck.mjs'
```

`build_deck.mjs` 在 `temp/e2e_flow_20261003/` 生成带独立图名和备注的候选，结构检查后的新PPT保存在 `e2e/output/e2e-flow/regenerated/views/`。画布为1800×1940排版像素，与分子XYZ Å世界坐标无关。

旧 [publish_ppt.ps1](../../../../archive/visualization/publication-history/e2e/e2e-flow-shared/base/publish_ppt.ps1) 已归档，仅保留历史发布过程。当前构造器已自行写入图名；旧脚本会重复追加批注并覆盖正式图集，不作为当前调用入口。

同目录的 `deck_manifest.json` 是长度 7 的页序列表。每页有 `name`（如 `"e2e-flow-9bjj"`）、`pdb`、`caption`、`panels`、`identities`、`final_physical_width_mm=183`。`panels` 按图片插入顺序记录 `key`（如 `"global_density"`）、`letter`（如 `"a"`）、`rectangle_px=[x,y,width,height]`（9BJJ 首面板为 `[130,262,480,255]`）与 `source_path`。`identities` 保留 `identity_index`、精确 `smiles`、`eligible`、`matched`、`chemical_graph_passed`，用于核对 PPT 与原身份轴，没有生成新科学评价。

PPT 每页一个成品图，独立 `@@图名` 批注用于定位，备注保存图注；其他来源批注不进入正文。正文引用、Word 导图与回转约定见 [转换工具 README](../../../../../../转换工具/README.md)。图注应说明对应候选路径、eligible 身份数、所示 Top-1 与 GT 参考用途，避免将显示切换写成三次预测。

这里保留基础v1的图与字段契约；当前正式图集、正文引用和双语图注以[阶段追溯](../../图表追溯.md)为准。

Word编译使用[统一转换工具](../../../../../../转换工具/README.md)。旧 [fit_word_layout.py](../../../../archive/visualization/e2e-word-layout/e2e-flow-shared/base/fit_word_layout.py) 已归档，不在当前转换后运行；固定148 mm缩图只属于当时的历史副本。

本次制图与 Word 副本的完成状态、生成命令和验收事实见 [执行记录](执行记录.md)。本 README 保存稳定字段与复现方法；逐次检查过程保存到执行记录及 `temp/`。
