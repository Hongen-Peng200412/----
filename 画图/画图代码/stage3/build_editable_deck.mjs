/** 从冻结实例 RMSD 生成三页可逐点编辑的 PowerPoint 图集。 */

import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import pptxgen from "file:///C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs/dist/pptxgen.cjs.js";

const paper = "C:/Users/15919/Desktop/论文草稿";
const input = path.join(paper, "画图/画图代码/stage3/data.json");
const buildDir = path.join(paper, "temp/stage3-deck-build");
const output = path.join(buildDir, "stage3-native-draft.pptx");
const data = JSON.parse(await fs.readFile(input, "utf8"));
const pptx = new pptxgen();
const width = 960;
const height = 505;
const ptToIn = value => value / 72;
const colors = { GT: "32887D", CA2: "5575B2", Build: "B17642", ink: "26333D", muted: "68747D", rule: "B8C0C5" };
const full = new Map(data.series.map(item => [`${item.model}/${item.receptor}/${item.protocol}`, item.rows]));
const subset = new Set(data.build.filter(row => row.top1 !== null && row.best !== null).map(row => `${row.pdb_id}/${row.occurrence_id}`));
const legends = [
  "图 7 | 官方与 local_cov 模型的首位配体姿态 RMSD。完整测试集包含 446 个小分子实例。左半为真实中心条件 C0，右半为真实包络条件 E；青绿色表示真实受体，蓝色表示 CryoAtom2 重建受体。每个浅色点是一个实例的 Top-1 姿态；箱体、中间横线和须分别表示第 25–75 百分位数、中位数和第 5–95 百分位数。纵轴使用对数刻度，灰色虚线标出 2 Å。官方模型在真实受体条件下有一个实例未形成可评价姿态，因此相应两组各有 445 个 RMSD；其余各组均为 446 个。",
  "图 8 | 官方与 local_cov 模型的 50 个候选中最佳配体姿态 RMSD。数据、C0/E 定位条件及颜色与图 7 相同。每个点是同一实例 50 个候选中最低的重原子 RMSD，表示事后可达到的精度上界，而非模型的候选排序结果。箱体、中间横线和须分别表示第 25–75 百分位数、中位数和第 5–95 百分位数；纵轴为对数刻度，虚线为 2 Å。官方模型在真实受体条件下有一个实例无可评价姿态，相应两组 n = 445；其余组 n = 446。",
  "图 9 | Find 命中实例上 local_cov-C 与 Emap2lig-Build 的配体姿态 RMSD。共同展示 237 个有可评价姿态的测试实例。a，原排序首位姿态；b，50 个候选中的最低 RMSD。local_cov-C 在真实中心 C0 下分别使用真实受体（青绿色）和 CryoAtom2 受体（蓝色），Emap2lig-Build 使用 Find 预测的原生 blob（赭色）。每点为一个实例；箱体、中间横线和须分别表示第 25–75 百分位数、中位数和第 5–95 百分位数。纵轴为对数刻度，虚线为 2 Å。",
];

pptx.defineLayout({ name: "STAGE3", width: ptToIn(width), height: ptToIn(height) });
pptx.layout = "STAGE3";
pptx.author = "Manuscript figures";
pptx.subject = "Frozen Stage3 docking RMSD distributions";

function addText(slide, value, x, y, w, h, size, options = {}) {
  slide.addText(value, {
    x: ptToIn(x), y: ptToIn(y), w: ptToIn(w), h: ptToIn(h),
    fontFace: "Arial", fontSize: size, color: options.color ?? colors.ink,
    bold: options.bold ?? false, align: options.align ?? "left",
    valign: "mid", breakLine: false, margin: 0,
    vert: options.vertical ? "vert270" : "horz",
  });
}

function addLine(slide, x1, y1, x2, y2, color, weight, dashed = false) {
  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2);
  slide.addShape(pptx.ShapeType.line, {
    x: ptToIn(left), y: ptToIn(top),
    w: ptToIn(Math.max(Math.abs(x2 - x1), 0.01)),
    h: ptToIn(Math.max(Math.abs(y2 - y1), 0.01)),
    flipV: (x2 - x1) * (y2 - y1) < 0,
    line: { color, width: weight, dash: dashed ? "dash" : "solid" },
  });
}

function addDot(slide, x, y, color) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x: ptToIn(x - 1.65), y: ptToIn(y - 1.65), w: ptToIn(3.3), h: ptToIn(3.3),
    fill: { color, transparency: 73 }, line: { color, transparency: 100 },
  });
}

function addDistribution(slide, rows, field, x, color, mapY) {
  const valid = rows.filter(row => row[field] !== null);
  const values = valid.map(row => row[field]).sort((a, b) => a - b);
  const quantile = fraction => {
    const position = fraction * (values.length - 1);
    const start = Math.floor(position);
    const end = Math.ceil(position);
    return values[start] + (position - start) * (values[end] - values[start]);
  };

  // 每个原始实例仍各占一个 PowerPoint 原生点; 抖动只移动横向显示位置。
  for (const row of valid) {
    const token = `${row.pdb_id}/${row.occurrence_id}`;
    const fraction = crypto.createHash("sha256").update(token).digest().readUInt32BE(0) / 2 ** 32;
    addDot(slide, x + (fraction - 0.5) * 34, mapY(row[field]), color);
  }
  const [p05, p25, median, p75, p95] = [0.05, 0.25, 0.5, 0.75, 0.95].map(quantile);
  addLine(slide, x, mapY(p05), x, mapY(p95), color, 1.1);
  addLine(slide, x - 8, mapY(p05), x + 8, mapY(p05), color, 1.1);
  addLine(slide, x - 8, mapY(p95), x + 8, mapY(p95), color, 1.1);
  slide.addShape(pptx.ShapeType.rect, {
    x: ptToIn(x - 12), y: ptToIn(mapY(p75)), w: ptToIn(24),
    h: ptToIn(mapY(p25) - mapY(p75)),
    fill: { color: "FFFFFF" }, line: { color, width: 1.5 },
  });
  addLine(slide, x - 12, mapY(median), x + 12, mapY(median), color, 2.4);
}

