"""提供 Qt 工作台、模型观察与 CXS v1 状态恢复, 科学选择由显式项目适配器提供.

LigandWorkbench 是已有作者会话记录的类身份 chimerax.ligand_workbench.tool.LigandWorkbench, 必须保持.
attach(apply=False) 只接回模型引用与控件, 不执行显隐或相机命令; 只有明确命令才调用 apply.
snapshot 保留 version/scene/models/config/overrides/shown, scene 与 config 对工具而言是不解释的适配器状态.
"""

from chimerax.core.commands import run
from chimerax.core.models import MODEL_DISPLAY_CHANGED, REMOVE_MODELS
from chimerax.core.tools import ToolInstance
from chimerax.core.errors import UserError
from .adapter_loader import load_adapter
from .ui import build_panel, refresh_panel
from .session_io import save_output, write_status


class LigandWorkbench(ToolInstance):
    """观察模型实际显隐并保存作者覆盖, 不自行定义科学候选、预算或构象排名."""

    SESSION_SAVE = True
    help = "help:user/commands/ligwork.html"

    def __init__(self, session, tool_name):
        super().__init__(session, tool_name)
        self.adapter, self.paths = load_adapter()
        self.scene = None
        self.config = dict(self.adapter.default_config)
        self.overrides, self.models, self.last = {}, {}, {}
        self.binding = None
        self.busy = False
        self.handlers = []
        session._ligand_workbench = self
        if session.ui.is_gui:
            build_panel(self, self.adapter.ui_schema)

    def _command(self, text):
        """面板操作统一进入正式命令栏并留在 Log."""
        run(self.session, "ligwork " + text, log=True)

    def _button(self, action, focused, checked):
        """Qt 按钮回调; focused 只表示拼入当前菜单值, 不解释该值的领域意义."""
        self._command(action + (" " + str(self.focus_combo.currentData()) if focused else ""))

    def _ui_change(self, key, changed):
        """Qt 控件回调; busy 时不将刷新控件产生的信号转成实际显示操作."""
        if self.busy or self.scene is None:
            return
        field = next(f for f in self.adapter.ui_schema["controls"] if f["key"] == key)
        widget = self.controls[key]
        value = ("on" if widget.isChecked() else "off") if field["type"] == "check" else widget.currentData()
        self._command(field["command"].format(value=value))

    def attach(self, scene, model_refs, config, overrides, apply):
        """连接已载入模型与保存的作者状态; 恢复 apply=False, 保留实际显示与相机.

        model_refs: dict[适配器模型 key, ChimeraX 模型]; config/overrides 原样复制; binding 只为标题、菜单和输出名称.
        """
        self.binding = self.adapter.bind(scene)
        self.scene, self.models = scene, model_refs
        self.config, self.overrides = dict(config), dict(overrides)
        self.handlers.append(self.session.triggers.add_handler(MODEL_DISPLAY_CHANGED, self._observe))
        self.handlers.append(self.session.triggers.add_handler(REMOVE_MODELS, self._observe))
        if self.session.ui.is_gui:
            self.focus_combo.clear()
            for label, value in self.binding["focus"]:
                self.focus_combo.addItem(label, value)
            self.title_label.setText(self.binding["title"])
        self.last = self.actual()
        if apply:
            self.apply()
        else:
            self.refresh()

    def actual(self):
        """返回模型 key 到实际可见布尔值的字典; visible 包括父组显隐, 不评价原子表示方式."""
        return {key: bool(model.visible) for key, model in self.models.items() if not model.deleted}

    def _observe(self, event, changed):
        """模型显示/删除触发器, 将作者手动显隐记为覆盖, 不运行任何图形命令."""
        if self.busy or self.scene is None:
            return
        current = self.actual()
        for key, value in current.items():
            if self.last.get(key) != value:
                self.overrides[key] = value
        self.last = current
        self.refresh()

    def apply(self, kinds=None):
        """执行适配器显式给出的显隐计划; 不改变颜色、原子表示、体素、坐标或相机.

        kinds=None 为会话兼容的完整操作, 实际类别由适配器 managed_kinds 给出; 局部类别由科学控件显式传入.
        """
        kinds = self.adapter.managed_kinds if kinds is None else kinds
        wanted, affected = self.adapter.plan(self.scene, self.config, self.overrides, self.actual(), tuple(self.models), kinds)
        roots = sorted({str(self.models[key].id[0]) for key in affected if not self.models[key].deleted})
        self.busy = True
        try:
            if roots:
                run(self.session, "hide " + "|".join("#" + value for value in roots) + " models", log=True)
            ids = ["#" + self.models[key].id_string for key in affected if not self.models[key].deleted and wanted[key]]
            if ids:
                run(self.session, "show " + "|".join(ids) + " models", log=True)
        finally:
            self.busy = False
        self.last = self.actual()
        self.refresh()

    def report(self):
        """返回科学适配器对实际显示的解释, 工具不改写其字段或重算统计."""
        return self.adapter.report(self.scene, self.config, self.overrides, self.actual())

    def refresh(self):
        """只刷新 GUI; 恢复会话、观察手动编辑及状态查询均不得由此改变显示."""
        if not self.session.ui.is_gui or self.scene is None:
            return
        state = self.adapter.presentation(self.scene, self.config, self.report())
        self.busy = True
        try:
            refresh_panel(self, state)
        finally:
            self.busy = False

    def take_snapshot(self, session, flags):
        """ChimeraX 固定保存协议; 保持作者 CXS 的 v1 字段和模型引用, 不另写科学清单."""
        return {"version": 1, "scene": self.scene, "models": self.models, "config": self.config, "overrides": self.overrides, "shown": self.tool_window.shown if session.ui.is_gui else False}

    @classmethod
    def restore_snapshot(cls, session, data):
        """ChimeraX 固定恢复协议; attach=False 防止应用预设覆盖作者保存的实际显示."""
        tool = cls(session, "Ligand Workbench")
        if data["scene"] is not None:
            tool.attach(data["scene"], data["models"], data["config"], data["overrides"], False)
        if session.ui.is_gui:
            tool.display(data["shown"])
        return tool

    def delete(self):
        """ChimeraX 固定销毁协议; 只注销本工具监听器, 不删除模型或磁盘资产."""
        for handler in self.handlers:
            handler.remove()
        self.handlers = []
        if getattr(self.session, "_ligand_workbench", None) is self:
            self.session._ligand_workbench = None
        super().delete()


# ================================================================================================
def workbench_command(session, action, argument="", value=""):
    """ChimeraX 命令入口; 通用开关/另存/状态留在工具, 科学操作统一交给项目适配器.

    argument/value 默认空字符串来自原已注册命令接口, 保持旧 CXS 对应版本和作者命令习惯.
    """
    tool = getattr(session, "_ligand_workbench", None)
    argument = argument.strip().strip('"')
    if action == "clear":
        if tool is not None:
            tool.delete()
        return
    if action == "open":
        if tool is not None:
            tool.delete()
        tool = LigandWorkbench(session, "Ligand Workbench")
        scene, refs = tool.adapter.open_scene(session, argument)
        tool.attach(scene, refs, tool.adapter.default_config, {}, True)
        if session.ui.is_gui:
            tool.display(True)
        return
    if tool is None or tool.scene is None:
        raise UserError("请先打开一个案例的 load.cxc 或工作会话")
    if action == "show":
        tool.display(True)
    elif action in ["save", "export"]:
        return save_output(tool, action)
    elif action == "status":
        return write_status(tool, argument, tool.report())
    else:
        return tool.adapter.command(tool, action, argument, value)
