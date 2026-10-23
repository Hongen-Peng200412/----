> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 端到端流程图 v2：从原生科学视图到可编辑 PPT

当前正式载体为 `画图/E2E案例可视化-端到端流程版_v3.pptx`；以下v2科学显示契约仍描述同一批冻结视图，不能据旧页号或旧PPT路径替代正文引用。完整当前来源见[阶段追溯](../图表追溯.md)。活动代码在本目录、`base/`与`source_prepare/`，冻结数据分别在 `e2e/output/e2e-flow/{display,views,source}/`；Python取数／格式转换／重导命令生成默认写 `temp/` 或对应 `regenerated/`，不覆盖冻结资产。

冷读顺序为 `source_prepare/prepare_data.py` 的原坐标格式转换、`base/prepare_flow_assets.py` 的完整地图与blob、当前两个 `prepare_*` 的原生重导命令、`draw_identities.py` 的精确身份二维图、`build_deck.mjs` 的PPT布局。两个 `verify_*` 只读检查原生相机、PNG及旧资产SHA，重核报告写 `temp/e2e_flow_v2_20261003/`。

迁移后，全部175个CXC直接 `open` 资源静态存在，活动基础CXS的相对MRC关联完整。七份冻结 `display/<pdb>/global_session.cxs` 仍保留77个原formal绝对MRC路径，只作历史会话留档；交互复现使用已重定向的基础CXC和新版CXC。保存PNG的原生日志与既有地图同尺度核对均已离线通过；本轮未启动ChimeraX重渲染。

v2 将同一批冻结案例组织为 **Input → Find → Match → Build**。正文按 **9LLG → 9BJJ → 30GA** 排列；9QRU、9RD8、9WUP、9XZL 留在同一图集作为备选。Build 的公开模型名称统一为 **PocketXMol-tuned**。

三维图来自 UCSF ChimeraX 1.10.1 原生命令。v2 删除全局 Find 的原生排名数字，并将完整实验地图沿用 CA2 / GT 的 `global_structure` 相机重新导出；地图、全部冻结 blob、受体和分子坐标均保持原样，其余三维 PNG 直接复用 v1。Input 的 a/b/c 使用同一原生相机、共同裁切和相同等比倍率，具有相同的物理比例。PPT 只进行非破坏裁切和等比放大，原 PNG 字节仍嵌入文件，可以在 PowerPoint 中取消裁切。外围稀疏密度点不决定面板的放大倍数，完整 CA2 受体和全部冻结 blob 都纳入全局 Find 的裁切范围。

Match 的二维图由精确输入 SMILES 独立生成，不读取 GT、预测 SDF 或三维坐标。三张 Build 图显示同一原自评分首位姿态，在受体、实验密度与沉积参考叠加下的不同外观。GT 指沉积结构及已有标注，仅用于参考显示和既有评价。

## 成品、来源与页序

下表保留v2的案例页序和稳定图名。当前正式载体为v3，路径与正文引用以[阶段追溯](../图表追溯.md)为准；每页的独立 `@@图名` 批注供转换器定位，备注保存图注。

| 页码 | 案例 | 图名 | 正文用途 |
| --- | --- | --- | --- |
| 1 | 9LLG · A1EKL，R:602 | `e2e-flow-9llg` | 图12 |
| 2 | 9BJJ · ATP，B:901 | `e2e-flow-9bjj` | 图13 |
| 3 | 30GA · ATP，N:401 | `e2e-flow-30ga` | 图14 |
| 4 | 9QRU · A1JAX，B:2801 | `e2e-flow-9qru` | 备选 |
| 5 | 9RD8 · BCT，A:902 | `e2e-flow-9rd8` | 备选 |
| 6 | 9WUP · FMN，B:1103 | `e2e-flow-9wup` | 备选 |
| 7 | 9XZL · AGS，F:1001 | `e2e-flow-9xzl` | 备选 |

`<pdb>` 在下列目录树中只表示表内七个小写目录。两棵树描述同一物理目录，分别列出科学图与事实、以及复现和验收辅助文件。

### 科学图与事实

