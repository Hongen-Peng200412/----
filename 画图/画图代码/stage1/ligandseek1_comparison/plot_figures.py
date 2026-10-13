"""把冻结的两代 LigandSeek 绘图统计绘制为六张单图和一张三行两列组合图.

先阅读 render_figures(), 再查看重复使用的 draw_panel(); 本模块只改变显示几何, 不重新定义 PDB 成员或评价指标.
plot_data 指向 prepare_plot_data.py 已生成的 JSON, 均值、bootstrap 区间、KDE 和分位数直接读取.
output_root 保存七组 SVG/PDF/PNG; SVG 与 PDF 保留可编辑文字, PNG 只供查看.
build_root 保存渲染暂存、PDF 审计、面板对齐 JSON 和 manifest.json; manifest 的 pages[*].shapes 是同一 SVG 转换出的原生 PowerPoint 场景.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FormatStrFormatter
from matplotlib.transforms import ScaledTranslation
import numpy as np


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Calibri"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams.update({
    "font.size": 9.0, "axes.labelsize": 9.0, "xtick.labelsize": 8.0, "ytick.labelsize": 8.0,
    "axes.linewidth": 0.65, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.major.size": 2.3, "ytick.major.size": 2.3, "xtick.major.width": 0.55, "ytick.major.width": 0.55,
    "svg.fonttype": "none", "pdf.fonttype": 42, "savefig.facecolor": "white", "legend.frameon": False,
})

METHODS = ("L2_GT", "L2_CA2", "L1_GT", "L1_CA2")  # 四个模型/受体条件的固定展示顺序; GT 是沉积受体, CA2 是 CryoAtom2 重建受体.
COLORS = {"L2_GT": "#007C83", "L2_CA2": "#566AB4", "L1_GT": "#7D8990", "L1_CA2": "#B08A60"}  # 一个方法在柱图、散点和分布中始终使用同一颜色.
LABELS = {"L2_GT": "LigandSeek2 (GT)", "L2_CA2": "LigandSeek2 (CA2)", "L1_GT": "LigandSeek1 (GT)", "L1_CA2": "LigandSeek1 (CA2)"}  # 受体简称由每页双语图注定义.
TITLE = {"bar": "Overall scores", "paired": "CA2: one-to-one PRAUC₀.₃", "violin": "CA2: one-to-one detection₀.₃"}  # Calibri 支持阈值 Unicode 下标, 保持 SVG 普通 text 节点, 不引入 mathtext 的 tspan.
COMPOSITE_SIZE = (163.0 / 25.4, 190.0 / 25.4)  # (2,), 完整图宽/高, 单位 inch; 正文缩到 147 mm 宽时字号仍高于 5 pt.
SINGLE_SIZE = (89.0 / 25.4, 85.0 / 25.4)  # (2,), 单图宽/高, 单位 inch; PowerPoint 只等比缩放同一 SVG 场景.
DPI = 350  # PNG 查看图每 inch 像素数; SVG/PDF 和 PowerPoint 数据几何仍是矢量.


def draw_panel(fig: plt.Figure, block: dict, kind: str, rect: list[float], letter: str) -> tuple[plt.Axes, list[plt.Axes]]:
    """在一个明确的 Figure 矩形内展示冻结统计, 同时服务六张单图和组合图.

    输入参数:
        - fig: Figure, 调用方已确定 inch 尺寸的画布.
        - block: dict, 一个冻结集合; n 是 PDB 数, models 的各指标值、均值区间和分布均已计算.
        - block.models[*].values: dict, 以下五项无量纲指标与 block.ids 逐项对齐; N 是 block.n.
            - dice: list[float], (N,), 逐 PDB 语义 F1.
            - prauc_0p3: list[float], (N,), 双向覆盖 0.3 下的逐 PDB 一对一 PRAUC.
            - prauc_0p5: list[float], (N,), 双向覆盖 0.5 下的逐 PDB 一对一 PRAUC.
            - precision: list[float], (N,), 双向覆盖 0.3 下的逐 PDB 一对一精确率.
            - recall: list[float], (N,), 双向覆盖 0.3 下的逐 PDB 一对一召回率.
        - block.models[*].bars[*]: dict, dice/prauc_0p3/prauc_0p5 各自的冻结均值和区间.
            - mean: float, 当前指标的 PDB 等权均值.
            - lower: float, 当前指标的 95% bootstrap 均值区间下界.
            - upper: float, 同一区间的上界.
        - block.models[*].distribution[*]: dict, precision/recall 各自的冻结展示分布.
            - grid: list[float], (161,), 从 0 到 1 的指标纵坐标.
            - density: list[float], (161,), 与 grid 对齐的归一化反射 KDE 展示宽度.
            - quartiles: list[float], (3,), 原始指标的 25/50/75 百分位数.
        - block.resolution: list[float], (N,), 同一 PDB 轴的实验分辨率, 单位 Å.
        - kind: str, bar/paired/violin 分别展示四方法柱图、CA2 两代配对、CA2 两代 P/R 分布.
        - rect: list[float], (4,), Figure 相对坐标的左/下/宽/高; 原点是画布左下角.
        - letter: str, a 到 f 的面板标识, 固定物理偏移放在绘图区左上方.

    返回值:
        - ax: Axes, 当前科学绘图区; 实测面板对齐只比较这个矩形.
        - colorbar_axes: list[Axes], paired 时仅含其分辨率色条轴, 其他图型为空; 从面板对齐集合精确排除.

    横向抖动只分开逐 PDB 点, 不改变任何纵向指标、配对坐标、均值或统计区间.
    """
    ax = fig.add_axes(rect)  # (4,) Figure 矩形变为一个绘图区; 所有科学坐标仍由冻结指标直接定义.
    colorbar_axes = []  # list[Axes], 仅收集当前面板的独立色条, 不把色条当成科学绘图区.
    if kind == "bar":
        bar_spacing = 0.205  # 指标组内部相邻方法的横向距离, 单位为分类轴坐标.
        for method_index, method in enumerate(METHODS):
            color = COLORS[method]
            for metric_index, metric in enumerate(("dice", "prauc_0p3", "prauc_0p5")):
                center = metric_index + (method_index - 1.5) * bar_spacing  # 每个指标组内四个方法的分类轴中心.
                stats = block["models"][method]["bars"][metric]  # mean/lower/upper 三个无量纲冻结统计值, 不在图代码重算.
                values = np.asarray(block["models"][method]["values"][metric], dtype=float)  # (N,), 当前方法/指标的全部逐 PDB 数值, 包含 0/1 端点.
                jitter = np.random.default_rng(710 + method_index * 13 + metric_index).uniform(-bar_spacing * 0.34, bar_spacing * 0.34, len(values))  # (N,), 单位为分类轴坐标, 只改变横向展示位置.
                ax.bar(center, stats["mean"], bar_spacing * 0.84, color=color, alpha=0.16, edgecolor=color, linewidth=0.65, zorder=1)
                ax.scatter(center + jitter, values, s=3.8, color=color, alpha=0.40, linewidths=0, zorder=2, clip_on=False)
                ax.vlines(center, stats["lower"], stats["upper"], color=color, linewidth=0.95, zorder=4)
                ax.hlines([stats["lower"], stats["upper"]], center - 0.043, center + 0.043, color=color, linewidth=0.95, zorder=4)
                ax.hlines(stats["mean"], center - 0.070, center + 0.070, color=color, linewidth=1.5, zorder=5)
        ax.set(xlim=(-0.50, 2.50), ylim=(-0.025, 1.035), yticks=[0, 0.5, 1], ylabel="Score", xticks=[0, 1, 2], xticklabels=["Semantic\nDice", "One-to-one\nPRAUC₀.₃", "One-to-one\nPRAUC₀.₅"])
        ax.tick_params(axis="x", length=0, pad=5)
        ax.grid(axis="y", color="#E7EBED", linewidth=0.45)
        ax.set_axisbelow(True)
    elif kind == "paired":
        x = np.asarray(block["models"]["L1_CA2"]["values"]["prauc_0p3"], dtype=float)  # (N,), 横轴是同一 PDB 的 LigandSeek1/CA2 一对一 PRAUC₀.₃.
        y = np.asarray(block["models"]["L2_CA2"]["values"]["prauc_0p3"], dtype=float)  # (N,), 纵轴是与 x 逐 PDB 配对的 LigandSeek2/CA2 一对一 PRAUC₀.₃.
        resolution = np.asarray(block["resolution"], dtype=float)  # (N,), 与 x/y 对齐的实验分辨率, 单位 Å.
        for start in np.arange(0.0, 1.0, 0.05):
            segment = [start, min(start + 0.025, 1.0)]  # (2,), 等值线的一段横/纵指标坐标; 实体分段使原生 PowerPoint 保留同一虚线几何.
            ax.plot(segment, segment, color="#939CA2", linewidth=0.65, zorder=0)
        scatter = ax.scatter(x, y, c=resolution, cmap="viridis_r", vmin=1.0, vmax=4.0, s=11.0, alpha=0.82, linewidths=0.22, edgecolors="white", zorder=2, clip_on=False)  # 固定 1-4 Å 色域, 域外分辨率仅饱和到端点颜色, 不修改数值或配对.
        ax.set(xlim=(0, 1), ylim=(0, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], aspect="equal", xlabel="LigandSeek1 (CA2)", ylabel="LigandSeek2 (CA2)")
        left, bottom, width, height = ax.get_position().bounds  # (4,), 最终绘图区在 Figure 内的左/下/宽/高; square aspect 已确定实际几何.
        colorbar_ax = fig.add_axes([left + width + 0.014, bottom, 0.010, height])  # (4,), 色条与配对图区同高, 独立创建以保持科学绘图区的宽度.
        colorbar = fig.colorbar(scatter, cax=colorbar_ax, ticks=[1, 2, 3, 4])
        colorbar.ax.tick_params(labelsize=8.0, length=2, pad=1.5)
        colorbar.ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        colorbar.set_label("Resolution (Å)", fontsize=8.0, labelpad=2)
        colorbar.outline.set_visible(False)
        colorbar.solids.set_rasterized(False)
        colorbar.solids.set_alpha(1)
        colorbar.solids.set_edgecolor("face")
        colorbar.solids.set_linewidth(0.2)
        colorbar_axes.append(colorbar_ax)
    elif kind == "violin":
        for metric_index, metric in enumerate(("precision", "recall")):
            for method_index, method in enumerate(("L2_CA2", "L1_CA2")):
                center = metric_index * 3.2 + method_index  # P/R 分别占一组, 每组只比较 CA2 受体下的两代模型.
                color = COLORS[method]
                stats = block["models"][method]["distribution"][metric]  # grid/density/quartiles 均是冻结展示统计, 不在图代码估计 KDE 或分位数.
                grid = np.asarray(stats["grid"], dtype=float)  # (161,), 无量纲指标纵坐标, 从 0 到 1 且保留两端.
                half_width = np.asarray(stats["density"], dtype=float) * 0.40  # (161,), 已归一化反射 KDE 乘固定几何比例后的分类轴半宽.
                ax.fill_betweenx(grid, center - half_width, center + half_width, facecolor=color, alpha=0.16, edgecolor=color, linewidth=0.65, zorder=1)
                values = np.asarray(block["models"][method]["values"][metric], dtype=float)  # (N,), 当前方法/指标的全部 PDB 数值, 不排除 0/1 端点.
                jitter = np.random.default_rng(970 + method_index * 13 + metric_index).uniform(-0.24, 0.24, len(values))  # (N,), 分类轴上的横向展示偏移, 与纵向 P/R 值无关.
                ax.scatter(center + jitter, values, s=4.0, color=color, alpha=0.43, linewidths=0, zorder=2, clip_on=False)
                q1, median, q3 = stats["quartiles"]  # (3,), 无量纲的第 25/50/75 百分位数, 原始 PDB 分布包括所有 0/1.
                ax.vlines(center, q1, q3, color=color, linewidth=1.7, zorder=4)
                ax.scatter([center], [median], s=13, facecolor="white", edgecolor=color, linewidth=0.8, zorder=5, clip_on=False)
        ax.set(xlim=(-0.65, 4.85), ylim=(-0.025, 1.035), yticks=[0, 0.5, 1], ylabel="Score", xticks=[0.5, 3.7], xticklabels=["Precision", "Recall"])
        ax.tick_params(axis="x", length=0, pad=5)
        ax.grid(axis="y", color="#E7EBED", linewidth=0.45)
        ax.set_axisbelow(True)
    title_offset = ScaledTranslation(0, 8 / 72, fig.dpi_scale_trans)  # ScaledTranslation, 使用 (dx,dy) inch 偏移的标题绘图变换.
    panel_offset = ScaledTranslation(-21 / 72, 8 / 72, fig.dpi_scale_trans)  # ScaledTranslation, 字母使用相同的 (dx,dy) inch 锚点偏移规则.
    ax.text(0, 1, TITLE[kind], transform=ax.transAxes + title_offset, fontsize=9.0, ha="left", va="bottom")
    ax.text(0, 1, letter, transform=ax.transAxes + panel_offset, fontsize=11.0, fontweight="bold", ha="left", va="bottom")
    return ax, colorbar_axes


# ================================================================================================


def render_figures(plot_data: Path, output_root: Path, build_root: Path, nature_scripts: Path) -> None:
    """读取冻结统计, 用 Matplotlib 绘图和审计, 再发布矢量图及同源 PowerPoint 场景.

    输入参数:
        - plot_data: Path, prepare_plot_data.py 生成的 JSON; 读取 cohorts.full/small, 不读取模型输出或评估输入.
        - output_root: Path, 七组正式 SVG/PDF/PNG 的目标目录; 同名文件存在时拒绝覆盖, 保留作者的手工修改.
        - build_root: Path, 论文 temp/ 下的独立构建目录; 暂存渲染、审计和 manifest.json 均由此参数决定.
        - nature_scripts: Path, Nature Figure 技能 scripts 目录; 调用已有面板对齐、PDF 字号和碰撞审计.

    正式图文件:
        - a_full_bar.{svg,pdf,png}: 完整 179 PDB 集合的四方法三指标柱图、全部逐 PDB 点和冻结 95% 区间.
        - b_small_bar.{svg,pdf,png}: 既定 94 PDB/821 小分子实例集合的对应柱图, 不重新确定成员.
        - c_full_paired.{svg,pdf,png}: 完整集合 CA2 输入下的两代配对 PRAUC₀.₃, 分辨率色条单位 Å.
        - d_small_paired.{svg,pdf,png}: 既定小分子集合的相同配对比较.
        - e_full_violin.{svg,pdf,png}: 完整集合 CA2 两代一对一₀.₃ P/R, 原始点、冻结反射 KDE 和分位数.
        - f_small_violin.{svg,pdf,png}: 既定小分子集合的相同 P/R 分布.
        - LigandSeek2_vs_LigandSeek1.{svg,pdf,png}: 163 mm × 190 mm 的三行两列组合图, 左列完整集合、右列小分子集合.

    构建文件:
        - render/: 七组发布前的同源 SVG/PDF/PNG, 不作为科学统计接口.
        - qa/<stem>.alignment.json: 最后一次 draw 后实测绘图区/字母锚点及 1.5 pt 比较结果; 按当前图实际集合精确排除色条轴, 单 paired 为 1 条, 组合为 2 条, 其他单图为 0 条.
        - qa/<stem>.alignment.svg: 仅绘图区矩形的对齐诊断, 不替代正式图.
        - qa/<stem>.glyph-audit.json: 同一 PDF 实际文字字号的审计, 5.55 pt 门槛覆盖从 163 到 147 mm 的缩放.
        - qa/<stem>.collision-audit.json: 同一 PDF 文字/路径/页面边缘的碰撞报告.
        - qa/<stem>.collision-audit.pdf: 仅含诊断标记的 PDF, 不发布到正式图目录.
        - manifest.json: JSON 对象, 供 build_deck.mjs 直接 transport, 不再绘制数据.
            - slide_size_pt: list[float], (2,), 组合画布的宽/高, 单位 pt; PowerPoint 将 pt 等比映射为 96 DPI CSS px.
            - pages: list[dict], 六张单图按 a 到 f 排列, 组合图位于第七页.
                - stem: str, 输出图文件的无扩展名名称, 如 a_full_bar.
                - name: str, 唯一图名批注的内容, 如 l2-l1-stage1-a-full-bar; JS 添加 @@ 前缀.
                - notes: str, 中文图注、独立 ENGLISH: 行和英文图注; 不含手写图号.
                - width: float, 本页源 SVG 宽度, 单位 pt.
                - height: float, 本页源 SVG 高度, 单位 pt.
                - shapes: list[dict], 成熟 convert(svg) 生成的普通文字/椭圆/折线场景, 顺序为 SVG 绘制顺序.
                    - kind: str, text/ellipse/path, 不允许整图图片或 mathtext 的 tspan.
                    - x: float, 形状左边界在 SVG 左上原点坐标系的位置, 单位 pt.
                    - y: float, 形状上边界在同一坐标系的位置, 单位 pt.
                    - w: float, 形状宽度, 单位 pt.
                    - h: float, 形状高度, 单位 pt.
                    - text: str, text 专有的原始文字, 保留原始阈值 Unicode 下标.
                    - font: float, text 专有的字体大小, 单位 pt.
                    - font_family: str, text 专有的字体族; 与 SVG 字宽度量相同, 本图为 Calibri.
                    - bold: bool, text 专有的粗体标记.
                    - rotation: float, text 专有的旋转角度, 单位 degree.
                    - color: str, text 专有的 RGB 填色.
                    - fill: str, path/ellipse 的 RGB 填色或 none.
                    - stroke: str, path/ellipse 的 RGB 描边或 none.
                    - fill_alpha: float, path/ellipse 的填色不透明度, 范围 [0,1].
                    - stroke_alpha: float, path/ellipse 的描边不透明度, 范围 [0,1].
                    - stroke_width: float, path/ellipse 的描边宽度, 单位 pt.
                    - dash: str, path/ellipse 的 SVG 线型; 本模块将等值虚线绘制成独立实线段.
                    - parts: list[list[list[float]]], path 专有的局部折线; 每个 (X,Y) 点相对于该 shape 左上角, 单位 pt; ellipse 不含此字段.

    PDF 审计 FAIL 或不可审计会阻止对应图发布; REVIEW REQUIRED 的 WARN 保存供逐面板人工检查.
    """
    data = json.loads(plot_data.read_text(encoding="utf-8-sig"))  # 顶层 JSON 的 cohorts 保存两个冻结集合, 不触发统计计算.
    sys.path.insert(0, str(nature_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    transport_root = Path(__file__).resolve().parent.parent / "main_sixpanel_20260929"  # 只复用成熟 SVG 支持子集, 不调用其旧输出目录或 __main__.
    sys.path.insert(0, str(transport_root))
    from svg_to_scene import convert
    render_root = build_root / "render"
    qa_root = build_root / "qa"
    render_root.mkdir(parents=True, exist_ok=True)
    qa_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    panel_specs = [(letter, cohort, kind) for letter, (kind, cohort) in zip("abcdef", (("bar", "full"), ("bar", "small"), ("paired", "full"), ("paired", "small"), ("violin", "full"), ("violin", "small")))]  # list[tuple], 六个固定面板的字母/集合/图型, 不按性能重新排序.
    stems = [f"{letter}_{cohort}_{kind}" for letter, cohort, kind in panel_specs] + ["LigandSeek2_vs_LigandSeek1"]  # (7,), 正式图文件与七页 PowerPoint 逐项对应.
    for stem in stems:
        for extension in ("svg", "pdf", "png"):
            if (output_root / f"{stem}.{extension}").exists():
                raise FileExistsError(f"Refusing to overwrite {output_root / f'{stem}.{extension}'}")
    captions = {}  # dict[str, str], 面板字母到完整双语图注的映射, 单图和组合图使用同一科学口径.
    for letter, cohort, kind in panel_specs:
        block = data["cohorts"][cohort]  # 当前完整/小分子集合, n/ids/models/resolution 均直接读取冻结 JSON.
        scope_cn = f"完整配体集合, {block['n']} 个 PDB" if cohort == "full" else f"小分子集合, {block['n']} 个 PDB、821 个小分子实例"
        scope_en = f"all ligands, {block['n']} PDB entries" if cohort == "full" else f"small molecules, {block['n']} PDB entries and 821 small-molecule instances"
        if kind == "bar":
            detail_cn = "语义 Dice、一对一 PRAUC₀.₃ 和 PRAUC₀.₅. 柱高为 PDB 等权均值, 点为全部逐 PDB 指标, 误差线为 10,000 次 PDB bootstrap 的 95% 均值区间; 四方法和三指标在各集合内共享重采样索引, seed=20260922."
            detail_en = "Semantic Dice and one-to-one precision–recall area under the curve (PRAUC) at bidirectional coverage thresholds of 0.3 and 0.5. Bars show equally weighted PDB means, points show every PDB value and error bars show 95% confidence intervals from 10,000 PDB bootstrap resamples. All four conditions and three metrics share resampling indices within each cohort (seed=20260922)."
        elif kind == "paired":
            counts = block["paired_counts"]  # 三个冻结方向计数, 不从 x/y 重新比较或计算统计检验.
            detail_cn = f"CA2 输入下一对一 PRAUC₀.₃ 的逐 PDB 配对比较. 横轴为 LigandSeek1, 纵轴为 LigandSeek2, 虚线为等值线, 点颜色为实验密度图分辨率. LigandSeek2 较高、相等、LigandSeek1 较高分别为 {counts['l2_higher']}、{counts['equal']}、{counts['l1_higher']} 个 PDB; 相等定义为差值绝对值不超过 1e-12."
            detail_en = f"Paired PDB comparison of one-to-one precision–recall area under the curve (PRAUC) at a bidirectional coverage threshold of 0.3 with CA2 receptors. The x and y axes show LigandSeek1 and LigandSeek2, respectively, the dashed line marks equality and point colours show experimental-map resolution. LigandSeek2 is higher for {counts['l2_higher']} PDB entries, values are equal for {counts['equal']} and LigandSeek1 is higher for {counts['l1_higher']}; equality means an absolute difference of at most 1e-12."
        else:
            detail_cn = "CA2 输入下一对一₀.₃ 精确率和召回率分布. 点为全部逐 PDB 指标, 包括 0/1 端点; 白点为中位数, 粗线为四分位范围. 小提琴使用在 0/1 两端反射的 Gaussian KDE, 无量纲 bw_method 因子为 0.045, 不对 P/R 另做 bootstrap."
            detail_en = "Distributions of one-to-one precision and recall at a bidirectional coverage threshold of 0.3 with CA2 receptors. Points show every PDB value, including endpoints at 0 and 1, white points mark medians and thick lines mark interquartile ranges. Violin widths use Gaussian kernel density estimation reflected at both boundaries with a dimensionless bw_method factor of 0.045. No bootstrap intervals are calculated for precision or recall."
        caption_cn = f"LigandSeek2 与 LigandSeek1 的配体区域检测比较: {scope_cn}. {detail_cn} 下标表示预测与真实区域的双向覆盖下限. GT 为沉积受体, CA2 为 CryoAtom2 重建受体. LigandSeek2 使用冻结的 F2–F1 Gaussian 流程; LigandSeek1 使用官方 PV 模型的默认阈值及原生实例平均概率."
        caption_en = f"Ligand-region detection by LigandSeek2 and LigandSeek1: {scope_en}. {detail_en} GT denotes deposited receptors and CA2 denotes CryoAtom2-reconstructed receptors. LigandSeek2 uses the frozen F2–F1 Gaussian workflow; LigandSeek1 uses the official PV model with its default thresholds and native mean instance probabilities."
        captions[letter] = caption_cn + "\nENGLISH:\n" + caption_en
    composite_cn = "LigandSeek2 与 LigandSeek1 的配体区域检测比较. 左列为全部 179 个 PDB, 右列为包含小分子标签的 94 个 PDB、821 个小分子实例. a、b, 语义 Dice 和一对一 PRAUC₀.₃/PRAUC₀.₅, 柱高为 PDB 等权均值, 点为全部 PDB 指标, 误差线为 10,000 次配对 PDB bootstrap 的 95% 均值区间; 四方法和三指标在各集合内共享重采样索引, seed=20260922. c、d, CA2 输入下一对一 PRAUC₀.₃ 的同 PDB 两代配对比较, 颜色表示实验密度图分辨率, 虚线表示相等. e、f, CA2 输入下一对一₀.₃ 精确率/召回率; 保留全部 0/1 端点, 白点为中位数, 粗线为四分位范围, 小提琴为两端反射 KDE (bw_method=0.045). 下标表示预测与真实区域的双向覆盖下限. GT 为沉积受体, CA2 为 CryoAtom2 重建受体. LigandSeek2 使用冻结的 F2–F1 Gaussian 流程; LigandSeek1 使用官方 PV 模型的默认阈值和原生实例平均概率. "
    composite_en = "Ligand-region detection by LigandSeek2 and LigandSeek1. The left column includes all 179 PDB entries; the right column includes 94 PDB entries with 821 small-molecule instances. a, b, Semantic Dice and one-to-one precision–recall area under the curve (PRAUC) at bidirectional coverage thresholds of 0.3 and 0.5. Bars show equally weighted PDB means, points show every PDB value and error bars show 95% mean confidence intervals from 10,000 paired PDB bootstrap resamples. Four conditions and three metrics share resampling indices within each cohort (seed=20260922). c, d, Paired PDB comparisons of one-to-one PRAUC₀.₃ with CA2 receptors. Colours show experimental-map resolution and dashed lines mark equality. e, f, One-to-one precision and recall at a coverage threshold of 0.3 with CA2 receptors. All endpoints at 0 and 1 are retained. White points mark medians, thick lines mark interquartile ranges and violin widths show boundary-reflected kernel density estimates (bw_method=0.045). GT denotes deposited receptors and CA2 denotes CryoAtom2-reconstructed receptors. LigandSeek2 uses the frozen F2–F1 Gaussian workflow; LigandSeek1 uses the official PV model with default thresholds and native mean instance probabilities. "
    pages = []  # list[dict], 同源 SVG 场景、双语备注和图名, 顺序决定 PowerPoint 页序.
    for page_index, stem in enumerate(stems):
        composite = page_index == 6
        fig = plt.figure(figsize=COMPOSITE_SIZE if composite else SINGLE_SIZE)
        axes, colorbar_axes, panel_ids = [], [], []  # 三个列表分别是科学绘图区、精确排除的色条、与科学轴逐项对齐的字母.
        if composite:
            for index, (letter, cohort, kind) in enumerate(panel_specs):
                col = index % 2
                left = (0.10, 0.58)[col]
                paired_height = 0.315 * 163.0 / 190.0  # 正方形配对图区的 Figure 相对高度, 等于固定宽度乘画布宽/高.
                paired_bottom = (0.718 + 0.060 + 0.177 - paired_height) / 2  # 与上方柱图和下方分布图保持相同实际绘图区间距.
                rect = {"bar": [left, 0.718, 0.315, 0.162], "paired": [left, paired_bottom, 0.315, paired_height], "violin": [left, 0.060, 0.315, 0.177]}[kind]  # (4,), 同列三面板左右边界和重复间距相同, paired 宽/高的物理长度相同.
                ax, panel_colorbars = draw_panel(fig, data["cohorts"][cohort], kind, rect, letter)
                axes.append(ax)
                colorbar_axes.extend(panel_colorbars)
                panel_ids.append(letter)
            for left, heading in ((0.10, "All ligands"), (0.58, "Small molecules")):
                fig.text(left + 0.315 / 2, 0.985, heading, ha="center", va="top", fontsize=10.0, fontweight="bold")
            legend_methods = METHODS
            notes = composite_cn + "\nENGLISH:\n" + composite_en
            name = "ligandseek2-vs-ligandseek1"
            row_groups = [["a", "b"], ["c", "d"], ["e", "f"]]  # 三个同排比较组, 每组上下边界与绘图区高度必须相同.
            column_groups = [["a", "c", "e"], ["b", "d", "f"]]  # 两个同列比较组, 每组三轴左右边界、宽度、字母横锚点与重复间距必须一致.
        else:
            letter, cohort, kind = panel_specs[page_index]
            rect = {"bar": [0.17, 0.300, 0.77, 0.460], "paired": [0.17, 0.220, 0.56, 0.56 * 89.0 / 85.0], "violin": [0.17, 0.300, 0.77, 0.460]}[kind]  # (4,), 单图专用 Figure 矩形, 不更改任何数据值或冻结统计.
            ax, colorbar_axes = draw_panel(fig, data["cohorts"][cohort], kind, rect, letter)
            axes, panel_ids = [ax], [letter]
            fig.text(0.17, 0.958, "All ligands" if cohort == "full" else "Small molecules", fontsize=10.0, fontweight="bold", va="top")
            legend_methods = METHODS if kind == "bar" else ("L2_CA2", "L1_CA2")
            notes = captions[letter]
            name = "l2-l1-stage1-" + stem.replace("_", "-")
            row_groups, column_groups = [], []
        handles = [Patch(facecolor=COLORS[method], edgecolor="none", label=LABELS[method]) for method in legend_methods]  # 每个图例元素对应一个实际展示的模型/受体条件.
        fig.legend(handles=handles, loc="upper center" if composite else "lower center", bbox_to_anchor=(0.5, 0.951) if composite else (0.55, 0.045), ncol=4 if composite else 2, fontsize=8.5, handlelength=1.0, handletextpad=0.45, columnspacing=1.0, labelspacing=0.45)
        fig.canvas.draw()  # 完成字体、图例、square aspect 和色条的最后布局, 然后测量实际绘图区.
        require_matplotlib_panel_alignment(fig, axes=axes, panel_ids=panel_ids, row_groups=row_groups, column_groups=column_groups, exclude_axes=colorbar_axes, json_out=qa_root / f"{stem}.alignment.json", overlay_svg=qa_root / f"{stem}.alignment.svg", tolerance_pt=1.5, gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
        svg_path = render_root / f"{stem}.svg"
        pdf_path = render_root / f"{stem}.pdf"
        fig.savefig(svg_path)
        fig.savefig(pdf_path)
        glyph_audit = subprocess.run([sys.executable, "-B", str(nature_scripts / "audit_pdf_text.py"), str(pdf_path), "--min-pt", "5.55", "--json"], check=True, capture_output=True, text=True, encoding="utf-8")
        (qa_root / f"{stem}.glyph-audit.json").write_text(glyph_audit.stdout, encoding="utf-8")
        subprocess.run([sys.executable, "-B", str(nature_scripts / "audit_figure_collisions.py"), str(pdf_path), "--json-out", str(qa_root / f"{stem}.collision-audit.json"), "--overlay-pdf", str(qa_root / f"{stem}.collision-audit.pdf")], check=True)
        fig.savefig(render_root / f"{stem}.png", dpi=DPI)
        svg_root = ET.parse(svg_path).getroot()  # 普通 SVG 节点树, 只检查成熟 transport 的已知支持子集, 不改写或 flatten 文字.
        if any(node.tag.rsplit("}", 1)[-1] in {"tspan", "image"} for node in svg_root.iter()):
            raise ValueError(f"Unsupported editable SVG content in {svg_path}")
        shapes = convert(svg_path)  # list[dict], 同一 SVG 的字形文本、点椭圆和路径折线; 不使用旧 parser 的全局目录或 CLI.
        pages.append({"stem": stem, "name": name, "notes": notes, "width": fig.get_figwidth() * 72, "height": fig.get_figheight() * 72, "shapes": shapes})
        for extension in ("svg", "pdf", "png"):
            shutil.copy2(render_root / f"{stem}.{extension}", output_root / f"{stem}.{extension}")
        plt.close(fig)
    manifest = {"slide_size_pt": [COMPOSITE_SIZE[0] * 72, COMPOSITE_SIZE[1] * 72], "pages": pages}  # 组合画布单位 pt, pages 的同源几何字段由本入口 Docstring 定义.
    (build_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-data", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--nature-scripts", type=Path, required=True)
    args = parser.parse_args()
    render_figures(args.plot_data, args.output_root, args.build_root, args.nature_scripts)
