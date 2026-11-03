"""从冻结作者会话生成9UJF单页PPT、原生会话及原RMSD摘要.

首个命令参数指定构建目录. source/author01.cxs保留作者相机与显隐,
caption.json为双语图注, performance_source.json为十个原Top-1记录.
输出candidate.pptx、author_native.png、author_final.cxs及performance_summary.json.
摘要只摘录原RMSD的范围和实例数, 不读取参考坐标或重新评价.
"""

import json
import subprocess
import sys
from pathlib import Path

import win32com.client
from PIL import Image

root = Path(__file__).resolve().parents[5]
build = Path(sys.argv[1]).resolve()
build.mkdir(parents=True, exist_ok=True)
frozen = root / '画图/画图代码/e2e/output/actual-small-molecule-cases/author_9ujf'
caption = json.loads((frozen / 'caption.json').read_text(encoding='utf-8'))
source = json.loads((frozen / 'performance_source.json').read_text(encoding='utf-8'))
# 十个实例的原模型Top-1 RMSD, 单位Å; 不从原子坐标重算或按RMSD选择姿态.
distances = [pose['rmsd_A'] for pose in source['poses']]
summary = {**source['expected'], 'returned_pose_count': len(distances), 'min_top1_rmsd_A': min(distances), 'max_top1_rmsd_A': max(distances), 'sub_angstrom_count': sum(value < 1.0 for value in distances)}
(build / 'performance_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
width, height = Image.open(frozen / 'source/author01.png').size
# 载入后只执行ChimeraX原生命令导出, 不改变相机、颜色、模型显隐或坐标.
commands = ['open "' + (frozen / 'source/author01.cxs').as_posix() + '"',
            'ligwork status "' + (build / 'status.json').as_posix() + '"',
            'save "' + (build / 'author_native.png').as_posix() + f'" width {width} height {height} supersample 1',
            'save "' + (build / 'author_final.cxs').as_posix() + '" includeMaps false',
            'log save "' + (build / 'commands.html').as_posix() + '"']
(build / 'render.py').write_text('from chimerax.core.commands import run\n' + '\n'.join('run(session, ' + repr(command) + ')' for command in commands), encoding='utf-8')
subprocess.run(['powershell.exe', '-NoProfile', '-File', str(root / '转换工具/ops/rebuild_support/run_chimerax.ps1'), '-CxcPath', str(build / 'render.py'), '-LogPrefix', str(build / 'native')], check=True)
app = win32com.client.DispatchEx('PowerPoint.Application')
deck = app.Presentations.Add(False)
try:
    # 作者全景等比放置, 图片不裁切、不加新标签; 颜色含义由双语图注解释.
    page_width = 180 * 72 / 25.4
    page_height = page_width * height / width
    deck.PageSetup.SlideWidth = page_width
    deck.PageSetup.SlideHeight = page_height
    slide = deck.Slides.Add(1, 12)
    slide.Shapes.AddPicture(str(build / 'author_native.png'), False, True, 0, 0, page_width, page_height)
    slide.Comments.Add(0, 0, 'Hongen Peng', 'HP', '@@full-pipeline-small-molecule-author-9ujf')
    slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = caption['zh'] + '\nENGLISH:\n' + caption['en']
    deck.SaveAs(str(build / 'candidate.pptx'))
    slide.Export(str(build / 'preview.png'), 'PNG', 1800, int(1800 * height / width))
    deck.SaveAs(str(build / 'figure.pdf'), 32)
finally:
    deck.Close()
print('AUTHOR_9UJF_NATIVE_AND_PPT_COMPLETE')
