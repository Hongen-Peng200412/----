"""复核Fig4当前9NVS全景与局部作者视图使用的原Dice/IoU."""

import numpy as np


def read_case(store):
    """返回9NVS语义Dice和同一真实实例的两方法IoU; 只读原评价, 不新匹配blob."""
    # /storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/evaluation/{official_find_li.jsonl,per_pdb/9nvs.npz}: semantic_macro_f1为原逐PDB语义Dice; source_blob_index/occurrence_id定位intersections(P,G)、pred_sizes(P)、gt_sizes(G), 本图取Emap blob2和真实occurrence1.
    # 生产说明: C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md; /home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md.
    emap = "/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/evaluation/"
    # /storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1/held_out_test_0/: evaluation/f2_centered_gaussian_macro_selected.jsonl给9nvs语义Dice; 9nvs/evaluation/f2_centered_gaussian_macro_selected.npz给本侧blob1/occurrence1交集. 原blob编号不等于压缩后的行位置.
    # 原CA2 launch明确绑定96938959ed1a; 生产说明: /home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_96938959ed1a/Pocket_Plus/src/inference/README.md; 本地C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md.
    ca2 = "/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1/held_out_test_0/"
    records = {}
    for name, path in [
        ("emap", emap + "official_find_li.jsonl"),
        ("ca2", ca2 + "evaluation/f2_centered_gaussian_macro_selected.jsonl"),
    ]:
        row = next(r for r in store.json(path) if r["pdb_id"] == "9nvs")
        records[name + "_semantic_dice"] = float(row["semantic_macro_f1"])
    for name, path, blob in [
        ("emap", emap + "per_pdb/9nvs.npz", 2),
        ("ca2", ca2 + "9nvs/evaluation/f2_centered_gaussian_macro_selected.npz", 1),
    ]:
        arrays = store.npz(path)
        # 原blob编号与GT occurrence 1分别定位两轴, 不沿用某次压缩数组的紧凑位置.
        i = int(np.flatnonzero(arrays["source_blob_index"] == blob)[0])
        j = int(np.flatnonzero(arrays["occurrence_id"] == 1)[0])
        intersection = int(arrays["intersections"][i, j])
        records[name + "_instance_iou"] = intersection / (
            int(arrays["pred_sizes"][i]) + int(arrays["gt_sizes"][j]) - intersection
        )
    assert {k: round(v, 3) for k, v in records.items()} == {
        "emap_semantic_dice": 0.160,
        "ca2_semantic_dice": 0.757,
        "emap_instance_iou": 0.306,
        "ca2_instance_iou": 0.656,
    }, "9NVS原实验数值与采用显示不一致"
    result = {
        "pdb": "9nvs",
        "occurrence_id": 1,
        "emap_source_blob_index": 2,
        "ca2_source_blob_index": 1,
        **records,
    }
    return result
