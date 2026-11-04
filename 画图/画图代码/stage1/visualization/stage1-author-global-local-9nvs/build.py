"""按作者第15页草案重绘9NVS八视图并装配一页可编辑PPT.

首个参数是本次构建目录. source_manifest.json连接八个冻结作者CXS与其原生相机;
source/*.cxs为实际绘图输入, caption.json为双语图注. 原生重开后只统一1126×814
窗口并导出3378×2442 PNG及最终CXS, 不更改材料、外观、取景、候选或评价.
输出candidate.pptx、figure.pdf、preview.png、native_state.json和native/八组图与会话.
整体图在PPT中统一裁掉外围空白, 局部图全幅等比放置; callouts.json记录原生相机
定义的局部窗口在全景中的位置. 只生成临时候选, 不写正式PPT或稿件.
"""

import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import win32com.client
from lxml import etree as XML


def local_frame_in_global(global_view, local_view):
    """把局部相机的完整画幅投影为全局图内的矩形, 不按mask包围盒冒充放大范围.

    两个view采用共同正交投影和相同窗口宽高比, 含camera (3,4)、field_width (Å)
    和window_size [宽,高]像素; 因宽高比相同, 两轴可共用视野宽度比extent.
    相机前三列是共同屏幕轴, 第四列是世界XYZ位置. 返回(2,2)归一化坐标,
    两行依次为左上／右下, 左上原点、y向下. 相同朝向已由八份作者会话核实.
    """
    camera = np.asarray(global_view['camera'])
    local_camera = np.asarray(local_view['camera'])
    # (3,), 世界XYZ位移转为共同屏幕XYZ位移, 单位Å.
    delta = (local_camera[:, 3] - camera[:, 3]) @ camera[:, :3]
    aspect = global_view['window_size'][1] / global_view['window_size'][0]
    center = np.array([0.5 + delta[0] / global_view['field_width'], 0.5 - delta[1] / (global_view['field_width'] * aspect)])
    extent = local_view['field_width'] / global_view['field_width']
    return np.array([center - extent / 2, center + extent / 2]).tolist()


# ================================================================================================
root = Path(__file__).resolve().parents[5]
build = Path(sys.argv[1]).resolve()
native = build / 'native'
native.mkdir(parents=True, exist_ok=True)
frozen = root / '画图/画图代码/stage1/output/stage1-author-global-local-9nvs'
manifest = json.loads((frozen / 'source_manifest.json').read_text(encoding='utf-8'))
caption = json.loads((frozen / 'caption.json').read_text(encoding='utf-8'))
figure = manifest['figure']
order = ['emap_global', 'emap_tp', 'emap_fp', 'ca2_global', 'ca2_tp', 'reference_global', 'reference_tp', 'reference_transparent']
# Python只分发原生命令并读取状态. 每幅先打开对应作者原件, 不用另一幅视图代替.
script = '''from pathlib import Path
import json,traceback,gc
from chimerax.core.commands import run
result={'passed':False,'views':{}}
try:
'''
for name in order:
    source = root / manifest['author_views'][name]['frozen']
    commands = ['close all', f'open "{source.as_posix()}"', 'windowsize 1126 814', 'wait 1', f'save "{(native / (name + ".png")).as_posix()}" width 3378 height 2442 supersample 1', f'save "{(native / (name + ".cxs")).as_posix()}" includeMaps true']
    (native / (name + '.cxc')).write_text('\n'.join(commands) + '\n', encoding='utf-8')
    # 旧会话的地图／表面可能有循环引用; 先原生关闭再回收, 避免嵌图保存时累积占用内存.
    script += ' run(session, "close all")\n gc.collect()\n'
    script += ' run(session, ' + repr(f'open "{(native / (name + ".cxc")).as_posix()}"') + ')\n'
    script += f' result["views"][{name!r}]={{"camera":session.main_view.camera.position.matrix.tolist(),"field_width":session.main_view.camera.field_width,"window_size":list(session.main_view.window_size),"visible":[m.id_string for m in session.models.list() if m.visible and len(m.id)==1]}}\n'
script += ' result["passed"]=True\nexcept Exception:\n result["traceback"]=traceback.format_exc()\nfinally:\n Path(' + repr(str(build / 'native_state.json')) + ').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")\n'
(build / 'render.py').write_text(script, encoding='utf-8')
subprocess.run(['powershell.exe', '-NoProfile', '-File', str(root / '转换工具/ops/rebuild_support/run_chimerax.ps1'), '-CxcPath', str(build / 'render.py'), '-LogPrefix', str(build / 'native_run')], check=True)
states = json.loads((build / 'native_state.json').read_text(encoding='utf-8'))
assert states['passed'], states
for name, state in states['views'].items():
    np.testing.assert_allclose(state['camera'], manifest['author_views'][name]['state']['camera'], atol=1e-8, rtol=0)
    np.testing.assert_allclose(state['field_width'], manifest['author_views'][name]['state']['field_width'], atol=1e-8, rtol=0)

