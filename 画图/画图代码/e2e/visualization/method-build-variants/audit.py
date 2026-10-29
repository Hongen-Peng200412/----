"""只读核对Build插页的原件保全、原生预览与分子几何记录; 输出audit.json及查看用裁图."""
import json
import os
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageChops, ImageOps, ImageDraw, ImageFont

root = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
build = Path(os.environ['FIGURE_BUILD_ROOT'])
info = json.loads((build / 'variants.json').read_text(encoding='utf-8'))
manifest = json.loads((build / 'render_manifest.json').read_text(encoding='utf-8'))
ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
checks = {'original_parts': {}, 'original_pixels': {}, 'variants': {}, 'molecules': {}}
failures = []
with ZipFile(root / info['source']) as source, ZipFile(build / 'candidate.pptx') as candidate:
    # 原有5个页、页关系、备注、批注及媒体都原样保留; 只允许presentation列表和新增资源改变.
    changed = []
    for name in source.namelist():
        if name.startswith(('ppt/slides/', 'ppt/notesSlides/', 'ppt/comments/', 'ppt/media/')) and source.read(name) != candidate.read(name):
            changed.append(name)
    checks['original_parts']['changed'] = changed
    if changed:
        failures.append('原页面或关联资源改变')
    for old, new in info['original_page_mapping'].items():
        before = Image.open(build / 'slides' / ('source-' + old + '.png')).convert('RGB')
        after = Image.open(build / 'slides' / ('candidate-' + str(new) + '.png')).convert('RGB')
        same = ImageChops.difference(before, after).getbbox() is None
        checks['original_pixels'][old] = same
        if not same:
            failures.append('原页原生渲染改变: ' + old)
    for variant in info['variants']:
        doc = ET.fromstring(candidate.read('ppt/slides/slide' + str(variant['part']) + '.xml'))
        text = ''.join(doc.itertext())
        native_texts = len(doc.findall('.//p:sp[p:txBody]', ns))
        ids = [n.get('id') for n in doc.findall('.//p:cNvPr', ns)]
        checks['variants'][variant['code']] = {'page': variant['page'], 'native_texts': native_texts, 'unique_ids': len(ids) == len(set(ids)), 'pictures': len(doc.findall('.//p:pic', ns))}
        if native_texts < 10 or len(ids) != len(set(ids)) or 'Other docking tools' in text or 'Downstream docking tools' in text:
            failures.append('候选对象或文字错误: ' + variant['code'])
        preview = Image.open(build / 'slides' / ('candidate-' + str(variant['page']) + '.png')).convert('RGB')
        # 只作预览裁边, 不修改实际PPT或科学图像.
        box = (1786, 22, 2310, 1644)
        preview.crop(box).save(build / (variant['code'] + '.png'))
for names in [['pose-1', 'pose-2', 'pose-3'], ['denoise-' + str(i) for i in range(5)]]:
    views = [manifest['images'][name]['view'] for name in names]
    counts = [manifest['images'][name]['atom_count'] for name in names]
    same = all(np.allclose(views[0], v, atol=1e-6) for v in views)
    checks['molecules'][names[0]] = {'common_camera': same, 'atom_counts': counts}
    if not same or len(set(counts)) != 1:
        failures.append('相机或原子数不一致: ' + names[0])
    for name in names:
        if not (build / 'render' / (name + '.pse')).is_file():
            failures.append('缺少原生会话: ' + name)
contact = Image.new('RGB', (524 * 4, 1685), 'white')
draw = ImageDraw.Draw(contact)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 25)
for i, variant in enumerate(info['variants']):
    image = Image.open(build / (variant['code'] + '.png')).convert('RGB')
    contact.paste(image, (524 * i, 48))
    draw.text((524 * i + 20, 9), variant['code'] + ' / page ' + str(variant['page']), font=font, fill='#263442')
contact.save(build / 'Build-comparison.png')
report = {'passed': not failures, 'failures': failures, 'checks': checks}
(build / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'failures': failures}, ensure_ascii=False))
if failures:
    raise SystemExit(1)
