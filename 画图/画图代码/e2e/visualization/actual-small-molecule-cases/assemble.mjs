// 将同次 ChimeraX 原生图片和 Python 测定布局写为单页可编辑 PPT.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {pathToFileURL} from 'node:url';

const runtime=path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies');
const modules=process.env.RUNTIME_NODE_MODULES??path.join(runtime,'node/node_modules');
process.env.RUNTIME_NODE_MODULES??=modules;
const skill=path.join(os.homedir(),'.codex/plugins/cache/openai-primary-runtime/presentations/26.1017.22136/skills/presentations');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(modules,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const build=path.resolve(process.argv[2]);
const page=JSON.parse(await fs.readFile(path.join(build,'presentation_data.json'),'utf8'));
const mm=96/25.4;
const deck=Presentation.create({slideSize:{width:page.width_mm*mm,height:page.height_mm*mm}});
const slide=deck.slides.add();
slide.background.fill='#ffffff';
for(const panel of page.panels){
 const bytes=await fs.readFile(panel.image);
 slide.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png',alt:`${panel.label}: ${panel.heading}`,fit:'contain',position:{left:panel.x_mm*mm,top:panel.y_mm*mm,width:panel.w_mm*mm,height:panel.h_mm*mm}});
}
for(const text of page.texts){
 const shape=slide.shapes.add({geometry:'textbox',name:`${page.id}_${text.y_mm}_${text.x_mm}`,position:{left:text.x_mm*mm,top:text.y_mm*mm,width:text.w_mm*mm,height:text.h_mm*mm},fill:'none',line:{fill:'none',width:0}});
 shape.text=text.text;
 shape.text.style={typeface:'Arial',fontSize:text.size_pt*96/72,bold:text.bold,color:'#222222',alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};
}
slide.speakerNotes.text=page.caption_zh+'\nENGLISH:\n'+page.caption_en;
const staging=path.join(build,'.codex-finalizer');
await fs.mkdir(staging,{recursive:true});
const candidate=path.join(staging,'candidate.pptx');
await(await PresentationFile.exportPptx(deck)).save(candidate);
await fs.mkdir(path.join(build,'published'),{recursive:true});
const final=path.join(build,'published',`actual-cases-${Date.now()}.pptx`);
await finalizePresentation({workspaceDir:build,candidatePath:candidate,finalPath:final,explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],pythonExecutable:path.join(runtime,'python/python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','6480000,6120000','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(staging,'validation.json')});
await fs.copyFile(final,path.join(build,'candidate.pptx'));
console.log(final);
