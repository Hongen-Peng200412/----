"""从冻结实例完成度导出正文两张表, 并只读核对中英文原稿.

入口为 export_tables. 默认只输出 JSON 核对报告; --output-dir 显式指定导出目录时写 completion_tables.csv 和 completion_tables.md, 不修改论文或 PPT.
输入 completion.json 的 panels 按 id 定位 full_GT/full_CA2 及八种 small 条件; distributions 内每个 PDB 的 completion 是比例, 均值和中位数在完整 PDB 轴上计算.
CSV 每条是表格的一个结果单元格, 保存 table、condition、domain、budget_percent、statistic、pdb_count、value_percent、display; display 按正文保留一位小数.
运行例子: python 画图/画图代码/e2e/calculate/e2e-instance-completion/ops/export_tables.py --output-dir temp/figure-provenance/table-export
"""

import argparse
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import statistics


class TableValues(HTMLParser):
    """按 Markdown 内 HTML 表格的物理顺序收集 tbody 数值单元格."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.in_body = False
        self.in_cell = False
        self.cell = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables.append([])
        elif tag == "tbody":
            self.in_body = True
        elif tag == "td" and self.in_body:
            self.in_cell = True
            self.cell = []

    def handle_data(self, data):
        if self.in_cell:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_cell:
            value = "".join(self.cell).strip()
            if re.fullmatch(r"\d+\.\d+", value):
                self.tables[-1].append(value)
            self.in_cell = False
        elif tag == "tbody":
            self.in_body = False


def export_tables(completion_path, manuscript_paths, output_dir):
    """导出40个结果单元格, 对原稿的前两张HTML表逐格核对.

    输入参数:
        - completion_path: Path, 冻结 completion.json; panels 的 distributions 使用相对预算字符串, 如 "100".
        - manuscript_paths: list[Path], 中文与英文正文文件, 各自前两张表分别为全配体与小分子完成度.
        - output_dir: Path 或 None, 显式导出目录; None 表示仅核对并返回报告.
    返回值:
        - report: dict, passed 为全部单元格一致, tables 保存每表单元格数, manuscripts 保存原稿路径、实际数量与逐格差异.
    """
    panels = {panel["id"]: panel for panel in json.loads(completion_path.read_text(encoding="utf-8"))["panels"]}
    cells = []
    # 两个列表按论文表格的行列顺序展开; Table 2 先 CA2 后 GT.
    conditions = [(1, "Find+Match", None, None, ("GT", "CA2"))]
    conditions += [(2, f"{'Top-1' if pose == 1 else 'Best'} RMSD <{threshold} Å", pose, threshold, ("CA2", "GT")) for pose in (1, 50) for threshold in (2, 3)]
    for table, condition, pose, threshold, domains in conditions:
        for domain in domains:
            panel_id = f"full_{domain}" if table == 1 else f"small_{domain}_pose{pose}_rmsd{threshold}"
            panel = panels[panel_id]
            for budget in (100, 300):
                records = panel["distributions"][str(budget)]
                values = [record["completion"] for record in records]
                for statistic, value in (("mean", statistics.mean(values)), ("median", statistics.median(values))):
                    cells.append({"table": table, "condition": condition, "domain": domain, "budget_percent": budget, "statistic": statistic, "pdb_count": len(values), "value_percent": value * 100, "display": f"{value * 100:.1f}"})
    expected = {table: [cell["display"] for cell in cells if cell["table"] == table] for table in (1, 2)}
    checks = []
    for manuscript in manuscript_paths:
        parser = TableValues()
        parser.feed(manuscript.read_text(encoding="utf-8"))
        mismatches = []
        for table in (1, 2):
            actual = parser.tables[table - 1]
            if len(actual) != len(expected[table]):
                mismatches.append({"table": table, "actual_count": len(actual), "expected_count": len(expected[table])})
            for index, (actual_value, expected_value) in enumerate(zip(actual, expected[table]), 1):
                if actual_value != expected_value:
                    mismatches.append({"table": table, "cell": index, "actual": actual_value, "expected": expected_value})
        checks.append({"path": str(manuscript), "passed": not mismatches, "mismatches": mismatches})
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "completion_tables.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(cells[0]))
            writer.writeheader()
            writer.writerows(cells)
        lines = ["# 正文实例完成度表格", "", "数值来自冻结逐 PDB 完成比例；百分数保留一位小数。", "", "| 表 | 条件 | 受体 | 预算（%） | 统计量 | PDB 数 | 完成度（%） |", "|---|---|---|---:|---|---:|---:|"]
        lines += [f"| {c['table']} | {c['condition']} | {c['domain']} | {c['budget_percent']} | {c['statistic']} | {c['pdb_count']} | {c['display']} |" for c in cells]
        (output_dir / "completion_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"passed": all(check["passed"] for check in checks), "source": str(completion_path), "tables": {str(table): len(values) for table, values in expected.items()}, "manuscripts": checks}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[6]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completion", type=Path, default=root / "画图/画图代码/e2e/output/e2e-instance-completion/completion.json")
    parser.add_argument("--manuscripts", type=Path, nargs="+", default=[root / "论文草稿.md", root / "draft.md"])
    parser.add_argument("--output-dir", type=Path)
    arguments = parser.parse_args()
    report = export_tables(arguments.completion, arguments.manuscripts, arguments.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)
