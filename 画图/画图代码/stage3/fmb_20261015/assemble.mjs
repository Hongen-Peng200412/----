// 将同源 SVG 几何装配为 PPT 原生形状; 字体和几何均按物理尺寸映射.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Presentation, PresentationFile} from 'file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const build = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..', 'temp/fmb_20261015');
const pages = JSON.parse(await fs.readFile(path.join(build, 'scenes.json'), 'utf8'));
const scale = 4 / 3; // SVG pt → CSS px, 保持 180 mm 图宽和原始字号.
const width = 180 / 25.4 * 96;
const height = 240 / 25.4 * 96;
const presentation = Presentation.create({slideSize: {width, height}});
let sequence = 0;

// 透明度沿用 SVG, 不将灰点或小提琴重新计算为另一套数据.
function color(value, alpha) {
  return value === 'none' ? 'none' : alpha < 1 ? `${value}/${Math.round(alpha * 100)}` : value;
}

for (const page of pages) {
  const slide = presentation.slides.add();
  slide.background.fill = '#FFFFFF';
  const offsetY = (height - page.height * scale) / 2;
  for (const item of page.shapes) {
    const position = {left: item.x * scale, top: offsetY + item.y * scale, width: Math.max(0.02, item.w * scale), height: Math.max(0.02, item.h * scale)};
    if (item.kind === 'text') {
      position.rotation = item.rotation;
      const shape = slide.shapes.add({geometry: 'textbox', name: `text_${sequence++}`, position, fill: 'none', line: {fill: 'none', width: 0}});
      shape.text = item.text;
      shape.text.style = {typeface: 'Arial', fontSize: item.font * scale, bold: item.bold, color: item.color, alignment: 'left', verticalAlignment: 'middle', autoFit: 'none', wrap: 'none', insets: {left: 0, right: 0, top: 0, bottom: 0}};
      continue;
    }
    const config = {name: `${page.stem}_${sequence++}`, position, fill: color(item.fill, item.fill_alpha), line: {fill: color(item.stroke, item.stroke_alpha), width: item.stroke === 'none' ? 0 : item.stroke_width * scale, style: item.dash === 'none' ? 'solid' : 'dashed'}};
    if (item.kind === 'ellipse') {
      slide.shapes.add({geometry: 'ellipse', ...config});
    } else {
      const commands = [];
      for (const part of item.parts) {
        part.forEach((point, index) => commands.push({[index ? 'lineTo' : 'moveTo']: {x: point[0] * scale, y: point[1] * scale}}));
        if (Math.hypot(part[0][0] - part.at(-1)[0], part[0][1] - part.at(-1)[1]) < 1e-5) commands.push({close: {}});
      }
      slide.shapes.add({geometry: 'custom', ...config, customPaths: [{width: position.width, height: position.height, commands}]});
    }
  }
  slide.speakerNotes.textFrame.setText(page.notes);
  console.log(`${page.stem}: ${page.shapes.length} editable shapes`);
}
await (await PresentationFile.exportPptx(presentation)).save(path.join(build, 'candidate.pptx'));
