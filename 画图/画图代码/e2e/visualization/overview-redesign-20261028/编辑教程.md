# 总览图 ChimeraX 编辑教程

建议先打开 `D55_完整受体半透明.cxs`：完整受体为 55% 透明的蓝灰 cartoon，密度为浅灰疏网格，四个配体保持不透明，透过受体也能辨认。`D35_完整受体半透明.cxs`、`D70_完整受体半透明.cxs` 分别提供 35%、70% 的对照。

原来的 `A_完整受体.cxs` 保留完整不透明受体与半透明密度表面；`B_局部剖切.cxs` 隐藏挡住配体的前景 ribbon，原子不删除；`C_密度网格.cxs` 提供较密的网格与完整不透明受体。六个会话使用相同原子坐标、默认角度与尺度，打开即为全局视图。

本教程对应 **UCSF ChimeraX 1.10.1**，文件后缀为 `.cxs`。命令在 ChimeraX 窗口底部输入，按 Enter 执行；不在 PowerShell 中执行。若命令行未显示，从 **Tools → General → Command Line** 打开。

会话起始缩放为桌面横向窗口预留了空间，打开可见全局。要恢复 PPT 使用的瘦长画布与缩放，在开始编辑前执行 `windowsize 1200 1500`，再执行 `view Fig1`。若窗口尺寸与本机不同而看到了裁边，执行 `view #1-6` 即可在当前窗口容纳完整场景，角度保持不变。

## 先认清画面中的模型

| 模型编号 | 实际对象 | 初始表示与用途 |
|---|---|---|
| `#1` | 完整四聚体受体，3604 个蛋白重原子 | 蓝灰色 cartoon；原子仍完整保存在会话中 |
| `#2` | B1 的 biotin（BTN） | 绿色碳、元素色杂原子的球棍 |
| `#3` | B2 的 biotin（BTN） | 与 B1 同一化学身份，另一结合位点 |
| `#4` | B4 的 desthiobiotin（DTB） | 金黄色碳的球棍 |
| `#5` | B5 的 iminobiotin（IMI） | 粉色碳的球棍 |
| `#6` | 整体示意密度 | 浅灰表面或网格 |
| `#7`、`#8` | B1、B2 候选区域 | 绿色，默认隐藏 |
| `#9` | B3 假阳性候选区域 | 灰色，默认隐藏；没有最终配体 |
| `#10`、`#11` | B4、B5 候选区域 | 金黄、粉色，默认隐藏 |

受体来自 1STP 的生物学组装；DTB、IMI 采用其他沉积结构的配体坐标叠合到对应位点。混合占据为示意组装，密度由原子坐标生成，不能当作某次真实 cryo-EM 实验或模型预测。三个身份的 Input SMILES、RDKit 游离构象、最终结合构象逐原子对应；游离和结合构象的内部二面角不同。

在 **Tools → General → Model Panel** 中，模型名称旁的“眼睛”复选框控制显隐，“手形”复选框控制选择。请保留模型编号，以便直接使用本教程及同步导出脚本。模型中的原子、表面和 cartoon 是不同的表示；模型总开关关闭时，它的所有表示都看不见。

## 调透明度、颜色和密度轮廓

### 密度透明度

```text
volume #6 transparency 0.90
```

这里的 `0.90` 表示 90% 透明，数值越大越透明。可比较 `0.80`、`0.88`、`0.94`；默认表面为 `0.88`。若使用百分数命令，可写等价的：

```text
transparency #6 90 target s
```

**两种命令的数值范围不同**：`volume ... transparency` 使用 0–1，`transparency` 使用 0–100。不要把 `90` 填进前一种命令。

按钮操作：打开 **Tools → Volume Data → Volume Viewer**，找到 `Schematic-density #6`，点击直方图上方的颜色方块，在颜色选择器中调整 opacity/alpha。Opacity 是不透明度，因此 12% opacity 对应 88% transparency。拖动直方图的阈值线会改变表面轮廓，和透明度是两件事。

### 受体与配体透明度

```text
transparency #1 0 target c
transparency #1 30 target c
transparency #2-5 0 target a
```

第一行恢复完全可见的 cartoon，第二行让 cartoon 变为 30% 透明，第三行保持四个配体完全可见。`c` 指 cartoon，`a` 指原子与键，`s` 指表面。多层透明表面可能相互遮挡；若 cartoon 因此消失，先用第一行恢复不透明，再以浅色代替透明度：

```text
color #1 #93AABA target c
```

恢复本图受体配色：

```text
color #1 #6E8DA2 target c
```

要透过受体看配体，同时保留可区分的密度，推荐本次实测的 D55 设置：

```text
volume #6 style mesh step 3 meshLighting false color #BFC7CF transparency 0
transparency #1 55 target c
transparency #2-5 0 target a
```

