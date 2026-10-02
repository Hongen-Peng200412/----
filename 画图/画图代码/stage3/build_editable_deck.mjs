/** 从冻结逐实例 RMSD 生成两页可逐点编辑的 PowerPoint 图集。 */

import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import pptxgen from "file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs/dist/pptxgen.cjs.js";

const paper = "C:/Users/15919/Desktop/论文草稿";
const data = JSON.parse(await fs.readFile(path.join(paper, "画图/画图代码/stage3/data.json"), "utf8"));
const output = path.join(paper, "temp/stage3-deck-build/stage3-native-draft.pptx");
const pptx = new pptxgen();
const inch = value => value / 72;
const color = { GT: "2D887E", CA2: "5879BD", Build: "B57442", ink: "25323B", light: "B8C2C8", guide: "C7CFD4" };
const full = new Map(data.series.map(group => [`${group.model}/${group.receptor}/${group.protocol}`, group.rows]));
const shared = new Set(data.build.filter(row => row.top1 !== null && row.best !== null)
  .map(row => `${row.pdb_id}/${row.occurrence_id}`));
const build = data.build.filter(row => shared.has(`${row.pdb_id}/${row.occurrence_id}`));

pptx.defineLayout({ name: "STAGE3", width: inch(980), height: inch(720) });
pptx.layout = "STAGE3";
pptx.author = "Manuscript figures";

function label(slide, value, x, y, w, h, size, options = {}) {
  slide.addText(value, {
    x: inch(x), y: inch(y), w: inch(w), h: inch(h),
    fontFace: "Arial", fontSize: size, color: options.color ?? color.ink,
    bold: options.bold ?? false, align: options.align ?? "left",
    valign: "mid", margin: 0, vert: options.vertical ? "vert270" : "horz",
  });
}

function line(slide, x1, y1, x2, y2, shade, width = 0.8, dashed = false) {
  slide.addShape(pptx.ShapeType.line, {
    x: inch(Math.min(x1, x2)), y: inch(Math.min(y1, y2)),
    w: inch(Math.max(Math.abs(x2 - x1), 0.01)),
    h: inch(Math.max(Math.abs(y2 - y1), 0.01)),
    flipV: (x2 - x1) * (y2 - y1) < 0,
    line: { color: shade, width, dash: dashed ? "dash" : "solid" },
  });
}

function dot(slide, x, y, shade, capped) {
  slide.addShape(capped ? pptx.ShapeType.triangle : pptx.ShapeType.ellipse, {
    x: inch(x - (capped ? 3 : 1.55)), y: inch(y - (capped ? 3 : 1.55)),
    w: inch(capped ? 6 : 3.1), h: inch(capped ? 5 : 3.1),
    fill: { color: shade, transparency: capped ? 18 : 61 },
    line: { color: shade, transparency: 100 },
  });
}

function quantile(values, fraction) {
  const index = fraction * (values.length - 1);
  const low = Math.floor(index);
  const high = Math.ceil(index);
  return values[low] + (index - low) * (values[high] - values[low]);
}

function distribution(slide, rows, field, x, shade, mapY, cap = null) {
  const valid = rows.filter(row => row[field] !== null);
  const values = valid.map(row => row[field]).sort((a, b) => a - b);
  // 每个原始实例画一个独立对象；哈希只决定横向抖动，不进入 RMSD 计算。
  for (const row of valid) {
    const key = `${row.pdb_id}/${row.occurrence_id}`;
    const fraction = crypto.createHash("sha256").update(key).digest().readUInt32BE(0) / 2 ** 32;
    const capped = cap !== null && row[field] > cap;
    dot(slide, x + (fraction - 0.5) * 34, capped ? mapY(cap) - 21 : mapY(row[field]), shade, capped);
  }
  const [p05, p25, median, p75, p95] = [0.05, 0.25, 0.5, 0.75, 0.95]
    .map(fraction => quantile(values, fraction));
  line(slide, x, mapY(p05), x, mapY(p95), shade, 1.1);
  for (const point of [p05, p95]) line(slide, x - 9, mapY(point), x + 9, mapY(point), shade, 1.1);
  slide.addShape(pptx.ShapeType.rect, {
    x: inch(x - 13), y: inch(mapY(p75)), w: inch(26), h: inch(mapY(p25) - mapY(p75)),
    fill: { color: "FFFFFF", transparency: 16 }, line: { color: shade, width: 1.55 },
  });
  line(slide, x - 13, mapY(median), x + 13, mapY(median), shade, 2.5);
}

