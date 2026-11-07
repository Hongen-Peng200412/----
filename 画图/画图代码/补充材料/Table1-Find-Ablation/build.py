"""从原十一份Find metrics构造补Table1的六模型消融表.

build只读取179-PDB宏平均汇总, 返回table.md路径并写table.csv/table.md/source_reads.json. 不运行任何图, 不读取716个计时文件, 不把结果回写作者论文原表.
"""

from pathlib import Path
import csv
import json
from TOOLS.server_io.source import SourceStore


# ================================================================================================
def build(output: Path):
    """在本次空temp目录生成六行乘六个数值, CSV保留原精度, Markdown保留三位小数.

    output: Path, 本次根temp目录. table.csv第一列模型名, 随后依次CA2和GT的Dice/PRAUC0.3/PRAUC0.5; table.md使用同一行列顺序. source_reads.json保存原件地址与读取摘要, 不是后续科学输入.
    """
    output.mkdir(parents=True, exist_ok=True)
    # 原生产说明: C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md; 历史原输入消融配置及CLI另见本图trace与服务器原release元数据.
    # 原件目录 /storage/penghongen/AdaLigand_stage1_inference/UNET 和 /storage/penghongen/AdaLigand_stage1_inference/Find_1; evaluation/*_macro_selected.metrics.json保存同一179-PDB范围的宏平均比例, 不是149-PDB历史派生.
    source_roots = {
        "unet_c1": {
            "CA2": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_c1_pdb_centric_v2/artifacts/unet_c1",
            "GT": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_c1_pdb_centric_v2/artifacts/unet_c1",
        },
        "unet_diff": {
            "CA2": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_diff/CryoAtom2受体/artifacts/unet_diff",
            "GT": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_diff/artifacts/unet_diff",
        },
        "unet_base": {
            "CA2": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_base/CryoAtom2受体/artifacts/unet_base",
            "GT": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_base/artifacts/unet_base",
        },
        "unet_full": {
            "CA2": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_full/CryoAtom2受体/artifacts/unet_full",
            "GT": "/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_full/artifacts/unet_full",
        },
        "Find_1": {
            "CA2": "/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1",
            "GT": "/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1",
        },
    }
    variants = [
        ("Density only", "unet_c1", "f1_blobs_basic"),
        ("+ Difference density", "unet_diff", "f1_blobs_basic"),
        ("+ Density bank", "unet_base", "f1_blobs_basic"),
        ("+ Receptor features", "unet_full", "f1_blobs_basic"),
        ("+ Centroid encoding", "Find_1", "f1_blobs_basic"),
        ("LigandSeek-Find", "Find_1", "f2_centered_gaussian"),
    ]
    store = SourceStore(output / "downloads", Path("D:/AdaLigand_Visualization/server"))
    table = []
    try:
        paths = {
            source_roots[model][domain] + "/held_out_test_0/evaluation/" + pipeline + "_macro_selected.metrics.json"
            for _, model, pipeline in variants
            for domain in ("CA2", "GT")
        }
        # Density-only两个受体共享同一原件; 按地址去重读取为11份, 保留两列显示而不伪造两次实验.
        metrics = {path: store.json(path) for path in sorted(paths)}
        for label, model, pipeline in variants:
            values = []
            for domain in ("CA2", "GT"):
                record = metrics[
                    source_roots[model][domain]
                    + "/held_out_test_0/evaluation/"
                    + pipeline
                    + "_macro_selected.metrics.json"
                ]
                assert record["pdb_count"] == 179
                # 三字段均为0-1宏平均比例, 同一PDB集等权; 如semantic_macro_f1为语义Dice, 不是逐实例micro统计.
                values.extend(
                    record[field]
                    for field in ("semantic_macro_f1", "one_to_one_macro_prauc_0p3", "one_to_one_macro_prauc_0p5")
                )
            table.append([label, *values])
        columns = ["模型", "CA2 Dice", "CA2 PRAUC0.3", "CA2 PRAUC0.5", "GT Dice", "GT PRAUC0.3", "GT PRAUC0.5"]
        with (output / "table.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(table)
        text = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        text += ["| " + " | ".join([row[0], *[f"{value:.3f}" for value in row[1:]]]) + " |" for row in table]
        (output / "table.md").write_text("\n".join(text) + "\n", encoding="utf-8")
        (output / "source_reads.json").write_text(
            json.dumps({"reads": store.reads}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    finally:
        store.close()
    return output / "table.md"
