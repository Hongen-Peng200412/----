> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 端到端案例图：从冻结结果到可复现的 ChimeraX 视图

本目录是当前端到端图的来源准备组件，正式引用见[阶段追溯](../../图表追溯.md)。`prepare_data.py` 默认只读 `e2e/output/e2e-flow/source/source/<pdb>/`，新格式转换资产写 `source/regenerated/<pdb>/`；`fetch_data.py` 重新取数时写 `temp/e2e_cases/refetched/`。当前七例配置 `cases.json` 保持原身份和顺序，服务器取数不属于日常离线绘图。本页以下说明原始来源包的字段与三维显示契约，旧图集名不是当前正文载体。

这套图展示七个 CryoAtom2 受体条件下的 **Find → Match → Build** 案例。分子、受体、密度与 blob 的显示全部由原生 **UCSF ChimeraX 1.10.1** 命令制备；Python 只提取冻结产物、转换文件格式与整理事实。每例有一份完整重建命令、一份含地图的三维会话和八张独立 PNG。原始案例布局的文字和箭头可在PPT中编辑，分子与密度在ChimeraX中编辑；当前正文载体和稳定图名见[阶段追溯](../../图表追溯.md)。

图中的姿态始终取本轮 `local_cov-C` 第一次中心推理 `local-c1` 的原 self-ranking **Top-1**。每候选已有 50 个姿态、每姿态 100 步；这里不重新推理、不挑选 RMSD 最低姿态，不使用第二次 C 或 E 的结果。

## 先用一分钟复现一个案例

1. 启动 `D:/ChimeraX 1.10.1/bin/ChimeraX.exe`。旧版 UCSF Chimera 不能直接打开 `.cxs`。
2. 通过 **Tools → General → Command Line** 显示命令栏。下列代码块中的命令都输入在这里，不是 PowerShell 或 Python。
3. 打开 [9BJJ 完整命令](9bjj_reproduce.cxc)，或粘贴这一行：

```text
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/visualization/e2e-flow-shared/source_prepare/9bjj_reproduce.cxc"
```

它先关闭当前模型，按固定顺序打开基础资产，依次生成八张 PNG，最后保存会话并停在 GT 与 Top-1 姿态叠加图。命令中没有自定义别名，也没有用 Python 控制颜色或相机。完整重建会覆盖该例的可再生 PNG 与会话，个人修改请另存。

已有会话也可以直接打开：

```text
close all
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/source/9bjj/session.cxs"
windowsize 960 720
view local
```

`includeMaps true` 已将地图嵌入会话。使用保存的会话查看不需要服务器，也不依赖原 MRC 仍在原位置。

## 产物位置与七个案例

```text
论文草稿/
├─ 画图/E2E案例可视化.pptx                     # 论文图集，图注在幻灯片备注
├─ 画图/画图代码/e2e/visualization/e2e-flow-shared/source_prepare/
│  ├─ README.md                               # 原生命令复现与调整教程
│  ├─ cases.json                              # 七例的 PDB、目标 blob 与案例分组
│  ├─ <pdb>_reproduce.cxc                      # 每例完整加载、显示、相机与导图命令
│  ├─ fetch_data.py                           # 只读下载冻结资产，不运行模型
│  ├─ prepare_data.py                         # 数组转换为 MRC，原子转换为 CIF/SDF
│  └─ build_deck.mjs                          # 将已导出图像与可编辑文字、箭头装配为 PPT
├─ 画图/画图代码/e2e/output/e2e-flow/source/
│  ├─ cases_summary.json                      # 七例身份数、配体信息与 Top-1 RMSD
│  ├─ source_manifest.json                    # 原始文件来源、字节数与 SHA-256
│  ├─ source/<pdb>/                           # 下载的原数组、排名、轨迹与文件来源
│  └─ <pdb>/
│     ├─ data.json                            # 当前案例事实、坐标规则与模型加载顺序
│     ├─ assets/                              # ChimeraX 直接打开的 MRC、CIF 和 SDF
│     ├─ session.cxs                          # 含地图、模型、配色和命名视角的会话
│     ├─ commands.html                        # 原生命令、相机矩阵和尺度的真实导出日志
│     └─ renders/                             # 八张 1440×1080 PNG
└─ temp/e2e_cases/                            # 下载、渲染与检查的临时文件
```

