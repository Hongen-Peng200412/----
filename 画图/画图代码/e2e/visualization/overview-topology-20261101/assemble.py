"""只修改冻结作者 PPT 的第13页, 新媒体采用独立关系以保全前12页.

FIGURE_BUILD_ROOT 的三幅身份 PNG、poses.png、scene.json 来自本次原生渲染.
candidate.pptx 为全13页可编辑候选; patch.json 记录实际变更包成员和未改页面验证.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

root = Path(__file__).resolve().parents[5]
source = root / '画图/画图代码/e2e/output/overview-topology-20261101/source'
build = Path(os.environ['FIGURE_BUILD_ROOT'])
scene = json.loads((build / 'scene.json').read_text(encoding='utf8'))
namespaces = dict(p='http://schemas.openxmlformats.org/presentationml/2006/main',
                  a='http://schemas.openxmlformats.org/drawingml/2006/main',
                  r='http://schemas.openxmlformats.org/officeDocument/2006/relationships')
with ZipFile(source / 'author-before.pptx') as archive:
    parts = {n: archive.read(n) for n in archive.namelist()}
original = dict(parts)
slide_path = 'ppt/slides/slide13.xml'
relationship_path = 'ppt/slides/_rels/slide13.xml.rels'
slide = E.fromstring(parts[slide_path])
relationships = E.fromstring(parts[relationship_path])
shapes = {s.xpath('.//p:cNvPr/@name', namespaces=namespaces)[0]: s
          for s in slide.xpath('//p:spTree//p:pic|//p:spTree//p:sp', namespaces=namespaces)}
for old_name, identity in zip(['BTN', 'DTB', 'IMI'], scene['identities']):
    shape = shapes[f'SMILES-{old_name}']
    text_body = shape.find('p:txBody', namespaces)
    paragraph = deepcopy(text_body.find('a:p', namespaces))
    for child in list(text_body):
        if child.tag == f'{{{namespaces["a"]}}}p':
            text_body.remove(child)
    paragraph.find('a:r/a:t', namespaces).text = identity['display_smiles']
    run_properties = paragraph.find('a:r/a:rPr', namespaces)
    run_properties.set('sz', '800')
    run_properties.find('a:solidFill/a:srgbClr', namespaces).set('val', identity['color'][1:])
    text_body.append(paragraph)
    shape.find('p:nvSpPr/p:cNvPr', namespaces).set('name', f'SMILES-{identity["id"]}')
media = [(f'RDKit-identity-{old_name}', f'identity-{identity["id"]}.png')
         for old_name, identity in zip(['BTN', 'DTB', 'IMI'], scene['identities'])]
media.append(('Global-poses-D55', 'poses.png'))
for ordinal, (shape_name, filename) in enumerate(media, 20):
    shape = shapes[shape_name]
    blip = shape.find('p:blipFill/a:blip', namespaces)
    relationship_id = f'rId{ordinal}'
    blip.set(f'{{{namespaces["r"]}}}embed', relationship_id)
    part_name = f'ppt/media/topology-{filename}'
    parts[part_name] = (build / filename).read_bytes()
    relation = E.SubElement(relationships, '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
    relation.set('Id', relationship_id)
    relation.set('Type', namespaces['r'] + '/image')
    relation.set('Target', '../media/' + part_name.rsplit('/', 1)[1])
    shape.find('p:nvPicPr/p:cNvPr', namespaces).set('descr', 'Native molecular rendering; schematic topology variant')
notes_path = 'ppt/notesSlides/notesSlide13.xml'
notes = E.fromstring(parts[notes_path])
# 只修正与作者已改编号直接相关的两个位置, 保留其余图注措辞.
texts = notes.xpath('//a:t', namespaces=namespaces)
for index, text in enumerate(texts):
    if text.text == 'B2 ' and index > 0 and texts[index - 2].text == 'B1 ':
        text.text = 'B3 '
    if text.text and 'B1 and B2 illustrate' in text.text:
        text.text = text.text.replace('B1 and B2 illustrate', 'B1 and B3 illustrate')
comment_path = 'ppt/comments/modernComment_11D_85773CCB.xml'
comments = E.fromstring(parts[comment_path])
comment_namespace = 'http://schemas.microsoft.com/office/powerpoint/2018/8/main'
for comment in list(comments):
    text = '\n'.join(comment.xpath('.//a:t/text()', namespaces=namespaces))
    if text.startswith('PROVENANCE v1') or text.startswith('@@'):
        comments.remove(comment)
    elif text.startswith('本页为总览图独立备选组件'):
        comment.xpath('.//a:t', namespaces=namespaces)[0].text = '本页是工作流程示意。受体和密度沿用作者原生素材；新配体由有效 SMILES 生成三维结构并作示意放置，不代表实验结合或对接结果。'
template = deepcopy(comments[0])
template.set('id', '{' + str(uuid.uuid4()).upper() + '}')
template.set('created', datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'))
body = template.find(f'{{{comment_namespace}}}txBody')
for child in list(body):
    if child.tag == f'{{{namespaces["a"]}}}p':
        body.remove(child)
paragraph = E.SubElement(body, f'{{{namespaces["a"]}}}p')
run = E.SubElement(paragraph, f'{{{namespaces["a"]}}}r')
E.SubElement(run, f'{{{namespaces["a"]}}}t').text = '@@fig-overview-topology'
comments.append(template)
for path, element in [(slide_path, slide), (relationship_path, relationships), (notes_path, notes), (comment_path, comments)]:
    parts[path] = E.tostring(element, encoding='UTF-8', xml_declaration=True, standalone=True)
changed = [name for name in parts if parts[name] != original.get(name)]
assert all(parts[f'ppt/slides/slide{i}.xml'] == original[f'ppt/slides/slide{i}.xml'] for i in range(1, 13))
assert len(slide.xpath('//p:sp[contains(p:nvSpPr/p:cNvPr/@name,"SMILES-") and not(p:nvSpPr/p:cNvPr/@name="SMILES-frame")]/p:txBody/a:p', namespaces=namespaces)) == 3
with ZipFile(build / 'candidate.pptx', 'w', ZIP_DEFLATED) as archive:
    for path, data in parts.items():
        archive.writestr(path, data)
(build / 'patch.json').write_text(json.dumps(dict(changed=changed, slides_1_12_unchanged=True), indent=2), encoding='utf8')
print(changed)
