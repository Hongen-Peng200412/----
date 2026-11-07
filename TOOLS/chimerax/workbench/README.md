# ChimeraX 作者工作台工具

这里保存窗口、模型显隐观察、会话恢复和另存机制。科学适配器保存在所属 Figure 目录；工具只按显式部署配置导入它，不保存实验目录、评价口径、预算公式或构象排名规则。

既有 CXS 使用 `chimerax.ligand_workbench.tool.LigandWorkbench` 恢复工具，因此安装包继续使用 `ChimeraX-LigandWorkbench` 注册名和原类位置。恢复只连接保存的模型引用和作者状态，不执行显隐、相机或材料补载命令。

## 文件与输出

```text
TOOLS/chimerax/workbench/
├─ bundle/
│  ├─ setup.py                         # 原注册名的纯 Python 包定义
│  └─ src/
│     ├─ __init__.py                   # ChimeraX 命令、工具和恢复类注册
│     ├─ adapter_loader.py             # 按显式路径导入科学适配器
│     ├─ tool.py                       # 工具生命周期、模型观察、v1 会话状态
│     ├─ ui.py                         # 按适配器表单描述创建和刷新 Qt 控件
│     ├─ session_io.py                 # 另存 CXS/PNG 与临时状态 JSON
│     └─ docs/user/commands/ligwork.html # 软件内命令帮助
├─ ops/deploy.py                       # 已注册当前用户包的定点更新工具
└─ test_workbench.py                   # 无科学输入、无原生进程的工具契约测试
```

正式作者输出根由安装者明确指定为本项目 `画图/Chimera`。`ligwork save` 写 `<输出根>/<适配器名称>/edit_001.cxs` 等新编号文件，使用 `includeMaps true` 内嵌地图；`ligwork export` 写同目录 PNG，保持 2400×1800 像素和三倍超采样。两个命令分别寻找各自扩展名的空编号，不覆盖原件。`ligwork status` 默认只写软件 Log；明确提供 JSON 路径时，只允许写项目本次 `temp` 内。

## 安装位置与路径配置

当前用户安装目录中的 `adapter.json` 是部署配置，不是科学副本。它包含四个字段：

| 字段 | 类型与含义 | 格式示例 |
|---|---|---|
| `project_root` | 绝对目录，定位唯一项目工作区 | `C:/Work/manuscript` |
| `adapter` | 项目相对 `.py` 路径，定位所属 Figure 的科学适配器 | `figures/figure_a/workbench/adapter.py` |
| `output_root` | 项目相对目录，供正式 CXS/PNG 另存 | `author_output` |
| `temp_root` | 项目相对目录，供临时状态报告 | `temp` |

示例只解释格式；本项目实际值由正式部署命令显式传入。导入将适配器目录作为包处理，因此允许适配器的相对导入；适配器源文件不复制到安装目录，也不在项目写 Python 字节码。路径配置变化后重新启动独立 ChimeraX 进程，既有作者窗口不热载。

`ops/deploy.py` 只更新已经注册、位于当前用户 `LOCALAPPDATA` 中的包，原公共软件与依赖保持原状。它写入上述六个包文件及一个 `adapter.json`，移除该包旧 `selection.py` 和该包旧 `.pyc`，不建立备份或修改 CXS。版本保留 `1.0.8`，因为注册身份与 v1 会话格式未改变。第一次安装注册包需使用已有 ChimeraX 的 bundle 安装机制；本工具不安装外部依赖。

先将 `$PackageRoot`、`$ProjectRoot`、`$FigureAdapter`、`$AuthorOutput`、`$TaskTemp` 分别设为已经核定的当前用户包、项目根、项目相对适配器、正式输出和临时目录。只读清单与正式部署分别执行：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/chimerax/workbench/ops/deploy.py --package-root $PackageRoot --project-root $ProjectRoot --adapter $FigureAdapter --output-root $AuthorOutput --temp-root $TaskTemp --inspect
```

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/chimerax/workbench/ops/deploy.py --package-root $PackageRoot --project-root $ProjectRoot --adapter $FigureAdapter --output-root $AuthorOutput --temp-root $TaskTemp
```

## 适配器与会话契约

推荐先读科学适配器的 README，再读 `tool.py` 的 `attach`、`apply`、`restore_snapshot`，最后按需要看 `ui.py` 和 `session_io.py`。工具把 `scene`、`config`、`overrides` 作为不解释的作者状态，领域含义由科学适配器说明。

适配器提供 `default_config`、`managed_kinds`、`ui_schema` 和 `bind/open_scene/plan/report/presentation/command`。`bind(scene)` 返回 `title` 标题、`focus` 的 `(文字, 菜单值)` 列表、`output_name` 保存子目录名。`open_scene(session,path)` 返回内存说明和已经载入的模型引用。`plan` 返回 `wanted: dict[模型key,bool]` 与本次可改的 `affected: list[模型key]`；工具只对这些模型执行显隐。`report` 返回领域状态原字典；`presentation` 返回 `values` 控件值、`enabled` 控件可用标记、`text` 文本和 `color` 颜色。`command` 只响应作者明确触发的领域操作。

`ui_schema.controls` 每项包含 `key`、`label`、`type`（`choice` 或 `check`）、`command` 模板；`choice` 另含 `(值, 文本)` 的 `choices`。如 `{"key":"choice","label":"选择","type":"choice","choices":[["a","选项A"]],"command":"choice {value}"}`。按钮描述是 `(显示文字, 命令动作)`；聚焦按钮在命令后附加当前菜单值。`initial_title/reset/focused_buttons/buttons/note` 分别控制初始标题、恢复按钮、聚焦按钮、普通按钮和静态说明。工具不解释这些值的科学含义。

CXS v1 保存以下字段，恢复时不应用默认预设：

| 字段 | 保存内容 |
|---|---|
| `version` | 整数 `1`，既有格式标识 |
| `scene` | 适配器说明字典，或尚未打开案例时的 `null` |
| `models` | 模型 key 到 ChimeraX 模型引用的字典，由软件恢复真实模型 |
| `config` | 作者保存的控件值字典 |
| `overrides` | 模型 key 到手动显隐布尔值的字典 |
| `shown` | 工具面板是否显示；无 GUI 时为 `false` |

模型 `visible` 包含父组显隐。观察回调只记录变化，刷新面板只改控件文字和值；二者均不运行模型或相机命令。只有作者主动控件操作才调用显隐计划。原子数组、地图、相机、颜色和表示方式不由工具计算。

## 测试命令

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/chimerax/workbench/test_workbench.py
```

测试在 `temp/figure-centric/workbench-contract` 创建并清理隔离夹具，检查 v1 恢复无显示副作用、手动观察、计划执行、另存不覆盖和路径边界。真实作者 CXS 的地图、坐标、颜色、相机、保存参数及像素等价由独立原生进程验收；测试命令不作为正式绘图命令。
