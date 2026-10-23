import fs from 'node:fs/promises';
import path from 'node:path';
import { Presentation, PresentationFile } from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import sharp from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/dist/index.mjs';
import { fileURLToPath as provenanceFilePath } from 'node:url';
import { existsSync as provenanceExists } from 'node:fs';

// 从脚本位置识别论文仓库, 不依赖目录层数或调用时的工作目录.
let repoRoot = path.dirname(provenanceFilePath(import.meta.url));
while (!(provenanceExists(path.join(repoRoot, 'AGENTS.md')) && provenanceExists(path.join(repoRoot, '论文草稿.md')))) {
  const parent = path.dirname(repoRoot);
  if (parent === repoRoot) throw new Error('找不到含 AGENTS.md 与论文草稿.md 的仓库根目录');
  repoRoot = parent;
}
process.env.RUNTIME_NODE_MODULES ??= 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';


const root = path.join(repoRoot, '画图/画图代码/e2e/output/fig-overview_v2');
const build = process.env.FIGURE_BUILD_ROOT ? path.resolve(process.env.FIGURE_BUILD_ROOT) : path.join(repoRoot,'temp/fig-overview_v2');
await fs.mkdir(build,{recursive:true});
const regenerated=process.env.FIGURE_BUILD_ROOT ? path.join(process.env.FIGURE_BUILD_ROOT,'published') : path.join(root,'regenerated');
await fs.mkdir(regenerated,{recursive:true});
const geo = JSON.parse(await fs.readFile(path.join(build,'geometry.json'),'utf8'));
const blobs = JSON.parse(await fs.readFile(path.join(build,'blobs.json'),'utf8'));
const W=1800,H=680;
const p=Presentation.create({slideSize:{width:W,height:H}});
p.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
const slide=p.slides.add(); slide.background.fill='#FFFFFF';
const C={ink:'#263442',sub:'#687780',line:'#87929B',green:'#50B982',yellow:'#DDAF36',red:'#E36A7C',gray:'#5C6570'};
let seq=0,svg=[];
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const rgb=h=>h.replace('#','').match(/../g).map(x=>parseInt(x,16));
const hex=a=>'#'+a.map(x=>Math.max(0,Math.min(255,Math.round(x))).toString(16).padStart(2,'0')).join('');
const mix=(a,b,t)=>hex(rgb(a).map((v,i)=>v*(1-t)+rgb(b)[i]*t));
function polygon(points,fill,stroke='none',width=0,name='shape',close=true){
 const xs=points.map(a=>a[0]),ys=points.map(a=>a[1]);
 const x=Math.min(...xs),y=Math.min(...ys),w=Math.max(.01,Math.max(...xs)-x),h=Math.max(.01,Math.max(...ys)-y);
 const commands=points.map((a,i)=>({[i?'lineTo':'moveTo']:{x:a[0]-x,y:a[1]-y}})); if(close)commands.push({close:{}});
 slide.shapes.add({geometry:'custom',name:name+'__'+seq++,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width},customPaths:[{width:w,height:h,commands}]});
 svg.push(`<path d="${points.map((a,i)=>(i?'L':'M')+a.join(',')).join(' ')}${close?' Z':''}" fill="${fill}" stroke="${stroke}" stroke-width="${width}" stroke-linejoin="round" stroke-linecap="round"/>`);
}
function multi(polys,fill,name,stroke='none',width=0){
 const points=polys.flat(),xs=points.map(a=>a[0]),ys=points.map(a=>a[1]);
 const x=Math.min(...xs),y=Math.min(...ys),w=Math.max(.01,Math.max(...xs)-x),h=Math.max(.01,Math.max(...ys)-y);
 const commands=polys.flatMap(points=>[...points.map((a,i)=>({[i?'lineTo':'moveTo']:{x:a[0]-x,y:a[1]-y}})),{close:{}}]);
 slide.shapes.add({geometry:'custom',name:name+'__'+seq++,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width},customPaths:[{width:w,height:h,commands}]});
 svg.push(`<path d="${polys.map(points=>points.map((a,i)=>(i?'L':'M')+a.join(',')).join(' ')+' Z').join(' ')}" fill="${fill}" stroke="${stroke}" stroke-width="${width}" stroke-linejoin="round"/>`);
}
function line(points,color=C.line,width=1.6,name='line'){polygon(points,'none',color,width,name,false);}
function text(t,x,y,w,h,size=22,color=C.ink,bold=false,align='left',name='label'){
 const s=slide.shapes.add({geometry:'textbox',name:name+'__'+seq++,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 s.text=t;s.text.style={typeface:'Arial',fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};
 const lines=t.split('\n');lines.forEach((t,i)=>svg.push(`<text x="${align==='center'?x+w/2:x}" y="${y+h/2+(i-(lines.length-1)/2)*size*1.2+size*.34}" font-family="Arial" font-size="${size}" font-weight="${bold?700:400}" text-anchor="${align==='center'?'middle':'start'}" fill="${color}">${esc(t)}</text>`));
}
function circle(x,y,r,fill,stroke='none',width=0,name='atom'){
 slide.shapes.add({geometry:'ellipse',name:name+'__'+seq++,position:{left:x-r,top:y-r,width:2*r,height:2*r},fill,line:{fill:stroke,width}});
 svg.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${width}"/>`);
}
function arrow(x1,y,x2,label){
 line([[x1,y],[x2-10,y]],C.ink,2.3,'flow_'+label);
 polygon([[x2,y],[x2-12,y-6],[x2-12,y+6]],C.ink,'none',0,'flow_'+label);
 if(label)text(label,x1-10,y-43,x2-x1+20,32,26,C.ink,true,'center');
}
// 真实密度的三角网格按深度和颜色归并成可编辑的自由轮廓。
const vx=geo.vertices.map(v=>v[0]),vy=geo.vertices.map(v=>v[1]);
const b=[Math.min(...vx),Math.min(...vy),Math.max(...vx),Math.max(...vy)];
function transform(box){const [x,y,w,h]=box,s=Math.min(w/(b[2]-b[0]),h/(b[3]-b[1]));return v=>[x+w/2+(v[0]-(b[0]+b[2])/2)*s,y+h/2-(v[1]-(b[1]+b[3])/2)*s];}
function density(box,pale,name){
 const trans=transform(box), bins=new Map();
 for(const t of geo.triangles){
  const nv=t.map(i=>geo.normals[i]).reduce((a,v)=>a.map((x,k)=>x+v[k]/3),[0,0,0]);if(nv[2]<-.06)continue;
  const vv=t.map(i=>geo.vertices[i]),depth=Math.floor(vv.reduce((a,v)=>a+v[2]/3,0)/3);
  const shade=Math.round(Math.max(0,Math.min(1,.53+.25*nv[2]-.15*nv[0]+.18*nv[1]))*12);
  const key=depth+':'+shade;if(!bins.has(key))bins.set(key,[]);bins.get(key).push(vv.map(trans));
 }
 for(const [key,polys] of [...bins.entries()].sort((a,b)=>parseInt(a[0])-parseInt(b[0]))){
  const shade=Number(key.split(':')[1])/12;
  const base=mix('#8597A4','#E0E6EB',shade),color=mix(base,'#FFFFFF',pale);
  multi(polys,color,name,color,.16);
 }
}
function receptor(box,pale,name){
 const trans=transform(box),segs=[];
 for(const chain of geo.chains){for(let i=1;i<chain.length;i++){
  const a=chain[i-1],bb=chain[i];if(Math.hypot(...a.slice(0,3).map((v,k)=>v-bb[k]))>5)continue;
  segs.push({a:trans(a),b:trans(bb),z:(a[2]+bb[2])/2,ss:bb[3]});
 }}
 segs.sort((a,b)=>a.z-b.z);
 const z0=Math.min(...segs.map(s=>s.z)),z1=Math.max(...segs.map(s=>s.z));
 for(const s of segs){const t=(s.z-z0)/(z1-z0),color=mix(mix('#617787','#B4C1CB',t),'#FFFFFF',pale);
  line([s.a,s.b],color,s.ss===0?.85:2.1,name);
 }
}
// 候选形状为流程示意；重复绿色使用同一几何和同一色彩。
function blob(x,y,w,h,color,kind,name,mesh=true){
 const g=blobs[kind],bins=new Map();
 for(const t of g.t){const vs=t.map(i=>g.v[i]),z=vs.reduce((a,v)=>a+v[2]/3,0);if(z<-.04)continue;
  const bin=Math.round(z*18);if(!bins.has(bin))bins.set(bin,[]);
  bins.get(bin).push(vs.map(v=>[x+v[0]*w,y-v[1]*h]));
 }
 for(const [bin,polys] of [...bins.entries()].sort((a,b)=>a[0]-b[0])){
  const fc=mix(color,'#FFFFFF',.02+bin/18*.48);
  multi(polys,fc,name,mesh?mix(color,'#FFFFFF',.55):fc,mesh?.42:.15);
 }
}
const mols=[
 {nodes:[[-1,0],[-.5,-.86],[.5,-.86],[1,0],[.5,.86],[-.5,.86],[1.85,-.4],[2.65,.1],[3.3,-.55],[-1.8,.5],[-2.5,.1]],edges:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,0],[3,6],[6,7],[7,8],[0,9],[9,10]]},
 {nodes:[[-1,0],[-.5,-.86],[.5,-.86],[1,0],[.5,.86],[-.5,.86],[1.8,-.5],[2.65,0],[2.65,1],[1.8,1.4],[-1.8,-.5],[-2.55,-.1]],edges:[[0,1],[1,2],[2,3],[3,4],[4,5],[5,0],[3,6],[6,7],[7,8],[8,9],[9,4],[0,10],[10,11]]},
 {nodes:[[-1,0],[-.3,-.8],[.6,-.5],[.6,.5],[-.3,.8],[1.55,-.9],[2.4,-.45],[2.4,.55],[1.55,1],[-1.8,.6],[-2.6,.1]],edges:[[0,1],[1,2],[2,3],[3,4],[4,0],[2,5],[5,6],[6,7],[7,8],[8,3],[0,9],[9,10]]}
];
function molecule(cx,cy,scale,color,kind,name,pose=false){
 const m=mols[kind],coords=m.nodes.map(([x,y],i)=>pose?[cx+x*scale+Math.sin(i)*scale*.18,cy+y*scale*.7+Math.cos(i*.9)*scale*.35]:[cx+x*scale,cy+y*scale]);
 m.edges.forEach(([a,b])=>line([coords[a],coords[b]],color,pose?3.5:2.6,name));
 coords.forEach(([x,y],i)=>circle(x,y,pose?3.7:2.1,i%5===0?mix(color,'#FFFFFF',.22):color,'#FFFFFF',pose?.45:0,name));
}

