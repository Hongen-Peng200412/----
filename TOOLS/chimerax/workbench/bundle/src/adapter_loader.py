"""按显式部署配置导入项目适配器, 工具自身不保存科学枚举或输入位置.

load_adapter 返回模块和路径配置. adapter.json 只含 project_root、adapter、output_root、temp_root; 后三项是项目相对路径.
导入使用适配器目录作为独立包以支持相对导入, 不向论文项目写 __pycache__.
"""

import importlib.util
import json
from pathlib import Path
import sys


def load_adapter():
    """从当前安装包旁的 adapter.json 加载唯一科学适配器, 返回 (模块, 路径字典).

    路径字典的 project_root 为绝对 Path, output_root/temp_root 为已解析的项目内目录; 不扫描旧目录或猜测替代位置.
    """
    config = json.loads(Path(__file__).with_name("adapter.json").read_text(encoding="utf-8"))
    root = Path(config["project_root"]).resolve()
    paths = {"project_root": root, **{key: (root / config[key]).resolve() for key in ["adapter", "output_root", "temp_root"]}}
    if any(not path.is_relative_to(root) for key, path in paths.items() if key != "project_root"):
        raise ValueError("工作台部署路径必须在明确的项目根内")
    name = "manuscript_figure_workbench"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, paths["adapter"], submodule_search_locations=[str(paths["adapter"].parent)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        old = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        finally:
            sys.dont_write_bytecode = old
    return sys.modules[name], paths
