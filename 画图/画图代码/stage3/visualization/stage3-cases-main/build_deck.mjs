/** 将已经核查的三维投影转换为 PowerPoint 原生线条、路径、圆形和文字. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
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


const root = repoRoot;
const runtime = 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES = `${runtime}/node/node_modules`;
// skill 指向本机已安装的 PPT 包校验工具, 不属于科学输入或临时产物.
const skill = 'C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const require = createRequire(`${runtime}/node/node_modules/@oai/artifact-tool/package.json`);
const { Presentation, PresentationFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const { finalizePresentation } = await import(pathToFileURL(`${skill}/container_tools/artifact_tool_utils.mjs`).href);
// output 指向当前条件的冻结案例及其图注; 未指定时仍读取原无 level 目录.
const output = process.env.FIGURE_SOURCE_ROOT ? path.resolve(process.env.FIGURE_SOURCE_ROOT) : path.join(root, '画图/画图代码/stage3/output/stage3-cases-main');
const temporary = process.env.FIGURE_BUILD_ROOT ? path.resolve(process.env.FIGURE_BUILD_ROOT) : path.join(root, 'temp/stage3_cases/deck');
await fs.mkdir(temporary, { recursive: true });
// regenerated 保存本条件的新图稿和候选图集, 与 output 中冻结科学输入分开.
const regenerated=process.env.FIGURE_RENDER_ROOT ? path.resolve(process.env.FIGURE_RENDER_ROOT) : path.join(output,'regenerated');
await fs.mkdir(regenerated,{recursive:true});
const requestedName=process.argv[2]??'stage3-cases';
if(path.basename(requestedName)!==requestedName) throw new Error('候选文件名不得含目录');
const candidateName=requestedName.replace(/\.pptx$/,'')+'_'+Date.now()+'.pptx';
const pages = JSON.parse(await fs.readFile(path.join(regenerated, 'deck_layout.json'), 'utf8'));
const captions = JSON.parse(await fs.readFile(path.join(output, 'captions.json'), 'utf8'));
const presentation = Presentation.create({ slideSize: { width: 980, height: 1256 } });
presentation.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});

/** 将半透明线条的颜色与白底合成, 保持 Python 预览的显示效果. */
function blended(color, alpha = 1) {
  const rgb = [1, 3, 5].map(i => parseInt(color.slice(i, i + 2), 16));
  return '#' + rgb.map(c => Math.round(c * alpha + 255 * (1 - alpha)).toString(16).padStart(2, '0')).join('');
}

/** 裁切显示线段到固定局部视野, 不改变三维构象或任何指标. */
function clipSegment(segment, width, height) {
  const [[x0, y0], [x1, y1]] = segment;
  const dx = x1 - x0, dy = y1 - y0;
  let low = 0, high = 1;
  const p = [-dx, dx, -dy, dy], q = [x0, width - x0, y0, height - y0];
  for (let k = 0; k < 4; k++) {
    if (p[k] === 0) { if (q[k] < 0) return null; }
    else {
      const t = q[k] / p[k];
      if (p[k] < 0) low = Math.max(low, t); else high = Math.min(high, t);
    }
  }
  if (low > high) return null;
  return [[x0 + low * dx, y0 + low * dy], [x0 + high * dx, y0 + high * dy]];
}

/** 将多个线段合成可编辑矢量路径. 网格是单一图层, 配体键逐条保留. */
function addPath(slide, name, segments, position, color, width, dashed = false) {
  if (!segments.length) return;
  slide.shapes.add({
    name, geometry: 'custom', position, fill: 'none',
    line: { fill: color, width, style: dashed ? 'dashed' : 'solid' },
    customPaths: [{ width: position.width, height: position.height,
      commands: segments.flatMap(([a, b]) => [{ moveTo: { x: a[0], y: a[1] } }, { lineTo: { x: b[0], y: b[1] } }]) }],
  });
}

for (const page of pages) {
  const slide = presentation.slides.add();
  slide.background.fill = '#FFFFFF';
  for (const [index, item] of page.items.entries()) {
    const name = `${page.figure_name}_${index}`;
    if (item.kind === 'text') {
      const shape = slide.shapes.add({ name, geometry: 'textbox',
        position: { left: item.x, top: item.y, width: item.width, height: item.height },
        fill: 'none', line: { fill: 'none', width: 0 } });
      shape.text = item.value;
      shape.text.style = { typeface: 'Arial', fontSize: item.size, bold: item.bold, color: item.color,
        alignment: 'left', verticalAlignment: 'middle', wrap: 'none', autoFit: 'none',
        insets: { top: 0, right: 0, bottom: 0, left: 0 } };
    } else if (item.kind === 'line') {
      addPath(slide, name, [[[item.x1, item.y1], [item.x2, item.y2]]],
        { left: 0, top: 0, width: 980, height: 1256 }, item.color, item.width);
    } else {
      const position = { left: item.x, top: item.y, width: item.width, height: item.height };
      for (const layer of item.layers) {
        const layerName = `${item.key.join('_')}_${item.method}_${layer.name}`;
        if (layer.kind === 'lines') {
          const segments = layer.lines.map(s => clipSegment(s, item.width, item.height)).filter(Boolean);
          const color = blended(layer.color, layer.alpha);
          // 网格与受体各一个可编辑路径; 配体键和碰撞线逐条编辑.
          if (['ExperimentalDensity', 'Receptor'].includes(layer.name)) {
            addPath(slide, layerName, segments, position, color, layer.width, layer.dashed);
          } else {
            segments.forEach((segment, i) => addPath(slide, `${layerName}_${i}`, [segment], position, color, layer.width, layer.dashed));
          }
        } else {
          layer.atoms.forEach((atom, i) => {
            if (atom.x - atom.radius < 0 || atom.x + atom.radius > item.width || atom.y - atom.radius < 0 || atom.y + atom.radius > item.height) return;
            slide.shapes.add({ name: `${layerName}_${i}`, geometry: 'ellipse',
              position: { left: item.x + atom.x - atom.radius, top: item.y + atom.y - atom.radius, width: atom.radius * 2, height: atom.radius * 2 },
              fill: atom.color, line: { fill: 'none', width: 0 } });
          });
        }
      }
    }
  }
  slide.speakerNotes.textFrame.setText(captions[page.figure_name]);
 presentation.comments.addThread({slide},'@@'+(page.figure_name),{position:{x:0,y:0,unit:'px'}});

}

const candidatePath = path.join(temporary, 'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const result = await finalizePresentation({
  workspaceDir: root, candidatePath, finalPath: path.join(regenerated,candidateName),
  pythonExecutable: `${runtime}/python/python.exe`,
  integrityValidatorPath: `${skill}/container_tools/inspect_presentation_package_integrity.py`,
  layoutValidatorPath: `${skill}/container_tools/inspect_presentation_layout_geometry.py`,
  layoutArgs: ['--expected-slide-size-emu', `${980 * 9525},${1256 * 9525}`, '--validate-heading-fit'],
  explicitTotalSlideCount: pages.length, requiredNativeTableOwnerSlides: [], requiredNativeChartOwnerSlides: [],
  fontPolicy: { basis: 'design', families: ['Arial'] }, verifyArtifactToolImport: true,
  receiptPath: path.join(temporary, candidateName.replace('.pptx','.validation.json')),
});
console.log(JSON.stringify({ slides: pages.length, final: result.finalPath ?? 'validated.pptx' }));
