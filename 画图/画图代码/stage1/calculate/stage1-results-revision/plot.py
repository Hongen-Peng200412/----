"""从冻结统计生成 Stage 1 主结果、候选质量和补充图。

入口 main 按相同 PDB 轴连接完成度记录，计算固定候选数量下宏平均的
bootstrap 区间，再由 draw_panel 与 export_figure 绘图和导出。
不运行模型、不修改实例命中判定，也不改写冻结输入。

输出目录由 FIGURE_BUILD_ROOT 指定，默认位于论文 temp。manifest.json
记录图名、SVG 物理尺寸及双语图注；scenes.json 保存同源 SVG 的可编辑
形状；completion_summary.csv 与 source_data.csv 保存新柱图统计和逐 PDB 值。
"""

import csv
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").is_file())
CODE = ROOT / "画图/画图代码"
sys.path.insert(0, str(CODE / "stage1/calculate/stage1-main-sixpanel"))
from svg_to_scene import convert
sys.path.insert(0, str(CODE / "e2e/calculate/find-build-shared"))
import completion_plot
sys.path.insert(0, str(Path.home() / ".codex/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment

MODELS = ("Emap", "Cryo", "GT")
DOMAINS = {"Emap": "Emap2lig", "Cryo": "CA2", "GT": "GT"}
COLOURS = {"Emap": "#A1ABB3", "Cryo": "#5B72B7", "GT": "#138B8D"}
LABELS = {"Emap": "Emap2lig-Find", "Cryo": "LigandSeek-Find (CA2)", "GT": "LigandSeek-Find (GT)"}


def draw_panel(ax, kind, cohort, data, summary):
    """在同尺度面板绘制冻结结果；只给散点增加可复现的横向抖动。

    cohort 为 full 或 small；data 保留原始 values、bars、distribution。
    summary 的键为 (cohort, model, budget)，每项含 mean/lower/upper，
    比例单位为 0–1；逐 PDB 结果和方法顺序都保持原样。
    paired_metric 在新条件取 dice, 旧条件缺省 oto03; 配对 x/y 均为 (N_pdb,), 与当前 cohort 的同一 PDB 轴对齐, full 为179、small 为94.
    """
    block = data["cohorts"][cohort]
    if kind in ("overall", "strict"):
        metrics = ("dice", "oto03") if kind == "overall" else ("oto05",)
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
        labels = ["Semantic Dice", "Instance-level\n" + r"$\mathrm{PRAUC}_{0.3}$"] if kind == "overall" else [r"Instance-level $\mathrm{PRAUC}_{0.5}$"]
        ax.set(xlim=(-0.5, len(metrics) - 0.5), xticks=range(len(metrics)), xticklabels=labels, ylabel="Score", ylim=(0, 1.06), yticks=[0, 0.5, 1])
        ax.tick_params(axis="x", length=0, pad=6)
    elif kind == "paired":
        # 新主图配对语义 Dice; no_level 的旧图仍使用原实例 PRAUC.
        metric = data["paired_metric"] if "paired_metric" in data else "oto03"
        x = np.asarray(block["models"]["Emap"]["values"][metric])
        y = np.asarray(block["models"]["Cryo"]["values"][metric])
        ax.plot([0, 1], [0, 1], color="#8B969F", linewidth=0.8, linestyle=(0, (3, 3)), zorder=1)
        points = ax.scatter(x, y, c=block["resolution"], cmap="viridis_r", vmin=1, vmax=4, s=13, edgecolor="white", linewidth=0.3, alpha=0.8, zorder=2, clip_on=False)
        ax.set(xlim=(0, 1), ylim=(0, 1), xticks=[0, 0.5, 1], yticks=[0, 0.5, 1], xlabel="Emap2lig-Find", ylabel="LigandSeek-Find (CA2)", aspect="equal")
        # 沿用原主图的分辨率着色、1–4 Å色条和等比例坐标，不替换为单色点。
        left, bottom, width, height = ax.get_position().bounds
        colour_axis = ax.figure.add_axes([left + width + 0.012, bottom, 0.010, height], label="<colorbar>")
        colourbar = ax.figure.colorbar(points, cax=colour_axis, ticks=[1, 2, 3, 4])
        colourbar.set_label("Resolution (Å)", fontsize=7.3, labelpad=3)
        colourbar.ax.tick_params(labelsize=7.1, length=2, width=0.6)
        colourbar.outline.set_visible(False)
        colourbar.solids.set_rasterized(False)
        colourbar.solids.set_alpha(1)
        colourbar.solids.set_edgecolor("face")
        colourbar.solids.set_linewidth(0.2)
        counts = block["paired_counts"]
        xlabel = f"Emap2lig-Find\nHigher / equal / lower:\n{counts['find_higher']} / {counts['equal']} / {counts['emap_higher']}" if "paired_metric" in data else f"Emap2lig-Find\nHigher / equal / lower: {counts['find_higher']} / {counts['equal']} / {counts['emap_higher']}"
        ax.set_xlabel(xlabel, fontsize=7.2)
    elif kind == "precision_recall":
        for metric_index, metric in enumerate(("precision", "recall")):
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
        ax.set(xlim=(-0.65, 6.75), ylim=(0, 1.06), yticks=[0, 0.5, 1], ylabel="Score", xticks=[1, 5.1], xticklabels=["Instance-level\nprecision", "Instance-level\nrecall"])
        ax.tick_params(axis="x", length=0, pad=6)
    elif kind == "completion":
        for budget_index, budget in enumerate((100, 300)):
            for model_index, model in enumerate(MODELS):
                x = budget_index + (model_index - 1) * 0.235
                stats = summary[(cohort, model, budget)]
                colour = COLOURS[model]
                mean, lower, upper = np.asarray([stats["mean"], stats["lower"], stats["upper"]]) * 100
                ax.bar(x, mean, width=0.205, color=colour, edgecolor="none", zorder=2)
                ax.vlines(x, lower, upper, color="#42515D", linewidth=0.85, zorder=3)
                ax.hlines([lower, upper], x - 0.035, x + 0.035, color="#42515D", linewidth=0.85, zorder=3)
                ax.text(x, upper + 3.2, f"{mean:.1f}", ha="center", va="bottom", fontsize=7.2, color="#263746")
        ax.set(xlim=(-0.53, 1.53), ylim=(0, 100), yticks=[0, 25, 50, 75, 100], xticks=[0, 1], xticklabels=["100", "300"], xlabel="Relative candidate count (%)", ylabel="Mean detection completion (%)")
    if kind == "completion":
        ax.grid(False)
    else:
        ax.grid(axis="y", color="#E5E9EC", linewidth=0.45, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7.2, length=2.5, width=0.65)


def flatten_positioned_text(svg):
    """展开公式定位tspan，保留标准小数点、下标和原生可编辑文字。

    只运输SVG已给定的逐字符位置，不重新排版，不用Unicode下标拼凑公式。
    """
    namespace = "{http://www.w3.org/2000/svg}"
    tree = ET.parse(svg)
    for parent in list(tree.getroot().iter()):
        for text in list(parent):
            spans = list(text) if text.tag == namespace + "text" else []
            if not spans:
                continue
            group = ET.Element(namespace + "g", dict(text.attrib))
            for span in spans:
                xs = [float(value) for value in span.get("x", "0").split()]
                ys = [float(value) for value in span.get("y", "0").split()]
                characters = span.text or ""
                assert len(xs) == len(characters), "公式SVG必须提供逐字符横坐标"
                for i, character in enumerate(characters):
                    item = ET.SubElement(group, namespace + "text", {"style": span.get("style", ""), "x": str(xs[i]), "y": str(ys[min(i, len(ys) - 1)])})
                    item.text = character
            index = list(parent).index(text)
            parent.remove(text)
            parent.insert(index, group)
    tree.write(svg, encoding="utf-8", xml_declaration=True)


def export_figure(fig, figure_id, notes, build, manifest):
    """在当前目录导出同源图稿、对齐证据与原生 PPT 场景清单。

    manifest 为按页面顺序追加的 list[dict]。每项保存 id、stem、宽高 pt、
    双语 notes 和 SVG 的 shapes；这些形状由 build_deck.mjs 直接装配。
    """
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=build / f"{figure_id}.alignment.json", overlay_svg=build / f"{figure_id}.alignment.svg", tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(build / f"{figure_id}.svg", facecolor="white")
    fig.savefig(build / f"{figure_id}.pdf", facecolor="white")
    fig.savefig(build / f"{figure_id}.png", dpi=600, facecolor="white")
    flatten_positioned_text(build / f"{figure_id}.svg")
    manifest.append({"id": figure_id, "stem": figure_id, "width": float(fig.get_figwidth() * 72), "height": float(fig.get_figheight() * 72), "notes": notes, "shapes": convert(build / f"{figure_id}.svg")})
    plt.close(fig)


# ================================================================================================
def main():
    """按固定图契约生成四张图，所有可再生输出只写本次 build 目录。"""
    build = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/stage1_revision_20261025/figures"
    build.mkdir(parents=True, exist_ok=True)
    # 当前主图读取显式 level 的冻结统计; no_level 只用于重建已区分的旧条件图.
    condition = os.environ.get("EMAP2LIG_CONDITION", "explicit_emdb_level")
    assert condition in ("explicit_emdb_level", "no_level"), "必须明确选择已登记的 Emap2lig 条件"
    # level_data 指向本轮新统计, 不覆盖原 v5 数据或旧共享完成度数据.
    level_data = CODE / "stage1/output/stage1-results-revision/explicit_emdb_level/data"
    # plot_path 指向当前条件的逐 PDB 指标、区间与小提琴分布; 旧 v5 保留原位.
    plot_path = level_data / "plot_data.json" if condition == "explicit_emdb_level" else CODE / "stage1/output/stage1-main-sixpanel/v5/data/plot_data.json"
    # completion_path 指向当前条件的全配体和全部小分子完成度面板; 不读取 Build 子集替代它们.
    completion_path = level_data / "completion_panels.json" if condition == "explicit_emdb_level" else CODE / "e2e/output/find-build-shared/data.json"
    data = json.loads(plot_path.read_text(encoding="utf-8"))
    panels = json.loads(completion_path.read_text(encoding="utf-8"))["panels"]
    completion = {}
    summary = {}
    source_rows = []
    summary_rows = []
    for cohort, scope in (("full", "find_full"), ("small", "find_stage1_small")):
        ids = data["cohorts"][cohort]["ids"]  # (P,), 当前固定 PDB 轴，分别含 179 或 94 个 PDB。
        # (10000, P), 同一集合所有方法和预算共用的有放回抽样索引。
        indices = np.random.default_rng(20260922).integers(0, len(ids), size=(10000, len(ids)))
        for model in MODELS:
            panel = next(p for p in panels if p["scope"] == scope and p["domain"] == DOMAINS[model])
            completion[(cohort, model)] = panel
            for budget in (100, 300):
                by_pdb = {row["pdb_id"]: row for row in panel["distributions"][str(budget)]}
                assert set(by_pdb) == set(ids), "完成度 PDB 轴必须与主性能范围一致"
                values = np.asarray([by_pdb[pdb]["completion"] for pdb in ids])
                lower, upper = np.percentile(values[indices].mean(axis=1), [2.5, 97.5])
                stats = {"mean": float(values.mean()), "lower": float(lower), "upper": float(upper)}
                summary[(cohort, model, budget)] = stats
                summary_rows.append({"cohort": cohort, "model": model, "candidate_percent": budget, "pdb_count": len(ids), **stats})
                for pdb in ids:
                    row = by_pdb[pdb]
                    source_rows.append({"cohort": cohort, "model": model, "candidate_percent": budget, "pdb_id": pdb, "success_count": row["success_count"], "target_count": row["target_count"], "candidate_limit": row["attempt_budget"], "completion": row["completion"]})
    for filename, rows in (("completion_summary.csv", summary_rows), ("source_data.csv", source_rows)):
        with (build / filename).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (build / "statistics.json").write_text(json.dumps({"bootstrap_replicates": 10000, "bootstrap_seed": 20260922, "completion": summary_rows, "paired_counts": {c: data["cohorts"][c]["paired_counts"] for c in ("full", "small")}}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Calibri 提供阈值下标字形；SVG 运输器按同一字体度量可编辑文字。
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Calibri", "Arial"], "font.size": 8, "axes.labelsize": 7.6, "axes.titlesize": 8.1, "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none", "pdf.fonttype": 42, "text.color": "#263746", "axes.labelcolor": "#263746", "xtick.color": "#263746", "ytick.color": "#263746"})
    handles = [Patch(facecolor=COLOURS[m], edgecolor="none", label=LABELS[m]) for m in MODELS]
    common_zh = "LigandSeek-Find 使用沉积受体（GT）或 CryoAtom2 重建受体（CA2），与仅使用密度的 Emap2lig-Find 比较。全配体包含179个PDB、2,502个实例；小分子包含94个PDB、821个实例。"
    common_en = "LigandSeek-Find uses deposited receptors (GT) or CryoAtom2-reconstructed receptors (CA2) and is compared with the density-only method Emap2lig-Find. All ligands comprise 179 PDB entries and 2,502 instances; small molecules comprise 94 PDB entries and 821 instances."
    captions = {
        "stage1-overall-performance": "配体区域检出的整体表现。" + common_zh + "\na, b，全配体和小分子的语义Dice，以及双向覆盖阈值0.3下的实例级PRAUC。柱高与横线为PDB等权均值，淡色点为逐PDB结果；误差条为10,000次PDB bootstrap的95%区间。\nc, d，同一PDB上CA2条件的LigandSeek-Find与Emap2lig-Find的实例级PRAUC比较；虚线表示分数相等，点颜色表示实验密度图分辨率。较高、相等、较低的PDB数分别为112/40/27和40/36/18。\nENGLISH:\nOverall performance of ligand-region detection. " + common_en + "\na, b, Semantic Dice, and instance-level PRAUC at a bidirectional coverage threshold of 0.3, for all ligands and small molecules, respectively. Bars and horizontal marks show PDB-equal means; faint points show individual PDB entries. Error bars show 95% intervals from 10,000 PDB bootstrap resamples.\nc, d, Paired instance-level PRAUC comparisons between LigandSeek-Find (CA2) and Emap2lig-Find. Each point represents one PDB entry; colours indicate map resolution, and dashed lines indicate equal scores. Higher/equal/lower counts are 112/40/27 for all ligands and 40/36/18 for small molecules.",
        "stage1-candidate-quality": "候选区域质量与有限候选数量下的配体检出。" + common_zh + "\na, b，双向覆盖阈值0.3下，全配体和小分子的实例级精确率与召回率。小提琴表示分布，淡色点为逐PDB结果，白色圆点与粗线为中位数和四分位范围。\nc, d，全配体和小分子在100%及300%相对候选数量下的平均检出完成度。100%表示考察的候选数上限等于该PDB的真实实例数，300%为其三倍。候选与真实实例的双向覆盖均至少为0.3；候选归属覆盖率几何均值最大的真实实例，每个实例只累计首次检出。小分子视图忽略归属于非小分子的候选，保留背景与重复命中。柱高为PDB等权均值；误差条为10,000次PDB bootstrap的95%区间。\nENGLISH:\nCandidate-region quality and ligand detection at limited candidate counts. " + common_en + "\na, b, Instance-level precision and recall for all ligands and small molecules, respectively, at a bidirectional coverage threshold of 0.3. Violins show distributions, faint points show individual PDB entries, and white circles and thick lines indicate medians and interquartile ranges.\nc, d, Mean detection completion for all ligands and small molecules at relative candidate counts of 100% and 300%. These limits equal one and three times the ground-truth instance count per PDB, respectively. Candidates are assigned by maximal geometric-mean coverage among pairs satisfying bidirectional coverage of at least 0.3. Each instance contributes only its first detection. The small-molecule evaluation omits candidates assigned to other ligand classes but retains background candidates and repeated hits. Bars show PDB-equal means; error bars show 95% intervals from 10,000 PDB bootstrap resamples.",
        "stage1-strict-threshold": "更严格覆盖阈值下的配体区域检出。" + common_zh + "\na, b，全配体和小分子在双向覆盖阈值0.5下的实例级PRAUC。柱高与横线表示PDB等权均值，淡色点表示各PDB结果；误差条为10,000次PDB bootstrap的95%区间。\nENGLISH:\nLigand-region detection at a stricter coverage threshold. " + common_en + "\na, b, Instance-level PRAUC for all ligands and small molecules, respectively, at a bidirectional coverage threshold of 0.5. Bars and horizontal marks show PDB-equal means; faint points show individual PDB entries. Error bars show 95% intervals from 10,000 PDB bootstrap resamples.",
    }
    if condition == "explicit_emdb_level":
        counts = [data["cohorts"][cohort]["paired_counts"] for cohort in ("full", "small")]
        counts_text = " and ".join(f"{item['find_higher']}/{item['equal']}/{item['emap_higher']}" for item in counts)
        captions["stage1-overall-performance"] = "配体区域检出的整体表现。" + common_zh + "\na, d，全配体和小分子的语义Dice，以及双向覆盖阈值0.3下的实例级PRAUC。柱高与横线为PDB等权均值，淡色点为逐PDB结果；误差条为10,000次PDB bootstrap的95%区间。\nb, e，同一PDB上CA2条件的LigandSeek-Find与Emap2lig-Find的语义Dice比较；虚线表示分数相等，点颜色表示实验密度图分辨率。较高、相等、较低的PDB数分别为141/15/23和68/7/19。\nc, f，双向覆盖阈值0.3下，全配体和小分子的实例级精确率与召回率。小提琴表示分布，淡色点为逐PDB结果，白色圆点与粗线为中位数和四分位范围。\nENGLISH:\nOverall performance of ligand-region detection. " + common_en + "\na, d, Semantic Dice, and instance-level PRAUC at a bidirectional coverage threshold of 0.3, for all ligands and small molecules, respectively. Bars and horizontal marks show PDB-equal means; faint points show individual PDB entries. Error bars show 95% intervals from 10,000 PDB bootstrap resamples.\nb, e, Paired semantic Dice comparisons between LigandSeek-Find (CA2) and Emap2lig-Find. Each point represents one PDB entry; colours indicate map resolution, and dashed lines indicate equal scores. Higher/equal/lower counts are " + counts_text + " for all ligands and small molecules, respectively.\nc, f, Instance-level precision and recall for all ligands and small molecules, respectively, at a bidirectional coverage threshold of 0.3. Violins show distributions, faint points show individual PDB entries, and white circles and thick lines indicate medians and interquartile ranges."
    manifest = []
    plt.rcParams.update({"mathtext.fontset": "custom", "mathtext.rm": "Calibri", "mathtext.it": "Calibri:italic", "mathtext.bf": "Calibri:bold", "mathtext.default": "regular"})
    specifications = (("stage1-overall-performance", ("overall", "paired"), 170), ("stage1-candidate-quality", ("precision_recall", "completion"), 132), ("stage1-strict-threshold", ("strict",), 78))
    for figure_id, kinds, height_mm in specifications:
        six_panel = figure_id == "stage1-overall-performance" and condition == "explicit_emdb_level"
        if six_panel:
            height_mm = 155
        fig = plt.figure(figsize=(180 / 25.4, height_mm / 25.4))
        if six_panel:
            grid = fig.add_gridspec(2, 3, left=0.085, right=0.955, bottom=0.16, top=0.87, wspace=0.60, hspace=0.70)
            # 六面板按行排列测试范围, 按列排列整体、配对和 P/R; 不改变现有图元.
            positions = [(row, col, kind, cohort) for row, cohort in enumerate(("full", "small")) for col, kind in enumerate(("overall", "paired", "precision_recall"))]
        elif figure_id == "stage1-overall-performance":
            grid = fig.add_gridspec(2, 2, left=0.105, right=0.91, bottom=0.12, top=0.86, wspace=0.48, hspace=0.48, height_ratios=[0.78, 1.2])
            positions = [(row, col, kind, cohort) for row, kind in enumerate(kinds) for col, cohort in enumerate(("full", "small"))]
        else:
            grid = fig.add_gridspec(len(kinds), 2, left=0.105, right=0.985, bottom=0.13 if len(kinds) == 2 else 0.24, top=0.83 if len(kinds) == 2 else 0.68, wspace=0.31, hspace=0.60)
            positions = [(row, col, kind, cohort) for row, kind in enumerate(kinds) for col, cohort in enumerate(("full", "small"))]
        fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.54, 0.985), ncol=3, frameon=False, fontsize=7.6, handlelength=1.2, columnspacing=1.2)
        for row, col, kind, cohort in positions:
            ax = fig.add_subplot(grid[row, col])
            if six_panel:
                ax.set_box_aspect(1)
            draw_panel(ax, kind, cohort, data, summary)
            letter = chr(97 + row * (3 if six_panel else 2) + col)
            ax.set_gid(letter)
            ax.annotate(letter, xy=(0, 1), xycoords="axes fraction", xytext=(-27, 8), textcoords="offset points", fontsize=10, fontweight="bold", va="bottom", annotation_clip=False)
            title = "All ligands" if cohort == "full" else "Small molecules"
            if kind == "paired":
                title += " · Dice" if six_panel else r" · instance-level $\mathbf{PRAUC}_{0.3}$"
            ax.set_title(title, loc="left", pad=10, fontweight="bold")
        export_figure(fig, figure_id, captions[figure_id], build, manifest)

    fig = plt.figure(figsize=(180 / 25.4, 142 / 25.4))
    grid = fig.add_gridspec(2, 3, left=0.085, right=0.985, bottom=0.13, top=0.82, wspace=0.34, hspace=0.52)
    completion_plot.COLORS.update({DOMAINS[m]: COLOURS[m] for m in MODELS})
    curve_handles = [Line2D([], [], color=completion_plot.MEAN_COLOR, linewidth=1.8, marker="o", markersize=3, label="Mean"), Line2D([], [], color=completion_plot.MEDIAN_COLOR, linewidth=1.05, marker="D", markerfacecolor="none", markersize=3.5, label="Median"), Line2D([], [], color="#7F8C97", marker="o", linestyle="none", markersize=3, label="Individual PDB")]
    fig.legend(handles=curve_handles, loc="upper center", bbox_to_anchor=(0.53, 0.98), ncol=3, frameon=False, fontsize=7.6)
    for row, cohort in enumerate(("full", "small")):
        for col, model in enumerate(("GT", "Cryo", "Emap")):
            ax = fig.add_subplot(grid[row, col])
            panel = completion[(cohort, model)]
            title = ("All ligands" if cohort == "full" else "Small molecules") + ", " + DOMAINS[model]
            letter = chr(97 + row * 3 + col)
            completion_plot.draw_panel(ax, panel, title, "", True)
            ax.set_gid(letter)
            ax.annotate(letter, xy=(0, 1), xycoords="axes fraction", xytext=(-22, 8), textcoords="offset points", fontsize=10, fontweight="bold", va="bottom", annotation_clip=False)
            if col == 0:
                ax.set_ylabel("Detected instances (%)", fontsize=7.6)
            if row == 1:
                ax.set_xlabel("Relative candidate count (%)", fontsize=7.2)
            else:
                ax.tick_params(axis="x", labelbottom=False)
    notes = "候选排序中的完整配体检出曲线。" + common_zh + "\na–c为全配体，d–f为小分子；左、中、右列分别为GT、CA2和Emap2lig。候选与真实实例的双向覆盖均至少为0.3，候选归属覆盖率几何均值最大的真实实例；每个实例只累计首次检出。横轴为候选数量相对于各PDB真实实例数的百分比，纵轴为检出的不同实例比例。小分子视图忽略归属于其他类别的候选，保留背景与重复命中。绿色圆点和实线表示PDB等权均值，蓝色菱形和实线表示中位数；灰点和小提琴表示50%、100%、200%、300%候选数量下的逐PDB分布。\nENGLISH:\nComplete ligand-detection curves across ranked candidates. " + common_en + "\na–c, All ligands. d–f, Small molecules. Columns show GT, CA2 and Emap2lig, respectively. Candidates are assigned by maximal geometric-mean coverage among pairs satisfying bidirectional coverage of at least 0.3. Each instance contributes only its first detection. The x-axis shows candidate counts relative to each PDB's ground-truth instance count; the y-axis shows the percentage of distinct instances detected. The small-molecule evaluation omits candidates assigned to other classes but retains background candidates and repeated hits. Green circles and lines show PDB-equal means; blue diamonds and lines show medians. Grey points and violins show PDB distributions at relative candidate counts of 50%, 100%, 200% and 300%."
    export_figure(fig, "stage1-completion-curves", notes, build, manifest)
    (build / "scenes.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (build / "manifest.json").write_text(json.dumps([{k: v for k, v in item.items() if k != "shapes"} for item in manifest], ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"figures": [p["id"] for p in manifest], "completion_bars": len(summary_rows), "pdb_observations": len(source_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
