// 将五套原生 ChimeraX 子图装配为两行三列候选; 图片不裁改, 文字、框线与比例尺可编辑.
// 先读 cases.json 和 README; 本文件写 candidate.pptx、published/validated.pptx 与 validation.json.
// manifest.json 为按病例排序的列表: figure/pdb/role 标识图、病例和展示角色; panels[*]={panel,x,y,width,height} 按 a–f 排列, x/y 是 1600×1960 页面左上原点的图像左上坐标, width/height 是图像宽高, 均为 px; caption_zh/en 为双语图注字符串.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

// code 为本图的病例配置目录; project 为论文仓库; scenes 是原生会话及六张导图的目录.
const code=path.dirname(fileURLToPath(import.meta.url));
const project=path.resolve(code,'../../../../..');
// build 是本次可清空的候选与验证目录, 由统一重建传入; 默认也只写仓库 temp.
const build=process.env.FIGURE_BUILD_ROOT ?? path.join(project,'temp/stage1_level_cases_20261027/deck');
const scenes=process.env.FIGURE_SCENE_ROOT ?? path.join(project,'画图/画图代码/stage1/output/stage1-level-global-local/explicit_emdb_level/scenes');
// runtime 是本机 bundled Node 依赖; skill 只提供既有 PPT 包和布局校验工具, 不承担科学计算.
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);

// 在原画布像素坐标加入原生文本; size 为布局字号, 用途是可编辑标签而非图片内烘焙文字.
const addText=(slide,value,x,y,w,h,size,color,bold)=>{
 const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;shape.text.style={typeface:'Arial',fontSize:size,color,bold,autoFit:'none'};
 return shape;
};
// 从像素端点生成原生线段; 这里用于可编辑比例尺, 长度来自原生视图的 Å/像素.
const addLine=(slide,x1,y1,x2,y2,color,width)=>{
 const x=Math.min(x1,x2),y=Math.min(y1,y2),w=Math.max(.01,Math.abs(x2-x1)),h=Math.max(.01,Math.abs(y2-y1));
 return slide.shapes.add({geometry:'custom',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:color,width},customPaths:[{width:w,height:h,commands:[{moveTo:{x:x1-x,y:y1-y}},{lineTo:{x:x2-x,y:y2-y}}]}]});
};
// 在原生子图上画定位框, 返回 {left,top,width,height} 像素矩形, 供独立标号定位.
const addBox=(slide,box,x,y,w,h,color)=>{
 // box 为 (2,2) 的归一化左上/右下坐标; 框周围加同样像素边距, 不裁剪预测图.
 const pad=7,left=x+box[0][0]*w-pad,top=y+box[0][1]*h-pad,width=(box[1][0]-box[0][0])*w+2*pad,height=(box[1][1]-box[0][1])*h+2*pad;
 slide.shapes.add({geometry:'rect',position:{left,top,width,height},fill:'none',line:{fill:color,width:2}});
 return {left,top,width,height};
};