```text
论文草稿/
├─ 画图/E2E案例可视化-端到端流程版_v2.pptx       # 七页完整行动流程，文字/箭头/彩框可编辑
├─ 画图/画图代码/e2e/output/e2e-flow/display/
│  ├─ e2e-flow-<pdb>.png                        # 对应七页 PPT 的整页导出
│  ├─ E2E案例可视化-端到端流程版_v2.pdf           # 七页 PDF 预览
│  └─ <pdb>/
│     ├─ renders/global_find.png                # 原生删除排名数字后的全局 Find 图
│     ├─ renders/global_density_same_scale.png   # 完整地图，沿用 CA2 / GT 相机与物理比例
│     └─ identities/
│        ├─ identity_manifest.json              # 精确身份轴、预测项、二维布局与化学核查
│        ├─ identity_XX.svg / .png               # 1600×720 透明 RDKit 结构图
│        └─ identity_XX_white.svg / .png         # 同一化学图的白底版本
├─ 画图/画图代码/e2e/output/e2e-flow/views/<pdb>/           # v2 保留并读取的 v1 科学来源
│  ├─ data.json                                 # 冻结候选、身份、姿态与评价
│  ├─ geometry.json                             # 模型号、全部 blob、spacing 与地图原点
│  ├─ camera.json                               # 原生相机矩阵与 Å/像素尺度
│  ├─ assets/                                   # 完整/局部 MRC、受体 CIF 与参考/预测 SDF
│  └─ renders/                                  # v2 复用的 Input、局部 Find 与三张 Build PNG
└─ 画图/画图代码/e2e/output/e2e-flow/source/source/<pdb>/   # 原冻结数组、排名、轨迹和 SMILES 身份来源
```

`XX` 是原 `prediction.identity_smiles` 的零基下标，从 `00` 开始。七例共 22 个身份，各有透明/白底 SVG 与 PNG，共 88 个结构图文件。

### 复现与验收辅助文件

```text
论文草稿/
├─ 画图/画图代码/e2e/visualization/e2e-flow-shared/
│  ├─ README.md                               # 本教程与字段契约
│  ├─ <pdb>_global_find.cxc                    # 每例原生删除排名标签并导图（可再生工具输入）
│  ├─ <pdb>_global_density_same_scale.cxc      # 每例完整地图同尺度导图（可再生工具输入）
│  ├─ prepare_global_find_v2.py                # 写 CXC、冻结体素投影框（可再生工具输入）
│  ├─ render_global_find_v2.ps1                # 七例顺序原生渲染（可再生工具输入）
│  ├─ prepare_same_scale_density.py            # 写同尺度完整地图 CXC（可再生工具输入）
│  ├─ render_same_scale_density.ps1            # 七例顺序原生补导完整地图（可再生工具输入）
│  ├─ draw_identities.py                      # 精确 SMILES 的横向 RDKit 绘图（可再生工具输入）
│  ├─ build_deck.mjs                          # 图片共同裁切与原生 PPT 对象装配（可再生工具输入）
│  ├─ apply_native_crop.py                    # 将 manifest 裁切写入原生 srcRect（可再生工具输入）
│  ├─ verify_global_find_v2.py                 # 来源、相机与原生日志核查（运行诊断）
│  ├─ verify_same_scale_density.py             # 完整地图来源及同尺度相机核查（运行诊断）
│  └─ 执行记录.md                             # 本次交付和验收状态（运行诊断）
├─ 画图/画图代码/e2e/output/e2e-flow/display/
│  ├─ projection_boxes_manifest.json          # 七例冻结候选的投影关联框（可再生辅助导出）
│  ├─ global_find_v2_manifest.json             # 无排名图、相机和 v1 保留核查（运行诊断）
│  ├─ same_scale_density_manifest.json         # 七例完整地图与受体相机一致核查（运行诊断）
│  └─ <pdb>/
│     ├─ projection_boxes.json                # 本例投影坐标与彩框边距（可再生辅助导出）
│     ├─ global_session.cxs                   # 无排名标签的全局会话（可再生辅助导出）
│     ├─ commands.html                        # 删除标签及相机的原生命令日志（运行诊断）
│     ├─ global_density_same_scale_commands.html # 同尺度完整地图原生命令日志（运行诊断）
│     └─ same_scale_density_camera.json        # 本例完整地图相机、来源及导图核查（运行诊断）
├─ 画图/画图代码/e2e/visualization/e2e-flow-shared/base/
│  └─ <pdb>_reproduce.cxc                      # 完整科学视图的 v1 原生入口（可再生工具输入）
└─ temp/e2e_flow_v2_20261003/
   ├─ deck_manifest.json                      # 页序、源图、共同裁切和 PPT 矩形（运行诊断）
   ├─ candidate.pptx / validated.pptx          # 发布前图集（工具临时目录）
   ├─ v1_readonly_baseline.json                # v1 输入 SHA-256 基线（运行诊断）
   ├─ same_scale_density_baseline.json         # 补导前 49 个 v1 来源 SHA-256（运行诊断）
   └─ 启动文件、控制台输出与图像检查              # 可再生检查材料（工具临时目录）
```

v2 全局会话以 `includeMaps false` 外部引用 v1 的完整 MRC，需保留 v1 资产目录。v1 的局部 `session.cxs` 嵌入局部地图和全部 blob。v2 没有复制一套新的三维科学资产。

## 四个行动与冻结事实

