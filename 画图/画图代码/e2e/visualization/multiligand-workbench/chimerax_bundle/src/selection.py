"""从冻结的候选计费号选择显示材料. 不重算 Find 对应、Match 身份或姿态排名.

selected_keys 返回 scene.models 中应显示的 key 集合. 过滤在预算确定后执行, 因此不会补入更后面的候选.
candidate_passes 只读真实实例类别, 用于整组过滤 blob、姿态和专属标注.
"""

MANAGED = {"blob", "pose", "identity", "correctness"}
VIEW_NAMES = {
    "find_all": "Find · 全配体",
    "find_small": "Find · 小分子",
    "find_match": "Find+Match · 全配体",
    "find_build": "Find+Build · 合格小分子（给定正确配体）",
    "pipeline": "Find+Match+Build · 合格小分子",
}
FILTER_NAMES = {"all": "无过滤", "foreground": "排除假阳性", "small": "仅小分子", "eligible": "仅合格小分子"}
DEFAULT = {
    "view": "find_match",
    "condition": "CA2",
    "budget": "100",
    "filter": "all",
    "pose": "top1",
    "identity": False,
    "correctness": False,
}


def candidate_passes(candidate, filter_name):
    """按原 30% 双向覆盖的对应关系及真实实例类型判断; 假阳性没有真实类别."""
    return (
        filter_name == "all"
        or (filter_name == "foreground" and candidate["foreground_target"])
        or (filter_name == "small" and candidate["is_small"])
        or (filter_name == "eligible" and candidate["is_eligible"])
    )


def selected_keys(scene, config):
    """返回当前配置所需的材料 key 集合; 预算百分比乘对应实例数向下取整, all 表示全部候选."""
    domain = config["condition"]
    view = config["view"]
    count = scene["counts"][
        "all" if view in ["find_all", "find_match"] else "small" if view == "find_small" else "eligible"
    ]
    budget = float("inf") if config["budget"] == "all" else int(config["budget"]) * count // 100
    allowed = {
        r["source_blob_index"]
        for r in scene["domains"][domain]["candidates"]
        if (config["budget"] == "all" or r["before"][view] < budget) and candidate_passes(r, config["filter"])
    }
    shown = set()
    for m in scene["models"]:
        if m["kind"] not in MANAGED or m["domain"] != domain or m["blob"] not in allowed:
            continue
        if m["kind"] == "blob":
            shown.add(m["key"])
        elif (
            m["kind"] == "pose"
            and view in m["views"]
            and (config["pose"] == "both" or m["pose"] == config["pose"])
        ):
            shown.add(m["key"])
        elif (
            m["kind"] in ["identity", "correctness"]
            and view in ["find_match", "pipeline"]
            and config[m["kind"]]
        ):
            shown.add(m["key"])
    return shown
