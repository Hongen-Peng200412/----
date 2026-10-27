"""在作者原始矢量组件上落实 Fig1/Fig2 的逐项修订。

两个候选文件各四页：三种整图配色和一页共用组件备选。
未被授权修改的网络节点与路径沿用原 XML，仅对有关组件平移。
读取 source/ 作者基底及本次 FIGURE_BUILD_ROOT 生成的新组件，
输出候选 PPT、页名清单和原生组件操作记录，不覆盖正式 PPT。
"""
import copy
import json
import os
import posixpath
import sys
import uuid
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as E

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').exists())
BUILD=Path(os.environ['FIGURE_BUILD_ROOT'])
SOURCE=ROOT/'画图/画图代码/e2e/output/fig12-revision/source'
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL='http://schemas.openxmlformats.org/package/2006/relationships'
CTYPE='http://schemas.openxmlformats.org/package/2006/content-types'
EMU=9525
serial=50000


def xml(data):
    """读取一个 OOXML 部件。"""
    return E.fromstring(data)


def identity(shape):
    """读取原生对象的 ID 与名称。"""
    meta=shape.find('.//p:cNvPr',NS)
    return (meta.get('id'),meta.get('name','')) if meta is not None else ('','')


def transform(shape):
    """定位对象自身的变换，不进入组内子对象。"""
    return shape.find('p:grpSpPr/a:xfrm',NS) if E.QName(shape).localname=='grpSp' else shape.find('p:spPr/a:xfrm',NS)


def box(shape):
    """以 CSS 像素读取当前父坐标系中的边界。"""
    t=transform(shape);o,e=t.find('a:off',NS),t.find('a:ext',NS)
    return [int(v)/EMU for v in [o.get('x'),o.get('y'),e.get('cx'),e.get('cy')]]


def reposition(shape,bounds):
    """只修改对象变换，组内路径、节点和相对比例不变。"""
    t=transform(shape)
    for tag,keys,values in [('off',['x','y'],bounds[:2]),('ext',['cx','cy'],bounds[2:])]:
        node=t.find('a:'+tag,NS)
        for key,value in zip(keys,values):node.set(key,str(round(value*EMU)))


def translate(shape,dx,dy):
    """平移一个原生组件，保留大小及内部结构。"""
    x,y,w,h=box(shape);reposition(shape,[x+dx,y+dy,w,h])


def reidentify(shape):
    """仅为新复制对象分配 ID，避免同页冲突。"""
    global serial
    for meta in shape.findall('.//p:cNvPr',NS):
        serial+=1;meta.set('id',str(serial))


def group(name,bounds,children):
    """将既有对象成组；坐标系一致时视觉不变。"""
    global serial
    serial+=1
    g=E.Element('{'+NS['p']+'}grpSp')
    nv=E.SubElement(g,'{'+NS['p']+'}nvGrpSpPr')
    E.SubElement(nv,'{'+NS['p']+'}cNvPr',id=str(serial),name=name)
    E.SubElement(nv,'{'+NS['p']+'}cNvGrpSpPr');E.SubElement(nv,'{'+NS['p']+'}nvPr')
    gp=E.SubElement(g,'{'+NS['p']+'}grpSpPr');t=E.SubElement(gp,'{'+NS['a']+'}xfrm')
    for tag,keys,values in [('off',['x','y'],bounds[:2]),('ext',['cx','cy'],bounds[2:]),('chOff',['x','y'],bounds[:2]),('chExt',['cx','cy'],bounds[2:])]:
        E.SubElement(t,'{'+NS['a']+'}'+tag,**{k:str(round(v*EMU)) for k,v in zip(keys,values)})
    g.extend(children)
    return g


def text_value(shape,value):
    """只替换明确指定的标签，保留字体与段落样式。"""
    texts=shape.findall('.//a:t',NS);texts[0].text=value
    for item in texts[1:]:item.text=''


