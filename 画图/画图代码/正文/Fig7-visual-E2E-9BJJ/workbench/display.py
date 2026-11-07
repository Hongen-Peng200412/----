"""把 E2E 科学选择转换为显隐计划与人读状态, 不执行 ChimeraX 命令.

visibility_plan 输出 wanted 模型显隐字典与 affected 模型 key 列表; report 解释实际显示与预设的差异; presentation 返回面板文本和控件可用状态.
所有输入均来自已打开 CXS 的 scene/config/模型引用, 不读取科学文件, 不改变原子坐标、排名或预算.
"""

from .selection import MANAGED, candidate_passes, selected_keys


def visibility_plan(scene, config, overrides, actual, model_keys, kinds):
    """形成显隐操作计划, 保留作者覆盖并防止标签重新打开手动隐藏的 blob.

    overrides/actual 为模型 key 到布尔值的字典; kinds 是本次允许修改的模型类别, 如 {pose} 只切换构象.
    返回 wanted: dict[str, bool] 与 affected: list[str], 后者只含 kinds 指定类别, 顺序沿用当前模型引用.
    """
    expected = selected_keys(scene, config)
    wanted = {k: k in expected for k in model_keys}
    # (受体条件, 原始 blob 编号) 定位候选; 不是对候选重新紧凑编号.
    candidates = {(d, r["source_blob_index"]): r for d, v in scene["domains"].items() for r in v["candidates"]}
    info = {m["key"]: m for m in scene["models"] if m["kind"] in MANAGED}
    for key, value in overrides.items():
        if key in wanted:
            wanted[key] = value
    for key, m in info.items():
        if not candidate_passes(candidates[(m["domain"], m["blob"])], config["filter"]):
            wanted[key] = False
        if m["kind"] in ["identity", "correctness"]:
            blobkey = f"{m['domain']}_blob_{m['blob']}"
            visible = wanted[blobkey] if "blob" in kinds else actual.get(blobkey, False)
            wanted[key] = wanted[key] and visible
    return wanted, [k for k in model_keys if info[k]["kind"] in kinds]


def report(scene, config, overrides, actual):
    """解释实际可见集合, 不把保存的显示选择当成重新评价的科学结果.

    返回 pdb_id/config/status, extra/hidden/visible 模型 key 列表, manual_overrides 显隐字典.
    build_states 每项含 blob 原始编号、predicted_smiles、原 actual_build.status/failure_reason; 仅 pipeline 显示的 blob 才列出.
    rmsd_unavailable_top1 是有 note 的可见构象 key 列表, 表示原会话缺参考 RMSD 时显示 Top-1, 不在此补算.
    """
    expected = selected_keys(scene, config)
    visible = {k for k, value in actual.items() if value}
    missing, extra = sorted(expected - visible), sorted(visible - expected)
    visible_blobs = {m["blob"] for m in scene["models"] if m["kind"] == "blob" and m["key"] in visible and m["domain"] == config["condition"]}
    build_states = [
        {"blob": r["source_blob_index"], "predicted_smiles": r["predicted_smiles"], "status": r["actual_build"]["status"], "failure_reason": r["actual_build"]["failure_reason"]}
        for r in scene["domains"][config["condition"]]["candidates"]
        if config["view"] == "pipeline" and r["source_blob_index"] in visible_blobs and r.get("actual_build") is not None
    ]
    fallback = [m["key"] for m in scene["models"] if m["kind"] == "pose" and m["key"] in visible and m.get("note")]
    return {"pdb_id": scene["pdb_id"], "config": dict(config), "status": "与预设一致" if not missing and not extra else "含手动显隐调整", "extra": extra, "hidden": missing, "visible": sorted(visible), "manual_overrides": dict(overrides), "build_states": build_states, "rmsd_unavailable_top1": fallback}


def presentation(scene, config, data):
    """返回通用面板需要的 values/enabled/text/color, 科学含义在本图中生成.

    values 沿用作者 config; enabled 按当前模式启用构象与标注; text 解释 blob/构象数和原 Build 失败原因; color 表示与预设是否一致.
    """
    visible = set(data["visible"])
    nblob = sum(m["kind"] == "blob" and m["key"] in visible for m in scene["models"])
    npose = sum(m["kind"] == "pose" and m["key"] in visible for m in scene["models"])
    text = f"显示状态：{data['status']}\n当前显示 {nblob} 个 blob、{npose} 个构象\n额外显示 {len(data['extra'])} 项；手动或父组隐藏 {len(data['hidden'])} 项"
    text += f"\n评价预算目标仍为 {scene['counts']['eligible']} 个合格小分子；画面包含实际输出" if config["view"] == "pipeline" else ""
    text += f"\n无可用参考 RMSD；{len(data['rmsd_unavailable_top1'])} 个构象显示 Top-1" if data["rmsd_unavailable_top1"] else ""
    text += "".join(f"\nblob {r['blob']}：Build {r['status']}；{r['failure_reason']}" for r in data["build_states"] if r["failure_reason"])
    return {"values": config, "enabled": {"pose": config["view"] in ["find_build", "pipeline"], "identity": config["view"] in ["find_match", "pipeline"], "correctness": config["view"] in ["find_match", "pipeline"]}, "text": text, "color": "#20764d" if data["status"] == "与预设一致" else "#a45827"}