`<pdb>` 只表示以下七个目录：`9bjj`、`30ga`、`9llg`、`9rd8`、`9qru`、`9wup`、`9xzl`。每例只有一份贯穿全部视图的会话。

PPT 共十页，前三页按候选路径组合案例，后七页逐例展示 `find`、`identity`、`pose`、`local_gt`、`local_find` 五类视图。另三张输入 PNG（`input_density`、`input_ca2`、`input_gt`）独立提供，不插入 PPT 详页：

| 页码 | 图名或案例 | 页面用途 | 正文引用 |
| --- | --- | --- | --- |
| 1 | `e2e-cases-main`：9BJJ / 30GA | 直接成功与背景之后成功的主图 | 图12 |
| 2 | `e2e-cases-multi-identity`：9LLG / 9QRU | 含多个合格小分子身份的补充案例 | 图13 |
| 3 | `e2e-cases-scope`：9WUP / 9XZL | 适用范围门禁的备选组合 | 不插入正文 |
| 4 | 9BJJ 详页 | 七例中第一例的五类视图与来源 | 不插入正文 |
| 5 | 30GA 详页 | 七例中第二例的五类视图与来源 | 不插入正文 |
| 6 | 9LLG 详页 | 七例中第三例的五类视图与来源 | 不插入正文 |
| 7 | 9RD8 详页 | 七例中第四例的五类视图与来源 | 不插入正文 |
| 8 | 9QRU 详页 | 七例中第五例的五类视图与来源 | 不插入正文 |
| 9 | 9WUP 详页 | 七例中第六例的五类视图与来源 | 不插入正文 |
| 10 | 9XZL 详页 | 七例中第七例的五类视图与来源 | 不插入正文 |

| PDB与沉积配体 | 路径类型 | 成功 blob 编号 | 原候选次序 / 计费尝试 | selected | 合格小分子身份数 / 全部身份数 | Top-1 RMSD（Å） | 完整命令 |
| --- | --- | ---: | --- | --- | --- | ---: | --- |
| 9BJJ · ATP，B:901 | 首候选直接成功 | 0 | 1 / 1 | true | 2 / 3 | 0.805 | [9bjj_reproduce.cxc](9bjj_reproduce.cxc) |
| 30GA · ATP，N:401 | 背景之后成功 | 1 | 2 / 2 | true | 1 / 2 | 1.036 | [30ga_reproduce.cxc](30ga_reproduce.cxc) |
| 9LLG · A1EKL，R:602 | 首候选直接成功 | 0 | 1 / 1 | true | 3 / 3 | 0.878 | [9llg_reproduce.cxc](9llg_reproduce.cxc) |
| 9RD8 · BCT，A:902 | 首候选直接成功 | 0 | 1 / 1 | true | 3 / 4 | 0.961 | [9rd8_reproduce.cxc](9rd8_reproduce.cxc) |
| 9QRU · A1JAX，B:2801 | 背景之后成功 | 1 | 2 / 2 | false | 2 / 3 | 0.633 | [9qru_reproduce.cxc](9qru_reproduce.cxc) |
| 9WUP · FMN，B:1103 | 两个范围外前景之后成功 | 2 | 3 / 1 | true | 4 / 4 | 0.524 | [9wup_reproduce.cxc](9wup_reproduce.cxc) |
| 9XZL · AGS，F:1001 | 一个范围外前景之后成功 | 1 | 2 / 1 | true | 1 / 3 | 0.912 | [9xzl_reproduce.cxc](9xzl_reproduce.cxc) |

`source_blob_index` 是原始 blob 编号，从 0 开始；`raw_rank` 是冻结候选顺序，从 1 开始，二者不是同一字段。`attempt_index` 是实际计费尝试数。例如 9WUP 的第三个候选是第一次计费尝试，因为前两项由适用范围门禁免费跳过。`selected=false` 也不代表没有评价：9QRU 的第二项来自完整候选顺序，实际进入了 Match 与 Build。

“合格小分子身份数”是 `prediction.small_molecule_answer_mask` 中 true 的个数；全部身份数是 `prediction.identity_smiles` 的长度。身份来自该 PDB 已提供的候选 SMILES 清单。30GA 和 9XZL 都只有一个合格小分子身份，应理解为定位与构象重建案例，不用它们证明多身份区分能力。

### 三种路径如何读

