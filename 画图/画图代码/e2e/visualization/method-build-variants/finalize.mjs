/** 用一方工具核查9页包、原画布、参考字体及导入兼容性. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const build=process.env.FIGURE_BUILD_ROOT;
let root=path.dirname(fileURLToPath(import.meta.url));
while(!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false)))root=path.dirname(root);
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const audit=JSON.parse(await fs.readFile(path.join(build,'audit.json'),'utf8'));
if(!audit.passed)throw Error('原件保全或原生渲染检查失败');
await fs.mkdir(path.join(build,'published'),{recursive:true});await fs.mkdir(path.join(build,'checks'),{recursive:true});
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(build,'candidate.pptx'),finalPath:path.join(build,'published/Method总图.pptx'),pythonExecutable:runtime+'/python/python.exe',
  integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','6480175,4468813','--validate-heading-fit'],
  explicitTotalSlideCount:9,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'reference',families:['Arial','Times New Roman'],referencePath:path.join(root,'画图/画图代码/e2e/output/method-build-variants/source/author-20261028-ce373d2e.pptx'),referenceSha256:'ce373d2ea868981a82ec77fc7c883684aa49648092e5cf74586d90fe0f0a1f49'},verifyArtifactToolImport:true,receiptPath:path.join(build,'checks/final.validation.json')});
await fs.writeFile(path.join(build,'delivery.json'),JSON.stringify({path:result.finalPath,sha256:result.finalSha256,receipt:result.receiptPath},null,2));
console.log('Build variants passed package, canvas, reference-font and Artifact Tool import checks.');
