// 只装配 SVG 几何与文字, 不读取原始实验文件, 不计算科学指标.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
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

const root=path.dirname(fileURLToPath(import.meta.url));
const workspace=repoRoot;
const build = process.env.FIGURE_BUILD_ROOT ? path.resolve(process.env.FIGURE_BUILD_ROOT) : path.join(workspace,'temp/stage1_main_sixpanel_20260929');
const version=process.env.STAGE1_FIGURE_VERSION??'v5';
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
// 原生 PowerPoint 对象由 Artifact Tool 生成, 不把整张图嵌为图片.
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
await fs.mkdir(build, {recursive:true});
const pages=JSON.parse(await fs.readFile(path.join(build,`scenes_${version}.json`),'utf8'));
const deck=Presentation.create({slideSize:{width:1000,height:924}});
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
// 当前幻灯片宽 1000 CSS px、9525000 EMU, 以下位置均从正式图集反推。
const emuFrame=([x,y,w,h])=>({left:x/9525,top:y/9525,width:w/9525,height:h/9525});
// 第 19 页手动调整后的原生对象位置; 图例始终是组合图末尾的六个形状。
const compositeLegendFrames=[
 [2001725,697023,124468,87127],[2166317,664656,2926080,155584],
 [4346259,705489,124468,87127],[4529139,664656,3017520,155584],
 [6757522,701256,124468,87127],[6948868,664656,1371600,155584],
];
const compositeLegendLabels=['Ligandseek-Find(deposited receptor)','Ligandseek-Find(CryoAtom2 receptor)','Emap2lig-Find'];
const compositeAxisTextFrames=new Map([
 [1863,['Emap2lig-Find',[2512678,6045506,555233,163994]]],
 [1870,['Ligandseek-Find (CryoAtom2)',[732737,4615257,1189432,163994]]],
 [4258,['Emap2lig-Find',[6155474,6045506,555233,163994]]],
 [4265,['Ligandseek-Find (CryoAtom2)',[4375533,4615257,1189432,163994]]],
]);
let seq=0;
function color(value,alpha){return value==='none'?'none':alpha<1?value+'/'+Math.round(alpha*100):value;}
for(const page of pages){
 const slide=deck.slides.add();slide.background.fill='#FFFFFF';
 // 单图按其自身比例居中; 组合图按高度约束. 源图本身控制紧凑留白.
 const s=Math.min(950/page.width,890/page.height),ox=(1000-page.width*s)/2,oy=(924-page.height*s)/2;
 for(const [index,shape] of page.shapes.entries()){
  let pos={left:ox+shape.x*s,top:oy+shape.y*s,width:Math.max(.02,shape.w*s),height:Math.max(.02,shape.h*s)};
  if(page.stem==='Stage1_sixpanel'){
   const axisText=compositeAxisTextFrames.get(index);
   if(axisText){
    if(shape.text!==axisText[0])throw new Error(`Unexpected composite axis label: ${shape.text}`);
    pos=emuFrame(axisText[1]);
   }
   if(shape.kind==='text'&&shape.text==='Small molecules'&&shape.y<20)
    pos=emuFrame([6032950,261696,1719166,210249]);
   const legendIndex=index-(page.shapes.length-compositeLegendFrames.length);
   if(legendIndex>=0){
    if(legendIndex%2===1&&shape.text!==compositeLegendLabels[(legendIndex-1)/2])
     throw new Error(`Unexpected composite legend label: ${shape.text}`);
    pos=emuFrame(compositeLegendFrames[legendIndex]);
   }
  }
  if(shape.kind==='text'){
   const t=slide.shapes.add({geometry:'textbox',name:'text_'+seq++,position:{...pos,rotation:shape.rotation},fill:'none',line:{fill:'none',width:0}});
   t.text=shape.text;t.text.style={typeface:'Arial',fontSize:shape.font*s,bold:shape.bold,color:shape.color,
    alignment:'left',verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};
   continue;
  }
  const config={name:page.stem+'_'+seq++,position:pos,fill:color(shape.fill,shape.fill_alpha),
    line:{fill:color(shape.stroke,shape.stroke_alpha),width:shape.stroke==='none'?0:shape.stroke_width*s,
          style:shape.dash==='none'?'solid':shape.dash.startsWith('1.')?'dotted':'dashed'}};
  if(shape.kind==='ellipse')slide.shapes.add({geometry:'ellipse',...config});
  else{
   const commands=[];
   for(const part of shape.parts){
    part.forEach((q,i)=>commands.push({[i?'lineTo':'moveTo']:{x:q[0]*s,y:q[1]*s}}));
    if(Math.hypot(part[0][0]-part.at(-1)[0],part[0][1]-part.at(-1)[1])<1e-5)commands.push({close:{}});
   }
   slide.shapes.add({geometry:'custom',...config,customPaths:[{width:pos.width,height:pos.height,commands}]});
  }
 }
 slide.speakerNotes.textFrame.setText(page.notes);
 deck.comments.addThread({slide},'@@'+(page.name),{position:{x:0,y:0,unit:'px'}});

 console.log(page.stem+' assembled');
}
await (await PresentationFile.exportPptx(deck)).save(path.join(build,`new_panels_${version}.pptx`));

const regenerated=process.env.FIGURE_BUILD_ROOT ? path.join(process.env.FIGURE_BUILD_ROOT,'published') : path.join(repoRoot,'画图/画图代码/stage1/output/stage1-main-sixpanel/regenerated');
await fs.mkdir(regenerated,{recursive:true});
const regeneratedCandidate=path.join(regenerated,`new_panels_${version}_${Date.now()}.pptx`);
await fs.copyFile(path.join(build,`new_panels_${version}.pptx`),regeneratedCandidate);
console.log(regeneratedCandidate);
