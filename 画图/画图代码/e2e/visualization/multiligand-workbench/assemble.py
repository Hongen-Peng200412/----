"""组合 ChimeraX 已导出的原生图片, 写候选主图、九例比较页和供可编辑 PPT 使用的布局.

仅对整张原生导图等比缩放与排列, 不改原子、密度、颜色或对比度. 输入为本轮 data-root 的
scene.json、view_index.json 和 exports/*.png; 输出全部写显式 build-root, 不读取旧 temp.
图像宽180 mm, 正文标签保持可编辑 PDF 文字. 统计直接引用冻结评价, 局部 RMSD 连接原 SDF.
"""

import argparse
import json
import string
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.insert(0, str(Path.home() / ".codex/skills/nature-figure/scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment


def captions(pdb, scene, local_rows):
    """按同一数据给九个病例页写双语图注. 无合法流水线构象时明确对应局部只含参考."""
    counts = scene["counts"]
    sites = []
    for domain, row in local_rows:
        occurrence = next(
            o for o in scene["occurrences"] if o["candidate_id"] == row["occurrence_id"]
        )
        sites.append(
            f"{domain}: {occurrence['display_name']} ({occurrence['site']}), "
            + (f"top-1 RMSD {row['rmsd_A']:.2f} Å" if row["prediction_model"] else "reference only")
        )
    en = (
        f"Multi-ligand recognition and modelling in {pdb.upper()}. "
        f"The complex contains {counts['all']} deposited ligand instances, including {counts['small']} small molecules "
        f"and {counts['eligible']} single-residue, complete organic small molecules eligible for modelling. "
        "Left and right columns use the CryoAtom2-reconstructed (CA2) and deposited (GT) receptor structures, respectively. "
        "a,b, LigandSeek-Find candidate ligand regions with LigandSeek-Match assignments. Teal denotes a correct identity "
        "at a foreground region, and brown denotes other candidates. Orange shows deposited ligands. "
        "c,d, Top-1 poses from the complete LigandSeek Find–Match–Build pipeline using PocketXMol-tuned. "
        "Teal and brown poses have heavy-atom root-mean-square deviation (RMSD) below and at least 2 Å, respectively. "
        "The labels give completed/target instance counts at 100% attempt budget. The budget equals the number of all "
        "ligand instances in a,b and eligible small-molecule instances in c,d. e,f, Selected local views with experimental "
        "density (grey mesh), receptor residues within 5 Å, deposited poses (orange) and available pipeline top-1 poses (teal). "
        + "; ".join(sites)
        + ". Local views use the same pipeline budgets. Overview scales differ between complexes."
    )
    zh = (
        f"{pdb.upper()}中的多配体识别与建模。复合物含{counts['all']}个沉积配体实例，其中小分子{counts['small']}个，"
        f"满足单残基、无缺失原子、有机条件的建模实例{counts['eligible']}个。左、右列分别采用CryoAtom2重建受体（CA2）和沉积受体（GT）。"
        "a、b，LigandSeek-Find候选配体区域及LigandSeek-Match身份匹配。青绿色表示前景区域中的身份匹配正确，棕色表示其他候选，橙色为沉积配体。"
        "c、d，采用PocketXMol-tuned的LigandSeek Find–Match–Build完整流水线首选构象。青绿色和棕色构象的重原子RMSD分别低于和不低于2 Å。"
        "标签列出100%尝试预算下的完成实例数/目标实例数；a、b以全配体实例数为预算基数，c、d以合格小分子实例数为基数。"
        "e、f，局部实验密度（灰色网格）、5 Å内的受体残基、沉积构象（橙色）和已有完整流水线首选构象（青绿色）。"
        + "；".join(sites)
        .replace("reference only", "仅参考构象")
        .replace("top-1 RMSD", "首选构象RMSD")
        + "。局部沿用相同完整流水线预算。不同复合物总览的显示比例不同。"
    )
    return en, zh


# ================================================================================================
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
parser.add_argument("--build-root", type=Path, required=True)
parser.add_argument("--figure", default="all", help="稳定图名; all 生成主图与九例比较页")
args = parser.parse_args()
build = args.build_root.resolve()
build.mkdir(parents=True, exist_ok=True)
width, height = 1280, 1600
pt_per_px = (180 / 25.4 * 72) / width
plt.rcParams.update(
    {"font.family": "Arial", "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"}
)
view_index = json.loads((args.data_root / "view_index.json").read_text(encoding="utf-8"))
by_view = {(r["pdb"], r["view"]): r for r in view_index}
case_ids = ["11jb", "9bjj", "9lov", "9okp", "30ga", "9ujf", "9wup", "9lw1", "9llg"]
if args.figure == "multiligand-workbench":
    case_ids = ["11jb", "9bjj", "9lov"]
elif args.figure != "all":
    case_ids = [args.figure.removeprefix("multiligand-workbench-")]
scenes = {
    p: json.loads((args.data_root / p / "scene.json").read_text(encoding="utf-8")) for p in case_ids
}
pages = []
main_panels = []
for pdb, oid in [("11jb", 16), ("9bjj", 16), ("9lov", 3)]:
    if pdb not in scenes:
        continue
    scene = scenes[pdb]
    evaluation = scene["domains"]["CA2"]["expected"]
    row = by_view[(pdb, f"CA2_local_{oid}")]
    occurrence = next(o for o in scene["occurrences"] if o["candidate_id"] == oid)
    assert row["prediction_model"] is not None
    main_panels.extend(
        [
            {
                "pdb": pdb,
                "view": "CA2_find_match",
                "heading": f"{pdb.upper()}   Find+Match {evaluation['find_match']['100']['success_count']}/{scene['counts']['all']}",
            },
            {
                "pdb": pdb,
                "view": f"CA2_local_{oid}",
                "heading": f"{occurrence['display_name']} ({occurrence['site']})   RMSD {row['rmsd_A']:.2f} Å",
            },
        ]
    )
main_en = (
    "Multi-ligand recognition and modelling by LigandSeek. a,c,e, LigandSeek-Find candidate ligand regions "
    "with LigandSeek-Match identity assignments in 11JB, 9BJJ and 9LOV, respectively, using CryoAtom2-reconstructed "
    "receptors. Teal denotes a correct identity at a foreground region, brown denotes other candidates and orange "
    "shows deposited ligands. The labels give completed/target instance counts at 100% attempt budget, with the attempt limit "
    "equal to the number of deposited ligand instances. b,d,f, Selected top-1 poses from the complete Find–Match–Build pipeline "
    "using PocketXMol-tuned (teal), overlaid with deposited poses (orange), experimental cryo-EM density (grey mesh) "
    "and receptor residues within 5 Å. Local panels use 100% budget relative to the number of single-residue, complete "
    "organic small molecules. At this budget, top-1 poses below 2 Å heavy-atom root-mean-square deviation (RMSD) complete 76/78, 10/11 and 3/3 "
    "eligible instances in the three complexes, respectively. The local panels show AR6 (f:2001), A1AP0 (E:1001) "
    "and ADP (B:1101). Overview scales differ between complexes."
)
main_zh = (
    "LigandSeek的多配体识别与建模。a、c、e，采用CryoAtom2重建受体，分别展示11JB、9BJJ、9LOV中的LigandSeek-Find候选配体区域及LigandSeek-Match身份匹配。"
    "青绿色表示前景区域的身份匹配正确，棕色表示其他候选，橙色为沉积配体。标签给出100%尝试预算下完成实例数/目标实例数，预算基数为全部沉积配体实例数。"
    "b、d、f，采用PocketXMol-tuned的完整Find–Match–Build流水线首选构象（青绿色）、沉积构象（橙色）、实验冷冻电镜密度（灰色网格）及5 Å内的受体残基。"
    "局部图以单残基、无缺失原子、有机的小分子实例数定义100%预算。在该预算下，三个复合物中重原子RMSD低于2 Å的首选构象分别完成76/78、10/11、3/3个合格实例。"
    "局部分别展示AR6（f:2001）、A1AP0（E:1001）及ADP（B:1101）。不同复合物总览的显示比例不同。"
)
if args.figure in ["all", "multiligand-workbench"]:
    pages.append(
        {
            "id": "multiligand-workbench",
            "title": "Multi-ligand recognition and modelling",
            "subtitle": "CryoAtom2 receptor, 100% attempt budgets",
            "panels": main_panels,
            "caption_en": main_en,
            "caption_zh": main_zh,
        }
    )
for pdb in [] if args.figure == "multiligand-workbench" else case_ids:
    scene = scenes[pdb]
    oid = scene["local_examples"][0]
    panels = []
    for task in ["find_match", "pipeline"]:
        for domain in ["CA2", "GT"]:
            e = scene["domains"][domain]["expected"][task]["100"]
            title = "Find+Match" if task == "find_match" else "Pipeline top-1 < 2 Å"
            panels.append(
                {
                    "pdb": pdb,
                    "view": f"{domain}_{task}",
                    "heading": f"{domain}   {title}   {e['success_count']}/{e['target_count']}",
                }
            )
    local_rows = []
    for domain in ["CA2", "GT"]:
        row = by_view[(pdb, f"{domain}_local_{oid}")]
        o = next(o for o in scene["occurrences"] if o["candidate_id"] == oid)
        metric = f"RMSD {row['rmsd_A']:.2f} Å" if row["prediction_model"] else "Reference only"
        panels.append(
            {
                "pdb": pdb,
                "view": row["view"],
                "heading": f"{domain}   {o['display_name']}   {metric}",
            }
        )
        local_rows.append((domain, row))
    en, zh = captions(pdb, scene, local_rows)
    c = scene["counts"]
    pages.append(
        {
            "id": f"multiligand-workbench-{pdb}",
            "title": f"{pdb.upper()}   Ligand recognition and modelling",
            "subtitle": f"{c['all']} deposited ligands, {c['small']} small molecules, {c['eligible']} eligible for modelling",
            "panels": panels,
            "caption_en": en,
            "caption_zh": zh,
        }
    )

for page in pages:
    # 180 × 225 mm; 直接给出英寸, 使静态尺寸检查与 PDF 实际物理尺寸一致.
    figure = plt.figure(figsize=(7.086614173228347, 8.858267716535433), facecolor="white")
    page["texts"] = [
        {"text": page["title"], "x": 32, "y": 24, "w": 1216, "h": 42, "size": 32, "bold": True},
        {"text": page["subtitle"], "x": 32, "y": 67, "w": 1216, "h": 26, "size": 18, "bold": False},
    ]
    axes = []
    for i, panel in enumerate(page["panels"]):
        label = string.ascii_lowercase[i]
        x, y = (32 if i % 2 == 0 else 672), 100 + (i // 2) * 484
        panel.update(
            {
                "label": label,
                "x": x,
                "y": y + 36,
                "w": 568,
                "h": 568 * 1400 / 1800,
                "image": str(args.data_root / panel["pdb"] / "exports" / (panel["view"] + ".png")),
            }
        )
        page["texts"].append(
            {"text": label, "x": x, "y": y, "w": 22, "h": 32, "size": 23, "bold": True}
        )
        page["texts"].append(
            {
                "text": panel["heading"],
                "x": x + 28,
                "y": y,
                "w": 540,
                "h": 32,
                "size": 23,
                "bold": True,
            }
        )
        ax = figure.add_axes(
            [
                x / width,
                1 - (panel["y"] + panel["h"]) / height,
                panel["w"] / width,
                panel["h"] / height,
            ],
            label=label,
        )
        ax.imshow(mpimg.imread(panel["image"]), interpolation="none", aspect="auto")
        ax.set_axis_off()
        # 标签锚点由实际 Matplotlib 轴测量; 标题的余下文字单独保持可编辑.
        ax.text(
            0,
            1 + 36 / panel["h"],
            label,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=23 * pt_per_px,
            weight="bold",
            color="#222222",
        )
        axes.append(ax)
    footer = (
        "Overview: teal, correct identity; brown, other candidates. Local: teal, top-1; orange, reference."
        if page["id"] == "multiligand-workbench"
        else "Find+Match: teal, correct identity. Pipeline: teal, RMSD < 2 Å; brown, ≥ 2 Å. Orange, reference."
    )
    page["texts"].append(
        {"text": footer, "x": 32, "y": 1561, "w": 1216, "h": 25, "size": 16, "bold": False}
    )
    for text in page["texts"]:
        if text["text"] in list("abcdef"):
            continue
        figure.text(
            text["x"] / width,
            1 - text["y"] / height,
            text["text"],
            fontsize=text["size"] * pt_per_px,
            weight="bold" if text["bold"] else "normal",
            ha="left",
            va="top",
            color="#222222",
        )
    figure.canvas.draw()
    require_matplotlib_panel_alignment(
        figure,
        axes=axes,
        panel_ids=list("abcdef"),
        row_groups=[list("ab"), list("cd"), list("ef")],
        column_groups=[list("ace"), list("bdf")],
        require_panel_labels=True,
        json_out=build / (page["id"] + ".alignment.json"),
        strict=True,
    )
    figure.savefig(build / (page["id"] + ".pdf"), dpi=400)
    figure.savefig(build / (page["id"] + ".svg"), dpi=600)
    figure.savefig(build / (page["id"] + ".png"), dpi=300)
    figure.savefig(build / (page["id"] + ".tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(figure)
    (build / (page["id"] + ".caption.md")).write_text(
        page["caption_en"] + "\n\n" + page["caption_zh"] + "\n", encoding="utf-8"
    )
    print(page["id"], "assembled", flush=True)
(build / "presentation_data.json").write_text(
    json.dumps(
        {"schema": 1, "width": width, "height": height, "pages": pages},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
