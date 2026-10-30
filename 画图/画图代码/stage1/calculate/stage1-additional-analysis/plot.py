"""复用 Stage1 原图元绘制两张补充联图, 并导出同源原生 PPT 场景.

先运行同目录 prepare_data.py, 再运行本脚本和共享 build_deck.mjs. FIGURE_BUILD_ROOT 指向本次构建目录; 所有 SVG/PDF/PNG、预算统计和场景文件均写该目录, 正式图集由验收后的追加步骤更新.
scenes.json 是两页 dict 的列表, 每页含 id、width/height(pt)、双语 notes 和可编辑 shapes; manifest.json 保留相同页面字段但不含 shapes.
budget_source_data.csv 每行是范围、方法、PDB、预算, 保存 success_count/target_count、candidate_limit 和 0-1 completion; budget_summary.csv 每行是范围、方法、预算, 保存 PDB 数与 0-1 mean/lower/upper.
"""

import csv
import json
import os
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

# root 为论文仓库; shared 指向已有的 Stage1 图元及 SVG-to-native-PPT 运输实现.
root = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").is_file())
shared = root / "画图/画图代码/stage1/calculate/stage1-results-revision"
sys.path.insert(0, str(shared))
# 当前模块作为 __main__ 执行, 这里的 plot 是上述共享目录中的原图元模块.
from plot import COLOURS, DOMAINS, LABELS, MODELS, draw_panel, export_figure


