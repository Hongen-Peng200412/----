"""复用既有完成度小提琴、散点和精确阶梯的绘图函数.

draw_panel把一个冻结面板绘制到给定坐标轴; save_figure在调用方指定的构建目录写出SVG/PDF/PNG、对齐报告并追加装配元数据.
本模块不读取姿态或重新汇总指标; 各图目录的plot.py负责读取data.json并组合本图.
"""

import os
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

sys.path.insert(0, "C:/Users/15919/.codex/skills/nature-figure/scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/fmb_20261015"
DATA = ROOT / "画图/画图代码/e2e/output/find-build-shared/data.json"
COLORS = {"GT": "#00878B", "CA2": "#596BC0", "Emap2lig": "#A57948"}
MEAN_COLOR = "#00878B"  # 所有受体条件共用的均值轨迹颜色, 不用于区分 GT 与 CA2.
MEDIAN_COLOR = "#3A64C8"  # 中位数轨迹颜色; 较细的实线覆盖均值线时仍可分别辨认.
INK = "#273744"
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "svg.fonttype": "none", "pdf.fonttype": 42, "axes.linewidth": 0.7, "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})


def draw_panel(ax, panel, title, letter, compact):
    """在固定坐标轴中展示一个条件的分布与精确事件阶梯.

    输入参数:
        - ax: Matplotlib Axes, 最终物理尺寸已由外层 GridSpec 固定.
        - panel: dict, 包含每 PDB 的分布和 exact Fraction 事件汇总曲线.
        - title、letter: str, 公开条件名称和面板字母; 单面板 letter 为空.
        - compact: bool, 汇总页使用较少刻度, 不改变科学数据.
    返回值:
        - 无. 添加小提琴、多 PDB 散点、均值与中位数实线阶梯, 以及固定预算处的圆点与菱形.
    """
    color = COLORS[panel["domain"]]
    for budget in (50, 100, 200, 300):
        records = panel["distributions"][str(budget)]
        values = np.array([row["completion"] for row in records])  # (P,), 完整 PDB 分母中的完成比例.
        grid = np.linspace(0, 1, 121)
        # 在 [0,1] 边界反射的 Gaussian KDE 仅用于分布轮廓, 不平滑或更改宏平均曲线.
        distances = grid[:, None] - np.concatenate((values, -values, 2 - values))[None, :]
        density = np.exp(-0.5 * (distances / 0.055) ** 2).sum(axis=1)
        width = 13 * density / density.max()
        ax.fill_betweenx(grid * 100, budget - width, budget + width, facecolor=color, alpha=0.12, edgecolor=color, linewidth=0.55, zorder=1)
        # PDB字符编码产生可复现的纯横向抖动; 相同 PDB 在所有条件保持相同偏移, y 不变.
        jitter = np.array([(int.from_bytes(row["pdb_id"].encode(), "little") % 997 / 996 - 0.5) * 19 for row in records])
        ax.scatter(budget + jitter, values * 100, s=5 if compact else 8, facecolor="#7F8C97", edgecolor="none", alpha=0.48, zorder=2)
    curve = panel["curve"]
    mean_percent = np.array(curve["mean"]) * 100  # (E,), 已冻结的 E 个预算事件对应的 PDB 等权均值, 转为百分比.
    median_percent = np.array(curve["median"]) * 100  # (E,), 与均值逐事件对齐的中位数百分比, 不重新汇总 PDB.
    ax.step(curve["budget_percent"], mean_percent, where="post", color=MEAN_COLOR, linewidth=1.8, zorder=4)
    ax.step(curve["budget_percent"], median_percent, where="post", color=MEDIAN_COLOR, linewidth=1.05, zorder=5)
    marker_budgets = np.array([50, 100, 200, 300])  # (4,), 与四个小提琴中心一致的相对尝试预算百分比.
    # int64, (4,), 每个固定预算对应的最后一个已发生事件编号; side="right" 保持原 post 阶梯在跳点处的取值.
    event_indices = np.searchsorted(curve["budget_percent"], marker_budgets, side="right") - 1
    ax.plot(marker_budgets, mean_percent[event_indices], linestyle="none", marker="o", markersize=3.4, markerfacecolor=MEAN_COLOR, markeredgecolor="white", markeredgewidth=0.35, zorder=6)
    ax.plot(marker_budgets, median_percent[event_indices], linestyle="none", marker="D", markersize=4.0, markerfacecolor="none", markeredgecolor=MEDIAN_COLOR, markeredgewidth=0.9, zorder=7)
    # 增加 0% 与 100% 外侧的显示留白, 使端点的圆点和菱形完整可见; 刻度与统计值均保持原样.
    ax.set(xlim=(-3, 321), ylim=(-5, 105), xticks=[0, 50, 100, 200, 300], yticks=[0, 50, 100] if compact else [0, 25, 50, 75, 100])
    ax.grid(axis="y", color="#DEE5EA", linewidth=0.55, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7.3 if compact else 8, length=3, width=0.6, pad=3)
    ax.set_title(title, loc="left", fontsize=8.5 if compact else 10, pad=9)
    if letter:
        ax.text(-0.14, 1.13, letter, transform=ax.transAxes, fontweight="bold", fontsize=10, va="top", clip_on=False)


def save_figure(fig, stem, figure_id, caption_zh, caption_en, manifest, build):
    """验收最终坐标轴对齐并导出同源矢量、预览和 PPT 装配元数据.

    输入参数:
        - fig: Matplotlib Figure, 已包含最终文字与图形布局.
        - stem、figure_id: str, 临时文件前缀及 PPT 唯一 @@ 标识.
        - caption_zh、caption_en: str, 不含手工图号的中英文图注.
        - manifest: list[dict], 按 PPT 页序追加图的物理尺寸、标题和图注.
        - build: Path, 当前图的临时构建目录, 如temp/find-only-instance-completion.
    返回值:
        - 无. 写入 SVG、PDF、PNG 与多面板布局报告, 并关闭该 Figure.
    """
    fig.canvas.draw()
    if len(fig.axes) > 1:
        require_matplotlib_panel_alignment(fig, json_out=build / f"{stem}.alignment.json", overlay_svg=build / f"{stem}.alignment.svg", tolerance_pt=1.5)
    fig.savefig(build / f"{stem}.svg", facecolor="white")
    fig.savefig(build / f"{stem}.pdf", facecolor="white")
    fig.savefig(build / f"{stem}.png", dpi=600, facecolor="white")
    manifest.append({"stem": stem, "id": figure_id, "width": float(fig.get_figwidth() * 72), "height": float(fig.get_figheight() * 72), "notes": caption_zh + "\nENGLISH:\n" + caption_en})
    plt.close(fig)
