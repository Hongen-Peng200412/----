// SVG 的文字、路径和散点逐组件转为原生 PowerPoint 对象；不嵌入统计图截图。
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {existsSync} from 'node:fs';

let root = path.dirname(fileURLToPath(import.meta.url));
while (!existsSync(path.join(root, '论文草稿.md'))) root = path.dirname(root);
const build = process.env.FIGURE_BUILD_ROOT ?? path.join(root, 'temp/stage1_revision_20261025/figures');
const runtime = process.env.RUNTIME_NODE_MODULES ?? 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {Presentation, PresentationFile} = await import(pathToFileURL(path.join(runtime, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const pages = JSON.parse(await fs.readFile(path.join(build, 'scenes.json'), 'utf8'));
const deck = Presentation.create({slideSize: {width: 1000, height: 924}});
// 复用作者在正式 PPT 中已有的批注身份; 不再创建 Figure Editor 占位作者.
deck.comments.setSelf({displayName: 'Hongen Peng', initials: 'HP', userId: '965de47efeb7ffa5', providerId: 'Windows Live'});
let sequence = 0;
const alphaColour = (value, alpha) => value === 'none' ? 'none' : alpha < 1 ? `${value}/${Math.round(alpha * 100)}` : value;
for (const page of pages) {
  const slide = deck.slides.add();
  slide.background.fill = '#FFFFFF';
  const scale = Math.min(950 / page.width, 890 / page.height);
  const offsetX = (1000 - page.width * scale) / 2;
  const offsetY = (924 - page.height * scale) / 2;
  for (const shape of page.shapes) {
    const position = {left: offsetX + shape.x * scale, top: offsetY + shape.y * scale, width: Math.max(0.02, shape.w * scale), height: Math.max(0.02, shape.h * scale)};
    if (shape.kind === 'text') {
      const text = slide.shapes.add({geometry: 'textbox', name: `text_${sequence++}`, position: {...position, rotation: shape.rotation}, fill: 'none', line: {fill: 'none', width: 0}});
      text.text = shape.text;
      text.text.style = {typeface: shape.font_family, fontSize: shape.font * scale, bold: shape.bold, color: shape.color, alignment: 'left', verticalAlignment: 'middle', autoFit: 'none', wrap: 'none', insets: {left: 0, right: 0, top: 0, bottom: 0}};
    } else {
      const style = {name: `data_${sequence++}`, position, fill: alphaColour(shape.fill, shape.fill_alpha), line: {fill: alphaColour(shape.stroke, shape.stroke_alpha), width: shape.stroke === 'none' ? 0 : shape.stroke_width * scale, style: shape.dash === 'none' ? 'solid' : 'dashed'}};
      if (shape.kind === 'ellipse') slide.shapes.add({geometry: 'ellipse', ...style});
      else {
        const commands = [];
        for (const part of shape.parts) {
          part.forEach((point, index) => commands.push({[index ? 'lineTo' : 'moveTo']: {x: point[0] * scale, y: point[1] * scale}}));
          if (Math.hypot(part[0][0] - part.at(-1)[0], part[0][1] - part.at(-1)[1]) < 1e-5) commands.push({close: {}});
        }
        slide.shapes.add({geometry: 'custom', ...style, customPaths: [{width: position.width, height: position.height, commands}]});
      }
    }
  }
  slide.speakerNotes.textFrame.setText(page.notes);
  deck.comments.addThread({slide}, `@@${page.id}`, {position: {x: 0, y: 0, unit: 'px'}});
}
await (await PresentationFile.exportPptx(deck)).save(path.join(build, 'candidate.pptx'));
console.log(`Created ${pages.length} editable figure pages in ${build}`);
