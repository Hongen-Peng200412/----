/**
 * 将七例冻结事实、原生 ChimeraX PNG 和 RDKit SVG 装配为可编辑的行动流程图集.
 * 入口为本模块末尾的逐案例循环. 科学图像保持独立图片, 标题、步骤、框线和图注为 PPT 原生对象.
 * temp/e2e_flow_20261003/deck_manifest.json 是数组, 每个元素含 name(图名)、pdb、caption(图注)、panels(图片几何)和 identities(精确身份与索引).
 * 临时候选自行包含独立图名和备注, 验收后的新PPT写入e2e/output/e2e-flow/regenerated/views/. 旧发布脚本已归档, 当前来源见所属图表追溯.md. 本模块不推理、不改变坐标、不按真值选姿态.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
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


const code = path.dirname(fileURLToPath(import.meta.url));
const project = repoRoot;
const output = path.join(project, '画图/画图代码/e2e/output/e2e-flow/views');
const temp = path.join(project, 'temp/e2e_flow_20261003');
const runtime = 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill = 'C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
process.env.RUNTIME_NODE_MODULES = path.join(runtime, 'node/node_modules');
const {Presentation, PresentationFile} = await import(pathToFileURL(`${runtime}/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs`).href);
const {finalizePresentation} = await import(pathToFileURL(`${skill}/container_tools/artifact_tool_utils.mjs`).href);

// 画布坐标为 CSS pixel, 原点在左上角; 与分子世界坐标 XYZ Å 无关.
const width = 1800, height = 1940;
const deck = Presentation.create({slideSize: {width, height}});
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});
const order = ['9bjj', '30ga', '9llg', '9qru', '9rd8', '9wup', '9xzl'];
const color = {text: '#203544', muted: '#60717a', pale: '#e6edeb', step: '#366755', blue: '#3169b3', teal: '#26a6a1', blob: '#e9983c', background: '#9f87a9', scope: '#9a907c', receptor: '#81a58b', density: '#516773'};
const manifest = [];

/** 创建一个原生文本框; x/y/w/h 是画布 pixel, value 是显示文本, 返回对象仍可在 PowerPoint 编辑. */
function text(slide, value, x, y, w, h, size = 32, bold = false, tint = color.text) {
  const shape = slide.shapes.add({geometry: 'textbox', position: {left: x, top: y, width: w, height: h}, fill: 'none', line: {fill: 'none', width: 0}});
  shape.text = value;
  shape.text.style = {typeface: 'Arial', fontSize: size, bold, color: tint, autoFit: 'none', insets: {left: 0, right: 0, top: 0, bottom: 0}};
  return shape;
}

/** 画一条原生直线, 输入是画布端点; 不投影原子或体素, 仅表达流程或分隔关系. */
function line(slide, x1, y1, x2, y2, tint = color.pale, thickness = 2) {
  const left = Math.min(x1, x2), top = Math.min(y1, y2);
  const w = Math.max(.1, Math.abs(x2 - x1)), h = Math.max(.1, Math.abs(y2 - y1));
  slide.shapes.add({geometry: 'custom', position: {left, top, width: w, height: h}, fill: 'none', line: {fill: tint, width: thickness}, customPaths: [{width: w, height: h, commands: [{moveTo: {x: x1 - left, y: y1 - top}}, {lineTo: {x: x2 - left, y: y2 - top}}]}]});
}

/** 添加步骤编号与横向标题线; 编号只描述行动顺序, 不代表模型采样步或 blob 排名. */
function step(slide, number, name, detail, y) {
  const badge = slide.shapes.add({geometry: 'ellipse', position: {left: 38, top: y, width: 50, height: 50}, fill: color.step, line: {fill: 'none', width: 0}});
  badge.text = String(number);
  badge.text.style = {typeface: 'Arial', fontSize: 31, bold: true, color: '#FFFFFF', alignment: 'center', verticalAlignment: 'middle', insets: {left: 0, right: 0, top: 0, bottom: 0}};
  text(slide, name, 130, y + 2, 210, 48, 38, true, color.step);
  text(slide, detail, 370, y + 5, 1335, 42, 31, false, color.muted);
  line(slide, 130, y + 61, 1710, y + 61);
}

/**
 * 插入独立原生三维 PNG, 只进行等比例缩放.
 * panels: 数组, 每个元素记录 key(视图文件名)、letter(面板字母)、rectangle_px([x,y,w,h])和 source_path(实际 PNG); 与图像插入顺序一致.
 * name 指向 <pdb>/renders/<name>.png. 与 ChimeraX camera.json 一起可追溯最终视图, 不从标签坐标推断科学坐标.
 */
