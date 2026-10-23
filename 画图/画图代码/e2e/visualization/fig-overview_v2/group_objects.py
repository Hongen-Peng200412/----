"""将连续同名绘图对象组合为可单独移动的原生组件。"""
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
import json

paper=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file() and (p/'论文草稿.md').is_file())
root = Path(os.environ["FIGURE_BUILD_ROOT"]) if "FIGURE_BUILD_ROOT" in os.environ else paper/'temp/fig-overview_v2'
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
q=lambda p,s:'{'+ns[p]+'}'+s
names={'Input_density':'输入：实验密度表面','Input_receptor':'输入：受体主链',
       'Candidate_density':'Find：淡灰密度表面','Candidate_receptor':'Find：受体主链',
       'Output_density':'Build：输出背景密度','Output_receptor':'Build：输出受体主链'}
with ZipFile(root/'candidate.pptx') as z:
    data={n:z.read(n) for n in z.namelist()}
tree=E.fromstring(data['ppt/slides/slide1.xml']); sp=tree.find('.//p:spTree',ns)
nodes=list(sp)[2:]; batches=[]
for node in nodes:
    cn=node.find('p:nvSpPr/p:cNvPr',ns)
    name=cn.get('name','') if cn is not None else ''
    prefix=name.split('__')[0]
    if batches and batches[-1][0]==prefix: batches[-1][1].append(node)
    else:batches.append((prefix,[node]))
newid=1+max(int(n.get('id')) for n in tree.findall('.//p:cNvPr',ns))
groups=[]
for prefix,items in batches:
    if len(items)<2:continue
    bounds=[]
    for node in items:
        xf=node.find('p:spPr/a:xfrm',ns); off=xf.find('a:off',ns);ext=xf.find('a:ext',ns)
        x,y=int(off.get('x')),int(off.get('y'));w,h=int(ext.get('cx')),int(ext.get('cy'))
        bounds.append((x,y,x+w,y+h))
    x=min(b[0] for b in bounds);y=min(b[1] for b in bounds)
    w=max(b[2] for b in bounds)-x;h=max(b[3] for b in bounds)-y
    group=E.Element(q('p','grpSp'));nv=E.SubElement(group,q('p','nvGrpSpPr'))
    E.SubElement(nv,q('p','cNvPr'),id=str(newid),name=names.get(prefix,prefix));newid+=1
    E.SubElement(nv,q('p','cNvGrpSpPr'));E.SubElement(nv,q('p','nvPr'))
    gp=E.SubElement(group,q('p','grpSpPr'));xf=E.SubElement(gp,q('a','xfrm'))
    E.SubElement(xf,q('a','off'),x=str(x),y=str(y));E.SubElement(xf,q('a','ext'),cx=str(w),cy=str(h))
    E.SubElement(xf,q('a','chOff'),x=str(x),y=str(y));E.SubElement(xf,q('a','chExt'),cx=str(w),cy=str(h))
    pos=sp.index(items[0]);sp.insert(pos,group)
    for node in items:sp.remove(node);group.append(node)
    groups.append({'name':names.get(prefix,prefix),'native_shapes':len(items)})
data['ppt/slides/slide1.xml']=E.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(root/'grouped_candidate.pptx','w',ZIP_DEFLATED) as z:
    for n,b in data.items():z.writestr(n,b)
report={'slides':1,'native_shapes':len(tree.findall('.//p:sp',ns)),
        'images':len(tree.findall('.//p:pic',ns)),
        'text_boxes':len(tree.findall('.//p:txBody',ns)),
        'groups':groups,'editable_geometry':'Native DrawingML shapes and custom paths; no pictures or embedded SVG'}
(root/'editability.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='groups'},ensure_ascii=False))
