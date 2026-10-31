"""保留作者(v1)全部排布，从冻结准确率重画b/c的纵坐标并完善双语图注。"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').is_file())
SOURCE=ROOT/'画图/画图代码/e2e/output/stage2-stage3-results/author-v1-20261031/author-before.pptx'
DATA=ROOT/'画图/画图代码/e2e/output/stage2-stage3-results/data.json'
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}


def captions():
    """返回独立可读的中英图注，统计口径沿冻结来源。"""
    main_zh=('配体身份匹配与构象构建。a，LigandSeek-Match在沉积受体（GT）与CryoAtom2受体（CA2）条件下的总体及分类匹配准确率。b、c，按每个PDB的候选SMILES身份数分层；Overall按正确匹配数与支持数汇总。a–c分别包括1238（GT）与1160（CA2）个身份支持blob。d–f，DG-PocketXMol（DG）与Emap2lig-Build（图中简称Emap2lig）使用各自预测区域，在共同检出且可评价的235个实例上比较。d，Top-1（实线）及Top-5（虚线）的累计成功率。e，深色为RMSD<1 Å，浅色柱总高为<2 Å。Top-1取各方法原排序首位；Top-5及best-of-50分别取原排序前5个及全部50个候选的最小RMSD。f，Top-1配对比较；胜率为DG的RMSD较低的实例比例，使用未截断数值计算；≥5 Å的点显示在边界。g–i，9WUP的FAD（A:1103）：原始PocketXMol、DG-PocketXMol及Emap2lig-Build。叠加显示沉积受体；前两者采用以沉积配体中心定义的标准Centre口袋。D为达到推荐密度阈值的配体重原子比例，Clash为配体–受体碰撞重原子对数。')
    main_en=('Ligand identity matching and pose construction. a, Overall and class-specific accuracy of LigandSeek-Match with deposited (GT) and CryoAtom2 (CA2) receptors. b, c, Accuracy by candidate SMILES identity count per PDB; Overall pools correct assignments and supports. a–c include 1,238 (GT) and 1,160 (CA2) identity-supported blobs. d–f, DG-PocketXMol (DG) versus Emap2lig-Build (Emap2lig in the plots), using their respective predicted regions on 235 jointly detected, evaluable instances. d, Cumulative success for Top-1 (solid) and Top-5 (dashed). e, Dark bars show RMSD <1 Å; total light-bar heights show <2 Å. Top-1 follows each method’s original ranking. Top-5 and best-of-50 report the minimum RMSD among the original top five and all 50 candidates, respectively. f, Paired Top-1 RMSDs; wins denote lower DG RMSD and are calculated before capping values ≥5 Å at the boundary. g–i, FAD (A:1103) in 9WUP: PocketXMol-official, DG-PocketXMol and Emap2lig-Build. Overlaid receptors are the deposited structures; the first two methods use standard Centre pockets centred on the deposited ligand. D denotes the fraction of ligand heavy atoms reaching the recommended density threshold; Clash counts clashing ligand–receptor heavy-atom pairs.')
    abl_zh=('身份匹配与密度引导构建的消融。a、b，沉积受体（GT）与CryoAtom2受体（CA2）条件下LigandSeek-Match四变体的身份准确率，分别包括1238与1160个身份支持blob。Strongest为完整模型；Voxel-only使用密度及体素化受体特征，Density-only仅使用实验密度，Pocket-only使用受体口袋信息。c、d，GT与CA2条件下，原始PocketXMol、无密度微调模型与DG-PocketXMol的标准Centre口袋对照；口袋中心为沉积配体中心。无密度微调模型新增核酸线性投影，并共同微调整个网络。完整测试集为446实例；原始模型GT有445个有效RMSD，其余各组446个。小提琴由完整有效RMSD分布计算；箱体为第25–75百分位，白线为中位数，须为第10–85百分位，不绘离群散点。各姿态组下方按模型颜色标出中位RMSD；参考线为1及2 Å。Top-1取原排序首位，Top-5与best-of-50分别取原排序前5个及全部50个候选的最小RMSD。')
    abl_en=('Ablation of identity matching and density-guided pose construction. a, b, Identity accuracy of four LigandSeek-Match variants with deposited (GT) and CryoAtom2 (CA2) receptors, including 1,238 and 1,160 identity-supported blobs, respectively. Strongest denotes the full model. Voxel-only uses density and voxelised receptor features. Density-only and Pocket-only retain experimental density and receptor-pocket information, respectively. c, d, PocketXMol-official, simple fine-tuning without density and DG-PocketXMol with GT and CA2 receptors. Standard Centre pockets are centred on the deposited ligands. Simple fine-tuning adds a nucleic-acid linear projection and jointly updates the network. The benchmark contains 446 instances; PocketXMol-official has 445 finite GT RMSDs and all other groups have 446. Violins use the complete finite RMSD distributions. Boxes span the 25th–75th percentiles, white lines denote medians, and whiskers span the 10th–85th percentiles; outlier points are omitted. Colour-matched numbers beneath each pose group report median RMSD; reference lines mark 1 and 2 Å. Top-1 follows the original ranking. Top-5 and best-of-50 report the minimum RMSD among the original top five and all 50 candidates, respectively.')
    return {2:main_zh+'\nENGLISH:\n'+main_en,4:abl_zh+'\nENGLISH:\n'+abl_en}


def shape_map(root):
    """按作者保留的原生对象名定位；不按当前页字母猜测病例或方法。"""
    return {s.find('p:nvSpPr/p:cNvPr',NS).get('name'):s for s in root.findall('.//p:sp',NS)}


def xfrm(shape):
    """返回原生形状的平移与尺寸，单位为EMU。"""
    xf=shape.find('p:spPr/a:xfrm',NS)
    return xf.find('a:off',NS),xf.find('a:ext',NS)


def rewrite_axis(root,data,receptor,start,frame_name,next_id):
    """用同一组真实准确率，把35–105范围改成0–105，标记尺寸保持。"""
    shapes=shape_map(root)
    off,ext=xfrm(shapes[frame_name]);top=int(off.get('y'));height=int(ext.get('cy'))
    def ordinate(value):return round(top+height*(1-value/105))
    marker_checks=[]
    for series,key in enumerate(['overall','small','metal','sugar']):
        line_number=start+6*series
        shape=shapes[f'results_{line_number}'];off,ext=xfrm(shape)
        path=shape.find('p:spPr/a:custGeom/a:pathLst/a:path',NS)
        points=path.findall('.//a:pt',NS)
        values=data['match']['by_candidate_count'][receptor][key]['accuracy_pct']
        if len(points)!=5:raise ValueError('作者折线对象结构变化，需要重新定位五个真实观测')
        ys=[ordinate(v) for v in values];low,high=min(ys),max(ys)
        off.set('y',str(low));ext.set('cy',str(high-low));path.set('h',str(high-low))
        for point,y in zip(points,ys):point.set('y',str(y-low))
        for i,(value,y) in enumerate(zip(values,ys),1):
            marker=shapes[f'results_{line_number+i}'];mo,me=xfrm(marker)
            old_center=int(mo.get('y'))+int(me.get('cy'))/2
            expected_old=top+height*(105-value)/70
            if abs(old_center-expected_old)>800:raise ValueError('作者标记已移动，旧刻度与冻结数值不符')
            mo.set('y',str(round(y-int(me.get('cy'))/2)))
            marker_checks.append({'category':key,'value':value,'new_y_emu':y})
    # 现有40/60/80/100网格及标签移动；新增0、20保持原字号、颜色和线宽。
    grid_start=start-13
    for i,value in enumerate([40,60,80,100]):
        for kind,number in [('results',grid_start+3*i),('results',grid_start+3*i+1),('text',grid_start+3*i+2)]:
            s=shapes[f'{kind}_{number}'];o,e=xfrm(s)
            if kind=='text':
                old_grid=int(xfrm(shapes[f'results_{grid_start+3*i}'])[0].get('y'))
                # 网格在此轮已移动，文字原有基线距网格2.419pt。
                o.set('y',str(ordinate(value)-round(2.4195*12700)))
            else:o.set('y',str(ordinate(value)))
    tree=root.find('p:cSld/p:spTree',NS);insertion=list(tree).index(shapes[f'results_{grid_start}'])
    for value in [0,20]:
        for prefix,number in [('results',grid_start),('results',grid_start+1),('text',grid_start+2)]:
            s=deepcopy(shapes[f'{prefix}_{number}']);prop=s.find('p:nvSpPr/p:cNvPr',NS)
            prop.set('id',str(next_id));next_id+=1
            prop.set('name',f'v1-zero-{receptor}-{prefix}-{number}-{value}')
            for node in s.iter():
                if etree.QName(node).localname=='creationId':node.set('id','{'+str(uuid.uuid4()).upper()+'}')
            o,e=xfrm(s)
            o.set('y',str(ordinate(value)-(round(2.4195*12700) if prefix=='text' else 0)))
            if prefix=='text':
                texts=s.findall('.//a:t',NS)
                texts[0].text=str(value)
                for text in texts[1:]:text.text=''
                if value==0:
                    for paragraph in s.findall('.//a:p',NS):
                        pp=paragraph.find('a:pPr',NS)
                        if pp is None:pp=etree.Element('{'+NS['a']+'}pPr');paragraph.insert(0,pp)
                        pp.set('algn','r')
            tree.insert(insertion,s);insertion+=1
    return next_id,marker_checks


def set_notes(blob,text):
    """备注仅存双语图注；保留页面编号等其它备注占位符。"""
    root=etree.fromstring(blob)
    body=root.xpath('//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=NS)[0]
    for p in body.findall('a:p',NS):body.remove(p)
    for line in text.splitlines():
        p=etree.SubElement(body,'{'+NS['a']+'}p');r=etree.SubElement(p,'{'+NS['a']+'}r')
        etree.SubElement(r,'{'+NS['a']+'}t').text=line
    return etree.tostring(root,encoding='utf-8',xml_declaration=True,standalone=True)


def build(output):
    """只修改第2页曲线纵坐标和第2/4页图注，原页1/3/5逐字节保留。"""
    with ZipFile(SOURCE) as z:parts={n:z.read(n) for n in z.namelist()}
    data=json.loads(DATA.read_text(encoding='utf-8'))
    slide=etree.fromstring(parts['ppt/slides/slide2.xml'])
    next_id=max(int(p.get('id')) for p in slide.findall('.//p:cNvPr',NS))+1
    next_id,gt=rewrite_axis(slide,data,'GT',81,'results_56',next_id)
    next_id,ca2=rewrite_axis(slide,data,'CA2',147,'results_122',next_id)
    parts['ppt/slides/slide2.xml']=etree.tostring(slide,encoding='utf-8',xml_declaration=True,standalone=True)
    for number,text in captions().items():
        name=f'ppt/notesSlides/notesSlide{number}.xml';parts[name]=set_notes(parts[name],text)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        for name,body in parts.items():z.writestr(name,body)
    report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
            'changed_parts':['ppt/slides/slide2.xml','ppt/notesSlides/notesSlide2.xml','ppt/notesSlides/notesSlide4.xml'],
            'axis_limits':[0,105],'verified_observations':{'GT':gt,'CA2':ca2},
            'caption_english_words':{str(n):len(t.split('ENGLISH:\n')[1].split()) for n,t in captions().items()}}
    output.with_suffix('.receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(report['caption_english_words'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
