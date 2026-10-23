"""从两代模型的冻结绘图统计导出表3, 不修改论文源稿.

运行时显式传入 --source plot_data.json 和 --output 目录. export_table() 写出 table.csv 与 table.md, 两者每行均对应一个集合/模型, 六个数依次为 CA2 与 GT 的 Dice、PRAUC0.3、PRAUC0.5. 只将已存均值显示为三位小数, 不重新求均值或改变样本资格.
"""
import argparse
import csv
import json
from pathlib import Path


def export_table(source: Path, output: Path) -> None:
    """读取 cohorts.<full/small>.models.<L1/L2>_<CA2/GT>.bars 的 mean 并导出.

    source 是 JSON 文件, bars 三键为 dice/prauc_0p3/prauc_0p5, 每键的 mean 是无量纲 PDB 等权均值. output 是新导出目录, table.csv 保留精确均值, table.md 仅显示三位小数; 不覆盖原稿和已有 PPT.
    """
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    columns = ["集合", "模型", "CA2 Dice", "CA2 PRAUC0.3", "CA2 PRAUC0.5", "GT Dice", "GT PRAUC0.3", "GT PRAUC0.5"]
    rows = []
    for cohort, cohort_name in (("full", "全配体"), ("small", "小分子配体")):
        for generation, name in (("L1", "LigandSeek"), ("L2", "LigandSeek2-Find")):
            values = [data["cohorts"][cohort]["models"][f"{generation}_{receptor}"]["bars"][metric]["mean"] for receptor in ("CA2", "GT") for metric in ("dice", "prauc_0p3", "prauc_0p5")]
            rows.append([cohort_name, name, *values])
    output.mkdir(parents=True, exist_ok=True)
    with (output / "table.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    text = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    text += ["| " + " | ".join([*row[:2], *[f"{value:.3f}" for value in row[2:]]]) + " |" for row in rows]
    (output / "table.md").write_text("\n".join(text) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_table(args.source, args.output)
