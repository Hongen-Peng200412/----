# Stage1 严格匹配与无 level 补充图

本目录管理 `stage1-additional-analysis`（显式 level，2×3）与 `stage1-no-level-comparison-NO_LEVEL`（无 level，2×2）。两图共享同一评价补算和原生图元运输，科学输入按条件分别保存，不覆盖旧结果。正式页追加在 `画图/stage1结果.pptx`，PPT 备注是双语图注的维护源。

当前两图按作者正文 v1 的风格压缩行列空白, 保留全部图元、字体与图例。2×3 的中列另左移画布宽度的 0.018 以平衡视觉空白, 上下行同步, 面板宽高不变；其 b/e 横向等间距检查具有明确作者布局豁免, 其他对齐与碰撞仍验收。2×2 保留容纳四组 P/R 的宽面板。原生批注署名沿用作者 `Hongen Peng`（HP）。

先读 `prepare_data.py` 的逐 PDB 装配，再读 `plot.py` 的预算统计及面板顺序；实例匹配唯一实现为 `stage1-main-sixpanel/science/compute_small_pr.py::evaluate_selected`。条形图、小提琴和 SVG 导出共享 `stage1-results-revision/plot.py::draw_panel/export_figure`，原生装配共享该目录 `build_deck.mjs`。新目录不复制匹配或图元定义。

## 冻结输入与范围

原无 level 指标来自 `stage1/output/stage1-main-sixpanel/v5/data/plot_data.json`；显式 level 指标来自 `stage1/output/stage1-results-revision/explicit_emdb_level/data/plot_data.json`。GT／CA2 全配体 0.5 P/R 从原 `data/server_metrics_and_pr.json` 读取；新 Emap2lig 全配体从双条件归档中的 `official_find_li.jsonl` 读取。小分子原始交集由旧 `evaluation_metadata/source_receipt.json` 的 `local` 指定；新 Emap2lig 交集来自 `补充数据/Emap2lig_双条件/explicit_emdb_level/find/held_out_test_0/evaluation/per_pdb/`。类别文件由同一 receipt 的 `occurrences` 定位。

全配体为 179 PDB／2,502 实例，全部小分子为 94 PDB／821 实例。`candidate_selected` 是冻结最终选择；实例 P/R 使用最大一对一匹配。小分子类别归属固定按 0.3 双向覆盖及覆盖率几何均值确定，并列取较小实例编号；切换到 0.5 只改变匹配边。空候选 P/R 保留 0。先逐 PDB 复现原 0.3 指标，再使用 0.5 补算值。

预算柱图只读取显式 level 的 `completion_panels.json`，按 `scope=find_full/find_stage1_small` 与 `domain=Emap2lig/CA2/GT` 选择。100%／300% 对应每 PDB 真实实例数的一倍／三倍候选上限；命中阈值仍为 0.3，首次命中累计，背景及重复命中占位置，归属其他类别的候选在小分子视图忽略。均值按 PDB 等权；10,000 次 bootstrap，种子 20260922，取 2.5%／97.5% 分位数。小提琴沿原图在 0/1 两端反射 KDE，带宽读取冻结值。

## 输出与字段

下列科学输入保存在同一 `stage1/output/stage1-additional-analysis/data/` 物理目录：

```text
## <科学产物>
stage1/output/stage1-additional-analysis/data/
├─ conditions.json       # 两条件的固定 PDB 轴、指标、条形图区间及小提琴分布
└─ source_data.csv        # 1,638 条条件×范围×方法×PDB 的七项指标
## <其他文件>
stage1/output/stage1-additional-analysis/data/
└─ verification.json     # 原 0.3 复现差异和 0.5 均值（运行统计）
```

`conditions.json` 顶层键为 `explicit_emdb_level` 和 `no_level`；各含 `cohorts.full/small`，其 `ids` 是长度 179／94 的固定 PDB 轴。`models.Emap/Cryo/GT.values` 的每个列表沿该轴排列；`dice/oto03/oto05` 分别为 Dice／实例 PRAUC@0.3／@0.5，`precision/recall` 为 0.3，`precision05/recall05` 为 0.5，均为 0–1 比例。例如无 level 的全配体 `bars.oto05.mean=0.12617247318175615`。`distribution` 的 `grid/density` 是 161 点的 0–1 KDE 网格及归一化宽度，`quartiles` 为 [25%、50%、75%] 分位数；`bars` 保留原冻结的 `mean/lower/upper`。

`source_data.csv` 每行对应 `(condition,cohort,method,pdb_id)`，如 `(no_level,full,Emap,9lfa)`；其余七列与上述 `values` 同名。`verification.json` 的 `comparisons` 包含 12 组条件×范围×方法，`original_precision_recall_max_error` 是原 0.3 指标逐 PDB 最大绝对差，应为 0，`precision05_mean/recall05_mean` 为新阈值 PDB 等权均值。

当前构建目录由 `FIGURE_BUILD_ROOT` 指定，`prepare_data.py` 在其 `data/` 内重新生成上述三份统计，`plot.py` 只读取同次生成的 `data/conditions.json`。只有单独运行准备程序且不指定该变量时，才写上述长期统计留档；完整重建不改写留档或原始结果。构建目录还包含两图的 SVG/PDF/600 dpi PNG、对齐 JSON、`scenes.json`、`manifest.json`、`candidate.pptx` 和预算 CSV。`budget_source_data.csv` 每行是范围、方法、PDB、预算，`success_count/target_count` 是成功／真实实例数，`candidate_limit` 是候选上限，`completion` 是二者比例；`budget_summary.csv` 的 `mean/lower/upper` 为 0–1 比例，图中才乘 100。

完整入口从仓库根运行，均先补算再绘图与原生装配，不依赖旧 temp：

```powershell
python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure stage1-additional-analysis
python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure stage1-no-level-comparison-NO_LEVEL
```

两命令都会生成共享两页并返回所选稳定图名。完整来源、关联图、正式页与核验范围以[Stage1 计算追溯](../图表追溯.md)为准；原始结果和历史页保持不变。
