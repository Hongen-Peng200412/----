// 检查最终本地PPT包和字体，保留原生对象；仅将验证通过的副本写入 published。
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { finalizePresentation } from 'file:///C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/container_tools/artifact_tool_utils.mjs';

let root=path.dirname(fileURLToPath(import.meta.url));
while (!(await fs.stat(path.join(root,'论文草稿.md')).catch(()=>false)))root=path.dirname(root);
const build=process.env.FIGURE_BUILD_ROOT;
process.env.RUNTIME_NODE_MODULES='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const output=path.join(build,'published',new Date().toISOString().replaceAll(/[^0-9]/g,''));await fs.mkdir(output,{recursive:true});
const checks=path.join(build,'checks',path.basename(output));await fs.mkdir(checks,{recursive:true});
const sources=JSON.parse(await fs.readFile(path.join(root,'画图/画图代码/e2e/output/fig12-revision/source/source_manifest.json'),'utf8'));
const results=JSON.parse(await fs.readFile(path.join(build,'finalization_index.json'),'utf8').catch(()=>'{}'));
for(const [kind,name,size,count] of [['overview','总览图','11906250,4572000',4],['method','Method总图','6480175,4468813',4]]){
  if(process.argv[2] && process.argv[2]!==kind)continue;
  const reference=path.join(root,'画图/画图代码/e2e/output/fig12-revision/source',kind+'-author.pptx');
  const digest=sources.find(r=>r.frozen.endsWith(kind+'-author.pptx')).sha256;
  const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(build,'candidate-'+kind+'.pptx'),finalPath:path.join(output,name+'.pptx'),
    pythonExecutable:'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu',size,'--validate-heading-fit'],
    explicitTotalSlideCount:count,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
    fontPolicy:{basis:'reference',families:kind==='method'?['Arial','Times New Roman','Calibri']:['Arial'],referencePath:reference,referenceSha256:digest},
    verifyArtifactToolImport:true,receiptPath:path.join(checks,kind+'.validation.json')});
  results[kind]={path:result.finalPath,sha256:result.finalSha256,receipt:result.receiptPath};
  await fs.writeFile(path.join(build,'finalization_index.json'),JSON.stringify(results,null,2));
  console.log(kind,'package, layout, reference fonts and first-party import passed.');
}
await fs.writeFile(path.join(build,'finalization_index.json'),JSON.stringify(results,null,2));
process.exit(0);
