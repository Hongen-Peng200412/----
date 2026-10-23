> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Stage1 四例主图与三种显示风格

本版对应 `stage1六框可视化_v2.pptx` 的更新。

这套图用同一个真实配体对照受体、真实标注区域和三种方法的预测。正文采用 **9PQM、9UWI、9WUP、9RMI** 四行；PPT 同时保留此前六例和新增 9PQM，共七个 PDB。每个 PDB 只有一个放大实例、一份含完整数据的 ChimeraX 会话，六格和三种风格共用相机。每行左上角以 a–d（或 a–c）标识实例；身份、颜色含义和方法顺序放在 PPT 备注中。

## 成品和会话

- [七页 PPT](../../../stage1六框可视化_v2.pptx)：第 1–2 页为 baseline，第 3–4 页为绿色受体与灰色密度网格，第 5–6 页为灰色密度表面与蓝色预测网格，第 7 页为正文四例主图。
- [新版 Nature Word](../../../../论文草稿.nature.docx)：由正文 Markdown 和第七页 PPT 编译。
- [Results 文字](Results与图注.md)、[图注源文件](captions.json)、[制作方案](方案.md)、[执行记录](执行记录.md)。图注的出版入口是 PPT 备注。

| PDB | 原样会话 | 唯一放大实例 | 用途 |
| --- | --- | --- | --- |
| 9PQM | [session.cxs](../../output/stage1-fourcase-main/display/9pqm/session.cxs) | ATPγS / AGS，A:401，occurrence 0 | 正文第 1 行，共同检出 |
| 9UWI | [session.cxs](../../output/stage1-fourcase-main/display/9uwi/session.cxs) | 胆固醇 / CLR，B:502，occurrence 3 | 正文第 2 行，覆盖完整性 |
| 9WUP | [session.cxs](../../output/stage1-fourcase-main/display/9wup/session.cxs) | NADPH / NDP，A:1104，occurrence 3 | 正文第 3 行，目标区域漏检 |
| 9RMI | [session.cxs](../../output/stage1-fourcase-main/display/9rmi/session.cxs) | ADP，C:401，occurrence 2 | 正文第 4 行，重建受体的影响 |
| 9WQ3 | [session.cxs](../../output/stage1-fourcase-main/display/9wq3/session.cxs) | 1SY，E:401，occurrence 3 | 风格对照第 1 页第 2 行 |
| 9X0X | [session.cxs](../../output/stage1-fourcase-main/display/9x0x/session.cxs) | 磷脂酰乙醇胺 / PTY，T:801，occurrence 7 | 风格对照第 1 页第 4 行 |
| 9BJJ | [session.cxs](../../output/stage1-fourcase-main/display/9bjj/session.cxs) | A1AP0，F:1001，occurrence 18 | 风格对照第 2 页第 1 行 |

使用 `D:/ChimeraX 1.10.1/bin/ChimeraX.exe`，即 **UCSF ChimeraX 1.10.1**。旧版 UCSF Chimera 无法直接打开 `.cxs`。会话嵌入了密度，打开时不需要连接服务器。它保存的是最终网格密度风格下的 Find 真实受体局部图；另外两种风格通过下方原生命令切换。

## 我如何原样复现

1. 在 ChimeraX 菜单 File → Open 打开上表的一份会话。如果已经打开另一 PDB，先在命令栏输入 `close all`。
2. 用 Tools → General → Command Line 显示命令栏。下面的命令全部粘贴在这里，**不是 PowerShell 或 Python**。
3. 输入 `windowsize 960 720`，保持局部画面的 4:3 比例。然后按需要逐组粘贴下列六组命令。每组都恢复相同的 `local` 视角，只改变哪些模型显示。

左上，真实受体：

```text
hide models; show #2 models; view local
```

中上，CryoAtom2 受体：

```text
hide models; show #3 models; view local
```

右上，真实配体原子与正式 GT ligand-area：

```text
hide models; show #4,8 models; view local
```

左下，Find 使用真实受体：

