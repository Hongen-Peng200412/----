// 将本轮布局与原生图片装配为可编辑 PPT. 每张图单独嵌入, 标题、计数和标签保持文字.
// 用 Codex 固定 Node 运行: node build_deck.mjs <含 presentation_data.json 的本轮构建目录>.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {pathToFileURL} from 'node:url';

const runtime = path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies');
const modules = process.env.RUNTIME_NODE_MODULES ?? path.join(runtime, 'node/node_modules');
process.env.RUNTIME_NODE_MODULES = modules;
const {Presentation, PresentationFile} = await import(pathToFileURL(path.join(modules, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const skill = path.join(os.homedir(), '.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations');
const {finalizePresentation} = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const build = path.resolve(process.argv[2]);
const data = JSON.parse(await fs.readFile(path.join(build, 'presentation_data.json'), 'utf8'));
// 180 mm 宽与 Python PDF 完全一致, 将布局的逻辑像素映射为 PPT 的96-dpi单位.
const scale = (180 / 25.4 * 96) / data.width;
const deck = Presentation.create({slideSize:{width:data.width*scale, height:data.height*scale}});
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
for (const page of data.pages) {
  const slide = deck.slides.add();
  slide.background.fill = '#ffffff';
  for (const panel of page.panels) {
    const bytes = await fs.readFile(panel.image);
    slide.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),
      contentType:'image/png',alt:`${panel.pdb.toUpperCase()} ${panel.view}`,
      fit:'contain',position:{left:panel.x*scale,top:panel.y*scale,width:panel.w*scale,height:panel.h*scale}});
  }
  for (const text of page.texts) {
    const shape = slide.shapes.add({geometry:'textbox',name:`${page.id}_${text.y}_${text.x}`,
      position:{left:text.x*scale,top:text.y*scale,width:text.w*scale,height:text.h*scale},
      fill:'none',line:{fill:'none',width:0}});
    shape.text = text.text;
    shape.text.style = {typeface:'Arial',fontSize:text.size*scale,bold:text.bold,color:'#222222',
      alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};
  }
  slide.speakerNotes.text = page.caption_zh+'\nENGLISH:\n'+page.caption_en;
  deck.comments.addThread({slide},'@@'+page.id,{position:{x:0,y:0,unit:'px'}});
}
const previews = path.join(build,'ppt_preview');
await fs.mkdir(previews,{recursive:true});
for (const [i,slide] of deck.slides.items.entries()) {
  const png = await deck.export({slide,format:'png',scale:2});
  await fs.writeFile(path.join(previews,`slide_${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const staging = path.join(build,'.codex-finalizer');
await fs.mkdir(staging,{recursive:true});
const candidate = path.join(staging,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
await fs.mkdir(path.join(build,'published'),{recursive:true});
const final = path.join(build,'published',`candidate_${Date.now()}.pptx`);
await finalizePresentation({workspaceDir:build,candidatePath:candidate,finalPath:final,
  explicitTotalSlideCount:data.pages.length,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  pythonExecutable:path.join(runtime,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu',`6480000,${Math.round(6480000*data.height/data.width)}`,'--validate-heading-fit'],
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(staging,path.basename(final)+'.validation.json')});
await fs.copyFile(final,path.join(build,'candidate.pptx'));
console.log(final);
