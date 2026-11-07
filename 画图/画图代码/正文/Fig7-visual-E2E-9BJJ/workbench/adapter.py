"""声明 Fig7/8 工作台的科学控件、会话绑定与主动显示命令.

bind 连接每图 case.json 与内嵌 scene, open_scene 绑定已载入模型, command 处理作者主动操作.
预算、过滤、Top-1/Top-5/best 解释见 selection.py; 显隐计划与状态文字见 display.py.
只读当前 CXS 与明确的 Fig7/8 配置, 不读取 scene.folder、D 盘旧加工材料或服务器文件.
"""

import json
from pathlib import Path

from chimerax.core.commands import run
from chimerax.core.errors import UserError
from .selection import DEFAULT as default_config, MANAGED as managed_kinds, VIEW_NAMES, FILTER_NAMES
from .display import visibility_plan as plan, report, presentation

ui_schema = {
    "initial_title": "先打开案例的 load.cxc 或初始会话",
    "controls": [
        {"key": "view", "label": "评估模式", "type": "choice", "choices": list(VIEW_NAMES.items()), "command": "view {value}"},
        {"key": "condition", "label": "预测采用的受体", "type": "choice", "choices": [("CA2", "CA2 · CryoAtom2 受体"), ("GT", "GT · 沉积受体")], "command": "condition {value}"},
        {"key": "budget", "label": "尝试预算", "type": "choice", "choices": [(x, x + "%" if x != "all" else "全部候选") for x in ["50", "100", "200", "300", "all"]], "command": "budget {value}"},
        {"key": "filter", "label": "画面过滤", "type": "choice", "choices": list(FILTER_NAMES.items()), "command": "filter {value}"},
        {"key": "pose", "label": "显示构象", "type": "choice", "choices": [("top1", "top-1 · 模型首选"), ("top5", "top-5 · 原评分前五中RMSD最小"), ("best", "best-of-50 · 原评价最优"), ("both", "同时显示两者")], "command": "pose {value}"},
        {"key": "identity", "label": "显示 Match 预测身份", "type": "check", "command": "labels identity {value}"},
        {"key": "correctness", "label": "显示 Match 正误标记", "type": "check", "command": "labels correctness {value}"},
    ],
    "reset": ("恢复预设显隐 · 保留颜色与视角", "reset"),
    "focused_buttons": [("聚焦所选配体", "focus"), ("只显示它周围 5 Å 口袋和 1.7 Å 密度", "pocket")],
    "buttons": [("回到本例初始总览 · 复原显隐", "home"), ("返回全局视角 · 保留显隐", "overview"), ("恢复完整实验密度", "unzone"), ("保存当前会话 · 自动另存新编号", "save"), ("导出当前图片 · 自动另存新编号", "export")],
    "note": "切换模式、受体或预算会取消手动显隐，按新选项显示。\n颜色、透明度、表示方式、视角和密度阈值保留。\n参考配体、受体和地图请在 Models 面板独立开关。",
}


def bind(scene):
    """显式绑定 Fig7/8 的 PDB 与出版条件, 返回标题、聚焦菜单和保存子目录名.

    case.json 的 pdb/receptor/condition/budget_percent/pose 记录每图输入条件, 不覆盖作者 CXS 当前 config、相机或显示.
    返回 title: str, focus: list[(显示名称, candidate_id)], output_name: str, case: 每图配置原字典.
    """
    main = Path(__file__).resolve().parents[2]
    cases = {"9bjj": main / "Fig7-visual-E2E-9BJJ/case.json", "9ujf": main / "Fig8-visual-E2E-9UJF/case.json"}
    pdb = scene["pdb_id"].lower()
    case = json.loads(cases[pdb].read_text(encoding="utf-8"))
    # 指向每图声明的同一科学适配器; 不从会话的历史 folder 寻找外部材料.
    root = main.parents[2]
    if case["pdb"] != pdb or (root / case["workbench_adapter"]).resolve() != Path(__file__).resolve():
        raise UserError("本图 case.json 的 PDB 或工作台适配器不一致")
    focus = [(f"{o['display_name']} · {o['site']} · 实例 {o['candidate_id']}", o["candidate_id"]) for o in scene["occurrences"]]
    return {"title": pdb.upper() + " · 多配体画图", "focus": focus, "output_name": pdb, "case": case}


