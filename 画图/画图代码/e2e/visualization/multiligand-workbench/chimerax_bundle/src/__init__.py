"""注册多配体画图命令、工具窗口与会话恢复类. 官方 BundleAPI 回调是 ChimeraX 的固定接口."""

from chimerax.core.toolshed import BundleAPI


class _WorkbenchAPI(BundleAPI):
    api_version = 1

    @staticmethod
    def register_command(bi, ci, logger):
        from chimerax.core.commands import CmdDesc, StringArg, register
        from .tool import workbench_command

        desc = CmdDesc(
            required=[("action", StringArg)],
            optional=[("argument", StringArg), ("value", StringArg)],
            synopsis="多配体模式、预算、过滤、姿态和手动编辑",
        )
        register(ci.name, desc, workbench_command, logger=logger)

    @staticmethod
    def start_tool(session, bi, ti):
        from .tool import LigandWorkbench

        tool = getattr(session, "_ligand_workbench", None)
        if tool is None:
            tool = LigandWorkbench(session, ti.name)
        tool.display(True)
        return tool

    @staticmethod
    def get_class(class_name):
        if class_name == "LigandWorkbench":
            from .tool import LigandWorkbench

            return LigandWorkbench


bundle_api = _WorkbenchAPI()
