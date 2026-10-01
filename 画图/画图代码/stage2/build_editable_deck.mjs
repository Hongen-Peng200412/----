/** 从冻结计数建立 PowerPoint 原生线条、标记和文字, 并保存两幅图的页备注。 */

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import pptxgen from "pptxgenjs";

const workspaceDir = "C:/Users/15919/Desktop/论文草稿";
const skillDir = "C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const buildDir = path.join(workspaceDir, "temp/stage2-deck-build");
const data = JSON.parse(await fs.readFile(path.join(workspaceDir, "画图/画图代码/stage2/data.json"), "utf8"));
const colors = {
  "strongest-1": "#BE493B", "density_only-106": "#265B8A",
  "density_only-0": "#438D79", "pocket_only-0": "#8A6D9B",
  "EMERALD-ID": "#B46932", small: "#265B8A",
  sugar: "#8A6D9B", metal: "#438D79", peptide: "#B46932",
};
const modelNames = [
  ["strongest-1", "strongest"], ["density_only-106", "voxel-only"],
  ["density_only-0", "density-only"], ["pocket_only-0", "pocket-only"],
];
const categoryNames = [
  ["small", "Small molecule"], ["sugar", "Sugar"],
  ["metal", "Metal ion"], ["peptide", "Peptide"],
];
const width = 960;
const height = 850;
const inches = points => points / 72;
const rgb = value => value.replace("#", "");
const captions = [
  "图 4 | 真实受体（a）和 CryoAtom2（b）条件下的前景 F1 与 SMILES 匹配。六轴自顶端顺时针为总体 SMILES、小分子、糖、前景 F1、金属离子和肽类；径向坐标为 20–100%。前景阈值由验证集冻结。真实受体条件有 1,653 个 Find 已选候选，其中身份支持数为总体 1,238 个、小分子 389 个、糖 284 个、金属离子 564 个、肽类 1 个；CryoAtom2 条件有 1,651 个已选候选，其中相应支持数为 1,160、348、277、534 和 1 个。图中四条轮廓按这些支持数计算百分比。菱形表示 EMERALD-ID 在独立小分子真实位点中至少一个身份取得评分后的 Top-1 准确率：真实受体 82.6%（282 个位点），CryoAtom2 84.0%（313 个位点）。",
  "图 5 | PDB 内候选 SMILES 数目与 strongest 的分类准确率。a，真实受体；b，CryoAtom2 受体。真实受体条件下小分子、糖、金属离子和肽类的支持数依次为 389、284、564 和 1 个；CryoAtom2 条件下依次为 348、277、534 和 1 个。横轴为该 PDB 提供给 Match 的精确 SMILES 去重数，五种及以上合并；纵轴为 Find 已选、真实前景且身份受支持候选的类别内准确率，以百分比表示。单身份 PDB 中四类均为 100%；肽类仅有一个候选，故只显示单个数据点。",
];

const artifact = Presentation.create({ slideSize: { width, height } });
artifact.comments.setSelf({ displayName: "Manuscript figure", initials: "MF" });
const powerpoint = new pptxgen();
powerpoint.defineLayout({ name: "STAGE2", width: inches(width), height: inches(height) });
powerpoint.layout = "STAGE2";
powerpoint.author = "Matcher manuscript";

function makeSlide(name, caption) {
  const draft = artifact.slides.add();
  draft.background.fill = "#FFFFFF";
  draft.speakerNotes.textFrame.setText(caption);
  artifact.comments.addThread({ slide: draft }, `@@${name}`);
  const final = powerpoint.addSlide();
  final.background = { color: "FFFFFF" };
  final.addNotes(caption);
  return { draft, final };
}

function line(slide, x1, y1, x2, y2, color, weight) {
  const left = Math.min(x1, x2);
  const top = Math.min(y1, y2);
  const dx = Math.max(Math.abs(x2 - x1), 0.01);
  const dy = Math.max(Math.abs(y2 - y1), 0.01);
  const flipV = (x1 <= x2 ? y2 < y1 : y1 < y2);
  slide.draft.shapes.add({
    geometry: "line", position: { left, top, width: dx, height: dy, verticalFlip: flipV },
    fill: "none", line: { style: "solid", fill: color, width: weight },
  });
  slide.final.addShape(powerpoint.ShapeType.line, {
    x: inches(left), y: inches(top), w: inches(dx), h: inches(dy), flipV,
    line: { color: rgb(color), width: weight },
  });
}

