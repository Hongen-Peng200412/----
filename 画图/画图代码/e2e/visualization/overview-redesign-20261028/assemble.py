"""在冻结作者 PPT 的副本中装配同坐标的三个左侧与五个右侧方案.

主入口 main 使用 PowerPoint COM 保留作者第 1、2 页, 修改第 3、4 页并新增第 5 至 12 页.
candidate.pptx 包含可编辑标签、边框、匹配线和两个独立组合; PNG 引用本次原生分子渲染, 不使用旧 temp.
layout.json 记录方案页码、分组框、相机和图名; preview/ 由 PowerPoint 导出整页供审读.
"""
import json
import os
import textwrap
from pathlib import Path

from PIL import Image
import win32com.client

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
INK, SUB, FRAME = '#263442', '#667783', '#C6D0D8'
COLOURS = {'B1': '#36986F', 'B2': '#36986F', 'B3': '#879098', 'B4': '#C49B32', 'B5': '#CB627F'}
LABEL_COLOURS = {'B1': '#24634E', 'B2': '#24634E', 'B3': '#4E5964', 'B4': '#896D1C', 'B5': '#9E3D5C'}


def rgb(value):
    r, g, b = (int(value[i:i+2], 16) for i in (1, 3, 5))
    return r + 256*g + 65536*b


def text(slide, value, box, size, colour=INK, bold=False, align=1, name='label', font='Arial'):
    """添加不自动缩小的原生文本框, box 为幻灯片点坐标 (left,top,width,height)."""
    shape = slide.Shapes.AddTextbox(1, *box)
    shape.Name = name
    frame = shape.TextFrame
    frame.MarginLeft = frame.MarginRight = frame.MarginTop = frame.MarginBottom = 0
    frame.WordWrap = 0
    frame.AutoSize = 0
    frame.VerticalAnchor = 3
    tr = frame.TextRange
    tr.Text = value
    tr.Font.Name = font
    tr.Font.Size = size
    tr.Font.Color.RGB = rgb(colour)
    tr.Font.Bold = -1 if bold else 0
    tr.ParagraphFormat.Alignment = align
    tr.ParagraphFormat.SpaceBefore = tr.ParagraphFormat.SpaceAfter = 0
    # 空文本框关闭换行时 Office 会收缩边界; 在文字与样式完成后恢复指定几何.
    shape.Left, shape.Top, shape.Width, shape.Height = box
    return shape


def rectangle(slide, name, box, colour=FRAME, fill=None, weight=0.65):
    shape = slide.Shapes.AddShape(1, *box)
    shape.Name = name
    if fill:
        shape.Fill.ForeColor.RGB = rgb(fill)
        shape.Fill.Transparency = 0
    else:
        shape.Fill.Visible = 0
    shape.Line.ForeColor.RGB = rgb(colour)
    shape.Line.Weight = weight
    return shape


def line(slide, name, start, end, colour=SUB, weight=1.05, arrow=False, dashed=False):
    shape = slide.Shapes.AddLine(*start, *end)
    shape.Name = name
    shape.Line.ForeColor.RGB = rgb(colour)
    shape.Line.Weight = weight
    if arrow:
        shape.Line.EndArrowheadStyle = 3
    if dashed:
        shape.Line.DashStyle = 4
    return shape


def picture(slide, path, box, name, crop=False):
    """嵌入透明图片; 全局结构不裁切, 只有独立 blob 缩略图按透明边界等比裁边."""
    if crop:
        im = Image.open(path).convert('RGBA')
        bbox = im.getchannel('A').getbbox()
        im = im.crop(bbox)
        shown = path.parent / (path.stem + '-trim.png')
        im.save(shown)
        path = shown
    w, h = Image.open(path).size
    scale = min(box[2]/w, box[3]/h)
    width, height = w*scale, h*scale
    x, y = box[0] + (box[2]-width)/2, box[1] + (box[3]-height)/2
    shape = slide.Shapes.AddPicture(str(path), 0, -1, x, y, width, height)
    shape.Name = name
    shape.AlternativeText = name
    return shape


def clear(slide):
    for i in range(slide.Shapes.Count, 0, -1):
        slide.Shapes.Item(i).Delete()