# 八图按方法分行: Emap全景/匹配/FP, CA2全景/匹配/图例, 参考全景/区域/透明区域.
app = win32com.client.DispatchEx('PowerPoint.Application')
deck = app.Presentations.Add(False)
mm = 72 / 25.4
width, height = 180 * mm, 201 * mm
aspect = 3378 / 2442
global_crop = {'l': 0.11, 'r': 0.18, 't': 0.0, 'b': 1 - 0.71 * aspect}
panels = [('a', 'emap_global', 0, 0, 'Emap2lig-Find', 'Semantic Dice: 0.160'), ('b', 'emap_tp', 0, 1, 'ii · Emap2lig-Find', 'IoU: 0.306'), ('c', 'emap_fp', 0, 2, 'i · Receptor-associated FP', 'Outlined blob: false positive'), ('d', 'ca2_global', 1, 0, 'LigandSeek-Find (CA2)', 'Semantic Dice: 0.757'), ('e', 'ca2_tp', 1, 1, 'ii · LigandSeek-Find', 'IoU: 0.656'), ('f', 'reference_global', 2, 0, 'Reference', 'PDB ID: 9NVS'), ('g', 'reference_tp', 2, 1, 'ii · Reference region', ''), ('h', 'reference_transparent', 2, 2, 'ii · Transparent reference', '')]
texts, frames = [], {}
try:
    deck.PageSetup.SlideWidth = width
    deck.PageSetup.SlideHeight = height
    slide = deck.Slides.Add(1, 12)
    for letter, name, row, column, title, metric in panels:
        x, row_y = 3 + 60 * column, 3 + 66 * row
        panel_width = 54
        panel_height = 54 if column == 0 else panel_width / aspect
        y = row_y + 5 if column == 0 else row_y + 32 - panel_height / 2
        image = slide.Shapes.AddPicture(str(native / (name + '.png')), False, True, x * mm, y * mm, panel_width * mm, panel_height * mm)
        image.Name = 'panel_' + letter
        frames[letter] = {'name': name, 'rect_mm': [x, y, panel_width, panel_height], 'crop': global_crop if column == 0 else None}
        texts += [(letter, x - 1, row_y, 5, 4.5, 10, True), (title, x + 4, row_y + 0.2, 50, 4.5, 8.2, False)]
        if metric:
            texts.append((metric, x, row_y + 60, 54, 4, 7.4, False))
    # 共同图例占据CA2行的右格; 它不构成另一项实验或一个新面板.
    texts += [('A1B32 (B:1001)', 124, 80, 52, 5, 8.6, True), ('Experimental density', 130, 91, 47, 4, 8, False), ('Receptor cartoon', 130, 100, 47, 4, 8, False), ('Reference ligand region', 130, 109, 47, 4, 8, False)]
    for color, y in [(0xBFB9B4, 92), (0xBDB5AD, 101), (0x0000FF, 110)]:
        swatch = slide.Shapes.AddShape(1, 124 * mm, y * mm, 3 * mm, 1.1 * mm)
        swatch.Fill.ForeColor.RGB = color
        swatch.Line.Visible = 0
    callouts = []
    for letter, key, local_key, tag in [('a', 'emap_global', 'emap_fp', 'i'), ('a', 'emap_global', 'emap_tp', 'ii'), ('d', 'ca2_global', 'ca2_tp', 'ii'), ('f', 'reference_global', 'reference_tp', 'ii')]:
        uv = np.array(local_frame_in_global(states['views'][key], states['views'][local_key]))
        # 全景在PPT统一裁掉外围空白; 标注与图像应用完全相同的坐标变换.
        uv = (uv - [global_crop['l'], global_crop['t']]) / [1 - global_crop['l'] - global_crop['r'], 1 - global_crop['t'] - global_crop['b']]
        x, y, pw, ph = frames[letter]['rect_mm']
        left, top = np.array([x, y]) + uv[0] * [pw, ph]
        rw, rh = (uv[1] - uv[0]) * [pw, ph]
        box = slide.Shapes.AddShape(1, left * mm, top * mm, rw * mm, rh * mm)
        box.Fill.Visible = 0
        box.Line.ForeColor.RGB = 0x333333
        box.Line.Weight = 0.65
        if tag == 'i':
            box.Line.DashStyle = 4
        texts.append((tag, left, top - 3.4, 6, 3.2, 7.6, True))
        callouts.append({'global_panel': letter, 'local_view': local_key, 'tag': tag, 'rect_mm': [left, top, rw, rh]})
    # c包含全部原可见预测; 细框只定位已有blob3, 不把窗口中另一块预测冒充它.
    fp_state = manifest['author_views']['emap_fp']['state']
    fp = next(model for model in fp_state['models'] if model['id'] == '12')
    # (8,3), 网格XYZ八角点经origin/step转换为世界XYZ坐标, 单位Å.
    xyz = np.array([[x, y, z] for x in (0, fp['size'][0] - 1) for y in (0, fp['size'][1] - 1) for z in (0, fp['size'][2] - 1)]) * fp['step'] + fp['origin']
    camera = np.asarray(fp_state['camera'])
    points = (xyz - camera[:, 3]) @ camera[:, :3]  # (8,3), 共同屏幕XYZ坐标, 单位Å.
    # (8,2), 左上原点、y向下的归一化图像坐标.
    uv = np.column_stack([0.5 + points[:, 0] / fp_state['field_width'], 0.5 - points[:, 1] / (fp_state['field_width'] / aspect)])
    x, y, pw, ph = frames['c']['rect_mm']
    left, top = [x, y] + uv.min(0) * [pw, ph]
    rw, rh = (uv.max(0) - uv.min(0)) * [pw, ph]
    box = slide.Shapes.AddShape(1, left * mm, top * mm, rw * mm, rh * mm)
    box.Fill.Visible = 0
    box.Line.ForeColor.RGB = 0x333333
    box.Line.Weight = 0.65
    texts.append(('FP', left + rw + 0.7, top, 7, 3.5, 7, True))
    for content, x, y, tw, th, size, bold in texts:
        shape = slide.Shapes.AddTextbox(1, x * mm, y * mm, tw * mm, th * mm)
        frame = shape.TextFrame
        frame.MarginLeft = frame.MarginRight = frame.MarginTop = frame.MarginBottom = 0
        frame.WordWrap = 0
        frame.TextRange.Text = content
        frame.TextRange.Font.Name = 'Arial'
        frame.TextRange.Font.Size = size
        frame.TextRange.Font.Bold = -1 if bold else 0
        frame.TextRange.Font.Color.RGB = 0x222222
    slide.Comments.Add(0, 0, 'Hongen Peng', 'HP', '@@' + figure)
    slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = caption['zh'] + '\nENGLISH:\n' + caption['en']
    deck.SaveAs(str(build / 'uncropped.pptx'))
