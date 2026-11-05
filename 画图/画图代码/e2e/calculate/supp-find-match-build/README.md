# 自动身份匹配后的Find–Match–Build补图

两张图分别选择CA2和GT的actual面板，包含同一77个PDB、446个合格小分子。三行依次为Top-1、Top-5、best-of-50，两列为严格RMSD <2 Å、<3 Å。曲线为PDB等权均值和中位数，小提琴与散点为50%、100%、200%、300%预算下完整PDB分布。

输入与统计契约沿用[Top-5共享数据说明](../e2e-top5-revision/README.md)。`data/master.json`在同次构建中由共享`prepare_data.py`从长期冻结输入生成；本入口读取`actual_{CA2,GT}_pose{1,5,50}_rmsd{2.0,3.0}`面板，不改变原事件、分母或计费。图形复用`find-build-shared/completion_plot.py`，原生可编辑PPT复用`e2e-top5-revision/build_pptx.py`。这两张图与给定正确身份的补图共用画法，实际身份匹配和计费仍沿各自冻结协议。

构建目录由`FIGURE_BUILD_ROOT`指定。输出为`figures/supp-find-match-build-{ca2,gt}.{svg,pdf,png}`、对齐报告、含稳定图名及双语图注的`manifest.json`，以及两页`candidate.pptx`。不读取旧temp，不修改正式图集。

在仓库根用`D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure supp-find-match-build-ca2`或gt对应图名完整重建，生成统计、两图及带来源的`rebuilt.pptx`。直接运行plot.py只完成绘图阶段。