text('a',28,18,40,44,38,C.ink,true);
text('From cryo-EM maps to ligand poses',80,21,1030,40,29,C.ink,true);
text('Whole-map inputs',24,97,215,36,23,C.ink,true,'center');
text('Candidate ligand regions',342,97,410,36,23,C.ink,true,'center');
text('Ligand identity assignment',860,97,355,36,23,C.ink,true,'center');
text('Structure building',1300,97,210,36,23,C.ink,true,'center');
text('Ligand poses',1540,97,230,36,23,C.ink,true,'center');

density([43,156,178,190],.12,'Input_density');
text('Cryo-EM map',22,351,216,27,20,C.ink,false,'center');
receptor([43,421,178,178],.03,'Input_receptor');
text('Receptor structure',18,610,226,27,20,C.ink,false,'center');
text('+',110,384,35,30,28,C.sub,false,'center');
arrow(242,343,326,'Find');

density([349,157,388,425],.49,'Candidate_density');
// 浅色主链与密度共同提供空间背景。
receptor([349,157,388,425],.77,'Candidate_receptor');
const sites=[{x:455,y:274,w:49,h:74,c:C.green,k:0,id:'B1'},
 {x:634,y:430,w:49,h:74,c:C.green,k:0,id:'B2'},
 {x:516,y:457,w:49,h:59,c:C.yellow,k:1,id:'B3'},
 {x:602,y:232,w:44,h:69,c:C.red,k:2,id:'B4'},
 {x:441,y:395,w:44,h:51,c:C.gray,k:1,id:'B5'}];