- **直接成功**：9BJJ、9LLG、9RD8 的首个候选处于冻结 Stage3 范围，Match 身份正确，已有 self-ranking Top-1 姿态的 RMSD 小于 2 Å。
- **背景之后成功**：30GA 和 9QRU 的首项是背景，消耗一次尝试；第二项匹配身份并重建成功。本轮 Stage3 流程没有对背景运行 Match 或 Build，图中的背景标记是评价事实，不是模型识别并拒绝背景的展示。
- **范围外前景之后成功**：9WUP 前两项均是 `small_molecule` 类别的真实前景，但不符合冻结 Stage3 适用范围，免费跳过；不能称为“非小分子”。9XZL 首项是 ion，亦免费跳过。两例后续小分子候选成功，仍是第一次计费尝试。

`data.json.full_matcher_predictions` 另外保留全配体 Matcher 评价事实：9WUP 前两项正确匹配含铁配体身份，9XZL 首项正确匹配 `[Zn+2]`。该事实来自单独的 `final_smiles/strongest-1/frozen_test.json`，不是本轮 Stage3 的实际 Match 调用。两种来源应分别解释，不能拼成一条实际执行过的调用链。

这些图说明不同候选路径的具体表现。总体成功率仍以正文中固定测试集的评价为准。

## 模型编号、基础文件和颜色

编号来自 `.cxc` 的固定 `open` 顺序。每次先 `close all`，不要叠加另一 PDB 后再照抄编号。

| 模型 | 基础文件 | 表示的实体 | 交付颜色 |
| --- | --- | --- | --- |
| #1 | `assets/density.mrc` | 候选附近的原值实验密度裁图 | 灰网格 `#a0a9ad` |
| #2 | `assets/ca2_receptor.cif` | 实际 CA2 受体 token 原子 | 绿 `#81a58b` |
| #3 | `assets/reference.sdf` | 沉积参考配体的重原子图与世界坐标 | 青绿 `#26a6a1` |
| #4 | `assets/prediction.sdf` | 原 self-ranking Top-1 世界坐标姿态 | 蓝 `#3169b3` |
| #5 | `assets/gt_area.mrc` | 该实例的冻结 GT 配体区域，二值体素 | 青绿网格 `#26a6a1` |
| #6 | `assets/gt_receptor.cif` | 真实受体 token 原子，仅作参考显示 | 绿 `#81a58b` |
| #7 起 | `assets/blob_<编号>.mrc` | 按原顺序展示的冻结 Find blob，二值体素 | 目标橙色 `#e9983c`，背景灰紫 `#9f87a9`，范围外前景灰褐 `#b4aa96` |

具体 blob 模型编号如下。overview 显示表中该例的全部候选；local_find 只显示“目标模型”列中的一个 blob，其他候选隐藏：

| PDB | #7 | #8 | #9 | 目标模型 |
| --- | --- | --- | --- | --- |
| 9BJJ、9LLG、9RD8 | blob 0，目标 | 无 | 无 | #7 |
| 30GA、9QRU | blob 0，背景 | blob 1，目标 | 无 | #8 |
| 9WUP | blob 0，范围外前景 | blob 1，范围外前景 | blob 2，目标 | #9 |
| 9XZL | blob 0，范围外前景 | blob 1，目标 | 无 | #8 |

密度 `level` 使用各例源元数据的 `contour_canonical`；二值 blob 与 GT 区域使用 0.5，不是可按案例优化的阈值。`data.json.contour` 与完整 `.cxc` 中保存了精确数值。

`ca2_receptor.cif` 与 `gt_receptor.cif` 由 token 原子导出，坐标保留原值；链名 `C0`、`C1` 及残基序号是可视化编号。上表病例身份仍取 `target_occurrence.components` 的沉积 `auth_asym_id` 与 `auth_seq_id`，不能根据导出 CIF 的新编号反推沉积残基号。

## 八张图如何从同一会话切换

`overview`、`local`、`identity` 是保存的视角名称，不是自定义命令别名。`hide models` 只隐藏模型，不删除数据；`view local` 恢复相机和保存的模型位置，不重置颜色、密度区域、透明度或原子 / cartoon 的显示范围。

### 1. 输入与 Find：共享 overview

会话最后停在局部图，因此要先恢复完整受体 cartoon 和未 zone 的显示密度，再切换这组图：

```text
hide #2,6 atoms
cartoon #2,6
transparency #2,6 45 target c
volume unzone #1
volume #1 region all
volume #1 transparency 0.45
```

**实验密度输入视图：**

```text
hide models; show #1 models; view overview
```

