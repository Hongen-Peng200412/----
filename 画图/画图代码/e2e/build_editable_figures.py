"""用冻结的逐位点计数生成六页可编辑 PowerPoint 端到端结果图。

前四页供正文引用，后两页仅展示迭代策略。所有数据线、点、坐标轴、
网格线和文字均为 PowerPoint 原生对象，图注写入幻灯片备注。
"""

from __future__ import annotations

import json
from pathlib import Path

import win32com.client


ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).with_name("data.json")
OUTPUT = ROOT / "画图/E2E结果图_可编辑.pptx"
SLIDE_W = 960.0
SLIDE_H = 540.0
COLOR = {
    "ink": "263746",
    "muted": "647483",
    "grid": "E3E8EB",
    "gt": "087E83",
    "ca2": "5A67AC",
    "emap": "90979D",
    "two": "087E83",
    "three": "C27A2C",
}


def rgb(hex_value: str) -> int:
    """把六位 RGB 色值转换为 Office 使用的 BGR 整数。"""
    red = int(hex_value[0:2], 16)
    green = int(hex_value[2:4], 16)
    blue = int(hex_value[4:6], 16)
    return red + 256 * green + 65536 * blue


def add_text(slide, content: str, x: float, y: float, w: float, h: float,
             *, size: float = 12, color: str = "ink", bold: bool = False,
             align: int = 1):
    """添加无边框文本框，尺寸及位置均为 PowerPoint point。"""
    shape = slide.Shapes.AddTextbox(1, x, y, w, h)
    shape.TextFrame.MarginLeft = 0
    shape.TextFrame.MarginRight = 0
    shape.TextFrame.MarginTop = 0
    shape.TextFrame.MarginBottom = 0
    shape.TextFrame.WordWrap = False
    run = shape.TextFrame.TextRange
    run.Text = content
    run.Font.Name = "Arial"
    run.Font.Size = size
    run.Font.Bold = -1 if bold else 0
    run.Font.Color.RGB = rgb(COLOR.get(color, color))
    run.ParagraphFormat.Alignment = align
    return shape


def add_line(slide, x1: float, y1: float, x2: float, y2: float,
             *, color: str, width: float = 1.2, dashed: bool = False):
    """添加可编辑线段；折线由相邻数据点间的独立线段组成。"""
    shape = slide.Shapes.AddLine(x1, y1, x2, y2)
    shape.Line.ForeColor.RGB = rgb(COLOR.get(color, color))
    shape.Line.Weight = width
    if dashed:
        shape.Line.DashStyle = 4
    return shape


def add_marker(slide, x: float, y: float, *, color: str):
    """在数据坐标中心放置独立圆点，便于在 PPT 中调整。"""
    diameter = 6.0
    shape = slide.Shapes.AddShape(9, x - diameter / 2, y - diameter / 2,
                                  diameter, diameter)
    shape.Fill.ForeColor.RGB = rgb(COLOR.get(color, color))
    shape.Line.ForeColor.RGB = rgb("FFFFFF")
    shape.Line.Weight = 0.7
    return shape


def draw_series(slide, values: list[int], denominator: int, *, color: str,
                dashed: bool, plot: tuple[float, float, float, float]):
    """把 K=1…10 的 PDB 命中数按同一百分比坐标系画成原生折线。"""
    left, top, width, height = plot
    points = [
        (left + index * width / 9, top + height * (1 - count / denominator))
        for index, count in enumerate(values)
    ]
    for start, end in zip(points, points[1:]):
        add_line(slide, *start, *end, color=color, width=2.6, dashed=dashed)
    for x, y in points:
        add_marker(slide, x, y, color=color)