Input 展示实验图，并用 CryoAtom2 重建受体的箭头连接 a 与 b；GT 受体 c 由虚线隔开。Find 展示全局候选和彩框关联的局部 GT / Find 对照。Match 完整展示当前 PDB 的已给定身份列表，蓝框标出实际预测项。Build 展示 PocketXMol-tuned 的同一原自评分首位姿态，三个外观不表示三次预测。

| PDB | 目标 blob / 原候选次序 / 计费尝试 | 合格身份 / 全身份 | 首位姿态 RMSD（Å） |
| --- | --- | --- | ---: |
| 9LLG | 0 / 1 / 1 | 3 / 3 | 0.878 |
| 9BJJ | 0 / 1 / 1 | 2 / 3 | 0.805 |
| 30GA | 1 / 2 / 2 | 1 / 2 | 1.036 |
| 9QRU | 1 / 2 / 2 | 2 / 3 | 0.633 |
| 9RD8 | 0 / 1 / 1 | 3 / 4 | 0.961 |
| 9WUP | 2 / 3 / 1 | 4 / 4 | 0.524 |
| 9XZL | 1 / 2 / 1 | 1 / 3 | 0.912 |

blob 编号 `source_blob_index` 从 0 开始，原候选顺序 `raw_rank` 和计费尝试 `attempt_index` 从 1 开始。30GA、9QRU 的首项是背景，消耗一次尝试，实际未运行 Match 或 Build。9WUP 的前两项是范围外小分子前景，9XZL 的首项是 ion，按冻结 Stage3 门禁免费跳过。9QRU 目标的原 `candidate_selected=false`，仍按完整顺序实际进入评价。

身份级 `eligible` 掩码与候选级 Stage3 范围门禁不同，例如 9WUP 四个身份均 eligible，却不能据此推断前两项候选在 Build 范围内。30GA、9XZL 仅一个合格身份，体现定位与构象重建，不单独证明多身份区分能力。

所示成功目标位点已有 50 个姿态、每姿态 100 步。本教程只复现显示；原 `data.json` 中内部协议 `local-c1` 和方法标识 `local_cov-C` 用来追溯这一原自评分首位姿态，不作为图与正文的公开模型名称。原始排名、SMILES、坐标与评价均保留，不按 GT RMSD 重新挑选。

## 每例的原生命令入口

启动 `D:/ChimeraX 1.10.1/bin/ChimeraX.exe`，在 **Tools → General → Command Line** 打开命令栏。下文 `text` 块是 ChimeraX 命令，PowerShell 块是终端命令。

先执行对应 v1 完整入口重建科学视图；再分别执行 v2 两个入口，生成无排名数字的全局 Find 和与 CA2 / GT 同尺度的完整地图。每个入口都先 `close all`，请将个人修改另存到 `temp/`。

| 案例 | v1 完整科学视图 | v2 无排名全局 Find | v2 同尺度 Input 地图 |
| --- | --- | --- | --- |
| 9LLG | [9llg_reproduce.cxc](base/9llg_reproduce.cxc) | [9llg_global_find.cxc](9llg_global_find.cxc) | [9llg_global_density_same_scale.cxc](9llg_global_density_same_scale.cxc) |
| 9BJJ | [9bjj_reproduce.cxc](base/9bjj_reproduce.cxc) | [9bjj_global_find.cxc](9bjj_global_find.cxc) | [9bjj_global_density_same_scale.cxc](9bjj_global_density_same_scale.cxc) |
| 30GA | [30ga_reproduce.cxc](base/30ga_reproduce.cxc) | [30ga_global_find.cxc](30ga_global_find.cxc) | [30ga_global_density_same_scale.cxc](30ga_global_density_same_scale.cxc) |
| 9QRU | [9qru_reproduce.cxc](base/9qru_reproduce.cxc) | [9qru_global_find.cxc](9qru_global_find.cxc) | [9qru_global_density_same_scale.cxc](9qru_global_density_same_scale.cxc) |
| 9RD8 | [9rd8_reproduce.cxc](base/9rd8_reproduce.cxc) | [9rd8_global_find.cxc](9rd8_global_find.cxc) | [9rd8_global_density_same_scale.cxc](9rd8_global_density_same_scale.cxc) |
| 9WUP | [9wup_reproduce.cxc](base/9wup_reproduce.cxc) | [9wup_global_find.cxc](9wup_global_find.cxc) | [9wup_global_density_same_scale.cxc](9wup_global_density_same_scale.cxc) |
| 9XZL | [9xzl_reproduce.cxc](base/9xzl_reproduce.cxc) | [9xzl_global_find.cxc](9xzl_global_find.cxc) | [9xzl_global_density_same_scale.cxc](9xzl_global_density_same_scale.cxc) |

以第一例 9LLG 为例，运行完整入口：

