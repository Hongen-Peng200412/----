# Find–Build 公平比较图

本目录从统一管线结果生成三页论文图，不执行 Find、Match、Build 或姿态评价。图中的完成度沿用已冻结的逐 PDB 分布和精确阶梯事件；姿态图使用共同命中实例的配对数值，不用真实中心对接替代预测中心对接。

## 数据与产物

输入根是论文仓库的 `画图/formal/fmb_20261015/sources/`。GT、CA2、Emap2lig 每个目录各有 `docking_results.jsonl`、`completion.json`，直接来自服务器统一根 `Adaligand_E2E/test/test_0/evaluation/`。

### data.json

`assemble_data.py` 在 `画图/formal/fmb_20261015/` 写出此字典。`panels` 原样合并三个条件的完成度面板，包括完整 PDB 分母、各预算分布和精确事件曲线。`pairs.GT`、`pairs.CA2` 各含：

- `common_count`：两种 Find 共同命中的实例总数。
- `all_rows`：共同命中实例列表，按 PDB 和原 occurrence 编号连接。`tuned_blob`、`emap_blob` 保留各自来源 blob 编号；四项距离为模型 Top-1 与 best-of-50 的世界坐标 RMSD，单位 Å，失败为 `null`。
- `numeric_rows`、`numeric_count`：两种模型的四项距离均有数值的配对集合及数量，用于箱图和中位数。
- `statistics`：各模型和姿态的均值、中位数、5/25/50/75/95百分位，以及严格 RMSD <2 Å、<3 Å 成功数。成功率分母仍为 `common_count`。
- `paired_differences`：同一实例中 tuned 距离更低的数量及 paired median(tuned−Emap2lig)，保留配对比较的可追溯统计。

`paired_pose.csv` 保留 `all_rows` 中全部共同实例；缺失距离留空。`summary.json` 保存配对统计和每个完成度面板在五种固定预算下的均值、中位数，不改变实例判胜。

### 完成度面板

完成度为一个 PDB 中已经成功处理的不同实例数除以该 PDB 的目标实例数 N；相对预算 ρ 对应向下取整的 floor(ρN) 次计费尝试。小分子面板固定 77 个 PDB、446 个实例，全配体 Find-only 固定 179 个 PDB、2,502 个实例，未检出和零候选 PDB 保留。均值和中位数均在完整 PDB 轴上计算，均值为 PDB 等权宏平均。

- `curve.budget_percent`、`curve.mean`、`curve.median`：长度相同的列表，依次为预算事件百分比、该事件后的平均完成比例和中位完成比例；绘图只转换比例单位，不重算事件。
- `distributions["50"/"100"/"200"/"300"]`：相应预算下每 PDB 一条记录；`pdb_id` 定位 PDB，`completion` 为 [0,1] 的完成比例。散点与小提琴使用同一分布。
- Find-only 全配体每个 blob 计费；Find-only 小分子与假定身份正确的 Build 均为背景计费、真实范围外前景免费。Find-only 只要求既有对应成立；Build 还要求原姿态排名中的 top-1 或 best-of-50 重原子 RMSD 严格小于 2 Å 或 3 Å。一次成功只增加一个不同实例。

### 可编辑图

所有渲染与装配中间文件位于 `temp/fmb_20261015/`，包括三组 SVG/PDF/PNG、对齐报告、`manifest.json`、`scenes.json` 和候选 PPT。

| 图标识 | 排列 | 科学内容 |
|---|---|---|
| `find-only-instance-completion` | 2×2 | 全配体／小分子 × GT／CA2，纯 Find 实例完成度 |
| `stage3-predicted-region-head-to-head` | 2×2 | GT／CA2 两项共同命中比较，各有 Top-1 与 best-of-50 |
| `supp-find-correct-match-build` | 2列6行 | Emap2lig、LigandSeek-CA2、LigandSeek-GT，各有 Top-1／best × 严格2／3 Å |

`manifest.json` 是按页排列的字典列表，每页包含图标识、点单位的宽高及双语图注。`svg_shapes.py` 复用现有 SVG 形状展开代码，将文字、散点、箱体、阶梯与小提琴分别保留为可编辑对象；`assemble.mjs` 将这些同源几何装配为原生 PPT，不重新计算统计。`ppt_metadata.py` 复用既有 PowerPoint 文件接口，将双语图注写入备注、唯一图标识写入传统批注，并导出实际渲染供验收；需要 Windows PowerPoint 与 pywin32。

`scenes.json` 在每页 manifest 字典中增加 `shapes` 列表。坐标原点为该页原始 SVG 左上角，x 向右、y 向下，长度与字号均为 pt（1/72 英寸）。装配时统一换成 CSS px，并把整页图形垂直居中，不改变组件间几何。

| 形状字段 | 含义 |
|---|---|
| `kind` | `text` 为文字框，`ellipse` 为独立椭圆，`path` 为路径 |
| `x/y/w/h` | 形状框左上角和宽高，pt；文字框旋转另由 rotation 表示 |
| `parts` | 仅路径使用的子路径列表；每项为 [点数,2] 的 XY 坐标，相对于该形状框左上角，pt |
| `text/font/bold/rotation/color` | 文字、字号(pt)、粗体、旋转角度(度)和颜色；文字不转轮廓 |
| `fill/stroke`、`fill_alpha/stroke_alpha` | 填充和描边颜色，以及 [0,1] 不透明度（0透明，1不透明）；`none` 表示不绘制 |
| `stroke_width/dash` | 描边宽度(pt)及原 SVG 虚线设置；装配保留实线/虚线含义 |

## 使用顺序

从论文仓库根依次执行：

```powershell
python 画图/画图代码/stage3/fmb_20261015/assemble_data.py
python 画图/画图代码/stage3/fmb_20261015/plot.py
python 画图/画图代码/stage3/fmb_20261015/svg_shapes.py
node 画图/画图代码/stage3/fmb_20261015/assemble.mjs
python 画图/画图代码/stage3/fmb_20261015/ppt_metadata.py
```

`completion_plot.py` 提供多次复用的原完成度绘图与导出函数，`plot.py` 决定三页布局和双语图注。先检查 PDF 对齐、字体与碰撞，再检查 PowerPoint 实际渲染；通过后发布图集，并按仓库转换工具编译中英文正文与补充材料。正式计算、源版本及运行状态统一记入 AdaLigand 的本轮总日志，不在本目录另建实验日志。