// ================================================================================================
const cases=JSON.parse(await fs.readFile(path.join(code,'cases.json'),'utf8'));
// v1 仅更换 9NVS 的展示指标；全局 Dice 读取正式逐 PDB 统计，局部 IoU 沿用同一匹配实例。
const revisedFigure=process.env.FIGURE_ID==='stage1-level-global-local-9nvs(v1)';
const cohort=revisedFigure?JSON.parse(await fs.readFile(path.join(project,'画图/画图代码/stage1/output/stage1-results-revision/explicit_emdb_level/data/plot_data.json'),'utf8')).cohorts.full:null;
const deck=Presentation.create({slideSize:{width:1600,height:1960}}),manifest=[];
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
const names=['a_reference','b_emap_global','c_ca2_global','d_receptor_fp','e_emap_local','f_ca2_local'];
const titles=['Reference','Emap2lig-Find','LigandSeek-Find (CA2)','i · Receptor-associated FP','ii · Emap2lig-Find','ii · LigandSeek-Find (CA2)'];
for(const sample of cases){
 const folder=path.join(scenes,sample.pdb),evidence=JSON.parse(await fs.readFile(path.join(folder,'evidence.json'),'utf8')),state=JSON.parse(await fs.readFile(path.join(folder,'view_state.json'),'utf8'));
 if(!state.success||!state.shared_cameras_verified)throw new Error(sample.pdb+' 原生视角未通过共同比较门控');
 // c/e 为实际匹配同一 occurrence 的 CA2/Emap blob 指标; blob_id 是原预测身份, 不是评价行号.
 const c=evidence.local_evidence.candidates.cryo.find(b=>b.blob_id===sample.local_blobs.cryo),e=evidence.local_evidence.candidates.emap.find(b=>b.blob_id===sample.local_blobs.emap);
 const component=evidence.occurrence.components[0],identity=`${component.ccd_id} (${component.auth_asym_id}:${component.auth_seq_id})`;
 const revised=revisedFigure&&sample.pdb==='9nvs',cohortRow=revised?cohort.ids.indexOf(sample.pdb):-1;
 const semantic=revised?{emap:cohort.models.Emap.values.dice[cohortRow],cryo:cohort.models.Cryo.values.dice[cohortRow]}:null;
 const slide=deck.slides.add();slide.background.fill='#FFFFFF';
 addText(slide,sample.pdb.toUpperCase()+' · '+identity,20,12,1500,42,30,'#111111',true);
 const panelPositions=[];
 for(const [i,name] of names.entries()){
  const x=20+(i%3)*525,y=70+Math.floor(i/3)*495,w=510,h=408;
  addText(slide,String.fromCharCode(97+i),x,y,45,45,40,'#111111',true);
  addText(slide,titles[i],x+43,y+4,w-43,38,27,'#333333',false);
  const iy=y+48;
  slide.images.add({blob:await fs.readFile(path.join(folder,'views',name+'.png')),contentType:'image/png',alt:sample.pdb+' '+name,fit:'contain',position:{left:x,top:iy,width:w,height:h}});
  panelPositions.push({panel:name,x,y:iy,width:w,height:h});
  // field 为原生正交相机的横向 Å 范围; 导图重采样不改变范围, bar/field*w 才是 PPT 中比例尺的像素长度.
  const field=state.views[name].pixel_size_A*state.views[name].window_size[0],bar=i<3?50:5,bw=bar/field*w,bx=x+w-bw-15,by=iy+h-20;
  addLine(slide,bx,by,bx+bw,by,'#374151',2.2);
  addText(slide,bar+' Å',bx-5,by-32,bw+35,32,24,'#374151',false);
  let metric;
  if(i===0)metric='Reference ligand regions';
  if(i===1)metric=revised?'Semantic Dice: '+semantic.emap.toFixed(3):`TP ${evidence.global_counts.emap.instance_tp} · FP ${evidence.global_counts.emap.instance_fp}`;
  if(i===2)metric=revised?'Semantic Dice: '+semantic.cryo.toFixed(3):`TP ${evidence.global_counts.cryo.instance_tp} · FP ${evidence.global_counts.cryo.instance_fp}`;
  if(i===3)metric='FP · zero overlap with ligand regions';
  if(i===4)metric=revised?'IoU: '+e.iou.toFixed(3):'Dice '+e.dice.toFixed(3);
  if(i===5)metric=revised?'IoU: '+c.iou.toFixed(3):'Dice '+c.dice.toFixed(3);
  addText(slide,metric,x+10,iy+h+3,w-10,32,25,'#333333',false);
 }
 for(const [index,key,label,color] of [[1,'fp','i','#b51f4b'],[1,'tp','ii','#266987'],[2,'tp','ii','#266987']]){
  const p=panelPositions[index],box=addBox(slide,state.views[names[index]].boxes_fraction[key],p.x,p.y,p.width,p.height,color);
  // i 位于 FP 框左侧居中, ii 位于 TP 框上方; 相邻框不会压住标号.
  const labelX=key==='fp'?box.left-28:box.left,labelY=key==='fp'?box.top+(box.height-31)/2:box.top-39;
  addText(slide,label,labelX,labelY,42,31,25,color,true);
 }
 const chinese=`受体背景下配体区域检出的全局与局部比较：${sample.pdb.toUpperCase()}。a–c，真实配体区域（绿色）、Emap2lig-Find 预测（橙色）和 LigandSeek-Find 的 CA2 预测（蓝色）。a、b 使用沉积受体，c 使用 CA2 受体；全部保留预测均显示。d，框 i 对应的受体上假阳性，与全部配体真实区域零交集。e、f，框 ii 对应的同一 ${identity} 实例，两方法均在双向覆盖阈值 0.3 的一对一评价中匹配该实例；Emap2lig 与 LigandSeek 的 Dice 分别为 ${e.dice.toFixed(3)} 和 ${c.dice.toFixed(3)}。绿色网格表示真实区域，棒状原子表示沉积配体和相应受体邻域。a–c 共用全局视角和尺度，e、f 共用局部视角和尺度；掩码为 0.5 等值面，不平滑。比例尺：a–c，50 Å；d–f，5 Å。`;
 const english=`Global and local comparison of ligand-region detection in ${sample.pdb.toUpperCase()}. a–c, Reference ligand regions (green), Emap2lig-Find predictions (orange), and LigandSeek-Find predictions with CA2 receptors (blue). Deposited receptors are shown in a and b, and the CA2 receptor in c. All retained predictions are displayed. d, The receptor-associated false positive marked by box i has zero overlap with all ground-truth ligand regions. e,f, The same ${identity} instance marked by box ii, matched by both methods under one-to-one evaluation at a bidirectional coverage threshold of 0.3. Dice is ${e.dice.toFixed(3)} for Emap2lig-Find and ${c.dice.toFixed(3)} for LigandSeek-Find. Green mesh denotes the ground-truth region; sticks show the deposited ligand and the corresponding receptor neighbourhood. Panels a–c share the global view and scale; e and f share the local view and scale. Binary masks are displayed at an isovalue of 0.5 without smoothing. Scale bars, 50 Å (a–c), 5 Å (d–f).`;
 const figure='stage1-level-global-local-'+sample.pdb+(revised?'(v1)':'');
 const captionZh=revised?chinese.replace('全部保留预测均显示。',`全部保留预测均显示；Emap2lig-Find 与 LigandSeek-Find 的全局语义 Dice 分别为 ${semantic.emap.toFixed(3)} 和 ${semantic.cryo.toFixed(3)}。`).replace(`Dice 分别为 ${e.dice.toFixed(3)} 和 ${c.dice.toFixed(3)}`,`IoU 分别为 ${e.iou.toFixed(3)} 和 ${c.iou.toFixed(3)}`):chinese;
 const captionEn=revised?english.replace('All retained predictions are displayed.',`All retained predictions are displayed. Global semantic Dice is ${semantic.emap.toFixed(3)} for Emap2lig-Find and ${semantic.cryo.toFixed(3)} for LigandSeek-Find.`).replace(`Dice is ${e.dice.toFixed(3)} for Emap2lig-Find and ${c.dice.toFixed(3)} for LigandSeek-Find.`,`IoU is ${e.iou.toFixed(3)} for Emap2lig-Find and ${c.iou.toFixed(3)} for LigandSeek-Find.`):english;
 slide.speakerNotes.textFrame.setText(captionZh+'\nENGLISH:\n'+captionEn);
 deck.comments.addThread({slide},'@@'+figure,{position:{x:0,y:0,unit:'px'}});
 manifest.push({figure,pdb:sample.pdb,role:sample.role,panels:panelPositions,caption_zh:captionZh,caption_en:captionEn});
}
await fs.mkdir(build,{recursive:true});
await fs.mkdir(path.join(build,'published'),{recursive:true});
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
await fs.writeFile(path.join(build,'manifest.json'),JSON.stringify(manifest,null,2));
await finalizePresentation({workspaceDir:build,candidatePath:candidate,finalPath:path.join(build,'published/validated.pptx'),pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu',`${1600*9525},${1960*9525}`],explicitTotalSlideCount:cases.length,verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
console.log('五套六面板PPT候选已装配。');