```text
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/visualization/e2e-flow-shared/base/9llg_reproduce.cxc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/visualization/e2e-flow-shared/9llg_global_find.cxc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/visualization/e2e-flow-shared/9llg_global_density_same_scale.cxc"
```

无排名入口的实际动作是打开 v1 全局会话、`view global_find`、`label delete #7 models`，再保存 PNG、全局会话与命令日志。同尺度地图入口仍打开 v1 全局会话，隐藏其余模型，只显示完整图 #10，恢复原源阈值及 `region all` / `unzone` / `step 1`，选择已有 `view global_structure`，保存 PNG 与独立日志。它不生成另一份会话。其他案例替换 PDB 路径和目标/完整图模型号；没有新模型变换或科学阈值。

### 手工打开的模型顺序

固定 #1–#6 分别为局部密度、实际 CA2 受体、沉积目标配体、预测首位姿态、目标 GT 区域、GT 受体。#7 起按原 `blobs.npz.blob_index` 加载全部 blob，最后加载完整实验图；背景例再加载一点显示锚。模型编号来自 `open` 顺序，不是候选排名。

| PDB | 全部 blob 文件与模型 | 目标模型 | 完整图模型 | 背景显示锚 |
| --- | --- | --- | --- | --- |
| 9LLG | `blob_0.mrc`–`blob_2.mrc`，#7–#9 | #7 | #10 | 无 |
| 9BJJ | `blob_0.mrc`–`blob_14.mrc`，#7–#21 | #7 | #22 | 无 |
| 30GA | `blob_0.mrc`–`blob_18.mrc`，#7–#25 | #8 | #26 | #27 |
| 9QRU | `blob_0.mrc`–`blob_3.mrc`，#7–#10 | #8 | #11 | #12 |
| 9RD8 | `blob_0.mrc`–`blob_4.mrc`，#7–#11 | #7 | #12 | 无 |
| 9WUP | `blob_0.mrc`–`blob_6.mrc`，#7–#13 | #9 | #14 | 无 |
| 9XZL | `blob_0.mrc`–`blob_2.mrc`，#7–#9 | #8 | #10 | 无 |

手工学习 9LLG 时，按下面顺序加载标准资产。此时尚未建立命名视角，随后建立显示属性与相机。

```text
close all
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/density.mrc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/ca2_receptor.cif"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/reference.sdf"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/prediction.sdf"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/gt_area.mrc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/gt_receptor.cif"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/blob_0.mrc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/blob_1.mrc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/blob_2.mrc"
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/assets/full_density.mrc"
```

建立 9LLG 的交付基础外观与三个全局相机：

```text
set bgColor white
camera ortho
windowsize 960 720
lighting soft
material dull
graphics silhouettes false
hide models
hide #2,6 atoms
cartoon #2,6
color #2,6 #81a58b target c
color #2,6 #81a58b target ab
transparency #2,6 20 target c
style #3,4 stick
size #3,4 stickRadius 0.20
color #3 #26a6a1 target ab
color #4 #3169b3 target ab
volume #1 style mesh step 1 level 0.009667073376476765 color #a0a9ad transparency 0.55 squareMesh true meshLighting false
volume #5 style mesh step 1 level 0.5 color #26a6a1 transparency 0.20
volume #7 style surface step 1 level 0.5 color #e9983c transparency 0.05 surfaceSmoothing false
volume #8,9 style surface step 1 level 0.5 color #cbd0d2 transparency 0.05 surfaceSmoothing false
volume #10 style surface step 1 level 0.009667073376476765 color #8e9ca5 transparency 0.15 surfaceSmoothing false
volume #10 region all
volume unzone #10
show #10 models
view #10 orient
turn y 25
turn x -20
view #10 pad 0.06
clip off
view name global_density
show #2,6 models
show #2,6 atoms
view #2,6 orient
turn y 25
turn x -20
view #2,6 pad 0.07
clip off
view name global_structure
view #2,6,7,8,9 pad 0.07
clip off
view name global_find
hide #2,6 atoms
```

`global_density` 保留按完整地图等值面取景的原 frame，供单独查看；完整 CA2 / GT 受体原子共同取景得到 `global_structure`；完整受体加全部 blob 共同取景得到 `global_find`。v2 最终 Input a/b/c 全部选择 `global_structure`，a 始终显示完整图模型，不使用 #1 局部裁图。相机取景不改变地图体素或模型坐标。手工按此路径加载没有创建排名标签，因此自然得到 v2 无排名外观。

### 打开已有会话并选视图

已有 v2 会话可直接恢复全局显示；它已含命名视角与标准外观：