def native_label(base,sid,bounds,scale,value):
    """保留原标签字形样式，通过外层组缩放字体和文字框。"""
    original=base.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)[0].getparent().getparent()
    leaf=copy.deepcopy(original)
    if value is not None:text_value(leaf,value)
    # PowerPoint 不随外层组变换自动缩放字号，显式执行同一组件的等比文字缩放。
    for p in leaf.xpath('.//a:rPr|.//a:defRPr|.//a:endParaRPr',namespaces=NS):
        if p.get('sz'):p.set('sz',str(round(int(p.get('sz'))*scale)))
    w,h=bounds[2]/scale,bounds[3]/scale
    reposition(leaf,[0,0,w,h])
    name='Original label '+sid+(' semantic B' if value and value.startswith('B') else '')
    outer=group(name,bounds,[leaf])
    t=transform(outer)
    for tag,keys,values in [('chOff',['x','y'],[0,0]),('chExt',['cx','cy'],[w,h])]:
        for key,val in zip(keys,values):t.find('a:'+tag,NS).set(key,str(round(val*EMU)))
    return outer


def green_blob(shape):
    """把作者已有黄色 blob 组件转为绿色，复用轮廓以区分 B1/B2。"""
    for c in shape.xpath('.//a:srgbClr',namespaces=NS):
        value=c.get('val');blue=int(value[4:6],16)
        alpha=max(0,min(1,(255-blue)/(255-54)))
        c.set('val',''.join(f'{round(255-alpha*(255-v)):02X}' for v in [80,185,130]))


def import_shapes(target,source,relationships,prefix):
    """导入本次新组件；媒体和所有后代对象 ID 独立重映射。"""
    relpart='ppt/slides/_rels/slide1.xml.rels'
    image_map={}
    for i,r in enumerate(xml(source[relpart])):
        if not r.get('Type').endswith('/image'):continue
        location=posixpath.normpath(posixpath.join('ppt/slides',r.get('Target'))).lstrip('/')
        destination='ppt/media/'+prefix+'_'+str(i)+Path(location).suffix
        target[destination]=source[location]
        rid='rIdF12'+prefix+str(i);image_map[r.get('Id')]=rid
        E.SubElement(relationships,'{'+REL+'}Relationship',Id=rid,Type=r.get('Type'),Target='../media/'+Path(destination).name)
    shapes=[]
    for child in xml(source['ppt/slides/slide1.xml']).find('p:cSld/p:spTree',NS):
        if E.QName(child).localname in ['nvGrpSpPr','grpSpPr']:continue
        child=copy.deepcopy(child);reidentify(child)
        for element in child.iter():
            for key,value in list(element.attrib.items()):
                if key.startswith('{'+NS['r']+'}') and value in image_map:element.set(key,image_map[value])
        shapes.append(child)
    return shapes


def pack_regions(sp,regions):
    """把同一组件的边框、图像和标签成组，便于作者独立复制。"""
    for name,bounds in regions:
        x,y,w,h=bounds;members=[]
        for s in list(sp):
            if transform(s) is None:continue
            a,b,c,d=box(s)
            if a>=x-.05 and b>=y-.05 and a+c<=x+w+.05 and b+d<=y+h+.05:members.append(s)
        if members:
            for s in members:sp.remove(s)
            sp.append(group(name,bounds,members))


def apply_palette(tree,mode,kind):
    """按授权分三档收敛装饰色；真实图、身份和特征颜色保留。"""
    if mode=='original':return
    for properties in tree.xpath('.//a:rPr|.//a:defRPr|.//a:endParaRPr',namespaces=NS):
        ancestors=properties.xpath('ancestor::p:sp|ancestor::p:grpSp',namespaces=NS)
        names=[identity(a)[1] for a in ancestors]
        semantic=any(any(word in name for word in ['Candidate_B','Match_B','semantic B','F1-identity-','F1-same-identity']) for name in names)
        if semantic:continue
        for colour in properties.xpath('./a:solidFill/a:srgbClr',namespaces=NS):
            if colour.get('val').upper() not in ['24634E','499D86']:colour.set('val','263442')
    if mode!='unified':return
    if kind=='overview':
        # 进一步统一非身份组件的中性色；语义色和真实结构图片不变。
        for sid in ['6211','6212','6215','6216']:
            s=tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)[0].getparent().getparent()
            for colour in s.xpath('.//a:srgbClr',namespaces=NS):
                value=colour.get('val');rgb=[int(value[i:i+2],16) for i in [0,2,4]]
                gray=round(.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]);colour.set('val',f'{gray:02X}'*3)
        return
    # 只收敛装饰背景；模块顺序、特征矩阵、模态颜色和连接线均保持。
    for sid in ['2','3','4','237','243','1188','1244']:
        shapes=tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)
        if not shapes:continue
        s=shapes[0].getparent().getparent()
        for colour in s.xpath('./p:spPr/a:solidFill/a:srgbClr',namespaces=NS):
            colour.set('val','F1F4F5')


