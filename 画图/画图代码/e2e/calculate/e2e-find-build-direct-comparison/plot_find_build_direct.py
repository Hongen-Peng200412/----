"""绘制给定正确身份时的 Find–Build 直接比较图。

直接读取冻结完成度面板，按四种构象／RMSD 条件绘制 100% 和 300% 预算下
的逐 PDB 等权均值与百分位 bootstrap 95% 区间，不重新推理或改变计费规则。
从文件末尾顺序阅读数据选择、重采样、绘图及导出；draw_panel 被四个面板共用。
输出固定在仓库 temp/emap2lig_direct_20261020，包含同源 SVG/PDF/PNG、
逐 PDB source_data.csv、24 根柱的 summary.csv 和可编辑 PPT 装配清单。
"""

import os
import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/emap2lig_direct_20261020"
sys.path.insert(0, "C:/Users/15919/.codex/skills/nature-figure/scripts")
from audit_panel_alignment import require_matplotlib_panel_alignment

plt.rcParams.update({
    "font.family": "Arial", "font.size": 8,
    "svg.fonttype": "none", "pdf.fonttype": 42,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "text.color": "#273744", "axes.labelcolor": "#273744",
    "xtick.color": "#273744", "ytick.color": "#273744",
    "legend.frameon": False,
})
METHODS = ("Emap2lig", "CA2", "GT")
COLORS = ("#A5ADB4", "#5B74BC", "#168D8D")
LABELS = ("Emap2lig", "LigandSeek (CA2)", "LigandSeek (GT)")


def draw_panel(ax, rows, title, letter):
    """将一个条件的六个均值及区间绘制到共享尺度的坐标轴。

    rows 含两种预算×三种方法，mean/ci_low/ci_high 均为百分比。
    柱顶数字放在区间上界上方；横坐标只区分预算，颜色对应固定方法顺序。
    """
    for method_index, method in enumerate(METHODS):
        subset = [r for r in rows if r["method"] == method]
        x = np.arange(2) + (method_index - 1) * 0.235
        means = np.array([r["mean"] for r in subset])
        lower = np.array([r["ci_low"] for r in subset])
        upper = np.array([r["ci_high"] for r in subset])
        ax.bar(x, means, width=0.205, color=COLORS[method_index], edgecolor="none", zorder=2)
        ax.errorbar(x, means, yerr=[means-lower, upper-means], fmt="none",
                    ecolor="#44505A", elinewidth=0.65, capsize=2.1, capthick=0.65, zorder=3)
        for xx, mean, high in zip(x, means, upper):
            ax.text(xx, high + 2.2, f"{mean:.1f}", ha="center", va="bottom", fontsize=7.2)
    ax.set(xlim=(-0.55, 1.55), ylim=(0, 100), xticks=[0, 1], xticklabels=["100", "300"],
           yticks=[0, 25, 50, 75, 100])
    ax.set_title(title, loc="left", fontsize=8.6, pad=9)
    ax.annotate(letter, xy=(0, 1), xycoords="axes fraction", xytext=(-17, 9),
                textcoords="offset points", fontsize=10, fontweight="bold", annotation_clip=False)
    ax.tick_params(length=2.5, width=0.55, labelsize=7.3, pad=3)
    ax.set_axisbelow(True)


# ================================================================================================
panels = json.loads((ROOT / "画图/画图代码/e2e/output/find-build-shared/data.json").read_text(encoding="utf-8"))["panels"]
panels = {p["id"]: p for p in panels}
BUILD.mkdir(parents=True, exist_ok=True)
conditions = [(1, 2.0), (1, 3.0), (50, 2.0), (50, 3.0)]
summaries, source_rows = [], []

# (10000,77)，每次抽取完整 PDB 轴；所有方法／预算共用同一索引以保留配对关系。
rng = np.random.default_rng(20261020)
bootstrap_index = rng.integers(0, 77, size=(10000, 77))
for panel_index, (pose, threshold) in enumerate(conditions):
    for budget in (100, 300):
        for method in METHODS:
            panel = panels[f"assume_{method}_pose{pose}_rmsd{threshold}"]
            records = sorted(panel["distributions"][str(budget)], key=lambda r: r["pdb_id"])
            values = np.array([r["completion"] for r in records]) * 100
            intervals = np.quantile(values[bootstrap_index].mean(axis=1), [0.025, 0.975])
            summaries.append({"panel": chr(97+panel_index), "pose_limit": pose, "rmsd_A": threshold,
                              "budget_percent": budget, "method": method, "pdb_count": len(records),
                              "mean": float(values.mean()), "ci_low": float(intervals[0]), "ci_high": float(intervals[1])})
            source_rows.extend({"panel": chr(97+panel_index), "pose_limit": pose, "rmsd_A": threshold,
                                "budget_percent": budget, "method": method, "pdb_id": r["pdb_id"],
                                "completion": r["completion"]} for r in records)

