"""按完整身份Match回答决定候选计费, 不改变原候选顺序或姿态指标.

accounting_action定义背景、范围外前景和合格目标的动作. reaccount把此规则应用到原完整轨迹, 仅改变计费号与全身份答案; docking_stage和methods仍来自同一次原姿态评价. localization_counts为假定身份正确的定位诊断, 不挪用实际Match计费.
"""

import copy

RULE = "match-aware-stage3-v2"


def accounting_action(candidate, predicted_smiles, predicted_category):
    """按用户确认的真实归属与 Match 输出确定单个 blob 的计费动作.

    输入参数:
        - candidate: dict, target_scope 为 background/non_stage3_foreground/stage3_foreground, target_category 为原类别, target_smiles 为目标精确字符串.
        - predicted_smiles: str, 对当前 PDB 全身份范围取 argmax 后得到的精确 SMILES.
        - predicted_category: str, predicted_smiles 在冻结身份清单中的原类别, 如 small_molecule 或 ion.
    返回值:
        - action: str, charge_ 开头表示消耗一次, skip_ 开头表示免费跳过; Stage3 合格目标即使被预测成非小分子也计费.
    """
    if candidate["target_scope"] == "background":
        return "charge_background"
    if candidate["target_category"] != "small_molecule":
        return "charge_non_small_as_small" if predicted_category == "small_molecule" else "skip_non_small_prediction"
    if candidate["target_scope"] == "non_stage3_foreground":
        return (
            "skip_correct_small_outside_stage3"
            if predicted_smiles == candidate["target_smiles"]
            else "charge_wrong_small_outside_stage3"
        )
    return "charge_stage3"


def localization_counts(traces, limits):
    """返回各给定K内至少定位一个合格实例的PDB数, 真实范围外前景免费.

    traces: dict[PDB,list[dict]], 原候选顺序, target_scope为background/non_stage3_foreground/stage3_foreground. limits: tuple[int,...], 当前图所需K, 如1到10. 背景和合格实例计费, 其余前景跳过; 保留零候选PDB完整分母.
    """
    first = []
    for items in traces.values():
        spent = 0
        hit = None
        for item in items:
            if item["target_scope"] == "non_stage3_foreground":
                continue
            spent += 1
            if item["target_scope"] == "stage3_foreground" and hit is None:
                hit = spent
        first.append(hit)
    return [sum(step is not None and step <= limit for step in first) for limit in limits]


# ================================================================================================
def reaccount(condition, candidates, full_predictions, identities, small, original, direct):
    """在原候选顺序上恢复全身份计费及对应逐候选姿态记录.

    condition: str, real_receptor或cryoatom2_receptor. candidates: list[dict], 冻结77-PDB全部原blob与target_scope. full_predictions: dict[PDB,list[dict]], 全身份argmax答案. identities: dict[(PDB,SMILES),str], 精确身份类别. small: dict, 原小分子测试的source_probability_mean轨迹. original: dict, 原实际姿态evaluation, 只读取traces的docking_stage. direct: list[dict], 同一实际实验的原逐blob姿态指标. 不写服务器或计算未请求的四方法整组汇总.

    返回值:
        - traces: dict[PDB,list[dict]], 保留77-PDB全部候选与原顺序, 以PDB+source_blob_index连接原blob, 不按新的计费号删去免费项.
            - previous_attempt_index/previous_action: 原small轨迹的attempt_index/action, 原样保留以说明该候选改前的计费记录.
            - attempt_index/action: 本次全身份重计费的1基次数与动作, 如2/charge_stage3; 免费跳过时attempt_index为None, action以skip_开头.
            - predicted_smiles/predicted_category: 全身份argmax的精确字符串及其原类别, 替换原小分子轨迹中的答案.
            - identity_correct: bool, 预测SMILES与原目标精确字符串相同.
            - success: bool, 只要求Stage3合格目标且identity_correct为True, 不表示构象RMSD过阈值.
            - docking_stage: 原实际evaluation的同序候选姿态记录, methods内保留原status、pose_min_rmsd_A和success阈值结果; 没有原直接姿态记录时为required=False及本次action原因.
        - direct: list[dict], 与输入direct的原逐blob记录顺序相同, 原methods姿态指标不变; previous_attempt_index保留该直接记录改前的计费号, attempt_index与predicted_smiles替换为同一blob的新轨迹值.
    """
    candidate_by_key = {(r["pdb_id"], r["source_blob_index"]): r for r in candidates}
    predicted_by_key = {(pdb, r["source_blob_index"]): r for pdb, items in full_predictions.items() for r in items}
    small_by_key = {(r["pdb_id"], r["source_blob_index"]): r for r in small["predictions"][condition]}
    assert all(
        predicted_by_key[key]["predicted_smiles"] == r["predicted_smiles_all_ligand"] for key, r in small_by_key.items()
    )
    source = small["traces"]["source_probability_mean"][condition]["small_molecule"]
    direct_by_key = {(r["pdb_id"], r["source_blob_index"]): r for r in direct}
    traces = {}
    for pdb, items in source.items():
        spent = 0
        records = []
        for item in items:
            key = (pdb, item["source_blob_index"])
            candidate = candidate_by_key[key]
            prediction = predicted_by_key[key]
            assert all(
                candidate[field] == prediction[field]
                for field in ("centered_box_index", "matched_occurrence_id", "target_smiles", "candidate_selected")
            )
            predicted = prediction["predicted_smiles"]
            category = identities[pdb, predicted]
            action = accounting_action(candidate, predicted, category)
            if action.startswith("charge_"):
                spent += 1
            # 新计费号为1基int, 免费跳过为None; 原item的计费号和动作写入previous_*保留.
            attempt = spent if action.startswith("charge_") else None
            correct = predicted == candidate["target_smiles"]
            # bool, 这里只判断合格目标+精确身份; 原构象成功与RMSD阈值仍在docking_stage.methods内.
            success = candidate["target_scope"] == "stage3_foreground" and correct
            docking = (
                copy.deepcopy(original["traces"][pdb][len(records)]["docking_stage"])
                if key in direct_by_key
                else {"required": False, "reason": action}
            )
            if success:
                assert key in direct_by_key, f"冻结姿态未覆盖身份正确候选: {key}"
            records.append(
                {
                    **item,
                    "previous_attempt_index": item["attempt_index"],
                    "previous_action": item["action"],
                    "attempt_index": attempt,
                    "action": action,
                    "candidate_selected": candidate["candidate_selected"],
                    "target_category": candidate["target_category"],
                    "predicted_smiles": predicted,
                    "predicted_category": category,
                    "identity_correct": correct,
                    "success": success,
                    "docking_stage": docking,
                }
            )
        traces[pdb] = records
    by_key = {(pdb, r["source_blob_index"]): r for pdb, items in traces.items() for r in items}
    new_direct = []
    for original_record in direct:
        record = copy.deepcopy(original_record)
        trace = by_key[record["pdb_id"], record["source_blob_index"]]
        # previous_attempt_index来自该原直接姿态记录, methods保持原值, 只转接同blob的新计费号和身份.
        record.update(
            previous_attempt_index=record["attempt_index"],
            attempt_index=trace["attempt_index"],
            predicted_smiles=trace["predicted_smiles"],
        )
        new_direct.append(record)
    return {"traces": traces, "direct": new_direct}
