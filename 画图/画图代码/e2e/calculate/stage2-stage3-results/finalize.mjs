// 对原生统计形状和作者病例对象作文件结构、字体与可导入性检查。
import path from 'node:path';
import fs from 'node:fs/promises';
import {finalizePresentation} from 'file:///C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1029.11837/skills/presentations/container_tools/artifact_tool_utils.mjs';
const build=process.env.FIGURE_BUILD_ROOT;
process.env.RUNTIME_NODE_MODULES ??= 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
if(!build)throw new Error('必须提供FIGURE_BUILD_ROOT');
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1029.11837/skills/presentations';
const pages=JSON.parse(await fs.readFile(path.join(build,'manifest.json'),'utf8'));
const output=path.join(build,'validated','stage2-stage3.pptx');
await fs.mkdir(path.dirname(output),{recursive:true});
const result=await finalizePresentation({
  workspaceDir:build,candidatePath:path.join(build,'candidate.pptx'),finalPath:output,
  pythonExecutable:'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:3,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  layoutArgs:['--expected-slide-size-emu',`${Math.round(pages[0].width*12700)},${Math.round(pages[0].height*12700)}`],
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(build,'presentation-validation.json')
});
console.log(JSON.stringify(result));
