"""从本地四模型完整frozen JSON导出绘图所需selected候选, 不运行推理.

--source-root 为保存<模型>.json的冻结目录, --output是selected_predictions.json的明确目标. 导出的source和sha256沿用已冻原来源身份, 并核对本地原件散列, 不重新生成科学预测.
"""
import argparse
import hashlib
import json
from pathlib import Path


def export_selected(source_root: Path, provenance: Path, output: Path) -> None:
    """保留四模型两受体所有selected预测及原metrics, 与旧摘录逐值相同.

    provenance保存原逐模型source/sha256/threshold_source身份; 输出字典按模型、conditions、real_receptor/cryoatom2_receptor和rows组织. 每行保存候选编号、前景真值/概率、身份支持及是否预测正确. 不导入科学包.
    """
    original = json.loads(provenance.read_text(encoding="utf-8-sig"))
    result = {}
    for model in ["strongest-1", "density_only-106", "density_only-0", "pocket_only-0"]:
        path = source_root / f"{model}.json"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != original[model]["sha256"]:
            raise ValueError(f"冻结原件与来源散列不一致: {path}")
        data = json.loads(raw)
        item = {key: original[model][key] for key in ["source", "sha256", "threshold_source"]}
        item["conditions"] = {}
        for condition in ["real_receptor", "cryoatom2_receptor"]:
            rows = []
            for pdb, candidates in data["predictions"][condition].items():
                for candidate in candidates:
                    if candidate["candidate_selected"]:
                        row = {key: candidate[key] for key in ["centered_box_index", "source_blob_index", "foreground_probability", "foreground_target", "identity_supported", "matched_occurrence_id", "target_category"]}
                        row.update(pdb_id=pdb, identity_correct=candidate["predicted_smiles"] == candidate["target_smiles"])
                        rows.append(row)
            item["conditions"][condition] = {"metrics": data["metrics"][condition], "rows": rows}
        result[model] = item
    if result != original:
        raise ValueError("完整冻结原件重建的selected事实与既有摘录不一致")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    project = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").is_file() and (parent / "论文草稿.md").is_file())
    source = project / "画图/画图代码/stage2/output/stage2-results"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=source / "frozen")
    parser.add_argument("--provenance", type=Path, default=source / "provenance/selected_predictions.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_selected(args.source_root, args.provenance, args.output)
