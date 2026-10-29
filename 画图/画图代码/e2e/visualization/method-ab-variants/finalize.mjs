// 使用当前 Presentations 运行时验收原生 PPT 包, 保留作者对象并检查一方导入兼容性.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const build=process.env.FIGURE_BUILD_ROOT;
const selected=process.argv[2]==='selected';
let root=path.dirname(fileURLToPath(import.meta.url));
while(!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false)))root=path.dirname(root);
const runtime='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const audit=JSON.parse(await fs.readFile(path.join(build,'audit.json'),'utf8'));
if(!audit.passed)throw new Error('对象差异和原生渲染审计尚未通过');
const source=selected?JSON.parse((await fs.readFile(path.join(root,'画图/画图代码/e2e/output/method-ab-variants/source/selected-layout.json'),'utf8')).replace(/^\uFEFF/,'')):{pptx:'画图/画图代码/e2e/output/method-ab-variants/source/author-20261028-deb03f10.pptx',sha256:'deb03f100ba843a6588b1f52849a921b77aee0319409dfca40c53ff0283c7c9f'};
await fs.mkdir(path.join(build,'published'),{recursive:true});
await fs.mkdir(path.join(build,'checks'),{recursive:true});
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(build,'candidate.pptx'),finalPath:path.join(build,'published/Method总图.pptx'),
  pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','6480175,4468813','--validate-heading-fit'],
  explicitTotalSlideCount:selected?5:11,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  fontPolicy:{basis:'reference',families:['Arial','Times New Roman'],referencePath:path.join(root,source.pptx),referenceSha256:source.sha256},
  verifyArtifactToolImport:true,receiptPath:path.join(build,'checks/final.validation.json')});
await fs.writeFile(path.join(build,'delivery.json'),JSON.stringify({path:result.finalPath,sha256:result.finalSha256,receipt:result.receiptPath},null,2));
console.log('Native object audit, package, dimensions, reference fonts and Artifact Tool import passed.');
