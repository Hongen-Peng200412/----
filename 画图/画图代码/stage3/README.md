# Stage3 配体姿态图

本目录保存两张正文图的绘图代码、逐实例数据和来源哈希。`画图/stage3结果.pptx` 是两页成品图集；每个观测点、箱体、坐标轴和文字都是 PowerPoint 原生对象，页面备注用于 Word 图注。`画图/formal/stage3/` 保存 PDF、SVG、PNG、TIFF 印刷预览及 `summary.json`。

图 7 使用 446 个 Stage3 测试实例，上、下两行分别绘制 Top-1 和 50 个候选中的最低重原子 RMSD。图 8 比较 Find 预测与目标小分子双向覆盖均达到 30% 后、三种方法都有可评价姿态的 237 个共同实例：local_cov-C 的真实受体 C0、CryoAtom2 受体 C0，以及使用 Find 预测 blob 的 Emap2lig-Build；Top-1 与 Best of 50 是各有完整纵轴的两个子图。箱体是第 25–75 百分位数，横线是中位数，须是第 5–95 百分位数。两条细虚线分别标出 2 Å 和 3 Å。图 7 中大于 50 Å 的点在顶端 `50+` 区画为三角形；所有分位数仍由未截断的原始 RMSD 计算。

`data.json` 中的八组 `series` 来自冻结的 PocketXMol `occurrences.json`，原始路径和 SHA-256 分别保存在 `source`、`source_sha256`。本地只读副本位于 `temp/stage3_source/`。Emap2lig-Build 的逐实例结果来自 `C:/Users/15919/Desktop/Emap2lig/测试Find出来的Build/结果与日志/正式产物/build_occurrences.jsonl`，其哈希保存在 `build_source_sha256`。`assemble_data.py` 校验完整测试集的 446 个实例、Find 命中的 243 个实例，并与既有 PocketXMol 汇总逐项比对。六条 Build 输入筛选失败仍保留在 `data.json`；图 8 只绘制三种方法共同有 RMSD 的 237 条。

绘图和汇总命令：

```powershell
& D:/Anaconda/python.exe 画图/画图代码/stage3/assemble_data.py --pocket-dir temp/stage3_source --build-dir C:/Users/15919/Desktop/Emap2lig/测试Find出来的Build/结果与日志/正式产物 --output 画图/画图代码/stage3/data.json
& D:/Anaconda/python.exe 画图/画图代码/stage3/plot_stage3.py
& C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe 画图/画图代码/stage3/build_editable_deck.mjs
& 画图/画图代码/stage3/finalize_editable_deck.ps1
```

最后一条命令从 `temp/stage3-deck-build/user-stage3-before-merge.pptx` 复制用户的图注文字，只把原图 9 的编号改为图 8，在临时目录产生带图名批注的候选 PPT。视觉验收通过后，再发布为 `画图/stage3结果.pptx`。正文在 `论文草稿.md` 中使用 `stage3-official-tuned` 与 `stage3-find-hit-head-to-head` 两个图名引用成品。Word 由仓库的 `md_to_word.py` 编译。
