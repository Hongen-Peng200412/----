"""将冻结的实例完成度绘制为十个单面板和两个汇总图.

运行入口为 main; 图稿、布局验收与装配清单均保存在仓库 temp/e2e_completion_20261011/.
本脚本只读取 completion.json, 不执行模型推理、姿态排序或科学指标重算.
"""

import os
import hashlib
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
BUILD = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/e2e_completion_20261011"
DATA = ROOT / "画图/画图代码/e2e/output/e2e-instance-completion/completion.json"
COLORS = {"GT": "#00878B", "CA2": "#596BC0"}
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
        # 哈希产生可复现的纯横向抖动; 相同 PDB 在所有条件保持相同偏移, y 不变.
        jitter = np.array([(int(hashlib.sha256(row["pdb_id"].encode()).hexdigest()[:8], 16) / (2**32 - 1) - 0.5) * 19 for row in records])
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


def save_figure(fig, stem, figure_id, caption_zh, caption_en, manifest):
    """验收最终坐标轴对齐并导出同源矢量、预览和 PPT 装配元数据.

    输入参数:
        - fig: Matplotlib Figure, 已包含最终文字与图形布局.
        - stem、figure_id: str, 临时文件前缀及 PPT 唯一 @@ 标识.
        - caption_zh、caption_en: str, 不含手工图号的中英文图注.
        - manifest: list[dict], 按 PPT 页序追加图的物理尺寸、标题和图注.
    返回值:
        - 无. 写入 SVG、PDF、PNG 与多面板布局报告, 并关闭该 Figure.
    """
    fig.canvas.draw()
    if len(fig.axes) > 1:
        require_matplotlib_panel_alignment(fig, json_out=BUILD / f"{stem}.alignment.json", overlay_svg=BUILD / f"{stem}.alignment.svg", tolerance_pt=1.5)
    fig.savefig(BUILD / f"{stem}.svg", facecolor="white")
    fig.savefig(BUILD / f"{stem}.pdf", facecolor="white")
    fig.savefig(BUILD / f"{stem}.png", dpi=600, facecolor="white")
    manifest.append({"stem": stem, "id": figure_id, "width": float(fig.get_figwidth() * 72), "height": float(fig.get_figheight() * 72), "notes": caption_zh + "\nENGLISH:\n" + caption_en})
    plt.close(fig)


def make_figure(panels, rows, columns, title, stem, figure_id, captions, manifest):
    """用统一的实体尺寸和网格排布可比较面板.

    输入参数:
        - panels: list[dict], 按行优先的科学面板; 不依赖数据 JSON 的内部顺序.
        - rows、columns: int, 分别为 1×1、1×2 或 4×2 布局.
        - title: str, 图的公开总标题.
        - stem、figure_id、captions、manifest: 导出标识、中英文图注和装配清单.
    返回值:
        - 无. 经 save_figure 保存一张独立图稿.
    """
    compact = columns == 2
    height_mm = 150 if rows == 4 else 92
    fig = plt.figure(figsize=(7.0866141732, height_mm / 25.4))  # 180 mm 宽, 以英寸传入 Matplotlib.
    grid = fig.add_gridspec(rows, columns, left=0.10, right=0.975, bottom=0.09 if rows == 4 else 0.16, top=0.88 if rows == 4 else 0.78, wspace=0.24, hspace=0.42)
    for index, panel in enumerate(panels):
        ax = fig.add_subplot(grid[index // columns, index % columns])
        criterion = "Find+Match" if panel["scope"] == "full" else f"{'Top-1' if panel['pose_limit'] == 1 else 'Best-of-50'} · RMSD <{int(panel['threshold_A'])} Å"
        label = f"{criterion} · {panel['domain']}" if rows == 4 or not compact else panel["domain"]
        draw_panel(ax, panel, label, chr(97 + index) if compact else "", compact)
        if index % columns == 0:
            ax.set_ylabel("Completion (%)" if rows == 4 else "Ligand completion (%)", fontsize=8)
        if index // columns == rows - 1:
            ax.set_xlabel("Relative attempt budget (%)", fontsize=8, labelpad=6)
        elif rows > 1:
            # 汇总页各行共用同一预算刻度; 仅底行显示数值, 为上一行与下一行标题留出空间.
            ax.tick_params(axis="x", labelbottom=False)
    handles = [Line2D([], [], color=MEAN_COLOR, linewidth=1.8, marker="o", markersize=3.4, markerfacecolor=MEAN_COLOR, markeredgecolor="white", markeredgewidth=0.35, label="Mean"), Line2D([], [], color=MEDIAN_COLOR, linewidth=1.05, marker="D", markersize=4.0, markerfacecolor="none", markeredgecolor=MEDIAN_COLOR, markeredgewidth=0.9, label="Median"), Line2D([], [], color="#7F8C97", marker="o", linestyle="none", markersize=3, label="Individual PDB")]
    # 图例占独立的顶部空间, 不遮盖数据; 线色标识统计量, GT/CA2 由面板标题指示.
    fig.text(0.10, 0.98 if rows == 4 else 0.97, title, fontsize=10.5, weight="bold", va="top")
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.09, 0.95 if rows == 4 else 0.91), ncol=3, frameon=False, handlelength=2.2, columnspacing=1.8, fontsize=7.5)
    save_figure(fig, stem, figure_id, *captions, manifest)


