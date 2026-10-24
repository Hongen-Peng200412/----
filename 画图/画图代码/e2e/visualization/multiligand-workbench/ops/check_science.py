"""对照原冻结完成数检查五模式与预算、构象的连接; 报告写 temp, 不计算新的 RMSD."""

import argparse
import importlib.util
import json
from pathlib import Path

root = next(p for p in Path(__file__).resolve().parents if (p / "论文草稿.md").exists())
code = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wb_selection", code / "chimerax_bundle/src/selection.py")
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-root", type=Path, default=Path("D:/AdaLigand_Visualization"))
args = parser.parse_args()
plots = root / "画图/画图代码"
panels = json.loads((plots / "e2e/output/find-build-shared/data.json").read_text(encoding="utf-8"))["panels"]
panels += json.loads(
    (plots / "e2e/output/e2e-instance-completion/completion.json").read_text(encoding="utf-8")
)["panels"]
panels = {p["id"]: p for p in panels}
checks = []
errors = []
for file in sorted(args.data_root.glob("*/scene.json")):
    s = json.loads(file.read_text(encoding="utf-8"))
    for d in ["CA2", "GT"]:
        for view in selection.VIEW_NAMES:
            for b in ["50", "100", "200", "300"]:
                for pose in ["top1", "best"] if view in ["find_build", "pipeline"] else ["top1"]:
                    for threshold in [2, 3] if view in ["find_build", "pipeline"] else [2]:
                        config = {
                            **selection.DEFAULT,
                            "condition": d,
                            "view": view,
                            "budget": b,
                            "pose": pose,
                        }
                        shown = selection.selected_keys(s, config)
                        matched = set()
                        for r in s["domains"][d]["candidates"]:
                            if f'{d}_blob_{r["source_blob_index"]}' not in shown:
                                continue
                            ok = (
                                r["foreground_target"]
                                if view == "find_all"
                                else (
                                    r["is_small"]
                                    if view == "find_small"
                                    else (
                                        r["identity_correct"]
                                        if view == "find_match"
                                        else any(
                                            m["key"] in shown
                                            and m["kind"] == "pose"
                                            and m["domain"] == d
                                            and m["blob"] == r["source_blob_index"]
                                            and m["rmsd_A"] is not None
                                            and m["rmsd_A"] < threshold
                                            for m in s["models"]
                                        )
                                    )
                                )
                            )
                            if ok:
                                matched.add(r["matched_occurrence_id"])
                        limit = 1 if pose == "top1" else 50
                        pid = {
                            "find_all": f"find_full_{d}",
                            "find_small": f"find_stage1_small_{d}",
                            "find_match": f"full_{d}",
                            "find_build": f"assume_{d}_pose{limit}_rmsd{threshold}.0",
                            "pipeline": f"small_{d}_pose{limit}_rmsd{threshold}",
                        }[view]
                        expected = next(
                            r["success_count"]
                            for r in panels[pid]["distributions"][b]
                            if r["pdb_id"] == s["pdb_id"]
                        )
                        row = {
                            "pdb": s["pdb_id"],
                            "condition": d,
                            "view": view,
                            "budget": b,
                            "pose": pose,
                            "threshold_A": threshold,
                            "expected": expected,
                            "actual": len(matched),
                        }
                        checks.append(row)
                        if expected != len(matched):
                            errors.append(row)
                # 过滤后的集合只能缩小, 不能把预算之外候选补入.
                previous = selection.selected_keys(
                    s, {**selection.DEFAULT, "condition": d, "view": view, "budget": b}
                )
                for filter_name in ["foreground", "small", "eligible"]:
                    current = selection.selected_keys(
                        s,
                        {
                            **selection.DEFAULT,
                            "condition": d,
                            "view": view,
                            "budget": b,
                            "filter": filter_name,
                        },
                    )
                    assert current <= previous, (s["pdb_id"], d, view, b, filter_name)
                    previous = current
out = root / "temp/multiligand-workbench/qa"
out.mkdir(parents=True, exist_ok=True)
(out / "science.json").write_text(
    json.dumps({"passed": not errors, "checks": checks, "errors": errors}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("comparisons", len(checks), "errors", len(errors))
print(json.dumps(errors[:5], ensure_ascii=False))
assert not errors