def draw_axes(slide, plot: tuple[float, float, float, float]):
    """绘制 0–100% 纵轴与每个整数 K 的刻度，四张正文图共用尺度。"""
    left, top, width, height = plot
    for percentage in (0, 20, 40, 60, 80, 100):
        y = top + height * (1 - percentage / 100)
        add_line(slide, left, y, left + width, y, color="grid", width=0.9)
        add_text(slide, str(percentage), left - 41, y - 8, 32, 17,
                 size=10, color="muted", align=3)
    add_line(slide, left, top, left, top + height, color="ink", width=1.2)
    add_line(slide, left, top + height, left + width, top + height,
             color="ink", width=1.2)
    for index in range(10):
        x = left + index * width / 9
        add_text(slide, str(index + 1), x - 8, top + height + 11, 16, 18,
                 size=10, color="muted", align=2)
    add_text(slide, "Ranked site K", left + width / 2 - 70,
             top + height + 40, 140, 20, size=12, color="ink", align=2)
    add_text(slide, "PDB success rate (%)", left, top - 24, 220, 20,
             size=11, color="muted")


def draw_legend(slide, items: list[tuple[str, str, bool]], y: float):
    """绘制两行紧凑图例，颜色表征输入域或阈值，线型表征评价阶段。"""
    for index, (label, color, dashed) in enumerate(items):
        row, col = divmod(index, 3)
        x = 86 + col * 282
        yy = y + row * 26
        add_line(slide, x, yy + 8, x + 27, yy + 8,
                 color=color, width=2.6, dashed=dashed)
        add_marker(slide, x + 13.5, yy + 8, color=color)
        add_text(slide, label, x + 38, yy, 235, 21, size=11, color="ink")


def make_chart(deck, *, name: str, title: str, subtitle: str,
               items: list[tuple[str, str, bool, list[int]]],
               denominator: int, caption: str, provenance: str):
    """新增一页单轴曲线图，并写入 Word 转换所需的图名批注与图注备注。"""
    slide = deck.Slides.Add(deck.Slides.Count + 1, 12)
    slide.Background.Fill.ForeColor.RGB = rgb("FFFFFF")
    add_text(slide, title, 80, 30, 805, 34, size=23, bold=True)
    add_text(slide, subtitle, 80, 69, 805, 23, size=12, color="muted")
    draw_legend(slide, [(label, color, dashed) for label, color, dashed, _ in items], 108)
    plot = (91.0, 181.0, 777.0, 272.0)
    draw_axes(slide, plot)
    for _, color, dashed, values in items:
        assert len(values) == 10
        draw_series(slide, values, denominator, color=color, dashed=dashed, plot=plot)
    slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = caption
    slide.Comments.Add(8, 8, "Manuscript figure", "MF", f"@@{name}")
    slide.Comments.Add(18, 18, "Source data", "SD", provenance)
    return slide