async function picture(slide, panels, pdb, name, letter, x, y, w, h) {
  const source = path.join(output, pdb, 'renders', `${name}.png`);
  slide.images.add({blob: await fs.readFile(source), contentType: 'image/png', alt: `${pdb.toUpperCase()} ${name}; native ChimeraX; frozen world coordinates`, fit: 'contain', position: {left: x, top: y, width: w, height: h}});
  panels.push({key: name, letter, rectangle_px: [x, y, w, h], source_path: source});
}

/** 添加图像标题和面板字母, 文字置于图像之外, 避免覆盖分子或把参考图误当模型输入. */
function panelTitle(slide, letter, title, x, y, w) {
  text(slide, letter, x, y, 37, 39, 33, true);
  text(slide, title, x + 44, y + 1, w - 44, 39, 31);
}

/**
 * 依 identity_smiles 原顺序插入全部二维结构, 每个 SVG 是独立矢量组件.
 * identities.identities 的 eligible 是 Stage3 范围掩码, matched 是与冻结 predicted_smiles_small_molecule 的精确字符串相等; 两者不能由画出的化学结构猜测.
 * SVG viewBox 只去除空白边缘并保留 20 pixel 安全边距, 不改路径、元素、电荷或手性. 标签为 PPT 原生文字.
 */
async function identityRow(slide, pdb, identities) {
  const count = identities.identity_count;
  const gap = 28, cardWidth = (1580 - gap * (count - 1)) / count;
  for (const item of identities.identities) {
    const x = 130 + item.identity_index * (cardWidth + gap);
    const tint = item.matched ? color.blue : item.eligible ? color.text : color.scope;
    const frame = slide.shapes.add({geometry: 'rect', position: {left: x, top: 1143, width: cardWidth, height: 280}, fill: '#FFFFFF', line: {fill: item.matched ? color.blue : color.pale, width: item.matched ? 3 : 1}});
    frame.name = `Identity ${item.identity_index + 1}, ${item.matched ? 'matched' : item.eligible ? 'eligible' : 'outside Stage3 scope'}`;
    text(slide, `${item.identity_index + 1}  ${item.display_label}`, x + 18, 1154, cardWidth - 36, 40, 32, item.matched, tint);
    let svg = await fs.readFile(path.join(output,pdb,'identities',path.basename(item.paths.transparent_svg)), 'utf8');
    const [left, top, right, bottom] = item.content_bbox_px;
    const boxWidth = right - left + 40, boxHeight = bottom - top + 40;
    svg = svg.replace(/viewBox='[^']*'/, `viewBox='${left - 20} ${top - 20} ${boxWidth} ${boxHeight}'`);
    svg = svg.replace(/viewBox="[^"]*"/, `viewBox="${left - 20} ${top - 20} ${boxWidth} ${boxHeight}"`);
    svg = svg.replace(/width='1200px' height='720px'/, `width='${boxWidth}px' height='${boxHeight}px'`);
    // 显式按裁后 SVG 的宽高比安排原生图片, 避免 Office 将同一 ATP 在两列/三列布局中横向拉伸.
    const scale = Math.min((cardWidth - 30) / boxWidth, 175 / boxHeight);
    const imageWidth = boxWidth * scale, imageHeight = boxHeight * scale;
    slide.images.add({blob: new TextEncoder().encode(svg), contentType: 'image/svg+xml', alt: `${pdb} identity_smiles[${item.identity_index}], exact SMILES ${item.smiles}`, fit: 'contain', position: {left: x + (cardWidth - imageWidth) / 2, top: 1195 + (175 - imageHeight) / 2, width: imageWidth, height: imageHeight}});
    text(slide, item.matched ? 'Matched identity' : item.eligible ? 'Eligible small molecule' : 'Outside Stage3 scope', x + 18, 1380, cardWidth - 36, 36, 28, item.matched, tint);
  }
}

/** 返回七例的真实轨迹概述; 背景只计费而未运行 Match/Build, 范围外前景由既定门禁免费跳过. */
function pathText(pdb, data) {
  if (data.case.group === 'background') return 'Background at rank 1, successful reconstruction at rank 2';
  if (data.case.group === 'scope_skip') return `Earlier foreground outside Stage3 scope, successful reconstruction at rank ${data.handoff.raw_rank}`;
  return 'The first-ranked site completes identity matching and pose reconstruction';
}

