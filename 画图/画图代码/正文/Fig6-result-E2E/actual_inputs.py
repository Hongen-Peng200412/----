"""只读取实际全身份Find-Match-Build所需原件, 与受控正确身份实验分开."""

from pathlib import Path
from TOOLS.runtime.paths import load_module

ACCOUNTING = load_module(Path(__file__).with_name("accounting.py"), "fig6_accounting")


# ================================================================================================
def read_actual(store, full, identities):
    """返回GT/CA2重计费轨迹与原姿态记录, 不汇总未使用方法或K.

    store: SourceStore, 本次读取. full: dict, 原frozen_test.json, predictions按real_receptor/cryoatom2_receptor和PDB分组. identities: dict[(PDB,SMILES),str], 原完整身份类别. 返回dict[GT/CA2,dict], 每项traces含完整77-PDB候选, direct含原正确身份姿态请求, 以PDB+source_blob_index连接.
    """
    # 原件 /storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/strongest-1/train_strongest1_revised_job378587_20260920T230727/evaluation.json, traces.source_probability_mean保存原selected优先的完整候选顺序; predictions中的predicted_smiles_all_ligand是完整身份argmax.
    # 生产说明 /home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md; 本地 C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md.
    small = store.json(
        "/storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/strongest-1/train_strongest1_revised_job378587_20260920T230727/evaluation.json"
    )
    result = {}
    for domain, condition, filename in [
        ("GT", "real_receptor", "real_candidates"),
        ("CA2", "cryoatom2_receptor", "cryoatom2_candidates"),
    ]:
        # 原件 /storage/penghongen/Matcher/manifests/test_smallmolecule_v1/real_candidates.jsonl 与 cryoatom2_candidates.jsonl; target_scope声明真实Stage3资格, target_category如ion, target_smiles为PDB内精确字符串, source_blob_index如11是原blob编号.
        candidates = store.json("/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/" + filename + ".jsonl")
        # 原件根 /storage/penghongen/PocketXMol/final_evaluation/end_to_end/GT 和 /storage/penghongen/PocketXMol/final_evaluation/end_to_end/CA2; 两根各读取evaluation.json与docking_results.jsonl; evaluation.traces保留原docking_stage, direct.methods.local_cov-C为第一轮DG Centre原姿态, pose_min_rmsd_A['5']是原排名前5的最低重原子RMSD Å, null保持无有效姿态, status如success.
        # 原实际程序 /home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/scripts/evaluate_end_to_end.py; 原生产说明为该release的 /home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/scripts/README.md, 本地 C:/Users/15919/Desktop/PocketXMol/scripts/README.md.
        root = "/storage/penghongen/PocketXMol/final_evaluation/end_to_end/" + domain
        evaluation = store.json(root + "/evaluation.json")
        direct = store.json(root + "/docking_results.jsonl")
        result[domain] = ACCOUNTING.reaccount(
            condition, candidates, full["predictions"][condition], identities, small, evaluation, direct
        )
    return result
