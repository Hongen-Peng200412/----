"""把冻结的端到端逐 K 计数绘成两张正文用的可编辑 PowerPoint 图。

入口 ``main`` 读取同目录 ``data.json``，分别写出单页的全配体图和
小分子 a/b/c 三联图。曲线、标记、坐标轴、图例和文字均是 PowerPoint
原生形状；图名存于批注，中文图注存于备注，供 Markdown→Word 转换读取。
"""

from __future__ import annotations

import json
from pathlib import Path

import win32com.client


ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = Path(__file__).with_name("data.json")
OUTPUT_DIR = ROOT / "画图"
TEMP_DIR = ROOT / "temp"
FIGURE_WIDTH = 519.0  # 183 mm，双栏成品宽度。
COLORS = {
    "ink": "263746",
    "muted": "5D6974",
    "grid": "DFE5E8",
    "gt": "087E83",
    "ca2": "5363AE",
    "emap": "858D93",
    "two": "087E83",
    "three": "BC762A",
}


def office_rgb(value: str) -> int:
    """将六位 RGB 颜色转为 PowerPoint 使用的整数颜色值。"""
    value = COLORS.get(value, value)
    return int(value[0:2], 16) + 256 * int(value[2:4], 16) + 65536 * int(value[4:6], 16)


def text_box(slide, label: str, x: float, y: float, width: float, height: float,
             *, size: float = 8.0, color: str = "ink", bold: bool = False,
             align: int = 1):
    """在以 point 为单位的版面位置添加可编辑的单行文字。"""
    shape = slide.Shapes.AddTextbox(1, x, y, width, height)
    frame = shape.TextFrame
    frame.MarginLeft = frame.MarginRight = frame.MarginTop = frame.MarginBottom = 0
    frame.WordWrap = False
    run = frame.TextRange
    run.Text = label
    run.Font.Name = "Arial"
    run.Font.Size = size
    run.Font.Bold = -1 if bold else 0
    run.Font.Color.RGB = office_rgb(color)
    run.ParagraphFormat.Alignment = align
    return shape


def line(slide, x1: float, y1: float, x2: float, y2: float,
         *, color: str, weight: float = 1.2, dashed: bool = False) -> None:
    """添加一段可编辑线；虚线用于区分身份匹配或事后 best。"""
    shape = slide.Shapes.AddLine(x1, y1, x2, y2)
    shape.Line.ForeColor.RGB = office_rgb(color)
    shape.Line.Weight = weight
    if dashed:
        shape.Line.DashStyle = 4


def marker(slide, x: float, y: float, *, color: str, shape_kind: int) -> None:
    """以数据点为中心添加可编辑标记；形状区分同色的两条曲线。"""
    diameter = 3.5
    point = slide.Shapes.AddShape(shape_kind, x - diameter / 2, y - diameter / 2,
                                  diameter, diameter)
    point.Fill.ForeColor.RGB = office_rgb(color)
    point.Line.ForeColor.RGB = office_rgb("FFFFFF")
    point.Line.Weight = 0.35


def axes(slide, plot: tuple[float, float, float, float]) -> None:
    """绘制单面板 K=1–10、成功 PDB 比例 0–100% 的完整坐标轴。"""
    left, top, width, height = plot
    # 旋转后让文字处于页内，并与每个面板的纵轴中心对齐。
    ylabel = text_box(slide, "Success rate (%)", 0, top + height / 2 - 6,
                      95, 12, size=7.4, color="ink", align=2)
    ylabel.Rotation = 270
    for percentage in (0, 25, 50, 75, 100):
        y = top + height * (1 - percentage / 100)
        if percentage in (25, 50, 75):
            line(slide, left, y, left + width, y, color="grid", weight=0.55)
        text_box(slide, str(percentage), left - 29, y - 5, 23, 10,
                 size=7.0, color="muted", align=3)
    line(slide, left, top, left, top + height, color="ink", weight=0.8)
    line(slide, left, top + height, left + width, top + height,
         color="ink", weight=0.8)
    for index in range(10):
        x = left + index * width / 9
        line(slide, x, top + height, x, top + height + 2.5,
             color="ink", weight=0.6)
        if index in (0, 2, 4, 6, 9):
            text_box(slide, str(index + 1), x - 5, top + height + 4, 10, 10,
                     size=7.0, color="muted", align=2)
    text_box(slide, "Ranked sites (K)", left + width / 2 - 52,
             top + height + 17, 104, 11, size=7.4, align=2)


