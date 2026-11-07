"""为项目工具和绘图入口配置固定依赖搜索位置, 不选择任何实验或科学字段.

configure_runtime(project)接收论文项目根目录, 将项目固定依赖加入当前解释器的模块路径. 不下载依赖, 不安装软件, 不扫描服务器, 不改变输入数组或产物.
"""

from pathlib import Path
import os
import sys


def configure_runtime(project: Path):
    """把project/TOOLS/runtime/.manuscript_deps中的既有运行包加入本进程.

    project: Path, 含论文源稿与TOOLS的本地项目根. 这里只设置导入位置和禁止字节码缓存, 不在项目内生成__pycache__.
    """
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ.setdefault(
        "RUNTIME_NODE_MODULES",
        str(
            Path.home()
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
        ),
    )
    dependencies = project / "TOOLS/runtime/.manuscript_deps"
    # 图表运行依赖集中在figure_runtime, 此处只加入其明确位置.
    figure_runtime = dependencies / "figure_runtime"
    if figure_runtime.is_dir() and str(figure_runtime) not in sys.path:
        sys.path.insert(0, str(figure_runtime))
    # 固定文稿依赖中的二进制包可能来自另一解释器; 优先当前Python已安装的兼容扩展.
    if dependencies.is_dir() and str(dependencies) not in sys.path:
        sys.path.append(str(dependencies))


def load_module(path: Path, name: str):
    """从明确的Python文件地址加载具名模块, 用于含连字符目录的显式代码依赖.

    path: Path, 调用方指定的本地科学模块或中性工具模块. name: str, 调用方提供的唯一模块名, 如fig3_find_science. 本工具不决定模块所属图或科学规则.
    """
    import importlib.util

    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module
