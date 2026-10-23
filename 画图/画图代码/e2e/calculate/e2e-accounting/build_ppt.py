"""保持原曲线图版式, 同步计费图注, 并单独制备原生可编辑流程草稿.

入口 main 读取 plot_data.json, 核对正文实际显示的全部整数计数与原曲线数据一致. 因此不重画曲线, 而是在原两份 E2E 曲线 PPT 内仅替换横轴文字和备注正文, 原生形状、字号、颜色、位置及页面大小保持.
产物为画图下的 E2E结果_全配体.pptx、E2E结果_小分子三联图.pptx、七页案例 v3 PPT, 以及单独的 E2E评价计费规则-草稿.pptx. 草稿不被论文引用. temp/e2e_accounting_20261004 保存 PowerPoint 原生 PNG/PDF 导出供验收.
"""

import os
import json
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
import win32com.client


ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').is_file() and (p / '论文草稿.md').is_file())
DATA = ROOT / "画图/画图代码/e2e/output/e2e-accounting"
TEMP = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else ROOT / "temp/e2e_accounting_20261004"
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "画图/画图代码/e2e/calculate/e2e-top-k-shared"))
import build_nature_figures as native


def update_curve(source, target, caption):
    """在原 PPT 内只更新横轴含义和 Word 图注, 不改变曲线形状.

    输入参数:
        - source: Path, 作者原曲线图的独立副本, 页面大小和全部可编辑原生形状均沿用.
        - target: Path, 作者指定的全配体或小分子曲线 PPT 路径.
        - caption: str, 中文完整图注, 写入 NotesPage 的正文占位符; 页码占位符不改.
    修改字段:
        - slide1.xml 的 a:t: 仅将 Ranked sites (K) 改为 Charged attempts (K), 原字体和位置保持.
        - notesSlide1.xml 的正文 p:txBody: 同步计费定义, 不改 NotesPage 中的页码或其他占位符.
    """
    with ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    slide = etree.fromstring(files["ppt/slides/slide1.xml"])
    for text in slide.findall(".//a:t", NS):
        if text.text == "Ranked sites (K)":
            text.text = "Charged attempts (K)"
    files["ppt/slides/slide1.xml"] = etree.tostring(slide, xml_declaration=True, encoding="UTF-8", standalone=True)
    notes = etree.fromstring(files["ppt/notesSlides/notesSlide1.xml"])
    for shape in notes.findall(".//p:sp", NS):
        placeholder = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
        if placeholder is not None and placeholder.get("type") == "body":
            body = shape.find("p:txBody", NS)
            paragraphs = body.findall("a:p", NS)
            paragraph = paragraphs[0]
            for child in list(paragraph):
                if child.tag != "{" + NS["a"] + "}pPr":
                    paragraph.remove(child)
            run = etree.SubElement(paragraph, "{" + NS["a"] + "}r")
            etree.SubElement(run, "{" + NS["a"] + "}t").text = caption
            for extra in paragraphs[1:]:
                body.remove(extra)
    files["ppt/notesSlides/notesSlide1.xml"] = etree.tostring(notes, xml_declaration=True, encoding="UTF-8", standalone=True)
    with ZipFile(target, "w", compression=8) as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def node(slide, text, rect, fill, decision):
    """画紧凑的原生流程节点, 决策用菱形, 行动用矩形.

    输入参数:
        - slide: PowerPoint Slide COM 对象, 整页 720×490 pt, 不进行成组缩放.
        - text: str, 节点行动或条件, 每行按节点宽度手动确定.
        - rect: tuple[float,float,float,float], 左、上、宽、高, 单位 pt.
        - fill: str, 六位 RGB 填色; 免费为浅金, 失败为浅灰, 成功为浅青绿.
        - decision: bool, True 使用菱形并居中判断条件, False 使用行动矩形.
    """
    shape = slide.Shapes.AddShape(4 if decision else 1, *rect)
    shape.Fill.ForeColor.RGB = native.office_rgb(fill)
    shape.Line.ForeColor.RGB = native.office_rgb("C9D3DA")
    shape.Line.Weight = 0.65
    frame = shape.TextFrame
    frame.MarginLeft = frame.MarginRight = 2
    frame.MarginTop = frame.MarginBottom = 1
    frame.VerticalAnchor = 3
    frame.WordWrap = True
    run = frame.TextRange
    run.Text = text
    run.Font.Name = "Arial"
    run.Font.Size = 9.0 if decision else 9.6
    run.Font.Color.RGB = native.office_rgb("ink")
    run.ParagraphFormat.Alignment = 2