function ellipse(slide, x, y, rx, ry, stroke, weight, fill = null) {
  const box = { left: x - rx, top: y - ry, width: 2 * rx, height: 2 * ry };
  slide.draft.shapes.add({
    geometry: "ellipse", position: box, fill: fill ?? "none",
    line: { style: "solid", fill: stroke, width: weight },
  });
  slide.final.addShape(powerpoint.ShapeType.ellipse, {
    x: inches(box.left), y: inches(box.top), w: inches(box.width), h: inches(box.height),
    fill: fill ? { color: rgb(fill) } : { color: "FFFFFF", transparency: 100 },
    line: { color: rgb(stroke), width: weight },
  });
}

function diamond(slide, x, y, radius, color) {
  const box = { left: x - radius, top: y - radius, width: 2 * radius, height: 2 * radius };
  slide.draft.shapes.add({
    geometry: "diamond", position: box, fill: color,
    line: { style: "solid", fill: "#FFFFFF", width: 1 },
  });
  slide.final.addShape(powerpoint.ShapeType.diamond, {
    x: inches(box.left), y: inches(box.top), w: inches(box.width), h: inches(box.height),
    fill: { color: rgb(color) }, line: { color: "FFFFFF", width: 1 },
  });
}

function text(slide, value, x, y, w, h, options = {}) {
  const fontSize = options.fontSize ?? 15;
  const color = options.color ?? "#26313A";
  const align = options.align ?? "left";
  const draft = slide.draft.shapes.add({
    geometry: "textbox", position: { left: x, top: y, width: w, height: h },
    fill: "none", line: { fill: "none", width: 0 },
  });
  draft.text = value;
  draft.text.style = {
    typeface: "Arial", fontSize, bold: options.bold ?? false,
    color, alignment: align, autoFit: "none",
  };
  slide.final.addText(value, {
    x: inches(x), y: inches(y), w: inches(w), h: inches(h),
    fontFace: "Arial", fontSize, bold: options.bold ?? false,
    color: rgb(color), align, valign: "mid", margin: 0,
    vert: options.vertical ? "vert270" : "horz",
  });
}

function radarPoint(cx, cy, radius, axis) {
  const angle = axis * Math.PI / 3;
  return [cx + radius * Math.sin(angle), cy - radius * Math.cos(angle)];
}

function drawRadarPanel(slide, condition, panel) {
  const cx = 338;
  const cy = panel === 0 ? 220 : 635;
  const radius = 145;
  const title = panel === 0 ? "Real receptor" : "CryoAtom2 receptor";
  text(slide, panel === 0 ? "a" : "b", 28, cy - 205, 20, 26,
    { fontSize: 17, bold: true });
  text(slide, title, 52, cy - 205, 300, 26,
    { fontSize: 18, bold: true });
  const keys = ["overall", "small", "sugar", "f1", "metal", "peptide"];
  const labels = ["Overall SMILES", "Small molecule", "Sugar", "Foreground F1", "Metal ion", "Peptide"];

  for (const tick of [50, 90, 100]) {
    const r = radius * (tick - 20) / 80;
    ellipse(slide, cx, cy, r, r,
      tick === 100 ? "#A3AFB6" : "#DDE3E6", tick === 100 ? 1.2 : 0.8);
    const [x, y] = radarPoint(cx, cy, r, 0.25);
    text(slide, String(tick), x + 3, y - 12, 28, 20,
      { fontSize: 12, color: "#66727D" });
  }
  for (let axis = 0; axis < 6; axis += 1) {
    const [x, y] = radarPoint(cx, cy, radius, axis);
    line(slide, cx, cy, x, y, "#DDE3E6", 0.7);
    const labelRadius = axis === 0 ? radius + 22 : axis === 1 ? radius + 52 : radius + 31;
    const [labelX, labelY] = radarPoint(cx, cy, labelRadius, axis);
    text(slide, labels[axis], labelX - 82, labelY - 11, 164, 22,
      { fontSize: 14, align: "center", color: "#202830" });
  }

  for (const [model] of modelNames) {
    const metrics = data.radar[condition][model];
    const points = keys.map((key, axis) => {
      const score = 100 * metrics[key][0] / metrics[key][1];
      return radarPoint(cx, cy, radius * (score - 20) / 80, axis);
    });
    for (let axis = 0; axis < 6; axis += 1) {
      line(slide, ...points[axis], ...points[(axis + 1) % 6], colors[model], 2.4);
    }
    for (const [x, y] of points) {
      ellipse(slide, x, y, 3.5, 3.5, colors[model], 0.4, colors[model]);
    }
  }
  const scored = data.radar.emerald_small_known_site[condition];
  const score = 100 * scored[0] / scored[1];
  const [markerX, markerY] = radarPoint(cx, cy, radius * (score - 20) / 80, 1);
  diamond(slide, markerX, markerY, 7, colors["EMERALD-ID"]);

  const legendX = 690;
  const legendY = cy - 61;
  [...modelNames, ["EMERALD-ID", "EMERALD-ID"]].forEach(([model, name], index) => {
    const y = legendY + 31 * index;
    if (model === "EMERALD-ID") {
      diamond(slide, legendX + 13, y + 8, 6, colors[model]);
    } else {
      line(slide, legendX, y + 8, legendX + 29, y + 8, colors[model], 2.5);
      ellipse(slide, legendX + 14.5, y + 8, 3.5, 3.5,
        colors[model], 0.3, colors[model]);
    }
    text(slide, name, legendX + 42, y - 3, 205, 24,
      { fontSize: 15, color: "#202830" });
  });
}

