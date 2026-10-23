/**
 * 将七例冻结预测与原生 ChimeraX/RDKit 资产装配成可编辑的端到端流程图.
 * 主入口为末尾的案例循环; 图片只用 PPT 的等比缩放与非破坏裁切, 不改变分子、密度或候选.
 * temp/e2e_flow_v2_20261003/deck_manifest.json 是逐页数组: name(图名)、caption(图注)、panels(源图及显示变换)、boxes(候选关联框)、identities(精确身份)按本页显示顺序保存.
 * 临时候选自行包含独立图名和备注, 验收后的新PPT写入e2e/output/e2e-flow/regenerated/display/. 旧发布脚本已归档, 当前来源见所属图表追溯.md.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {parseArgs} from 'node:util';
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
const original = path.join(project, '画图/画图代码/e2e/output/e2e-flow/views');
const output = process.env.FIGURE_ASSET_ROOT??path.join(project, '画图/画图代码/e2e/output/e2e-flow/display');
// 显式选择只影响装配页集合, 原七例次序仍决定既有图注编号.
const {values:cli}=parseArgs({options:{pdb:{type:'string'},'build-root':{type:'string'}}});
const allOrder=['9llg','9bjj','30ga','9qru','9rd8','9wup','9xzl'];
const selectedPdb=cli.pdb?.toLowerCase();
if(selectedPdb&&!allOrder.includes(selectedPdb)) throw new Error('pdb必须是七例冻结案例之一');
const order=selectedPdb?[selectedPdb]:allOrder;
const temp=process.env.FIGURE_BUILD_ROOT?path.resolve(process.env.FIGURE_BUILD_ROOT):cli['build-root']?path.resolve(project,cli['build-root']):path.join(project,selectedPdb?`temp/e2e-flow-${selectedPdb}`:'temp/e2e_flow_v2_20261003');
const buildRelative=path.relative(path.join(project,'temp'),temp);
if(buildRelative.startsWith('..')||path.isAbsolute(buildRelative)) throw new Error('构建目录必须位于论文仓库temp内');
const runtime = 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill = 'C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
process.env.RUNTIME_NODE_MODULES = path.join(runtime, 'node/node_modules');
const {Presentation, PresentationFile} = await import(pathToFileURL(`${runtime}/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs`).href);
const {finalizePresentation} = await import(pathToFileURL(`${skill}/container_tools/artifact_tool_utils.mjs`).href);
const width = 1800, height = 2100;
const deck = Presentation.create({slideSize: {width, height}});
deck.comments.setSelf({displayName:'Figure Editor',initials:'FE',userId:'figure-editor',providerId:'None'});

const color = {text: '#203544', muted: '#60717a', pale: '#e6edeb', step: '#366755', blue: '#3169b3', teal: '#26a6a1', blob: '#e9983c', background: '#9f87a9', scope: '#9a907c', receptor: '#81a58b', density: '#516773'};
// 以 PDB 为键的索引: 几何范围来自原始投影, 像素 bbox 仅用于显示裁切, 不参与科学计算.
const framing = Object.fromEntries(JSON.parse(await fs.readFile(path.join(original, 'global_framing_manifest.json'), 'utf8')).map(item => [item.pdb, item]));
const native = Object.fromEntries(JSON.parse(await fs.readFile(path.join(original, 'native_render_manifest.json'), 'utf8')).map(item => [item.pdb, item]));
const projected = Object.fromEntries(JSON.parse(await fs.readFile(path.join(output, 'projection_boxes_manifest.json'), 'utf8')).map(item => [item.pdb, item]));
const manifest = [];

/** 添加原生可编辑文字; x/y/w/h 为左上角原点的画布 pixel, 与分子 XYZ Å 坐标无关. */
function text(slide, value, x, y, w, h, size = 32, bold = false, tint = color.text) {
  const shape = slide.shapes.add({geometry: 'textbox', position: {left: x, top: y, width: w, height: h}, fill: 'none', line: {fill: 'none', width: 0}});
  shape.text = value;
  shape.text.style = {typeface: 'Arial', fontSize: size, bold, color: tint, autoFit: 'none', insets: {left: 0, right: 0, top: 0, bottom: 0}};
  return shape;
}

