"""核对作者组件保留、编号、直线交叉及共用备选页。

在仓库根设置 FIGURE_BUILD_ROOT 后运行；只读取作者基底和本次候选，
将实际 OOXML 比较结果写入本次目录，不改 PPT 或科学输入。
"""
import copy
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile

from lxml import etree as E

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').exists())
BUILD=Path(os.environ['FIGURE_BUILD_ROOT'])
SOURCE=ROOT/'画图/画图代码/e2e/output/fig12-revision/source'
N={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
errors=[]


def shapes(tree):
    """按原生 ID 提取对象；页容器自身不计入组件。"""
    return {m.get('id'):m.getparent().getparent() for m in tree.findall('.//p:cNvPr',N) if E.QName(m.getparent().getparent()).localname!='spTree'}


def content(element):
    """忽略位置变换，比较原有路径、文字、样式及连接对象。"""
    return [element.tag,sorted(element.attrib.items()),element.text or '',[content(c) for c in element if E.QName(c).localname!='xfrm']]


def world_box(shape):
    """合成祖先组变换，读取页面上的真实矩形。"""
    t=shape.find('p:grpSpPr/a:xfrm',N) if E.QName(shape).localname=='grpSp' else shape.find('p:spPr/a:xfrm',N)
    o,e=t.find('a:off',N),t.find('a:ext',N)
    x,y,w,h=[int(v)/9525 for v in [o.get('x'),o.get('y'),e.get('cx'),e.get('cy')]]
    parent=shape.getparent()
    while parent is not None:
        tr=parent.find('p:grpSpPr/a:xfrm',N) if E.QName(parent).localname=='grpSp' else None
        if tr is not None:
            o,e,co,ce=[tr.find('a:'+n,N) for n in ['off','ext','chOff','chExt']]
            sx,sy=int(e.get('cx'))/int(ce.get('cx')),int(e.get('cy'))/int(ce.get('cy'))
            x=int(o.get('x'))/9525+(x-int(co.get('x'))/9525)*sx
            y=int(o.get('y'))/9525+(y-int(co.get('y'))/9525)*sy
            w*=sx;h*=sy
        parent=parent.getparent()
    return [x,y,w,h]


def board_contents(package,overview):
    """比较两页的组件几何、文字和真实媒体，忽略包装组及关系 ID。"""
    tree=E.fromstring(package.read('ppt/slides/slide4.xml'))
    rels=E.fromstring(package.read('ppt/slides/_rels/slide4.xml.rels'))
    media={r.get('Id'):hashlib.sha256(package.read('ppt/'+r.get('Target').removeprefix('../'))).hexdigest() for r in rels if r.get('Type').endswith('/image')}
    owner=tree.xpath('//p:grpSp[p:nvGrpSpPr/p:cNvPr[@name="Shared component alternatives"]]',namespaces=N)[0] if overview else tree.find('p:cSld/p:spTree',N)
    result=[]
    for s in owner:
        if E.QName(s).localname in ['nvGrpSpPr','grpSpPr']:continue
        s=copy.deepcopy(s)
        for node in s.iter():
            if E.QName(node).localname=='cNvPr':node.attrib.pop('id',None)
            for key,value in list(node.attrib.items()):
                if key.startswith('{'+N['r']+'}') and value in media:node.set(key,media[value])
        result.append(E.tostring(s,method='c14n',exclusive=True))
    return result


# ================================================================================================
report={}
with ZipFile(SOURCE/'method-author.pptx') as original,ZipFile(BUILD/'candidate-method.pptx') as candidate:
    old=shapes(E.fromstring(original.read('ppt/slides/slide1.xml')))
    new=shapes(E.fromstring(candidate.read('ppt/slides/slide2.xml')))
    removed={'21','23','1437','1247','18'}
    removed |= {m.get('id') for sid in list(removed) for m in old[sid].findall('.//p:cNvPr',N)}
    resized={'636','657','659','731','734','700','707','714'}
    changed=[]
    for sid in old.keys()-removed-{'1242'}:
        a,b=copy.deepcopy(old[sid]),copy.deepcopy(new[sid])
        if sid in resized:
            for item in [a,b]:
                for p in item.xpath('.//a:rPr|.//a:defRPr|.//a:endParaRPr',namespaces=N):p.attrib.pop('sz',None)
        if content(a)!=content(b):changed.append(sid)
    if changed:errors.append('原生组件除平移/缩放外发生变化：'+','.join(sorted(changed,key=int)))
    strict_ids={str(i) for i in range(301,751)}|{str(i) for i in range(1371,1431)}|{'1436','1479','1480','1481','1482','1483'}
    moved=[]
    for sid in strict_ids & old.keys() & new.keys():
        expected=world_box(old[sid])
        expected[0]+=15
        if sid in ['700','714']:expected[1]+=-1 if sid=='700' else 1
        if max(abs(a-b) for a,b in zip(expected,world_box(new[sid])))>.01:moved.append(sid)
    if moved:errors.append('未涉及的 Match 网络发生布局变化：'+','.join(sorted(moved,key=int)))
    report['method_native_components_compared']=len(old)-len(removed)-1
    report['unexpected_component_changes']=changed
    report['unchanged_match_objects']=len(strict_ids & old.keys() & new.keys())
    report['match_block_uniform_translation_px']=15
    report['explicit_small_text_resizing']=sorted(resized,key=int)
    report['embedding_original_ids_retained']=all(sid in new for sid in old.keys() & {str(i) for i in range(1443,1478)})
    a,b,c=[world_box(new[sid]) for sid in ['2','3','4']]
    aligned=max(abs(a[0]-b[0]),abs(a[0]+a[2]-b[0]-b[2]),abs(c[1]-a[1]),abs(c[1]+c[3]-b[1]-b[3]))<.02
    report['stage_boundaries_aligned']=aligned
    if not aligned:errors.append('a/b左右边界或c上下边界未对齐')
    preview=[]
    for meta in E.fromstring(candidate.read('ppt/slides/slide1.xml')).findall('.//p:cNvPr',N):
        if meta.get('name','').startswith('Find preview '):preview.append(world_box(meta.getparent().getparent())[2:])
    report['find_preview_component_sizes']=preview
    if len(preview)!=3 or any(max(abs(a-b) for a,b in zip(v,[42.5,41.5]))>.01 for v in preview):errors.append('Find三幅预览尺寸不一致')

with ZipFile(BUILD/'candidate-overview.pptx') as overview,ZipFile(BUILD/'candidate-method.pptx') as method:
    same=board_contents(overview,True)==board_contents(method,False)
    report['common_component_page_identical']=same
    if not same:errors.append('两份组件页内容不一致')
    tree=E.fromstring(overview.read('ppt/slides/slide1.xml'));items=shapes(tree)
    global_labels={}
    for sid,wanted in [('3951','B1'),('3963','B2'),('3997','B3'),('3974','B4'),('3986','B5')]:
        value=''.join(items[sid].xpath('.//a:t/text()',namespaces=N));x,y,w,h=world_box(items[sid])
        inside=x>=250 and y>=83 and x+w<=472.35 and y+h<=347.45
        global_labels[wanted]={'text':value,'inside_map':inside}
        if value!=wanted or not inside:errors.append('全局标签位置或编号不符：'+wanted)
    report['global_labels']=global_labels
    edges={}
    for meta in tree.findall('.//p:cNvPr',N):
        if not meta.get('name','').startswith('F1-match-straight-'):continue
        s=meta.getparent().getparent();path=s.find('p:spPr/a:custGeom/a:pathLst/a:path',N)
        if path is None or [E.QName(c).localname for c in path]!=['moveTo','lnTo']:errors.append('匹配边不是单一直线：'+meta.get('name'))
        x,y,w,h=world_box(s);points=[]
        for node in path:
            pt=node.find('a:pt',N);points.append([x+int(pt.get('x'))/int(path.get('w'))*w,y+int(pt.get('y'))/int(path.get('h'))*h])
        edges[meta.get('name').rsplit('-',1)[1]]=points
    intersections=0
    for i,a in enumerate(edges.values()):
        for b in list(edges.values())[i+1:]:
            def cross(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
            if cross(a[0],a[1],b[0])*cross(a[0],a[1],b[1])<0 and cross(b[0],b[1],a[0])*cross(b[0],b[1],a[1])<0:intersections+=1
    report['straight_matching_edges']=len(edges);report['matching_intersections']=intersections
    if len(edges)!=5 or intersections<1:errors.append('五条直线或交叉关系缺失')
    for kind,package in [('overview',overview),('method',method)]:
        for page in range(1,5):
            t=E.fromstring(package.read(f'ppt/slides/slide{page}.xml'))
            ids=t.xpath('.//p:cNvPr/@id',namespaces=N)
            if len(ids)!=len(set(ids)):errors.append(f'{kind} 第{page}页有重复对象 ID')

render=json.loads((BUILD/'render/render_manifest.json').read_text(encoding='utf-8'))
report['pose_candidate_count']=len(render['poses'])
report['pocket_variant_count']=len(render['pockets'])
if len(render['poses'])<15:errors.append('真实 pose 候选不足15例')
for item in render['pockets']:
    if item['ligand_visible'] or (item['mode']=='cartoon' and item['displayed_wall_atom_count']):errors.append('Pocket 表示包含不应出现的配体或 sticks')
report['passed']=not errors;report['errors']=errors
(BUILD/'component-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)
