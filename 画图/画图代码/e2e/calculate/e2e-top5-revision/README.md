# E2E Top-5 主图与三种方法的 Find–Build 补图

本目录从论文仓库已有的候选、计费事件和姿态评价生成四张可编辑图：`e2e-main-top5`，以及 `supp-find-correct-match-build-{emap2lig,ca2,gt}`。主图沿作者提供的2×2模板；三张补图分别为3×2，行是Top-1、Top-5、best-of-50，列是严格RMSD <2 Å和<3 Å。

英文正文当前使用作者编辑的 `e2e-main-top5(v1)`。其原生排版冻结于 `output/e2e-top5-revision/author-v1/`，共享统计定义不变；v1另有局部横向运输入口，保留作者简化文字与间距。

完整重建使用仓库根的既有入口：

```powershell
D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure e2e-main-top5
```

一次运行同时生成四张同源图及4页候选PPT。候选不自动替换正式图集。固定运行环境为 `D:/Anaconda/python.exe` 的NumPy 1.26.4、Matplotlib 3.9.2、SciPy 1.13.1；纯Python PPT包从仓库固定 `.manuscript_deps/` 读取，不从旧temp加载依赖。

作者v1使用同一重建入口的独立选择：

```powershell
D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure "e2e-main-top5(v1)"
```

此选择依次重新生成科学统计、原尺度与加宽参考图，再从作者冻结原件运输为单页原生候选。候选保留v1双语图注，逐点比对925个科学曲线路径点；不能以旧PNG代替重绘。`ops/widen_author_v1.py --publish --build-root <本次构建目录>`只在作者未另行保存时发布v1页和来源批注，其他页和图注部件逐字节保留。

## 产物位置

下列科学输入的冻结副本与可再生产物分别保存，不互相覆盖。

```text
## <科学产物>
画图/画图代码/e2e/output/e2e-top5-revision/
├─ data/master.json            # 全部40个面板、逐PDB分母和预算事件、统计摘要
├─ data/source_data.csv        # 17,950条面板×固定预算×PDB观察
└─ template/                   # 作者提供的两份Python模板原始字节

画图/画图代码/e2e/output/e2e-top5-revision/author-v1/
├─ author_v1.pptx              # 作者当前14页图集的冻结排版原件；使用第10页
├─ layout.json                 # a图显示倍率、对象编号和预算锚点
└─ validation.json             # 完整重建、对象保全、版面核查及Word发布的完成证据

## <其他文件>
temp/figure_rebuild/<运行号>/e2e-main-top5/
├─ data/                       # 本次从冻结原评价重新生成的绘图输入（计算中间文件）
├─ figures/                    # 四张SVG、PDF、PNG及对齐报告（可再生辅助导出）
├─ manifest.json               # 四页图名、物理尺寸与双语备注（可再生工具输入）
├─ native-shapes.json          # 各页原生对象计数（运行诊断）
├─ candidate.pptx              # 四页独立原生形状与文本（可再生辅助导出）
└─ rebuilt.pptx                # 带当前图注与来源批注的候选（可再生辅助导出）
```

## 科学输入与统计

全配体范围包含179个PDB、2,502个实例；合格小分子范围包含77个PDB、446个实例。合格小分子为单残基、相对于模板无缺失原子的有机小分子。分母不因检测、匹配、构象生成或姿态失败而缩小。

共享的显式level面板来自 `../find-build-shared` 对应的 `e2e/output/find-build-shared/explicit_emdb_level/data.json`；Emap2lig逐姿态原评价来自 `补充数据/Emap2lig_双条件/explicit_emdb_level/build/build_occurrences.jsonl`。正确身份假设下GT／CA2结果来自 `e2e/output/find-build-shared/sources/{GT,CA2}/docking_results.jsonl`。实际Match结果来自 `e2e/output/e2e-accounting/{GT,CA2}/evaluation.json` 和同目录 `docking_results.jsonl`；全配体实际匹配完成度沿用 `e2e/output/e2e-instance-completion/completion.json`。

每个PDB的完成度为预算内成功的不同实例数除以完整目标数，再给所有PDB相同权重求均值和中位数。百分比预算 `percentage` 允许 `percentage*N//100` 次计费尝试，例如一个目标实例在50%预算下允许零次。原候选顺序、范围外前景处理、背景计费和同实例去重规则保持原冻结协议。实际Match使用原 `attempt_index`；给定正确身份的Emap2lig必须使用 `selected_blob_events.json.charged_attempt`，原 `find_rank` 未扣除免费跳过项，不能替代计费号。

Top-1、Top-5、best-of-50分别使用原模型排名前1、5、50个构象中的最低重原子RMSD。仅读取原评价，不重新排名、对齐或计算坐标误差。严格成功条件为RMSD <2 Å或<3 Å，等于阈值不成功。新Top-5采用与原1／50相同的候选事件；程序在新增前逐项复现20个原条件的成功事件及完整固定预算分布。

## `data/master.json`

一个文件表示四图共用的统计容器，顶层为 `metadata`、`panels`、`summaries`。

