"""提供中文操作面板, 记录手动显隐, 随 CXS 保存并恢复当前编辑状态.

本文件只通过 chimerax.core.commands.run 执行显示、相机、局部密度与导出. 模型 API 仅用于读取
对象显隐和监听变化. take_snapshot/restore_snapshot/delete 是官方工具协议, 不承担科学选择.
"""

import json
from pathlib import Path

from chimerax.core.commands import run
from chimerax.core.models import MODEL_DISPLAY_CHANGED, REMOVE_MODELS
from chimerax.core.tools import ToolInstance
from chimerax.core.errors import UserError
from .selection import DEFAULT, MANAGED, VIEW_NAMES, FILTER_NAMES, selected_keys, candidate_passes


class LigandWorkbench(ToolInstance):
    SESSION_SAVE = True
    help = "help:user/commands/ligwork.html"

    def __init__(self, session, tool_name):
        super().__init__(session, tool_name)
        self.scene = None
        self.config = dict(DEFAULT)
        self.overrides = {}
        self.models = {}
        self.last = {}
        self.busy = False
        self.handlers = []
        session._ligand_workbench = self
        if session.ui.is_gui:
            from chimerax.ui import MainToolWindow
            from Qt.QtWidgets import (
                QVBoxLayout,
                QFormLayout,
                QComboBox,
                QLabel,
                QCheckBox,
                QPushButton,
                QHBoxLayout,
            )

            self.tool_window = MainToolWindow(self, close_destroys=False)
            layout = QVBoxLayout(self.tool_window.ui_area)
            self.title_label = QLabel("先打开案例的 load.cxc 或初始会话")
            layout.addWidget(self.title_label)
            form = QFormLayout()
            layout.addLayout(form)
            self.controls = {}
            options = [
                ("view", "评估模式", list(VIEW_NAMES.items())),
                (
                    "condition",
                    "预测采用的受体",
                    [("CA2", "CA2 · CryoAtom2 受体"), ("GT", "GT · 沉积受体")],
                ),
                (
                    "budget",
                    "尝试预算",
                    [
                        (x, x + "%" if x != "all" else "全部候选")
                        for x in ["50", "100", "200", "300", "all"]
                    ],
                ),
                ("filter", "画面过滤", list(FILTER_NAMES.items())),
                (
                    "pose",
                    "显示构象",
                    [
                        ("top1", "top-1 · 模型首选"),
                        ("best", "best-of-50 · 原评价最优"),
                        ("both", "同时显示两者"),
                    ],
                ),
            ]
            for key, title, values in options:
                combo = QComboBox()
                for value, text in values:
                    combo.addItem(text, value)
                combo.currentIndexChanged.connect(lambda _, k=key: self._ui_change(k))
                self.controls[key] = combo
                form.addRow(title, combo)
            for key, text in [
                ("identity", "显示 Match 预测身份"),
                ("correctness", "显示 Match 正误标记"),
            ]:
                check = QCheckBox(text)
                check.toggled.connect(lambda _, k=key: self._ui_change(k))
                self.controls[key] = check
                layout.addWidget(check)
            self.status_label = QLabel("尚未载入案例")
            self.status_label.setWordWrap(True)
            layout.addWidget(self.status_label)
            button = QPushButton("恢复预设显隐 · 保留颜色与视角")
            button.clicked.connect(lambda: self._command("reset"))
            layout.addWidget(button)
            self.focus_combo = QComboBox()
            layout.addWidget(self.focus_combo)
            for text, action in [
                ("聚焦所选配体", "focus"),
                ("只显示它周围 5 Å 口袋和 1.7 Å 密度", "pocket"),
            ]:
                button = QPushButton(text)
                button.clicked.connect(
                    lambda _, a=action: self._command(a + " " + str(self.focus_combo.currentData()))
                )
                layout.addWidget(button)
            for text, action in [
                ("回到本例初始总览 · 复原显隐", "home"),
                ("返回全局视角 · 保留显隐", "overview"),
                ("恢复完整实验密度", "unzone"),
                ("保存当前会话 · 自动另存新编号", "save"),
                ("导出当前图片 · 自动另存新编号", "export"),
            ]:
                button = QPushButton(text)
                button.clicked.connect(lambda _, a=action: self._command(a))
                layout.addWidget(button)
            self.note_label = QLabel(
                "切换模式、受体或预算会取消手动显隐，按新选项显示。\n颜色、透明度、表示方式、视角和密度阈值保留。\n参考配体、受体和地图请在 Models 面板独立开关。"
            )
            self.note_label.setWordWrap(True)
            layout.addWidget(self.note_label)
            layout.addStretch(1)
            self.tool_window.manage("side")

    def _command(self, text):
        """面板按钮与命令栏使用同一个 ligwork 命令入口, 操作留在 Log."""
        run(self.session, "ligwork " + text, log=True)

    def _ui_change(self, key):
        if self.busy or self.scene is None:
            return
        widget = self.controls[key]
        value = (
            ("on" if widget.isChecked() else "off")
            if key in ["identity", "correctness"]
            else widget.currentData()
        )
        self._command(
            ("labels " + key + " " + value)
            if key in ["identity", "correctness"]
            else key + " " + str(value)
        )

    def attach(self, scene, model_refs, config, overrides, apply):
        """连接已由原生命令载入的材料. 会话恢复 apply=False, 保持实际保存的显隐与外观."""
        self.scene = scene
        self.models = model_refs
        self.config = dict(config)
        self.overrides = dict(overrides)
        self.handlers.append(
            self.session.triggers.add_handler(MODEL_DISPLAY_CHANGED, self._observe)
        )
        self.handlers.append(self.session.triggers.add_handler(REMOVE_MODELS, self._observe))
        if self.session.ui.is_gui:
            self.focus_combo.clear()
            for o in scene["occurrences"]:
                self.focus_combo.addItem(
                    f"{o['display_name']} · {o['site']} · 实例 {o['candidate_id']}",
                    o["candidate_id"],
                )
            self.title_label.setText(scene["pdb_id"].upper() + " · 多配体画图")
        self.last = self.actual()
        if apply:
            self.apply()
        else:
            self.refresh()

    def actual(self):
        """读取登记模型及父组共同决定的显隐; 原子表示方式不属于这项状态检查."""
        return {k: bool(m.visible) for k, m in self.models.items() if not m.deleted}

    def _observe(self, event, changed):
        if self.busy or self.scene is None:
            return
        current = self.actual()
        for key, value in current.items():
            if self.last.get(key) != value:
                self.overrides[key] = value
        self.last = current
        self.refresh()

    def apply(self, kinds=MANAGED):
        """执行当前显隐配置. 过滤保留人工隐藏; 标签开关只改标签, 不重新显示隐藏的 blob."""
        expected = selected_keys(self.scene, self.config)
        wanted = {k: k in expected for k in self.models}
        candidates = {
            (d, r["source_blob_index"]): r
            for d, v in self.scene["domains"].items()
            for r in v["candidates"]
        }
        info = {m["key"]: m for m in self.scene["models"] if m["kind"] in MANAGED}
        for key, value in self.overrides.items():
            if key in wanted:
                wanted[key] = value
        for key, m in info.items():
            if not candidate_passes(candidates[(m["domain"], m["blob"])], self.config["filter"]):
                wanted[key] = False
            if m["kind"] in ["identity", "correctness"]:
                blobkey = f"{m['domain']}_blob_{m['blob']}"
                # 只对实际可见的 blob 开标注, 避免标签按钮重新打开手动关闭的候选.
                visible = wanted[blobkey] if "blob" in kinds else self.actual().get(blobkey, False)
                wanted[key] = wanted[key] and visible
        affected = [k for k in self.models if info[k]["kind"] in kinds]
        roots = sorted({str(self.models[k].id[0]) for k in affected if not self.models[k].deleted})
        self.busy = True
        try:
            if roots:
                # 先关整组, 再开需要的叶对象; show 会自动开启祖先组.
                # 避免短暂打开全部构象和标签, 也缩短 Log 中的对象清单.
                run(
                    self.session, "hide " + ("|".join("#" + x for x in roots)) + " models", log=True
                )
            ids = [
                "#" + self.models[k].id_string
                for k in affected
                if not self.models[k].deleted and wanted[k]
            ]
            if ids:
                run(self.session, "show " + "|".join(ids) + " models", log=True)
        finally:
            self.busy = False
        self.last = self.actual()
        self.refresh()

    def set_option(self, key, value):
        if key in ["identity", "correctness"]:
            if value not in ["on", "off"]:
                raise UserError("标注使用 on 或 off")
            self.config[key] = value == "on"
            self.apply({"identity", "correctness"})
            return
        allowed = {
            "view": set(VIEW_NAMES),
            "condition": {"CA2", "GT"},
            "budget": {"50", "100", "200", "300", "all"},
            "filter": set(FILTER_NAMES),
            "pose": {"top1", "best", "both"},
        }
        if value not in allowed[key]:
            raise UserError(f"{key} 可选: " + ", ".join(sorted(allowed[key])))
        self.config[key] = value
        if key in ["view", "condition", "budget"]:
            self.overrides.clear()
        elif key == "pose":
            # 用户主动选择构象档位时只重设构象, 保留 blob 与标签的独立手动显隐.
            pose_keys = {m["key"] for m in self.scene["models"] if m["kind"] == "pose"}
            self.overrides = {k: v for k, v in self.overrides.items() if k not in pose_keys}
        self.apply({"pose"} if key == "pose" else MANAGED)

    def report(self):
        expected = selected_keys(self.scene, self.config)
        actual = {k for k, v in self.actual().items() if v}
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        return {
            "pdb_id": self.scene["pdb_id"],
            "config": dict(self.config),
            "status": "与预设一致" if not missing and not extra else "含手动显隐调整",
            "extra": extra,
            "hidden": missing,
            "visible": sorted(actual),
            "manual_overrides": dict(self.overrides),
        }

    def refresh(self):
        if not self.session.ui.is_gui or self.scene is None:
            return
        data = self.report()
        self.busy = True
        try:
            for key, widget in self.controls.items():
                if key in ["identity", "correctness"]:
                    widget.setChecked(self.config[key])
                else:
                    widget.setCurrentIndex(widget.findData(self.config[key]))
            build = self.config["view"] in ["find_build", "pipeline"]
            match = self.config["view"] in ["find_match", "pipeline"]
            self.controls["pose"].setEnabled(build)
            for key in ["identity", "correctness"]:
                self.controls[key].setEnabled(match)
            visible = set(data["visible"])
            nblob = sum(m["kind"] == "blob" and m["key"] in visible for m in self.scene["models"])
            npose = sum(m["kind"] == "pose" and m["key"] in visible for m in self.scene["models"])
            self.status_label.setText(
                f"显示状态：{data['status']}\n当前显示 {nblob} 个 blob、{npose} 个构象\n额外显示 {len(data['extra'])} 项；手动或父组隐藏 {len(data['hidden'])} 项"
            )
            self.status_label.setStyleSheet(
                "color: " + ("#20764d" if data["status"] == "与预设一致" else "#a45827")
            )
        finally:
            self.busy = False

    def take_snapshot(self, session, flags):
        return {
            "version": 1,
            "scene": self.scene,
            "models": self.models,
            "config": self.config,
            "overrides": self.overrides,
            "shown": self.tool_window.shown if session.ui.is_gui else False,
        }

    @classmethod
    def restore_snapshot(cls, session, data):
        tool = cls(session, "Ligand Workbench")
        if data["scene"] is not None:
            tool.attach(data["scene"], data["models"], data["config"], data["overrides"], False)
        if session.ui.is_gui:
            tool.display(data["shown"])
        return tool

    def delete(self):
        for handler in self.handlers:
            handler.remove()
        self.handlers = []
        if getattr(self.session, "_ligand_workbench", None) is self:
            self.session._ligand_workbench = None
        super().delete()


