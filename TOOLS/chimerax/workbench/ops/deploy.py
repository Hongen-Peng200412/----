"""部署中性工作台到已经注册的当前用户包, 不安装依赖或改动公共软件.

输入为 package_root/project_root/adapter/output_root/temp_root 的显式参数; 只更新本套件列出的代码、帮助和路径配置.
旧 selection.py 与本包 pyc 是旧科学实现, 在项目适配器就位后移除; 不建立备份, 不重写作者 CXS.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path


def main():
    """更新已有当前用户包并打印逐文件 SHA; --inspect 只展示清单, 不修改文件."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["package-root", "project-root", "adapter", "output-root", "temp-root"]:
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()
    package, project = Path(args.package_root).resolve(), Path(args.project_root).resolve()
    if not package.is_relative_to(Path(os.environ["LOCALAPPDATA"]).resolve()) or not (package / "__init__.py").is_file():
        raise RuntimeError("只允许更新已经注册的当前用户工作台包")
    for path in [args.adapter, args.output_root, args.temp_root]:
        if not (project / path).resolve().is_relative_to(project):
            raise RuntimeError("适配器与输出位置必须在明确的项目根内")
    if not (project / args.adapter).is_file():
        raise FileNotFoundError(project / args.adapter)
    source = Path(__file__).resolve().parents[1] / "bundle/src"
    files = [path for path in source.rglob("*") if path.is_file()]
    config = json.dumps({"project_root": str(project), "adapter": args.adapter, "output_root": args.output_root, "temp_root": args.temp_root}, ensure_ascii=False, indent=2).encode("utf-8")
    writes = {str(path.relative_to(source)).replace("\\", "/"): path.read_bytes() for path in files}
    writes["adapter.json"] = config
    deletes = [path for path in [package / "selection.py", *(package / "__pycache__").glob("*.pyc")] if path.is_file()]
    report = {"package": str(package), "writes": {name: hashlib.sha256(data).hexdigest() for name, data in writes.items()}, "deletes": {str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest() for path in deletes}, "inspect_only": args.inspect}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.inspect:
        return
    for name, data in writes.items():
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        assert target.read_bytes() == data
    for path in deletes:
        path.unlink()


if __name__ == "__main__":
    main()
