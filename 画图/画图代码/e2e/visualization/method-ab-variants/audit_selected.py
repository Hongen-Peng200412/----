"""核对五页版的作者布局、a/b灰色框、受保护内容和原生渲染, 仅写本次构建报告."""
from pathlib import Path
from zipfile import ZipFile
import copy
import json
import os
import sys
from lxml import etree as E
from PIL import Image, ImageChops

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').exists())
BUILD = Path(os.environ['FIGURE_BUILD_ROOT'])
NS = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
ops = json.loads((BUILD/'selected_operations.json').read_text(encoding='utf8'))
failures = []
checks = {}


def value(n):
    """保留文字空格, 忽略 XML 排版空白后比较完整对象树."""
    text=n.text if E.QName(n).localname=='t' else n.text if n.text and n.text.strip() else ''
    return (n.tag,tuple(sorted(n.attrib.items())),text,tuple(value(c) for c in n))


def shape_map(n):
    """以页内原生 ID 连接同一组件, 含组、图片、形状和分子图连边."""
    return {int(s.find('.//p:cNvPr',NS).get('id')):s for s in n.xpath('.//p:sp|.//p:grpSp|.//p:pic|.//p:cxnSp',namespaces=NS)}


with ZipFile(ROOT/ops['source']) as z, ZipFile(BUILD/'candidate.pptx') as c:
    source={n:z.read(n) for n in z.namelist()};target={n:c.read(n) for n in c.namelist()}
    baseline=E.fromstring(source['ppt/slides/slide3.xml']).find('p:cSld/p:spTree',NS)
    base_shapes=shape_map(baseline)
    for page in [1,2,3]:
        for part in [f'ppt/slides/slide{page}.xml',f'ppt/notesSlides/notesSlide{page}.xml']:
            if source[part]!=target[part]:failures.append('原页改变: '+part)
    for part in source:
        if part.startswith('ppt/media/') and source[part]!=target.get(part):failures.append('作者媒体改变: '+part)
    for page in [4,5]:
        tree=E.fromstring(target[f'ppt/slides/slide{page}.xml']).find('p:cSld/p:spTree',NS)
        same=copy.deepcopy(tree)
        for s in same.xpath('.//p:sp',namespaces=NS):
            sid=int(s.find('.//p:cNvPr',NS).get('id'))
            if sid in ops['container_ids']+ops['divider_ids']:
                own=s.find('p:spPr',NS);original=base_shapes[sid].find('p:spPr',NS)
                for path in ['a:solidFill/a:srgbClr','a:ln/a:solidFill/a:srgbClr']:
                    a,b=own.find(path,NS),original.find(path,NS)
                    if a is not None and b is not None:a.set('val',b.get('val'))
        if value(same)!=value(baseline):failures.append(f'第{page}页存在框色以外的结构、位置、文字或尺寸差异')
        now=shape_map(tree); modules=[]
        for sid in ops['container_ids']:
            n=now[sid];stroke=n.find('p:spPr/a:ln/a:solidFill/a:srgbClr',NS)
            if stroke is None or stroke.get('val')!=ops['border']:failures.append(f'第{page}页对象{sid}框线未灰化')
            if page==5:
                fill=n.find('p:spPr/a:solidFill/a:srgbClr',NS)
                if fill is None or fill.get('val')!=ops['fill'] or fill.get('val')==stroke.get('val'):failures.append(f'第{page}页对象{sid}浅灰填充不正确')
            name=n.find('.//p:cNvPr',NS).get('name')
            if name.startswith('Op |'):modules.append(name)
        checks[str(page)]={'exact_page3_geometry_and_content':True,'grey_functional_module_frames':modules,'containers':len(ops['container_ids'])}
    native={}
    for page in [1,2,3]:
        a=Image.open(BUILD/f'render/reference-{page}.png').convert('RGB');b=Image.open(BUILD/f'render/candidate-{page}.png').convert('RGB')
        native[str(page)]=ImageChops.difference(a,b).getbbox() is None
        if not native[str(page)]:failures.append(f'第{page}页原生导出不同')
    checks['preserved_native_render']=native
    sys.path.insert(0,str(ROOT/'转换工具/ops'))
    from figure_provenance import Deck,load_records,comment_text
    deck=Deck(BUILD/'candidate.pptx');records={r.identifier:r for r in load_records(ROOT,[])}
    if len(deck.slides)!=5:failures.append('不是五页')
    for name in ['fig-method-ab-a1','fig-method-ab-a4','fig-method-ab-a5']:
        found=deck.managed().get(name,[])
        if len(found)!=1 or comment_text(found[0][2])!=records[name].comment:failures.append(name+'来源不一致')
result={'passed':not failures,'checks':checks,'failures':failures}
(BUILD/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['passed'] else 1)