```text
hide models; show #1,2,4,5 models; view local
```

中下，Find 使用 CryoAtom2 受体：

```text
hide models; show #1,3,4,6 models; view local
```

右下，Emap2lig：

```text
hide models; show #1,4,7 models; view local
```

这些是原生命令，没有定义任何别名。`local` 和 `overview` 是 ChimeraX 保存的视角名称，不是命令别名。六格中出现的配体原子始终是同一真实实验结构，蓝色区域才是模型的预测结果。

要重新生成某个 PDB 的三种风格、所有 PNG 和会话，打开相应的 `<pdb>_reproduce.cxc`，或将其中的原生命令按组粘贴。开头的 `runscript open_data.py` 只加载十二个基础模型和保存会话；此后的颜色、透明度、相机和导图均为可见的 ChimeraX 命令。该文件会覆盖本次生成的 PNG 与会话，手工版本请另存。

## 我如何调整相机角度和远近

先恢复基准，再做一次调整，最后另存自己的视角：

```text
view local
turn y 15
turn x -10
zoom 0.85
view name my_local
```

`turn y 15` 向左右方向转动 15°，`turn x -10` 向上下方向转动 −10°；`turn z 10` 在画面内转动 10°。`zoom 0.85` 拉远，相同内容缩小到当前的 85%，视野宽度扩大到约 1.176 倍；`zoom 1.15` 拉近。连续执行会累积，因此每次试验从 `view local` 开始更容易比较。

本版已经按照用户两次反馈扩大取景：原六例中除 9WUP 外，视野宽度相对旧版扩大约 47%；9WUP 重新旋转后以配体居中，并将原来的视野宽度扩大约 18%。9WUP 的邻近预测较大，因此同一局部图需同时容纳目标和该邻近区域。本次在该相机基础上再执行 `zoom 1.05`，使显示物体放大 5%、视野宽度变为此前的 1/1.05。局部受体显示范围扩大到配体周围 15 Å 的完整残基，实验密度范围扩大到 7 Å；增加的是周围上下文，预测与 GT 掩码不变。

保存 `my_local` 后，六组切换中的最后一条改成 `view my_local`，即可用同一新相机重做整组六框。直接输入 `view local` 可恢复交付视角。若只想改远近，这两条即可：

```text
view local
zoom 0.85
```

若想把放大中心重新定位到配体，可用 `show #4 models; view #4`；它也会重新缩放。每个 `<pdb>_local.cxc` 给出了从默认坐标方向出发的精确旋转、居中、`zoom pixelSize` 和最后 `zoom 0.85`、`zoom 1.05`，可逐行重建本版视角。`pixelSize` 是当前窗口下每像素的 Å 数；较大值对应更宽视野，所以应同时保留文件中的 `windowsize`。

## 我如何调颜色和透明度

编号固定如下。对 `#2,3` 同时操作可让两种受体保持相同美术风格；对 `#5-7` 同时操作可让三种预测保持相同外观。

| 编号 | 内容 | 颜色和透明度命令对象 |
| --- | --- | --- |
| #1 | 完整实验密度 | `volume #1 ...` |
| #2、#3 | 真实受体、CryoAtom2 受体 | `color #2,3 ... target c`；`transparency #2,3 ... target c` |
| #4 | 当前唯一真实配体 | `color #4 ...` |
| #5、#6、#7 | 三种方法的目标预测 | `volume #5-7 ...` |
| #8 | 当前实例的正式 GT 区域 | `volume #8 ...` |
| #9、#10、#11 | 各方法完整选定预测的并集 | 整体图默认显示 #9 |
| #12 | 所有标注小分子的真实原子 | 用于整体定位 |

例如，将受体改成绿色，设为 55% 透明；将配体碳原子改成橙色，保留氧、氮、磷等元素本色；将预测设为蓝色、60% 透明：

```text
color #2,3 #94ad9f target c
transparency #2,3 55 target c
color #4 byelement
color #4 & C #c97b29
volume #5-7 color #239fd0 transparency 0.60
```