| 字段 | 含义及对齐 | 具体值或示例 |
|---|---|---|
| `metadata.condition` | 固定实验条件，显式给Emap2lig官方入口提供EMDB推荐值，官方实际阈值为L/2 | `"explicit_emdb_level"` |
| `metadata.bootstrap_replicates`、`bootstrap_seed` | 完整PDB轴的重采样次数与种子；同一范围的所有方法和预算使用同一组抽样索引 | `10000`、`20261020` |
| `panels[panel_id]` | 一个评价条件；键包含任务、方法、原排名姿态数和阈值 | `"assume_Emap2lig_pose5_rmsd2.0"` |
| `pdb_count`、`occurrence_count` | 完整PDB与真实实例分母 | 小分子为`77`、`446` |
| `success_events[pdb_id]` | 该PDB内每个成功实例及首次成功计费号；重复候选不重复增加成功实例 | `[{"occurrence_id":0,"first_success_attempt":1}]`，仅为字段格式示例 |
| `distributions[budget]` | 预算下完整PDB记录；键为百分数文本 | `"100"`、`"300"`；零成功PDB仍有记录 |
| `curve` | 精确有理数预算下的宏平均与中位数；比例单位为0–1 | 三分之一预算保存为`budget_numerator=1`、`budget_denominator=3` |
| `polyline` | 给作者模板提供的事件阶梯；`budget_percent`与`mean_percent`逐项对齐 | `is_step=true`；百分比在绘图时使用post阶梯，不插值 |
| `all_candidates_final` | 用尽全部候选后的结果；300%只限制展示横轴 | 候选与计费总数继承同协议原面板，不把显示截点当执行终点 |
| `summaries[panel_id][budget]` | `mean`、`median`、`ci_low`、`ci_high`均为百分比；区间为bootstrap均值的2.5%／97.5%分位数 | Emap2lig Top-5、<2 Å、100%的`mean=33.7054107508653` |

固定预算逐PDB记录的真实格式为 `{"pdb_id":"11jb","success_count":78,"target_count":78,"attempt_budget":78,"completion":1.0}`；它对应GT Find-only、100%预算。背景或失败不会生成成功事件，但其PDB记录始终存在。

## `data/source_data.csv`

一行对应 `panel_id`、`budget_percent` 与 `pdb_id` 唯一确定的观察。另含 `success_count`、`target_count`、`attempt_budget` 和0–1单位的 `completion`。例如同一PDB在不同姿态条件或预算下占不同的行，不能把这些行当独立重复实验。每个面板每个预算都包含全部77或179个PDB。

## 图形与备注接口

`manifest.json` 每项的 `id` 是独立 `@@` 图名，`stem` 指同次 `figures/` 文件前缀，`width`、`height` 单位为pt，`notes` 为中文在前、独立 `ENGLISH:` 行后为英文的双语图注。补图复用原 `find-build-shared/completion_plot.py::draw_panel`，只拆方法组和增加Top-5行。主图以159.262 mm版心导出，字号、线宽与标记一起按物理比例设置；SVG文字保持可编辑。

`prepare_data.py` 负责完整事件与摘要；`plot_main.py` 负责作者2×2主图；`plot_supplement.py` 负责三张原样式补图和备注；`build_pptx.py` 仅将同源SVG运输为原生PPT对象。推荐先读本契约与冻结面板，再按这个顺序阅读入口。SVG运输已补齐Matplotlib的font简写解析，保留实际字号与粗体。

`ops/publish.py` 只负责向当前 `画图/E2E结果.pptx` 追加新页。它复用作者Hongen Peng／HP的现代批注身份，原页图形、备注、媒体和批注逐部件保留，替换前检测并发保存。执行状态与核验记录见[本轮执行记录](../../../../../talk/e2e_top5_20261102/执行记录.md)，四图当前用途见[所属追溯文档](../图表追溯.md)。

## 作者v1的横向显示契约

`layout.json.figure`固定为 `e2e-main-top5(v1)`，`source_pptx`为同目录 `author_v1.pptx`，`source_sha256`标识本次冻结原件。`a_left_emu`、`a_width_emu`以PPT原点为基准，单位EMU；`x_stretch=1.1798592265168129`表示0%纵轴固定后所有预算横向距离的共同倍率。预算标值仍是0／50／100／200／300%；没有改为340%轴上限。

`curve_panels`将原生对象64–68连接到五个全配体面板，如 `"64":"find_full_GT"`。`x_ticks`将对象编号连接到预算；误差线及数据标记按原预算中心移动，帽宽、圆点大小和视觉错位量保留。`reference_and_note_ids`为100%参考线与作者合并后的注记，`percentage_ids`为五个300%末端标签。横向增量为 `a_width_emu * budget / 400 * (x_stretch - 1)`；百分比标签随300%预算移动并保留作者设置的文字间距。

`plot_main.py`的 `a_x_stretch`默认为1，以兼容原版；`--author-v1`同时输出未重新简化曲线的原尺度核验图及加宽参考图。`ops/widen_author_v1.py::build_v1`逐点核对本次科学重绘，只允许105个对象的横位置及五条曲线横向尺寸改变，361个对象完全保留。所有对象的纵位置、纵向尺寸、文字和样式均核对不变。其输出 `v1-preservation.json`记录每个允许变化与科学路径误差；原始几何报警、原生PDF和Word排版复核留在本次temp。当前执行范围见[v1执行记录](../../../../../talk/e2e_v1_widen_20261102/执行记录.md)。

`author-v1/validation.json`保存本轮完成时的科学文件散列、925点核对、原生对象保全、字号／对齐结果、碰撞原始计数与人工判定，以及八份Word的发布散列和相关页码。它是只读完成证据，不是绘图输入；清空temp后仍可阅读，但后续作者保存的正式PPT和Word可具有新的文件散列。
