/**
 * 从作者冻结的第3页原生对象生成 A0–A5, 并恢复第4页误删的输入框.
 * 输入是 source/author-20261028-deb03f10.pptx, 不读取旧 temp 或当前编辑中的图集.
 * 输出 candidate.pptx、operations.json、variant_manifest.json 到 FIGURE_BUILD_ROOT.
 * ZIP 与 XML 仅作对象级补丁, 不经过图形重绘或 PPTX 导入导出往返.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { createHash, randomUUID, randomInt } from 'node:crypto';

const modules=process.env.RUNTIME_NODE_MODULES || 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const require=createRequire(path.join(modules,'__method_ab__.cjs'));
const JSZip=require('jszip');
const {xml2js,js2xml}=require('xml-js');
let root=path.dirname(fileURLToPath(import.meta.url));
while (!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false))) root=path.dirname(root);
const build=process.env.FIGURE_BUILD_ROOT;
if (!build) throw new Error('必须显式指定 FIGURE_BUILD_ROOT');
const sourceRelative='画图/画图代码/e2e/output/method-ab-variants/source/author-20261028-deb03f10.pptx';
const expectedSource='deb03f100ba843a6588b1f52849a921b77aee0319409dfca40c53ff0283c7c9f';
const input=await fs.readFile(path.join(root,sourceRelative));
if (createHash('sha256').update(input).digest('hex')!==expectedSource) throw new Error('作者冻结输入的内容发生变化');
const zip=await JSZip.loadAsync(input);
const mm=36000;
const relType='http://schemas.openxmlformats.org/officeDocument/2006/relationships/';
const palette={arrow:'77828C',skip:'A3ACB4',border:'BEC7CE',divider:'C8CFD4',box:'F4F6F7',bank:'F0F3F5',embedding:'FAFBFC'};
const containerIds=new Set([13,235,237,243,299,662,1249,1443]);
const dividerIds=new Set([303,1250,1479]);
const arrowIds=new Set([1324,1325,1328,1329,...Array.from({length:99},(_,i)=>1332+i),...Array.from({length:6},(_,i)=>1471+i),1480,1481,1482,1483,29,31]);
const variants=[
  {code:'A0',arrow:false,border:false,fill:false,label:'间距修正基准'},
  {code:'A1',arrow:true,border:false,fill:false,label:'普通箭头灰色'},
  {code:'A2',arrow:false,border:true,fill:false,label:'容器边框灰色'},
  {code:'A3',arrow:false,border:true,fill:true,label:'容器边框及填充中性化'},
  {code:'A4',arrow:true,border:true,fill:false,label:'箭头及容器边框中性化'},
  {code:'A5',arrow:true,border:true,fill:true,label:'箭头与容器完整中性化'},
];
const parse=text=>xml2js(text,{compact:false,ignoreComment:false,captureSpacesBetweenElements:true});
const serial=node=>js2xml(node,{compact:false,spaces:0});
const clone=node=>structuredClone(node);
const children=node=>(node?.elements || []).filter(n=>n.type==='element');
const child=(node,name)=>children(node).find(n=>n.name===name);
const at=(node,...names)=>names.reduce((p,n)=>child(p,n),node);
const descend=(node,name)=>[...children(node).filter(n=>n.name===name),...children(node).flatMap(n=>descend(n,name))];
const element=(name,attributes={},elements=[])=>({type:'element',name,attributes,elements});
const readXml=async part=>parse(await zip.file(part).async('string'));
const saveXml=(part,node)=>zip.file(part,serial(node));
const meta=shape=>descend(shape,'p:cNvPr')[0];
const id=shape=>Number(meta(shape)?.attributes?.id);
const xfrm=shape=>at(shape,shape.name==='p:grpSp'?'p:grpSpPr':'p:spPr','a:xfrm');
const drawable=node=>['p:sp','p:pic','p:grpSp','p:cxnSp','p:graphicFrame'].includes(node.name);
const shapeTree=slide=>at(slide,'p:sld','p:cSld','p:spTree');
const box=(shape,t=[1,1,0,0])=>{
  const x=xfrm(shape);if(!x)return null;
  const o=child(x,'a:off').attributes,e=child(x,'a:ext').attributes;
  return [(t[0]*Number(o.x)+t[2])/mm,(t[1]*Number(o.y)+t[3])/mm,t[0]*Number(e.cx)/mm,t[1]*Number(e.cy)/mm];
};
const groupTransform=(shape,t)=>{
  const x=xfrm(shape),o=child(x,'a:off').attributes,e=child(x,'a:ext').attributes;
  const c=child(x,'a:chOff').attributes,d=child(x,'a:chExt').attributes;
  const sx=Number(e.cx)/Number(d.cx),sy=Number(e.cy)/Number(d.cy);
  return [t[0]*sx,t[1]*sy,t[2]+t[0]*(Number(o.x)-sx*Number(c.x)),t[3]+t[1]*(Number(o.y)-sy*Number(c.y))];
};
function walkShapes(parent,action,t=[1,1,0,0]){
  for(const shape of children(parent).filter(drawable)){
    const recurse=action(shape,t);
    if(shape.name==='p:grpSp' && recurse!==false)walkShapes(shape,action,groupTransform(shape,t));
  }
}
function collect(slide){
  const rows=[];walkShapes(shapeTree(slide),(s,t)=>rows.push({id:id(s),name:meta(s).attributes.name,box_mm:box(s,t),type:s.name}));return rows;
}
function translate(shape,dx,t){
  const o=child(xfrm(shape),'a:off').attributes;o.x=String(Math.round(Number(o.x)+dx*mm/t[0]));
}
function extractAB(slide){
  const tree=clone(slide);
  const prune=(parent,t)=>{
    parent.elements=parent.elements.filter(s=>!drawable(s) || !box(s,t) || box(s,t)[0]<134.5);
    for(const s of children(parent).filter(s=>s.name==='p:grpSp'))prune(s,groupTransform(s,t));
  };
  prune(shapeTree(tree),[1,1,0,0]);return tree;
}
function refreshSlide(slide,name){
  at(slide,'p:sld','p:cSld').attributes ||= {};
  at(slide,'p:sld','p:cSld').attributes.name=name;
  for(const node of descend(slide,'p14:creationId'))node.attributes.val=String(randomInt(1,4294967295));
}
function recolour(shape,variant,changes){
  const sid=id(shape),sp=child(shape,'p:spPr');if(!sp)return;
  const edit=(holder,value,scope)=>{
    const color=at(holder,'a:solidFill','a:srgbClr');if(!color || color.attributes.val===value)return;
    changes.push({id:sid,name:meta(shape).attributes.name,scope,before:color.attributes.val,after:value});color.attributes.val=value;
  };
  if(variant.arrow && arrowIds.has(sid)){
    const value=sid>=1348 && sid<=1353?palette.skip:palette.arrow;
    edit(sp,value,'shape.fill');edit(child(sp,'a:ln'),value,'line.fill');
  }
  if(variant.border && containerIds.has(sid))edit(child(sp,'a:ln'),palette.border,'container.border');
  if(variant.border && dividerIds.has(sid)){
    edit(sp,palette.divider,'divider.fill');edit(child(sp,'a:ln'),palette.divider,'divider.line');
  }
  if(variant.fill && containerIds.has(sid)){
    const current=at(sp,'a:solidFill','a:srgbClr')?.attributes.val;
    if(current && current!=='FFFFFF')edit(sp,sid===1249?palette.bank:sid===1443?palette.embedding:palette.box,'container.fill');
  }
}

const baseline=await readXml('ppt/slides/slide3.xml');
const ab=extractAB(baseline);
const rows=collect(ab),lookup=new Map(rows.map(r=>[r.id,r]));
const findPanel=lookup.get(2).box_mm,matchPanel=lookup.get(3).box_mm;
const findLeft=lookup.get(13).box_mm[0]-findPanel[0];
const findRight=findPanel[0]+findPanel[2]-(lookup.get(299).box_mm[0]+lookup.get(299).box_mm[2]);
const divider=lookup.get(303).box_mm[0];
const candidateLeft=lookup.get(644).box_mm[0],candidateRight=lookup.get(635).box_mm[0]+lookup.get(635).box_mm[2];
const identityLeft=lookup.get(687).box_mm[0],identityRight=lookup.get(698).box_mm[0]+lookup.get(698).box_mm[2];
const shifts={find:(findRight-findLeft)/2,candidate:((divider-candidateRight)-(candidateLeft-matchPanel[0]))/2,
  identity:((matchPanel[0]+matchPanel[2]-identityRight)-(identityLeft-divider))/2};
const movements=[];
const positioned=clone(ab);
walkShapes(shapeTree(positioned),(shape,t)=>{
  const sid=id(shape),b=box(shape,t);if(!b)return;
  if([2,3,7,8,9,10,303].includes(sid))return false;
  if(sid===1395){
    translate(shape,shifts.candidate,t);
    const e=child(xfrm(shape),'a:ext').attributes;e.cx=String(Math.round(Number(e.cx)+(shifts.identity-shifts.candidate)*mm/t[0]));
    movements.push({id:sid,name:meta(shape).attributes.name,kind:'bridge_stretch',dx_start_mm:shifts.candidate,dx_end_mm:shifts.identity});return false;
  }
  let region=null;
  if(sid===1396)region='identity';
  else if(b[1]>=7 && b[1]+b[3]<=51.4)region='find';
  else if(b[1]>=57.5 && b[0]+b[2]<=divider+.03)region='candidate';
  else if(b[1]>=57.5 && b[0]>=divider-.03)region='identity';
  if(region){translate(shape,shifts[region],t);movements.push({id:sid,name:meta(shape).attributes.name,region,dx_mm:shifts[region]});return false;}
});

const presentation=await readXml('ppt/presentation.xml');
const presRoot=child(presentation,'p:presentation');
const slideList=child(presRoot,'p:sldIdLst');
const presRels=await readXml('ppt/_rels/presentation.xml.rels');
const relationList=child(presRels,'Relationships');
const types=await readXml('[Content_Types].xml'),typeList=child(types,'Types');
const sourceRels=await readXml('ppt/slides/_rels/slide3.xml.rels');
const sourceRelationList=child(sourceRels,'Relationships');
const sourceCommentRel=children(sourceRelationList).find(r=>r.attributes.Type.endsWith('/comments'));
const sourceCommentPart=path.posix.normalize('ppt/slides/'+sourceCommentRel.attributes.Target);
const sourceComments=await readXml(sourceCommentPart);
const commentRoot=children(sourceComments)[0],commentTemplate=children(commentRoot)[0];
const sourceNotes=await readXml('ppt/notesSlides/notesSlide3.xml');
const notesRelTemplate=await readXml('ppt/notesSlides/_rels/notesSlide3.xml.rels');
const traceRelative='画图/画图代码/e2e/visualization/图表追溯.md';
const trace=(await fs.readFile(path.join(root,traceRelative),'utf8')).replace(/\r\n?/g,'\n');
const maxSlideId=Math.max(...children(slideList).map(n=>Number(n.attributes.id)));
const captionCN='LigandSeek-Find 与 LigandSeek-Match 的网络架构和数据流。\na，Find 对密度和受体信息进行编码，生成候选配体区域和辅助特征。三维 U-Net 与 Point Transformer V3 结合密度和受体原子特征，并通过迭代回收机制更新表示。\nb，Match 通过候选编码器和身份编码器进行前景判别与配体身份匹配。候选编码器融合局部密度、口袋、候选区域及辅助特征；身份编码器整合分子图、SMI-TED 表示及同一 PDB 条目中的身份上下文。前景头预测前景概率，余弦评分给出候选与身份的匹配分数。';
const captionEN='Network architecture and data flow of LigandSeek-Find and LigandSeek-Match.\na, Find encodes density and receptor information to produce candidate ligand regions and auxiliary features. A 3D U-Net and Point Transformer V3 combine density and receptor-atom features, with recycling to update representations.\nb, Match uses candidate and identity encoders for foreground classification and ligand identity matching. The candidate encoder combines local density, pocket, candidate-region and auxiliary features. The identity encoder integrates molecular graphs, SMI-TED representations and identity context within the same PDB entry. A foreground head predicts foreground probability, and cosine scoring produces candidate-to-identity matching scores.';

function noteFor(page){
  const doc=clone(sourceNotes);
  const body=descend(doc,'p:sp').find(s=>at(s,'p:nvSpPr','p:nvPr','p:ph')?.attributes.type==='body');
  const tx=child(body,'p:txBody');tx.elements=children(tx).filter(n=>n.name!=='a:p');
  for(const line of (captionCN+'\nENGLISH:\n'+captionEN).split('\n'))tx.elements.push(element('a:p',{},[element('a:r',{},[element('a:t',{},[{type:'text',text:line}])])]));
  const relation=clone(notesRelTemplate);
  for(const r of children(child(relation,'Relationships')))if(r.attributes.Type===relType+'slide')r.attributes.Target='../slides/slide'+page+'.xml';
  return [doc,relation];
}
function commentsFor(figure,slideId,managed){
  const doc=clone(sourceComments),list=children(doc)[0];list.elements=[];
  const values=['@@'+figure];
  if(managed){
    const regex=new RegExp('<!--\\s*provenance:begin\\s+'+figure+'\\s*-->([\\s\\S]*?)<!--\\s*provenance:end\\s+'+figure+'\\s*-->');
    const block=trace.match(regex);if(!block)throw new Error('缺少候选追溯记录: '+figure);
    const body=block[1].replace(/^\s*<!--\s*provenance-meta\s+\{[\s\S]*?\}\s*-->\s*/,'').trim();
    values.push('PROVENANCE v1\nid: '+figure+'\nsource: '+traceRelative+'\n\n'+body);
  }
  for(const value of values){
    const cm=clone(commentTemplate);cm.attributes.id='{'+randomUUID().toUpperCase()+'}';cm.attributes.created=new Date().toISOString();
    for(const mk of descend(cm,'pc:sldMk'))mk.attributes.sldId=String(slideId);
    const tx=children(cm).find(n=>n.name.endsWith(':txBody'));
    tx.elements=[element('a:bodyPr'),element('a:lstStyle'),...value.split('\n').map(line=>element('a:p',{},[element('a:r',{},[element('a:t',{},[{type:'text',text:line}])])]))];
    list.elements.push(cm);
  }
  return doc;
}
function registerType(part,contentType){
  const full='/'+part;
  if(!children(typeList).some(n=>n.attributes.PartName===full))typeList.elements.push(element('Override',{PartName:full,ContentType:contentType}));
}
async function putSlide(page,slide,figure,slideId,managed){
  const relations=clone(sourceRels),list=child(relations,'Relationships');
  const commentPart='ppt/comments/method_ab_'+page+'.xml';
  for(const r of children(list)){
    if(r.attributes.Type.endsWith('/comments'))r.attributes.Target='../comments/method_ab_'+page+'.xml';
    if(r.attributes.Type===relType+'notesSlide')r.attributes.Target='../notesSlides/notesSlide'+page+'.xml';
  }
  saveXml('ppt/slides/slide'+page+'.xml',slide);saveXml('ppt/slides/_rels/slide'+page+'.xml.rels',relations);
  const [note,noteRelations]=noteFor(page);
  saveXml('ppt/notesSlides/notesSlide'+page+'.xml',note);saveXml('ppt/notesSlides/_rels/notesSlide'+page+'.xml.rels',noteRelations);
  saveXml(commentPart,commentsFor(figure,slideId,managed));
  registerType('ppt/slides/slide'+page+'.xml','application/vnd.openxmlformats-officedocument.presentationml.slide+xml');
  registerType('ppt/notesSlides/notesSlide'+page+'.xml','application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml');
  registerType(commentPart,children(typeList).find(n=>n.attributes.PartName==='/'+sourceCommentPart).attributes.ContentType);
}