```text
close all
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/display/9llg/global_session.cxs"
hide models; show #10 models; volume #10 transparency 0.15; view global_structure
transparency #2,6 20 target c
hide models; show #2 models; view global_structure
hide models; show #6,3 models; view global_structure
transparency #2 0 target c
volume #10 transparency 0.78
hide models; show #10,2,7,8,9 models; view global_find
```

会话保存于 Find 外观，完整图透明度是 `0.78`。重导 Input 的完整图 a 时使用 `volume #10 transparency 0.15` 和 `view global_structure`；b/c 的受体 cartoon 为 20% 透明，d 的 CA2 cartoon 为 0%。透明度是外观属性，不随 `view` 恢复：

```text
transparency #2,6 20 target c
volume #10 transparency 0.15
```

重新导出 d 前改为 `transparency #2 0 target c` 和 `volume #10 transparency 0.78`。只切相机不能恢复这些显示属性。若要单独浏览完整地图原 frame，可选 `view global_density`；这个视角不用于最终 v2 Input a。

局部图可另开 v1 局部会话：

```text
close all
open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/e2e-flow/views/9llg/session.cxs"
```

或在手工加载后建立下列局部显示。两种路径均使用目标 #7；已有会话内 `view local` 可直接恢复原局部相机：

```text
hide models
hide #2,6 cartoons
hide #2,6 surfaces
hide #2,6 atoms
show (#2,6 & (#3 :< 6)) atoms
style #2,6 stick
size #2,6 stickRadius 0.055
transparency #2,6 45 target ab
show #3,4,7 models
view #3 orient
turn y 35
turn x -25
view #3,4,7 pad 0.25
clip off
view name local
volume zone #1 nearAtoms #3 range 4 newMap false minimalBounds true
volume #1 color #a0a9ad transparency 0.55
hide models; show #3,5,6 models; view local
hide models; show #1,2,7 models; view local
```

最后两行分别得到局部 GT 与局部 Find。`#3 :< 6` 只是参考配体 6 Å 内完整受体残基的显示范围；zone 只限制密度显示，不重采样、归一化或重新分割。

三种 Build 外观分别使用相同的 `view local`：

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

这三段依次是受体表面、实验密度与沉积构象叠加。#4 的原子坐标从始至终相同。原子/cartoon 透明度使用百分数，如 `68`；volume 使用 0–1，如 `0.12`。`view local` 不恢复颜色、zone 或显示状态。不要单独 fit、旋转或平移某个模型。

每张原生 PNG 以 1440×1080、两倍超采样保存，练习产物放到 `temp/`：

```text
view matrix
zoom
wait 2
save "C:/Users/15919/Desktop/论文草稿/temp/my_e2e_v2.png" width 1440 height 1080 supersample 2
```

以上手工数值针对 9LLG。其他案例按模型表替换目标与完整图号，密度 level 使用其 `geometry.json.contour_canonical`；完整姿态、背景邻域和每张保存命令可直接运行对应 v1 CXC 精确重建。

## 图片来源、共同裁切与可编辑彩框

| 面板 | 来源 | 原生相机 | PPT 共同裁切范围 |
| --- | --- | --- | --- |
| a | v2 `renders/global_density_same_scale.png` | 与 b/c 相同的 `global_structure` | 与 b/c 相同的 `structureCrop`，留 36 源像素 |
| b/c | v1 `global_ca2.png` / `global_gt.png` | 同一 `global_structure` | 完整 CA2 与 GT 受体原子投影共同范围，留 36 源像素 |
| d | v2 `renders/global_find.png` | 原 `global_find` | 完整 CA2、全部冻结 blob 及关联框共同范围，留 36 源像素 |
| e/f | v1 `local_gt.png` / `local_find.png` | 同一 `local` | 两张非白范围的并集，留 24 源像素 |
| 背景 e/f | v1 `background_gt.png` / `background_find.png`，仅 30GA/9QRU | 同一 `background` | 同一背景两张非白范围并集，留 24 源像素 |
| g | v2 `identities/identity_XX.svg` | 二维布局，无三维相机 | 实际内容 bbox 外留 20 像素，不修改化学路径 |
| h/i/j | v1 `dock_receptor.png` / `dock_density.png` / `dock_gt_overlay.png` | 同一 `local`、同一 #4 姿态 | 三张非白范围并集，留 24 源像素 |

裁切范围只用于显示。完整 MRC 仍 `region all` / `unzone` / `step 1`；a/d 的裁切不需要把外围零散密度点和空白全部放入面板。a/b/c、同位点 e/f、h/i/j 各组的原相机、共同裁切范围及等比比例一致。Input 三图还使用相同的 `[480,300]` 占位宽高，因此同一世界坐标距离对应同一画面长度。

### `deck_manifest.json`

