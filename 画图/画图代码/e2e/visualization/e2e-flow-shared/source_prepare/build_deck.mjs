// 装配原生ChimeraX成像与可编辑文字、流程线；不计算或重画原子、体素和相机。
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
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

const code=path.dirname(fileURLToPath(import.meta.url));
const project=repoRoot;
const output=path.join(project,'画图/画图代码/e2e/output/e2e-flow/source');
const temp=path.join(project,'temp/e2e_cases');
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {Presentation,PresentationFile}=await import(pathToFileURL(`${runtime}/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs`).href);
const {finalizePresentation}=await import(pathToFileURL(`${skill}/container_tools/artifact_tool_utils.mjs`).href);
const deck=Presentation.create({slideSize:{width:1600,height:1260}});
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
const cases=JSON.parse(await fs.readFile(path.join(code,'cases.json'),'utf8'));
const data={};
for(const c of cases)data[c.pdb]=JSON.parse(await fs.readFile(path.join(output,c.pdb,'data.json'),'utf8'));
const manifest=[];
const color={text:'#203544',muted:'#667783',blue:'#3169b3',teal:'#26a6a1',blob:'#e9983c',background:'#9f87a9',scope:'#958a74'};
function text(slide,value,x,y,w,h,size=26,bold=false,tint=color.text){
 const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;shape.text.style={typeface:'Arial',fontSize:size,bold,color:tint,autoFit:'none'};
 return shape;
}
function line(slide,x1,y1,x2,y2,tint=color.muted,width=2){
 const left=Math.min(x1,x2),top=Math.min(y1,y2),w=Math.max(.1,Math.abs(x2-x1)),h=Math.max(.1,Math.abs(y2-y1));
 slide.shapes.add({geometry:'custom',position:{left,top,width:w,height:h},fill:'none',line:{fill:tint,width},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-left,y:y1-top}},{lineTo:{x:x2-left,y:y2-top}}]}]});
}
function arrow(slide,x1,y,x2,tint=color.muted){line(slide,x1,y,x2,y,tint);line(slide,x2-12,y-7,x2,y,tint);line(slide,x2-12,y+7,x2,y,tint);}
async function picture(slide,pdb,name,x,y,w,h){
 slide.images.add({blob:await fs.readFile(path.join(output,pdb,'renders',name+'.png')),contentType:'image/png',alt:`${pdb} ${name}; native ChimeraX`,fit:'contain',position:{left:x,top:y,width:w,height:h}});
}
// 编号的终点由原生Find图片目视定位；只标注排序，不重新投影或移动体素。
function siteLabels(slide,pdb,x,y,w,h){
 const positions={
  '30ga':[[1,.592,.136,.39,.10,color.background],[2,.466,.804,.25,.86,color.blob]],
  '9qru':[[1,.55,.529,.73,.47,color.background],[2,.369,.598,.21,.70,color.blob]],
  '9wup':[[3,.414,.54,.32,.67,color.blob]],
  '9xzl':[[1,.441,.362,.27,.29,color.scope],[2,.59,.56,.76,.65,color.blob]],
 };
 for(const [rank,px,py,lx,ly,tint] of positions[pdb]||[]){
  const cx=x+lx*w,cy=y+ly*h;
  const tx=x+px*w,ty=y+py*h,dist=Math.hypot(tx-cx,ty-cy);
  line(slide,cx+22*(tx-cx)/dist,cy+22*(ty-cy)/dist,tx,ty,tint,2);
  const badge=slide.shapes.add({geometry:'ellipse',position:{left:cx-20,top:cy-20,width:40,height:40},fill:'#FFFFFF',line:{fill:'none',width:0}});
  badge.text=String(rank);
  badge.text.style={typeface:'Arial',fontSize:22,bold:true,color:tint,alignment:'center',verticalAlignment:'middle',insets:{left:0,right:0,top:0,bottom:0}};
 }
}
function addLegend(slide,y,receptorLabel='CA2 receptor'){
 const labels=[[receptorLabel,'#81a58b'],['Experimental density','#a0a9ad'],['Predicted blob',color.blob],['Top-1 pose',color.blue],['Deposited ligand',color.teal]];
 labels.forEach(([label,tint],i)=>{line(slide,55+i*303,y+17,83+i*303,y+17,tint,5);text(slide,label,92+i*303,y,225,35,22,false,color.muted);});
}
function compound(pdb){const c=data[pdb].target_occurrence.components[0];return `${c.ccd_id} (${c.auth_asym_id}:${c.auth_seq_id})`;}
function matchLabel(pdb){const d=data[pdb];return `${d.prediction.small_molecule_answer_mask.filter(Boolean).length} eligible small-molecule SMILES\nExact SMILES match: ${d.target_occurrence.components[0].ccd_id}`;}
function pathLabel(pdb){const c=data[pdb].case.group;return c==='direct'?'First-ranked site succeeds':c==='background'?'Background first, ligand second':'Out-of-scope foreground precedes ligand';}
function rankLabel(pdb){const d=data[pdb];return `Site rank ${d.handoff.raw_rank} · charged attempt ${d.handoff.attempt_index}`;}

