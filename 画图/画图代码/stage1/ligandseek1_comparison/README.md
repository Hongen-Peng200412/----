# LigandSeek2-Find 与 LigandSeek 比较图

本目录拥有六张版本比较图的长期绘图代码与规格，不承担推理或科学评估。`prepare_plot_data.py` 从冻结逐 PDB 指标生成柱图、小提琴和配对散点所需统计；它不导入模型或评估包，不读取概率图或体素掩码，不计算交集、匹配、PRAUC、成员资格或哈希。真实 179-PDB 双受体测试及 149／94 视图已完成并验收；本目录只读最终指标生成比较图。

## 数据与职责

绘图只读取冻结的逐 PDB JSONL／指标表以及对应的预先确定成员列表。均值、逐 PDB bootstrap 区间、KDE 和配对散点属于绘图数据准备；掩码交集、匹配、PRAUC 和小分子样本资格由 Ligandseek 的正式评估包确定，不能在本目录重算或重定。

LigandSeek 科学代码与稳定任务入口位于 `C:/Users/15919/Desktop/Ligandseek/src/ligandseek/{evaluation,execution}/` 和 `训练与运行/sh/infer/ligandseek1_held_out.sh`。其服务器正式根为 `/storage/penghongen/AdaLigand_stage1_inference/Ligandseek1/official_v1.0.0_pv`；LigandSeek2-Find 继续使用论文已冻结的结果，不重新校准或推理。

六图统计和视觉契约见[规格](规格.md)。代码组织为一个可直接阅读的公共函数 `prepare_plot_data()`：依次读取成员与指标、计算绘图统计、发布三个文件；末尾 CLI 只装配四个必需路径。测试代码见 `tests/test_plot_data.py`；渲染、测试和 Office 快照进入论文 `temp/`，不能成为长期源代码或默认入口。

## 输入和预期输出

四个必需路径分别为 `--ligandseek2-source`、`--ligandseek1-root`、`--input-manifest`、`--output-root`。输出根必须没有三个同名文件，脚本不覆盖既有产物。下面的接口已由本次最终真实指标生成，不使用测试夹具。

```text
## <科学产物>
画图/formal/LigandSeek2_vs_LigandSeek1/data/
├── ligandseek1/                             # 从验收结果复制的只读本地镜像
│   └── <deposited|inferred>/                 # 沉积受体和 CryoAtom2 重建受体两个条件
│       └── held_out_test_0/
│           ├── evaluation/official_pv.jsonl # 179 个 PDB 的正式完整评估指标
│           └── small_molecule_only/official_pv.jsonl # 94 个冻结小分子阳性 PDB 的正式指标
└── statistics/
    ├── plot_data.json                       # 固定成员、五个逐 PDB 指标、均值区间和分布
    ├── source_data.csv                      # 两集合/四方法的逐 PDB 指标镜像
    └── bar_statistics.csv                   # 两集合/四方法/三柱图指标的均值和区间
```

LigandSeek2-Find 输入为论文已经冻结的 `画图/formal/Stage1_main_sixpanel_20260929/data/server_metrics_and_pr.json`，只使用 `models.GT`、`models.Cryo` 与 `resolution`，不使用其中的 Emap2lig 指标。成员输入为 Ligandseek 正式评估的 `实验记录/held_out/inputs.json`，分别读取 `test_0_pdb_ids` 和 `small_pdb_ids`。缺少成员、顺序不同、非有限指标或指标超出 `[0,1]` 均停止，不补零或改变资格。

## 绘图数据契约

### 配对指标与分布

#### `statistics/plot_data.json`

文件是一个 JSON 对象。全局 `bootstrap_replicates=10000`、`bootstrap_seed=20260922`、`kde_bandwidth=0.045` 为固定绘图统计条件；`sources` 包含 `ligandseek2_source`、`ligandseek1_root`、`input_manifest` 三个读取路径，不包含自行计算的哈希。`cohorts.full` 对应 179 个完整 PDB，`cohorts.small` 对应冻结 94 个小分子阳性 PDB；二者重叠，不视为独立统计样本。

每个集合的字段如下，N 表示该集合 PDB 数。

