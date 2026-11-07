# 通用图元与 Office 容器

本套件运输调用方已经确定的图元、样式、作者设计和备注。实际数据、方法名称、面板选择和评价参数由 Figure 提供。

| 文件 | 输入与输出 |
| --- | --- |
| `matplotlib_export.py` | Matplotlib Figure → 本次 SVG/PDF/PNG、可编辑场景及面板几何报告；字号、DPI、画幅参数由调用方明确给定 |
| `svg_scene.py` | SVG 路径、文字及变换 → 对应的中性场景对象，不重新计算数据曲线 |
| `build_scene.mjs` | 本次 `scenes.json` 和调用方 display 定义 → 原生可编辑 `candidate.pptx`、装配说明 |
| `svg_native.py` | SVG/原生对象、画布和样式定义 → DrawingML、单页或明确多页候选 |
| `native_geometry.py` | 二维线段和分组坐标 → 裁切、分组后的几何对象，不解释原子或科学轴 |
| `display_patch.py` | 明确的对象变换及附加对象 → 候选 ZIP 部件补丁；特殊科学对象由 Figure 回调提供 |
| `author_display.py` | 单页作者设计闭包 → 候选；也可从给定完整图名提取当前页必要依赖 |
| `deck.py` | PPT ZIP → 实际页面、完整图名、备注/批注关系；仅保存明确修改的部件 |
| `captions.py` | 同名正式作者页备注 → 候选页备注，保留文字、公式及格式；正式图集只读 |
| `ppt_figures.py`、`export_slide.ps1` | 完整图名定位、双语图注和原生 PowerPoint 导图，供 Word 转换使用 |
| `audit_panel_alignment.py` | 调用方画面 → 面板物理对齐检查，不读取实验文件 |

Figure 的 `display.json` 或 `layout.json` 负责实际页面尺寸、面板位置、颜色、对象选择及作者身份。工具不能内置实验根、排名或方法名单。所有场景、候选和比较副本只写本次根 temp；它们不是长期科学输入。

PPT 的备注是作者图注，`@@图名` 批注定位页面。来源短指路由 [figure_runner](../figure_runner/README.md) 按本图声明维护，不能把整份实验解释塞进 PPT。