**实际 CA2 受体输入视图：**

```text
hide models; show #2 models; view overview
```

**GT 受体参考视图：**

```text
hide models; show #6 models; view overview
```

**Find 视图，以 9BJJ 为例：**

```text
hide models
show #1,2,7 models
transparency #2,6 70 target c
volume #1 transparency 0.75
volume #7 transparency 0.10
view overview
```

30GA、9QRU 和 9XZL 改为 `show #1,2,7,8 models`，并将 blob 透明度命令改为 `volume #7,8 transparency 0.10`；9WUP 分别使用 `show #1,2,7,8,9 models` 和 `volume #7,8,9 transparency 0.10`。Find 图将受体 cartoon 设为 70% 透明、密度网格设为 75% 透明，blob 仅 10% 透明，让候选边界更突出。

这组图的相机由所展示的冻结 blob 共同范围确定，旋转为先 `turn y 25`，再 `turn x -20`；完整命令中有明确的 `view ... pad 0.14`。

`input_density.png` 展示的是包含全部展示 blob、外围保留 16 Å 的密度裁图，**不是整幅原密度图**。`input_ca2.png` 与 `input_gt.png` 也沿用这个候选范围相机，完整受体模型仍保存在会话中。若想观察整条受体，可另用 `view #2`，并将个人视角另命名。

### 2. GT 区域、局部 Find 与最终姿态：共享 local

从 overview 回到局部时，先恢复用于画图的受体显示范围和密度 zone：

```text
hide #2,6 cartoons
hide #2,6 atoms
show (#2,6 & (#3 :< 6)) atoms
style #2,6 stick
size #2,6 stickRadius 0.055
transparency #2,6 50 target ab
volume zone #1 nearAtoms #3 range 4 newMap false minimalBounds true
volume #1 transparency 0.45
```

`#3 :< 6` 显示距参考配体任一原子 6 Å 内的完整受体残基，采用统一绿色的纤细 stick，半径 0.055 Å、50% 透明；局部图不显示 cartoon，避免带状受体遮住配体。这只是图像显示范围，不是正式中心口袋的残基质量中心 `<15 Å` 选袋规则。`volume zone` 限制密度网格的显示区域，`newMap false` 不创建新密度；原 MRC 数值保持不变。

**沉积配体、GT 区域及 GT 受体参考：**

```text
hide models; show #3,5,6 models; view local
```

**局部 Find，以 9BJJ 为例：**

```text
hide models; show #1,2,7 models; view local
```

30GA、9QRU 和 9XZL 仅显示目标 #8，使用 `hide models; show #1,2,8 models; view local`；9WUP 仅显示目标 #9，使用 `hide models; show #1,2,9 models; view local`。9LLG 与 9RD8 的目标同样为 #7，沿用 9BJJ 命令。这里不沿用 overview 的全部候选集合；原目标 blob 不被 `volume zone` 改写。

**CA2 受体、实验密度与 GT / Top-1 姿态叠加：**

```text
hide models; show #1,2,3,4 models; view local
```

这三张图共用一个相机与尺度。它由 `view #3 orient` 复位方向，先绕 Y 旋转 35°，再绕 X 旋转 −25°，用 `view #3,4 pad 0.12` 围绕 #3 和 #4 的共同范围取景，最后 `clip off; view name local`。局部密度透明度为 45%，blob 沿用 Find 图的 10%。GT 配体只用于参考显示及已有评价，不进入冻结推理输入，也不用于选择 Top-1。

### 3. Match 身份示意：identity

```text
hide models; show #4 models; view identity
```

这张图仅显示 #4 的分子图，配合 PPT 中的真实 CCD 身份与匹配标签。它复用已保存 Top-1 分子作为身份图示，不表示另一轮推理、不表示二维化学结构图，也不使用额外生成的构象。完整精确 SMILES 保存在 `data.json.handoff.prepared_smiles`；如 9BJJ 的预测与目标字符串完全一致。

对应八张输出：

| 文件 | 视角 | 显示内容 |
| --- | --- | --- |
| `renders/input_density.png` | overview | 候选附近的实验密度 |
| `renders/input_ca2.png` | overview | 实际 CA2 受体 |
| `renders/input_gt.png` | overview | GT 受体参考 |
| `renders/find.png` | overview | 实验密度、CA2 与所展示的原 blob |
| `renders/local_gt.png` | local | 沉积配体、GT 区域与 GT 受体 |
| `renders/local_find.png` | local | 实验密度、CA2 与唯一目标 blob |
| `renders/pose.png` | local | 实验密度、CA2、沉积配体与 Top-1 姿态 |
| `renders/identity.png` | identity | 匹配身份的单分子示意 |

