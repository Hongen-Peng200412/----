// 只构造本轮新增的可编辑图形；作者原有网络及真实几何由 assemble.py 原样承接。
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import sharp from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/dist/index.mjs';

let root=path.dirname(fileURLToPath(import.meta.url));
while (!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false))) root=path.dirname(root);
const build=process.env.FIGURE_BUILD_ROOT;
const geometry=JSON.parse(await fs.readFile(path.join(build,'geometry.json'),'utf8'));
const manifest=JSON.parse(await fs.readFile(path.join(build,'render/render_manifest.json'),'utf8'));
const display=path.join(build,'display');await fs.mkdir(display,{recursive:true});
const selected=['9bjj_16','9llg_2','30ga_7','9wup_2'];
const ink='#263442',sub='#687780',green='#50B982',yellow='#DDAF36',red='#E36A7C';
let count=0;
let commonStructureCrop;
function text(slide,t,x,y,w,h,size=14,color=ink,bold=false,align='left',name='label'){
  const s=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  s.text=t;s.text.style={typeface:'Arial',fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};return s;
}
function shape(slide,name,x,y,w,h,fill,stroke,width=1,geometry='rect'){
  return slide.shapes.add({geometry,name,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width}});
}
function line(slide,name,points,color=ink,width=1.5){
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys),w=Math.max(.01,Math.max(...xs)-x),h=Math.max(.01,Math.max(...ys)-y);
  slide.shapes.add({geometry:'custom',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:color,width},customPaths:[{width:w,height:h,commands:points.map((p,i)=>({[i?'lineTo':'moveTo']:{x:p[0]-x,y:p[1]-y}}))}]});
}
function arrow(slide,name,x1,y1,x2,y2,color=ink,width=1.6){
  line(slide,name,[[x1,y1],[x2,y2]],color,width);
  const angle=Math.atan2(y2-y1,x2-x1),s=width>2?9:4.2;
  line(slide,name+'-head',[[x2-s*Math.cos(angle-.44),y2-s*Math.sin(angle-.44)],[x2,y2],[x2-s*Math.cos(angle+.44),y2-s*Math.sin(angle+.44)]],color,width);
}
function molecule(slide,smiles,box,color){
  const data=geometry.molecules.find(d=>d.smiles===smiles),xs=data.atoms.map(a=>a.x),ys=data.atoms.map(a=>a.y);
  const minx=Math.min(...xs),maxx=Math.max(...xs),miny=Math.min(...ys),maxy=Math.max(...ys);
  const scale=Math.min((box[2]-24)/Math.max(1,maxx-minx),(box[3]-20)/Math.max(1,maxy-miny));
  const pts=data.atoms.map(a=>[box[0]+box[2]/2+(a.x-(maxx+minx)/2)*scale,box[1]+box[3]/2-(a.y-(maxy+miny)/2)*scale]);
  for(const b of data.bonds){let p=[...pts[b.start]],q=[...pts[b.stop]];const dx=q[0]-p[0],dy=q[1]-p[1],norm=Math.hypot(dx,dy);if(data.atoms[b.start].element!=='C')p=[p[0]+dx/norm*13,p[1]+dy/norm*13];if(data.atoms[b.stop].element!=='C')q=[q[0]-dx/norm*13,q[1]-dy/norm*13];line(slide,'F1-identity-bond-'+count++,[p,q],color,2.5);if(b.order>=2){let ox=-dy/norm*3.8,oy=dx/norm*3.8;const centre=[box[0]+box[2]/2,box[1]+box[3]/2];if((centre[0]-(p[0]+q[0])/2)*ox+(centre[1]-(p[1]+q[1])/2)*oy<0){ox=-ox;oy=-oy;}line(slide,'F1-identity-bond-'+count++,[[p[0]+ox,p[1]+oy],[q[0]+ox,q[1]+oy]],color,1.7);}}
  for(const [i,a] of data.atoms.entries())if(a.element!=='C'){const label=a.element+(a.hydrogens?'H'+(a.hydrogens>1?'₂':''):'');const width=label.length*10;shape(slide,'F1-identity-atom-background',pts[i][0]-6,pts[i][1]-8,width,16,'#FFFFFF','none',0);text(slide,label,pts[i][0]-7,pts[i][1]-10,width,20,14,color,true,'left','F1-identity-atom');}
}
async function picture(slide,relative,box,name){
  const input=path.join(build,'render',relative),output=path.join(display,relative.replaceAll('/','-'));
  const source=sharp(input);
  if(relative.startsWith('pockets/') || relative==='method-output.png')source.extract(commonStructureCrop);
  else source.trim({threshold:8});
  await source.extend({top:25,bottom:25,left:25,right:25,background:{r:255,g:255,b:255,alpha:0}}).png().toFile(output);
  slide.images.add({blob:await fs.readFile(output),contentType:'image/png',alt:name,fit:'contain',position:{left:box[0],top:box[1],width:box[2],height:box[3]}});
}
function smiles(slide,x,y,w,size,lineHeight,prefix){
  const entries=['CCO','CC(=O)O','Cc1ccccc1','CC(N)=O'];
  shape(slide,prefix+'-selected',x-3,y+2*lineHeight-1,w+6,lineHeight+1,'#DCF8EB','#499D86',1,'roundRect');
  for(const [i,s] of entries.entries())text(slide,s,x,y+i*lineHeight,w,lineHeight,size,i===2?'#24634E':ink,false,'left',prefix+'-SMILES-'+i);
}
function cube(slide,x,y,size){
  const k=size*.26;
  line(slide,'crop-cube',[[x,y+k],[x+size-k,y+k],[x+size-k,y+size],[x,y+size],[x,y+k],[x+k,y],[x+size,y],[x+size,y+size-k],[x+size-k,y+size]],'#263442',.9);
  line(slide,'crop-cube',[[x+size-k,y+k],[x+size,y]],'#263442',.9);
}

