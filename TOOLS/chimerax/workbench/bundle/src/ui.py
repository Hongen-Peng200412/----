"""按适配器提供的表单描述建立 Qt 面板, 不解释选项的科学意义.

build_panel 建立 choice/check 控件和按钮; refresh_panel 仅更新文字、选中值、可用状态, 不执行显示或相机命令.
"""

from functools import partial


def build_panel(tool, schema):
    """由 controls/buttons 描述创建 UI; 控件 key、标签、选项值和命令模板均由适配器提供."""
    from chimerax.ui import MainToolWindow
    from Qt.QtWidgets import QVBoxLayout, QFormLayout, QComboBox, QLabel, QCheckBox, QPushButton

    tool.tool_window = MainToolWindow(tool, close_destroys=False)
    layout = QVBoxLayout(tool.tool_window.ui_area)
    tool.title_label = QLabel(schema["initial_title"])
    layout.addWidget(tool.title_label)
    form = QFormLayout()
    layout.addLayout(form)
    tool.controls = {}
    for field in schema["controls"]:
        key = field["key"]
        if field["type"] == "check":
            widget = QCheckBox(field["label"])
            widget.toggled.connect(partial(tool._ui_change, key))
            layout.addWidget(widget)
        else:
            widget = QComboBox()
            for value, label in field["choices"]:
                widget.addItem(label, value)
            widget.currentIndexChanged.connect(partial(tool._ui_change, key))
            form.addRow(field["label"], widget)
        tool.controls[key] = widget
    tool.status_label = QLabel("尚未载入案例")
    tool.status_label.setWordWrap(True)
    layout.addWidget(tool.status_label)
    label, action = schema["reset"]
    button = QPushButton(label)
    button.clicked.connect(partial(tool._button, action, False))
    layout.addWidget(button)
    tool.focus_combo = QComboBox()
    layout.addWidget(tool.focus_combo)
    for label, action in schema["focused_buttons"]:
        button = QPushButton(label)
        button.clicked.connect(partial(tool._button, action, True))
        layout.addWidget(button)
    for label, action in schema["buttons"]:
        button = QPushButton(label)
        button.clicked.connect(partial(tool._button, action, False))
        layout.addWidget(button)
    note = QLabel(schema["note"])
    note.setWordWrap(True)
    layout.addWidget(note)
    layout.addStretch(1)
    tool.tool_window.manage("side")


def refresh_panel(tool, state):
    """把 values/enabled/text/color 应用到已有控件; 由工具 busy 标记隔离 Qt 信号回调."""
    for field in tool.adapter.ui_schema["controls"]:
        key, widget = field["key"], tool.controls[field["key"]]
        if field["type"] == "check":
            widget.setChecked(state["values"][key])
        else:
            widget.setCurrentIndex(widget.findData(state["values"][key]))
        widget.setEnabled(state["enabled"].get(key, True))
    tool.status_label.setText(state["text"])
    tool.status_label.setStyleSheet("color: " + state["color"])