def curve(slide, counts: list[int], denominator: int,
          plot: tuple[float, float, float, float], *, color: str,
          dashed: bool, marker_kind: int) -> None:
    """将十个 PDB 成功数除以固定分母后映射到同一百分比坐标系。"""
    left, top, width, height = plot
    # (10, 2)：每行依次是 K=1…10 的幻灯片横纵坐标，纵轴 0–100%。
    points = [(left + index * width / 9,
               top + height * (1 - count / denominator))
              for index, count in enumerate(counts)]
    for start, end in zip(points, points[1:]):
        line(slide, *start, *end, color=color, weight=1.6, dashed=dashed)
    for x, y in points:
        marker(slide, x, y, color=color, shape_kind=marker_kind)


def legend(slide, items: list[tuple[str, str, bool, int, list[int]]],
           *, x: float, top: float, row_height: float) -> None:
    """在图右侧竖排各曲线的颜色、线型、标记与名称。"""
    for index, (label, color, dashed, marker_kind, _) in enumerate(items):
        y = top + index * row_height
        line(slide, x, y + 5, x + 20, y + 5,
             color=color, weight=1.6, dashed=dashed)
        marker(slide, x + 10, y + 5, color=color, shape_kind=marker_kind)
        text_box(slide, label, x + 27, y - 1, 102, 12, size=7.7)


def panel(slide, *, top: float, plot_height: float, denominator: int,
          items: list[tuple[str, str, bool, int, list[int]]],
          label: str = "", description: str = "") -> tuple[float, float, float, float]:
    """绘制一个面板并返回供版面对齐核查的绘图区矩形。

    ``items`` 每项依次为图例文字、颜色键、虚线标志、标记形状编号和
    (10,) 成功 PDB 计数；每项的第 k 个数对应排序前 k+1 个计费位点。
    """
    if label:
        text_box(slide, label, 9, top, 15, 14, size=10, bold=True)
        text_box(slide, description, 27, top + 1, 265, 12,
                 size=8.4, bold=True)
    plot_top = top + 27 if label else top + 24
    plot = (70.0, plot_top, 288.0, plot_height)
    axes(slide, plot)
    for _, color, dashed, marker_kind, counts in items:
        curve(slide, counts, denominator, plot,
              color=color, dashed=dashed, marker_kind=marker_kind)
    legend(slide, items, x=380, top=plot_top + 12,
           row_height=16.4 if len(items) == 5 else 17.4)
    return plot


def save_figure(application, *, name: str, filename: str, height: float,
                caption: str, source: str, draw) -> None:
    """将单页原生形状图、图名批注与中文备注保存为 PPTX、预览 PNG、PDF。

    正式 PPTX 写到 ``画图/filename``；PNG/PDF 只用于 ``temp/`` 版面验收。
    ``draw`` 在空白页绘制曲线，数据始终来自冻结的 ``data.json``。
    """
    deck = application.Presentations.Add()
    deck.PageSetup.SlideWidth = FIGURE_WIDTH
    deck.PageSetup.SlideHeight = height
    slide = deck.Slides.Add(1, 12)
    slide.Background.Fill.ForeColor.RGB = office_rgb("FFFFFF")
    draw(slide)
    slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = caption
    slide.Comments.Add(8, 8, "Manuscript figure", "MF", f"@@{name}")
    slide.Comments.Add(18, 18, "Frozen source", "FS", source)
    deck.SaveAs(str(OUTPUT_DIR / filename), 24)
    slide.Export(str(TEMP_DIR / f"{name}.png"), "PNG",
                 2400, round(2400 * height / FIGURE_WIDTH))
    deck.SaveAs(str(TEMP_DIR / f"{name}.pdf"), 32)
    deck.Close()