/** 添加原生直线, 仅表达步骤、图例或参考分栏; 端点按画布 pixel 给出. */
function line(slide, x1, y1, x2, y2, tint = color.pale, thickness = 2) {
  const left = Math.min(x1, x2), top = Math.min(y1, y2);
  const w = Math.max(.1, Math.abs(x2 - x1)), h = Math.max(.1, Math.abs(y2 - y1));
  slide.shapes.add({geometry: 'custom', position: {left, top, width: w, height: h}, fill: 'none', line: {fill: tint, width: thickness}, customPaths: [{width: w, height: h, commands: [{moveTo: {x: x1 - left, y: y1 - top}}, {lineTo: {x: x2 - left, y: y2 - top}}]}]});
}

/** 添加行动编号及标题; 0–3 是流程行动, 不是模型去噪步或 Find 排名. */
function step(slide, number, name, detail, y) {
  const badge = slide.shapes.add({geometry: 'ellipse', position: {left: 38, top: y, width: 50, height: 50}, fill: color.step, line: {fill: 'none', width: 0}});
  badge.text = String(number);
  badge.text.style = {typeface: 'Arial', fontSize: 31, bold: true, color: '#FFFFFF', alignment: 'center', verticalAlignment: 'middle', insets: {left: 0, right: 0, top: 0, bottom: 0}};
  text(slide, name, 130, y + 2, 210, 48, 38, true, color.step);
  text(slide, detail, 370, y + 5, 1335, 42, 31, false, color.muted);
  line(slide, 130, y + 61, 1710, y + 61);
}

/** 返回多个 PNG 范围的共同裁切框; 输入是 [left,top,right,bottom], 输出保留 margin 像素并限于 1440×1080 原图. */
function cropUnion(boxes, margin = 30) {
  return [Math.max(0, Math.min(...boxes.map(b => b[0])) - margin), Math.max(0, Math.min(...boxes.map(b => b[1])) - margin), Math.min(1440, Math.max(...boxes.map(b => b[2])) + margin), Math.min(1080, Math.max(...boxes.map(b => b[3])) + margin)];
}

/** 从原生导图记录取非白区域 bbox; 只用于移除显示边缘, 不删改源 PNG 内任何像素. */
function renderBox(pdb, name) {
  return native[pdb].renders.find(item => item.name === `${name}.png`).nonwhite_bbox_xyxy;
}

/**
 * 在指定展示框内放置非破坏裁切的原生 PNG, 图片和裁切框保持同一比例.
 * crop 是源 PNG 的 [left,top,right,bottom] pixel, frame 是画布 [x,y,w,h] pixel; 可比较图组共用 crop 和 frame 尺寸.
 * 返回并写入 panels: key/letter/source_path 标识原图; rectangle_px 为实际图像占位; crop_bbox_px 为源图保留范围; scale 是源像素到画布像素比例.
 * 图像字节未修改, PPT 中仍可取消裁切; 科学坐标不从裁切后的屏幕位置重新计算.
 */
async function picture(slide, panels, pdb, name, letter, frame, crop) {
  const source = path.join(['global_find', 'global_density_same_scale'].includes(name) ? output : (process.env.FIGURE_NATIVE_ROOT??original), pdb, 'renders', `${name}.png`);
  const [x, y, w, h] = frame, [left, top, right, bottom] = crop;
  const scale = Math.min(w / (right - left), h / (bottom - top));
  const imageWidth = (right - left) * scale, imageHeight = (bottom - top) * scale;
  const rectangle = [x + (w - imageWidth) / 2, y + (h - imageHeight) / 2, imageWidth, imageHeight];
  slide.images.add({blob: await fs.readFile(source), contentType: 'image/png', alt: `${pdb.toUpperCase()} ${name}; native ChimeraX; frozen coordinates`, fit: 'cover', position: {left: rectangle[0], top: rectangle[1], width: rectangle[2], height: rectangle[3]}, crop: {left: left / 1440, top: top / 1080, right: (1440 - right) / 1440, bottom: (1080 - bottom) / 1080}});
  const entry = {key: name, letter, rectangle_px: rectangle, frame_px: frame, crop_bbox_px: crop, scale, source_path: source};
  panels.push(entry);
  return entry;
}