位于 `temp/e2e_flow_v2_20261003/`，长度 7，页序与 PPT 一致。每项含 `name`、`pdb`、`caption`、`panels`、`boxes`、`identities`、`canvas_px=[1800,2100]`、`final_physical_width_mm=183`。`panels` 按图片插入顺序记录：

| 字段 | 类型与含义 | 9LLG b 面板真实示例 |
| --- | --- | --- |
| `key` / `letter` | 原生文件名 / 面板字母 | `"global_ca2"` / `"b"` |
| `source_path` | 实际读取的原 PNG 路径 | v1 `9llg/renders/global_ca2.png` |
| `crop_bbox_px` | 源图 `[left,top,right,bottom]` 浮点像素范围 | `[273.748004,107.818293,1140.337735,919.824063]` |
| `frame_px` | PPT 预留 `[x,y,width,height]` 画布像素框 | `[680,260,480,300]` |
| `scale` | 源像素到 PPT 画布像素的单一等比倍数 | `0.3694555027` |
| `rectangle_px` | 裁切图最终居中后的 `[x,y,width,height]` | `[759.916828,260,320.166345,300]` |

9LLG a/b/c 使用同一 `crop_bbox_px` 与 `scale`，最终图片宽高均为 `[320.166345,300]`；a 的矩形为 `[209.916828,260,320.166345,300]`，b/c 每次向右平移 550 排版像素。e/f 共同裁切为 `[114,0,1331,1080]`，比例为 `0.3240740741`；h/i/j 共同裁切为 `[30,0,1436,1080]`，比例为 `0.2777777778`。精确浮点值以 manifest 为准。

### `same_scale_density_manifest.json`

该文件汇总七例，每例另存 `same_scale_density_camera.json`。字段包括 `pdb`、`full_map_model_id`、`full_source_shape_zyx`、`full_source_sha256`、`full_map_asset_path`、`full_map_region`、`contour_canonical`、`camera_native_logged_values`、`matches_global_ca2_gt_camera`、`scientific_geometry_unchanged`、`v1_49_source_hash_checks_passed`、PNG 路径/SHA、原生日志路径及共同裁切约定。相机字段保存真实 `view matrix`、`zoom`、窗口 `[960,720]` 和导出 `[1440,1080]`。

9LLG 完整图为 #10，原 shape 是 `[208,208,208]`，原 contour 为 `0.009667073376476765`；同尺度地图与 v1 CA2 / GT 的原生相机矩阵完全相等，原生 zoom 为 `0.176` Å/窗口像素。七例的相机相等、科学坐标不变和补导前 49 个 v1 来源 SHA 核查均为 true。窗口像素与 1440×1080 导出像素按 1.5 倍对应，PPT 再使用上面的共同等比倍率；不能把窗口尺度直接当作 PPT 排版像素的 Å 尺度。

若裁切宽高为 $C_w,C_h$，预留框宽高为 $W,H$，共同等比倍数为 $q=\min(W/C_w,H/C_h)$。最终图像宽高是 $qC_w,qC_h$，在预留框中居中。坐标单位是排版像素，与原子 XYZ Å 世界坐标无关。

`build_deck.mjs` 在导出临时 `candidate.pptx` 后、验收前自动调用 `apply_native_crop.py`，把 manifest 的范围写入每张三维图片的原生 `a:srcRect`。四边保存为移除边缘的十万分比，保留包内媒体字节；无需另跑该脚本。共同 crop 的实际 PPT 属性可由 `srcRect` 核对，不能只根据装配器输入判断裁切已生效。

### `projection_boxes.json` 与彩框

每例 `projection_boxes.json` 记录原 `global_find` 正交相机、原体素坐标和显示框；根目录 `projection_boxes_manifest.json` 汇总七例。`boxes` 共有 9 项，7 个 target 加 30GA/9QRU 两个 background。原排名保存在字段中，v2 全局截图不再显示数字。

每项保存 `role`、`source_blob_index`、`raw_rank`、`model_id`、`source_voxel_count`、`color`、`centroid_world_xyz_A`、`centroid_export_xy_px`、`voxel_centers_bbox_xyxy_px`、`voxel_halfcell_envelope_bbox_xyxy_px`、`suggested_box_xyxy_px`、`requested_pixel_margin`、`minimum_display_box_wh_px`、`actual_margin_ltrb_px`、`all_frozen_voxel_support_in_frame` 与 `algorithm_detection_scope_changed`。

9LLG target 是 blob `0`、模型 `7`、原排名 `1`，含 `380` 个原体素。其半体素支撑包络约为 `[770.797642,277.640157,861.545909,387.488048]`；建议彩框为 `[746.797642,253.640157,885.545909,411.488048]`，外留 24 源像素。小框的最小显示宽高为 `[80,80]`，实际四边边距逐项保存。框只是全局到局部的显示关联，不是新的分割边界；`algorithm_detection_scope_changed=false`。

