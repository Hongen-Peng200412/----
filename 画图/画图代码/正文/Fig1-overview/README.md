# Fig1：当前总览图的组合

本目录只组合正文当前采用的 `@@fig-overview-topology`。输出保留现有图名、文字、图片、裁切、分组、作者布局和双语图注，不恢复未采用的旧总览生成流程。

```powershell
D:/Anaconda/python.exe -X utf8 -B 画图/画图代码/正文/Fig1-overview/run.py --build temp/本次Fig1
```

`run.py` 调用中性 Office 装配工具，将 `design/drawing.xml` 放入本页的 Office 容器，生成 `candidate.pptx`；随后读取 `画图/PPT/总览图.pptx` 的同名页，保留作者最新备注。正式 PPT 只读。候选文件和构建说明均在本次 temp，目录迁移不需要运行旧的 `同步导出.py`。

当前必要设计、媒体、作者会话及其职责见 [trace.md](trace.md)。修改可见图或图注仍回到所属 PPT；需要更新设计源码时，只收取当前实际采用页的依赖，不把其它备选页面一同纳入。
