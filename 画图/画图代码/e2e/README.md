# 端到端结果图

`data.json` 保存六页折线图所用的逐 K 成功 PDB 数。每条数组按 K=1～10 排列；完整测试集分母为 179 个 PDB，Stage3 小分子及构象重建的分母为 77 个 PDB。图中的点只使用冻结评价产物的精确计数，没有插值。

前两页的 Find／Find+Match 曲线来自 Matcher 正式评价。小分子 Find 与 Emap2lig-Find 曲线另与 `Matcher/测试结果与追溯/测试结果总览/小分子stage3专用测试集.md` 的逐 K 表核对。后四页的姿态曲线从 PocketXMol 正式端到端评价的 `docking_results.jsonl` 按 `attempt_index ≤ K` 和固定 77-PDB 名单重新汇总；K=1、3、5、10 的数值已与原 `evaluation.json` 主表逐项相等。姿态结果依次使用 `local_cov-C`、`C-C`、`C-C-E` 的原记录，未重新运行模型。

运行 `D:/Anaconda/python.exe 画图/画图代码/e2e/build_editable_figures.py` 生成 `画图/E2E结果图_可编辑.pptx`。脚本用 PowerPoint 原生文字、线段、圆点绘制图形。每页的 `@@` 批注是 Word 转换器的图名，备注是中文图注。正文只引用前四页；第五、六页分别保存 CryoAtom2 条件下 C→C 和 C→C→E 的附加图，不进入正文或 Word。

图片预览、PDF 和碰撞核查文件留在仓库 `temp/`。修改正式图及图注时，重建 PPT 后再运行 `D:/Anaconda/python.exe md_to_word.py`，以 `论文草稿.md` 为正文源稿。

最终 PPT 共六页，每页均由原生 PowerPoint 形状构成，没有嵌入位图。导出的六页 PDF 已通过文字审计（最小字形约 10 pt）及碰撞审计（0 项警告、0 项失败）。Matplotlib 源码预检器不识别 PowerPoint 原生形状及其 PDF 导出，故其 SVG 专项提示不适用于本图集。
