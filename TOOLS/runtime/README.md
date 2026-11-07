# 固定依赖与运行时定位

`paths.py::configure_runtime(project)` 从明确项目根定位 `TOOLS/runtime/.manuscript_deps/`。figure_runtime 优先接入，通用依赖目录追加在当前 Python 自身二进制依赖之后；同时设置不生成 pyc 和原生装配的 Node 模块位置。

`load_module(path, name)` 按调用方的明确文件位置装载模块，支持含连字符的 Figure 目录。调用方决定科学依赖，不由工具搜索或选择版本。

依赖本轮原样迁移，没有升级包。它被精选 Git 忽略，全面 Git 收录，不放旧 temp 或建立旧位置链接。