| 字段 | 类型、形状与含义 | 示例值 |
| --- | --- | --- |
| `ids` | 长度 N 的字符串列表，与正式成员清单严格同序 | `["9ter", "30yu"]`，仅展示完整清单开头片段 |
| `n` | 整数，等于 `len(ids)` | 完整集为 `179` |
| `resolution` | 长度 N 的 float 列表，与 `ids` 逐 PDB 对齐，单位 Å | 如某 PDB 的 `3.5` |
| `models` | 四个固定方法的对象，`L2/L1` 为两代模型，`GT/CA2` 为沉积／重建受体 | `L1_CA2` 对应第一代 LigandSeek 的重建受体条件；图内第二代模型统一显示为 LigandSeek2-Find，第一代显示为 LigandSeek，源字段和文件名保持原样 |
| `paired_counts` | 三个整数 `l2_higher/equal/l1_higher`，合计 N；对相同 PDB 的 CA2 输入 PRAUC₀.₃ 判断方向，差值绝对值不超过 `1e-12` 为相等 | 格式如 `{"l2_higher":1,"equal":1,"l1_higher":0}`，为 2-PDB 构造示例 |

每个 `models.<method>` 包含 `values`、`bars` 和 `distribution`，不共享或合并不同 PDB 身份。

| 子字段 | 类型、形状与含义 | 示例值 |
| --- | --- | --- |
| `values.dice` | 长度 N 的 float 列表，逐 PDB 语义 F1／Dice，不是由平均 P/R 再计算 F1 | 单项如 `0.6` |
| `values.prauc_0p3/0p5` | 各为长度 N 的 float 列表，已评估的一对一 PRAUC，双向覆盖阈值分别为 0.3／0.5 | 单项如 `0.7` |
| `values.precision/recall` | 各为长度 N 的 float 列表，已评估的一对一₀.₃ P/R，包含所有 0／1 值 | 单项如 `0.0` 或 `1.0` |
| `bars.<dice|prauc_0p3|prauc_0p5>` | `mean/lower/upper` 三个 float，PDB 等权均值及 95% bootstrap 分位区间 | `{"mean":0.5,"lower":0.0,"upper":1.0}` 为格式示例 |
| `distribution.<precision|recall>.grid` | 长度 161 的 float 列表，0 到 1 的等距指标轴 | 开头为 `[0.0,0.00625]`，仅展示片段 |
| `distribution.<precision|recall>.density` | 长度 161 的 float 列表，与 grid 对齐的相对小提琴宽度，除以该曲线最大值 | 曲线最大值为 `1.0`，不是性能分数 |
| `distribution.<precision|recall>.quartiles` | 长度 3 的 float 列表，原始逐 PDB 指标的 25／50／75 百分位数 | `[0.25,0.5,0.75]` 为格式示例 |

以下是 2-PDB 构造示例，完整展示某个 `models.<method>` 的 `values` 和 `bars` 片段；省略全局字段、集合信息、其他方法以及该方法的 `distribution`。五个指标列表使用相同 PDB 顺序，不是实际模型结果：

```json
{
  "values":{"dice":[0.0,1.0],"prauc_0p3":[0.25,0.75],"prauc_0p5":[0.0,0.5],"precision":[0.0,1.0],"recall":[0.0,1.0]},
  "bars":{
    "dice":{"mean":0.5,"lower":0.0,"upper":1.0},
    "prauc_0p3":{"mean":0.5,"lower":0.25,"upper":0.75},
    "prauc_0p5":{"mean":0.25,"lower":0.0,"upper":0.5}
  }
}
```

`distribution` 只含 P/R，每条曲线的 `grid/density` 等长，`quartiles` 长度为 3。没有缺失值或补零字段。

指标读取映射明确区分旧文件名和新文件名，但不转换数值：

| 绘图指标 | LigandSeek2 完整视图及 LigandSeek1 两视图的源字段 | LigandSeek2 冻结小分子视图的源字段 |
| --- | --- | --- |
| `dice` | `semantic_macro_f1` | `semantic_dice` |
| `prauc_0p3` | `one_to_one_macro_prauc_0p3` | `one_to_one_prauc_0p3` |
| `prauc_0p5` | `one_to_one_macro_prauc_0p5` | `one_to_one_prauc_0p5` |
| `precision` | `one_to_one_macro_precision_0p3` | `one_to_one_precision_0p3` |
| `recall` | `one_to_one_macro_recall_0p3` | `one_to_one_recall_0p3` |