## 怎样调整视角、颜色和保存自己的图

### 调整相机，不移动单个模型

先回到交付相机，再试一个调整：

```text
view local
turn y 15
turn x -10
zoom 0.85
clip off
view name my_local
```

`turn` 单位为度；`zoom 0.85` 拉远，`zoom 1.15` 拉近，连续输入会累积。回到 `view local` 可重新从基准尝试。不要单独旋转或 fit 某个分子，否则预测、受体和实验密度原来的世界坐标关系会被改变。

将三张局部图的 `view local` 都替换为 `view my_local`，用新公共视角重新导出。不能只改变 GT 图或预测图的角度后作对比。

需要数值留证时输入：

```text
view matrix
zoom
```

Log 显示相机的 3×4 矩阵及当前 Å/像素尺度。各例真实运行日志已保存为 `commands.html`，如 [9BJJ 原生命令日志](../../../output/e2e-flow/source/9bjj/commands.html)，可在浏览器查看命令及相机数值。`view matrix camera` 的参数是按行排列的 12 个逗号分隔数字，其中第 4、8、12 项为平移。矩阵不保存正交视野宽度；精确复现还须保留 `camera ortho`、`windowsize 960 720` 和对应 `zoom pixelSize`。直接打开交付 `.cxs` 并调用命名视角会同时恢复相机位置与视野宽度。

### 统一方法色，避免元素色混入

```text
color #2,6 #81a58b target c
color #2,6 #81a58b target ab
color #3 #26a6a1 target ab
color #4 #3169b3 target ab
size #3,4 stickRadius 0.18
volume #1 color #a0a9ad transparency 0.45
```

`target c` 指受体 cartoon，`target ab` 指原子与键。配体所有重原子统一颜色，不执行 `byelement`，因此不会出现未经定义的氧红、氮蓝或磷黄。绿色受体和灰网格各自提供环境与密度参照。

注意透明度单位：`transparency #2 50 target ab` 是 50%，而 `volume #1 transparency 0.45` 是 45%。提高数值会更透明。overview 的输入受体 cartoon 为 45% 透明，Find 中为 70%；local 的受体 stick 为 50%，三者分别恢复。改变颜色和透明度不会被 `view local` 撤回；要恢复全部交付外观，重新打开原会话或执行完整 `.cxc`。

### 保存 PNG 与练习会话

切到所需视图后，在 ChimeraX 命令栏输入：

```text
wait 2
save "C:/Users/15919/Desktop/论文草稿/temp/my_e2e_pose.png" width 1440 height 1080 supersample 2
save "C:/Users/15919/Desktop/论文草稿/temp/my_e2e_session.cxs" includeMaps true
```

八张交付 PNG 都用 4:3 比例、1440×1080 像素和两倍超采样。三维内容保持在 ChimeraX 中；图内的排序文字、路径箭头、PDB 与指标由 PPT 添加，避免把文字固化进分子截图。

## 坐标、数组和冻结来源如何核对

源密度数组按 **ZYX** 存放，世界坐标按 **XYZ** 表示，单位 Å。源元数据 `origin` 为体素边界角点，`voxel_size` 为实际逐轴间距，不固定为 1 Å。显示裁块首体素中心为：

$$
O_{\mathrm{MRC}}=O_{\mathrm{corner}}+(s_{\mathrm{XYZ}}+0.5)\odot d_{\mathrm{XYZ}}.
$$

其中 $s$ 是显示裁块起点，`crop_start_zyx` 重排后得到 XYZ；$d$ 是源 spacing；$\odot$ 表示逐分量乘法。MRC 的 `header.origin` 写首采样点中心，原子坐标不再平移。9BJJ 的实际 spacing 为每轴约 1.001724 Å，显示起点 ZYX 为 `[108,118,63]`，首中心 XYZ 约为 `[63.609482,118.704309,108.687067]` Å。这些数值可在 [9BJJ data.json](../../../output/e2e-flow/source/9bjj/data.json) 核对。

`density.mrc` 是原采样值切片，没有重采样或重新归一化。二值 blob / GT MRC 按原体素索引导出，外侧加两层零体素方便生成闭合显示表面；非零体素的数量与世界位置不变。透明度、mesh 与相机只改变看法，不改变冻结评价。

