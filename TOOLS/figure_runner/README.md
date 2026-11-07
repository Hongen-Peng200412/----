# 按 Figure 运行与检查来源

本套件读取 `画图/画图代码/<类别>/<图目录>/figure.json`，不内置图号、实验根和统计口径。声明包括 `kind`、`figures`、`pptx`、`entry`、`outputs`；表格设 `kind=table`，不强行要求 PPT。

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/figure_runner/run.py --figure "正文/Fig3-result-Find"
D:/Anaconda/python.exe -X utf8 -B TOOLS/figure_runner/run.py --all
D:/Anaconda/python.exe -X utf8 -B TOOLS/figure_runner/provenance.py --check
D:/Anaconda/python.exe -X utf8 -B TOOLS/figure_runner/provenance.py --sync
```

`--figure` 接受完整目录标识或唯一完整图名，可重复指定。`--build-root` 指定根 temp 下的新空目录；默认生成本次时间目录。每个单元独立执行，只使用本次构建目录。守卫禁止读旧 temp，限制项目内写入本次目录。启动日志与读审计放本次根的 `logs/<图目录>/`，不污染单图入口需要的空输出目录；`summary.json` 保存本次执行证据，不作科学输入。候选完整图名集合必须等于声明。

`--check` 只读核对本图说明、唯一页面及 `TRACE v3`。`--sync` 仅替换或补齐来源短指路，沿用既有批注身份，保持图形、备注和其它批注；本次比较副本只放 temp。它检查可定位性，不代替科学与视觉验收。

`annotate_candidate(candidate, figure_directory)` 为各图入口生成的本次候选补齐相同指路。独立数字不通过运行器执行，其字段和算式写在 `追溯文档/claim/`。
