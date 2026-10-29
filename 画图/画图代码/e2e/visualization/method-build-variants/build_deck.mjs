/** 以作者独立Build页为模板, 用Artifact Tool构造可编辑内部示意, 只插入四个新页面. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {createHash,randomUUID} from 'node:crypto';
import {Presentation,PresentationFile} from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const require=createRequire('C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/__method_build__.cjs');
const JSZip=require('jszip'),{xml2js,js2xml}=require('xml-js');
let root=path.dirname(fileURLToPath(import.meta.url));
while(!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false)))root=path.dirname(root);
const build=process.env.FIGURE_BUILD_ROOT;
const frozen='画图/画图代码/e2e/output/method-build-variants/source/author-20261028-ce373d2e.pptx';
const sourceHash='ce373d2ea868981a82ec77fc7c883684aa49648092e5cf74586d90fe0f0a1f49';
const sourceBytes=await fs.readFile(path.join(root,frozen));
if(createHash('sha256').update(sourceBytes).digest('hex')!==sourceHash)throw Error('作者冻结基底已改变');
const manifest=JSON.parse(await fs.readFile(path.join(build,'render_manifest.json'),'utf8'));
const unit=96/25.4,pt=96/72,ink='#263442',grey='#77828C',border='#C8CFD4',gold='#D8A95A';
const pres=Presentation.create({slideSize:{width:6480175/9525,height:4468813/9525}});
function text(slide,value,x,y,w,h,size=6.8,bold=false,colour=ink,name='label'){
  const s=slide.shapes.add({geometry:'textbox',name:'Build | '+name,position:{left:x*unit,top:y*unit,width:w*unit,height:h*unit},fill:'none',line:{fill:'none',width:0}});
  s.text=value;s.text.style={typeface:'Arial',fontSize:size*pt,color:colour,bold,alignment:'center',verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};
  return s;
}
function box(slide,name,x,y,w,h,fill='#FFFFFF',stroke=border,geometry='roundRect'){
  return slide.shapes.add({geometry,name:'Build | '+name,position:{left:x*unit,top:y*unit,width:w*unit,height:h*unit},fill,line:{fill:stroke,width:.6*pt}});
}
function line(slide,name,points,colour=grey,width=.65){
  const xs=points.map(p=>p[0]*unit),ys=points.map(p=>p[1]*unit),x=Math.min(...xs),y=Math.min(...ys),w=Math.max(.01,Math.max(...xs)-x),h=Math.max(.01,Math.max(...ys)-y);
  return slide.shapes.add({geometry:'custom',name:'Build | '+name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:colour,width:width*pt},customPaths:[{width:w,height:h,commands:points.map((p,i)=>({[i?'lineTo':'moveTo']:{x:p[0]*unit-x,y:p[1]*unit-y}}))}]});
}
function arrow(slide,name,points,colour=grey){
  line(slide,name,points,colour);const [x,y]=points.at(-1),[u,v]=points.at(-2),a=Math.atan2(y-v,x-u),r=.85;
  line(slide,name+' head',[[x-r*Math.cos(a-.48),y-r*Math.sin(a-.48)],[x,y],[x-r*Math.cos(a+.48),y-r*Math.sin(a+.48)]],colour);
}
async function picture(slide,name,x,y,w,h){
  slide.images.add({name:'Build native '+name,blob:await fs.readFile(path.join(build,'render',name+'.png')),contentType:'image/png',alt:'PyMOL '+name,fit:'contain',position:{left:x*unit,top:y*unit,width:w*unit,height:h*unit}});
}
function engine(slide){
  box(slide,'compact density-conditioned engine',138.8,53.2,30.7,8.4,'#FAF1DE',gold);
  text(slide,'DG-PocketXMol',139.3,54.0,29.7,3.1,6.9,true);
  text(slide,'Density-conditioned fine-tuning',139.3,57.4,29.7,2.8,5.8,false,'#4D5B64');
  arrow(slide,'inputs to engine',[[154.1,49.0],[154.1,52.0]]);
}
const variants=[
  {code:'C1',figure:'fig-method-build-context',label:'整体与局部结构',pocket:'reference-pocket',cn:'真实受体与配体复合物及其局部放大。整体和局部采用同一9BJJ沉积受体与ATP参考结构。箭头表示局部放大, 不表示模型以真实配体坐标作为推理输入。',en:'A receptor–ligand complex and its local view. The same deposited 9BJJ receptor and reference ATP supply both views. The zoom arrow indicates a change in display scale.'},
  {code:'C2',figure:'fig-method-build-conditioning',label:'简化密度接入机制',pocket:'prediction-pocket',cn:'简化的密度条件注入。三维卷积读取当前配体原子附近的密度与受体信号, 经FiLM调制原子特征并参与坐标更新。图中折叠了重复的网络块, 不代表只执行一次更新。',en:'Simplified density conditioning. A 3D convolutional module reads local density and receptor signals, which modulate atom features through FiLM before coordinate updates. Repeated network blocks are collapsed in the schematic.'},
  {code:'C3',figure:'fig-method-build-poses',label:'多个输出构象',pocket:'prediction-pocket',cn:'同一口袋和视角下的三个配体输出。三幅采用9BJJ同一ATP身份的原候选坐标与对应CryoAtom2受体; 顺序用于显示, 不表示原模型排名或性能优劣。',en:'Three ligand poses in the same pocket and view. Original candidate coordinates for the same ATP identity in 9BJJ are shown with the corresponding CryoAtom2 receptor. Display order does not indicate model ranking or accuracy.'},
  {code:'C4',figure:'fig-method-build-denoising',label:'去噪过程',pocket:'prediction-pocket',cn:'密度条件去噪的示意过程。高斯初始化之后显示早期、中期和晚期三个中间状态及最终pose。各状态使用固定种子的坐标扰动构造, 不对应测得的真实采样时间步; 原子身份与数目保持不变。',en:'Schematic density-conditioned denoising. Gaussian initialisation is followed by early, middle and late intermediate states and a final pose. Fixed-seed coordinate perturbations illustrate noise levels rather than measured sampling timesteps; atom identities and count remain fixed.'}
];
for(const variant of variants){
  const slide=pres.slides.add();slide.background.fill='#FFFFFF';
  if(variant.code==='C1'){
    engine(slide);arrow(slide,'engine to complex',[[154.1,62.4],[154.1,64.2]]);
    box(slide,'global structure viewport',138.8,65.2,30.7,27.0);
    await picture(slide,'complex',139.5,65.4,29.3,22.7);
    text(slide,'Receptor–ligand complex',139.0,88.7,30.3,2.7,6.2);
    arrow(slide,'zoom into pocket',[[154.1,92.8],[154.1,96.2]]);
    text(slide,'Zoom',156.4,93.1,9.0,2.8,5.9,false,'#596873');
    box(slide,'local structure viewport',138.8,97.3,30.7,23.8);
    await picture(slide,'reference-pose',140.0,97.8,28.3,19.0);
    text(slide,'All-atom ligand pose',139.0,117.5,30.3,2.8,6.7);
  }else if(variant.code==='C2'){
    arrow(slide,'inputs to conditioner',[[154.1,49.0],[154.1,52.0]]);
    box(slide,'simplified density-conditioned engine',138.8,53.2,30.7,44.2,'#FDF9F0',gold);
    text(slide,'DG-PocketXMol',139.3,54.6,29.7,3.1,6.9,true);
    text(slide,'Atom\nfeatures',140.1,63.8,12.5,6.8,6.2);
    text(slide,'Density +\nreceptor',155.1,61.6,12.5,6.3,6.2);
    for(let row=0;row<2;row++)for(let col=0;col<3;col++)box(slide,'local density voxel',157.2+col*2.6,69.0+row*1.8,2.6,1.8,['#89BED4','#B4D9E5','#559EBB'][(row+col)%3],'none','rect');
    arrow(slide,'local readout to CNN',[[161.1,73.3],[161.1,75.3]],'#7294A6');
    box(slide,'local 3D convolution',154.9,76.2,12.9,6.1,'#F0F6F9');text(slide,'3D CNN',155.1,77.2,12.5,3.6,6.4);
    arrow(slide,'atom features into FiLM',[[146.4,71.4],[146.4,81.6]]);
    box(slide,'feature modulation FiLM',140.1,82.5,12.5,6.1,'#EDE7F5','#B8A9D9');text(slide,'FiLM',140.4,83.6,11.9,3.6,6.7);
    arrow(slide,'density condition into FiLM',[[161.1,83.1],[161.1,85.6],[153.3,85.6]],'#7294A6');
    arrow(slide,'modulated features to coordinate update',[[146.4,89.0],[146.4,90.3]]);
    box(slide,'coordinate update',140.1,91.1,27.7,5.1,'#FFFFFF');text(slide,'Coordinate update',140.4,92.0,27.1,3.1,6.3);
    arrow(slide,'updated atom coordinates to pose',[[154.1,98.2],[154.1,100.0]]);
    await picture(slide,'prediction',139.6,100.5,29.1,17.5);
    text(slide,'All-atom ligand pose',139.0,118.5,30.3,2.8,6.7);
  }else if(variant.code==='C3'){
    engine(slide);arrow(slide,'engine to alternative poses',[[154.1,62.4],[154.1,64.2]]);
    box(slide,'alternative pose output',138.8,65.0,30.7,56.1);
    for(let i=0;i<3;i++){
      await picture(slide,'pose-'+(i+1),139.6,65.4+i*17.7,29.1,17.2);
      if(i<2)line(slide,'pose separator '+i,[[141,82.9+i*17.7],[167.3,82.9+i*17.7]],'#E0E4E6',.4);
    }
    text(slide,'All-atom ligand poses',139.0,118.0,30.3,2.8,6.7);
  }else{
    text(slide,'DG-PocketXMol',138.8,53.3,30.7,3.2,6.9,true);
    text(slide,'Density-conditioned denoising',138.8,57.0,30.7,2.9,5.8,false,'#4D5B64');
    arrow(slide,'inputs to iterative denoising',[[154.1,49.0],[154.1,51.8]]);
    const labels=['Gaussian\nnoise','Early','Middle','Late','Pose'];
    for(let i=0;i<5;i++){
      const y=61.2+i*11.75;
      text(slide,labels[i],138.8,y+3.1,9.0,i===0?5.2:3.3,5.8,false,'#596873','denoising stage '+i);
      await picture(slide,'denoise-'+i,147.0,y,22.5,11.6);
      if(i<4)arrow(slide,'denoising transition '+i,[[158.3,y+11.0],[158.3,y+12.0]]);
    }
  }
}
await (await PresentationFile.exportPptx(pres)).save(path.join(build,'components.pptx'));

// 仅合并新增原生对象与媒体, 避免将作者的原5页经导入导出后重写.
const zip=await JSZip.loadAsync(sourceBytes),components=await JSZip.loadAsync(await fs.readFile(path.join(build,'components.pptx')));
const parse=t=>xml2js(t,{compact:false,captureSpacesBetweenElements:true});
const children=n=>(n?.elements||[]).filter(e=>e.type==='element');
const child=(n,name)=>children(n).find(e=>e.name===name);
const at=(n,...names)=>names.reduce((p,k)=>child(p,k),n);
const all=(n,name)=>[...children(n).filter(e=>e.name===name),...children(n).flatMap(e=>all(e,name))];
const element=(name,attributes={},elements=[])=>({type:'element',name,attributes,elements});
const read=async(part,pack=zip)=>parse(await pack.file(part).async('string'));
const save=(part,doc)=>zip.file(part,js2xml(doc,{compact:false,spaces:0}));
const clone=structuredClone,relType='http://schemas.openxmlformats.org/officeDocument/2006/relationships/';
const base=await read('ppt/slides/slide2.xml'),baseRels=await read('ppt/slides/_rels/slide2.xml.rels');
const presentation=await read('ppt/presentation.xml'),list=at(presentation,'p:presentation','p:sldIdLst');
const relations=await read('ppt/_rels/presentation.xml.rels'),relationList=child(relations,'Relationships');
const types=await read('[Content_Types].xml'),typeList=child(types,'Types');
const maxId=Math.max(...children(list).map(e=>Number(e.attributes.id)));
const commentRel=children(child(baseRels,'Relationships')).find(e=>e.attributes.Type.endsWith('/comments'));
const commentSource=path.posix.normalize('ppt/slides/'+commentRel.attributes.Target);
const comments=await read(commentSource),commentTemplate=children(children(comments)[0])[0];
const notes=await read('ppt/notesSlides/notesSlide2.xml'),noteRels=await read('ppt/notesSlides/_rels/notesSlide2.xml.rels');
const traceRelative='画图/画图代码/e2e/visualization/图表追溯.md';
const trace=(await fs.readFile(path.join(root,traceRelative),'utf8')).replace(/\r\n?/g,'\n');
const keepIds=new Set([4,11,12,768,769,770,771,773,774,775,967,1484,1485,22,27,50483,50484,50485,50486,50487,50488,50489,50490,50491]);
const newIds=[];const output=[];
for(const [index,variant] of variants.entries()){
  const partNumber=6+index,slideId=maxId+index+1,slide=clone(base),tree=at(slide,'p:sld','p:cSld','p:spTree');
  at(slide,'p:sld','p:cSld').attributes={...(at(slide,'p:sld','p:cSld').attributes||{}),name:variant.code+' '+variant.label};
  tree.elements=children(tree).filter(e=>['p:nvGrpSpPr','p:grpSpPr'].includes(e.name)||keepIds.has(Number(all(e,'p:cNvPr')[0]?.attributes.id)));
  const sr=clone(baseRels),srList=child(sr,'Relationships');
  const pocketId='rIdBuildPocket'+index,pocketMedia='ppt/media/method-build-'+index+'-pocket.png';
  zip.file(pocketMedia,await fs.readFile(path.join(build,'render',variant.pocket+'.png')));
  srList.elements.push(element('Relationship',{Id:pocketId,Type:relType+'image',Target:'../media/'+path.posix.basename(pocketMedia)}));
  const pocket=children(tree).find(e=>Number(all(e,'p:cNvPr')[0]?.attributes.id)===50483);
  all(pocket,'a:blip')[0].attributes['r:embed']=pocketId;
  const componentPart='ppt/slides/slide'+(index+1)+'.xml';
  const comp=await read(componentPart,components),compTree=at(comp,'p:sld','p:cSld','p:spTree');
  const compRels=await read('ppt/slides/_rels/slide'+(index+1)+'.xml.rels',components);
  const mediaMap=new Map();
  for(const relation of children(child(compRels,'Relationships')).filter(e=>e.attributes.Type===relType+'image')){
    const target=relation.attributes.Target.startsWith('/')?relation.attributes.Target.slice(1):path.posix.normalize('ppt/slides/'+relation.attributes.Target);
    const name='method-build-'+index+'-'+relation.attributes.Id+path.posix.extname(target),destination='ppt/media/'+name;
    zip.file(destination,await components.file(target).async('nodebuffer'));
    const rid='rIdBuild'+index+relation.attributes.Id;mediaMap.set(relation.attributes.Id,rid);
    srList.elements.push(element('Relationship',{Id:rid,Type:relType+'image',Target:'../media/'+name}));
  }
  let shapeId=60000;
  for(const object of children(compTree).filter(e=>!['p:nvGrpSpPr','p:grpSpPr'].includes(e.name))){
    const obj=clone(object);
    for(const nv of all(obj,'p:cNvPr'))nv.attributes.id=String(shapeId++);
    for(const blip of all(obj,'a:blip'))if(mediaMap.has(blip.attributes['r:embed']))blip.attributes['r:embed']=mediaMap.get(blip.attributes['r:embed']);
    tree.elements.push(obj);
  }
  const note=clone(notes),noteRelations=clone(noteRels);
  const body=all(note,'p:sp').find(e=>at(e,'p:nvSpPr','p:nvPr','p:ph')?.attributes.type==='body');
  const caption='LigandSeek-Build的'+variant.label+'示意。'+variant.cn+'\nENGLISH:\nSchematic of LigandSeek-Build. '+variant.en;
  const tx=child(body,'p:txBody');tx.elements=children(tx).filter(e=>e.name!=='a:p');
  for(const value of caption.split('\n'))tx.elements.push(element('a:p',{},[element('a:r',{},[element('a:t',{},[{type:'text',text:value}])])]));
  for(const r of children(child(noteRelations,'Relationships')))if(r.attributes.Type===relType+'slide')r.attributes.Target='../slides/slide'+partNumber+'.xml';
  const comment=clone(comments),cmList=children(comment)[0];cmList.elements=[];
  const match=trace.match(new RegExp('<!--\\s*provenance:begin\\s+'+variant.figure+'\\s*-->([\\s\\S]*?)<!--\\s*provenance:end\\s+'+variant.figure+'\\s*-->'));
  if(!match)throw Error('缺少追溯: '+variant.figure);
  const bodyText=match[1].replace(/^\s*<!--\s*provenance-meta\s+\{[\s\S]*?\}\s*-->\s*/,'').trim();
  for(const value of ['@@'+variant.figure,'PROVENANCE v1\nid: '+variant.figure+'\nsource: '+traceRelative+'\n\n'+bodyText]){
    const cm=clone(commentTemplate);cm.attributes.id='{'+randomUUID().toUpperCase()+'}';cm.attributes.created=new Date().toISOString();
    for(const mk of all(cm,'pc:sldMk'))mk.attributes.sldId=String(slideId);
    const tb=children(cm).find(e=>e.name.endsWith(':txBody'));
    tb.elements=[element('a:bodyPr'),element('a:lstStyle'),...value.split('\n').map(t=>element('a:p',{},[element('a:r',{},[element('a:t',{},[{type:'text',text:t}])])]))];cmList.elements.push(cm);
  }
  const commentPart='ppt/comments/method_build_'+partNumber+'.xml';
  for(const r of children(srList)){
    if(r.attributes.Type.endsWith('/comments'))r.attributes.Target='../comments/'+path.posix.basename(commentPart);
    if(r.attributes.Type===relType+'notesSlide')r.attributes.Target='../notesSlides/notesSlide'+partNumber+'.xml';
  }
  const rid='rIdMethodBuild'+index;newIds.push(element('p:sldId',{id:String(slideId),'r:id':rid}));
  relationList.elements.push(element('Relationship',{Id:rid,Type:relType+'slide',Target:'slides/slide'+partNumber+'.xml'}));
  for(const [part,doc,type] of [['ppt/slides/slide'+partNumber+'.xml',slide,'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'],['ppt/notesSlides/notesSlide'+partNumber+'.xml',note,'application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml'],[commentPart,comment,children(typeList).find(e=>e.attributes.PartName==='/'+commentSource).attributes.ContentType]]){
    save(part,doc);typeList.elements.push(element('Override',{PartName:'/'+part,ContentType:type}));
  }
  save('ppt/slides/_rels/slide'+partNumber+'.xml.rels',sr);save('ppt/notesSlides/_rels/notesSlide'+partNumber+'.xml.rels',noteRelations);
  output.push({...variant,page:3+index,part:partNumber,editable_objects:children(tree).length-2});
}
const originals=children(list);list.elements=[...originals.slice(0,2),...newIds,...originals.slice(2)];
save('ppt/presentation.xml',presentation);save('ppt/_rels/presentation.xml.rels',relations);save('[Content_Types].xml',types);
await fs.writeFile(path.join(build,'candidate.pptx'),await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE',compressionOptions:{level:6}}));
await fs.writeFile(path.join(build,'variants.json'),JSON.stringify({source:frozen,source_sha256:sourceHash,variants:output,original_page_mapping:{1:1,2:2,3:7,4:8,5:9}},null,2));
console.log('Four editable Build variants inserted after page 2; original five slide parts retained.');
