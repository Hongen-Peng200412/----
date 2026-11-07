// 按调用者提供的场景和显示配置装配原生PPT, 不选择实验、方法或科学字段.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const build = path.resolve(process.argv[2]);
const runtime = process.env.RUNTIME_NODE_MODULES;
if (!runtime) throw new Error('请由项目入口配置RUNTIME_NODE_MODULES');
const {Presentation, PresentationFile} = await import(pathToFileURL(path.join(runtime, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const pages = JSON.parse(await fs.readFile(path.join(build, 'scenes.json'), 'utf8'));
const display = JSON.parse(await fs.readFile(path.resolve(process.argv[3]), 'utf8'));
const layouts = display.layouts;
const deck = Presentation.create({slideSize: display.canvas});
deck.comments.setSelf(display.author);
const alphaColour = (value, alpha) => value === 'none' ? 'none' : alpha < 1 ? `${value}/${Math.round(alpha * 100)}` : value;
const receipts = [];
for (const page of pages) {
  const layout = layouts[page.id];
  if (layout && page.shapes.length !== layout.expected_source_shapes) throw new Error(`${page.id}: 原件重算形状数量改变, 不能套用作者面板参数`);
  const slide = deck.slides.add();
  slide.background.fill = '#FFFFFF';
  const scale = display.scale ?? Math.min(display.viewport.width / page.width, display.viewport.height / page.height);
  const offsetX = display.offset?.[0] ?? (display.canvas.width - page.width * scale) / 2;
  const offsetY = display.offset?.[1] ?? (display.canvas.height - page.height * scale) / 2;
  let emitted = 0;
  for (const [index, shape] of page.shapes.entries()) {
    // 此处只保存面板平移及文字省略. 点、柱和曲线坐标都由本次原科学值重新生成.
    if (layout?.omit_shape_indices.includes(index)) continue;
    let dx = 0, dy = 0;
    if (layout) {
      const range = layout.shape_index_ranges.find(item => index >= item.first && index <= item.last);
      if (range) [dx, dy] = [range.dx, range.dy];
      if (layout.specific_shifts[String(index)]) [dx, dy] = layout.specific_shifts[String(index)];
    }
    const position = {left: offsetX + shape.x * scale + dx / 9525, top: offsetY + shape.y * scale + dy / 9525, width: Math.max(.02, shape.w * scale), height: Math.max(.02, shape.h * scale)};
    if (shape.kind === 'text') {
      const text = slide.shapes.add({geometry: 'textbox', name: shape.name ?? `text_${index}`, position: {...position, rotation: shape.rotation}, fill: 'none', line: {fill: 'none', width: 0}});
      text.text = layout?.blank_text_indices.includes(index) ? '' : shape.text;
      text.text.style = {typeface: shape.font_family, fontSize: shape.font * scale, bold: shape.bold, color: shape.color, alignment: 'left', verticalAlignment: 'middle', autoFit: 'none', wrap: 'none', insets: {left: 0, right: 0, top: 0, bottom: 0}};
    } else {
      const style = {name: shape.name ?? `data_${index}`, position, fill: alphaColour(shape.fill, shape.fill_alpha), line: {fill: alphaColour(shape.stroke, shape.stroke_alpha), width: shape.stroke === 'none' ? 0 : shape.stroke_width * scale, style: shape.dash === 'none' ? 'solid' : 'dashed'}};
      if (shape.kind === 'ellipse') slide.shapes.add({geometry: 'ellipse', ...style});
      else {
        const commands = [];
        for (const part of shape.parts) {
          part.forEach((point, i) => commands.push({[i ? 'lineTo' : 'moveTo']: {x: point[0] * scale, y: point[1] * scale}}));
          if (Math.hypot(part[0][0] - part.at(-1)[0], part[0][1] - part.at(-1)[1]) < 1e-5) commands.push({close: {}});
        }
        slide.shapes.add({geometry: 'custom', ...style, customPaths: [{width: position.width, height: position.height, commands}]});
      }
    }
    emitted++;
  }
  if (layout && emitted !== layout.expected_final_shapes) throw new Error(`${page.id}: 作者最终形状数量不符`);
  slide.speakerNotes.textFrame.setText(page.notes);
  deck.comments.addThread({slide}, `@@${page.id}`, {position: {x: 0, y: 0, unit: 'px'}});
  receipts.push({figure: page.id, source_shapes: page.shapes.length, final_shapes: emitted, author_panel_parameters_applied: Boolean(layout)});
}
await (await PresentationFile.exportPptx(deck)).save(path.join(build, 'candidate.pptx'));
await fs.writeFile(path.join(build, 'assembly.json'), JSON.stringify(receipts, null, 2));
console.log(JSON.stringify(receipts));