// Pocket 与输出使用同一裁剪矩形，切换 sticks/surface 不改变受体画面的尺度。
let x0=1500,y0=1100,x1=0,y1=0;
for(const relative of ['method-output.png',...['match','build'].flatMap(role=>['atoms','surface','cartoon'].map(mode=>'pockets/'+role+'-'+mode+'.png'))]){
  const {data,info}=await sharp(path.join(build,'render',relative)).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++)if(data[(y*info.width+x)*4+3]>8){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
}
commonStructureCrop={left:x0,top:y0,width:x1-x0+1,height:y1-y0+1};

const overview=Presentation.create({slideSize:{width:1250,height:480}});
const s=overview.slides.add();s.background.fill='#FFFFFF';
// 这里只新增已获授权的输入、化学身份、直线匹配及真实 pose；旧组件由装配器复用。
shape(s,'F1-Find-input-frame',18,58,178,291,'none','#BAC8D1',1,'roundRect');
shape(s,'F1-SMILES-input-frame',18,355,178,119,'none','#BAC8D1',1,'roundRect');
for(let y=205;y<223;y+=5)line(s,'CryoAtom2-dashed',[[106,y],[106,y+2.5]],sub,1.3);
arrow(s,'CryoAtom2-arrow',106,220,106,229,sub,1.2);
text(s,'CryoAtom2',114,207,78,17,14,sub);
smiles(s,35,366,142,14,19,'F1-input');
text(s,'SMILES',35,449,142,20,14,ink,false,'center','F1-input-label');
text(s,'Ligand identities',651,58,169,20,15,sub,false,'center','F1-identity-title');
for(const [id,y1,y2,color] of [['B1',112,189,green],['B2',175,189,green],['B3',238,238,'#737C84'],['B4',301,112,yellow],['B5',365,365,red]]){
  line(s,'F1-match-straight-'+id,[[564,y1],[666,y2]],color,2.6);
}
molecule(s,'CCO',[676,86,120,55],yellow);
molecule(s,'Cc1ccccc1',[676,161,120,55],green);
text(s,'Same identity',671,206,132,20,14,green,false,'center','F1-same-identity');
text(s,'∅  Reject',676,224,120,21,16,sub,false,'center','F1-reject');
text(s,'False positive',669,249,136,19,14,sub,false,'center','F1-false-positive');
molecule(s,'CC(N)=O',[676,338,120,55],red);
line(s,'F1-SMILES-to-identities',[[196,433],[737,433],[737,397]],ink,1.7);
arrow(s,'F1-SMILES-identity-entry',737,407,737,397,ink,1.7);
for(const [i,caseId] of selected.entries()){
  const x=918+(i%2)*164,y=73+Math.floor(i/2)*184;
  shape(s,'F1-pose-viewport-'+i,x,y,157,155,'#FFFFFF','none',0);
  await picture(s,'poses/'+caseId+'.png',[x,y,157,155],'Real predicted pose '+caseId);
}
await (await PresentationFile.exportPptx(overview)).save(path.join(build,'overview-components.pptx'));