这里有两套单位：`transparency ... 55 target c` 使用 **0–100 的百分数**；`volume ... transparency 0.60` 使用 **0–1 的比例**。数值越大越透明。`target c` 指受体的 cartoon，不是原子或密度。

恢复交付的网格密度风格，逐行粘贴：

```text
color #2,3 #94ad9f target c
transparency #2,3 55 target c
color #4,12 byelement
color #4,12 & C #c97b29
volume #1 style mesh color #75838b transparency 0.45 squareMesh true meshLighting false
volume #5-7,9-11 style surface color #239fd0 transparency 0.60
volume #8 style surface color #9fbfc7 transparency 0.70
```

切换到参考论文的 baseline：

```text
color #2,3 #aaaab5 target c
transparency #2,3 40 target c
color #4,12 byelement
color #4,12 & C #8e9098
volume #1 style surface color #c9c9d2 transparency 0.80
volume #5-7,9-11 style surface color #27a9e0 transparency 0.50
volume #8 style surface color #7fcfe7 transparency 0.55
```

切换到突出密度表面的第三种风格：

```text
color #2,3 #94ad9f target c
transparency #2,3 70 target c
color #4,12 byelement
color #4,12 & C #c97b29
volume #1 style surface color #7c858b transparency 0.82
volume #5-7,9-11 style mesh color #239fd0 transparency 0 meshLighting false squareMesh true
volume #8 style mesh color #8daeb8 transparency 0 meshLighting false squareMesh true
```

ChimeraX 1.10.1 对多个透明表面的排序有限制：位于前面的透明模型可能让后面的透明模型消失。第三种风格让密度为透明表面、预测边界为不透明网格，以减少这种遮挡。正文选用密度网格风格，便于连续观察配体和预测覆盖范围。

## 我如何调整口袋和密度的显示范围

相机只决定“看多大”；下列命令决定“显示哪些周围结构”。例如把受体范围从 15 Å 改为 18 Å：

```text
hide #2,3 cartoons
cartoon (#2,3 & (#4 :< 18))
```

`:<` 按完整残基选取。下面将密度显示范围从距配体 7 Å 改为 9 Å：

```text
volume zone #1 nearAtoms #4 range 9 newMap false minimalBounds true
```

范围调整不会重新计算模型的预测。三种方法比较时使用同一密度范围和同一相机。`volume #1 level 数值` 可改变实验密度的显示等值面；每个 PDB 的原始值记录在 `data.json` 的 `contour` 中，并在复现命令里明确写出。预测和 GT 使用二值掩码的 0.5 等值面、`step 1`、`surfaceSmoothing false`，保证三种方法的绘图处理一致。

## 我如何看整体、回到局部和保存

整体图：

```text
windowsize 960 675
hide models
show #1,2,9,12 models
cartoon #2
transparency #2 0 target c
volume unzone #1
volume #1 region all step 1 style surface color #92949c transparency 0.65
volume #9 style surface transparency 0.60
view overview
```

返回局部后，重新应用局部范围和交付风格：

```text
windowsize 960 720
hide #2,3 cartoons
cartoon (#2,3 & (#4 :< 15))
volume zone #1 nearAtoms #4 range 7 newMap false minimalBounds true
volume #1 style mesh color #75838b transparency 0.45 squareMesh true meshLighting false
transparency #2,3 55 target c
hide models
show #1,2,4,5 models
view local
```

只调用 `view local` 不会自动撤销你修改的颜色、显隐、局部密度范围。它恢复的是相机；上述返回命令同时恢复这些局部设置。

导出无文字图片，例如：

```text
save "C:/Users/15919/Desktop/论文草稿/temp/my_find_real.png" width 1440 height 1080 supersample 2
```

另存你的完整会话：

```text
save "C:/Users/15919/Desktop/论文草稿/temp/my_9uwi.cxs" includeMaps true
```

`includeMaps true` 将密度一起保存，便于以后离线打开。要导出整组六框，按上方六组切换，每次保存不同文件名。为保证公平比较，一组六图只使用一个保存的相机。

