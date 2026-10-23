"""从实际179-PDB身份轴与完整strongest预测核对当前五组分类计数.

--source-root 指向stage2-results冻结数据根, --output写一份分组JSON. 不重新前向或科学评价, 只按实际输入精确SMILES数量分组已冻的selected、支持身份真前景候选.
"""
import argparse
import collections
import json
from pathlib import Path


def rebuild_groups(source_root: Path, output: Path) -> None:
    """恢复正确数/支持数, 与当前绘图冻结count逐项相等后才写出.

    两manifest分别定义GT和CA2实际输入身份轴. 每个PDB按SMILES精确去重计数, 五种及以上并入第5组. 输出real/cryo各四类别的(5,2)整数计数, 最后一维为correct/support; 零支持保留[0,0].
    """
    frozen = json.loads((source_root / "frozen/strongest-1.json").read_text(encoding="utf-8"))
    categories = {"small_molecule": "small", "sugar": "sugar", "ion": "metal", "peptide_like": "peptide"}
    result = {}
    for condition, domain, folder in [("real_receptor", "real", "test0_real_smiles_v1"), ("cryoatom2_receptor", "cryo", "test0_cryoatom2_smiles_v1")]:
        directory = source_root / "manifests" / folder
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        identities = collections.defaultdict(set)
        identity_file = directory / manifest["splits"]["held_out_test_0"]["identities"]
        for line in identity_file.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            identities[row["pdb_id"]].add(row["smiles"])
        grouped = {category: [[0, 0] for _ in range(5)] for category in categories.values()}
        for pdb, candidates in frozen["predictions"][condition].items():
            group = min(5, len(identities[pdb])) - 1
            for candidate in candidates:
                if candidate["candidate_selected"] and candidate["foreground_target"] and candidate["identity_supported"]:
                    counts = grouped[categories[candidate["target_category"]]][group]
                    counts[0] += int(candidate["predicted_smiles"] == candidate["target_smiles"])
                    counts[1] += 1
        result[domain] = grouped
    expected = json.loads((source_root / "data_忽视2+2例子.json").read_text(encoding="utf-8"))["strongest_by_candidate_smiles_count"]
    if result != expected:
        raise ValueError("原身份轴重建计数与当前冻结图数据不一致")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    project = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").is_file() and (parent / "论文草稿.md").is_file())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=project / "画图/画图代码/stage2/output/stage2-results")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rebuild_groups(args.source_root, args.output)