const method=Presentation.create({slideSize:{width:680.333333,height:469.166667}});
const a=method.slides.add();a.background.fill='#FFFFFF';
// 密度库只替换图示；原预处理框、分隔、标题、56 channels 和所有拓扑仍取自作者页。
for(let i=8;i>=0;i--)shape(a,'F2-bank-channel',144+i*.8,59-i*.7,27,20,'#EBF7FC','#A6C5DF',.45);
for(let i=0;i<4;i++)for(let j=0;j<4;j++)shape(a,'F2-density-voxel',146+j*5.5,60+i*4.5,5.5,4.5,['#CCE5EE','#86C0D7','#4D9ABB','#B6DDE7'][(i+j)%4],'none',0);
text(a,'Spatial\ntransform',101.5,46,39.5,19,7.2,ink,false,'center','F2-spatial-transform');
text(a,'Atom\nembeddings',101.5,123,39.5,19,7.2,ink,false,'center','F2-atom-embeddings-input');
cube(a,73.5,65.8,12.5);text(a,'80³',67.25,80.5,25,10,8,ink,true,'center','F2-density-crop-size');
cube(a,73.5,147.5,12.5);text(a,'80³',67.25,162.2,25,10,8,ink,true,'center','F2-receptor-crop-size');
await picture(a,'pockets/match-atoms.png',[69,312,49,36],'Match receptor pocket — scheme 2B');
await picture(a,'pockets/build-atoms.png',[585,51,56,36],'Build receptor pocket — scheme 2B');
const bx=532,by=114,row=7.8,gap=4.2;
shape(a,'F2-Build-selected',bx-2,by+2*row+gap-0.6,41,row+0.8,'#DCF8EB','#499D86',.75,'roundRect');
for(const [t,dy] of [['CCO',0],['CC(=O)O',row],['…',2*row],['Cc1ccccc1',2*row+gap],['CC(N)=O',3*row+gap]]){
  if(t==='…'){for(let i=0;i<3;i++)shape(a,'F2-Build-continuation',bx+i*2.1,by+dy+gap/2,.7,.7,sub,'none',0,'ellipse');}
  else text(a,t,bx,by+dy,38,row,7.2,t==='Cc1ccccc1'?'#24634E':ink,false,'left','F2-Build-SMILES-'+dy);
}
await picture(a,'method-output.png',[525,365,116,70],'9BJJ ATP B:901 frozen Top-1 pose');
await (await PresentationFile.exportPptx(method)).save(path.join(build,'method-components.pptx'));

// 一页统一组件板：16 个真实 pose、两处 Pocket 的三种表示及两种 SMILES 组件。
// 两份正式 PPT 直接插入同一页内容，配色分支不再与 Pocket 方案做笛卡尔积。
const board=Presentation.create({slideSize:{width:680.333333,height:469.166667}});
const b=board.slides.add();b.background.fill='#FFFFFF';
text(b,'Reusable components',14,9,650,24,17,ink,true);
text(b,'Pose candidates',14,37,420,16,11,ink,true);
text(b,'Match Pocket',452,37,99,16,10,ink,true,'center');
text(b,'Build Pocket',562,37,99,16,10,ink,true,'center');
for(const [i,r] of manifest.poses.entries()){
  const x=14+(i%4)*106,y=57+Math.floor(i/4)*100;
  const chosen=selected.includes(r.case);
  shape(b,'Candidate-'+r.case,x,y,101,93,'none',chosen?'#499D86':'#DFE5E9',chosen?1:.55);
  await picture(b,'poses/'+r.case+'.png',[x+3,y+2,95,68],'Pose candidate '+r.case);
  text(b,r.pdb_id.toUpperCase()+' · '+r.ligand,x+3,y+71,95,11,8.8,ink,chosen,'center','Candidate-identity');
  text(b,r.chain+':'+r.residue,x+3,y+82,95,9,7.5,sub,false,'center','Candidate-instance');
}
for(const [i,mode] of ['surface','atoms','cartoon'].entries()){
  const y=57+i*79;
  for(const [j,role] of ['match','build'].entries()){
    const x=452+j*110;
    shape(b,'Pocket-viewport-'+role+'-'+mode,x,y,99,75,'none','#DFE5E9',.55);
    await picture(b,'pockets/'+role+'-'+mode+'.png',[x+2,y+2,95,56],role+' Pocket '+mode);
    text(b,mode==='surface'?'1 · surface':mode==='atoms'?'2B · sticks':'Cartoon only',x+2,y+60,95,12,8,ink,false,'center','Pocket-variant-label');
  }
}
text(b,'SMILES input',452,301,99,16,10,ink,true,'center');
text(b,'Build SMILES',562,301,99,16,10,ink,true,'center');
shape(b,'Board-input-SMILES-frame',452,322,99,103,'none','#BAC8D1',.8,'roundRect');
smiles(b,461,330,80,10,18,'Board-input');
text(b,'SMILES',460,404,83,15,9,ink,false,'center');
shape(b,'Board-build-SMILES-frame',562,322,99,103,'none','#BAC8D1',.8,'roundRect');
shape(b,'Board-build-selected',568,368,86,15,'#DCF8EB','#499D86',.8,'roundRect');
for(const [t,y] of [['CCO',329],['CC(=O)O',346],['…',360],['Cc1ccccc1',369],['CC(N)=O',388]]){
  if(t==='…'){for(let i=0;i<3;i++)shape(b,'Board-build-continuation',571+i*3,y+3,1,1,sub,'none',0,'ellipse');}
  else text(b,t,571,y,80,14,10,t==='Cc1ccccc1'?'#24634E':ink,false,'left','Board-build-SMILES');
}
text(b,'Green frames mark the four examples used in Fig. 1.',452,435,209,22,8.3,sub,false,'left');
await (await PresentationFile.exportPptx(board)).save(path.join(build,'component-board.pptx'));
await fs.writeFile(path.join(build,'selection.json'),JSON.stringify({selected,pose_count:manifest.poses.length,default_colour:'text',default_pocket:'atoms',pocket_alternatives:['surface','atoms','cartoon'],common_structure_crop:commonStructureCrop},null,2));
console.log('Native components generated; one common alternatives board; colour and Pocket choices are independent.');