每例 `data.json` 按职责保留以下事实：

- `handoff`：实际匹配后交给 Build 的记录，包括目标 SMILES、原 blob 编号、给定中心和种子；例如 9BJJ 的 `source_blob_index=0`、`matched_occurrence_id=4`。
- `trace`：到目标候选为止的原候选路径、计费状态与完整四阶段既有评价；例如 30GA 的首项 `action=spend_background`，第二项为 `spend_stage3_target`。
- `prediction`：本轮 Stage3 Matcher 的候选身份列表、原 logits、合格小身份掩码与预测精确 SMILES。
- `full_matcher_predictions`：单独全配体 Matcher 评价的对应事实，用于解释范围外候选，不替代本轮调用轨迹。
- `top1`、`predicted_sdf_index`：冻结排名首位及其在原 `poses.sdf` 中的零基记录索引。`sample_index` 与 `sdf_index` 是不同字段，提取使用后者；9BJJ 两者恰好均为 21。
- `method`：本轮 `local_cov-C` 的最终评价，例如 `pose_min_rmsd_A["1"]=0.804542527...`。这是所示 Top-1 的 RMSD。
- `files`、`blobs`、`density_grid`、`contour`：标准文件加载顺序、原 blob 的分数与体素数、坐标参数和原密度阈值。
- `source_paths`：实际服务器冻结产物位置。

共同来源为：

```text
/storage/penghongen/PocketXMol/final_evaluation/end_to_end/CA2/
  evaluation.json
  inputs/base.jsonl
  local_cov/test/local-c1/<pdb>/<source_blob_index>/

/storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/strongest-1/
  train_strongest1_revised_job378587_20260920T230727/evaluation.json

/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json
```

逐文件路径与 SHA-256 在 `source_manifest.json`，原数组和冻结排名在 `source/<pdb>/`。沉积 GT 只用于展示与既有评价，实际给定中心和排序均沿用冻结推理事实。查看某例具体来源时，先看 `data.json.source_paths`，再对照对应 `source` 文件。

## 从基础资产重建，以及替换 PPT 图片

日常学习直接使用已有标准资产和 `.cxc`，无需下载。确需从冻结资产重建时，在仓库根目录 PowerShell 运行以下**数据准备命令**；它们不是新的模型推理或实验命令：

```powershell
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/source_prepare/fetch_data.py'
& 'D:/Anaconda/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/source_prepare/prepare_data.py'
```

下载沿用本机已有的 SSH helper，只读服务器冻结产物。完成后用 ChimeraX 打开七个对应 `.cxc`。不要把显示属性加进 `prepare_data.py`，相机、颜色、显示区域和保存命令继续留在明文 `.cxc` 中。

在 PPT 中选中需要更新的独立视图，使用 **图片格式 → 更改图片 → 来自文件** 替换对应 PNG，保留原框位置和大小。文字、箭头、排序卡和指标可直接编辑；不要拉伸 4:3 图像。想改变密度透明度或原子颜色，应先在 ChimeraX 中修改、重新导出，再替换图片。

Find 图上的数字是原候选排序。编号和指引线是 PPT 原生对象，终点依据实际 ChimeraX 截图目视放置，不改变 blob 的形状、位置和大小。如果更换视角，需在 PPT 中将对应指引线重新指向该 blob。

本目录的 `build_deck.mjs` 为原始案例布局生成带独立图名和备注的候选，通过结构检查的新PPT保存在 `e2e/output/e2e-flow/regenerated/source/`。当前正文图集和引用以[阶段追溯](../../图表追溯.md)为准；图注回到正式PPT备注，正文回到Markdown维护。Word导图和回转由[转换工具](../../../../../../转换工具/README.md)统一处理。

旧 [publish_ppt.ps1](../../../../archive/visualization/publication-history/e2e/e2e-flow-shared/source_prepare/publish_ppt.ps1) 已归档，仅保留历史发布过程。当前构造器已自行写入图名；旧脚本会重复追加批注并覆盖正式图集，不作为当前调用入口。

进一步学习公共相机、原子与体素坐标及多视图切换，可阅读 [Stage1 制作与分析教程](../../../../archive/visualization/stage1/chimera_sixpanel_20260929/制作与分析教程.md)。本轮病例、模型编号、颜色和评价范围以当前 README 与七份完整命令为准。
