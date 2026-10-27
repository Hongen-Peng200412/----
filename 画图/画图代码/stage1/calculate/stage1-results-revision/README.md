# Stage 1 主结果与候选质量图

本目录从已冻结的 Stage 1 统计生成主结果及补充候选图。所有绘图组件通过 SVG 转成原生 PPT 文字、线条、柱、散点和路径。候选图集只写本次构建目录，追加原图集是另外的发布步骤。

当前默认条件为 `explicit_emdb_level`，读取 `stage1/output/stage1-results-revision/explicit_emdb_level/data/{plot_data.json,completion_panels.json}`；新 `stage1-overall-performance` 为两行三列，上行全配体、下行全部小分子，依列为总体指标、逐 PDB 语义 Dice 配对、实例 P/R。原图元、方法颜色、bootstrap 和小提琴定义保持。`stage1-candidate-quality` 仍生成原四面板候选，供候选预算结果在补充材料中选用；`stage1-strict-threshold` 与 `stage1-completion-curves` 同步读取新条件。`EMAP2LIG_CONDITION=no_level` 显式选择旧冻结输入及原四面板主性能版式，不覆盖旧产物。

该环境变量用于直接运行 `plot.py`。使用统一重建入口时，旧条件必须选择带后缀的图名，例如 `python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure stage1-overall-performance-NO_LEVEL`；统一入口以追溯记录绑定条件，不依赖外部遗留环境变量。

新 `plot_data.json` 增加 `condition="explicit_emdb_level"` 和 `paired_metric="dice"`；其余字段沿原契约，`paired_counts` 相应按语义 Dice 计算。`statistics_summary.json` 保存各指标均值、配对数及完成度，`small_per_pdb.jsonl` 保存94个PDB的小分子并集TP/FP/FN和实例指标。`data/gt_masks/<pdb>.npz` 是94份原始真值稀疏掩码，`gt_masks/sources.json` 逐份记录服务器原路径、字节数与SHA-256；`data/provenance/small_molecule_recompute.py` 冻结原小分子评价定义。GT／CA2的全部既有绘图统计保持原样，原Emap小分子P/R与PRAUC已逐PDB复现后才应用新条件。

## 代码与阅读顺序

1. `plot.py::main` 读取固定 PDB 轴及完成度记录，并用相同抽样索引生成12根完成度柱的区间。
2. `plot.py::draw_panel` 绘制总体性能、逐 PDB 比较、P/R 分布和完成度柱图；`export_figure` 导出同源图稿及对齐报告。
3. `flatten_positioned_text`展开Matplotlib公式的定位tspan，标准小数点与下标基线保留为逐字可编辑文字；SVG、PDF和PPT同源。
4. `build_deck.mjs` 将 `scenes.json` 的几何和文字装入四页可编辑 PPT。

## 输入与科学契约

- `../../output/stage1-main-sixpanel/v5/data/plot_data.json`：顶层 `cohorts.full/small`，各自含固定 `ids`、逐方法 `values`、冻结 `bars` 与 `distribution`。例如 `cohorts.full.models.Cryo.bars.oto03.mean=0.5408831328191608`。`oto03/oto05` 为实例级 PRAUC，不改原接口键。
- `../../../e2e/output/find-build-shared/data.json`：顶层 `panels` 为列表，本图只选择 `scope=find_full/find_stage1_small` 及 `domain=GT/CA2/Emap2lig`。例如 `find_stage1_small_CA2` 含94个PDB、821个实例。`distributions["100"]` 中每条记录保存 PDB、成功实例数、真实实例数、候选上限和完成比例。

总体范围为179 PDB／2,502实例，小分子为94 PDB／821实例。P/R 使用冻结最终候选的一对一匹配；完成度累计候选排序中的首次命中，保留背景和重复命中的候选位置，忽略归属于范围外真实配体的候选。两种口径共享覆盖阈值0.3，但不互相替换。

完成度均值先逐PDB求比例再等权平均；10,000次PDB bootstrap共享集合内抽样索引，种子20260922，区间取2.5%和97.5%分位数。没有检出的PDB保留为0。Dice、PRAUC及P/R直接沿用冻结值。配对图沿用分辨率色条及等比例坐标；0–1指标图从0起，图内PRAUC使用标准0.3／0.5数学下标。

## 构建产物

```text
<FIGURE_BUILD_ROOT>/
├─ stage1-overall-performance.{svg,pdf,png}  # level 六面板／no_level 四面板整体性能
├─ stage1-candidate-quality.{svg,pdf,png}    # P/R与完成度
├─ stage1-strict-threshold.{svg,pdf,png}     # 0.5阈值补充图
├─ stage1-completion-curves.{svg,pdf,png}    # 完整六面板曲线
├─ *.alignment.json                       # 最终物理尺寸的面板几何核验
├─ source_data.csv                        # 1,638条逐PDB完成度观测
├─ completion_summary.csv                 # 12根柱的均值、区间和PDB数
├─ statistics.json                        # bootstrap参数、柱统计和配对计数
├─ manifest.json                          # 图名、物理尺寸与双语图注
├─ scenes.json                            # 可编辑形状清单
└─ candidate.pptx                         # 新增四页候选
```

`source_data.csv` 的 `completion` 是0–1比例，例如 `success_count=2,target_count=4,completion=0.5`；`candidate_percent=100` 表示候选上限等于真实实例数。`completion_summary.csv` 的 `mean/lower/upper` 也为0–1比例，绘图时才乘100。

完整重建由 [所属追溯](../图表追溯.md) 登记；从仓库根运行 `python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure stage1-candidate-quality`，或替换为其余三个图名。每个入口重建共享四页候选，最终按指定稳定图名返回受检页及来源。旧temp不可作为输入。此目录仅共享SVG几何运输和完整曲线图元，不重新计算模型结果。
