# Stage2 结果图

此目录从已经冻结的 Matcher 和 EMERALD-ID 测试计数绘制 Stage2 论文图，不运行模型，也不重新计算测试预测。当前论文使用两张双面板图：第一张合并真实受体与 CryoAtom2 的六轴比较，第二张合并两个受体条件下 strongest 按 PDB 身份数分组的结果。`data.json` 保存正确数、支持数和冻结前景 F1；百分数按正确数除以支持数计算。`plot_stage2_pairs.py` 生成同内容的印刷图文件，`build_editable_deck.mjs` 生成 PowerPoint 原生图形。

## 冻结数据及图的含义

- 六轴图：四个 Matcher 变体在 179-PDB `held_out_test_0` 上的 selected 候选结果。前景 F1 使用各模型在 validation 冻结的阈值；身份准确率只统计真实前景、身份受支持的 selected 候选。自顶端顺时针依次为总体 SMILES、小分子、糖、前景 F1、金属离子和肽类。图 4a 和 4b 分别对应真实受体与 CryoAtom2；肽类在各条件下只有一个候选，支持数写在图注而不写在图内。EMERALD-ID 仅在小分子轴用菱形标出独立真实位点上至少一个身份取得有效评分时的准确率：真实受体为 82.6%（282 个位点），CryoAtom2 为 84.0%（313 个位点）。它不提供前景 F1 或其他类别身份准确率。雷达径向下界是 20%，轮廓面积不作为指标。
- strongest-1 分类折线图：图 5a 和 5b 分别对应真实受体与 CryoAtom2。横轴是测试 manifest 中该 PDB **实际提供给 Matcher 的精确 SMILES 去重数**，五种及以上合并为 `≥5`。纵轴是对应类别 selected、真实前景、身份受支持候选的正确数除以支持数。该图不是所有真实 occurrence 的已知位点准确率；肽类只有横轴为 1 的单个观察值。

`plot_stage2.py` 保留先前六张单图的历史绘制方法；论文当前不展示其中两张小分子真实位点直接对比图，`plot_stage2_pairs.py` 也不生成它们。保留原脚本与冻结 `data.json`，便于追溯已核对的计数，不将历史图误认为本版论文结果。

原始数字分别可核对 [完整测试集总览](../../../../Matcher/测试结果与追溯/测试结果总览/全测试集.md)、[真实受体小分子位点结果](../../../../Matcher/测试结果与追溯/测试结果总览/nxu小分子真实测试.md)、[CryoAtom2 小分子位点结果](../../../../Matcher/测试结果与追溯/测试结果总览/nxu小分子CryoAtom2测试.md)。strongest-1 横轴分组由其服务器冻结 `frozen_test.json` 的逐候选结果与对应测试 manifest 身份表只读汇总；每一类别各组的正确数与支持数加和必须与正式实验报告的分类总数相等，绘图脚本在执行时检查该等式。

## 输出

运行 `D:\Anaconda\python.exe 画图/画图代码/stage2/plot_stage2_pairs.py`，在 `画图/formal/stage2/` 输出同名 PDF、SVG、600 dpi PNG、600 dpi TIFF 和面板对齐检查记录。运行 `build_editable_deck.mjs` 后，再运行 `finalize_editable_deck.py`，生成 `画图/stage2结果图_v6_可编辑.pptx`。该文件的两页分别对应图 4 和图 5；每页的 a/b 面板分别有相同图例。线条、标记和文字均为 PowerPoint 原生对象，可独立编辑，没有整页位图。每页备注保存相应中文图注，图名批注供 Markdown 转 Word 时定位。

`build_deck.mjs` 与 `office_compatibility.py` 是此前把 PNG 放入 `画图/stage2结果图_v3.pptx` 的历史实现；该版本整页是图片，不满足当前的可编辑要求。当前稿件只引用 v6 原生对象图集；图 4、图 5 各占一页，每张图内部的 a/b 面板共用图注。

此前的 `论文草稿.nature.stage2.v3.docx` 仍指向历史位图版本，不用于核对当前 PPT。Markdown 的两处 `pptfig` 引用现指向 v6 原生对象图集。`论文草稿.nature.stage2.v6.docx` 是按当前 Markdown 生成的检查稿；为使图 4 和图注同页，仅将该图注设为 10 磅、1.3 倍行距，没有修改正文、PPT 图形或图注文字。Word 转换器会把 PPT 页导出为图片嵌入 Word；需要编辑图形时应打开 v6 PPT。
