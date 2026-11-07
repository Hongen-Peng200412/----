"""只计算补Fig5实际使用的18条K=1到10整数曲线, 不生成预算完成度面板."""

from pathlib import Path
from TOOLS.runtime.paths import load_module

ROOT = Path(__file__).resolve().parents[4]
MAIN = ROOT / "画图/画图代码/正文/Fig6-result-E2E"
COHORTS = load_module(MAIN / "cohorts.py", "fig6_cohorts")
ACTUAL = load_module(MAIN / "actual_inputs.py", "fig6_actual")
CONTROLLED = load_module(MAIN / "controlled_inputs.py", "fig6_controlled")
ACCOUNTING = load_module(MAIN / "accounting.py", "fig6_accounting")


# ================================================================================================
def prepare_topk(store):
    """返回全配体5、小分子定位/身份5、实际构象8条长度10的整数序列.

    store: SourceStore, 本次只读原件. 返回full/small_find/small_match/build四组; build只含local_cov-C的pose1/50_lt2/3, denominators固定full179/small77. K是计费尝试数, 曲线值为前K至少成功一个目标的PDB数, 不按成功实例数加权, 不计算Top5、四方法或相对预算曲线.
    """
    full_counts, members, identities = COHORTS.read_cohorts(store, True)
    # 原件 /storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json, curves.source_probability_mean保存完整179-PDB的原Find/Match计数, predictions保存所有候选的精确身份argmax; 原生产说明 /home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md, 本地 C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md.
    full = store.json("/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json")
    # 原件 /storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/stage1_only/stage1_only.json, traces.source_probability_mean.real_receptor/cryoatom2_receptor为77-PDB完整候选; target_scope声明background/non_stage3_foreground/stage3_foreground, 真实范围外前景免费, 与实际Match计费分开.
    stage1 = store.json("/storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/stage1_only/stage1_only.json")
    actual = ACTUAL.read_actual(store, full, identities)
    emap = CONTROLLED.read_emap(store, full_counts, members, (), ())
    limits = tuple(range(1, 11))
    data = {
        "accounting_rule": ACCOUNTING.RULE,
        "full": {
            key: full["curves"]["source_probability_mean"][key]["hit_count"][:10]
            for key in ("real_stage1_only", "real_stage1_matcher", "cryo_stage1_only", "cryo_stage1_matcher")
        },
        "small_find": {},
        "small_match": {},
        "build": {},
        "denominators": {"full": len(full_counts), "small": len(members)},
        "provenance": {
            "emap2lig_condition": "explicit_emdb_level",
            "sources": "server original arrays and original model evaluations",
        },
    }
    data["full"]["emap2lig"] = [
        sum(any(step <= k for step in emap["full_success"][pdb].values()) for pdb in full_counts) for k in limits
    ]
    data["small_find"]["emap2lig"] = [
        sum(any(step <= k for step in emap["small_success"][pdb].values()) for pdb in members) for k in limits
    ]
    for domain, condition in [("GT", "real_receptor"), ("CA2", "cryoatom2_receptor")]:
        traces = actual[domain]["traces"]
        direct = {(r["pdb_id"], r["source_blob_index"]): r for r in actual[domain]["direct"]}
        data["small_find"][condition] = ACCOUNTING.localization_counts(
            stage1["traces"]["source_probability_mean"][condition], limits
        )
        data["small_match"][condition] = [
            sum(
                any(
                    c["target_scope"] == "stage3_foreground" and c["attempt_index"] <= k and c["success"] for c in trace
                )
                for trace in traces.values()
            )
            for k in limits
        ]
        data["build"][domain] = {"local_cov-C": {}}
        for pose in (1, 50):
            for threshold in ("2.0", "3.0"):
                # 原姿态字段由Fig6实际读取器说明: methods.local_cov-C.success[阈值][原排名数]保留原布尔评价, 不重新排序或根据RMSD选择身份.
                counts = [
                    sum(
                        any(
                            c["target_scope"] == "stage3_foreground"
                            and c["attempt_index"] <= k
                            and c["success"]
                            and (pdb, c["source_blob_index"]) in direct
                            and direct[pdb, c["source_blob_index"]]["methods"]["local_cov-C"]["success"]
                            .get(threshold, {})
                            .get(str(pose), False)
                            for c in trace
                        )
                        for pdb, trace in traces.items()
                    )
                    for k in limits
                ]
                data["build"][domain]["local_cov-C"][f"pose{pose}_lt{int(float(threshold))}"] = counts
    return data