投影坐标原点在 1440×1080 PNG 左上，X 向右、Y 向下。原生命令打印矩阵约 5 位有效数字、尺度约 3 位，所记录边界是这些日志值的名义投影，并有显式边距。PPT 将源框映射为 `(源像素−裁切左上角)×scale+rectangle_px左上角`。彩框是可编辑矩形，橙色表示目标，灰紫色表示背景。

## 从精确 SMILES 独立重建 Match 二维图

在仓库根目录 PowerShell 使用已安装 RDKit 2026.03.6 的 bundled Python 3.12：

```powershell
$env:PYTHONPATH = 'C:/Users/15919/Desktop/论文草稿/temp/e2e_flow_20261003/rdkit_deps'
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/draw_identities.py' --source-root '画图/画图代码/e2e/output/e2e-flow/source' --output-root '画图/画图代码/e2e/output/e2e-flow/display/regenerated'
```

这个入口仅读取旧 `data.json` 的身份清单和已有 CCD 来源，单独生成二维图。`identity_smiles`、`small_molecule_answer_mask` 和 `identity_logits` 是长度 I、按同一身份下标对齐的数组；`matched` 是与冻结 `predicted_smiles_small_molecule` 逐字符相等，不由 GT、RMSD 或画出的结构决定。

| PDB | 全身份数 I | eligible 掩码 | matched 零基下标 |
| --- | ---: | --- | ---: |
| 9LLG | 3 | `[true,true,true]` | 1 |
| 9BJJ | 3 | `[true,true,false]` | 0 |
| 30GA | 2 | `[true,false]` | 0 |
| 9QRU | 3 | `[true,true,false]` | 0 |
| 9RD8 | 4 | `[true,true,true,false]` | 1 |
| 9WUP | 4 | `[true,true,true,true]` | 2 |
| 9XZL | 3 | `[true,false,false]` | 0 |

每例 `identity_manifest.json` 保存原精确 `smiles`、身份 `identity_index`、`eligible`、`matched`、`identity_logit`、可证的 `ccd_label` / `ccd_label_evidence`、中性 `display_label`、展示 `atom_count`、`content_bbox_px`、`layout_2d`、`card_legibility`、`chemical_graph` 与四种图的 `paths`。未知 CCD 标签为 `null`，不根据结构外观猜测名称；所有非匹配项仍绘制，PPT 不重复写额外范围提示。

二维展示采用标准删氢、确定性二维布局及二维刚体旋转；布局单位没有 Å 的物理意义，不生成或改变三维姿态。`layout_2d` 记录生成器、旋转角、绘图范围、卡片比例、显示键长、元素字号和文字相交核查。9BJJ ATP 的实际记录为 `generator="RDKit_seed0_samples0"`、`rotation_degrees=175`、`atom_font_size_px=76`、`atom_label_bbox_overlap_count=0`，bbox 为 `[66,49,1534,670]`。磷酸支链的绘图键长调整只为元素文字留空间，原元素、形式电荷、同位素、键型和已声明手性不变。

同一精确 SMILES 使用同一布局缓存，9BJJ 与 30GA 的 ATP SVG/PNG 分别逐字节一致。`chemical_graph` 中的删氢后加氢同构、二维绘图同构、已声明手性保持及未新增立体化学检查均须通过。精确输入字符串没有被规范化字符串替换。`card_legibility` 保存按给定总图宽估计的字号与单原子建议高度，这些是排版估计，不是化学指标。装配器按 `atom_count===1` 将单原子结构的最大绘图高度设为 80 排版像素，其余结构为 220，不依赖是否有 CCD 标签。

若只练习一个精确字符串，可在已设置上述 PYTHONPATH 的 Python 中直接使用现有绘图函数，产物写到 `temp/`：

```python
from pathlib import Path
import sys
sys.path.insert(0, "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/visualization/e2e-flow-shared")
from draw_identities import describe_chemical_graph, draw_identity_assets

smiles = "[Mg+2]"
molecule, chemical_graph, layout = describe_chemical_graph(smiles, card_width_px=508)
destination = Path("C:/Users/15919/Desktop/论文草稿/temp/single_smiles_2d")
destination.mkdir(parents=True, exist_ok=True)
draw_identity_assets(molecule, True, destination, 0, layout["atom_font_size_px"])
```

## 坐标、地图与姿态的来源

原密度数组按 ZYX 存放，世界坐标按 XYZ 表示，单位 Å。源 `origin` 是体素边界角点，`voxel_size` 是实际 XYZ spacing；MRC 首采样点中心为 $O_{corner}+(s_{XYZ}+0.5)\odot d_{XYZ}$，其中 $s$ 为裁图起点、$d$ 为 spacing、$\odot$ 为逐分量乘法。完整图 $s=0$。9LLG 的实际逐轴 spacing 为 `1.00153851509094` Å，完整首中心约 `[0.500769258,0.500769258,0.500769258]` Å；局部裁图起点 ZYX 为 `[102,91,79]`，首中心 XYZ 约 `[79.622312,91.640774,102.657698]` Å。