def main() -> None:
    """用冻结计数分别生成图 10 与图 11 的可编辑正文 PPT。"""
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    full = data["full"]
    small_find = data["small_find"]
    small_match = data["small_match"]
    full_items = [
        ("Find · GT", "gt", False, 9, full["real_stage1_only"]),
        ("Find+Match · GT", "gt", True, 1, full["real_stage1_matcher"]),
        ("Find · CA2", "ca2", False, 9, full["cryo_stage1_only"]),
        ("Find+Match · CA2", "ca2", True, 1, full["cryo_stage1_matcher"]),
        ("Emap2lig-Find", "emap", False, 4, full["emap2lig"]),
    ]
    small_items = [
        ("Find · GT", "gt", False, 9, small_find["real_receptor"]),
        ("Find+Match · GT", "gt", True, 1, small_match["real_receptor"]),
        ("Find · CA2", "ca2", False, 9, small_find["cryoatom2_receptor"]),
        ("Find+Match · CA2", "ca2", True, 1, small_match["cryoatom2_receptor"]),
        ("Emap2lig-Find", "emap", False, 4, small_find["emap2lig"]),
    ]

    def build_items(domain: str) -> list[tuple[str, str, bool, int, list[int]]]:
        """取单次 local_cov-C 的四条曲线，按阈值与姿态选择顺序排图例。"""
        counts = data["build"][domain]["local_cov-C"]
        return [
            ("Top-1 · <2 Å", "two", False, 9, counts["pose1_lt2"]),
            ("Top-1 · <3 Å", "three", False, 9, counts["pose1_lt3"]),
            ("Best-of-50 · <2 Å", "two", True, 1, counts["pose50_lt2"]),
            ("Best-of-50 · <3 Å", "three", True, 1, counts["pose50_lt3"]),
        ]

    def draw_full(slide) -> None:
        """绘制 179-PDB 的独立 Find/Find+Match 比较图。"""
        panel(slide, top=3, plot_height=193, denominator=179, items=full_items)

    def draw_small(slide) -> None:
        """以同一横纵轴尺度上下排列 77-PDB 的检出、GT 构象、CA2 构象。"""
        panel(slide, top=9, plot_height=79, denominator=77,
              items=small_items, label="a", description="Detection and identity")
        panel(slide, top=145, plot_height=79, denominator=77,
              items=build_items("GT"), label="b", description="Pose reconstruction · GT")
        panel(slide, top=281, plot_height=79, denominator=77,
              items=build_items("CA2"), label="c", description="Pose reconstruction · CA2")

    application = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        save_figure(
            application, name="e2e-all-find-match",
            filename="E2E结果_全配体.pptx", height=252,
            caption=("图 10｜一般配体的区域检出与化学身份识别。179 个 PDB 中，前 K 个排序"
                     "候选至少有一个区域命中时计为 Find 成功；同时具有正确精确 SMILES "
                     "身份时计为 Find+Match 成功。纵轴为成功 PDB 比例，K=1–10。"
                     "GT 与 CA2 分别使用真实受体与 CryoAtom2 受体及其对应模拟密度，"
                     "两者共用实验密度；Emap2lig-Find 不使用受体，按自身位点得分排序。"),
            source=data["provenance"]["full_matcher"], draw=draw_full,
        )
        save_figure(
            application, name="e2e-small-pipeline",
            filename="E2E结果_小分子三联图.pptx", height=425,
            caption=("图 11｜Stage3 小分子从位点检出到全原子构象重建。"
                     "a，在 77 个 PDB 中，前 K 个位点至少有一次区域检出或正确身份"
                     "匹配时的 Find、Find+Match 成功率，以及不使用受体的 "
                     "Emap2lig-Find 成功率；已知不适用于 Stage3 的前景位点不计入 K。"
                     "b、c，分别在真实受体与 CryoAtom2 受体条件下，使用单次 "
                     "local_cov-C 重建配体姿态。前 K 个计费位点有任一成功姿态时，"
                     "该 PDB 计为成功。实线为每个位点自评分首位姿态，虚线为该位点"
                     "全部 50 个姿态中事后 RMSD 最低值；两种阈值均为严格 "
                     "RMSD <2 Å 或 <3 Å。纵轴为成功 PDB 比例，K=1–10。"
                     "GT 与 CA2 分别使用真实受体与 CryoAtom2 受体及其对应模拟密度，"
                     "实验密度相同。"),
            source=(f"{data['provenance']['small_matcher']}；"
                    f"{data['provenance']['pocket_root']}/GT、CA2/docking_results.jsonl"),
            draw=draw_small,
        )
    finally:
        application.Quit()


if __name__ == "__main__":
    main()
