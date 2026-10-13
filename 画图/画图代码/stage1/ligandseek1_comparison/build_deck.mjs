// 将 Matplotlib SVG 的既有场景等比 transport 为七页原生 PowerPoint 对象; 不读取或计算科学指标.
// 入口参数依次为 manifest.json 路径、temp/ 下的构建输出目录; candidate.pptx 尚需主工作流最终验收和发布.
// candidate.pptx 保存七页可编辑对象、图名批注及双语图注; 不含整图栅格图片.
// transport_validation.json 是一个 JSON 对象, 只记录显示几何和原生对象数量:
// - slide_count: int, 总页数.
// - slide_size_px: number[2], 页宽/高, 单位 CSS px.
// - pages: object[], 按页序记录以下字段.
//   - stem: string, 源 SVG 无扩展名文件名.
//   - name: string, 唯一图名, 不含批注的 @@ 前缀.
//   - counts: object, 三种原生形状的数量.
//     - text: int, 原生文本框数量.
//     - ellipse: int, 原生椭圆数量.
//     - path: int, 原生路径数量.
//   - source_shape_count: int, 同页源 SVG 场景对象总数.
//   - scale_px_per_pt: number, 源 SVG pt 到 CSS px 的等比缩放因子.
//   - offset_px: number[2], 源 SVG 左上角在页内的 X/Y 居中偏移, 单位 px.
// candidate.inspect.ndjson 每行是 artifact 工具的 slide/textbox/shape/notes/thread 检查记录, 不保存科学指标或第二套绘图.
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [manifestPath, buildOutput] = process.argv.slice(2);  // 两个具体路径, 不引入旧图的输出目录、页码或 shape 编号.
const runtimeModule = "C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { Presentation, PresentationFile } = await import(pathToFileURL(runtimeModule).href);
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));  // slide_size_pt 和 pages[*].shapes 均来自已审计的同一 Matplotlib SVG.
const slideWidth = manifest.slide_size_pt[0] * 96 / 72;  // 源图 pt -> CSS px; 同一物理宽度对应 96 DPI.
const slideHeight = manifest.slide_size_pt[1] * 96 / 72;  // 源图 pt -> CSS px; 组合页与 Matplotlib 画布物理尺寸相同.
const presentation = Presentation.create({ slideSize: { width: slideWidth, height: slideHeight } });
presentation.comments.setSelf({ displayName: "Figure Editor", initials: "FE", userId: "figure-editor", providerId: "None" });  // 本地编辑身份, 不冒充作者账户; 两字段是 PowerPoint 现代批注的必需身份属性.
const pageReports = [];  // 每页原生文本/椭圆/路径计数及等比变换, 仅供编辑性检查.
let sequence = 0;

function svgFill(value, alpha) {
  // 将 SVG 填色转换为原生填充; value 是 RGB 颜色字符串或 none, alpha 是 [0,1] 不透明度.
  // 返回 none 或 solid 对象; color.value 保留 RGB, color.transform.opacity 保留原 alpha, 不按百分比舍入.
  return value === "none" ? "none" : { type: "solid", color: { type: "rgb", value, transform: { opacity: alpha } } };
}

for (const page of manifest.pages) {
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  const scale = Math.min(slideWidth / page.width, slideHeight / page.height);  // pt -> px 的统一比例, 两轴采用相同比例以保持 SVG 几何.
  const offsetX = (slideWidth - page.width * scale) / 2;  // 仅等比居中源 SVG, 不重排图例或轴标签.
  const offsetY = (slideHeight - page.height * scale) / 2;
  const counts = { text: 0, ellipse: 0, path: 0 };  // 三种支持的原生对象数量; 不添加整图图片.
  for (const shape of page.shapes) {
    const position = { left: offsetX + shape.x * scale, top: offsetY + shape.y * scale, width: Math.max(0.02, shape.w * scale), height: Math.max(0.02, shape.h * scale) };  // x/y/w/h 的单位 pt -> px; 0.02 px 只避免零宽/高路径的原生对象框退化.
    if (shape.kind === "text") {
      const textbox = slide.shapes.add({ geometry: "textbox", name: `${page.stem}_text_${sequence++}`, position: { ...position, rotation: shape.rotation }, fill: "none", line: { fill: "none", width: 0 } });
      textbox.text = shape.text;  // 保留 Unicode 下标与品牌大小写, 不改写轴标签或图例文字.
      textbox.text.style = { typeface: shape.font_family, fontSize: shape.font * scale, bold: shape.bold, color: shape.color, alignment: "left", verticalAlignment: "middle", autoFit: "none", wrap: "none", insets: 0 };
      counts.text += 1;
      continue;
    }
    const config = { name: `${page.stem}_${shape.kind}_${sequence++}`, position, fill: svgFill(shape.fill, shape.fill_alpha), line: { fill: svgFill(shape.stroke, shape.stroke_alpha), width: shape.stroke === "none" ? 0 : shape.stroke_width * scale, style: "solid" } };
    if (shape.dash !== "none") throw new Error(`Unexpected dashed transport path in ${page.stem}; the source must publish segmented equality lines.`);
    if (shape.kind === "ellipse") {
      slide.shapes.add({ geometry: "ellipse", ...config });
      counts.ellipse += 1;
      continue;
    }
    if (shape.kind !== "path") throw new Error(`Unsupported SVG scene kind: ${shape.kind}`);
    const commands = [];  // 原生 custom path 的局部 X/Y px 折线命令, 每个 part 保留 SVG 中的分段边界.
    for (const part of shape.parts) {
      for (const [index, point] of part.entries()) commands.push({ [index === 0 ? "moveTo" : "lineTo"]: { x: point[0] * scale, y: point[1] * scale } });
      if (Math.hypot(part[0][0] - part.at(-1)[0], part[0][1] - part.at(-1)[1]) < 1e-5) commands.push({ close: {} });
    }
    slide.shapes.add({ geometry: "custom", ...config, customPaths: [{ width: position.width, height: position.height, commands }] });
    counts.path += 1;
  }
  slide.speakerNotes.text = page.notes;  // 中文和 ENGLISH: 后的英文图注均由 manifest 提供.
  presentation.comments.addThread({ slide }, `@@${page.name}`, { position: { x: 0, y: 0, unit: "px" } });  // 批注单独承载唯一图名, 不混入图注.
  pageReports.push({ stem: page.stem, name: page.name, counts, source_shape_count: page.shapes.length, scale_px_per_pt: scale, offset_px: [offsetX, offsetY] });
}
await fs.mkdir(buildOutput, { recursive: true });
await (await PresentationFile.exportPptx(presentation)).save(path.join(buildOutput, "candidate.pptx"));
await fs.writeFile(path.join(buildOutput, "transport_validation.json"), JSON.stringify({ slide_count: presentation.slides.items.length, slide_size_px: [slideWidth, slideHeight], pages: pageReports }, null, 2), "utf8");
await fs.writeFile(path.join(buildOutput, "candidate.inspect.ndjson"), (await presentation.inspect({ kind: "slide,textbox,shape,notes,thread", maxChars: 2000000 })).ndjson, "utf8");
