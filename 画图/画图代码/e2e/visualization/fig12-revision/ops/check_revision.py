"""对候选PPT执行原生导出、逐页PDF检查及实际输出框对齐核对。"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from lxml import etree as E
import win32com.client
from PIL import Image, ImageChops

root=next(p for p in Path(__file__).resolve().parents if (p/'论文草稿.md').exists())
sys.path.insert(0,str(root/'.manuscript_deps/figure_runtime'))
import pymupdf

build=Path(os.environ['FIGURE_BUILD_ROOT'])
qa=build/('qa-'+datetime.now().strftime('%H%M%S'));qa.mkdir()
tools=Path.home()/'.codex/skills/nature-figure/scripts'
environment=dict(os.environ);environment['PYTHONPATH']=str(root/'.manuscript_deps/figure_runtime')
app=win32com.client.Dispatch('PowerPoint.Application')
for kind in ['overview','method']:
    deck=app.Presentations.Open(str(build/('candidate-'+kind+'.pptx')),True,False,False)
    try:
        for page in range(1,deck.Slides.Count+1):deck.Slides(page).Export(str(qa/f'{kind}-{page}.png'),'PNG',2200,0)
        deck.SaveAs(str(qa/(kind+'.pdf')),32)
    finally:deck.Close()

summary={'qa':str(qa.relative_to(root)),'figures':{}}
for kind,count in [('overview',3),('method',3)]:
    document=pymupdf.open(qa/(kind+'.pdf'));records=[]
    for index in range(count):
        path=qa/f'{kind}-page{index+1}.pdf'
        # 按正文版心宽度和导图裁边后的实际宽度检查字体，避免以大画布掩盖小字。
        bitmap=Image.open(qa/f'{kind}-{index+1}.png').convert('RGB')
        difference=ImageChops.difference(bitmap,Image.new('RGB',bitmap.size,'white'))
        bounds=difference.convert('L').point(lambda value:255 if value>12 else 0).getbbox()
        margin=max(12,round(min(bitmap.size)*.012))
        left=max(0,bounds[0]-margin);right=min(bitmap.width,bounds[2]+margin)
        top=max(0,bounds[1]-margin);bottom=min(bitmap.height,bounds[3]+margin)
        page=document[index];clip=pymupdf.Rect(left/bitmap.width*page.rect.width,top/bitmap.height*page.rect.height,right/bitmap.width*page.rect.width,bottom/bitmap.height*page.rect.height)
        single=pymupdf.open();physical_width=6.27*72
        resized=single.new_page(width=physical_width,height=physical_width*clip.height/clip.width)
        resized.show_pdf_page(resized.rect,document,index,clip=clip)
        single.save(path)
        for name,extra in [('audit_pdf_text.py',[]),('audit_figure_collisions.py',['--overlay-pdf',str(qa/f'{kind}-{index+1}-overlay.pdf')])]:
            output=qa/f'{kind}-{index+1}-{name}.json'
            args=['--json'] if name=='audit_pdf_text.py' else ['--json-out',str(output),*extra]
            run=subprocess.run([sys.executable,'-X','utf8','-B',str(tools/name),str(path),*args],capture_output=True,text=True,encoding='utf-8',env=environment)
            if name=='audit_pdf_text.py':output.write_text(run.stdout,encoding='utf-8')
            (qa/f'{kind}-{index+1}-{name}.log').write_text(run.stdout+run.stderr,encoding='utf-8')
            records.append({'page':index+1,'check':name,'exit_code':run.returncode,'report':str(output.name)})
            if name=='audit_figure_collisions.py':
                collision=json.loads(output.read_text(encoding='utf-8'))
                intentional=[];unresolved=[]
                for finding in collision['findings']:
                    if kind=='overview' and finding['text'] in ['B1','B2','B3','B4','B5'] and finding['kind'] in ['text-stroke','text-fill-edge']:
                        intentional.append({'text':finding['text'],'bbox':finding['text_bbox'],'reason':'作者明确要求标签位于原生三维密度/受体内部；与背景网格叠加为既定标注，不外置标签。'})
                    elif finding['severity']=='FAIL':unresolved.append(finding)
                records.append({'page':index+1,'check':'collision-reviewed','passed':not unresolved,'intentional_annotation_overlays':intentional,'unresolved':unresolved})
        spans=[span for block in single[0].get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for span in line['spans'] if span['text'].strip()]
        minimum=min(s['size'] for s in spans)
        records.append({'page':index+1,'check':'physical-font-6.27in-cropped','minimum_pt':minimum,'passed':minimum>=4.99})
    summary['figures'][kind]=records

# 四个真实结构例子用相等viewport排版；同时核对PDF实际白色框的物理矩形。
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
panels=[]
with ZipFile(build/'candidate-overview.pptx') as package:
    tree=E.fromstring(package.read('ppt/slides/slide1.xml'))
    for shape in tree.xpath('.//p:sp',namespaces=ns):
        name=shape.find('p:nvSpPr/p:cNvPr',ns).get('name')
        if name.startswith('F1-pose-viewport-'):
            t=shape.find('p:spPr/a:xfrm',ns);off=t.find('a:off',ns);ext=t.find('a:ext',ns)
            x,y,w,h=[int(v)/12700 for v in [off.get('x'),off.get('y'),ext.get('cx'),ext.get('cy')]]
            parent=shape.getparent()
            while parent is not None:
                tr=parent.find('p:grpSpPr/a:xfrm',ns) if E.QName(parent).localname=='grpSp' else None
                if tr is not None:
                    o,e,co,ce=[tr.find('a:'+n,ns) for n in ['off','ext','chOff','chExt']]
                    sx,sy=int(e.get('cx'))/int(ce.get('cx')),int(e.get('cy'))/int(ce.get('cy'))
                    x=int(o.get('x'))/12700+(x-int(co.get('x'))/12700)*sx
                    y=int(o.get('y'))/12700+(y-int(co.get('y'))/12700)*sy
                    w*=sx;h*=sy
                parent=parent.getparent()
            panels.append({'id':name.rsplit('-',1)[1],'bbox_pt':[x,y,x+w,y+h]})
document=pymupdf.open(qa/'overview.pdf');drawings=document[0].get_drawings()
for panel in panels:
    delta=min(sum(abs(a-b) for a,b in zip(panel['bbox_pt'],list(d['rect']))) for d in drawings if d.get('fill') and min(d['fill'])>.97)
    panel['rendered_frame_max_total_delta_pt']=delta
    if delta>0.5:raise ValueError(f'输出框与PDF不对应: {panel}')
alignment={'schema_version':1,'figure':{'width_pt':float(document[0].rect.width),'height_pt':float(document[0].rect.height)},'panels':panels,'row_groups':[['0','1'],['2','3']],'column_groups':[['0','2'],['1','3']]}
(qa/'overview-layout.json').write_text(json.dumps(alignment,indent=2),encoding='utf-8')
run=subprocess.run([sys.executable,'-B',str(tools/'audit_panel_alignment.py'),str(qa/'overview-layout.json'),'--json-out',str(qa/'overview-alignment.json'),'--overlay-svg',str(qa/'overview-alignment.svg'),'--strict'],capture_output=True,text=True,encoding='utf-8')
summary['alignment_exit_code']=run.returncode
(qa/'overview-alignment.log').write_text(run.stdout+run.stderr,encoding='utf-8')
# a/b共享列边界，c跨越两行；以原生PDF中的面板框核对实际渲染。
with ZipFile(build/'candidate-method.pptx') as package:
    method_tree=E.fromstring(package.read('ppt/slides/slide1.xml'))
method_pdf=pymupdf.open(qa/'method.pdf');drawings=method_pdf[0].get_drawings();height=method_pdf[0].rect.height
method_panels=[]
for sid,name,row_start,row_stop,col_start,col_stop in [('2','a',0,1,0,1),('3','b',1,2,0,1),('4','c',0,2,1,2)]:
    shape=method_tree.xpath('//p:cNvPr[@id="'+sid+'"]',namespaces=ns)[0].getparent().getparent()
    t=shape.find('p:spPr/a:xfrm',ns);o,e=t.find('a:off',ns),t.find('a:ext',ns)
    x,y,w,h=[int(v)/12700 for v in [o.get('x'),o.get('y'),e.get('cx'),e.get('cy')]]
    expected=[x,y,x+w,y+h]
    delta=min(sum(abs(a-b) for a,b in zip(expected,list(d['rect']))) for d in drawings if d.get('fill'))
    if delta>.5:raise ValueError('方法图面板框未对应原生PDF：'+name)
    method_panels.append({'id':name,'bbox_pt':[x,height-y-h,x+w,height-y],'row_start':row_start,'row_stop':row_stop,'col_start':col_start,'col_stop':col_stop,'rendered_frame_total_delta_pt':delta})
method_alignment={'schema_version':1,'figure':{'width_pt':float(method_pdf[0].rect.width),'height_pt':float(height)},'panels':method_panels,'column_groups':[['a','b']]}
(qa/'method-layout.json').write_text(json.dumps(method_alignment,indent=2),encoding='utf-8')
method_run=subprocess.run([sys.executable,'-B',str(tools/'audit_panel_alignment.py'),str(qa/'method-layout.json'),'--json-out',str(qa/'method-alignment.json'),'--strict'],capture_output=True,text=True,encoding='utf-8')
(qa/'method-alignment.log').write_text(method_run.stdout+method_run.stderr,encoding='utf-8')
summary['method_alignment_exit_code']=method_run.returncode
summary['passed']=summary['alignment_exit_code']==0 and method_run.returncode==0 and all(r.get('passed',True) and (r['check']!='audit_pdf_text.py' or r['exit_code']==0) for records in summary['figures'].values() for r in records)
(qa/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(build/'qa_index.json').write_text(json.dumps({'directory':str(qa)},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'qa':summary['qa'],'passed':summary['passed'],'pose_alignment':summary['alignment_exit_code'],'stage_alignment':method_run.returncode,'minimum_font_pt':{kind:min(r['minimum_pt'] for r in records if 'minimum_pt' in r) for kind,records in summary['figures'].items()}},ensure_ascii=False))
if not summary['passed']:raise SystemExit(1)
