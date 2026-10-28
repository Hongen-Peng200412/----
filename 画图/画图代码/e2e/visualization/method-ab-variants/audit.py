"""核对作者原件保全、间距、配色白名单及 PowerPoint 实际渲染.

FIGURE_BUILD_ROOT 指定本次构建目录. 输入 candidate.pptx、operations.json 和
render/ 中本次 PowerPoint 导出的原页与候选页; 冻结作者 PPT 为独立长期输入.
输出 audit.json, failures 非空时退出码为 1; 不修改图集或任何科学素材.
"""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import copy
import json
import os
import sys

from lxml import etree as E
from PIL import Image, ImageChops

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').exists())
BUILD = Path(os.environ['FIGURE_BUILD_ROOT'])
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
operations = json.loads((BUILD / 'operations.json').read_text(encoding='utf8'))
failures = []
checks = {}


def native_shapes(root):
    """返回以页内原生 ID 为键的对象映射, 保留组内原子与分子键."""
    result = {}
    for node in root.xpath('.//p:sp|.//p:grpSp|.//p:pic|.//p:cxnSp', namespaces=NS):
        meta = node.find('.//p:cNvPr', NS)
        if meta is not None:
            result[int(meta.get('id'))] = node
    return result


def structural_value(node):
    """忽略无内容排版空白, 比较 XML 的实际节点、属性、文字及子对象."""
    if not isinstance(node.tag, str):
        return None
    text = node.text if E.QName(node).localname == 't' else node.text if node.text and node.text.strip() else ''
    return (node.tag, tuple(sorted(node.attrib.items())), text, tuple(structural_value(c) for c in node))