def notes(parts,number,author,caption):
    """沿用作者备注结构，并维护完整的中英分区。"""
    tree=xml(author['ppt/notesSlides/notesSlide1.xml'])
    body=tree.xpath('//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=NS)[0]
    for child in list(body):
        if E.QName(child).localname=='p':body.remove(child)
    for line in caption.split('\n'):
        p=E.SubElement(body,'{'+NS['a']+'}p');r=E.SubElement(p,'{'+NS['a']+'}r')
        E.SubElement(r,'{'+NS['a']+'}t').text=line
    parts[f'ppt/notesSlides/notesSlide{number}.xml']=E.tostring(tree)
    rels=xml(author['ppt/notesSlides/_rels/notesSlide1.xml.rels'])
    for r in rels:
        if r.get('Type').endswith('/slide'):r.set('Target',f'../slides/slide{number}.xml')
    parts[f'ppt/notesSlides/_rels/notesSlide{number}.xml.rels']=E.tostring(rels)


# ================================================================================================
sys.path.insert(0,str(ROOT/'转换工具/ops'))
from figure_provenance import Deck,comment_text,set_comment_text

overview_caption='''LigandSeek 的 Find–Match–Build 配体自动建模工作流程。LigandSeek-Find（Find）使用实验冷冻电镜密度图与受体结构；受体既可直接提供，也可经 CryoAtom2 从密度重建。候选配体身份以 SMILES 输入 LigandSeek-Match（Match）。Match 过滤假阳性，并为有效候选区域指派身份；B1、B2 表示两个位点匹配同一身份，B3 为被拒绝候选。LigandSeek-Build（Build）结合位点、身份、受体及局部密度重建全原子结合构象。右侧四幅真实结构来自 9BJJ 的 A1AP0（E:1001）、9LLG 的 CLR（R:603）、30GA 的 ATP（L:401）和 9WUP 的 FAD（A:1103），使用沉积受体，预测配体以青绿色棒状显示。候选位置与身份连线为流程示意。
ENGLISH:
Find–Match–Build workflow of LigandSeek for automated ligand modelling. LigandSeek-Find (Find) uses an experimental cryo-electron microscopy (cryo-EM) density map and a receptor structure, supplied directly or reconstructed by CryoAtom2. Candidate ligand identities are provided as SMILES for LigandSeek-Match (Match). Match filters false-positive regions and assigns identities to valid candidates. B1 and B2 illustrate distinct sites assigned the same identity, whereas B3 is rejected. LigandSeek-Build (Build) combines the site, identity, receptor and local density to reconstruct all-atom ligand poses. Structural examples show A1AP0 in 9BJJ (E:1001), CLR in 9LLG (R:603), ATP in 30GA (L:401) and FAD in 9WUP (A:1103). These examples use deposited receptors, with predicted ligands shown as teal sticks. Blob placement and identity connections illustrate the workflow.'''
method_caption='''LigandSeek 的网络架构与信息流。框架的三个阶段 LigandSeek-Find、LigandSeek-Match 和 LigandSeek-Build 分别简称 Find、Match 和 Build。a，Find 在局部80³体素块中联合编码密度和受体原子。四个基础密度场、两种归一化表示和七种空间变换构成56通道密度库。受体嵌入头提供原子特征；3D U-Net 与 Point Transformer V3 通过多尺度融合和迭代回收连接。全局密度图与局部 blob 的形状对应，辅助特征传递给 Match。b，Match 的候选编码器结合48³体素块、口袋原子、blob 与辅助特征。池化、交叉注意力和特征线性调制（FiLM）整合辅助输入。身份编码器融合 SMI-TED、由图神经网络（GNN）编码的分子图及同一复合物中的其他身份。前景头与余弦评分分别输出前景概率和身份匹配分数。c，Build 接收位点、匹配的 SMILES、口袋和密度，默认引擎为密度引导的 PocketXMol（DG-PocketXMol），同时保留其他工具接口。两处 Pocket 显示受体局部折叠和口袋原子，配体隐藏。Build 输出示例为9BJJ中ATP（B:901）的模型首选构象。列表中的 Cc1ccccc1 高亮表示身份选择；该列表和全局 blob 为架构示意。
ENGLISH:
Network architecture and information flow of LigandSeek. The framework comprises LigandSeek-Find (Find), LigandSeek-Match (Match) and LigandSeek-Build (Build). a, Find jointly encodes density and receptor atoms within local 80³ voxel crops. Four base density fields, two normalisations and seven spatial transforms form a 56-channel density bank. A receptor embedding head supplies atom features. A 3D U-Net and Point Transformer V3 are connected through multiscale fusion and recycling. Corresponding blob shapes link the global map to local candidates, and auxiliary features pass to Match. b, The candidate encoder combines a 48³ voxel crop, pocket atoms, blob features and auxiliary features. Pooling, cross-attention and feature-wise linear modulation (FiLM) integrate auxiliary inputs. The identity encoder integrates SMI-TED representations, molecular graphs encoded by a graph neural network (GNN), and other identities in the same complex. A foreground head and cosine scoring yield foreground probabilities and identity-matching scores, respectively. c, Build receives the site, matched SMILES, pocket and density. The default engine is density-guided PocketXMol (DG-PocketXMol), with interfaces to other docking tools. Pocket views show local receptor folds and atoms with the ligand hidden. The output illustrates the model-ranked top-1 ATP pose in 9BJJ (B:901). Highlighted Cc1ccccc1 illustrates identity selection; the identity list and global blobs are architectural schematics.'''


variants=[]
operations={'overview':{},'method':{}}
for kind in ['overview','method']:
    with ZipFile(SOURCE/(kind+'-author.pptx')) as z:author={n:z.read(n) for n in z.namelist()}
    with ZipFile(BUILD/(kind+'-components.pptx')) as z:components={n:z.read(n) for n in z.namelist()}
    with ZipFile(BUILD/'component-board.pptx') as z:board={n:z.read(n) for n in z.namelist()}
    parts=dict(author);base=xml(author['ppt/slides/slide1.xml']);base_rels=xml(author['ppt/slides/_rels/slide1.xml.rels'])
    original_sp=base.find('p:cSld/p:spTree',NS)
    originals={identity(s)[0]:s for s in original_sp if identity(s)[0]}
    base_name='fig-overview_v3' if kind=='overview' else 'fig-method-v9'
    presentation=xml(parts['ppt/presentation.xml']);sldlist=presentation.find('p:sldIdLst',NS)
    for item in list(sldlist):sldlist.remove(item)
    presentation_rels=xml(parts['ppt/_rels/presentation.xml.rels'])
    for rel in list(presentation_rels):
        if rel.get('Type').endswith('/slide'):presentation_rels.remove(rel)
    if kind=='overview':
        size=presentation.find('p:sldSz',NS);size.set('cx',str(1250*EMU));size.set('cy',str(480*EMU))
    ctypes=xml(parts['[Content_Types].xml'])
    comment_relation=next(r for r in base_rels if 'comment' in r.get('Type','').lower())
    comment_source=posixpath.normpath(posixpath.join('ppt/slides',comment_relation.get('Target')))
    author_comments=xml(author[comment_source])
    marker_template=next(c for c in author_comments if comment_text(c).strip()=='@@'+base_name)
    comment_type=next(c.get('ContentType') for c in ctypes if c.get('PartName')=='/'+comment_source)
    for number,mode in enumerate(['text','original','unified','components'],1):
        tree=copy.deepcopy(base);sp=tree.find('p:cSld/p:spTree',NS);relationships=copy.deepcopy(base_rels)
        for r in list(relationships):
            if 'comment' in r.get('Type','').lower():relationships.remove(r)
        if mode=='components' or kind=='overview':
            for child in list(sp):
                if E.QName(child).localname not in ['nvGrpSpPr','grpSpPr']:sp.remove(child)
        if mode=='components':
            sp.extend(import_shapes(parts,board,relationships,f'board{kind}{number}'))
            records=json.loads((BUILD/'render/render_manifest.json').read_text(encoding='utf-8'))['poses']
            regions=[('Pose candidate '+r['case'],[14+(i%4)*106,57+(i//4)*100,101,93]) for i,r in enumerate(records)]
            regions += [(role+' Pocket '+m,[452+j*110,57+i*79,99,75]) for i,m in enumerate(['surface','atoms','cartoon']) for j,role in enumerate(['match','build'])]
            regions += [('SMILES input component',[452,322,99,103]),('Build SMILES component',[562,322,99,103])]
            pack_regions(sp,regions)
            if kind=='overview':
                children=[s for s in list(sp) if transform(s) is not None]
                for s in children:sp.remove(s)
                container=group('Shared component alternatives',[0,0,680.333333,469.166667],children)
                translate(container,(1250-680.333333)/2,(480-469.166667)/2);sp.append(container)
        elif kind=='overview':
            # 作者头部、输入结构、全局密度、原生 blob 和流程箭头均直接复用。
            for sid,bounds in [('3',[18,17,178,30]),('4',[232,17,245,30]),('5',[489,17,329,30]),('7',[918,17,321,30])]:
                sp.append(native_label(base,sid,bounds,1.3,None))
            for sid,x,y,scale in [('6211',59.5,65,1.06),('6212',69,230,.95)]:
                shape=copy.deepcopy(originals[sid]);_,_,w,h=box(shape);reposition(shape,[x,y,w*scale,h*scale]);sp.append(shape)
            for sid,bounds in [('227',[28,181,158,23]),('1972',[24,324,166,23])]:
                sp.append(native_label(base,sid,bounds,1.08,None))
            global_ids=['6215','6216','6217','6218','6219','6220','6221']
            dx,dy=250-178.79*1.12,83-360.33*1.12
            for sid in global_ids:
                shape=copy.deepcopy(originals[sid])
                if sid=='6218':
                    shape=copy.deepcopy(originals['6219']);reidentify(shape);shape.find('p:nvGrpSpPr/p:cNvPr',NS).set('name','Candidate_B2')
                    green_blob(shape);x,y,_,_=box(originals[sid]);_,_,w,h=box(shape);reposition(shape,[x,y,w,h])
                x,y,w,h=box(shape);reposition(shape,[x*1.12+dx,y*1.12+dy,w*1.12,h*1.12]);sp.append(shape)
            for sid,value in [('3951','B1'),('3963','B2'),('3997','B3'),('3974','B4'),('3986','B5')]:
                x,y,_,_=box(originals[sid])
                sp.append(native_label(base,sid,[x*1.12+dx,y*1.12+dy,28,21],1.65 if value=='B3' else 1.35,value))
            for sid,value,y in [('6225','B1',112),('6228','B2',175),('6229','B3',238),('6227','B4',301),('6226','B5',365)]:
                shape=copy.deepcopy(originals[sid])
                if sid=='6228':
                    shape=copy.deepcopy(originals['6227']);reidentify(shape);shape.find('p:nvGrpSpPr/p:cNvPr',NS).set('name','Match_B2');green_blob(shape)
                _,_,w,h=box(shape);w*=1.2;h*=1.2;reposition(shape,[531,y-h/2,w,h]);sp.append(shape)
                label={'B1':'4020','B2':'4055','B3':'4066','B4':'4043','B5':'4032'}[value]
                sp.append(native_label(base,label,[499,y-10,28,21],1.28,value))
            for sid,x,y,width in [('6214',202,211,40),('6223',478,211,45),('6',814,235,82)]:
                shape=copy.deepcopy(originals[sid]);_,_,w,h=box(shape);reposition(shape,[x,y,width,h*width/w]);sp.append(shape)
            for sid,bounds in [('1976',[194,180,58,25]),('4001',[470,180,61,25]),('4145',[814,204,82,25])]:
                sp.append(native_label(base,sid,bounds,1.2,None))
            # 边框先放在原生对象后面；其余新增对象保持前景层级。
            imported=import_shapes(parts,components,relationships,f'{kind}{number}')
            frames=[s for s in imported if identity(s)[1].endswith('input-frame')]
            for s in reversed(frames):sp.insert(2,s)
            sp.extend(s for s in imported if s not in frames)
            pack_regions(sp,[(f'Pose output {i}',[918+(i%2)*164,73+(i//2)*184,157,155]) for i in range(4)])
            operations[kind]={'native_global_components':global_ids,'labels_inside_global_map':True,'reject':'B3','identity_order':['yellow','green','reject','red'],'match_edges':'five straight segments; intersections retained','B2_shape':'reused author yellow blob mesh, recoloured green','unrequested_native_redraw':False}
        else:
            # 分摊间距：预处理、网络、输出分别平移16、23、30；Match整块平移15。
            # 原始 embedding、U-Net、PTv3 及所有 Match 网络的节点和路径均保留。
            remove={'21','23','1437','1247','18'}
            for sid in remove:
                found=tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)
                if found:
                    s=found[0].getparent().getparent();s.getparent().remove(s)
            input_ids={'13','14','15','235','236','1435'}
            find_ids={'237','238','239','240','241','242','243','244','256','266','273','283','295','296','297','298','299','300','751','755','758','761','765','6','25','1442'}|{str(i) for i in range(1443,1478)}
            build_ids={'4','11','12','768','769','770','771','773','774','775','776','777','778','967','1187','1188','1189','1242','1243','1244','1245','1246','1484','1485','1486','1487','1488','1489','22','27'}
            core_ids={'237','238','239','240','241','242','243','244','256','266','273','283','295','296','297','298','751'}
            match_ids={str(i) for i in range(301,751)}|{'766','767','1436','1479','1480','1481','1482','1483'}
            for s in list(sp):
                sid,_=identity(s)
                if sid in input_ids:translate(s,-6,0)
                elif sid in find_ids:
                    move=23 if sid in core_ids|{'1472','1476'} else 16 if sid=='1442' or 1443<=int(sid)<=1477 else 30
                    translate(s,move,0)
                    if sid in ['1471','1475']:
                        x,y,w,h=box(s);reposition(s,[x,y,w+7,h])
                elif sid in build_ids:translate(s,30,0)
                elif sid in match_ids:translate(s,15,0)
                elif sid in ['2','3']:
                    x,y,w,h=box(s);reposition(s,[x,y,w+30,h])
                elif sid=='10':translate(s,1.06,0)
            # c区边框与a区顶边、b区底边严格对齐，内部内容保持。
            c=next(s for s in sp if identity(s)[0]=='4');x,_,w,_=box(c);reposition(c,[x,8.99,w,463.78-8.99])
            # 三幅预览使用相同大小的组件框，保留各自原始长宽比。
            preview_regions=[]
            for sid,cx,y in [('15',74.965,49.5),('1435',74.965,131.5),('25',477.845,52)]:
                s=next(s for s in sp if identity(s)[0]==sid);_,_,w,h=box(s)
                new_h=h*42.5/w;reposition(s,[cx-21.25,y+(41.5-new_h)/2,42.5,new_h])
                preview_regions.append(('Find preview '+sid,[cx-21.25,y,42.5,41.5]))
            flow=tree.xpath('//p:grpSp[p:nvGrpSpPr/p:cNvPr[@id="1248"]]',namespaces=NS)[0]
            t=transform(flow);sx=int(t.find('a:ext',NS).get('cx'))/int(t.find('a:chExt',NS).get('cx'))
            pre_ids={'1249','1250','1251','1252','1324','1325','1328','1329'}
            for s in flow:
                sid,_=identity(s)
                if sid in pre_ids:translate(s,16/sx,0)
                elif sid in {str(i) for i in range(1253,1285)}|{'1333','1335'}:translate(s,30/sx,0)
                elif sid in {str(i) for i in range(1336,1371)}:translate(s,23/sx,0)
                elif sid in ['1332','1334']:
                    translate(s,23/sx,0);x,y,w,h=box(s);reposition(s,[x,y,w+7/sx,h])
                elif sid in {str(i) for i in range(1285,1324)}|{str(i) for i in range(1371,1431)}:translate(s,15/sx,0)
            boundary=tree.xpath('//p:cNvPr[@id="1478"]',namespaces=NS)[0].getparent().getparent()
            translate(boundary,15/sx,0)
            for sid in ['1324','1328']:
                s=tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)[0].getparent().getparent()
                x,y,w,h=box(s);reposition(s,[x-32/sx,y,w+32/sx,h])
            # Build列表上下留白：略增输入框高度，标签下移并缩短既有出口箭头。
            for sid in ['768','1484','1485']:
                s=next(s for s in sp if identity(s)[0]==sid);x,y,w,h=box(s);reposition(s,[x,y,w,h+6])
            for sid in ['773','774']:
                s=next(s for s in sp if identity(s)[0]==sid);translate(s,0,4)
            s=next(s for s in sp if identity(s)[0]=='775');x,_,w,h=box(s);reposition(s,[x,154.48,w,h])
            s=next(s for s in sp if identity(s)[0]=='1486');x,y,w,h=box(s);reposition(s,[x,y+6,w,h-6])
            label=tree.xpath('//p:cNvPr[@id="1242"]',namespaces=NS)[0].getparent().getparent()
            text_value(label,'DG-PocketXMol');x,y,_,h=box(label);reposition(label,[x,y,86,h])
            # 保留未改文字，只收窄原本越过工具卡片的空文本框。
            for sid,width in [('1243',86),('1245',110)]:
                s=tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)[0].getparent().getparent()
                x,y,_,h=box(s);reposition(s,[x,y,width,h])
            # 仅放大既有小字组件；符号、字体、相对上下标和连接关系不变。
            for sid in ['636','657','659','731','734','700','707','714']:
                s=tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=NS)[0].getparent().getparent()
                scale=1.16 if sid in ['700','707','714'] else 1.04
                for p in s.xpath('.//a:rPr|.//a:defRPr|.//a:endParaRPr',namespaces=NS):
                    if p.get('sz'):p.set('sz',str(round(int(p.get('sz'))*scale)))
                if sid in ['700','714']:translate(s,0,-1 if sid=='700' else 1)
            # 四个原生轮廓等比缩小；对应副本叠回全局图，不旋转、不改路径。
            for sid,cx,cy,gx,gy in [('758',437.27,112.56,465.5,67),('6',461.43,113.08,486,70),('761',437.22,126.63,463.5,84),('755',459.74,126.72,478,89)]:
                s=next(s for s in sp if identity(s)[0]==sid);x,y,w,h=box(s)
                reposition(s,[cx+30-w*.8/2,cy-h*.8/2,w*.8,h*.8])
                clone=copy.deepcopy(s);reidentify(clone);clone.find('p:nvGrpSpPr/p:cNvPr',NS).set('name','Global copy of blob '+sid)
                # 与右上全局图一起等比收小，形状和相对位置保持。
                scale=42.5/52.67
                gx=456.595+(gx-451.51)*scale;gy=52+(41.5-50.29*scale)/2+(gy-49.37)*scale
                reposition(clone,[gx-w*.25*scale/2,gy-h*.25*scale/2,w*.25*scale,h*.25*scale]);sp.append(clone)
            sp.extend(import_shapes(parts,components,relationships,f'{kind}{number}'))
            pack_regions(sp,preview_regions)
            operations[kind]={'restored_embedding_ids':list(range(1443,1478)),'native_input_topology':'author original, unchanged path geometries','find_translation_px':{'preprocessing':16,'network':23,'outputs':30},'match_block_translation_px':15,'input_translation_px':-6,'preview_component_size_px':[42.5,41.5],'panel_a_b':'same left and right edges','removed':['old placeholders 21,23','old density-stack image 1437','old pose image 1247','duplicate local blob 18'],'redrawn_network_nodes':0,'global_blob_copies':'identical author paths and uniform scaling; local uniform scale .8'}
        if mode!='components':apply_palette(tree,mode,kind)
        tree.find('p:cSld',NS).set('name',kind+' / '+mode)
        for rel in relationships:
            if rel.get('Type').endswith('/notesSlide'):rel.set('Target',f'../notesSlides/notesSlide{number}.xml')
        figure=base_name if number==1 else base_name+'-'+mode
        comments=copy.deepcopy(author_comments)
        for c in list(comments):
            value=comment_text(c).strip()
            if value.startswith('PROVENANCE v1'):comments.remove(c);continue
            if value=='@@'+base_name:set_comment_text(c,'@@'+figure)
            for node in c.iter():
                if node.get('sldId') is not None:node.set('sldId',str(255+number))
                if node.tag.endswith('}cm') and node.get('id'):node.set('id','{'+str(uuid.uuid4()).upper()+'}')
        part=f'ppt/comments/fig12_{kind}_{number}.xml';parts[part]=E.tostring(comments)
        E.SubElement(relationships,'{'+REL+'}Relationship',Id='rIdF12Comment',Type=comment_relation.get('Type'),Target='../comments/'+Path(part).name)
        if not any(c.get('PartName')=='/'+part for c in ctypes):E.SubElement(ctypes,'{'+CTYPE+'}Override',PartName='/'+part,ContentType=comment_type)
        for node in tree.iter():
            for key,value in list(node.attrib.items()):
                if key=='{'+NS['r']+'}id' and value==comment_relation.get('Id'):node.set(key,'rIdF12Comment')
        parts[f'ppt/slides/slide{number}.xml']=E.tostring(tree)
        parts[f'ppt/slides/_rels/slide{number}.xml.rels']=E.tostring(relationships)
        caption=overview_caption if kind=='overview' else method_caption
        if mode=='components':
            caption='Fig1 与 Fig2 共用的组件与备选。左侧为16个冻结的模型首选构象，绿色框标出主图采用的四例。右侧依次提供 Match、Build 的方案1、2B及仅隐藏输出配体的 cartoon 版；所有 Pocket 使用同一相机及裁剪，不改变各阶段原子定义。SMILES 组件可独立复制，配色选择与局部组件方案相互独立。\nENGLISH:\nShared component alternatives for Figs. 1 and 2. Sixteen frozen model-ranked top-1 poses are shown; green frames mark the four examples used in the overview. Match and Build Pocket alternatives include schemes 1 and 2B and a cartoon-only view with the output ligand hidden. Pocket variants share the camera and crop while retaining the stage-specific atom definitions. SMILES components can be copied independently of the figure colour scheme.'
        notes(parts,number,author,caption)
        rid='rIdF12Slide'+str(number)
        E.SubElement(sldlist,'{'+NS['p']+'}sldId',id=str(255+number),attrib={'{'+NS['r']+'}id':rid})
        E.SubElement(presentation_rels,'{'+REL+'}Relationship',Id=rid,Type=NS['r']+'/slide',Target=f'slides/slide{number}.xml')
        for part,typ in [(f'/ppt/slides/slide{number}.xml','application/vnd.openxmlformats-officedocument.presentationml.slide+xml'),(f'/ppt/notesSlides/notesSlide{number}.xml','application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml')]:
            if not any(c.get('PartName')==part for c in ctypes):E.SubElement(ctypes,'{'+CTYPE+'}Override',PartName=part,ContentType=typ)
        variants.append({'kind':kind,'slide':number,'colour':mode,'pocket':'independent alternatives' if mode=='components' else 'atoms','figure':figure})
    parts['ppt/presentation.xml']=E.tostring(presentation);parts['ppt/_rels/presentation.xml.rels']=E.tostring(presentation_rels)
    if not any(c.get('Extension')=='png' for c in ctypes):E.SubElement(ctypes,'{'+CTYPE+'}Default',Extension='png',ContentType='image/png')
    parts['[Content_Types].xml']=E.tostring(ctypes)
    target=BUILD/('candidate-'+kind+'.pptx')
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
    assert len(Deck(target).figures)==4

(BUILD/'variant_manifest.json').write_text(json.dumps(variants,ensure_ascii=False,indent=2),encoding='utf-8')
(BUILD/'native_component_operations.json').write_text(json.dumps(operations,ensure_ascii=False,indent=2),encoding='utf-8')
print('Author components reused; three colour pages plus one shared component page in each deck.')