for(const s of sites){blob(s.x,s.y,s.w,s.h,s.c,s.k,'Candidate_'+s.id);text(s.id,s.x+s.w*.4+3,s.y-12,35,26,16,mix(s.c,C.ink,.25),true);}
text('Map + receptor + predicted blobs',329,602,430,28,20,C.sub,false,'center');
arrow(752,343,841,'Match');
text('AUX',765,385,70,25,16,C.sub,false,'center');
line([[774,382],[819,382]],C.line,1,'AUX');

const ys=[211,286,371,456,548],ids=['B1','B4','B3','B2','B5'];
const cc=[C.green,C.red,C.yellow,C.green,C.gray],ks=[0,2,1,0,1];
const targetY=[306,466,218,306,548];
for(let i=0;i<ys.length;i++){
 const y=ys[i],ty=targetY[i];
 line([[923,y],[976+(i===3?18:0),(y+ty)/2],[1056,ty]],mix(cc[i],'#FFFFFF',.12),2.2,'Matching_'+ids[i]);
}
for(let i=0;i<ys.length;i++){
 blob(899,ys[i],37,ks[i]===1?43:55,cc[i],ks[i],'Match_'+ids[i]);
 text(ids[i],850,ys[i]-12,32,24,17,C.sub,false,'center');
}
text('Supplied ligand identities',1023,148,222,26,19,C.ink,false,'center');
molecule(1140,218,23,C.yellow,1,'Identity_yellow');
molecule(1140,306,23,C.green,0,'Identity_green');
molecule(1140,466,23,C.red,2,'Identity_red');
text('Same identity',1066,352,150,27,18,C.green,false,'center');
text('∅',1070,526,54,44,36,C.gray,false,'center');
text('Reject',1130,532,80,30,19,C.gray);
text('False positive',1044,579,180,26,17,C.sub,false,'center');
text('Assign identities and reject false positives',838,621,405,29,18,C.sub,false,'center');