`assets/full_density.mrc` 是服务器完整实验数组转换，`density.mrc` 是 v1 保留的局部原值裁图，二者没有重采样或重新归一化。全部 blob 沿用原整数体素索引；预测 SDF 始终是原自评分首位世界坐标。完整来源、源 SHA-256、每例精确 spacing、相机与模型表见 v1 的 `geometry.json`、`camera.json`、`full_density_manifest.json` 和 [v1 复现说明](base/README.md)。这里的内部 trace 仅追溯已有结果，不运行新的科学推理。

## 原生视图与候选生成命令

以下在论文仓库根目录 PowerShell 运行。已有 v1 标准资产与会话时，准备 v2 投影记录并原生生成无排名截图：

```powershell
& 'D:/Anaconda/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/prepare_global_find_v2.py'
powershell -NoProfile -File '画图/画图代码/e2e/visualization/e2e-flow-shared/render_global_find_v2.ps1'
```

再以 bundled Python 生成同尺度地图入口，并用同一 ChimeraX 原生补导七例完整地图：

```powershell
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/prepare_same_scale_density.py'
powershell -NoProfile -File '画图/画图代码/e2e/visualization/e2e-flow-shared/render_same_scale_density.ps1'
```

`prepare_same_scale_density.py` 仅使用标准库；渲染脚本已有 UTF-8 BOM，可由 Windows PowerShell 5 读取中文路径。所有补导均调用现有会话与源地图，不重新运行科学实验。

按前文 RDKit 命令生成身份图后，装配带图名的新候选：

```powershell
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/build_deck.mjs'
```

PPT画布为1800×2100排版像素。装配器在 `temp/e2e_flow_v2_20261003/` 写候选、独立图名与备注，再应用原生裁切并检查结构；新候选保存在 `e2e/output/e2e-flow/regenerated/display/`。原生文字、箭头、彩框和独立图片均可编辑。

旧 [publish_ppt.ps1](../../../archive/visualization/publication-history/e2e/e2e-flow-shared/publish_ppt.ps1) 已归档，仅保留历史发布过程。当前构造器已自行写入图名；旧脚本会重复追加批注并覆盖正式图集，不作为当前调用入口。

当前正式图集为 `画图/E2E案例可视化-端到端流程版_v3.pptx`，正文引用9LLG、9BJJ、30GA三个稳定图名，具体路径以[阶段追溯](../图表追溯.md)为准。

图注在正式PPT备注中修改，正文在Markdown中修改。Word图号、完整图注空间及回转由[转换工具](../../../../../转换工具/README.md)统一处理。旧 [fit_word_layout.py](../../../archive/visualization/e2e-word-layout/e2e-flow-shared/fit_word_layout.py) 已归档，不在当前Word转换后运行；它只处理当时固定的文稿副本。历史验收记录见[执行记录](执行记录.md)。

## QA 命令与检查证据

正式产图完成后，再单独核查 v1 输入未改、原生相机一致及日志无命令错误：

```powershell
& 'D:/Anaconda/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/verify_global_find_v2.py'
& 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' '画图/画图代码/e2e/visualization/e2e-flow-shared/verify_same_scale_density.py'
```

第一个核查器读取基线 SHA、v2 `commands.html` 和新旧 Find PNG，写出 `global_find_v2_manifest.json`。每例记录 `rank_label_deleted_by_native_command`、`camera_unchanged`、原矩阵、尺度、图像尺寸/SHA、差异像素统计、`v1_inputs_unchanged` 和投影框数量。差异统计用于记录重新导图的像素变化，不解释为模型精度或新的密度检测。第二个核查器使用已有 PIL 读取新完整地图 PNG，核对 1440×1080 尺寸、日志无命令错误、相机与 v1 `global_structure` 完全相等及 49 个旧来源 SHA 未变，写出前文同尺度 manifest。

裁切与版面检查读取 `deck_manifest.json`：a 的 `key` 应为 `global_density_same_scale`，a/b/c 的 `crop_bbox_px`、`scale` 和占位宽高必须相同；同位点 e/f 成对图也应相同；d 的裁切应覆盖完整 CA2 受体、全部冻结 blob 投影及彩框；h/i/j 必须共用同一 crop 和同一预测源。RDKit 的原身份顺序、精确字符串、matched 下标及化学图检查应与冻结清单一致。所有额外检查和临时导出统一放入 `temp/e2e_flow_v2_20261003/`，不修改科学源资产。
