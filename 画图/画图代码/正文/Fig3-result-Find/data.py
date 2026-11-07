"""为一个具名Find图读取所需原件并组装逐PDB指标, 不运行其他图或消融表.

prepare_find是唯一跨图入口. 调用方必须明示level条件、指标列表、是否需要完整预算输入和配对Dice. 返回plot_data及可选completion_inputs; 其中PDB、候选、真实实例轴保留原顺序. 所有实验地址与字段解释集中于本文件, 候选归属、实例指标与语义并集分别由matching.py、instance_metrics.py、semantic.py拥有.
"""

from pathlib import Path
import copy
import numpy as np
from scipy.stats import gaussian_kde
from TOOLS.runtime.paths import load_module

MATCHING = load_module(Path(__file__).with_name("matching.py"), "fig3_find_matching")
INSTANCE = load_module(Path(__file__).with_name("instance_metrics.py"), "fig3_find_instance")
SEMANTIC = load_module(Path(__file__).with_name("semantic.py"), "fig3_find_semantic")
# GT/CA2实际生产说明分别为下列历史release, 不是当前V3教程的追溯替代.
# GT说明: /home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_d24c9e99c664/Pocket_Plus/src/inference/README.md; 本地入口: C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md.
# CA2说明: /home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_96938959ed1a/Pocket_Plus/src/inference/README.md; 本地入口: C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md.
# 显式level说明: /home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md; 本地入口: C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md.
# 旧无level原status没有完整argv/release字段, 不能用上述新level版本或当前HEAD补写旧运行身份.
ROOTS = {
    "GT": "/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1/held_out_test_0",
    "Cryo": "/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1/held_out_test_0",
    "Emap_level": "/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0",
    "Emap_no_level": "/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0",
}
SMALL_ROOT = "/storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0"
ORI = "/storage/penghongen/AdaLigand/Ori_Data"
METHODS = ("GT", "Cryo", "Emap")
FIELDS = {
    "full": {
        "dice": "semantic_macro_f1",
        "oto03": "one_to_one_macro_prauc_0p3",
        "oto05": "one_to_one_macro_prauc_0p5",
        "precision": "one_to_one_macro_precision_0p3",
        "recall": "one_to_one_macro_recall_0p3",
        "precision05": "one_to_one_macro_precision_0p5",
        "recall05": "one_to_one_macro_recall_0p5",
    },
    "small": {
        "dice": "semantic_dice",
        "oto03": "one_to_one_prauc_0p3",
        "oto05": "one_to_one_prauc_0p5",
        "precision": "one_to_one_precision_0p3",
        "recall": "one_to_one_recall_0p3",
        "precision05": "one_to_one_precision_0p5",
        "recall05": "one_to_one_recall_0p5",
    },
}


