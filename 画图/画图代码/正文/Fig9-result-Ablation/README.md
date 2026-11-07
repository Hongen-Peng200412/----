# 正文Fig9: Centre消融

本目录只重建`stage2-stage3-ablation-centre(v1)`这一张采用图, 最终输出一页candidate.pptx。a/b保留GT/CA2下四个Matcher变体的身份准确率雷达; c/d显示标准Centre口袋的Build三模型完整分布。当前双语图注直接复制`画图/PPT/stage2-stage3结果.pptx`中本图的作者备注。

## 完整运行

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/正文/Fig9-result-Ablation/run.py"
```

无参时自动新建根temp中的本次目录; `--build temp/<新目录>`可显式指定空目录。输出包括单页`candidate.pptx`、原数组与描述统计`data/`、绝对路径/完整SHA256读取记录`source_reads.json`、本次SVG/PDF/PNG和面板对齐证据。入口不保存正式PPT, 所有产物可随根temp清空。

## 按科学流程读代码

先读[trace.md](trace.md), 再读`run.py → build.py → plot.py`。本图入口显式读取正文Fig5的`science.py::read_standard_build(...,'C0')`和`build_panels.py::boxes`; 它们唯一持有服务器标准Build目录、446成员检查、原排序字段和全分布百分位/KDE规则。本图另外调用read_match(...,'ablation'), 仅读取四模型冻结metrics供雷达。

跨图复用的是明确归属Fig5的科学实现, 不把实验规则放到TOOLS。本图不运行Fig5入口, 不读取235实例受控主比较、候选身份数分组或9WUP构象/密度; 也不计算另一口袋协议。`author_layout.json`只保存本图作者排版; 0–10Å是绘图显示窗口, 不删除长尾观测。

迁移验收已实跑本图: 446实例轴、全部原排序RMSD、失败/缺失和显示分布与原入口一致; 2000像素宽的PowerPoint导出与原入口及当前正式页均0像素差。