def open_scene(session, path):
    """把明确 scene.json 的模型编号连接到当前已载入模型, 不加载或补造科学材料.

    返回 scene 与 refs: dict[模型 key, ChimeraX 模型]. scene.models[].id 是点分原模型编号, 如 4.2.1; key 与显隐选择逐项对齐.
    """
    scene = json.loads(Path(path).read_text(encoding="utf-8"))
    registered = {tuple(int(v) for v in m["id"].split(".")): m["key"] for m in scene["models"] if m["kind"] in managed_kinds}
    refs = {registered[m.id]: m for m in session.models.list() if m.id in registered}
    if len(refs) != len(registered):
        raise UserError("材料尚未完整载入, 请运行本案例 load.cxc")
    return scene, refs


# ================================================================================================
def command(tool, action, argument, value):
    """执行作者明确触发的科学控件或聚焦命令, 不能在恢复/刷新时隐式调用.

    tool 保存 config/overrides 与已载入模型引用. 预算仍按原 before 累计计费, Top-5 缺材料时报错, 不重新排名或读取外部文件.
    返回值仅用于 status 以外的日志; 所有图形命令显式留在 ChimeraX Log.
    """
    if action in ["view", "condition", "budget", "filter", "pose", "labels"]:
        key = argument if action == "labels" else action
        selected = value if action == "labels" else argument
        if key in ["identity", "correctness"]:
            if selected not in ["on", "off"]:
                raise UserError("标注使用 on 或 off")
            tool.config[key] = selected == "on"
            tool.apply({"identity", "correctness"})
            return
        allowed = {"view": set(VIEW_NAMES), "condition": {"CA2", "GT"}, "budget": {"50", "100", "200", "300", "all"}, "filter": set(FILTER_NAMES), "pose": {"top1", "top5", "best", "both"}}
        if selected not in allowed[key]:
            raise UserError(f"{key} 可选: " + ", ".join(sorted(allowed[key])))
        if key == "pose" and selected == "top5" and "top5" not in tool.scene.get("pose_modes", []):
            tool.refresh()
            raise UserError("当前会话没有Top-5材料; 请用正式服务器材料入口准备新会话, upgrade仅校对已内嵌材料")
        tool.config[key] = selected
        if key in ["view", "condition", "budget"]:
            tool.overrides.clear()
        elif key == "pose":
            pose_keys = {m["key"] for m in tool.scene["models"] if m["kind"] == "pose"}
            tool.overrides = {k: v for k, v in tool.overrides.items() if k not in pose_keys}
        tool.apply({"pose"} if key == "pose" else managed_kinds)
    elif action == "reset":
        tool.overrides.clear()
        tool.apply()
    elif action in ["focus", "pocket"]:
        target = f"#3.{int(argument) + 1}"
        receptor = "#1.2" if tool.config["condition"] == "CA2" else "#1.1"
        text = f"show {target} models; show {target} atoms; view {target} clip false; cofr {target}; zoom 0.75"
        if action == "pocket":
            text = f"hide #1 cartoons; hide #1 atoms; show {receptor} models; show {receptor}&({target}:<5) atoms; style {receptor} stick; show #2.1 models; volume #2.1 style mesh step 1; volume zone #2.1 nearAtoms {target} range 1.7 newMap false minimalBounds true; " + text
        run(tool.session, text, log=True)
    elif action == "overview":
        run(tool.session, "view overview; clip off", log=True)
    elif action == "home":
        tool.config = dict(default_config)
        tool.overrides.clear()
        tool.apply()
        text = "hide #1 models; hide #1 atoms; hide #1 cartoons; hide #1 surfaces; show #1.2 models; cartoon #1.2; show #3 models; show #3 atoms; style #3 stick; hide #2 models; show #4 models; hide "
        text += "|".join("#!" + m["id"] for m in tool.scene["models"] if m["kind"] == "area")
        run(tool.session, text + " models; hide #!4 models; view overview; clip off", log=True)
    elif action == "upgrade":
        available = {m.id_string for m in tool.session.models.list()}
        missing = [m["id"] for m in tool.scene["models"] if m["id"] not in available]
        tool.last = tool.actual()
        tool.refresh()
        tool.session.logger.info("已检查当前会话内嵌材料, 未读取外部清单或改变科学对象、配色、视角与显隐. " + ("当前未载入的登记对象: " + ", ".join(missing) + ". " if missing else "") + "新增实验材料须由正式服务器供应入口生成新会话.")
    elif action == "unzone":
        run(tool.session, "volume unzone #2.1; volume #2.1 region all; show #2.1 models", log=True)
    else:
        raise UserError("操作: view, condition, budget, filter, pose, labels, reset, focus, pocket, home, overview, upgrade, unzone, save, export, status")