def route(slide, points, label, label_rect):
    """按明确顶点连接流程节点, 最后一段带箭头, 可附 Yes/No 标签.

    输入参数:
        - points: list[tuple[float,float]], 顺序折线顶点, 坐标单位 pt, 不跨越节点正文.
        - label: str, 条件说明; 空字符串表示不添加旁注.
        - label_rect: tuple[float,float,float,float], 标签矩形; 空 label 时不读取.
    """
    for index, (start, end) in enumerate(zip(points, points[1:])):
        shape = slide.Shapes.AddLine(*start, *end)
        shape.Line.ForeColor.RGB = native.office_rgb("697782")
        shape.Line.Weight = 0.9
        if index == len(points) - 2:
            shape.Line.EndArrowheadStyle = 3
    if label:
        native.text_box(slide, label, *label_rect, size=8.6, color="muted", align=2)


def main(rules_only=False):
    """同步两张原曲线图、清理 v3 中本轮新增页, 导出单独的流程草稿.

    产物:
        - 两张原曲线 PPT: 仍为 519×252 pt 和 519×425 pt 的一页一图, 数据点和版式不重建.
        - E2E案例可视化-端到端流程版_v3.pptx: 原七页案例, 不包含本轮流程或曲线页; 仅将主图编号恢复为 12–14.
        - E2E评价计费规则-草稿.pptx: a 全配体、b Stage3 的可编辑计费草稿, 不插入论文.
        - temp 中的 curve_full/small 和 rules_draft PNG/PDF: 原生 PowerPoint 导出, 用于检查实际版面.
    """
    TEMP.mkdir(parents=True,exist_ok=True)
    data = json.loads((DATA / "plot_data.json").read_text(encoding="utf-8"))
    before = json.loads((ROOT / "画图/画图代码/e2e/output/e2e-top-k/data.json").read_text(encoding="utf-8"))
    # 当前绘制的所有曲线计数一致, 允许直接保留作者的原生曲线位置而不重新生成.
    assert data["full"] == before["full"]
    assert data["small_find"] == before["small_find"]
    assert data["small_match"] == before["small_match"]
    assert all(data["build"][domain]["local_cov-C"][field] == values for domain in ("GT", "CA2") for field, values in before["build"][domain]["local_cov-C"].items())
    captions = {
        "full": "图 10｜一般配体的区域检出与化学身份识别。179 个 PDB 中，前 K 次计费尝试至少有一个区域命中时计为 Find 成功；同时具有正确精确 SMILES 身份时计为 Find+Match 成功。Find 为假定后续 Match 完全正确时的定位诊断。纵轴为成功 PDB 比例，K=1–10。GT 与 CA2 分别使用真实受体与 CryoAtom2 受体及其对应模拟密度，两者共用实验密度；Emap2lig-Find 不使用受体，按自身冻结候选顺序进行相同定位诊断。",
        "small": "图 11｜单残基无缺失原子的有机小分子从位点检出到全原子构象重建。a，在 77 个 PDB 中，前 K 次计费尝试至少有一次区域检出或正确身份匹配时的 Find、Find+Match 成功率，以及不使用受体的 Emap2lig-Find 成功率。Find 与 Emap2lig-Find 均为假定后续 Match 完全正确时的定位诊断：背景计费，真实范围外前景免费跳过，合格小分子覆盖命中计费并记为定位成功；两者使用同一 77 个 PDB 分母、既定双向覆盖均 ≥0.3 的命中规则和各自冻结候选顺序。Find+Match 为假定后续 Build 完全正确时的诊断，按实际全身份 Match 的计费规则统计。b、c，分别在真实受体与 CryoAtom2 受体条件下，使用单次 PocketXMol-tuned 重建配体姿态，计费同 Find+Match。前 K 次计费尝试有任一成功姿态时，该 PDB 计为成功。实线为每个位点自评分首位姿态，虚线为该位点全部 50 个姿态中事后 RMSD 最低值；两种阈值均为严格 RMSD <2 Å 或 <3 Å。纵轴为成功 PDB 比例，K=1–10。GT 与 CA2 使用对应受体及模拟密度，实验密度相同。",
    }
    targets = {"full": TEMP / "E2E结果_全配体.pptx", "small": TEMP / "E2E结果_小分子三联图.pptx"}
    if not rules_only:
        for key, target in targets.items():
            update_curve(DATA / "sources" / ("all.before.pptx" if key == "full" else "small.before.pptx"), target, captions[key])

    app = win32com.client.Dispatch("PowerPoint.Application")
    if not rules_only:
        case_copy = TEMP / "cases.refined.pptx"
        shutil.copy2(ROOT / "画图/E2E案例可视化-端到端流程版_v3.pptx", case_copy)
        deck = app.Presentations.Open(str(case_copy), False, False, False)
        for index in range(deck.Slides.Count, 0, -1):
            slide = deck.Slides(index)
            tags = [comment.Text.strip() for comment in slide.Comments]
            if any(tag in ("@@e2e-accounting-rules", "@@e2e-all-find-match", "@@e2e-small-pipeline") for tag in tags):
                slide.Delete()
        # 补充案例也属于公开图集, 标题使用读者可理解的范围描述, 不暴露内部 Stage3 名称.
        for slide in deck.Slides:
            for shape in slide.Shapes:
                if shape.HasTextFrame and shape.TextFrame.HasText:
                    text = shape.TextFrame.TextRange.Text
                    revised = text.replace("Earlier foreground outside Stage3 scope, successful reconstruction at rank", "Earlier out-of-scope ligands; reconstruction at rank")
                    if revised != text:
                        shape.TextFrame.TextRange.Text = revised
        for index in range(1, 4):
            for shape in deck.Slides(index).NotesPage.Shapes:
                if shape.Type == 14 and shape.PlaceholderFormat.Type == 2:
                    text = shape.TextFrame.TextRange.Text
                    text = text.replace("图 " + str(index + 12) + "｜", "图 " + str(index + 11) + "｜")
                    shape.TextFrame.TextRange.Text = text
        deck.Save()
        deck.Close()
        shutil.copy2(case_copy, TEMP / "E2E案例可视化-端到端流程版_v3.pptx")

    deck = app.Presentations.Add(False)
    deck.PageSetup.SlideWidth, deck.PageSetup.SlideHeight = 720, 490
    slide = deck.Slides.Add(1, 12)
    native.text_box(slide, "a", 15, 10, 15, 17, size=13, bold=True)
    native.text_box(slide, "All ligands · detection and identity", 36, 11, 670, 17, size=11.4, bold=True)
    node(slide, "Next candidate", (27, 40, 88, 30), "EDF4F5", False)
    node(slide, "Ligand\nhit?", (142, 33, 94, 44), "FFFFFF", True)
    node(slide, "Match\nAll identities", (272, 40, 103, 30), "EEF0FA", False)
    node(slide, "Correct\nidentity?", (408, 33, 97, 44), "FFFFFF", True)
    node(slide, "+1 · PDB success", (565, 38, 131, 32), "E3F1EC", False)
    node(slide, "+1 · failure; next", (565, 90, 131, 29), "EFF2F4", False)
    route(slide, [(115, 55), (142, 55)], "", (0, 0, 0, 0))
    route(slide, [(236, 55), (272, 55)], "Yes", (239, 38, 30, 12))
    route(slide, [(375, 55), (408, 55)], "", (0, 0, 0, 0))
    route(slide, [(505, 55), (565, 55)], "Yes", (514, 38, 39, 12))
    route(slide, [(189, 77), (189, 104.5), (565, 104.5)], "No", (193, 80, 29, 12))
    route(slide, [(456.5, 77), (456.5, 104.5)], "No", (460, 80, 29, 12))
    native.line(slide, 15, 134, 705, 134, color="grid", weight=0.65)

    native.text_box(slide, "b", 15, 148, 15, 17, size=13, bold=True)
    native.text_box(slide, "Complete single-residue organic small molecules", 36, 149, 670, 17, size=11.4, bold=True)
    node(slide, "Next candidate", (27, 181, 88, 30), "EDF4F5", False)
    node(slide, "Ligand\nhit?", (142, 174, 94, 44), "FFFFFF", True)
    node(slide, "Match\nAll identities", (272, 181, 103, 30), "EEF0FA", False)
    node(slide, "Reference target class", (416, 181, 117, 30), "EDF4F5", False)
    node(slide, "+1 · failure; next", (142, 236, 104, 23), "EFF2F4", False)
    route(slide, [(115, 196), (142, 196)], "", (0, 0, 0, 0))
    route(slide, [(236, 196), (272, 196)], "Yes", (239, 180, 30, 12))
    route(slide, [(375, 196), (416, 196)], "", (0, 0, 0, 0))
    route(slide, [(189, 218), (189, 236)], "No", (193, 219, 29, 12))
    # Reference scope 是固定清单中的真实类别/资格, 与 Match 的预测身份分开.
    native.line(slide, 474.5, 211, 474.5, 268, color="muted", weight=0.9)
    native.line(slide, 124, 268, 599, 268, color="muted", weight=0.9)
    for center, label in ((124, "Non-small-molecule target"), (361, "Other small-molecule targets"), (599, "Complete single-residue\norganic small molecules")):
        route(slide, [(center, 268), (center, 280)], "", (0, 0, 0, 0))
        node(slide, label, (center - 97, 280, 194, 26), "EDF4F5", False)
    for x, text in ((77, "Predicted\nsmall?"), (314, "Correct\nidentity?"), (552, "Correct\nidentity?")):
        node(slide, text, (x, 326, 94, 44), "FFFFFF", True)
        route(slide, [(x + 47, 306), (x + 47, 326)], "", (0, 0, 0, 0))
    node(slide, "Free skip", (27, 399, 86, 28), "FCF1D9", False)
    node(slide, "+1; next", (136, 399, 85, 28), "EFF2F4", False)
    route(slide, [(100, 358), (70, 358), (70, 399)], "No", (74, 376, 25, 12))
    route(slide, [(147, 358), (178.5, 358), (178.5, 399)], "Yes", (184, 376, 29, 12))
    node(slide, "+1; next", (264, 399, 86, 28), "EFF2F4", False)
    node(slide, "Free skip", (374, 399, 84, 28), "FCF1D9", False)
    route(slide, [(337, 358), (307, 358), (307, 399)], "No", (313, 376, 25, 12))
    route(slide, [(384, 358), (416, 358), (416, 399)], "Yes", (423, 376, 29, 12))
    node(slide, "+1; next", (503, 399, 86, 28), "EFF2F4", False)
    node(slide, "Build", (612, 390, 86, 27), "EEF0FA", False)
    route(slide, [(575, 358), (546, 358), (546, 399)], "No", (552, 376, 25, 12))
    route(slide, [(622, 358), (655, 358), (655, 390)], "Yes", (662, 374, 29, 12))
    route(slide, [(655, 417), (655, 436)], "", (0, 0, 0, 0))
    node(slide, "Pose succeeds: +1 · PDB success\nOtherwise: +1 · failure; next", (503, 436, 195, 35), "E3F1EC", False)
    native.text_box(slide, "Free skip: continue without charging K. Stop at K charges or exhausted candidates.", 27, 478, 670, 12, size=8.5)
    slide.Comments.Add(5, 5, "Figure", "F", "@@e2e-accounting-rules-draft")
    for shape in slide.NotesPage.Shapes:
        if shape.Type == 14 and shape.PlaceholderFormat.Type == 2:
            shape.TextFrame.TextRange.Text = "草稿｜全配体与单残基无缺失原子的有机小分子端到端计费规则。Reference target class 为评价清单中的真实类别与合格小分子资格。Match 统一读取全身份 Top-1；真实非小分子预测为非小分子时即免费，即使身份错误。真实小分子匹配错误时计费，正确但不属于上述小分子范围时免费。合格小分子身份正确后执行 Build，输入/采样失败同姿态失败计费。背景计费。此页暂不进入论文。"
    draft = TEMP / "E2E评价计费规则-草稿.pptx"
    deck.SaveAs(str(draft), 24)
    slide.Export(str(TEMP / "rules_draft.png"), "PNG", 1800, 1225)
    deck.SaveAs(str(TEMP / "rules_draft.pdf"), 32)
    deck.Close()
    if not rules_only:
        for key, target in targets.items():
            copy = TEMP / (key + ".render.pptx")
            shutil.copy2(target, copy)
            deck = app.Presentations.Open(str(copy), False, False, False)
            deck.Slides(1).Export(str(TEMP / ("curve_" + key + ".png")), "PNG", 1557, 1275 if key == "small" else 756)
            deck.SaveAs(str(TEMP / ("curve_" + key + ".pdf")), 32)
            deck.Close()
    print("Original curve layout retained; cases: 7; separate rules draft: 1.")


if __name__ == "__main__":
    main("--rules-only" in sys.argv)
