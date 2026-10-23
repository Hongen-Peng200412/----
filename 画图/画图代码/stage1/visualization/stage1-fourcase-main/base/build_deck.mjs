// 基于真实三维渲染装配图版。定位框和连接线保持 PowerPoint 原生可编辑。
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

const code=path.dirname(fileURLToPath(import.meta.url)),project=repoRoot;
const out=path.join(project,'画图/画图代码/stage1/output/stage1-fourcase-main/base'),temp=path.join(project,'temp/stage1_chimera_v3');
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const captions=JSON.parse(await fs.readFile(code+'/captions.json','utf8'));
const deck=Presentation.create({slideSize:{width:1600,height:1960}}),manifest=[];
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
const names=['receptor_real','receptor_ca2','gt','find_real','find_ca2','emap'];
const pages=[];for(const palette of ['baseline','contrast','density']){pages.push({palette,pdbs:['9pqm','9wq3','9uwi','9x0x'],group:1});pages.push({palette,pdbs:['9bjj','9wup','9rmi'],group:2});}
pages.push({palette:'contrast',pdbs:['9pqm','9uwi','9wup','9rmi'],main:true});
for(const page of pages){
 const slide=deck.slides.add();slide.background.fill='#FFFFFF';
 const line=(x1,y1,x2,y2)=>{const x=Math.min(x1,x2),y=Math.min(y1,y2),w=Math.max(.01,Math.abs(x1-x2)),h=Math.max(.01,Math.abs(y1-y2));slide.shapes.add({geometry:'custom',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'#266987',width:2.1},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-x,y:y1-y}},{lineTo:{x:x2-x,y:y2-y}}]}]});};
 const rect=(left,top,width,height)=>slide.shapes.add({geometry:'rect',position:{left,top,width,height},fill:'none',line:{fill:'#266987',width:2.1}});
 for(const [i,pdb] of page.pdbs.entries()){
  const y=page.pdbs.length===4?24+i*480:160+i*570,ox=10,ow=610,oh=ow*1125/1600,oy=y+(450-oh)/2,lx=670,lw=300,lh=225;
  const d=path.join(out,pdb),scene=JSON.parse(await fs.readFile(path.join(d,'scene_checks.json'),'utf8'))[page.palette+'_overview'];
  slide.images.add({blob:await fs.readFile(path.join(d,page.palette,'overview.png')),contentType:'image/png',alt:pdb+' complex overview',fit:'contain',position:{left:ox,top:oy,width:ow,height:oh}});
  for(const [j,n] of names.entries())slide.images.add({blob:await fs.readFile(path.join(d,page.palette,n+'.png')),contentType:'image/png',alt:pdb+' '+n+' '+page.palette,fit:'contain',position:{left:lx+(j%3)*lw,top:y+Math.floor(j/3)*lh,width:lw,height:lh}});
  const [lo,hi]=scene.ligand_bounds_camera,fw=scene.field_width,fh=fw*oh/ow,pad=2.5;
  const bx=ox+(.5+(lo[0]-pad)/fw)*ow,by=oy+(.5-(hi[1]+pad)/fh)*oh,bw=(hi[0]-lo[0]+2*pad)/fw*ow,bh=(hi[1]-lo[1]+2*pad)/fh*oh;
  line(bx+bw,by,lx,y);line(bx+bw,by+bh,lx,y+2*lh);rect(bx,by,bw,bh);rect(lx,y,3*lw,2*lh);
  line(lx+lw,y,lx+lw,y+2*lh);line(lx+2*lw,y,lx+2*lw,y+2*lh);line(lx,y+lh,lx+3*lw,y+lh);
 }
 const caption=page.main?captions.main:captions['group'+page.group]+captions.palette[page.palette];slide.speakerNotes.textFrame.setText(caption);
 deck.comments.addThread({slide},'@@'+(page.main?'stage1-fourcase-main':`stage1-seven-group${page.group}-${page.palette}`),{position:{x:0,y:0,unit:'px'}});
 manifest.push({...page,name:page.main?'stage1-fourcase-main':`stage1-seven-group${page.group}-${page.palette}`,caption});
}
await fs.mkdir(temp,{recursive:true});
const regenerated=process.env.FIGURE_BUILD_ROOT ? path.join(process.env.FIGURE_BUILD_ROOT,'published') : path.join(project,'画图/画图代码/stage1/output/stage1-fourcase-main/regenerated', 'base');
await fs.mkdir(regenerated,{recursive:true});
const candidate=path.join(temp,'fourcase_candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
await fs.writeFile(temp+'/deck_manifest.json',JSON.stringify(manifest,null,2));
const run=Date.now(),validated=path.join(regenerated,`fourcase_${run}.pptx`);await fs.mkdir(path.dirname(validated),{recursive:true});
await finalizePresentation({workspaceDir:(process.env.FIGURE_BUILD_ROOT??project),candidatePath:candidate,finalPath:validated,pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu',`${1600*9525},${1960*9525}`],explicitTotalSlideCount:7,verifyArtifactToolImport:true,receiptPath:path.join(temp,`validation_${run}.json`)});
await fs.copyFile(validated,temp+'/fourcase_validated.pptx');console.log('Seven-slide draft validated.');
