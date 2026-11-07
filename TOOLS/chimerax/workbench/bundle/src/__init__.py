"""保留原 BundleAPI 注册身份, 让既有作者 CXS 恢复同名 LigandWorkbench 类."""

from chimerax.core.toolshed import BundleAPI


class _WorkbenchAPI(BundleAPI):
    """ChimeraX 固定注册回调, 只连接命令、窗口与会话恢复类."""

    api_version = 1

    @staticmethod
    def register_command(bi, ci, logger):
        from chimerax.core.commands import CmdDesc, StringArg, register
        from .tool import workbench_command
        desc = CmdDesc(required=[("action", StringArg)], optional=[("argument", StringArg), ("value", StringArg)], synopsis="项目适配工作台与作者显示保存")
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