/** 添加图外标题和面板字母; 标题仍为 PowerPoint 原生文本. */
function panelTitle(slide, letter, title, x, y, w) {
  text(slide, letter, x, y, 37, 39, 33, true);
  text(slide, title, x + 44, y + 1, w - 44, 39, 31);
}

/**
 * 将冻结体素的 PNG 投影框映射到已裁切的全局图, 用原生彩框关联相应局部对照.
 * box.suggested_box_xyxy_px 为完整源 PNG 范围, 已含 24 pixel 提示边距; role 区分 target/background, 不是新增候选分类.
 * 返回数组逐框保存源框、画布框、blob 编号及原排名; 框不表示算法分割的新边界.
 */
function candidateFrames(slide, pdb, panel) {
  return projected[pdb].boxes.map(box => {
    const [l, t, r, b] = box.suggested_box_xyxy_px;
    const [x, y] = panel.rectangle_px, [cropLeft, cropTop] = panel.crop_bbox_px;
    const rectangle = [x + (l - cropLeft) * panel.scale, y + (t - cropTop) * panel.scale, (r - l) * panel.scale, (b - t) * panel.scale];
    slide.shapes.add({geometry: 'rect', name: `${box.role} blob ${box.source_blob_index}`, position: {left: rectangle[0], top: rectangle[1], width: rectangle[2], height: rectangle[3]}, fill: 'none', line: {fill: box.color, width: 3}});
    return {role: box.role, raw_rank: box.raw_rank, source_blob_index: box.source_blob_index, source_bbox_px: [l, t, r, b], rectangle_px: rectangle, purpose: 'display association only'};
  });
}

/**
 * 原顺序展示全部精确 SMILES 的 RDKit SVG; 蓝框和原生文字标识已冻结的匹配项.
 * identity_index 指向 identity_smiles 的原始位置; eligible/matched 保留在追溯记录, 非匹配项不重复显示适用范围说明.
 * content_bbox_px 是 SVG 内容范围, 仅扩大 20 pixel 后修改 viewBox; 元素路径、化学图和身份均不改变.
 * SVG 根尺寸按实际文件通用替换, 单原子身份限定 80 pixel 高, 防止 Mg/Zn 被空白裁切放大成巨字.
 */