const repaired=clone(ab);refreshSlide(repaired,'a/b / baseline copy restored');
await putSlide(4,repaired,'fig-method-v9-EDITING-4',Number(children(slideList)[3].attributes.id),false);
const manifest=[],colourChanges={};
for(const [index,variant] of variants.entries()){
  const page=6+index,figure='fig-method-ab-'+variant.code.toLowerCase(),slide=clone(positioned);
  const changes=[];walkShapes(shapeTree(slide),shape=>recolour(shape,variant,changes));
  refreshSlide(slide,variant.code+' / '+variant.label);
  const rid='rIdMethodAB'+variant.code,sid=maxSlideId+index+1;
  slideList.elements.push(element('p:sldId',{id:String(sid),'r:id':rid}));
  relationList.elements.push(element('Relationship',{Id:rid,Type:relType+'slide',Target:'slides/slide'+page+'.xml'}));
  await putSlide(page,slide,figure,sid,true);
  manifest.push({...variant,page,figure,source_slide:3,only_panels:['a','b'],objects:collect(slide).length});colourChanges[variant.code]=changes;
}
saveXml('ppt/presentation.xml',presentation);saveXml('ppt/_rels/presentation.xml.rels',presRels);saveXml('[Content_Types].xml',types);
await fs.mkdir(build,{recursive:true});
await fs.writeFile(path.join(build,'candidate.pptx'),await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE',compressionOptions:{level:6}}));
await fs.writeFile(path.join(build,'variant_manifest.json'),JSON.stringify(manifest,null,2));
await fs.writeFile(path.join(build,'operations.json'),JSON.stringify({source:sourceRelative,source_sha256:expectedSource,palette,
  container_ids:[...containerIds],divider_ids:[...dividerIds],arrow_ids:[...arrowIds],shifts_mm:shifts,
  spacing_definition:{find_card_gutters_before_mm:[findLeft,findRight],candidate_body_before_mm:[candidateLeft-matchPanel[0],divider-candidateRight],identity_body_before_mm:[identityLeft-divider,matchPanel[0]+matchPanel[2]-identityRight]},
  movements,colour_changes:colourChanges,original_ab:collect(ab),positioned_ab:collect(positioned),preserved_pages:[1,2,3,5],repaired_page:4},null,2));
console.log('A0–A5 generated from the saved author baseline; original pages 1, 2, 3 and 5 retained.');
