/** 将六张已核对的 Python 结果图装入论文 PPT，并以页备注保存图注。 */

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/15919/Desktop/论文草稿";
const skillDir = "C:/Users/15919/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const imageDir = path.join(workspaceDir, "画图/formal/stage2");
const buildDir = path.join(workspaceDir, "temp/stage2-deck-build");
const finalPath = path.join(buildDir, "final/stage2_results.pptx");

const figures = [
  {
    name: "stage2-radar-real", file: "stage2_radar_real.png",
    caption: "图4 | 真实受体条件下的 Match 模型变体比较。六轴依次显示冻结 validation 阈值下的前景 F1、总体及小分子、糖、金属离子、肽类的 SMILES 匹配准确率。四个 Matcher 变体使用完整 held_out_test_0 中的 selected 候选；身份准确率仅以真实前景且身份受支持的候选为分母。肽类只有一个样本。EMERALD-ID 的菱形仅表示另一组小分子已知位点的 Top-1 准确率，不连成六轴轮廓。雷达径向刻度从 30% 起。",
  },
  {
    name: "stage2-radar-cryo", file: "stage2_radar_cryo.png",
    caption: "图5 | CryoAtom2 受体条件下的 Match 模型变体比较。六轴与图4定义相同，使用相同的 179 个测试 PDB，但候选由 CryoAtom2 受体条件下的 Find 推理产生。肽类身份只有一个支持样本。EMERALD-ID 的单个菱形表示小分子已知位点准确率，不代表其他类别或前景检测。径向刻度从 30% 起。",
  },
  {
    name: "stage2-strongest-real", file: "stage2_strongest_categories_real.png",
    caption: "图6 | strongest-1 在真实受体条件下的身份匹配准确率随候选身份数变化。横轴是每个 PDB 提供给 Matcher 的精确 SMILES 去重数，5 个及以上合并；纵轴为完整测试集中 selected、真实前景且身份受支持候选的类别内准确率。图例中的 n 是各类别的候选支持数。肽类仅有一个位于单身份 PDB 的样本，因此不形成连续曲线。",
  },
  {
    name: "stage2-strongest-cryo", file: "stage2_strongest_categories_cryo.png",
    caption: "图7 | strongest-1 在 CryoAtom2 受体条件下的分层身份匹配。横轴是 PDB 内实际提供给 Matcher 的精确 SMILES 去重数，纵轴为相应类别的正确数除以身份受支持的 selected 真前景候选数。5 个及以上身份合并，图例标出每类总支持数；肽类仅有一个样本。",
  },
  {
    name: "stage2-known-site-real", file: "stage2_known_site_real.png",
    caption: "图8 | 真实受体条件下 density_only-106 与官方 EMERALD-ID 的小分子已知位点比较。冻结的 84 个 PDB 包含 357 个 occurrence 位点；横轴是各 PDB 的小分子精确 SMILES 去重数，刻度下方给出固定查询点数。实线以该组所有查询点为分母，准备或评分失败仍计入分母；虚线仅以至少有一个候选 SMILES 取得分数的查询点为分母。部分身份失败时，仍按其余有效分数选择身份。Matcher 每个位点均有分数，故两条蓝线数值重合。",
  },
  {
    name: "stage2-known-site-cryo", file: "stage2_known_site_cryo.png",
    caption: "图9 | CryoAtom2 受体条件下的小分子已知位点身份比较。使用与图8完全相同的 84 个 PDB、357 个真实位置和每个 PDB 的小分子候选 SMILES 集合，只改变受体条件。实线保留全部查询点；虚线只统计至少一个身份有分数的位点。两种方法均采用同一位点的 Top-1 精确 SMILES 命中口径，刻度下方标出各组固定支持数。",
  },
];

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
presentation.comments.setSelf({ displayName: "Manuscript figure", initials: "MF" });

for (const item of figures) {
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  const bytes = new Uint8Array(await fs.readFile(path.join(imageDir, item.file)));
  slide.images.add({
    blob: bytes, contentType: "image/png", fit: "contain",
    position: { left: 24, top: 14, width: 1232, height: 692 },
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
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000"],
  fontPolicy: { basis: "design", families: ["Arial", "Helvetica"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "validation.json"),
});
console.log(finalPath);