finally:
    deck.Close()

# srcRect作用于原图片采样区域; 裁后全景天然为方形, 不把整幅图强行拉伸为方形.
with ZipFile(build / 'uncropped.pptx') as package:
    parts = {name: package.read(name) for name in package.namelist()}
ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
tree = XML.fromstring(parts['ppt/slides/slide1.xml'])
for pic in tree.findall('.//p:pic', ns):
    name = pic.find('p:nvPicPr/p:cNvPr', ns).get('name')
    if name in ['panel_a', 'panel_d', 'panel_f']:
        fill = pic.find('p:blipFill', ns)
        crop = XML.Element('{' + ns['a'] + '}srcRect', **{key: str(round(value * 100000)) for key, value in global_crop.items()})
        fill.insert(1, crop)
parts['ppt/slides/slide1.xml'] = XML.tostring(tree, encoding='UTF-8', xml_declaration=True, standalone=True)
with ZipFile(build / 'candidate.pptx', 'w') as package:
    for name, content in parts.items():
        package.writestr(name, content)
(build / 'panels.json').write_text(json.dumps(frames, ensure_ascii=False, indent=2), encoding='utf-8')
(build / 'callouts.json').write_text(json.dumps(callouts, ensure_ascii=False, indent=2), encoding='utf-8')
(build / 'manifest.json').write_text(json.dumps([{'id': figure, 'width': width, 'height': height}], ensure_ascii=False), encoding='utf-8')
deck = app.Presentations.Open(str(build / 'candidate.pptx'), True, False, False)
try:
    deck.Slides(1).Export(str(build / 'preview.png'), 'PNG', 2400, 0)
    deck.SaveAs(str(build / 'figure.pdf'), 32)
finally:
    deck.Close()
print('9NVS八视图原生重绘及候选PPT完成: ' + str(build / 'candidate.pptx'))
