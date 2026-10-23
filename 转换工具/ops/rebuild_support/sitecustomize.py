"""重建子进程的可选文件审计：禁止读取旧temp及改写冻结输入。"""
import json
import os
from pathlib import Path
import sys

if os.environ.get("FIGURE_VERIFY_ROOT"):
    workspace = Path(os.environ["FIGURE_VERIFY_ROOT"]).resolve()
    current = Path(os.environ["FIGURE_BUILD_ROOT"]).resolve()
    log = current / "python-reads.jsonl"
    recording = False

    def audit_files(event, arguments):
        """多次处理Python文件事件，旧构建的存在与内容不参与本次运行。"""
        global recording
        if recording:return
        if event=='open':
            path,mode,flags=arguments
            writing=isinstance(mode,str) and any(value in mode for value in 'wax+')
            writing |= isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            paths=[(path,writing)]
        elif event in ('shutil.copyfile','shutil.copytree','os.rename'):
            paths=[(arguments[0],False),(arguments[1],True)]
        elif event in ('os.listdir','os.scandir'):paths=[(arguments[0],False)]
        elif event in ('os.remove','os.rmdir'):paths=[(arguments[0],True)]
        else:return
        for path,writing in paths:
            if path is None or isinstance(path,int):continue
            # 先折叠..和链接，避免本次目录下的相对路径绕回旧temp。
            path=Path(os.fsdecode(path)).resolve()
            if path.is_relative_to(workspace/'temp') and not path.is_relative_to(current):
                raise FileNotFoundError(f'本次重建屏蔽旧temp: {path}')
            if writing and path.is_relative_to(workspace) and not path.is_relative_to(current):
                raise PermissionError(f'重建只允许写本次构建目录: {path}')
            if not writing and path.is_relative_to(workspace) and not path.is_relative_to(current):
                recording=True
                try:
                    with log.open('a',encoding='utf-8') as handle:handle.write(json.dumps(str(path.relative_to(workspace)),ensure_ascii=False)+'\n')
                finally:recording=False

    sys.addaudithook(audit_files)
