> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# 官方模型与微调模型的完整测试集比较

本目录维护 `stage3-official-tuned` 的数据组装、印刷预览和原生 PPT 生成代码。论文图保存在 `画图/stage3结果.pptx`；当前PPT的手工修改不由默认重绘覆盖。完整来源、协议、中位数和原实验版本见[阶段追溯](../图表追溯.md)。

先读 `assemble_data.py::main` 理解八组原评价与实例键，再读 `plot_stage3.py::draw_distribution` 和 `main` 理解预览，最后读 `build_editable_deck.mjs` 的 `distribution`、`fullPanel`、`officialFigure` 理解原生PPT。历史237例比较仍会作为预览辅助页导出，正文现用预测区域比较另由 `stage3-predicted-region-head-to-head` 目录维护。

冻结输入为仓库 `画图/画图代码/stage3/output/stage3-official-tuned/`：

```text
stage3/output/stage3-official-tuned/
├─ data.json              # 八组逐实例距离、原来源散列及历史Build子集
├─ frozen/                # 八份446实例原评价副本
├─ summary.json           # 初始冻结距离统计
├─ evidence/              # 实例冻结与正式实验日志
└─ regenerated/           # 默认重绘的PDF/SVG/PNG/TIFF和新summary
```

`data.json.series[*].rows` 每条保存 `(pdb_id,occurrence_id)`、`top1`、`best`、`status`；距离为Å，缺失为null。八组均有446个实例；官方GT两协议各445个有效距离，其余446。箱体25–75百分位，须5–95百分位，中心线为中位数；超过50Å只在显示时置于50+区，不截断分位计算。

从仓库根运行：

```powershell
python 画图/画图代码/stage3/calculate/stage3-official-tuned/plot_stage3.py
```

它只读冻结 `data.json`，将新预览及 `summary.json` 写入 `output/stage3-official-tuned/regenerated/`，布局诊断写 `temp/stage3-figure-qa/`。原数据组装需要显式提供八份评价目录、Build冻结目录和新输出路径；输出应指向 `regenerated/data.json` 或 `temp/`，不要覆写现有冻结文件。原生PPT生成只产生候选；发布到正式PPT前按仓库规则同步来源和双语备注。

历史定页合并脚本 [finalize_editable_deck.ps1](../../../archive/calculate/publication-history/stage3/stage3-official-tuned/finalize_editable_deck.ps1) 已归档。它读取当时的临时备份并按固定页号复制备注，不作为当前入口。当前 `build_editable_deck.mjs` 直接生成带独立图名与备注的新候选；真实输入和生成位置以[阶段追溯](../图表追溯.md)为准。
