"""从已冻原始metrics导出表4, 不修改论文源稿.

显式传入 --source frozen指标目录 和 --output 目录. export_table() 读取11份原始metrics中的既有macro指标, 写出 table.csv 与 table.md. 不从概率图重新评价, 不运行模型.
"""
import argparse
import csv
import json
from pathlib import Path


def export_table(source: Path, output: Path) -> None:
    """从原指标读取CA2/GT的Dice、PRAUC0.3、PRAUC0.5, 并显示三位小数.

    source 是冻结metrics目录, 含unet_c1/shared、unet_diff/base/full的CA2/GT、Find_1的CA2/GT. 最终Find用f2_centered_gaussian, 其余用f1_blobs_basic. CSV保留原始精度, Markdown显示三位, 不重算科学指标.
    """
    rows = []
    variants = [("Density only", "unet_c1", "f1_blobs_basic"), ("+ Difference density", "unet_diff", "f1_blobs_basic"), ("+ Density bank", "unet_base", "f1_blobs_basic"), ("+ Receptor features", "unet_full", "f1_blobs_basic"), ("+ Centroid encoding", "Find_1", "f1_blobs_basic"), ("LigandSeek2-Find", "Find_1", "f2_centered_gaussian")]
    for label, model, pipeline in variants:
        values = []
        for condition in ["CA2", "GT"]:
            data = json.loads((source / model / ("shared" if model == "unet_c1" else condition) / f"{pipeline}_macro_selected.metrics.json").read_text(encoding="utf-8"))
            if data["pdb_count"] != 179:
                raise ValueError("消融表仅使用179-PDB test_0原指标")
            values.extend(data[key] for key in ["semantic_macro_f1", "one_to_one_macro_prauc_0p3", "one_to_one_macro_prauc_0p5"])
        rows.append([label, *values])
    columns = ["模型", "CA2 Dice", "CA2 PRAUC0.3", "CA2 PRAUC0.5", "GT Dice", "GT PRAUC0.3", "GT PRAUC0.5"]
    output.mkdir(parents=True, exist_ok=True)
    with (output / "table.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    text = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    text += ["| " + " | ".join([row[0], *[f"{value:.3f}" for value in row[1:]]]) + " |" for row in rows]
    (output / "table.md").write_text("\n".join(text) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_table(args.source, args.output)