# ================================================================================================
def prepare_find(store, condition: str, metrics: tuple[str, ...], with_completion: bool, paired: bool):
    """只为当前请求组装一个level条件的Find绘图输入.

    输入参数:
        - store: SourceStore, 中性服务器原字节读取接口, 不负责候选归属或统计.
        - condition: str, explicit_emdb_level或no_level, 每次恰好一个条件.
        - metrics: tuple[str, ...], 当前图实际使用的指标, 如('dice','oto03','precision','recall').
        - with_completion: bool, 只有补Fig1为True, 因为该图需要179/94-PDB的100%与300%预算.
        - paired: bool, 只有正文Fig3为True, 读取原地图分辨率并生成Dice配对计数.

    返回值:
        - plot_data: dict, condition和cohorts.full/small; 每个cohort含ids/n/models, ids按原PDB顺序, 如small首个9lfa.
            - models[method].values[metric]: list[float], (N_pdb,), 0-1比例, 与ids逐PDB对齐.
            - models[method].bars[metric]: dict, mean/lower/upper为PDB等权均值和10,000次bootstrap的95%区间; 仅当前图请求的Dice/PRAUC.
            - models[method].distribution[metric]: dict, grid/density均长161, 后者为反射KDE最大值归一到1; quartiles为25/50/75%分位; 仅当前图请求的P/R.
            - resolution: list[float], (N_pdb,), 原地图分辨率, 单位Å; 只有paired为True时存在.
            - paired_counts: dict[str,int], find_higher/equal/emap_higher为CA2相对Emap的Dice计数; 只有paired为True时存在.
        - completion_inputs: dict, with_completion=False时为空; 否则含facts/types/original_candidates.
            - facts[method,pdb]: dict[str,np.ndarray], 原候选×真实实例交集及两轴编号, 仅当前level的三方法.
            - types[pdb]: dict[int,str], 原真实实例编号到类别, 如{1:'small_molecule'}.
            - original_candidates: dict, real_receptor/cryoatom2_receptor各按PDB保存完整原Find候选, 包含selected/概率均值/blob编号/真实归属.
    """
    # 原件 /storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/provenance.json: cohort_pdb_ids固定94-PDB小分子范围, quality_manifest为实际绝对文件地址.
    provenance = store.json(SMALL_ROOT + "/provenance.json")
    emap_key = "Emap_level" if condition == "explicit_emdb_level" else "Emap_no_level"
    roots = {"GT": ROOTS["GT"], "Cryo": ROOTS["Cryo"], "Emap": ROOTS[emap_key]}
    stems = {
        "GT": "f2_centered_gaussian_macro_selected",
        "Cryo": "f2_centered_gaussian_macro_selected",
        "Emap": "official_find_li",
    }
    pipelines = {"GT": "find_real_f2_gaussian", "Cryo": "find_cryo_f2_gaussian", "Emap": "emap_official_li"}
    rows = {}
    for method in METHODS:
        # 例如完整原件 /storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1/held_out_test_0/evaluation/f2_centered_gaussian_macro_selected.jsonl, 每行一个PDB的原宏平均指标.
        rows[method] = {"full": store.json(roots[method] + "/evaluation/" + stems[method] + ".jsonl")}
        if method != "Emap" or condition == "no_level":
            # 原件 /storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/find_real_f2_gaussian.per_pdb.jsonl 等, 每行一个小分子PDB, 不是Build的77-PDB筛选范围.
            rows[method]["small"] = store.json(SMALL_ROOT + "/" + pipelines[method] + ".per_pdb.jsonl")
        else:
            rows[method]["small"] = []
    full_ids = [row["pdb_id"] for row in rows["GT"]["full"]]
    small_ids = provenance["cohort_pdb_ids"]
    assert len(full_ids) == 179 and len(small_ids) == 94
    # 原件 /storage/penghongen/AdaLigand/Ori_Data/parse/9nvs/occurrences.jsonl: candidate_id是真实实例原编号, type_tag如small_molecule, 不等于预测blob编号.
    store.read_many([ORI + "/parse/" + pdb + "/occurrences.jsonl" for pdb in small_ids])
    types = {
        pdb: {
            int(row["candidate_id"]): row["type_tag"]
            for row in store.json(ORI + "/parse/" + pdb + "/occurrences.jsonl")
        }
        for pdb in small_ids
    }
    resolution = {}
    if paired:
        # 原件 /storage/penghongen/AdaLigand/held_out/held_out_base.jsonl: quality.map_resolution为地图分辨率Å, 只用于当前Fig3散点颜色, 不筛选PDB.
        resolution = {
            row["pdb_id"]: row["quality"]["map_resolution"]
            for row in store.json(provenance["quality_manifest"], provenance["quality_manifest_sha256"])
        }
    facts = {}
    npz_ids = full_ids if with_completion else small_ids
    for method in METHODS:
        # GT/CA2例: /storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1/held_out_test_0/9nvs/evaluation/f2_centered_gaussian_macro_selected.npz.
        # Emap level例: /storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/evaluation/per_pdb/9nvs.npz; nolevel例: /storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0/evaluation/per_pdb/9nvs.npz.
        paths = [
            roots[method]
            + (
                "/evaluation/per_pdb/" + pdb + ".npz"
                if method == "Emap"
                else "/" + pdb + "/evaluation/" + stems[method] + ".npz"
            )
            for pdb in npz_ids
        ]
        for start in range(0, len(paths), 64):
            store.read_many(paths[start : start + 64])
        for pdb, path in zip(npz_ids, paths):
            # intersections: int,(N_pred,N_gt), 交集体素数; pred_sizes/gt_sizes对齐第一/第二轴; occurrence_id:(N_gt,)是真实原编号, 如1; source_blob_index:(N_pred,)为原blob编号, 如11, 不是紧凑轴下标.
            # candidate_selected/candidate_prauc_eligible: bool,(N_pred,), 分别是原最终选择和PRAUC可扫描资格; candidate_score:(N_pred,)为原评分, 保留原精度并将并列分数成组处理.
            facts[method, pdb] = store.npz(path)
    need_dice = "dice" in metrics
    thresholds = tuple(
        t
        for t, names in ((0.3, ("precision", "recall", "oto03")), (0.5, ("precision05", "recall05", "oto05")))
        if any(name in metrics for name in names)
    )
    if condition == "explicit_emdb_level" and need_dice:
        # /storage/penghongen/AdaLigand/Ori_Data/density/9nvs/ligand_area.npz保存grid_shape_zyx和mask_<真实实例编号>的(K,3)全图ZYX坐标; 生产说明 C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/Ori_Data/README.md 所属原预处理说明见trace.
        # /storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/mapped/9nvs/official_blobs.npz含voxel_offsets和voxel_index_global_zyx, offsets按原blob轴切分同一坐标数组.
        paths = [
            path
            for pdb in small_ids
            for path in (
                ORI + "/density/" + pdb + "/ligand_area.npz",
                roots["Emap"] + "/mapped/" + pdb + "/official_blobs.npz",
            )
        ]
        for start in range(0, len(paths), 64):
            store.read_many(paths[start : start + 64])
    for method in METHODS:
        previous = {row["pdb_id"]: row for row in rows[method]["small"]}
        computed = []
        for pdb in small_ids:
            arrays = facts[method, pdb]
            # gt_types: list[str], (N_gt,), 与该NPZ的occurrence_id轴逐项对应, 不按JSON行位置拼接.
            gt_types = [types[pdb][int(identifier)] for identifier in arrays["occurrence_id"]]
            row = copy.deepcopy(previous[pdb]) if previous else {"pdb_id": pdb}
            for threshold in thresholds:
                row.update(
                    INSTANCE.evaluate_selected(
                        arrays["intersections"],
                        arrays["pred_sizes"],
                        arrays["gt_sizes"],
                        arrays["occurrence_id"],
                        gt_types,
                        arrays["candidate_selected"],
                        threshold,
                    )
                )
            if method == "Emap" and condition == "explicit_emdb_level":
                small_axis = np.asarray([kind == "small_molecule" for kind in gt_types])
                keep = ~MATCHING.ignored_candidates(
                    arrays["intersections"], arrays["pred_sizes"], arrays["gt_sizes"], arrays["occurrence_id"], gt_types
                )
                if need_dice:
                    masks = store.npz(ORI + "/density/" + pdb + "/ligand_area.npz")
                    shape = tuple(int(value) for value in masks["grid_shape_zyx"])
                    gt_rows = [
                        masks["mask_" + str(int(identifier))] for identifier in arrays["occurrence_id"][small_axis]
                    ]
                    blobs = store.npz(roots["Emap"] + "/mapped/" + pdb + "/official_blobs.npz")
                    tp, fp, fn = SEMANTIC.semantic_counts(
                        blobs, arrays["source_blob_index"][keep], arrays["candidate_selected"][keep], gt_rows, shape
                    )
                    row["semantic_dice"] = 2 * tp / (2 * tp + fp + fn)
                # 只重算本图请求的PRAUC; 0.3候选归属在0.5分析中仍然固定, 不能按0.5重新忽略非小分子.
                fact = {
                    "pdb_id": pdb,
                    "gt_sizes": arrays["gt_sizes"][small_axis],
                    "pred_sizes": arrays["pred_sizes"][keep],
                    "intersections": arrays["intersections"][np.ix_(keep, small_axis)],
                    "score": arrays["candidate_score"][keep],
                    "eligible": arrays["candidate_prauc_eligible"][keep],
                }
                for threshold, name in ((0.3, "oto03"), (0.5, "oto05")):
                    if name in metrics:
                        row[FIELDS["small"][name]] = INSTANCE.prauc(
                            [fact], [INSTANCE.coverage_edges(fact, threshold)], "one_to_one"
                        )
            computed.append(row)
        rows[method]["small"] = computed
    data = {
        "condition": condition,
        "bootstrap_replicates": 10000,
        "bootstrap_seed": 20260922,
        "kde_bandwidth": 0.045,
        "cohorts": {},
    }
    if paired:
        data["paired_metric"] = "dice"
    for cohort, ids in (("full", full_ids), ("small", small_ids)):
        block = {"ids": ids, "n": len(ids), "models": {}}
        if paired:
            block["resolution"] = [float(resolution[pdb]) for pdb in ids]
        for method in METHODS:
            by_pdb = {row["pdb_id"]: row for row in rows[method][cohort]}
            values = {metric: [float(by_pdb[pdb][FIELDS[cohort][metric]]) for pdb in ids] for metric in metrics}
            distribution = {}
            for metric in metrics:
                if metric.startswith(("precision", "recall")):
                    vector = np.asarray(values[metric])
                    grid = np.linspace(0, 1, 161)
                    density = gaussian_kde(np.r_[vector, -vector, 2 - vector], bw_method=0.045)(grid)
                    distribution[metric] = {
                        "grid": grid.tolist(),
                        "density": (density / density.max()).tolist(),
                        "quartiles": np.quantile(vector, [0.25, 0.5, 0.75]).tolist(),
                    }
            block["models"][method] = {"values": values, "distribution": distribution, "bars": {}}
        bar_metrics = tuple(metric for metric in metrics if metric in ("dice", "oto03", "oto05"))
        keys = [(method, metric) for method in METHODS for metric in bar_metrics]
        matrix = np.column_stack([block["models"][method]["values"][metric] for method, metric in keys])
        rng = np.random.default_rng(20260922)
        boot = np.concatenate([matrix[rng.integers(0, len(ids), size=(250, len(ids)))].mean(axis=1) for _ in range(40)])
        bounds = np.quantile(boot, [0.025, 0.975], axis=0)
        for index, (method, metric) in enumerate(keys):
            block["models"][method]["bars"][metric] = {
                "mean": float(matrix[:, index].mean()),
                "lower": float(bounds[0, index]),
                "upper": float(bounds[1, index]),
            }
        if paired:
            difference = np.asarray(block["models"]["Cryo"]["values"]["dice"]) - np.asarray(
                block["models"]["Emap"]["values"]["dice"]
            )
            block["paired_counts"] = {
                "find_higher": int((difference > 1e-12).sum()),
                "equal": int((abs(difference) <= 1e-12).sum()),
                "emap_higher": int((difference < -1e-12).sum()),
            }
        data["cohorts"][cohort] = block
    completion = {}
    if with_completion:
        # 原件 /storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json: 两受体predictions内保留Find原排序所需的概率均值, 不能替换为Gaussian NPZ评分; 生产说明 C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md, 原release cab21d9ceea5.
        candidates = store.json("/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json")[
            "predictions"
        ]
        completion = {"facts": facts, "types": types, "original_candidates": candidates}
    return data, completion
