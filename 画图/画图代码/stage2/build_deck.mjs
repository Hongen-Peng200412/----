/** 将两张双面板 Stage2 结果图装入论文 PPT，并以页备注保存图注。 */

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/15919/Desktop/论文草稿";
const skillDir = "C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const imageDir = path.join(workspaceDir, "画图/formal/stage2");
const buildDir = path.join(workspaceDir, "temp/stage2-deck-build");
const finalPath = path.join(buildDir, "final/stage2_results_v3.pptx");

const figures = [
  {
    name: "stage2-radar-pair", file: "stage2_radar_pair.png",
    caption: "图 4 | 真实受体（a）和 CryoAtom2（b）条件下的前景 F1 与 SMILES 匹配。六轴为前景 F1、总体及四类身份准确率；前景阈值由验证集冻结。Find 已选候选数为 1,653/1,651；身份支持数依次为总体 1,238/1,160、小分子 389/348、糖 284/277、金属离子 564/534、肽类 1/1（斜杠前后对应 a/b）。菱形仅示 EMERALD-ID 在独立小分子真实位点中至少一个身份取得评分后的 Top-1（233/282、263/313）。径向坐标为 30–100%。",
  },
  {
    name: "stage2-strongest-pair", file: "stage2_strongest_pair.png",
    caption: "图 5 | PDB 内候选 SMILES 数目与 strongest-1 的分类准确率。a，真实受体；b，CryoAtom2 受体。横轴为该 PDB 提供给 Match 的精确 SMILES 去重数，五种及以上合并；纵轴为 Find 已选、真实前景且身份受支持候选的类别内准确率。真实受体条件下，小分子、糖、金属离子和肽类的总支持数分别为 389、284、564 和 1；CryoAtom2 条件下分别为 348、277、534 和 1。单身份 PDB 中四类均为 100%；肽类仅有一个候选，故只显示单个数据点。",
  },
];

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const presentation = Presentation.create({ slideSize: { width: 960, height: 850 } });
presentation.comments.setSelf({ displayName: "Manuscript figure", initials: "MF" });

for (const item of figures) {
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  const bytes = new Uint8Array(await fs.readFile(path.join(imageDir, item.file)));
  slide.images.add({
    blob: bytes, contentType: "image/png", fit: "contain",
    position: { left: 16, top: 12, width: 928, height: 826 },
    alt: item.name,
  });
  slide.speakerNotes.textFrame.setText(item.caption);
  presentation.comments.addThread({ slide }, `@@${item.name}`);
  presentation.comments.addThread(
    { slide },
    `Source: 画图/画图代码/stage2/data.json; plot_stage2.py; ${item.file}`,
  );
}

const { finalizePresentation } = await import(pathToFileURL(
  path.join(skillDir, "container_tools/artifact_tool_utils.mjs"),
).href);
const candidatePath = path.join(buildDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
await finalizePresentation({
  workspaceDir,
  candidatePath,
  finalPath,
  explicitTotalSlideCount: figures.length,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  pythonExecutable: "C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "9144000,8096250"],
  fontPolicy: { basis: "design", families: ["Arial", "Helvetica"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "validation_v3.json"),
});
console.log(finalPath);