# ================================================================================================
def workbench_command(session, action, argument="", value=""):
    """统一命令入口. 新功能通过官方命令实现; status 可写 JSON 用于追溯实际显示集合."""
    tool = getattr(session, "_ligand_workbench", None)
    argument = argument.strip().strip('"')
    if action == "clear":
        if tool is not None:
            tool.delete()
        return
    if action == "open":
        if tool is not None:
            tool.delete()
        scene = json.loads(Path(argument).read_text(encoding="utf-8"))
        tool = LigandWorkbench(session, "Ligand Workbench")
        registered = {
            tuple(int(v) for v in m["id"].split(".")): m["key"]
            for m in scene["models"]
            if m["kind"] in MANAGED
        }
        refs = {registered[m.id]: m for m in session.models.list() if m.id in registered}
        if len(refs) != len(registered):
            raise UserError("材料尚未完整载入, 请运行本案例 load.cxc")
        tool.attach(scene, refs, DEFAULT, {}, True)
        if session.ui.is_gui:
            tool.display(True)
        return
    if tool is None or tool.scene is None:
        raise UserError("请先打开一个案例的 load.cxc 或工作会话")
    if action in ["view", "condition", "budget", "filter", "pose"]:
        tool.set_option(action, argument)
    elif action == "labels":
        tool.set_option(argument, value)
    elif action == "reset":
        tool.overrides.clear()
        tool.apply()
    elif action == "show":
        tool.display(True)
    elif action in ["focus", "pocket"]:
        oid = int(argument)
        target = f"#3.{oid+1}"
        domain = tool.config["condition"]
        receptor = "#1.2" if domain == "CA2" else "#1.1"
        command = f"show {target} models; show {target} atoms; view {target} clip false; cofr {target}; zoom 0.75"
        if action == "pocket":
            command = (
                f"hide #1 cartoons; hide #1 atoms; show {receptor} models; show {receptor}&({target}:<5) atoms; style {receptor} stick; show #2.1 models; volume #2.1 style mesh step 1; volume zone #2.1 nearAtoms {target} range 1.7 newMap false minimalBounds true; "
                + command
            )
        run(session, command, log=True)
    elif action == "overview":
        # 旧会话的命名视角可能记录了裁剪平面, 返回后明确解除, 避免再次切掉模型.
        run(session, "view overview; clip off", log=True)
    elif action == "home":
        # 初始总览是一条主动恢复命令, 不参与状态栏自动观察; 不重新载入材料或读取会话文件.
        tool.config = dict(DEFAULT)
        tool.overrides.clear()
        tool.apply()
        run(
            session,
            "hide #1 models; hide #1 atoms; hide #1 cartoons; hide #1 surfaces; "
            "show #1.2 models; cartoon #1.2; show #3 models; show #3 atoms; style #3 stick; "
            "hide #2 models; show #4 models; hide "
            + "|".join("#!" + m["id"] for m in tool.scene["models"] if m["kind"] == "area")
            + " models; hide #!4 models; view overview; clip off",
            log=True,
        )
    elif action == "upgrade":
        # 旧个人会话显式升级: 只从同例 scene.json 补充显示名称, 不替换预算记录或实际编辑状态.
        metadata = json.loads(
            (Path(tool.scene["folder"]) / "scene.json").read_text(encoding="utf-8")
        )
        names = {m["key"]: m["display_name"] for m in metadata["models"] if "display_name" in m}
        by_id = {m.id_string: m for m in session.models.list()}
        for m in tool.scene["models"]:
            if m["key"] in names:
                m["display_name"] = names[m["key"]]
                run(session, f'rename #{m["id"]} "{m["display_name"]}"', log=True)
        # 只准备原本关闭的 area. 保留父组与体积的开关, 以及已可见区域的手动样式与颜色.
        areas = [m for m in tool.scene["models"] if m["kind"] == "area"]
        hidden = [m for m in areas if not by_id[m["id"]].display]
        off = [
            m.id_string
            for m in session.models.list()
            if m.id[0] == 4 and not m.display and len(m.id) <= 2
        ]
        if hidden:
            run(session, "show " + "|".join("#" + m["id"] for m in hidden) + " models", log=True)
            if off:
                run(session, "hide " + "|".join("#!" + i for i in off) + " models", log=True)
        run(session, "lighting depthCue false; clip off", log=True)
        session.logger.info(
            "已更新参考名称并解除深度淡化和裁剪; 原配色、视角与显隐保留. 请另存个人会话."
        )
    elif action == "unzone":
        run(session, "volume unzone #2.1; volume #2.1 region all; show #2.1 models", log=True)
    elif action in ["save", "export"]:
        folder = Path(tool.scene["folder"])
        suffix = "cxs" if action == "save" else "png"
        index = 1
        while (folder / f"edit_{index:03}.{suffix}").exists():
            index += 1
        f = folder / f"edit_{index:03}.{suffix}"
        run(
            session,
            f'save "{f.as_posix()}"'
            + (
                " includeMaps false"
                if action == "save"
                else " width 2400 height 1800 supersample 3"
            ),
            log=True,
        )
        session.logger.info("已另存：" + str(f))
    elif action == "status":
        report = tool.report()
        if argument:
            Path(argument).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        session.logger.info(json.dumps(report, ensure_ascii=False))
        return report
    else:
        raise UserError(
            "操作: view, condition, budget, filter, pose, labels, reset, focus, pocket, home, overview, upgrade, unzone, save, export, status"
        )
