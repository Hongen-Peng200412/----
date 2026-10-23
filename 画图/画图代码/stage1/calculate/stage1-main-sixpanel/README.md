> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Stage1 六面板主结果图

本任务将 test_0 的全配体（179 PDB）与小分子-only（94 PDB、821 实例）并排展示。科学计算与画图分层：`science/` 读取评估事实并产生统计，绘图代码只读取已计算的数据。源实验文件始终只读。

## 文件职责与修改入口

| 文件 | 职责与常改参数 |
|---|---|
| `science/compute_small_pr.py` | 在服务器只读补算小分子 P/R，输出 JSON；固定原始最终选择，不重新调阈值 |
| `science/prepare_plot_data.py` | 本地 macro 均值、PDB bootstrap、分布统计；`BOOTSTRAP_N`、`SEED`、`KDE_BANDWIDTH` 在文件顶部 |
| `science/replace_tau05.py` | 读取已保存的逐 PDB PRAUC@0.5，将 v3 绘图数据中的第三组柱图换为 0.5，重新计算其 macro 均值与区间；其余指标逐字段沿用 v3 |
| `plot_config.py` | 颜色 `COLORS`、字号 `FONT`、点大小、透明度、尺寸、色条范围与输出版本 |
| `plot_figures.py` | 六张独立图与三行两列组合；`rect` 控制坐标轴比例与间距，备注由 `caption` 生成 |
| `svg_to_scene.py` | SVG 转原生形状清单；文本保持可编辑，散点为独立椭圆，曲线为折线 |
| `build_deck.mjs` | Artifact Tool 生成七张可编辑幻灯片；组合页的标题、图例和配对坐标轴文字按正式图集第 19 页的位置装配 |
| `finalize.mjs` | 检查新生成的七页候选、字体与包结构，写入 `regenerated/` 并把收据保存在 `temp/` |

当前显示名称更新后的图在 `画图/画图代码/stage1/output/stage1-main-sixpanel/v5/`；其 `data/` 与 v4 相同，统计结果未改。`v4/backup/` 保存 0.6 版图集和修改前正文。冻结的原始评估数据仍在上一层 `data/server_metrics_and_pr.json`。`v3` 保留 0.6 的整套结果用于复现，`v4` 仅换 0.5，`v5` 仅更新显示名称。正式图集为 `画图/stage1结果.pptx`，第 1–6、19 页已同步更新。装配、渲染与验证中间文件在论文根目录 `temp/`。

## 指标口径

三方法为 Find_1 真实受体、Find_1 CryoAtom2 受体（均 F2–F1 Gaussian）及 Emap2lig 官方 Find/Li。原始数据保留这些标识；图和正文统一显示为 Ligandseek-Find（注明受体来源）及 Emap2lig-Find。这里只读取主结果，不改变先前 basic 推理族的切换开关和消融结果。

P/R 依据原始 NPZ 的 `candidate_selected`，不是 PRAUC 扫描时的候选选择。预测与 GT 的双向覆盖均不小于 0.30 才能形成边；按覆盖率几何均值最大、并列时 occurrence 编号最小，固定候选的配体类别归属。归属非小分子的候选忽略，未归属候选保留为可能的假阳性。对剩余最终选择和小分子 GT 做最大基数二分匹配，P=匹配数/选择数，R=匹配数/GT 数；空预测 P=0。补算结果逐项验证原报告的忽略数量和小分子 GT 数。

两列柱图依次展示 Semantic Dice、one-to-one PRAUC@0.3、one-to-one PRAUC@0.5，均按 PDB 等权。均值误差线为 10,000 次 PDB bootstrap 的百分位 95% 区间，种子 20260922；同一 cohort 内方法与指标共享重采样索引。小提琴白点为中位数，粗线为四分位范围；0 和 1 的样本全部保留，密度采用边界反射。散点水平抖动只影响显示，不改变纵坐标。配对图仍采用 one-to-one PRAUC@0.3，相等容差为 1e-12，色条固定 1.0–4.0 Å。

小分子列使用 GT 归属进行评价范围过滤，不能将它解释为模型自行识别小分子的能力；两列样本和 GT 范围不同，不把均值变化解释为性能提升。

## 重现

当前构建以冻结的 v5 绘图数据生成七页候选，每页自行写入独立 `@@图名` 和备注。详细输入、函数和当前命令见[所属追溯文档](../图表追溯.md)。从论文仓库根目录运行：

```powershell
$code='画图/画图代码/stage1/calculate/stage1-main-sixpanel'
$env:STAGE1_FIGURE_VERSION='v5'
& D:/Anaconda/python.exe -B "$code/plot_figures.py"
& D:/Anaconda/python.exe -B "$code/svg_to_scene.py"
$node='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
& $node "$code/build_deck.mjs"
& $node "$code/finalize.mjs"
```

中间清单和候选在 `temp/stage1_main_sixpanel_20260929/`，新候选另存 `stage1/output/stage1-main-sixpanel/regenerated/`，保留既有正式图集和冻结数据。统计阈值的科学转换仍保留在 `science/replace_tau05.py`，其字段和版本关系见本页指标口径及所属追溯。

历史19页图集合并脚本 [merge_atlas.ps1](../../../archive/calculate/publication-history/stage1/stage1-main-sixpanel/merge_atlas.ps1) 和定页替换脚本 [replace_tau05.ps1](../../../archive/calculate/publication-history/stage1/stage1-main-sixpanel/replace_tau05.ps1) 已归档，仅用于解释当时的发布过程，不作为当前调用入口。两者依赖历史备份和固定页号，不能用于更新作者当前图集。历史命令与验收事实见[执行记录](执行记录.md)。

## 正文与 Word

正文按独立图名 `stage1-main-sixpanel` 定位主结果，当前案例图的直接入口单列在[阶段追溯](../图表追溯.md)。双语图注在所属正式PPT备注中维护，来源批注按追溯文档同步。Word的图号、图注空间、导图和回转统一由[转换工具](../../../../../转换工具/README.md)管理；当前流程不调用历史图集定页替换或Word排版后处理脚本。
