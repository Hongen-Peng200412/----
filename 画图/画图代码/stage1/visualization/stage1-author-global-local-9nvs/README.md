# 9NVS作者八视图的重绘与发布

本目录把作者第15页草案整理为论文图，保留所有八个视图与原评价数值。`build.py`用ChimeraX原生导图、PowerPoint装配，`ops/publish.py`只追加新页；原16页、原生作者CXS和其他论文内容保留。

当前正文采用作者手调的`stage1-author-global-local-9nvs(v1)`（第17页），上方a–c为整体、下方五幅局部；基础版现保留于第16页。两版共享八张原生图与科学定义，`author_v1/`冻结当前排版、双语图注和媒体映射。作者版按仓库规则沿本目录重建科学图，不用初版排版覆盖作者手调PPT。

## 输入与产物

下列路径相对论文仓库根，两个临时构建目录模式指同一次构建，不是长期输入。

```text
画图/画图代码/stage1/output/stage1-author-global-local-9nvs/
├─ source_manifest.json    # 八份作者CXS、来源散列、原相机及固定科学数字
├─ caption.json            # 中英文图注
├─ source/                 # 八份冻结作者CXS、initial.cxs及完整作者草案PPT
├─ native/                 # 正式采用的八份PNG、最终CXS和原生命令
└─ qa/                     # 隔离重建、科学材料、几何、文本及旧页保全证据（验收）
temp/<本次构建>/
├─ native/                 # 本次原生重绘与保存的八视图（可再生辅助导出）
├─ native_state.json       # 原生相机、窗口与可见模型（运行统计）
├─ panels.json             # 八幅图在候选PPT中的矩形和全景裁边（可再生工具输入）
├─ callouts.json           # 完整局部画幅在全景中的定位框（可再生工具输入）
├─ candidate.pptx          # 一页八视图及双语备注（可再生辅助导出）
├─ preview.png、figure.pdf # PowerPoint真实导出（可再生辅助导出）
└─ publish-receipt.json    # 追加页、旧部件保全及发布状态（验收）
```

`source_manifest.json.author_views`以`emap_global`等8个视图名为键，每项记录仓库相对`original/frozen`路径、`sha256`和`state`。`state.camera`为3×4相机姿态，前三列为屏幕XYZ轴、末列为世界位置Å；`field_width`为横向视野Å，`window_size=[1126,814]`为像素宽高；`models`保留原顶层模型、显隐及材料描述。`scientific_numbers`保留原显示值，不从坐标或掩码重算评价。

`panels.json`按a–h连接视图名，`rect_mm=[左,上,宽,高]`为候选页的毫米矩形；全景`crop`记录0–1比例的四边裁切，局部`crop=null`表示全幅显示。`callouts.json`每项连接`global_panel`、`local_view`、`tag`及同单位矩形，标记完整局部画幅而非目标blob包围盒。例：a的`tag="ii"`连接`local_view="emap_tp"`。三幅全景共用相机与尺度，四幅共同实例局部也共用相机与尺度；c保留独立原放大倍数。

## 代码与入口

先读作者目录的`论文图说明.md`，再读`build.py`。唯一小工具`local_frame_in_global`被四个定位框复用，返回左上／右下归一化坐标；其后主流程依次原生导出、读取状态、按方法分行装配、写原生裁边、导出PPT/PDF。`ops/publish.py`只做XML及PNG运输，沿既有发布工具的旧部件保全方式，使用原HP批注身份，不参与科学定义。

重建入口为仓库根的`转换工具/ops/rebuild_figures.py --figure stage1-author-global-local-9nvs`，明确屏蔽旧temp。所有科学输入均在本图output，脚本每次生成新的运行命令与状态。正式采用后的`native/`供作者打开及追溯，不被重建读取。正式PPT位于`画图/stage1可视化.pptx`，图名`stage1-author-global-local-9nvs`。实际运行、此前尝试及验证统一记录在`talk/author_visualization_20261103/执行记录.md`。