async function identityRow(slide, ids) {
  const count = ids.identity_count, gap = 28, cardWidth = (1580 - gap * (count - 1)) / count;
  for (const item of ids.identities) {
    const x = 130 + item.identity_index * (cardWidth + gap);
    slide.shapes.add({geometry: 'rect', name: `Identity ${item.identity_index + 1}`, position: {left: x, top: 1230, width: cardWidth, height: 300}, fill: '#FFFFFF', line: {fill: item.matched ? color.blue : color.pale, width: item.matched ? 3 : 1}});
    text(slide, `${item.identity_index + 1}  ${item.display_label}`, x + 18, 1242, cardWidth - 36, 40, 32, item.matched, item.matched ? color.blue : color.text);
    let svg = await fs.readFile(path.join(output,ids.pdb,'identities',path.basename(item.paths.transparent_svg)), 'utf8');
    const [left, top, right, bottom] = item.content_bbox_px;
    const boxWidth = right - left + 40, boxHeight = bottom - top + 40;
    svg = svg.replace(/viewBox=(['"])[^'"]*\1/, `viewBox='${left - 20} ${top - 20} ${boxWidth} ${boxHeight}'`);
    svg = svg.replace(/width=(['"])[\d.]+px\1/, `width='${boxWidth}px'`).replace(/height=(['"])[\d.]+px\1/, `height='${boxHeight}px'`);
    const maximumHeight = item.atom_count === 1 ? 80 : 220;
    const scale = Math.min((cardWidth - 30) / boxWidth, maximumHeight / boxHeight);
    const imageWidth = boxWidth * scale, imageHeight = boxHeight * scale;
    slide.images.add({blob: new TextEncoder().encode(svg), contentType: 'image/svg+xml', alt: `identity_smiles[${item.identity_index}], exact SMILES ${item.smiles}`, fit: 'contain', position: {left: x + (cardWidth - imageWidth) / 2, top: 1284 + (220 - imageHeight) / 2, width: imageWidth, height: imageHeight}});
    if (item.matched) text(slide, 'Matched identity', x + 18, 1496, cardWidth - 36, 30, 28, true, color.blue);
  }
}

/** 返回真实决策轨迹的短标题; 背景候选未进行 Match/Build, 适用范围外前景遵循既定免费跳过规则. */
function pathText(data) {
  if (data.case.group === 'background') return 'Background at rank 1, successful reconstruction at rank 2';
  if (data.case.group === 'scope_skip') return `Earlier foreground outside Stage3 scope, successful reconstruction at rank ${data.handoff.raw_rank}`;
  return 'The first-ranked site completes identity matching and pose reconstruction';
}

/** 根据冻结数据生成面板图注; 主文前三页为图 12–14, 其余为备选, 不将内部实现名称用作模型名称. */
function caption(pdb, index, data, ids) {
  const c = data.target_occurrence.components[0], target = `${c.ccd_id}(${c.auth_asym_id}:${c.auth_seq_id})`;
  const eligible = ids.identities.filter(item => item.eligible).length;
  const attempt = data.case.group === 'background' ? `首位背景消耗一次尝试，未进入 Match 或 Build；第二位 ${target} 完成重建。` : data.case.group === 'scope_skip' ? `前 ${data.handoff.raw_rank - 1} 位前景经 Stage3 范围门禁免费跳过，第 ${data.handoff.raw_rank} 位 ${target} 为首个计费候选。` : `首位 ${target} 依次完成区域检出、身份匹配和构象重建。`;
  const selected = data.handoff.candidate_selected === false ? '该候选原入选标记为 false，仍按完整顺序评价。' : '';
  return `${index < 3 ? `图 ${12 + index}｜` : '备选图｜'}${pdb.toUpperCase()} 的完整重建流程。${attempt}a–c，实验密度、CryoAtom2 重建受体及隔开的 GT 受体参考。d，预测 blob 的全局分布，彩框关联局部视图；e、f，GT 邻域与 Find 局部对照，同组朝向和尺度一致。g，原顺序的全部 ${ids.identity_count} 个 SMILES 身份，其中 ${eligible} 个合格小分子参与匹配，蓝框标出精确匹配项。h–j，PocketXMol-tuned 自评分首位姿态的受体、密度和沉积构象叠加视图，重原子 RMSD ${data.method.pose_min_rmsd_A['1'].toFixed(2)} Å。受体绿色，密度灰色，目标 blob 橙色，背景灰紫色，预测构象蓝色，沉积构象青绿色。所示目标位点生成 50 个姿态，每姿态 100 步采样；GT 用于参考显示与最终评价。${selected}`;
}

// 主文案例先后顺序与用户指定一致; 备选页保留真实轨迹与身份, 不新增模型推理.
for (const pdb of order) {
  const index=allOrder.indexOf(pdb);
  const data = JSON.parse(await fs.readFile(path.join(original, pdb, 'data.json'), 'utf8'));
  const ids = JSON.parse(await fs.readFile(path.join(output, pdb, 'identities/identity_manifest.json'), 'utf8'));
  const component = data.target_occurrence.components[0];
  const slide = deck.slides.add(), panels = [];
  slide.background.fill = '#FFFFFF';
  text(slide, `${pdb.toUpperCase()}  ${component.ccd_id} (${component.auth_asym_id}:${component.auth_seq_id})`, 130, 22, 1540, 58, 46, true);
  text(slide, pathText(data), 130, 85, 1580, 44, 32, false, color.muted);
  for (const [from, to] of [[188, 580], [630, 1154], [1204, 1550]]) {
    line(slide, 63, from + 10, 63, to - 12, '#bdcdc6', 3);
    line(slide, 56, to - 22, 63, to - 12, '#bdcdc6', 3);
    line(slide, 70, to - 22, 63, to - 12, '#bdcdc6', 3);
  }
  step(slide, 0, 'Input', 'Reconstructing the receptor from the experimental map with CryoAtom2', 138);
  const checks = framing[pdb].checks;
  // 原生相机投影记录为 960×720 window, 转换到 1440×1080 PNG 时统一乘 1.5.
  const structureCrop = cropUnion(['global_structure/ca2_receptor', 'global_structure/gt_receptor'].map(key => checks[key].window_bbox_xyxy.map(value => value * 1.5)), 36);
  // 密度完整源图原生重导为受体相机; 三图共用四边裁切与展示框, 保持相同 Å/显示 pixel.
  const topPanels = [['a', 'Experimental map', 'global_density_same_scale', structureCrop], ['b', 'CA2 receptor', 'global_ca2', structureCrop], ['c', 'GT receptor (reference)', 'global_gt', structureCrop]];
  for (const [i, [letter, title, render, crop]] of topPanels.entries()) {
    const x = 130 + i * 550;
    panelTitle(slide, letter, title, x, 218, 480);
    await picture(slide, panels, pdb, render, letter, [x, 260, 480, 300], crop);
  }
  text(slide, 'CryoAtom2', 544, 359, 222, 42, 30, true, color.step);
  line(slide, 555, 410, 767, 410, color.step, 4);
  line(slide, 752, 400, 767, 410, color.step, 4);
  line(slide, 752, 420, 767, 410, color.step, 4);
  // 虚线分栏明确 GT 是展示参考, 箭头只连接实验图与重建受体.
  for (let y = 210; y < 560; y += 20) line(slide, 1200, y, 1200, y + 11, '#bdcdc6', 2);
  step(slide, 1, 'Find', 'Locating candidate ligand regions in the experimental map', 580);
  panelTitle(slide, 'd', 'Global candidates', 130, 656, 620);
  const findCrop = cropUnion(['global_find/ca2_receptor', 'global_find/all_blob_voxels'].map(key => checks[key].window_bbox_xyxy.map(value => value * 1.5)).concat(projected[pdb].boxes.map(item => item.suggested_box_xyxy_px)), 36);
  const globalPanel = await picture(slide, panels, pdb, 'global_find', 'd', [130, 705, 620, 430], findCrop);
  const boxes = candidateFrames(slide, pdb, globalPanel);
  panelTitle(slide, 'e', 'GT neighborhood', 830, 656, 425);
  panelTitle(slide, 'f', 'Find prediction', 1285, 656, 425);
  const localCrop = cropUnion([renderBox(pdb, 'local_gt'), renderBox(pdb, 'local_find')], 24);
  if (data.case.group === 'background') {
    text(slide, 'Rank 1: background, one attempt', 830, 701, 880, 38, 30, true, color.background);
    const backgroundCrop = cropUnion([renderBox(pdb, 'background_gt'), renderBox(pdb, 'background_find')], 24);
    await picture(slide, panels, pdb, 'background_gt', 'e', [830, 745, 425, 175], backgroundCrop);
    await picture(slide, panels, pdb, 'background_find', 'f', [1285, 745, 425, 175], backgroundCrop);
    text(slide, 'Rank 2: target ligand, next attempt', 830, 922, 880, 38, 30, true, color.blob);
    await picture(slide, panels, pdb, 'local_gt', 'e', [830, 962, 425, 175], localCrop);
    await picture(slide, panels, pdb, 'local_find', 'f', [1285, 962, 425, 175], localCrop);
  } else {
    text(slide, `Rank ${data.handoff.raw_rank}: target ligand`, 830, 701, 880, 40, 30, true, color.blob);
    await picture(slide, panels, pdb, 'local_gt', 'e', [830, 747, 425, 350], localCrop);
    await picture(slide, panels, pdb, 'local_find', 'f', [1285, 747, 425, 350], localCrop);
    if (data.case.group === 'scope_skip') text(slide, data.handoff.raw_rank === 2 ? 'Rank 1: free scope skip' : `Ranks 1–${data.handoff.raw_rank - 1}: free scope skips`, 830, 1108, 880, 38, 30, false, color.scope);
  }
  step(slide, 2, 'Match', 'Matching candidate regions to ligand SMILES from the same PDB', 1154);
  text(slide, 'g', 99, 1233, 30, 40, 33, true);
  await identityRow(slide, ids);
  step(slide, 3, 'Build', 'Reconstructing ligand poses with PocketXMol-tuned', 1550);
  const dockCrop = cropUnion(['dock_receptor', 'dock_density', 'dock_gt_overlay'].map(name => renderBox(pdb, name)), 24);
  for (const [i, [letter, title, render]] of [['h', 'Receptor surface', 'dock_receptor'], ['i', 'Experimental density', 'dock_density'], ['j', 'Deposited pose overlay', 'dock_gt_overlay']].entries()) {
    const x = 130 + i * 550;
    panelTitle(slide, letter, title, x, 1630, 480);
    await picture(slide, panels, pdb, render, letter, [x, 1674, 480, 300], dockCrop);
  }
  text(slide, `RMSD ${data.method.pose_min_rmsd_A['1'].toFixed(2)} Å`, 130, 1990, 1580, 47, 34, true, color.blue);
  for (const [i, [label, tint]] of [['Receptor', color.receptor], ['Density', color.density], ['Target blob', color.blob], ['Predicted pose', color.blue], ['Deposited pose', color.teal]].entries()) {
    const x = 130 + i * 320;
    line(slide, x, 2068, x + 32, 2068, tint, 5);
    text(slide, label, x + 43, 2052, 270, 34, 27, false, color.muted);
  }
  const notes = caption(pdb, index, data, ids);
  slide.speakerNotes.textFrame.setText(notes);
 deck.comments.addThread({slide},'@@'+(`e2e-flow-${pdb}`),{position:{x:0,y:0,unit:'px'}});

  manifest.push({name: `e2e-flow-${pdb}`, pdb, caption: notes, panels, boxes, identities: ids.identities.map(item => ({identity_index: item.identity_index, smiles: item.smiles, eligible: item.eligible, matched: item.matched, chemical_graph_passed: item.chemical_graph.passed})), canvas_px: [width, height], final_physical_width_mm: 183});
}
await fs.mkdir(temp, {recursive: true});
await fs.writeFile(path.join(temp, 'deck_manifest.json'), JSON.stringify(manifest, null, 2));
const candidate = path.join(temp, 'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
// artifact-tool 的 cover 导出会重算 srcRect; 将已记录的裁切写回原生 PPT 属性, 不裁写媒体文件.
execFileSync(`${runtime}/python/python.exe`, [path.join(code, 'apply_native_crop.py'),'--build-root',temp], {cwd: project, stdio: 'inherit'});
const regenerated=process.env.FIGURE_BUILD_ROOT ? path.join(process.env.FIGURE_BUILD_ROOT,'published') : selectedPdb?path.join(project,`画图/画图代码/e2e/output/e2e-flow-${selectedPdb}/regenerated`):path.join(project,'画图/画图代码/e2e/output/e2e-flow/regenerated/display');
await fs.mkdir(regenerated,{recursive:true});
const stamp = Date.now().toString(), validated = path.join(regenerated, `validated-${stamp}.pptx`);
await fs.mkdir(path.join(temp, 'validation'), {recursive: true});
await finalizePresentation({workspaceDir: project, candidatePath: candidate, finalPath: validated, pythonExecutable: `${runtime}/python/python.exe`, integrityValidatorPath: path.join(skill, 'container_tools/inspect_presentation_package_integrity.py'), layoutValidatorPath: path.join(skill, 'container_tools/inspect_presentation_layout_geometry.py'), layoutArgs: ['--expected-slide-size-emu', `${width * 9525},${height * 9525}`], explicitTotalSlideCount: order.length, fontPolicy: {basis: 'design', families: ['Arial']}, verifyArtifactToolImport: true, receiptPath: path.join(temp,`validation_${stamp}.json`)});
await fs.copyFile(validated, path.join(temp, 'validated.pptx'));
console.log(`${order.length} editable v2 flow page(s) exported and structurally validated.`);
