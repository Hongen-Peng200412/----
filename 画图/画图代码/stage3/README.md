# Stage3 配体姿态图

本目录保存三张正文图的绘图代码、逐实例绘图数据和来源哈希。`画图/stage3结果图_可编辑.pptx` 是三页成品图集；每页由 PowerPoint 原生点、线、箱体和文字组成，备注是 Word 图注。`画图/formal/stage3/` 保存相同数据的 PDF、SVG、PNG、TIFF 印刷预览及 `summary.json`。

前两张图使用 446 个 Stage3 测试实例，分别绘制 Top-1 和 50 个候选中的最低重原子 RMSD。第三张图比较 Find 预测与目标小分子双向覆盖均达到 30% 后、三种方法都有可评价姿态的 237 个共同实例：local_cov-C 的真实受体 C0、CryoAtom2 受体 C0，以及使用 Find 预测 blob 的 Emap2lig-Build。箱体为第 25–75 百分位数，横线为中位数，须为第 5–95 百分位数；每个点对应一个实际 RMSD，纵轴为对数刻度。第三张图的比较同时包含两种方法所获定位输入的差异。

`data.json` 中的 `series` 来自八份冻结 PocketXMol `occurrences.json`，其服务器原路径与 SHA-256 分别记录在各组的 `source`、`source_sha256`。本地只读副本位于 `temp/stage3_source/`。Emap2lig-Build 的原始逐实例结果来自 `C:/Users/15919/Desktop/Emap2lig/测试Find出来的Build/结果与日志/正式产物/build_occurrences.jsonl`；其哈希在 `build_source_sha256`。本地 `pocket_comparison.json` 的哈希也保存在数据文件中。`assemble_data.py` 会核对 446 个完整实例及 Find 命中 243 个实例的编号，并逐项比对先前汇总中的 PocketXMol RMSD。六条 Build 输入筛选失败保留在 `data.json` 中，第三张 RMSD 图只绘制共同有数值的 237 条。

重建数据与图集的命令如下。PowerPoint 图名批注由最后一条命令写入。

```powershell
& D:/Anaconda/python.exe 画图/画图代码/stage3/assemble_data.py --pocket-dir temp/stage3_source --build-dir C:/Users/15919/Desktop/Emap2lig/测试Find出来的Build/结果与日志/正式产物 --output 画图/画图代码/stage3/data.json
& D:/Anaconda/python.exe 画图/画图代码/stage3/plot_stage3.py
& C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe 画图/画图代码/stage3/build_editable_deck.mjs
& 画图/画图代码/stage3/finalize_editable_deck.ps1
```

正文在 `论文草稿.md` 中通过 `stage3-top1-full`、`stage3-best-full`、`stage3-find-hit-head-to-head` 三个图名引用该图集。Word 编译使用仓库的 `md_to_word.py`，其临时文件保存在 `temp/`。
