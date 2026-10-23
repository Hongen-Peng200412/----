"""只读汇总已冻Match manifest的源PDB、全部候选、selected与身份可用候选规模.

--source-root为stage2-results目录, --output写计数JSON. 输入只使用保全的manifest、identities和candidates; 身份支持严格按(pdb_id,精确SMILES), 不推理、不重新生成候选.
"""
import argparse
import collections
import json
from pathlib import Path


def count_manifests(source_root: Path, output: Path) -> None:
    """逐条统计四种候选集合, 保留每种实际覆盖PDB数和源清单规模.

    输出列表每项包含manifest、split、source_pdb、all/selected/usable/selected_usable, 后四项各含pdb/blob整数. 背景始终可用, 真前景须能在实际输入身份表找到target_smiles; 空候选PDB仅保留在source_pdb分母.
    """
    result = []
    for folder in ["final_train_validation_shards01_06_v1", "test0_real_smiles_v1", "test0_cryoatom2_smiles_v1"]:
        directory = source_root / "manifests" / folder
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        for split, files in manifest["splits"].items():
            identity_rows = [json.loads(line) for line in (directory / files["identities"]).read_text(encoding="utf-8").splitlines() if line]
            supported = {(row["pdb_id"], row["smiles"]) for row in identity_rows}
            counts = collections.Counter()
            pdbs = {name: set() for name in ["all", "selected", "usable", "selected_usable"]}
            for line in (directory / files["candidates"]).read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                selected = row["candidate_selected"]
                usable = not row["foreground_target"] or (row["pdb_id"], row["target_smiles"]) in supported
                for name, keep in [("all", True), ("selected", selected), ("usable", usable), ("selected_usable", selected and usable)]:
                    if keep:
                        counts[name] += 1
                        pdbs[name].add(row["pdb_id"])
            result.append({"manifest": folder, "split": split, "source_pdb": manifest["summary"][split]["pdb_count"], **{name: {"pdb": len(pdbs[name]), "blob": counts[name]} for name in pdbs}})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    project = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").is_file() and (parent / "论文草稿.md").is_file())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=project / "画图/画图代码/stage2/output/stage2-results")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count_manifests(args.source_root, args.output)
