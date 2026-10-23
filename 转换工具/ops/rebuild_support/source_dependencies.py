"""只读识别图表源代码中的本仓库导入与共享目录，不执行绘图模块。"""
import ast
from pathlib import Path
import re


def path_value(node, values: dict, root: Path):
    """解释重复出现的静态路径表达式；未知动态表达式保留为未知。"""
    if isinstance(node,ast.Constant):return node.value
    if isinstance(node,ast.Name):return values.get(node.id)
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):
        left,right=path_value(node.left,values,root),path_value(node.right,values,root)
        if isinstance(left,Path) and isinstance(right,(str,Path)):return left/right
    if isinstance(node,ast.Attribute):
        value=path_value(node.value,values,root)
        if isinstance(value,Path) and node.attr in ('parent','parents'):return getattr(value,node.attr)
    if isinstance(node,ast.Subscript):
        value=path_value(node.value,values,root);index=path_value(node.slice,values,root)
        if isinstance(value,Path('.').parents.__class__) and isinstance(index,int):return value[index]
    if isinstance(node,ast.Call):
        if isinstance(node.func,ast.Name):
            if node.func.id=='next':return root
            if node.func.id in ('str','Path') and node.args:
                value=path_value(node.args[0],values,root)
                if isinstance(value,(str,Path)):return Path(value) if node.func.id=='Path' else str(value)
        if isinstance(node.func,ast.Attribute) and node.func.attr=='resolve':
            value=path_value(node.func.value,values,root)
            if isinstance(value,Path):return value.resolve()
    return None


def code_dependencies(root: Path, entries: list) -> tuple[set, set]:
    """遍历本地Python/JS/CXC依赖，返回实际代码文件和指向temp的搜索目录。"""
    code=root/'画图/画图代码';pending=[root/e['path'] for e in entries];seen=set();temporary=set()
    while pending:
        path=pending.pop().resolve()
        if path in seen or not path.is_file():continue
        seen.add(path)
        text=path.read_text(encoding='utf-8-sig') if path.suffix.lower() in ('.py','.mjs','.js','.cxc') else ''
        found=[]
        if path.suffix=='.py':
            tree=ast.parse(text);values={'__file__':str(path)};search=[path.parent]
            for node in sorted(ast.walk(tree),key=lambda n:getattr(n,'lineno',0)):
                if isinstance(node,ast.Assign):
                    value=path_value(node.value,values,root)
                    for target in node.targets:
                        if isinstance(target,ast.Name):values[target.id]=value
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='insert' and node.args:
                    value=path_value(node.args[-1],values,root)
                    if isinstance(value,(str,Path)):
                        candidate=Path(value)
                        if candidate.is_absolute():
                            search.insert(0,candidate)
                            if candidate.is_relative_to(root/'temp'):temporary.add(candidate)
                names=[]
                if isinstance(node,ast.Import):names=[item.name for item in node.names]
                elif isinstance(node,ast.ImportFrom) and node.module:names=[node.module]
                for name in names:
                    for directory in search:
                        candidate=directory/(name.replace('.','/')+'.py')
                        if candidate.is_file():found.append(candidate);break
        elif path.suffix in ('.mjs','.js'):
            found.extend((path.parent/match).resolve() for match in re.findall(r"['\"](\.\.?/[^'\"]+\.(?:mjs|js|py))['\"]",text))
        elif path.suffix=='.cxc':
            found.extend(Path(match) for match in re.findall(r'^(?:runscript|open)\s+"([^"]+\.(?:py|cxc))"',text,re.M))
        pending.extend(candidate for candidate in found if candidate.is_relative_to(code) and not any(part in ('output','archive') for part in candidate.relative_to(code).parts))
    return seen,temporary


def source_owner(path: Path, root: Path):
    """按stage/category/目录确定图或共享代码归属，冻结证据不算活动代码。"""
    try:parts=path.relative_to(root/'画图/画图代码').parts
    except ValueError:return None
    if len(parts)<4 or parts[0]=='archive' or parts[1] not in ('calculate','visualization'):return None
    return root/'画图/画图代码'/Path(*parts[:3])