// 第一至三页为紧凑的双案例图；第三页的范围门禁只作为备选，不插入现有正文。
for(const [index,pair] of [['main',['9bjj','30ga']],['multi-identity',['9llg','9qru']],['scope',['9wup','9xzl']]]){
 const slide=deck.slides.add();slide.background.fill='#FFFFFF';
 ['Find','Match','Build'].forEach((name,i)=>text(slide,name,[62,613,1110][i],22,420,46,34,true));
 arrow(slide,490,44,570);arrow(slide,1000,44,1080);
 for(let row=0;row<pair.length;row++){
  const pdb=pair[row],d=data[pdb],y=95+row*545;
  text(slide,`${row?'d':'a'}  ${pdb.toUpperCase()} · ${compound(pdb)}`,55,y,850,42,29,true);
  text(slide,pathLabel(pdb),55,y+44,520,35,24,false,color.muted);
  await picture(slide,pdb,'find',45,y+80,485,364);
  siteLabels(slide,pdb,45,y+80,485,364);
  text(slide,rankLabel(pdb),55,y+448,525,35,24);
  if(d.case.group==='background')text(slide,'Rank 1: background · one attempt',55,y+485,525,35,22,false,color.background);
  if(d.case.group==='scope_skip')text(slide,'Earlier sites: Stage3 scope gate · free skip',55,y+485,555,35,22,false,color.scope);
  text(slide,row?'e':'b',610,y+80,40,36,26,true);
  await picture(slide,pdb,'identity',605,y+115,420,275);
  text(slide,matchLabel(pdb),610,y+410,450,78,24);
  await picture(slide,pdb,'pose',1090,y+85,465,349);
  text(slide,row?'f':'c',1110,y+80,40,36,26,true);
  text(slide,`Self-ranking Top-1 · RMSD ${d.method.pose_min_rmsd_A['1'].toFixed(2)} Å`,1110,y+445,460,40,24,true);
  if(d.handoff.candidate_selected===false)text(slide,'Appended candidate (unselected)',1110,y+488,450,32,21,false,color.muted);
 }
 addLegend(slide,1200);
 const caption=index==='main'?'图 12｜CryoAtom2 受体条件下的 Find–Match–Build 重建实例。a–c，9BJJ 的首位候选对应 ATP（B:901），依次完成区域检出、精确 SMILES 身份匹配和构象重建。d–f，30GA 的首位候选为背景，按评测规则消耗一次尝试，未进入 Match 或 Build；第二位候选对应 ATP（N:401），随后完成重建。Find 列显示候选区域，Match 列标出匹配身份，Build 列叠加预测与沉积构象。受体为绿色，实验密度为灰色网格，小分子候选 blob 为橙色，背景 blob 为灰紫色，预测配体为蓝色，沉积配体为青绿色。Build 展示每个位点 50 个姿态中按 self-ranking 排序的首位姿态，两个实例的重原子 RMSD 分别为 0.80 Å 和 1.04 Å。':index==='multi-identity'?'图 13｜多个小分子身份候选下的端到端重建。a–c，9LLG 的首位 blob 对应 A1EKL（R:602），Matcher 在三个合格小分子精确 SMILES 中匹配到正确身份，local_cov-C 首位姿态的 RMSD 为 0.88 Å。d–f，9QRU 首位背景候选消耗一次尝试，第二位 blob 对应 A1JAX（B:2801），在两个合格小分子身份中匹配成功，首位姿态的 RMSD 为 0.63 Å。9QRU 的第二位 blob 是完整候选顺序中的追加候选，原入选标记为 false，仍按既定评价规则进入对接。列顺序、颜色与 Top-1 定义同图 12。':'备选图｜Stage3 适用范围门禁与后续小分子重建。9WUP 的前两个前景实例不在冻结 Stage3 合格范围，按既定门禁免费跳过，第三位 FMN（B:1103）成为首个计费位点；9XZL 的首位离子候选也免费跳过，第二位 AGS（F:1001）进入重建。对应 local_cov-C 自评分首位 RMSD 为 0.52 Å 和 0.91 Å。这是带 Stage3 范围门禁的冻结评价轨迹，不表示模型在盲测中自行排除了这些前景。颜色与姿态定义同主图。';
 slide.speakerNotes.textFrame.setText(caption);
 deck.comments.addThread({slide},`@@e2e-cases-${index}`,{position:{x:0,y:0,unit:'px'}});
 manifest.push({name:`e2e-cases-${index}`,caption,cases:pair});
}