function drawCategoryPanel(slide, condition, panel) {
  const top = panel === 0 ? 85 : 490;
  const bottom = top + 267;
  const left = 105;
  const right = 660;
  const title = panel === 0 ? "a  strongest · Real receptor" : "b  strongest · CryoAtom2 receptor";
  text(slide, title, 45, top - 60, 410, 28, { fontSize: 20, bold: true });
  for (let tick = 0; tick <= 100; tick += 20) {
    const y = bottom - (tick / 100) * (bottom - top);
    line(slide, left, y, right, y,
      tick === 0 ? "#26313A" : "#DDE3E6", tick === 0 ? 1.3 : 0.8);
    text(slide, String(tick), left - 49, y - 11, 38, 23,
      { fontSize: 13, align: "right" });
  }
  line(slide, left, top, left, bottom, "#26313A", 1.3);
  text(slide, "SMILES matching accuracy (%)", 17, top + 15, 33, 235,
    { fontSize: 14, align: "center", vertical: true });

  const xPositions = [135, 258, 381, 504, 627];
  xPositions.forEach((x, index) => {
    line(slide, x, bottom, x, bottom + 7, "#26313A", 1);
    text(slide, index === 4 ? "≥5" : String(index + 1), x - 23, bottom + 11, 46, 22,
      { fontSize: 14, align: "center" });
  });
  if (panel === 1) {
    text(slide, "Candidate SMILES per PDB", 235, bottom + 55, 280, 28,
      { fontSize: 15, align: "center" });
  }

  for (const [category] of categoryNames) {
    const counts = data.strongest_by_candidate_smiles_count[condition][category];
    const points = counts.map(([correct, support], index) => support === 0
      ? null : [xPositions[index], bottom - (correct / support) * (bottom - top)]);
    for (let index = 0; index < 4; index += 1) {
      if (points[index] && points[index + 1]) {
        line(slide, ...points[index], ...points[index + 1], colors[category], 2.5);
      }
    }
    for (const point of points) {
      if (point) {
        ellipse(slide, point[0], point[1], 4, 4,
          colors[category], 0.3, colors[category]);
      }
    }
  }
  const legendX = 706;
  const legendY = top + 83;
  categoryNames.forEach(([category, name], index) => {
    const y = legendY + 31 * index;
    line(slide, legendX, y + 8, legendX + 29, y + 8, colors[category], 2.5);
    ellipse(slide, legendX + 14.5, y + 8, 4, 4,
      colors[category], 0.3, colors[category]);
    text(slide, name, legendX + 42, y - 3, 208, 24,
      { fontSize: 15, color: "#202830" });
  });
}

const radarSlide = makeSlide("stage2-radar-pair", captions[0]);
drawRadarPanel(radarSlide, "real", 0);
drawRadarPanel(radarSlide, "cryo", 1);
const categorySlide = makeSlide("stage2-strongest-pair", captions[1]);
drawCategoryPanel(categorySlide, "real", 0);
drawCategoryPanel(categorySlide, "cryo", 1);

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(path.join(buildDir, "final"), { recursive: true });
const candidatePath = path.join(buildDir, "candidate_editable_v6.pptx");
const artifactPath = path.join(buildDir, "final/stage2_editable_artifact_v6.pptx");
await (await PresentationFile.exportPptx(artifact)).save(candidatePath);
const { finalizePresentation } = await import(pathToFileURL(
  path.join(skillDir, "container_tools/artifact_tool_utils.mjs"),
).href);
await finalizePresentation({
  workspaceDir, candidatePath, finalPath: artifactPath,
  explicitTotalSlideCount: 2,
  requiredNativeTableOwnerSlides: [], requiredNativeChartOwnerSlides: [],
  pythonExecutable: "C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "9144000,8096250"],
  fontPolicy: { basis: "design", families: ["Arial"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "validation_editable_v6.json"),
});
const nativePath = path.join(buildDir, "stage2_editable_powerpoint_v6.pptx");
await powerpoint.writeFile({ fileName: nativePath });
console.log(nativePath);