/** 生成与各页面板对应的中文图注; 数值来自已冻结的 local-c1, reference 仅用于显示和最终评价. */
function caption(pdb, number, data, ids) {
  const component = data.target_occurrence.components[0];
  const eligible = ids.identities.filter(item => item.eligible).length;
  const rmsd = data.method.pose_min_rmsd_A['1'].toFixed(2);
  const target = `${component.ccd_id}(${component.auth_asym_id}:${component.auth_seq_id})`;
  const title = number <= 15 ? `图 ${number}｜` : '备选图｜';
  const attempt = data.case.group === 'background' ? `首位背景消耗一次尝试，未进入 Match 或 Build；第二位 ${target} 完成重建。` : data.case.group === 'scope_skip' ? `前 ${data.handoff.raw_rank - 1} 位前景经 Stage3 范围门禁免费跳过，第 ${data.handoff.raw_rank} 位 ${target} 为首个计费候选。` : `首位 ${target} 依次完成区域检出、身份匹配和构象重建。`;
  const selected = data.handoff.candidate_selected === false ? ' 该候选原入选标记为 false，仍按完整顺序评价。' : '';
  return `${title}${pdb.toUpperCase()} 的完整重建流程。${attempt} a–c，完整实验密度、CryoAtom2 受体及 GT 受体参考。d，全部 ${data.flow_geometry.blob_count_original} 个预测 blob 的全局分布；e、f，GT 邻域与 Find 局部对照，每对朝向和尺度一致。g，原顺序的全部 ${ids.identity_count} 个 SMILES 身份，${eligible} 个合格小分子参与匹配，蓝框标出精确匹配项。h–j，同一 local_cov-C 自评分首位姿态的受体、密度和沉积构象叠加视图，重原子 RMSD ${rmsd} Å。受体绿色，密度灰色，目标 blob 橙色，背景灰紫色，预测构象蓝色，沉积构象青绿色。所示目标位点生成 50 个姿态，每姿态 100 步采样；GT 仅供参考及最终评价。${selected}`;
}

