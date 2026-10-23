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
const out=process.env.FIGURE_BUILD_ROOT?path.join(build,'published'):path.join(workspace,'画图/画图代码/stage1/output/stage1-main-sixpanel/regenerated');
const candidate=process.env.STAGE1_FIGURE_CANDIDATE??path.join(build,`new_panels_${version}.pptx`);
const finalPath=process.env.STAGE1_FIGURE_FINAL??path.join(out,`stage1_panels_${version}_${Date.now()}.pptx`);
if (!path.resolve(finalPath).startsWith(path.resolve(out)+path.sep)) throw new Error('验收候选只允许写入regenerated目录');
await fs.mkdir(out,{recursive:true});
const receipt=process.env.STAGE1_FIGURE_RECEIPT??path.join(build,`final_${version}.validation.json`);
process.env.RUNTIME_NODE_MODULES='C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const skill='C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
console.log(await finalizePresentation({workspaceDir:(process.env.FIGURE_BUILD_ROOT??workspace),candidatePath:candidate,
 finalPath,
 pythonExecutable:'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','9525000,8801100'],
 explicitTotalSlideCount:7,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 // Calibri 仅存在于保留的旧 case 页; 新增科学图统一 Arial.
 fontPolicy:{basis:'design',families:['Arial','Calibri']},verifyArtifactToolImport:true,
 receiptPath:receipt}));