arrow(1240,343,1300,'Build');
// 与用户手绘稿一致：下游可接多个建模器，本研究路径置于首位。
text('Density-guided\nPocketXMol',1314,218,187,67,23,C.ink,true,'center');
line([[1324,304],[1490,304]],'#D2D9DE',1,'Builder_divider');
text('PocketXMol\nSurflex-Dock\nEMERALD\nVina\n…',1312,332,191,181,20,C.sub,false,'center');
text('Site + identity\n+ receptor pocket',1298,548,222,60,18,C.sub,false,'center');
arrow(1509,343,1542,'');

density([1550,202,224,325],.79,'Output_density');
receptor([1550,202,224,325],.82,'Output_receptor');
const out=[{x:1612,y:283,c:C.green,k:0},{x:1698,y:406,c:C.green,k:0},{x:1630,y:421,c:C.yellow,k:1},{x:1686,y:246,c:C.red,k:2}];
for(const [i,s] of out.entries())molecule(s.x,s.y,11,s.c,s.k,'Pose_'+i,true);
text('All-atom reconstruction',1529,548,253,28,20,C.ink,false,'center');
text('Schematic workflow; colors track ligand identities',42,656,1300,22,15,C.sub);

slide.speakerNotes.textFrame.setText('图 a 概览。依据用户提供的 关于图a.pptx 第2页手绘流程、第3页密度参考及现代批注。真实背景为 AdaLigand 数据中的 PDB 9hjx 实验密度和受体，来源 /storage/penghongen/AdaLigand/Ori_Data/density/9hjx/ 与 raw/rcsb_mmcif/9hjx.cif。绘图副本高斯平滑 sigma=1.5 voxel，ChimeraX contour=2.6、step=3，使用当前正交视角。B1–B5、三种拓扑及最终构象均为流程示意，不是 9hjx 的模型预测或真实配体身份。两枚绿色候选匹配同一身份，灰色候选拒绝。Build 列表遵循用户手绘稿，仅表示可接的下游工具，不表示本论文实际运行了所有工具。当前论文及源码依据：论文草稿.md Overview；Pocket_Plus/src/inference；Matcher/README.md；PocketXMol/models/density/local_cov.py。ChimeraX 官方命令参考：https://www.cgl.ucsf.edu/chimerax/docs/user/commands/volume.html 和 https://www.cgl.ucsf.edu/chimerax/docs/user/commands/camera.html。');
p.comments.addThread({slide},'@@fig-overview_v2',{position:{x:0,y:0,unit:'px'}});
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidate);
const svgString=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><rect width="100%" height="100%" fill="white"/>${svg.join('\n')}</svg>`;
await fs.writeFile(path.join(build,'figure_a.svg'),svgString);
await sharp(Buffer.from(svgString)).png().toFile(path.join(build,'preview.png'));
try {const im=await p.export({slide,format:'png',scale:1.2});await fs.writeFile(path.join(build,'artifact_preview.png'),new Uint8Array(await im.arrayBuffer()));}catch(e){console.log('Artifact render',e.message);}
console.log(JSON.stringify({candidate,shapes:seq}));

const regeneratedCandidate=path.join(regenerated,`candidate_${Date.now()}.pptx`);
await fs.copyFile(candidate,regeneratedCandidate);
console.log(regeneratedCandidate);