// panels 和 identities 都按本页实际显示顺序保留, 不取重排后的 top-k 子集.
for (const [index, pdb] of order.entries()) {
  const data = JSON.parse(await fs.readFile(path.join(output, pdb, 'data.json'), 'utf8'));
  data.flow_geometry = JSON.parse(await fs.readFile(path.join(output, pdb, 'geometry.json'), 'utf8'));
  const ids = JSON.parse(await fs.readFile(path.join(output, pdb, 'identities/identity_manifest.json'), 'utf8'));
  const component = data.target_occurrence.components[0];
  const slide = deck.slides.add(), panels = [];
  slide.background.fill = '#FFFFFF';
  text(slide, `${pdb.toUpperCase()}  ${component.ccd_id} (${component.auth_asym_id}:${component.auth_seq_id})`, 130, 22, 1540, 58, 46, true);
  text(slide, pathText(pdb, data), 130, 85, 1580, 44, 32, false, color.muted);
  // 纵向连接线止于编号圆外, 不穿过文字或证据图像.
  for (const [from, to] of [[185, 538], [588, 1073], [1123, 1447]]) {
    line(slide, 63, from + 10, 63, to - 12, '#bdcdc6', 3);
    line(slide, 56, to - 22, 63, to - 12, '#bdcdc6', 3);
    line(slide, 70, to - 22, 63, to - 12, '#bdcdc6', 3);
  }
  step(slide, 0, 'Input', 'Experimental map and CA2 receptor', 138);
  const topPanels = [['a', 'Full experimental map', 'global_density'], ['b', 'Full CA2 receptor', 'global_ca2'], ['c', 'GT receptor (reference)', 'global_gt']];
  for (const [i, [letter, title, render]] of topPanels.entries()) {
    const x = 130 + i * 550;
    panelTitle(slide, letter, title, x, 218, 480);
    await picture(slide, panels, pdb, render, letter, x, 262, 480, 255);
  }
  step(slide, 1, 'Find', `Ranked density regions, site ${data.handoff.raw_rank} uses charged attempt ${data.handoff.attempt_index}`, 538);
  panelTitle(slide, 'd', 'Global candidates', 130, 620, 620);
  await picture(slide, panels, pdb, 'global_find', 'd', 130, 670, 620, 310);
  text(slide, `All ${data.flow_geometry.blob_count_original} predicted blobs`, 130, 994, 620, 39, 30, false, color.muted);
  panelTitle(slide, 'e', 'GT neighborhood', 840, 620, 420);
  panelTitle(slide, 'f', 'Find prediction', 1290, 620, 420);
  if (data.case.group === 'background') {
    text(slide, 'Rank 1: background, one attempt', 840, 665, 860, 38, 30, true, color.background);
    await picture(slide, panels, pdb, 'background_gt', 'e', 840, 705, 420, 135);
    await picture(slide, panels, pdb, 'background_find', 'f', 1290, 705, 420, 135);
    text(slide, 'Rank 2: target ligand, next attempt', 840, 844, 860, 38, 30, true, color.blob);
    await picture(slide, panels, pdb, 'local_gt', 'e', 840, 886, 420, 135);
    await picture(slide, panels, pdb, 'local_find', 'f', 1290, 886, 420, 135);
  } else {
    text(slide, `Rank ${data.handoff.raw_rank}: target ligand`, 840, 667, 865, 40, 30, true, color.blob);
    await picture(slide, panels, pdb, 'local_gt', 'e', 840, 711, 420, 274);
    await picture(slide, panels, pdb, 'local_find', 'f', 1290, 711, 420, 274);
    if (data.case.group === 'scope_skip') text(slide, data.handoff.raw_rank === 2 ? 'Rank 1: free scope skip' : `Ranks 1–${data.handoff.raw_rank - 1}: free scope skips`, 840, 995, 870, 38, 30, false, color.scope);
  }
  step(slide, 2, 'Match', 'RDKit structures of every supplied SMILES identity', 1073);
  text(slide, 'g', 99, 1146, 30, 40, 33, true);
  await identityRow(slide, pdb, ids);
  step(slide, 3, 'Build', 'local_cov-C self-ranking Top-1, one pose in three views', 1447);
  const dockPanels = [['h', 'Receptor surface', 'dock_receptor'], ['i', 'Experimental density', 'dock_density'], ['j', 'Deposited pose overlay', 'dock_gt_overlay']];
  for (const [i, [letter, title, render]] of dockPanels.entries()) {
    const x = 130 + i * 550;
    panelTitle(slide, letter, title, x, 1528, 480);
    await picture(slide, panels, pdb, render, letter, x, 1573, 480, 248);
  }
  text(slide, `Heavy-atom RMSD ${data.method.pose_min_rmsd_A['1'].toFixed(2)} Å     Clash ${data.top1.num_clashes}     50 poses, 100 steps`, 130, 1838, 1580, 47, 34, true, color.blue);
  const legend = [['Receptor', color.receptor], ['Density', color.density], ['Target blob', color.blob], ['Predicted pose', color.blue], ['Deposited pose', color.teal]];
  for (const [i, [label, tint]] of legend.entries()) {
    const x = 130 + i * 320;
    line(slide, x, 1910, x + 32, 1910, tint, 5);
    text(slide, label, x + 43, 1894, 270, 34, 27, false, color.muted);
  }
  const notes = caption(pdb, 12 + index, data, ids);
  slide.speakerNotes.textFrame.setText(notes);
 deck.comments.addThread({slide},'@@'+(`e2e-flow-${pdb}`),{position:{x:0,y:0,unit:'px'}});

  manifest.push({name: `e2e-flow-${pdb}`, pdb, caption: notes, panels, identities: ids.identities.map(item => ({identity_index: item.identity_index, smiles: item.smiles, eligible: item.eligible, matched: item.matched, chemical_graph_passed: item.chemical_graph.passed})), final_physical_width_mm: 183});
}
await fs.mkdir(temp, {recursive: true});
await fs.writeFile(path.join(temp, 'deck_manifest.json'), JSON.stringify(manifest, null, 2));
const candidate = path.join(temp, 'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const regenerated=process.env.FIGURE_BUILD_ROOT ? path.join(process.env.FIGURE_BUILD_ROOT,'published') : path.join(project,'画图/画图代码/e2e/output/e2e-flow/regenerated/views');
await fs.mkdir(regenerated,{recursive:true});
const stamp = Date.now().toString(), validated = path.join(regenerated, `validated-${stamp}.pptx`);
await fs.mkdir(path.join(temp, 'validation'), {recursive: true});
await finalizePresentation({workspaceDir: project, candidatePath: candidate, finalPath: validated, pythonExecutable: `${runtime}/python/python.exe`, integrityValidatorPath: path.join(skill, 'container_tools/inspect_presentation_package_integrity.py'), layoutValidatorPath: path.join(skill, 'container_tools/inspect_presentation_layout_geometry.py'), layoutArgs: ['--expected-slide-size-emu', `${width * 9525},${height * 9525}`], explicitTotalSlideCount: 7, fontPolicy: {basis: 'design', families: ['Arial']}, verifyArtifactToolImport: true, receiptPath: path.join(project, `temp/ppt_validation/e2e-flow-${stamp}.json`)});
await fs.copyFile(validated, path.join(temp, 'validated.pptx'));
console.log('Seven editable flow pages exported and structurally validated.');