with ZipFile(ROOT / operations['source']) as source, ZipFile(BUILD / 'candidate.pptx') as candidate:
    original_parts = {n: source.read(n) for n in source.namelist()}
    target_parts = {n: candidate.read(n) for n in candidate.namelist()}
    preserved = []
    for page in operations['preserved_pages']:
        for name in (f'ppt/slides/slide{page}.xml', f'ppt/slides/_rels/slide{page}.xml.rels', f'ppt/notesSlides/notesSlide{page}.xml'):
            if original_parts[name] != target_parts[name]:
                failures.append('未授权原页内容改变: ' + name)
            preserved.append(name)
    media = [n for n in original_parts if n.startswith('ppt/media/')]
    changed_media = [n for n in media if original_parts[n] != target_parts.get(n)]
    if changed_media:
        failures.append('作者嵌入媒体改变: ' + repr(changed_media))
    checks['preserved_parts'] = preserved
    checks['preserved_media_count'] = len(media)

    base = E.fromstring(target_parts['ppt/slides/slide6.xml'])
    base_shapes = native_shapes(base)
    checks['candidate_native_types'] = dict(Counter(E.QName(s).localname for s in base_shapes.values()))
    for page in [4] + list(range(6, 12)):
        tree = E.fromstring(target_parts[f'ppt/slides/slide{page}.xml'])
        shapes = native_shapes(tree)
        if set(shapes) != set(base_shapes):
            failures.append(f'第{page}页对象集合不一致')
        if 1478 not in shapes:
            failures.append(f'第{page}页未恢复 Match 输入边框')
        if any('Build' in s.find('.//p:cNvPr', NS).get('name', '') for s in shapes.values()):
            failures.append(f'第{page}页混入 Build 对象')

    colour_variants = {}
    for page, code in enumerate(['A0', 'A1', 'A2', 'A3', 'A4', 'A5'], 6):
        shapes = native_shapes(E.fromstring(target_parts[f'ppt/slides/slide{page}.xml']))
        changed = []
        for sid, base_node in base_shapes.items():
            before, after = copy.deepcopy(base_node), copy.deepcopy(shapes[sid])
            before_colours = before.findall('.//a:srgbClr', NS)
            after_colours = after.findall('.//a:srgbClr', NS)
            if len(before_colours) != len(after_colours):
                failures.append(f'{code} 对象{sid}颜色节点数量改变')
            for bc, ac in zip(before_colours, after_colours):
                if bc.get('val') != ac.get('val'):
                    if E.QName(before).localname != 'grpSp':
                        changed.append(sid)
                    ac.set('val', bc.get('val'))
            if structural_value(before) != structural_value(after):
                failures.append(f'{code} 对象{sid}发生颜色以外的变化')
        allowed = {row['id'] for row in operations['colour_changes'][code]}
        if set(changed) != allowed:
            failures.append(f'{code} 实际颜色变化与操作白名单不符')
        if any(sid not in set(operations['container_ids'] + operations['divider_ids'] + operations['arrow_ids']) for sid in changed):
            failures.append(f'{code} 改变了受保护对象的颜色')
        colour_variants[code] = {'changed_object_ids': sorted(set(changed)), 'colour_edits': len(operations['colour_changes'][code])}
    checks['colour_variants'] = colour_variants

    # 作者冻结原件和 A0 之间只允许具名对象平移, 以及一条跨 encoder 折线水平伸长.
    source_shapes = native_shapes(E.fromstring(original_parts['ppt/slides/slide3.xml']))
    moved_ids = {row['id'] for row in operations['movements']}
    for sid, node in base_shapes.items():
        before, after = copy.deepcopy(source_shapes[sid]), copy.deepcopy(node)
        for parent in (before, after):
            for shape in [parent] + list(parent.xpath('.//p:sp|.//p:grpSp|.//p:pic|.//p:cxnSp', namespaces=NS)):
                meta = shape.find('.//p:cNvPr', NS)
                if meta is None or int(meta.get('id')) not in moved_ids:
                    continue
                transform = shape.find('p:grpSpPr/a:xfrm', NS) if E.QName(shape).localname == 'grpSp' else shape.find('p:spPr/a:xfrm', NS)
                if transform is not None:
                    transform.find('a:off', NS).set('x', '0')
                    if int(meta.get('id')) == 1395:
                        transform.find('a:ext', NS).set('cx', '0')
        if structural_value(before) != structural_value(after):
            failures.append(f'A0 对象{sid}不是单纯授权平移')
    checks['source_to_a0_geometry_only'] = not any('A0 对象' in item for item in failures)

    sys.path.insert(0, str(ROOT / '转换工具/ops'))
    from figure_provenance import Deck, load_records, comment_text
    deck = Deck(BUILD / 'candidate.pptx')
    record_errors = []
    records = {r.identifier: r for r in load_records(ROOT, record_errors)}
    if record_errors:
        failures.extend(record_errors)
    for code in colour_variants:
        name = 'fig-method-ab-' + code.lower()
        matches = deck.managed().get(name, [])
        if len(matches) != 1 or comment_text(matches[0][2]) != records[name].comment:
            failures.append(name + ' 来源批注不一致')
    checks['figure_names'] = {name: page.page for name, page in deck.figures.items()}
    checks['slide_count'] = len(deck.slides)
    if len(deck.slides) != 11:
        failures.append('最终页数不是11')

    pixel_checks = {}
    for page in operations['preserved_pages']:
        before = Image.open(BUILD / 'render' / f'reference-{page}.png').convert('RGB')
        after = Image.open(BUILD / 'render' / f'candidate-{page}.png').convert('RGB')
        equal = before.size == after.size and ImageChops.difference(before, after).getbbox() is None
        pixel_checks[str(page)] = equal
        if not equal:
            failures.append(f'未授权第{page}页 PowerPoint 渲染发生变化')
    checks['unchanged_native_render'] = pixel_checks

original = {row['id']: row['box_mm'] for row in operations['original_ab']}
positioned = {row['id']: row['box_mm'] for row in operations['positioned_ab']}
panel_find, panel_match = positioned[2], positioned[3]
gutter_find = [positioned[13][0] - panel_find[0], sum(panel_find[::2]) - sum(positioned[299][::2])]
divider = positioned[303][0]
gutter_candidate = [positioned[644][0] - panel_match[0], divider - sum(positioned[635][::2])]
gutter_identity = [positioned[687][0] - divider, sum(panel_match[::2]) - sum(positioned[698][::2])]
checks['balanced_gutters_mm'] = {'find_cards': gutter_find, 'candidate_body': gutter_candidate, 'identity_body': gutter_identity}
for name, values in checks['balanced_gutters_mm'].items():
    if abs(values[0] - values[1]) > 0.001:
        failures.append(name + '两侧间距仍不相等')

report = {'passed': not failures, 'checks': checks, 'failures': list(dict.fromkeys(failures))}
(BUILD / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({'passed': report['passed'], 'slides': checks['slide_count'], 'gutters_mm': checks['balanced_gutters_mm'], 'failures': report['failures']}, ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)