if __name__ == "__main__":
    # build 是当前可清空的图稿输出; data_root 是同一次 prepare_data.py 刚生成的两条件输入, 不读取旧 temp 或旧派生缓存.
    build = Path(os.environ["FIGURE_BUILD_ROOT"])
    build.mkdir(parents=True, exist_ok=True)
    data_root = build / "data"
    conditions = json.loads((data_root / "conditions.json").read_text(encoding="utf-8"))
    # completion_path 仅指向显式 level 实验的完整 Find 预算面板, 不读取 Build 子集.
    completion_path = root / "画图/画图代码/stage1/output/stage1-results-revision/explicit_emdb_level/data/completion_panels.json"
    panels = json.loads(completion_path.read_text(encoding="utf-8"))["panels"]
    summary = {}
    source_rows = []
    summary_rows = []
    for cohort, scope in (("full", "find_full"), ("small", "find_stage1_small")):
        ids = conditions["explicit_emdb_level"]["cohorts"][cohort]["ids"]
        # (10000, N_pdb), 集合内所有方法和两档预算共用 PDB bootstrap 索引.
        indices = np.random.default_rng(20260922).integers(0, len(ids), size=(10000, len(ids)))
        for model in MODELS:
            panel = next(p for p in panels if p["scope"] == scope and p["domain"] == DOMAINS[model])
            for budget in (100, 300):
                by_pdb = {row["pdb_id"]: row for row in panel["distributions"][str(budget)]}
                values = np.asarray([by_pdb[pdb]["completion"] for pdb in ids])
                lower, upper = np.percentile(values[indices].mean(axis=1), [2.5, 97.5])
                stats = {"mean": float(values.mean()), "lower": float(lower), "upper": float(upper)}
                summary[(cohort, model, budget)] = stats
                summary_rows.append({"cohort": cohort, "method": model, "budget_percent": budget, "pdb_count": len(ids), **stats})
                for pdb in ids:
                    row = by_pdb[pdb]
                    source_rows.append({"cohort": cohort, "method": model, "pdb_id": pdb, "budget_percent": budget, "success_count": row["success_count"], "target_count": row["target_count"], "candidate_limit": row["attempt_budget"], "completion": row["completion"]})
    for filename, rows in (("budget_source_data.csv", source_rows), ("budget_summary.csv", summary_rows)):
        with (build / filename).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Calibri", "Arial"], "font.size": 8, "axes.labelsize": 7.6, "axes.titlesize": 8.1, "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none", "pdf.fonttype": 42, "text.color": "#263746", "axes.labelcolor": "#263746", "xtick.color": "#263746", "ytick.color": "#263746"})
    common_zh = "全配体包含179个PDB、2,502个实例，小分子包含94个PDB、821个实例。LigandSeek-Find 使用沉积受体（GT）或 CryoAtom2 重建受体（CA2）。"
    common_en = "All ligands comprise 179 PDB entries and 2,502 instances; small molecules comprise 94 PDB entries and 821 instances. LigandSeek-Find uses deposited receptors (GT) or CryoAtom2-reconstructed receptors (CA2). "
    captions = {
        "stage1-additional-analysis": "配体区域检出的补充分析。" + common_zh + "Emap2lig-Find 显式接收 EMDB 推荐 contour level。\na, d，全配体和小分子在双向覆盖阈值0.5下的实例级 $\\mathrm{PRAUC}_{0.5}$。柱高为PDB等权均值，淡色点为逐PDB结果；误差条为10,000次PDB bootstrap的95%区间。\nb, e，相同0.5阈值下的实例级精确率与召回率。小提琴为逐PDB分布，白点与粗线为中位数及四分位范围。\nc, f，100%和300%相对候选数量下的平均检出完成度。候选上限分别为每PDB真实实例数的一倍和三倍；命中仍要求双向覆盖至少0.3，每个真实实例只累计首次检出。背景与重复命中保留候选位置，小分子视图忽略归属于其他类别的候选。柱高为PDB等权均值，误差条同上。\nENGLISH:\nAdditional analyses of ligand-region detection. " + common_en + "Emap2lig-Find receives the EMDB-recommended contour level.\na, d, Instance-level $\\mathrm{PRAUC}_{0.5}$ for all ligands and small molecules at a bidirectional coverage threshold of 0.5. Bars show PDB-equal means, faint points show individual PDB entries, and error bars show 95% intervals from 10,000 PDB bootstrap resamples.\nb, e, Instance-level precision and recall at the same 0.5 threshold. Violins show PDB distributions; white circles and thick lines indicate medians and interquartile ranges.\nc, f, Mean detection completion at relative candidate counts of 100% and 300%, allowing one and three times the ground-truth instance count per PDB. Detection retains a bidirectional coverage threshold of 0.3, with each instance counted only on its first detection. Background candidates and repeated hits retain their positions; the small-molecule view omits candidates assigned to other classes. Bars show PDB-equal means; error bars are defined as above.",
        "stage1-no-level-comparison-NO_LEVEL": "未显式提供 contour level 时的配体区域检出。" + common_zh + "Emap2lig-Find 未显式接收 EMDB 推荐 contour level。\na, c，全配体和小分子的语义Dice、实例级 $\\mathrm{PRAUC}_{0.3}$ 与 $\\mathrm{PRAUC}_{0.5}$。柱高为PDB等权均值，淡色点为逐PDB结果；误差条为10,000次PDB bootstrap的95%区间。\nb, d，双向覆盖阈值0.3和0.5下的实例级精确率与召回率。小提琴为逐PDB分布，白点与粗线为中位数及四分位范围。两个阈值沿用同一最终候选选择与小分子类别归属。\nENGLISH:\nLigand-region detection without an explicitly supplied contour level. " + common_en + "Emap2lig-Find does not receive an explicit EMDB-recommended contour level.\na, c, Semantic Dice, instance-level $\\mathrm{PRAUC}_{0.3}$ and $\\mathrm{PRAUC}_{0.5}$ for all ligands and small molecules. Bars show PDB-equal means, faint points show individual PDB entries, and error bars show 95% intervals from 10,000 PDB bootstrap resamples.\nb, d, Instance-level precision and recall at bidirectional coverage thresholds of 0.3 and 0.5. Violins show PDB distributions; white circles and thick lines indicate medians and interquartile ranges. Both thresholds retain the same final candidate selection and small-molecule class assignment."
    }
    manifest = []
    for figure_id, condition, kinds in (("stage1-additional-analysis", "explicit_emdb_level", ("strict", "precision_recall05", "completion")), ("stage1-no-level-comparison-NO_LEVEL", "no_level", ("three_metrics", "precision_recall_both"))):
        data = conditions[condition]
        fig = plt.figure(figsize=(180 / 25.4, 148 / 25.4))
        # 沿作者正文 v1 收紧轴框间隔; 保留画布、字体、全部数据图元及 2×2 的宽面板.
        grid = fig.add_gridspec(2, len(kinds), left=0.095, right=0.985, bottom=0.16, top=0.86, wspace=0.45 if len(kinds) == 3 else 0.25, hspace=0.55)
        handles = [Patch(facecolor=COLOURS[model], edgecolor="none", label="Emap2lig-Find (no level)" if model == "Emap" and condition == "no_level" else LABELS[model]) for model in MODELS]
        fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.54, 0.98), ncol=3, frameon=False, fontsize=7.6, handlelength=1.2, columnspacing=1.2)
        for row, cohort in enumerate(("full", "small")):
            for column, kind in enumerate(kinds):
                ax = fig.add_subplot(grid[row, column])
                draw_panel(ax, kind, cohort, data, summary)
                if len(kinds) == 3 and column == 1:
                    # 第一列的数据标记较集中, 中列左移画布宽度的1.8%以平衡视觉空白; 轴框宽高和内容不变.
                    position = ax.get_position()
                    ax.set_position([position.x0 - 0.018, position.y0, position.width, position.height])
                if kind == "completion":
                    # 窄面板中同一预算的三个标签共用最高误差条上方的基线, 避免标注穿过相邻误差条.
                    for index, label in enumerate(ax.texts):
                        budget = (100, 300)[index // len(MODELS)]
                        label.set_y(max(summary[(cohort, model, budget)]["upper"] for model in MODELS) * 100 + 3.2)
                        label.set_fontsize(6.4)
                        label.set_x(label.get_position()[0] + (index % len(MODELS) - 1) * 0.05)
                letter = chr(97 + row * len(kinds) + column)
                ax.set_gid(letter)
                ax.annotate(letter, xy=(0, 1), xycoords="axes fraction", xytext=(-27, 8), textcoords="offset points", fontsize=10, fontweight="bold", va="bottom", annotation_clip=False)
                ax.set_title("All ligands" if cohort == "full" else "Small molecules", loc="left", pad=10, fontweight="bold")
        export_figure(fig, figure_id, captions[figure_id], build, manifest)
    (build / "scenes.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (build / "manifest.json").write_text(json.dumps([{key: value for key, value in page.items() if key != "shapes"} for page in manifest], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"两张原生联图场景已保存: {build}")