把 `55` 换成 `35` 或 `70` 即可比较。ChimeraX 的官方说明指出，多透明模型重叠时只显示每像素最前面的透明模型；因此 D 组把密度显示为浅色、不透明的疏网格，让受体成为唯一的半透明实体，而不是同时调高两个透明度导致受体消失。细节见[官方透明度限制说明](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/colornames.html#transparency-limitations)。

### 表面、网格与阈值

```text
volume #6 style surface step 1 level 0.17 color #CAD0D6 transparency 0.88
volume #6 style mesh step 2 meshLighting false color #A8B2BC transparency 0.45
```

两行分别切换为表面和网格。`step 2` 使网格较疏，适合缩小后放进 Fig1；它改变显示采样，不改变配体或受体坐标。`level` 是等值面阈值，默认 0.17；调高通常使包络收紧，调低通常使包络增大。

若想直接比较真实原子形成的受体分子表面，可执行：

```text
surface #1
color #1 #7795A3 target s
transparency #1 85 target s
```

这个表面属于同一个受体模型。恢复只显示 cartoon：

```text
hide #1 surfaces
cartoon #1
```

## 调整整体角度与画面大小

默认鼠标左键在图形窗口内拖动用于整体旋转，滚轮缩放。需要可重复的小幅调整时使用命令：

```text
turn y 10
turn x -8
turn z 5
zoom 1.10
```

`turn` 后的数值为度，正负号控制方向；X、Y、Z 默认分别按当前屏幕的水平、垂直、进出屏幕方向解释。`zoom 1.10` 放大约 10%。这些命令不单独指定模型时，保持密度、受体和配体的相对位置。

会话内已保存三个备选视角：

```text
view slender
view taller
view open
```

`slender` 是默认较瘦长角度，兼顾四个位点的分离；`taller` 更瘦，但部分位点更靠近；`open` 更展开。它们都通过刚体旋转得到，没有非等比拉伸。

保存自己的新角度与模型位置：

```text
view name MyEdit
```

随后用 `view MyEdit` 恢复。用 `view Fig1` 可恢复交付起始状态；**命名视图也保存各模型的位置**，因此移动过单个配体后，先保存 `MyEdit`，再切换旧视图，避免将手动位移一同恢复。

完成角度调整后，对 Input、Candidate 和 Ligand poses 统一导出，不能只替换其中一张后继续使用其他角度的旧图。

## 只移动某一个配体

### 按命令平移

下面只移动 B1，不移动其他三种结构：

```text
move x 1 models #2
move y -0.5 models #2
move z 1 models #2
```

单位为 Å，方向按当前屏幕坐标解释。可先每次移动 0.5–1 Å，观察它与真实口袋的关系。把 `#2` 换为 `#3`、`#4`、`#5`，分别移动 B2、B4、B5。

如果希望沿受体本地坐标轴移动，而不随屏幕旋转改变方向：

```text
move x 1 models #2 coordinateSystem #1
```

`models #2` 是对整个配体作刚体变换，键长与键角保持原样。

### 绕配体自身中心旋转

```text
turn y 15 models #2 center #2
turn z -10 models #2 center #2
```

`center #2` 把旋转中心设在该配体上，避免它绕整幅受体公转。这仍是刚体旋转，不会改变分子的内部二面角。

### 用鼠标拖动

先只选中 B1：

```text
select #2
mousemode rightMode "translate selected models"
```

随后在图形窗口按住右键拖动即可平移 B1。要旋转选中的配体：

```text
mousemode rightMode "rotate selected models"
```

这些模式也位于顶部工具栏的 **Right Mouse** 标签中。将鼠标停在图标上可看到 `translate selected models` 或 `rotate selected models` 的名称；在 Model Panel 的手形选择栏仅选中目标模型，再选相应图标即可。没有选中模型时，该模式会作用于全部模型，因此先检查选择状态。

完成后清空选择并恢复普通右键平移：

```text
select clear
mousemode rightMode translate
```

### 让候选 blob 跟随

只改整体视角时，所有模型应一起转动。只改某个配体的位置时，原 blob 仍停在旧位置。可在命令中一同移动对应的配体和 blob，例如：

```text
move x 1 models #2,7
turn y 10 models #2,7 center #2
```

四组对应为 `#2,7`、`#3,8`、`#4,10`、`#5,11`；B3 的 `#9` 没有配体。下面的同步导出脚本会按当前配体世界坐标重新生成四个 blob 和整体示意密度，所以也可以先只编辑配体，最后统一同步。这里的重新生成只适用于本编辑包的示意密度。

## 局部剖切与显隐

隐藏或显示整体密度：

```text
hide #6 models
show #6 models
```

在最终 pose 和候选 blob 之间切换：

```text
hide #2-5 models
show #7-11 models
hide #7-11 models
show #2-5 models
```

每两行是一组。受体与密度的相机和缩放保持不变。

`B_局部剖切.cxs` 只隐藏遮挡配体的少量前景 ribbon，完整原子仍在 `#1`。恢复完整 cartoon 用 `cartoon #1`。若当前角度下希望隐藏某段 ribbon，可以在 Model Panel 选择受体，再在图中 Ctrl+单击选中相应残基，执行：

```text
hide sel cartoons
```

恢复被选残基用 `show sel cartoons`。剖切只改变展示，不将局部口袋贴到其他受体上。

## 保存会话与导出图片

保存当前完整编辑状态：

```text
save "C:/Users/15919/Desktop/论文草稿/temp/my_overview.cxs" includeMaps true
```

`includeMaps true` 将地图内嵌进会话。重新打开这个 CXS 后，角度、模型位置、颜色、显隐和地图都能恢复。也可用 **File → Save**，文件类型选择 ChimeraX session；保存为新文件即可保留交付原件。

单张预览可用：

```text
save "C:/Users/15919/Desktop/论文草稿/temp/my_overview.png" width 1200 height 1500 supersample 3 transparentBackground true
```

`supersample 3` 用更高采样改善边缘，`transparentBackground true` 保留透明背景。透明 PNG 在部分查看器中会显示为黑底；插入白底 PPT 后以实际效果为准。需要纯白底预览时改成 `transparentBackground false`。

### 同一视角导出整套素材

完成透明度、角度和配体位置编辑后，在命令行执行编辑包中的脚本：

```text
runscript "C:/Users/15919/Desktop/论文草稿/画图/总览图_ChimeraX/同步导出.py"
```

脚本从当前会话读取相机和模型位置，按当前世界坐标重新生成示意密度与对应 blob，然后导出：

| 文件 | 对应 PPT 内容 |
|---|---|
| `Input-density.png` | Input 上半部分密度 |
| `Input-receptor.png` | Input 下半部分受体 |
| `Candidate.png` | Candidate blob 全局图 |
| `Ligand-poses.png` | 最终全局 pose 图 |
| `blob-B1.png` 等五张 | Match 栏的五个 blob；按透明边界裁切后等比使用 |
| `B1.sdf`、`B2.sdf`、`B4.sdf`、`B5.sdf` | 当前世界坐标中的四个配体，供后续编辑 |
| `Edited-global.cxs` | 本次全局编辑状态，内嵌新地图 |
| `export_manifest.json` | 相机矩阵、统一画布、配体中心和标签投影位置 |

输出位置会显示在 Log 中，默认是本仓库 `temp/overview_manual/日期_时间/`。四张主图的画布均为 1200×1500，使用同一正交相机和场宽；脚本不重新居中，也不自动改变你的视角。`before-export.cxs` 保存同步前的状态，可用于返回。

## 放回 PowerPoint

| 页码 | 组件或预览 |
|---|---|
| 1、2 | 作者历史图与 baseline，保留 |
| 3、5 | 左侧 A/B：分列或数字顺序布局 |
| 4、6 | 右侧 A/B：完整受体或局部 ribbon 剖切 |
| 7 | 左 A 与右 A 组合预览 |
| 8 | 左侧 C：密度疏网格、55% 透明受体，与 D 组配套 |
| 9 | 右侧 D55：完整受体 55% 透明 |
| 10 | 左 C 与右 D55 组合预览，建议先看这一页 |
| 11、12 | 右侧 D35、D70：35%、70% 透明度对照 |

每半幅是一个原生组合，复制整个组合到另一页后保留位置和尺寸即可组合，不能分别拉伸其中的分子图片。A/B 左侧配 A/B 右侧；C 左侧与 D 组右侧使用同一密度网格表示，D35/55/70 均可直接替换。

需要替换图片时，先进入相应组合选中内部图片，在 **图片格式 → 更改图片 → 从文件** 中选择新 PNG。Candidate 与 Ligand poses 的图片框均为 **177.6×222 点**，Input 两张图片框均为 **72×90 点**。同组内保持位置、宽高及锁定纵横比。

角度或配体位置改动后，B1–B5 的可编辑标签也要移到新位置。`export_manifest.json` 的 `blob_label_centres_pixels` 给出 1200×1500 画布中的中心；把标签放在对应轮廓旁，保留留白。Match 的缩略图应使用本次同名 `blob-B*.png`，避免全局与缩略图轮廓不一致。

最后在整页大小下核对：五个候选中有四个最终 pose；B1/B2 同为绿色；B3 只有 Reject；B4 为金黄、B5 为粉色；密度、受体和配体能通过表示及图例分别认出。

## 官方说明

本教程的命令及界面位置依据本机 1.10.1 官方文档，并在交付会话中核对。更完整的选项可查：

- [透明度与 target 参数](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/transparency.html)
- [密度显示、阈值、表面和网格](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/volume.html)
- [整体与单模型平移](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/move.html)
- [旋转中心及模型旋转](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/turn.html)
- [命名视图](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/view.html)
- [Right Mouse 工具栏及选中模型移动](https://www.cgl.ucsf.edu/chimerax/docs/user/tools/mousemodes.html)
- [Model Panel 的眼睛、选择栏与按钮](https://www.cgl.ucsf.edu/chimerax/docs/user/tools/modelpanel.html)
- [Volume Viewer 的阈值与颜色选择器](https://www.cgl.ucsf.edu/chimerax/docs/user/tools/volumeviewer.html)
- [会话、内嵌地图和 PNG 保存](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/save.html)

结构来源：[1STP](https://www.rcsb.org/structure/1STP)、[3RDQ](https://www.rcsb.org/structure/3RDQ)、[2RTL](https://www.rcsb.org/structure/2RTL)。逐原子字段、来源下载地址与固定重建入口另保存在项目 e2e 图表追溯记录。
