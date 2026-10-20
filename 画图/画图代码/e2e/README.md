# 端到端结果图

## 当前图集与 Find–Build 直接比较

`画图/E2E结果.pptx` 当前包含四页：全配体 top-k success、小分子 top-k success、给定正确身份的完整 Find–Build 完成度曲线，以及正文使用的四面板分组柱状图。前三页沿用已有组件和双语图注；第四页图内只有图例、面板条件和坐标标签，评价前提写在图注中。

运行 `D:/Anaconda/python.exe -B 画图/画图代码/e2e/plot_find_build_direct.py` 生成第四页的同源图形与装配清单。输入为 `画图/formal/fmb_20261015/data.json` 中的十二个 `assume` 面板；每个面板含相同的77个PDB、446个小分子实例。脚本只读取100%和300%预算的既有逐PDB完成比例，不重新推理或修改计费。柱高为PDB等权均值；同一77-PDB轴进行10,000次有放回重采样，所有条件共用索引，以2.5%和97.5%分位数给出区间。

输出统一位于 `temp/emap2lig_direct_20261020/`：`source_data.csv` 保存1,848个逐PDB观测，字段为面板、构象数、RMSD阈值（Å）、预算（%）、方法、PDB编号和完成比例（0–1）；`summary.csv` 保存24根柱的PDB数、均值及区间上下界（均为%）。`direct.svg`、`direct.pdf`和`direct.png`共享同一几何；`manifest.json`保存唯一图名、180×118 mm尺寸和双语图注，`scenes.json`增加原生形状清单，长度与坐标单位为pt。新页图名为`e2e-find-build-direct-comparison`，旧曲线页仍为`supp-find-correct-match-build`。

本轮PPT原生归并与验收脚本位于上述临时目录。当前发布位置和执行证据见[执行记录](../../../RULES/执行记录.md)。下面保留早期top-k图的生成说明，不作为当前四页图集的发布清单。

## 历史 top-k 绘图流程

正文现在使用两份一页一图的可编辑 PPT：`画图/E2E结果_全配体.pptx`
显示 179 个 PDB 的 Find/Find+Match，`画图/E2E结果_小分子三联图.pptx`
按 a/b/c 堆叠 77 个 PDB 的 Find/Find+Match、真实受体单次 local_cov-C
姿态、CryoAtom2 受体单次 local_cov-C 姿态。两图的 K 均为 1～10，
每个面板都有自己的刻度与右侧竖排图例。图 11b、c 的阈值是严格
RMSD <2 Å / <3 Å；Best-of-50 为事后上界。正文不引用 C→C、C→C→E。

运行 `D:/Anaconda/python.exe 画图/画图代码/e2e/build_nature_figures.py`
生成两份 PPT；每个组件都是 PowerPoint 原生可编辑形状。对应预览图和
PDF 仅保存在 `temp/`，`论文草稿.md` 通过图名批注引用 PPT，并把
备注中的中文图注带入 Word。冻结计数仍由下述 `data.json` 提供。

原六页 `画图/E2E结果.pptx` 保留作历史及迭代策略附图，不随正文图重排。

## 冻结计数与原六页图集

`data.json` 保存六页折线图所用的逐 K 成功 PDB 数。每条数组按 K=1～10 排列；完整测试集分母为 179 个 PDB，Stage3 小分子及构象重建的分母为 77 个 PDB。图中的点只使用冻结评价产物的精确计数，没有插值。

前两页的 Find／Find+Match 曲线来自 Matcher 正式评价。小分子 Find 与 Emap2lig-Find 曲线另与 `Matcher/测试结果与追溯/测试结果总览/小分子stage3专用测试集.md` 的逐 K 表核对。后四页的姿态曲线从 PocketXMol 正式端到端评价的 `docking_results.jsonl` 按 `attempt_index ≤ K` 和固定 77-PDB 名单重新汇总；K=1、3、5、10 的数值已与原 `evaluation.json` 主表逐项相等。姿态结果依次使用 `local_cov-C`、`C-C`、`C-C-E` 的原记录，未重新运行模型。

历史脚本 `build_editable_figures.py` 曾生成六页图集；当前保留的成品为 `画图/E2E结果.pptx`。其第五、六页分别保存 CryoAtom2 条件下 C→C 和 C→C→E 的附加图，不进入正文或 Word。该脚本中旧输出文件名只反映当时生成图集的路径。

图片预览、PDF 和碰撞核查文件留在仓库 `temp/`。修改正式图及图注时，重建 PPT 后再运行 `D:/Anaconda/python.exe md_to_word.py`，以 `论文草稿.md` 为正文源稿。

原六页图集每页均由 PowerPoint 原生形状构成，没有嵌入位图。此前导出的六页 PDF 已通过文字审计（最小字形约 10 pt）及碰撞审计（0 项警告、0 项失败）。Matplotlib 源码预检器不识别 PowerPoint 原生形状及其 PDF 导出，故其 SVG 专项提示不适用于本图集。
