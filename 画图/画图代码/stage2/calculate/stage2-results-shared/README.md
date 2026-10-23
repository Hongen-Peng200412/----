> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Stage 2 共享绘图实现

当前两图由相邻 `stage2-radar-pair/ops/render.py` 与 `stage2-strongest-pair/ops/render.py` 独立生成，本目录集中保留共用颜色、冻结数据读取和实际绘图函数。

`plot_stage2.py::configure(profile, output)` 默认使用 `stage2/output/stage2-results/data_忽视2+2例子.json`；显式 `--profile old` 才使用 `data.json`。两者只有八个前景 F1 槽位不同。`plot_stage2_pairs.py::plot_radar_pair()` 和 `plot_categories_pair()` 读取同一数据对象，输出 PDF、SVG、600 dpi PNG／TIFF 及布局核查；分组表元素是 `[correct,support]`，零支持显示缺失，不画零准确率。

`build_editable_deck.mjs` 建立原生 PPT 线条、标记、文字和图名批注，默认当前新口径，从数据目录 `两种口径图注.json` 读取同口径双语图注。默认产物进入 `temp/stage2-deck-build/`；`--output` 可指定其他候选目录。它不会覆盖 `画图/` 内作者正式 PPT。`finalize_editable_deck.py` 给 PPTXGenJS 候选加传统图名批注，默认只另存 temp 候选。

建议按 `configure()`、两个 `plot_*_pair()`、JS `drawRadarPanel()/drawCategoryPanel()` 的顺序阅读。完整来源、排除口径与分母见 [本阶段追溯](../图表追溯.md)。`ops/switch_profile.py` 仅在作者明确要求切换正文口径时使用；作者改写过的处理句无法匹配时停止，不强行回退其文字。