def main() -> None:
    """从冻结计数创建四页正文图和两页未引用的迭代策略图。"""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    application = win32com.client.DispatchEx("PowerPoint.Application")
    deck = application.Presentations.Add()
    deck.PageSetup.SlideWidth = SLIDE_W
    deck.PageSetup.SlideHeight = SLIDE_H
    try:
        full = data["full"]
        make_chart(
            deck, name="e2e-all-find-match",
            title="From ligand detection to identity assignment",
            subtitle="All ligand classes · 179 PDBs · top-K ranked sites",
            items=[
                ("Find · GT", "gt", False, full["real_stage1_only"]),
                ("Find+Match · GT", "gt", True, full["real_stage1_matcher"]),
                ("Find · CryoAtom2", "ca2", False, full["cryo_stage1_only"]),
                ("Find+Match · CryoAtom2", "ca2", True, full["cryo_stage1_matcher"]),
                ("Emap2lig-Find", "emap", False, full["emap2lig"]),
            ], denominator=179,
            caption=("完整配体测试集的区域检出与身份匹配。179 个 PDB 的前 K 个排序候选中，"
                     "至少一个候选覆盖真实配体时记为 Find 成功；Find+Match 还要求该候选的"
                     "精确 SMILES 身份正确。Find 候选按源概率均值排序。GT 与 CryoAtom2"
                     "分别表示真实受体及其模拟密度、重建受体及其模拟密度，"
                     "两者共用实验密度；受体无关的 Emap2lig-Find 按自身概率排序。"
                     "纵轴为成功 PDB 比例，K=1–10。"),
            provenance=data["provenance"]["full_matcher"],
        )
        small_find = data["small_find"]
        small_match = data["small_match"]
        make_chart(
            deck, name="e2e-small-find-match",
            title="Detection and identity assignment for Stage3 ligands",
            subtitle="Single-residue carbon-containing ligands · 77 PDBs · top-K ranked sites",
            items=[
                ("Find · GT", "gt", False, small_find["real_receptor"]),
                ("Find+Match · GT", "gt", True, small_match["real_receptor"]),
                ("Find · CryoAtom2", "ca2", False, small_find["cryoatom2_receptor"]),
                ("Find+Match · CryoAtom2", "ca2", True, small_match["cryoatom2_receptor"]),
                ("Emap2lig-Find", "emap", False, small_find["emap2lig"]),
            ], denominator=77,
            caption=("Stage3 合格小分子的区域检出与身份匹配。77 个 PDB 含 446 个合格"
                     "配体实例。前 K 个计费候选中至少一个区域命中时记为 Find 成功；"
                     "Find+Match 还要求精确 SMILES 身份正确。计费时跳过已知不适用"
                     "Stage3 的前景候选。纵轴为成功 PDB 比例，K=1–10；Emap2lig-Find"
                     "使用自身排序且不读取受体；GT 和 CryoAtom2 分别使用真实受体"
                     "及其模拟密度、重建受体及其模拟密度，实验密度相同。"),
            provenance=data["provenance"]["small_matcher"],
        )
        for condition, name, title, subtitle, method in (
            ("GT", "e2e-build-c-gt", "Pose reconstruction from ranked sites",
             "GT receptor · local_cov single C · 77 PDBs", "local_cov-C"),
            ("CA2", "e2e-build-c-ca2", "Pose reconstruction from ranked sites",
             "CryoAtom2 receptor · local_cov single C · 77 PDBs", "local_cov-C"),
            ("CA2", "e2e-build-cc-ca2", "Iterative pose reconstruction: C→C",
             "CryoAtom2 receptor · 77 PDBs · additional figure", "C-C"),
            ("CA2", "e2e-build-cce-ca2", "Iterative pose reconstruction: C→C→E",
             "CryoAtom2 receptor · 77 PDBs · additional figure", "C-C-E"),
        ):
            curves = data["build"][condition][method]
            items = [
                ("Top-1 · <2 Å", "two", False, curves["pose1_lt2"]),
                ("Top-1 · <3 Å", "three", False, curves["pose1_lt3"]),
                ("Best-of-50 · <2 Å", "two", True, curves["pose50_lt2"]),
                ("Best-of-50 · <3 Å", "three", True, curves["pose50_lt3"]),
            ]
            input_domain = ("真实受体与其模拟密度" if condition == "GT"
                            else "CryoAtom2 受体与其模拟密度")
            iteration = {
                "local_cov-C": "单次中心模型",
                "C-C": "两次中心模型",
                "C-C-E": "两次中心模型后接包络模型",
            }[method]
            caption = (
                f"{input_domain}及实验密度条件下，{iteration}的小分子端到端构象重建。"
                "77 个 PDB 中，前 K 个计费位点只要有一个姿态的重原子 RMSD "
                "严格小于 2 Å 或 3 Å，该 PDB 即记为成功。实线为各位点自评分首位姿态；"
                "虚线为各位点 50 个姿态中的事后最低 RMSD。K=1–10。"
            )
            make_chart(
                deck, name=name, title=title, subtitle=subtitle,
                items=items, denominator=77, caption=caption,
                provenance=(f"{data['provenance']['pocket_root']}/{condition}/"
                            "docking_results.jsonl"),
            )
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        deck.SaveAs(str(OUTPUT), 24)
        for index, slide in enumerate(deck.Slides, 1):
            slide.Export(str(ROOT / f"temp/e2e-slide-{index}.png"), "PNG", 1920, 1080)
        deck.SaveAs(str(ROOT / "temp/e2e-figures.pdf"), 32)
    finally:
        deck.Close()
        application.Quit()
    print(OUTPUT)


if __name__ == "__main__":
    main()
