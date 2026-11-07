"""读取每个图表单元自己声明的入口, 不保存图名、实验地址或评价规则.

discover(project)只读取画图代码根下两级目录内的figure.json. 图表单元自行声明figures、kind、entry、outputs和正式pptx; 此处不定义论文的采用范围或科学数据.
"""
from pathlib import Path
import json


def discover(project: Path) -> dict:
    """返回目录标识到图表声明的映射, 如正文/Fig3-result-Find.

    每项含folder和directory(本地地址), kind为figure或table, figures为完整PPT图名列表, entry为本目录脚本, outputs为本次目录内的产物相对地址. pptx只用于figure的正式作者图集定位.
    """
    code = project / '画图/画图代码'
    result = {}
    figures = set()
    for path in sorted(code.glob('*/*/figure.json')):
        entry = json.loads(path.read_text(encoding='utf-8'))
        folder = path.parent.relative_to(code).as_posix()
        names = entry['figures']
        if figures.intersection(names):
            raise ValueError('多个图目录声明相同完整图名: ' + folder)
        figures.update(names)
        entry['folder'] = folder
        entry['directory'] = path.parent
        result[folder] = entry
    return result


def trace_comment(entry: dict) -> str:
    """生成只含当前图目录的PPT来源指路, 不复制实验解释或数值."""
    directory = '画图/画图代码/' + entry['folder']
    return 'TRACE v3\n绘图与本图追溯: ' + directory + '/trace.md\n代码与产物说明: ' + directory + '/README.md'
