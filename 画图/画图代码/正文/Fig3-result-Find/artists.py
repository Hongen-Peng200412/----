"""绘制Find的指标柱与P/R分布, 只消费当前图已经计算的科学字段.

draw_scores和draw_precision_recall由正文Fig3与两张关联补图显式复用. 方法次序、颜色及PDB抖动是这组Find展示约定, 不是中性绘图工具. 本文件不读取文件、不选择level、不构造其他图.
"""

import numpy as np

MODELS = ("Emap", "Cryo", "GT")
COLOURS = {"Emap": "#A1ABB3", "Cryo": "#5B72B7", "GT": "#138B8D"}
LABELS = {"Emap": "Emap2lig-Find", "Cryo": "LigandSeek-Find (CA2)", "GT": "LigandSeek-Find (GT)"}


def draw_scores(ax, block, metrics, labels):
    """用本图明示的指标绘制PDB散点、等权均值和95%区间.

    block: dict, models[方法].values[指标]为(N_pdb,)的0-1比例, bars[指标]含mean/lower/upper. metrics和labels逐项对齐, 如('dice','oto03')对应语义Dice和PRAUC0.3. x为方法在该指标组内的显示位置, 不改变纵轴科学值.
    """
    for metric_index, metric in enumerate(metrics):
        for model_index, model in enumerate(MODELS):
            x = metric_index + (model_index - 1) * 0.24
            colour = COLOURS[model]
            stats = block["models"][model]["bars"][metric]
            values = np.asarray(block["models"][model]["values"][metric])
            jitter = np.random.default_rng(730 + metric_index * 13 + model_index).uniform(-0.075, 0.075, len(values))
            ax.bar(x, stats["mean"], width=0.205, color=colour, alpha=0.27, edgecolor=colour, linewidth=0.65, zorder=1)
            ax.scatter(x + jitter, values, s=4, color=colour, alpha=0.15, linewidths=0, zorder=2)
            ax.vlines(x, stats["lower"], stats["upper"], color=colour, linewidth=1.15, zorder=4)
            ax.hlines([stats["lower"], stats["upper"]], x - 0.045, x + 0.045, color=colour, linewidth=1.15, zorder=4)
            ax.hlines(stats["mean"], x - 0.085, x + 0.085, color=colour, linewidth=1.8, zorder=5)
    ax.set(
        xlim=(-0.5, len(metrics) - 0.5),
        xticks=range(len(metrics)),
        xticklabels=labels,
        ylabel="Score",
        ylim=(0, 1.06),
        yticks=[0, 0.5, 1],
    )
    ax.tick_params(axis="x", length=0, pad=6)


def draw_precision_recall(ax, block, metrics, labels):
    """按本图指标列表绘制反射KDE、原PDB散点、中位数与四分位.

    block: dict, 每个方法的distribution[指标].grid/density为(161,)配对曲线, quartiles为(3,)的25/50/75%分位. metrics如('precision05','recall05'), labels只决定同序轴文字; values[指标]为(N_pdb,)原0-1比例.
    """
    for metric_index, metric in enumerate(metrics):
        for model_index, model in enumerate(MODELS):
            x = metric_index * 4.1 + model_index
            colour = COLOURS[model]
            stats = block["models"][model]["distribution"][metric]
            grid = np.asarray(stats["grid"])
            width = np.asarray(stats["density"]) * 0.37
            ax.fill_betweenx(grid, x - width, x + width, facecolor=colour, alpha=0.18, edgecolor=colour, linewidth=0.65)
            values = np.asarray(block["models"][model]["values"][metric])
            jitter = np.random.default_rng(970 + metric_index * 13 + model_index).uniform(-0.24, 0.24, len(values))
            ax.scatter(x + jitter, values, s=4, color=colour, alpha=0.22, linewidths=0, zorder=2)
            q1, median, q3 = stats["quartiles"]
            ax.vlines(x, q1, q3, color=colour, linewidth=1.9, zorder=4)
            ax.scatter([x], [median], s=16, facecolor="white", edgecolor=colour, linewidth=0.95, zorder=5)
    ax.set(
        xlim=(-0.65, (len(metrics) - 1) * 4.1 + 2.65),
        ylim=(0, 1.06),
        yticks=[0, 0.5, 1],
        ylabel="Score",
        xticks=[1 + index * 4.1 for index in range(len(metrics))],
        xticklabels=labels,
    )
    ax.tick_params(axis="x", length=0, pad=6)