## 从数据到论文图的分析思路

先选定一个真实实例，再根据正式评估找到对应的选定预测，核对 precision、recall 和 Dice；随后在同一物理坐标中叠加真实原子、GT、密度与预测。对有交集的例子，视角应能看见未覆盖部分；对无交集的例子，要显示目标和邻近预测之间的空间关系。二维图上的遮挡不能代替三维体素交集的计算。

9PQM 用于共同检出：真实受体 Find / CA2 Find / Emap2lig 的 Dice 为 0.816 / 0.816 / 0.766。9UWI 的 Emap2lig precision 为 0.990，但 recall 只有 0.300，因此不能只根据局部落点准确就称其完整。9WUP 的目标 NADPH 与所有正式选定 Emap2lig 预测都没有交集，图中显示其最近的候选；这不表示整个 PDB 都没有预测。9RMI 中 CA2 仍覆盖 81.0% 的目标区域，但区域扩展导致 precision 降低。Results 按这些证据描述差异，而不是把四个实例当成总体性能估计。

新增例筛选覆盖已有 71 个至少含两个小分子的 PDB，按同一实例的三方法指标筛选。原六例不换 occurrence；正文用 9PQM 替换 9X0X，9X0X 继续保留在 PPT。PDB 排名和局部指标是两种层级，完整数值见 [selection_metrics.csv](../../output/stage1-fourcase-main/display/selection_metrics.csv)。PRAUC 存在大量并列第一，排名采用竞赛排名并保留并列说明。9UWI 和 9BJJ 延续上一版按视觉目的放宽 PDB 排名的选例。

新增 9PQM 含六个小分子，其真实受体条件下的 PDB 级小分子 Dice 为 0.795，在 94 个 PDB 中排名第 23，处于前 24.5%。上文 0.816 是所展示实例的 Dice，不能与 PDB 级指标混用。

## 数据和脚本的分工

- [原下载脚本](base/fetch_data.py)：只读下载基础数据和已有推理结果，并记录来源与 SHA-256。
- [原转换脚本](base/prepare_data.py)：将数组转换为 MRC/mmCIF，核对正式候选、交集和原子坐标。基础数据仍保存在 `画图/画图代码/stage1/output/stage1-fourcase-main/base/`；本轮的 `open_data.py` 直接读取其中 assets，本轮新会话则嵌入数据并独立保存。
- `open_data.py`：按固定顺序加载十二个模型并建立一份会话，不设置外观、透明度或相机。
- `common_style.cxc`、`contrast_style.cxc`、`density_style.cxc`、`<pdb>_local.cxc`：所有显示参数和相机的原生命令。
- `<pdb>_reproduce.cxc`：从基础数据完整重建该 PDB 的三种风格和原样会话；`<pdb>_six_views.cxc` 提供六组独立切换命令。
- `write_commands.mjs`：只负责把人可读的原生命令写入文件；`build_deck.mjs` 将 ChimeraX PNG、原生框线与图注装配成 PPT；`compile_word.py` 调用项目转换器并应用图版分页。

MRC 数组按 ZYX 储存，原子按 XYZ 表示，单位 Å。源网格的 corner origin 加半个 spacing 后写入 MRC 首体素中心；裁去 mask 外围零体素时同步移动 origin，非零体素不变。会话中的 receptor 来自实际推理 token；目标配体保留沉积 CIF 的 auth 编号。详细坐标核对见每例 `data.json`。

配体身份以沉积 CIF 为准，并核对 RCSB 的 [AGS](https://www.rcsb.org/ligand/AGS)、[CLR](https://www.rcsb.org/ligand/CLR)、[NDP](https://www.rcsb.org/ligand/NDP) 和 [ADP](https://www.rcsb.org/ligand/ADP)。AGS 是 ATPγS；本例 NDP 是 NADPH，不能写作 NADP+。版式参考 Li 等论文第 12 页，拓展为六个局部面板。