def annotate(slide, figure, chinese, english):
    """新页的图名进入独立批注; 双语图注按项目现有分隔保留在备注."""
    for i in range(slide.Comments.Count, 0, -1):
        slide.Comments.Item(i).Delete()
    slide.Comments.Add(0, 0, 'Figure', 'F', '@@' + figure)
    slide.Comments.Add(0, 0, 'Figure', 'F', '本页为总览图独立备选组件。三维分子为真实坐标的示意混合占据；密度为原子坐标生成的示意密度，不是实验 cryo-EM 结果。完整来源见 e2e/visualization/图表追溯.md 的本页稳定图名。')
    # 只写图注, 方案使用方法保存在交付教程与来源批注中.
    notes = slide.NotesPage.Shapes
    for i in range(1, notes.Count + 1):
        item = notes.Item(i)
        if item.Type == 14 and item.PlaceholderFormat.Type == 2:
            item.TextFrame.TextRange.Text = chinese + '\r\rENGLISH:\r\r' + english


def group_half(slide, name, left, width):
    anchor = rectangle(slide, '组合坐标框', (left, 0, width, 360))
    anchor.Line.Visible = 0
    anchor.Fill.Visible = 0
    result = slide.Shapes.Range(tuple(range(1, slide.Shapes.Count + 1))).Group()
    result.Name = name
    return result


def add_input(slide, build, scene, variant):
    native = build / 'native'
    rectangle(slide, 'Input-map-and-receptor', (37, 43.5, 100, 218.25))
    # 密度和受体使用完全相同的 72×90 点框, 避免相对缩放变化.
    picture(slide, native / ('input-density-D.png' if variant == 'C' else 'input-density.png'), (51, 44, 72, 90), 'Input-density')
    text(slide, 'Cryo-EM map', (39, 135, 96, 16), 12.4, bold=True, align=2)
    picture(slide, native / ('input-receptor-D.png' if variant == 'C' else 'input-receptor.png'), (51, 166, 72, 90), 'Input-receptor')
    text(slide, 'Receptor structure', (38, 246, 98, 16), 10.7, bold=True, align=2)
    line(slide, 'CryoAtom2-flow', (79, 153), (79, 169), weight=0.8, arrow=True, dashed=True)
    text(slide, 'CryoAtom2', (82, 153, 52, 14), 10.7, SUB)
    identities = scene['identities']
    if variant == 'A':
        rectangle(slide, 'SMILES-frame', (37, 268.5, 100, 77.72))
        for i, identity in enumerate(identities):
            value = '\r'.join(textwrap.wrap(identity['smiles'], width=23, break_long_words=True, break_on_hyphens=False))
            text(slide, value, (44, 272+i*18.2, 90, 18), 6.25, identity['color'], name='SMILES-' + identity['id'], font='Consolas')
        text(slide, 'SMILES', (42, 329, 90, 15), 12, bold=True, align=2)
    else:
        rectangle(slide, 'SMILES-frame', (37, 291, 353, 55))
        text(slide, 'SMILES', (45, 293, 72, 15), 11.5, bold=True)
        for i, identity in enumerate(identities):
            x = 45 + i*114
            line(slide, 'SMILES-key-' + identity['id'], (x, 312), (x+100, 312), identity['color'], 1.0)
            value = '\r'.join(textwrap.wrap(identity['smiles'], width=25, break_long_words=True, break_on_hyphens=False))
            text(slide, value, (x, 315, 106, 24), 6.9, identity['color'], name='SMILES-' + identity['id'], font='Consolas')


def add_global(slide, build, kind, box, labels):
    picture(slide, build / 'native' / (kind + '.png'), box, 'Global-' + kind)
    manifest = json.loads((build / 'native/manifest.json').read_text(encoding='utf8'))
    for blob in labels:
        px, py = manifest['projected_blob_centres'][blob]
        bb = Image.open(build / 'render' / ('blob-' + blob + '.png')).getchannel('A').getbbox()
        x = box[0] + (bb[0] / 1200 * box[2] - 22 if px < 600 else bb[2] / 1200 * box[2] + 3)
        y = box[1] + py/1500*box[3] - 6
        text(slide, blob, (x, y, 21, 13), 10.5, LABEL_COLOURS[blob], True, name='Global-label-' + blob)