function axis(slide, left, right, top, bottom, low, high, ticks, capped, showLabels = true) {
  const bodyTop = top + (capped ? 25 : 0);
  const mapY = value => bottom - (Math.log10(value) - Math.log10(low))
    / (Math.log10(high) - Math.log10(low)) * (bottom - bodyTop);
  line(slide, left, top, left, bottom, color.ink, 0.95);
  line(slide, left, bottom, right, bottom, color.ink, 0.95);
  for (const tick of ticks) {
    const y = mapY(tick);
    line(slide, left - 5, y, left, y, color.ink);
    if (showLabels) label(slide, String(tick), left - 50, y - 9, 40, 18, 13, { align: "right" });
  }
  if (capped) {
    line(slide, left - 5, top + 4, left, top + 4, color.ink);
    label(slide, "50+", left - 56, top - 6, 46, 19, 13, { align: "right" });
    // 轴断裂只改变 >50 Å 点的显示高度；所有箱线分位数仍用原始距离。
    line(slide, left - 5, top + 14, left + 2, top + 19, color.ink, 0.9);
    line(slide, left - 5, top + 19, left + 2, top + 24, color.ink, 0.9);
  }
  for (const threshold of [2, 3]) {
    line(slide, left, mapY(threshold), right, mapY(threshold), color.guide, 0.65, true);
  }
  return mapY;
}

function key(slide, items) {
  const starts = items.length === 2 ? [305, 560] : [185, 425, 700];
  items.forEach(([name, shade], index) => {
    slide.addShape(pptx.ShapeType.rect, {
      x: inch(starts[index]), y: inch(30), w: inch(15), h: inch(9),
      fill: { color: shade }, line: { color: shade },
    });
    label(slide, name, starts[index] + 22, 22, items.length === 2 ? 194 : 208, 26, 15);
  });
}

function fullPanel(slide, letter, title, field, top, bottom) {
  const left = 129, right = 908;
  const centres = [231, 406, 631, 806];
  label(slide, letter, 66, top - 58, 35, 34, 23, { bold: true });
  label(slide, title, 103, top - 58, 190, 31, 19);
  label(slide, "Centre pocket · C0", 160, top - 28, 321, 24, 15, { align: "center" });
  label(slide, "Envelope pocket · E", 550, top - 28, 321, 24, 15, { align: "center" });
  const mapY = axis(slide, left, right, top, bottom, 0.15, 50,
    [0.2, 0.5, 1, 2, 3, 5, 10, 50], true);
  label(slide, "RMSD (Å)", 57, top + 32, 31, bottom - top - 36, 16,
    { vertical: true, align: "center" });
  line(slide, 518, top + 1, 518, bottom, color.light, 0.85);
  centres.forEach((centre, index) => {
    const protocol = index < 2 ? "C0" : "E";
    const model = index % 2 === 0 ? "official" : "local_cov";
    for (const [receptor, offset] of [["GT", -26], ["CA2", 26]]) {
      distribution(slide, full.get(`${model}/${receptor}/${protocol}`),
        field, centre + offset, color[receptor], mapY, 50);
    }
    line(slide, centre, bottom, centre, bottom + 5, color.ink);
    label(slide, index % 2 === 0 ? "Official" : "Tuned",
      centre - 65, bottom + 7, 130, 27, 16, { align: "center" });
  });
}

function officialFigure() {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  key(slide, [["GT receptor", color.GT], ["CryoAtom2 receptor", color.CA2]]);
  fullPanel(slide, "a", "Top-1 pose", "top1", 120, 326);
  fullPanel(slide, "b", "Best of 50", "best", 442, 648);
}

function buildPanel(slide, letter, title, field, left, right, centres, showLabels) {
  const top = 135, bottom = 583;
  label(slide, letter, left - 24, 76, 28, 35, 23, { bold: true });
  label(slide, title, left + 35, 76, 171, 35, 19);
  const mapY = axis(slide, left, right, top, bottom, 0.18, 25,
    [0.2, 0.5, 1, 2, 3, 5, 10, 20], false, showLabels);
  const groups = [
    [full.get("local_cov/GT/C0").filter(row => shared.has(`${row.pdb_id}/${row.occurrence_id}`)), color.GT],
    [full.get("local_cov/CA2/C0").filter(row => shared.has(`${row.pdb_id}/${row.occurrence_id}`)), color.CA2],
    [build, color.Build],
  ];
  const names = ["Tuned\nGT", "Tuned\nCryoAtom2", "Emap2lig-\nBuild"];
  groups.forEach(([rows, shade], index) => {
    distribution(slide, rows, field, centres[index], shade, mapY);
    line(slide, centres[index], bottom, centres[index], bottom + 5, color.ink);
    label(slide, names[index], centres[index] - 59, bottom + 11, 118, 58, 15, { align: "center" });
  });
}

function buildFigure() {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  key(slide, [
    ["Tuned · GT", color.GT], ["Tuned · CryoAtom2", color.CA2],
    ["Emap2lig-Build", color.Build],
  ]);
  buildPanel(slide, "a", "Top-1 pose", "top1", 107, 465, [171, 285, 399], true);
  buildPanel(slide, "b", "Best of 50", "best", 565, 923, [629, 743, 857], true);
  label(slide, "RMSD (Å)", 47, 205, 31, 300, 16,
    { vertical: true, align: "center" });
  label(slide, "RMSD (Å)", 480, 205, 31, 300, 16,
    { vertical: true, align: "center" });
}

officialFigure();
buildFigure();
await fs.mkdir(path.dirname(output), { recursive: true });
await pptx.writeFile({ fileName: output });
console.log(output);
