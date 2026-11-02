"""按作者9BJJ会话重绘并装配单页PPT, 保留原相机和显隐.

参数为本轮构建目录. 原件来自画图/古法Chimera/E2E/9bjj,
图注来自冻结author_9bjj/caption.json. 不计算评价或改变结构坐标.
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
source = root / '画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/source'
caption = json.loads((root / '画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/caption.json').read_text(encoding='utf-8'))
width, height = Image.open(source / 'author04.png').size
# Python只调度原生命令, 不调整作者会话中的分子、密度、相机或显隐.
commands = ['open "' + (source / 'author04.cxs').as_posix() + '"',
            'ligwork status "' + (build / 'status.json').as_posix() + '"',
            'save "' + (build / 'author_native.png').as_posix() + f'" width {width} height {height} supersample 1',
            'save "' + (build / 'author_final.cxs').as_posix() + '" includeMaps false',
            'log save "' + (build / 'commands.html').as_posix() + '"']
(build / 'render.py').write_text('from chimerax.core.commands import run\n' + '\n'.join('run(session, ' + repr(c) + ')' for c in commands), encoding='utf-8')
subprocess.run(['powershell.exe', '-NoProfile', '-File', str(root / '转换工具/ops/rebuild_support/run_chimerax.ps1'), '-CxcPath', str(build / 'render.py'), '-LogPrefix', str(build / 'native')], check=True)
app = win32com.client.DispatchEx('PowerPoint.Application')
deck = app.Presentations.Add(False)
try:
    # 原图等比放置, 不裁切、不调整颜色; 上缘只增加可编辑图例.
    image_height = 180 * height / width
    mm = 72 / 25.4
    deck.PageSetup.SlideWidth = 180 * mm
    deck.PageSetup.SlideHeight = (image_height + 10) * mm
    slide = deck.Slides.Add(1, 12)
    slide.Shapes.AddPicture(str(build / 'author_native.png'), False, True, 0, 10 * mm, 180 * mm, image_height * mm)
    for x, text, color in [(6, 'Deposited structure', 255), (65, 'CryoAtom2 receptor and predicted ligands', 0x739e00)]:
        box = slide.Shapes.AddTextbox(1, x * mm, 2 * mm, (110 if x == 65 else 56) * mm, 7 * mm)
        box.TextFrame.TextRange.Text = text
        box.TextFrame.TextRange.Font.Name = 'Arial'
        box.TextFrame.TextRange.Font.Size = 8
        box.TextFrame.TextRange.Font.Color.RGB = color
    slide.Comments.Add(0, 0, 'Hongen Peng', 'HP', '@@full-pipeline-small-molecule-author-9bjj')
    slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = caption['zh'] + '\nENGLISH:\n' + caption['en']
    deck.SaveAs(str(build / 'candidate.pptx'))
    slide.Export(str(build / 'preview.png'), 'PNG', width, int(height + width / 18))
    deck.SaveAs(str(build / 'figure.pdf'), 32)
finally:
    deck.Close()
print('AUTHOR_9BJJ_NATIVE_AND_PPT_COMPLETE')