for name, rows in [("summary.csv", summaries), ("source_data.csv", source_rows)]:
    with (BUILD/name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

fig, axes = plt.subplots(2, 2, figsize=(7.0866141732, 4.6456692913))  # 180×118 mm。
fig.subplots_adjust(left=0.095, right=0.98, bottom=0.14, top=0.86, hspace=0.44, wspace=0.19)
for index, (ax, (pose, threshold)) in enumerate(zip(axes.flat, conditions)):
    name = "Top-1" if pose == 1 else "Best-of-50"
    draw_panel(ax, [r for r in summaries if r["panel"] == chr(97+index)],
               f"{name}, RMSD <{threshold:g} Å", chr(97+index))
    if index % 2 == 0:
        ax.set_ylabel("Mean completion (%)", fontsize=8)
fig.legend(handles=[Patch(facecolor=c, edgecolor="none", label=l) for c,l in zip(COLORS,LABELS)],
           loc="upper left", bbox_to_anchor=(0.084, 0.995), ncol=3, fontsize=8,
           handlelength=1.1, handleheight=0.8, columnspacing=2.4, handletextpad=0.6)
fig.supxlabel("Relative attempt budget (%)", y=0.035, fontsize=8.5)
fig.canvas.draw()
require_matplotlib_panel_alignment(fig, json_out=BUILD/"direct.alignment.json",
                                  overlay_svg=BUILD/"direct.alignment.svg", tolerance_pt=1.5,
                                  gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
fig.savefig(BUILD/"direct.svg", facecolor="white")
fig.savefig(BUILD/"direct.pdf", facecolor="white")
fig.savefig(BUILD/"direct.png", dpi=600, facecolor="white")

notes_zh = (r"给定正确配体身份时 LigandSeek 与 Emap2lig 的 Find–Build 完成度比较。"
            r"a,b，模型评分首选构象；c,d，50 个候选中重原子 RMSD 最低的构象。"
            r"左、右列分别要求重原子 RMSD 严格 $<2\,\mathrm{Å}$ 和 $<3\,\mathrm{Å}$。"
            r"每组柱从左到右为 Emap2lig、使用 CryoAtom2 重建受体（CA2）的 LigandSeek，以及使用沉积受体（GT）的 LigandSeek。"
            r"两条管线均在相同的 77 个 PDB、446 个单残基无缺失原子有机小分子上评估，并给定正确 SMILES。"
            r"LigandSeek 使用预测 blob 质心引导的 PocketXMol-tuned 中心对接，Emap2lig 使用其原生 blob 引导的 Build 模型。"
            r"柱高为逐 PDB 等权平均完成度，误差线为对 77 个 PDB 进行 10,000 次 bootstrap 重采样得到的百分位 95% 区间。"
            r"相对预算 $\rho$ 允许每个含 $N$ 个目标实例的 PDB 进行 $\lfloor\rho N\rfloor$ 次计费尝试；"
            r"完成度为成功实例数除以 $N$。背景候选计费，真实范围外前景跳过；未检出与失败实例保留在分母中。")
notes_en = (r"Find–Build completion by LigandSeek and Emap2lig with correct ligand identities. "
            r"a,b, Model-ranked top-1 poses. c,d, Poses with the lowest heavy-atom RMSD among 50 candidates. "
            r"Left and right columns require heavy-atom RMSD strictly $<2\,\mathrm{Å}$ and $<3\,\mathrm{Å}$, respectively. "
            r"Within each budget, bars show Emap2lig, LigandSeek with CryoAtom2-reconstructed receptors (CA2), and LigandSeek with deposited receptors (GT), from left to right. "
            r"Both pipelines were evaluated on the same 77 PDBs containing 446 single-residue organic small molecules with no missing atoms and were supplied with the correct SMILES. "
            r"LigandSeek uses PocketXMol-tuned centre docking guided by predicted blob centroids; Emap2lig uses its native blob-guided Build model. "
            r"Bars show the PDB-equal mean completion; error bars show percentile 95% intervals from 10,000 bootstrap resamples of the 77 PDBs. "
            r"For a PDB containing $N$ target instances, relative budget $\rho$ allows $\lfloor\rho N\rfloor$ charged attempts. "
            r"Completion is the number of successful instances divided by $N$. Background candidates are charged, and out-of-scope foreground candidates are skipped. "
            r"Undetected and failed instances remain in the denominator.")
manifest = [{"stem": "direct", "id": "e2e-find-build-direct-comparison", "width": 180/25.4*72,
             "height": 118/25.4*72, "notes": notes_zh+"\nENGLISH:\n"+notes_en}]
(BUILD/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# 复用既有 SVG→原生形状转换，只转换外观几何，不再处理科学数值。
sys.path.insert(0, str(ROOT/"画图/画图代码/e2e/calculate/find-build-shared"))
from svg_shapes import SceneReader
reader = SceneReader(BUILD/"direct.svg")
reader.walk(reader.root, np.eye(3), {})
manifest[0]["shapes"] = reader.items
(BUILD/"scenes.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
print(f"24 bars; {len(source_rows)} PDB observations; {len(reader.items)} editable shapes")