bootstrap 在每个集合内共同抽取 PDB 整数索引，四方法与三柱图指标使用同一组索引，完整集和小分子集分别计算。小提琴沿用原图的 `gaussian_kde([v,-v,2-v], bw_method=0.045)`，再除以曲线最大值；`0.045` 是无量纲带宽因子，核标准差为反射样本标准差乘 `0.045`，核协方差为反射样本协方差乘 `0.045²`，不是指标单位下的固定绝对标准差。中位数和四分位数从未反射的原始指标计算。

### 可核对的表格

#### `statistics/source_data.csv`

UTF-8 BOM 的 CSV，包含 `cohort,method,pdb_id,resolution_angstrom,dice,prauc_0p3,prauc_0p5,precision,recall` 九列。每行对应一个集合／方法／PDB，`cohort` 为 `full/small`，`method` 为上述四方法之一。分辨率单位 Å，其余五指标无量纲。行数为 `4×(179+94)=1092`；每个方法在各集合内保持清单顺序，小分子 PDB 也出现在完整视图中，不把这 1092 行当作独立样本数。

#### `statistics/bar_statistics.csv`

UTF-8 BOM 的 CSV，包含 `cohort,method,metric,n,mean,ci95_lower,ci95_upper` 七列。`metric` 只取 `dice/prauc_0p3/prauc_0p5`，共 `2×4×3=24` 行；`n` 为集合 PDB 数。后三个 float 对应 JSON `bars` 的 `mean/lower/upper`，数值不舍入。

## 门控命令

以下仅运行测试，不是模型正式运行命令，也不发布性能图：

```powershell
& D:/Anaconda/envs/Pocket_Plus_windows/python.exe -B -m unittest discover -s 画图/画图代码/stage1/ligandseek1_comparison/tests -v
```

正式模型命令、资源和 release 记录保存在论文 `实验记录/LigandSeek1/执行日志.md`。统计、绘图和 Office 门控分别记录，不能把测试夹具的输出当作真实模型结果。

## 图形与 PowerPoint

`plot_figures.py` 的唯一公共入口 `render_figures()` 读取已冻结 plot_data，以同一 `draw_panel()` 构造六单图和三行两列组合图，不重新计算任何统计。图内性能数值轴统一显示三位小数，0.3／0.5 阈值和分辨率色条沿用参数与单位所需精度。七组 SVG／PDF／PNG 进入指定输出根；构建根在论文 temp 中，保存 alignment、PDF 字号／碰撞报告及 `manifest.json`。manifest 的七页包含唯一图名、双语图注、pt 画布几何和文本／椭圆／路径场景；字段逐项定义见函数 Docstring。

`build_deck.mjs` 只接收该 manifest 与构建目录，按同一 SVG 几何等比写七页原生文本、椭圆和路径。它写 `candidate.pptx`、`transport_validation.json` 和检查 NDJSON，不重新画数据、不导入模型。最终交付为论文 `画图/LigandSeek2_vs_LigandSeek1.pptx`，六单图各一页，第七页为组合图；原 `stage1结果.pptx` 不改。

同源场景依赖成熟 `main_sixpanel_20260929/svg_to_scene.py` 和只含路径常量的 `plot_config.py`；不调用旧 CLI 或旧输出路径。仅文本字体度量扩展为 Calibri，旧 Arial 路径不变；场景 `font_family` 随 SVG 保留。Calibri 的阈值下标字形已实测存在，统一用下标遵守术语 E05。现代批注写明本地编辑身份的 userId/providerId，使 PowerPoint 能读取唯一图名；不使用作者账户。

Python 正式渲染参数为 `--plot-data`、`--output-root`、`--build-root`、`--nature-scripts`，JS 参数为 manifest 和构建目录。所有测试／Office 快照与兼容探测留在 temp；它们不成为正式源代码。正式导出先做 1.5 pt 对齐、PDF 最小字号和碰撞门控，再核验每一页实际 PowerPoint；结构检查不替代视觉检查。