def add_left(slide, build, scene, variant):
    clear(slide)
    text(slide, 'Input', (20, 12.75, 133.5, 22.5), 16.5, bold=True, align=2)
    text(slide, 'Candidate blob', (174, 12.75, 183.75, 22.5), 16.5, bold=True, align=2)
    text(slide, 'Ligand identity assignment', (397, 12.75, 246.75, 22.5), 16.0, bold=True, align=2)
    add_input(slide, build, scene, variant)
    add_global(slide, build, 'candidate-D55' if variant == 'C' else 'candidate', (185, 54, 177.6, 222), ['B1', 'B2', 'B3', 'B4', 'B5'])
    text(slide, 'Find', (145, 135, 43, 18.75), 14.5, bold=True, align=2)
    line(slide, 'Find-arrow', (151, 161), (180, 161), INK, 1.8, arrow=True)
    text(slide, 'Match', (353, 135, 45, 18.75), 14.5, bold=True, align=2)
    line(slide, 'Match-arrow', (359, 161), (393, 161), INK, 1.8, arrow=True)
    text(slide, 'Blobs', (410, 43.5, 68, 15), 11.7, SUB, align=2)
    text(slide, 'Ligand identities', (525, 43.5, 116, 15), 11.7, SUB, align=2)
    if variant == 'A':
        rectangle(slide, 'Blob-column', (408, 63, 64, 238))
        rectangle(slide, 'Chemical-identities-only', (531, 63, 108, 188))
        rows = {'B1': 84, 'B2': 118, 'B4': 162, 'B5': 225, 'B3': 283}
        identity_centres = {'BTN': 99, 'DTB': 161, 'IMI': 223}
        for blob, y in rows.items():
            text(slide, blob, (412, y-8, 21, 16), 11.3, SUB, align=2, name='Match-label-' + blob)
            picture(slide, build / 'render' / ('blob-' + blob + '.png'), (435, y-13.5, 26, 27), 'Match-blob-' + blob, crop=True)
        targets = {'B1': 99, 'B2': 99, 'B4': 161, 'B5': 223, 'B3': 283}
        for blob, y in rows.items():
            line(slide, 'Assignment-' + blob, (473, y), (531, targets[blob]), COLOURS[blob] if blob != 'B3' else SUB, 1.05)
        for identity in scene['identities']:
            y = identity_centres[identity['id']]
            picture(slide, build / 'render' / ('identity-' + identity['id'] + '.png'), (536, y-24.5, 98, 49), 'RDKit-identity-' + identity['id'], crop=True)
        text(slide, '∅  Reject', (535, 274, 83, 16), 12.5)
        text(slide, 'False positive', (536, 292, 91, 12), 9.6, SUB)
        start_x, baseline, entry_y, rdkit_x = 138, 329, 251, 369
    else:
        rectangle(slide, 'Chemical-identities-only', (537, 63, 102, 244))
        rows = {'B1': 76, 'B2': 119, 'B3': 162, 'B4': 205, 'B5': 248}
        centres = {'BTN': 89, 'DTB': 184, 'IMI': 279}
        for blob, y in rows.items():
            text(slide, blob, (412, y-8, 21, 16), 11.3, SUB, align=2, name='Match-label-' + blob)
            picture(slide, build / 'render' / ('blob-' + blob + '.png'), (436, y-13.5, 27, 27), 'Match-blob-' + blob, crop=True)
            target = 162 if blob == 'B3' else centres[{'B1':'BTN', 'B2':'BTN', 'B4':'DTB', 'B5':'IMI'}[blob]]
            line(slide, 'Assignment-' + blob, (469, y), (480 if blob == 'B3' else 537, target), COLOURS[blob] if blob != 'B3' else SUB, 1.05)
        for identity in scene['identities']:
            y = centres[identity['id']]
            picture(slide, build / 'render' / ('identity-' + identity['id'] + '.png'), (539, y-26, 98, 52), 'RDKit-identity-' + identity['id'], crop=True)
        text(slide, '∅ Reject', (479, 154, 58, 16), 11.1)
        text(slide, 'False positive', (476, 173, 61, 12), 7.8, SUB)
        start_x, baseline, entry_y, rdkit_x = 391, 325, 307, 468
    # 终点只连接真正的化学身份框, 不指向 Reject.
    line(slide, 'SMILES-route-horizontal', (start_x, baseline), (608, baseline), SUB, 0.85)
    line(slide, 'SMILES-route-entry', (608, baseline), (608, entry_y), SUB, 0.85, arrow=True)
    text(slide, 'RDKit', (rdkit_x, baseline-19, 56, 16), 11.0, SUB, align=2, name='RDKit-label')
    return group_half(slide, 'Build左侧-' + variant, 0, 647)