function addAxis(slide, left, top, right, bottom, low, high, ticks, leftLabels) {
  const mapY = value => bottom - (Math.log10(value) - Math.log10(low)) / (Math.log10(high) - Math.log10(low)) * (bottom - top);
  addLine(slide, left, top, left, bottom, colors.ink, 1.0);
  addLine(slide, left, bottom, right, bottom, colors.ink, 1.0);
  for (const tick of ticks) {
    const y = mapY(tick);
    addLine(slide, left - 5, y, left, y, colors.ink, 0.9);
    if (leftLabels) addText(slide, String(tick), left - 55, y - 12, 43, 22, 13, { align: "right" });
  }
  addLine(slide, left, mapY(2), right, mapY(2), "A5ADB3", 0.8, true);
  return mapY;
}

function addFullFigure(field, legend, filename) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addNotes(legend);
  const left = 105;
  const right = 920;
  const top = 93;
  const bottom = 402;
  const mapY = addAxis(slide, left, top, right, bottom, 0.15, 260, [0.2, 0.5, 1, 2, 5, 10, 50, 200], true);
  addText(slide, "Ligand heavy-atom RMSD (Å)", 14, 149, 40, 252, 18, { vertical: true, align: "center" });
  addText(slide, "Known centre · C0", 188, 57, 245, 26, 17, { align: "center" });
  addText(slide, "Known pocket · E", 595, 57, 245, 26, 17, { align: "center" });
  addLine(slide, 512, top, 512, bottom, colors.rule, 0.8);
  slide.addShape(pptx.ShapeType.rect, { x: ptToIn(583), y: ptToIn(22), w: ptToIn(16), h: ptToIn(9), fill: { color: colors.GT }, line: { color: colors.GT } });
  addText(slide, "GT receptor", 607, 15, 128, 27, 15);
  slide.addShape(pptx.ShapeType.rect, { x: ptToIn(739), y: ptToIn(22), w: ptToIn(16), h: ptToIn(9), fill: { color: colors.CA2 }, line: { color: colors.CA2 } });
  addText(slide, "CryoAtom2 receptor", 763, 15, 182, 27, 15);
  const positions = [192, 377, 602, 787];
  const modelLabels = ["Official", "local_cov", "Official", "local_cov"];
  positions.forEach((x, index) => {
    addLine(slide, x, bottom, x, bottom + 6, colors.ink, 0.8);
    addText(slide, modelLabels[index], x - 60, bottom + 14, 120, 30, 17, { align: "center" });
  });
  for (const [protocolIndex, protocol] of ["C0", "E"].entries()) {
    for (const [modelIndex, model] of ["official", "local_cov"].entries()) {
      const x = positions[protocolIndex * 2 + modelIndex];
      for (const [receptor, offset] of [["GT", -27], ["CA2", 27]]) {
        addDistribution(slide, full.get(`${model}/${receptor}/${protocol}`), field, x + offset, colors[receptor], mapY);
      }
    }
  }
  return slide;
}

function addHeadToHead() {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addNotes(legends[2]);
  const panels = [
    { left: 90, right: 481, centers: [158, 286, 414], letter: "a", title: "Top-1", field: "top1" },
    { left: 557, right: 948, centers: [625, 753, 881], letter: "b", title: "Best of 50", field: "best" },
  ];
  for (const panel of panels) {
    const top = 100;
    const bottom = 402;
    const mapY = addAxis(slide, panel.left, top, panel.right, bottom, 0.2, 30, [0.2, 0.5, 1, 2, 5, 10, 20], panel.letter === "a");
    addText(slide, panel.letter, panel.left - 40, 47, 28, 30, 20, { bold: true });
    addText(slide, panel.title, panel.left + 2, 47, 145, 30, 18);
    const rows = [
      [...full.get("local_cov/GT/C0")].filter(row => subset.has(`${row.pdb_id}/${row.occurrence_id}`)),
      [...full.get("local_cov/CA2/C0")].filter(row => subset.has(`${row.pdb_id}/${row.occurrence_id}`)),
      data.build.filter(row => subset.has(`${row.pdb_id}/${row.occurrence_id}`)),
    ];
    const palette = [colors.GT, colors.CA2, colors.Build];
    const labels = ["local_cov-C\nGT", "local_cov-C\nCryoAtom2", "Emap2lig-\nBuild"];
    panel.centers.forEach((x, index) => {
      addDistribution(slide, rows[index], panel.field, x, palette[index], mapY);
      addLine(slide, x, bottom, x, bottom + 6, colors.ink, 0.8);
      addText(slide, labels[index], x - 61, bottom + 13, 122, 57, 15, { align: "center" });
    });
  }
  addText(slide, "Ligand heavy-atom RMSD (Å)", 8, 159, 37, 242, 17, { vertical: true, align: "center" });
  return slide;
}

addFullFigure("top1", legends[0], "stage3_top1_full");
addFullFigure("best", legends[1], "stage3_best_full");
addHeadToHead();
await fs.mkdir(buildDir, { recursive: true });
await pptx.writeFile({ fileName: output });
console.log(output);