def main(figure_id=None):
    """按既定顺序生成12页图稿；指定稳定图名时只生成该图。

    输入文件:
        - completion.json: panels 包含完整 PDB 分布和精确事件曲线.
    输出文件:
        - 本 temp 目录中的 12 组 SVG/PDF/PNG、两份 alignment JSON/SVG 和 manifest.json.
    """
    BUILD.mkdir(parents=True, exist_ok=True)
    panels = {panel["id"]: panel for panel in json.loads(DATA.read_text(encoding="utf-8"))["panels"]}
    order = ["full_GT", "full_CA2"] + [f"small_{domain}_pose{pose}_rmsd{threshold}" for pose, threshold in ((1, 2), (1, 3), (50, 2), (50, 3)) for domain in ("GT", "CA2")]
    base_zh = "相对尝试预算 ρ 允许每个 PDB 计费 floor(ρN) 次; N 包含该 PDB 的全部合格实例. 完成度为成功的不同实例数除以 N. 绿线与圆点、蓝线与菱形分别为 PDB 等权均值和中位数; 灰点与小提琴展示 50%、100%、200% 和 300% 预算下的 PDB 分布. "
    base_en = "Budget ρ allows floor(ρN) charged attempts, where N includes all eligible instances per PDB. Completion counts distinct successful instances divided by N. Green lines/circles and blue lines/diamonds show the PDB-equal mean and median, respectively. Grey points and violins show PDB distributions at 50%, 100%, 200% and 300% budgets. "
    manifest = []
    for number, panel_id in enumerate(order, 1):
        single_id = "supp-completion-" + panel_id.lower().replace("_", "-")
        if figure_id is not None and figure_id != single_id:
            continue
        panel = panels[panel_id]
        scope = "Detection and identity" if panel["scope"] == "full" else "Small-molecule reconstruction"
        if panel["scope"] == "full":
            captions = (f"{panel['domain']} 条件的全配体定位与身份匹配实例完成度, 包含 179 个 PDB、2,502 个实例. " + base_zh, f"Ligand-instance completion for detection and identity matching under {panel['domain']}, including 179 PDBs and 2,502 instances. " + base_en.replace("successfully reconstructed", "correctly detected and identified"))
        else:
            captions = (f"{panel['domain']} 条件的单残基无缺失原子的有机小分子实例完成度, 包含 77 个 PDB、446 个实例, {'top-1' if panel['pose_limit'] == 1 else 'best-of-50'} 严格 RMSD <{int(panel['threshold_A'])} Å. " + base_zh, f"Instance completion of single-residue organic small molecules with no missing atoms under {panel['domain']}, including 77 PDBs and 446 instances; {'top-1' if panel['pose_limit'] == 1 else 'best-of-50'}, strict RMSD <{int(panel['threshold_A'])} Å. " + base_en)
        make_figure([panel], 1, 1, scope, f"{number:02d}_{panel_id}", "supp-completion-" + panel_id.lower().replace("_", "-"), captions, manifest)
    all_zh = "全配体定位与身份匹配的实例完成度. a, 沉积受体 (GT). b, CryoAtom2 重建受体 (CA2). 两个条件均包含 179 个 PDB、2,502 个配体实例. Find 与 Match 分别为 LigandSeek 的区域检出与身份匹配阶段. " + base_zh + "全配体的每个候选均消耗一次尝试, 沿用冻结的候选顺序与全身份 Top-1 Match 判定. 300% 为本图预算截点, 不是候选尝试上限."
    all_en = "Ligand-instance completion for detection and identity matching. a, Deposited receptors (GT). b, CryoAtom2-reconstructed receptors (CA2). Both conditions include 179 PDBs and 2,502 ligand instances. Find and Match are the region-detection and identity-matching stages of LigandSeek. " + base_en.replace("successfully reconstructed", "correctly detected and identified") + "Every candidate consumes one attempt, using the frozen candidate order and full-identity Top-1 Match predictions. The 300% endpoint is a plotting cutoff, not a limit on candidate attempts."
    if figure_id is None or figure_id == "supp-e2e-completion-all":
        make_figure([panels["full_GT"], panels["full_CA2"]], 1, 2, "Completion of ligand detection and identity matching", "11_all", "supp-e2e-completion-all", (all_zh, all_en), manifest)
    small_zh = "单残基无缺失原子的有机小分子端到端实例完成度. 左列为沉积受体 (GT), 右列为 CryoAtom2 重建受体 (CA2). a,b, self-ranking 首选构象的重原子均方根偏差 (RMSD) 严格 <2 Å; c,d, <3 Å; e–h, best-of-50 在对应阈值下的结果. LigandSeek Find–Match–Build 结果含 77 个 PDB、446 个实例, Build 采用 PocketXMol-tuned 单次对接. 每个 PDB 含 N 个合格实例, 预算 ρ 允许 floor(ρN) 次计费尝试, 完成度为成功的不同实例数/N. 绿线与圆点、蓝线与菱形分别为 PDB 等权均值和中位数; 灰点与小提琴为 50%、100%、200%、300% 预算下的分布. 沿用冻结顺序与 Match 感知免费跳过. Best-of-50 仅按最低 RMSD 评价."
    small_en = "End-to-end completion of single-residue organic small molecules with no missing atoms. GT, deposited receptors (left); CA2, CryoAtom2-reconstructed receptors (right). a,b, Self-ranked top-1 heavy-atom root-mean-square deviation (RMSD) <2 Å; c,d, <3 Å; e–h, best-of-50 at corresponding strict thresholds. LigandSeek Find–Match–Build results comprise 77 PDBs and 446 instances with single-pass PocketXMol-tuned docking. For N eligible instances per PDB, budget ρ allows floor(ρN) charged attempts; completion is distinct successes/N. Green lines/circles and blue lines/diamonds indicate PDB-equal mean and median; grey points and violins show distributions at 50%, 100%, 200% and 300%. Frozen ordering and Match-aware free skips apply. Best-of-50 uses lowest-RMSD poses only for evaluation."
    if figure_id is None or figure_id == "supp-e2e-completion-small":
        make_figure([panels[key] for key in order[2:]], 4, 2, "Completion of end-to-end small-molecule reconstruction", "12_small", "supp-e2e-completion-small", (small_zh, small_en), manifest)
    (BUILD / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(manifest)} editable-source figures")


if __name__ == "__main__":
    main()