def add_right(slide, build, variant):
    clear(slide)
    text(slide, 'Ligand poses', (679, 12.75, 240.75, 22.5), 16.5, bold=True, align=2)
    text(slide, 'Build', (648, 155.25, 61.5, 18.75), 14.5, bold=True, align=2)
    line(slide, 'Build-arrow', (648.5, 182.3), (710, 182.3), INK, 2.2, arrow=True)
    add_global(slide, build, 'poses-' + variant, (719, 54, 177.6, 222), [])
    for x, label, colour, mode in [(720, 'Density', '#A7B0B9', 'surface'), (781, 'Receptor', '#4C6E83', 'ribbon'), (850, 'Ligands', '#36986F', 'sticks')]:
        if mode == 'surface':
            rectangle(slide, 'Legend-' + label, (x, 294, 7, 7), colour, '#E2E7EB', 0.5)
        else:
            line(slide, 'Legend-' + label, (x, 297.5), (x+8, 297.5), colour, 1.7 if mode == 'ribbon' else 2.2)
        text(slide, label, (x+10, 289.5, 52, 16), 10.3, SUB)
    return group_half(slide, 'Build及输出-' + variant, 647, 290.5)


def main():
    build = Path(os.environ['FIGURE_BUILD_ROOT'])
    scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
    app = win32com.client.GetActiveObject('PowerPoint.Application')
    for existing in list(app.Presentations):
        if existing.FullName == str(build / 'candidate.pptx'):
            existing.Close()
    source = ROOT / '画图/画图代码/e2e/output/overview-redesign-20261028/source/author.pptx'
    deck = app.Presentations.Open(str(source), 0, 0, 0)
    deck.SaveAs(str(build / 'candidate.pptx'))
    while deck.Slides.Count < 12:
        deck.Slides.Add(deck.Slides.Count + 1, 12)
    specs = [(3, 'left-A'), (4, 'right-A'), (5, 'left-B'), (6, 'right-B'), (8,'left-C'), (9,'right-D55'), (11,'right-D35'), (12,'right-D70')]
    cn = 'LigandSeek 总览示意。Find 定位五个候选区域，Match 将 B1 和 B2 指派为同一配体身份，将 B4 和 B5 指派为另外两种身份，并拒绝 B3。Build 为四个通过匹配的区域构建配体结合构象。密度、受体和配体分别用浅灰包络、蓝灰 cartoon 和彩色球棍表示。分子场景为示意混合占据，密度由原子坐标生成；不表示一次真实实验或模型预测。'
    en = 'Schematic overview of LigandSeek. Find identifies five candidate regions. Match assigns B1 and B2 to the same ligand identity, assigns B4 and B5 to two other identities, and rejects B3. Build produces four ligand poses. Density, receptor and ligands are shown as a light-grey envelope, blue-grey cartoons and coloured ball-and-stick models, respectively. The molecular scene illustrates mixed occupancy, with density generated from atomic coordinates, and does not represent an experimental map or a model prediction.'
    layout = []
    for page, role in specs:
        slide = deck.Slides.Item(page)
        if role.startswith('left'):
            add_left(slide, build, scene, role[-1])
        else:
            add_right(slide, build, role.split('-')[1])
        figure = 'fig-overview-v4-' + role.lower()
        transparent = role == 'left-C' or role.startswith('right-D')
        annotate(slide, figure, cn.replace('浅灰包络','浅灰网格') if transparent else cn, en.replace('light-grey envelope','light-grey mesh') if transparent else en)
        slide.Name = role
        layout.append(dict(page=page, role=role, figure=figure))
    combined = deck.Slides.Item(7)
    clear(combined)
    for page in [3, 4]:
        deck.Slides.Item(page).Shapes.Item(1).Copy()
        pasted = combined.Shapes.Paste().Item(1)
        pasted.Left = 0 if page == 3 else 647
        pasted.Top = 0
    annotate(combined, 'fig-overview-v4-preview', cn, en)
    combined.Name = 'left-A-plus-right-A'
    layout.append(dict(page=7, role='left-A-plus-right-A', figure='fig-overview-v4-preview'))
    combined = deck.Slides.Item(10)
    clear(combined)
    for page in [8,9]:
        deck.Slides.Item(page).Shapes.Item(1).Copy()
        pasted = combined.Shapes.Paste().Item(1)
        pasted.Left = 0 if page == 8 else 647
        pasted.Top = 0
    annotate(combined,'fig-overview-v4-preview-transparent',cn.replace('浅灰包络','浅灰网格'),en.replace('light-grey envelope','light-grey mesh'))
    combined.Name = 'left-C-plus-right-D55'
    layout.append(dict(page=10,role='left-C-plus-right-D55',figure='fig-overview-v4-preview-transparent'))
    deck.Save()
    preview = build / 'preview'
    preview.mkdir(exist_ok=True)
    for page in range(1, 13):
        deck.Slides.Item(page).Export(str(preview / f'slide-{page}.png'), 'PNG', 2500, 960)
    deck.SaveCopyAs(str(build / 'candidate.pdf'), 32)
    (build / 'layout.json').write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding='utf8')
    deck.Close()


if __name__ == '__main__':
    main()