// 七张详页让Find定位、局部区域核对、身份与最终原子姿态均有充足空间。
for(const c of cases){
 const pdb=c.pdb,d=data[pdb],slide=deck.slides.add();slide.background.fill='#FFFFFF';
 text(slide,`${pdb.toUpperCase()} · ${compound(pdb)}`,55,24,950,45,34,true);
 text(slide,pathLabel(pdb),55,75,1050,35,25,false,color.muted);
 text(slide,'Find',55,128,650,40,29,true);
 await picture(slide,pdb,'find',40,178,700,525);
 siteLabels(slide,pdb,40,178,700,525);
 text(slide,rankLabel(pdb),55,704,660,35,25);
 let labels=d.blobs.map(b=>`#${b.raw_rank}  p=${b.probability_mean.toFixed(3)}  ${b.scope==='background'?'background':b.scope==='non_stage3_foreground'?'outside Stage3 scope':'target ligand'}`);
 labels.forEach((s,i)=>text(slide,s,55,745+i*35,670,34,23,false,d.blobs[i].scope==='background'?color.background:d.blobs[i].scope==='non_stage3_foreground'?color.scope:color.text));
 text(slide,'Match',815,128,650,40,29,true);
 await picture(slide,pdb,'identity',775,172,400,300);
 text(slide,d.target_occurrence.components[0].ccd_id,1210,195,330,45,31,true,color.blue);
 text(slide,`${d.prediction.small_molecule_answer_mask.filter(Boolean).length} eligible small-molecule\nSMILES identities`,1210,255,350,85,25);
 text(slide,'Exact SMILES match',1210,370,345,40,25,true);
 text(slide,'Build · self-ranking Top-1',815,510,720,45,29,true);
 await picture(slide,pdb,'pose',805,560,740,555);
 text(slide,`RMSD ${d.method.pose_min_rmsd_A['1'].toFixed(2)} Å · Clash ${d.top1.num_clashes}`,815,1122,700,42,28,true);
 text(slide,'GT region (reference)',55,890,340,38,23);
 text(slide,'Predicted blob + CA2',425,890,350,38,23);
 await picture(slide,pdb,'local_gt',40,932,340,255);
 await picture(slide,pdb,'local_find',415,932,340,255);
 addLegend(slide,1200,'Receptor');
 const caption=`${pdb.toUpperCase()} 端到端案例详图。${compound(pdb)}；${rankLabel(pdb)}。Matcher 的精确 SMILES 与冻结目标身份相同，${d.prediction.small_molecule_answer_mask.filter(Boolean).length} 个合格小分子身份参与本轮匹配。Build 为第一次 local_cov-C 的实际 self-ranking Top-1（sample_index=${d.method.top1_sample_index}），重原子 RMSD ${d.method.pose_min_rmsd_A['1'].toFixed(2)} Å。底部两图共用朝向与尺度，以沉积区域对照冻结预测 blob。三维视图均由 ChimeraX 原生命令生成，沉积结构仅用于参考显示和最终评价。`;
 slide.speakerNotes.textFrame.setText(caption);
 deck.comments.addThread({slide},`@@e2e-case-${pdb}`,{position:{x:0,y:0,unit:'px'}});
 manifest.push({name:`e2e-case-${pdb}`,caption,cases:[pdb]});
}
await fs.mkdir(temp,{recursive:true});
await fs.writeFile(path.join(temp,'deck_manifest.json'),JSON.stringify(manifest,null,2));
const candidate=path.join(temp,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const regenerated=process.env.FIGURE_BUILD_ROOT ? path.join(process.env.FIGURE_BUILD_ROOT,'published') : path.join(project,'画图/画图代码/e2e/output/e2e-flow/regenerated/source');
await fs.mkdir(regenerated,{recursive:true});
const run=Date.now().toString(),validated=path.join(regenerated,`validated-${run}.pptx`);
await fs.mkdir(path.join(project,'temp/ppt_validation'),{recursive:true});
await finalizePresentation({workspaceDir:(process.env.FIGURE_BUILD_ROOT??project),candidatePath:candidate,finalPath:validated,pythonExecutable:`${runtime}/python/python.exe`,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu',`${1600*9525},${1260*9525}`],explicitTotalSlideCount:10,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(project,`temp/ppt_validation/e2e-${run}.json`)});
await fs.copyFile(validated,path.join(temp,'validated.pptx'));
console.log('10 editable-layout slides exported and validated.');
