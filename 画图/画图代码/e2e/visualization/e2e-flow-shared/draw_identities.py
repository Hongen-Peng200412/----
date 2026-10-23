"""为端到端流程 v2 的横向 Match 卡片绘制完整预测身份列表的 RDKit 二维化学图.

主要入口为 draw_identities. 此脚本仅读取旧例子的 data.json 和 source/<pdb>/occurrences.jsonl, 不改变预测、排序或科学推理.
运行时需把已安装 RDKit 的目录放入 PYTHONPATH; 本任务使用 temp/e2e_flow_20261003/rdkit_deps 与 bundled Python 3.12.
命令示例: python draw_identities.py --source-root 画图/画图代码/e2e/output/e2e-flow/source --output-root 画图/画图代码/e2e/output/e2e-flow/display/regenerated
二维坐标只由精确 SMILES 生成. 在确定性候选布局中选择适合横向卡片的朝向, 不读取 GT、预测 SDF 或三维坐标.
相同精确 SMILES 使用同一布局缓存, 因此 9BJJ 与 30GA 的 ATP 使用完全相同的绘图坐标和图形.

落盘文件:
    - <output_root>/<pdb>/identities/identity_XX.svg: 1600 x 720 的透明矢量化学图, XX 是原 identity_smiles 中从零开始的下标.
    - <output_root>/<pdb>/identities/identity_XX.png: 与 SVG 相同画布的透明 PNG, 作为 PPT 兼容备用图.
    - <output_root>/<pdb>/identities/identity_XX_white.svg: 与透明 SVG 同图同尺寸的白底版本.
    - <output_root>/<pdb>/identities/identity_XX_white.png: 与白底 SVG 相同画布的 PNG.
    - <output_root>/<pdb>/identities/identity_manifest.json: dict, 包含 pdb、exact_predicted_smiles、matched_identity_indices、identity_count、image_size_px、rdkit_version、identities.
        - identities: list[dict], 与 prediction.identity_smiles 保持同样顺序, 包括所有 eligible=False 身份.
        - identities[*].identity_index: int, 0-based 原始身份下标, 例如 index=2 对应 prediction.identity_smiles[2].
        - identities[*].smiles: str, 未经规范化或删氢的精确输入字符串.
        - identities[*].eligible: bool, prediction.small_molecule_answer_mask 同下标的值, False 身份以灰色绘制.
        - identities[*].matched: bool, 是否与 prediction.predicted_smiles_small_molecule 逐字符相等, 不依据真值或姿态 RMSD 选择.
        - identities[*].ccd_label: str | None, 仅在源资产中通过精确 SMILES 与 occurrence_id 关联获得的 CCD 标签, 未知为 None.
        - identities[*].display_label: str, 可用 CCD 标签或 Identity1 这类按原列表编号的中性名称.
        - identities[*].content_bbox_px: list[int], 透明 PNG 中实际化学图的 [left, top, right, bottom] 像素范围, 可供 PPT 设置留白与缩放.
        - identities[*].layout_2d: dict, generator、rotation_degrees、normalized_extent_xy、nominal_card_aspect、atom_font_size_px 与文字相交核查; 仅描述二维绘图坐标布局, 没有物理单位或三维姿态含义.
        - identities[*].card_legibility: dict, 按 1580 pixel 总卡片宽、28 pixel 间距和 220 pixel 绘制区高估计的可见文字尺寸, 用于主代理安排图片大小.
        - identities[*].chemical_graph: dict, 显式氢移除、元素/电荷/同位素/键/手性与无新增立体化学的核查结果.
        - identities[*].paths: dict[str, str], transparent_svg、transparent_png、white_svg、white_png 的绝对路径.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from xml.etree import ElementTree

import numpy as np
from PIL import Image
from rdkit import Chem, rdBase
from rdkit.Chem import rdCoordGen, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D


ATOM_FONT_SIZE_PX = 76


def label_overlap_count(molecule: Chem.Mol, atom_font_size_px: int) -> int:
    """按最终 RDKit 字号绘制一次内存 SVG, 统计不同原子文字边界的相交数.

    输入参数:
        - molecule: RDKit Mol, 已附纯二维坐标的布局候选.
        - atom_font_size_px: int, 与最终 SVG/PNG 相同的元素文字字号.

    返回值:
        - count: int, 不同 atom-N 标签包围框同时在 X/Y 方向相交的原子对数; 同一原子的 O/H 或形式电荷字形合并计算.

    SVG 只用于内存中的布局选择. 不写文件, 不修改分子, 不改变元素或化学键.
    """
    drawer = rdMolDraw2D.MolDraw2DSVG(1600, 720)
    options = drawer.drawOptions()
    options.prepareMolsBeforeDrawing = False
    options.clearBackground = False
    options.padding = 0.06
    options.fixedBondLength = 90
    options.fixedFontSize = atom_font_size_px
    options.maxFontSize = 96
    options.addStereoAnnotation = False
    options.unspecifiedStereoIsUnknown = False
    drawer.DrawMolecule(molecule)
    drawer.FinishDrawing()
    labels = {}
    for node in ElementTree.fromstring(drawer.GetDrawingText()).iter():
        atom_class = node.get("class", "")
        if re.fullmatch(r"atom-\d+", atom_class) is None:
            continue
        points = np.asarray([float(value) for value in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", node.get("d", ""))]).reshape(-1, 2)
        if len(points):
            box = np.concatenate((points.min(axis=0), points.max(axis=0)))
            if atom_class in labels:
                box[:2] = np.minimum(labels[atom_class][:2], box[:2])
                box[2:] = np.maximum(labels[atom_class][2:], box[2:])
            labels[atom_class] = box
    boxes = list(labels.values())
    count = 0
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            if min(first[2], second[2]) > max(first[0], second[0]) and min(first[3], second[3]) > max(first[1], second[1]):
                count += 1
    return count


def horizontal_layout(molecule: Chem.Mol, card_width_px: float) -> tuple[Chem.Mol, dict]:
    """仅在二维显示空间选择确定性布局和旋转, 减少横向卡片中的内部留白.

    输入参数:
        - molecule: RDKit Mol, 标准 RemoveHs 后的精确身份化学图, 不含来源三维构象.
        - card_width_px: float, 同一精确 SMILES 在全部例子中最窄卡片的宽度, 由 1580 pixel 总宽与原身份数确定.

    返回值:
        - molecule: RDKit Mol, 与输入化学图相同的副本, 附一个二维 conformer.
        - layout: dict, generator 为 CoordGen 或 RDKit 二维生成器及其采样种子, rotation_degrees 为刚体二维旋转角, normalized_extent_xy 为无物理单位的绘图范围, nominal_card_aspect 为卡片内部绘制区宽高比, atom_font_size_px 为不产生文字相交的最大候选字号.

    对含金属配位的分子只使用 CoordGen, 保留其展开宏环的清楚布局. 对其它分子比较 CoordGen 与 RDKit 的确定性二维候选.
    全部候选按中位键长统一绘图单位; 二维旋转行列式为 +1, 不反射分子或改变已声明手性.
    P 与非环 O/S 之间的显示键长增至 2.2 个绘图单位, 并平移整条支链, 给磷酸基元素文字留空间.
    """
    candidates = []
    coordgen = Chem.Mol(molecule)
    rdCoordGen.AddCoords(coordgen)
    candidates.append(("CoordGen", coordgen))
    if all(atom.GetAtomicNum() in {1, 6, 7, 8, 9, 15, 16, 17, 35, 53} for atom in molecule.GetAtoms()):
        for seed, samples in ((0, 0), (0, 80), (17, 80), (31, 80)):
            candidate = Chem.Mol(molecule)
            rdDepictor.Compute2DCoords(candidate, canonOrient=False, clearConfs=True, nFlipsPerSample=3 if samples else 0, nSample=samples, sampleSeed=seed, permuteDeg4Nodes=True, bondLength=1.5, forceRDKit=True, useRingTemplates=True)
            candidates.append((f"RDKit_seed{seed}_samples{samples}", candidate))

    layouts = []
    for generator, candidate in candidates:
        # (N_atom, 2), 纯二维绘图坐标, 轴序 XY; 键长归一化只控制展示大小, 没有 Å 单位.
        points = np.asarray(candidate.GetConformer().GetPositions(), dtype=np.float64)[:, :2]
        lengths = [np.linalg.norm(points[bond.GetBeginAtomIdx()] - points[bond.GetEndAtomIdx()]) for bond in candidate.GetBonds()]
        if lengths:
            points = points * (1.5 / np.median(lengths))
        # 含 P 的非环 O/S 键仅在绘图空间加长, 给 OH 与形式电荷留空间; 整个相连支链平移, 不改变其内部键或环.
        for atom in candidate.GetAtoms():
            if atom.GetAtomicNum() != 15:
                continue
            phosphorus_index = atom.GetIdx()
            for bond in atom.GetBonds():
                neighbor = bond.GetOtherAtom(atom)
                if bond.IsInRing() or neighbor.GetAtomicNum() not in {8, 16}:
                    continue
                neighbor_index = neighbor.GetIdx()
                vector = points[neighbor_index] - points[phosphorus_index]
                translation = vector * (2.2 / np.linalg.norm(vector) - 1)
                branch = set()
                pending = [neighbor_index]
                while pending:
                    current = pending.pop()
                    if current == phosphorus_index or current in branch:
                        continue
                    branch.add(current)
                    pending.extend(a.GetIdx() for a in candidate.GetAtomWithIdx(current).GetNeighbors())
                points[list(branch)] += translation
        points = points - points.mean(axis=0, keepdims=True)
        for angle in range(0, 180, 5):
            theta = np.deg2rad(angle)
            rotation = np.asarray([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
            rotated = points @ rotation.T
            extent = np.ptp(rotated, axis=0)
            # 每边加同样的原子文字空间, 优先放大可读键长, 而不是拉伸 SVG 或删除化学内容.
            score = min((card_width_px - 30) / (extent[0] + 2.6), 220 / (extent[1] + 2.6))
            layouts.append((score, generator, angle, candidate, rotated, extent))
    chosen = None
    # 每个字号先查尺寸利用率高的布局; 优先用 76 pixel 字号, 只有所有朝向都相交时才降字号.
    for atom_font_size_px in (76, 74, 72, 70, 68, 64):
        for score, generator, angle, candidate, points, extent in sorted(layouts, key=lambda item: item[0], reverse=True):
            result = Chem.Mol(candidate)
            for atom_index, xy in enumerate(points):
                result.GetConformer().SetAtomPosition(atom_index, (float(xy[0]), float(xy[1]), 0.0))
            overlaps = label_overlap_count(result, atom_font_size_px)
            if overlaps == 0:
                chosen = (generator, angle, result, extent, atom_font_size_px)
                break
        if chosen is not None:
            break
    if chosen is None:
        raise ValueError("二维布局仍有原子文字相交, 停止输出并检查字号或绘图坐标")
    generator, angle, result, extent, atom_font_size_px = chosen
    return result, {"generator": generator, "rotation_degrees": angle, "normalized_extent_xy": extent.tolist(), "nominal_card_aspect": (card_width_px - 30) / 220, "phosphate_display_bond_length": 2.2, "atom_font_size_px": atom_font_size_px, "atom_label_bbox_overlap_count": 0}


def describe_chemical_graph(smiles: str, card_width_px: float) -> tuple[Chem.Mol, dict, dict]:
    """保留精确输入化学信息, 只对展示图执行标准 RemoveHs 并生成二维坐标.

    输入参数:
        - smiles: str, prediction.identity_smiles 中的原始精确字符串, 可含显式 H、形式电荷、同位素和已经声明的立体化学.
        - card_width_px: float, horizontal_layout 使用的最窄身份卡片宽度.

    返回值:
        - drawing_molecule: RDKit Mol, 仅有二维坐标的展示分子; 不从三维姿态推断或补充立体化学.
        - graph: dict, input_atom_count、display_atom_count、heavy_atom_count、removed_display_hydrogens、formal_charge、input_declared_atom_stereo、display_declared_atom_stereo、input_declared_bond_stereo、display_declared_bond_stereo、canonical_isomeric_smiles、remove_hs_roundtrip_isomorphic、drawing_graph_isomorphic、stereo_preserved、no_new_stereo、passed.
            - remove_hs_roundtrip_isomorphic: bool, 对输入和展示图都加全氢后, 比较原子数、键数与双向 useChirality=True 子图匹配.
            - drawing_graph_isomorphic: bool, 生成二维坐标与绘图键方向后, 原子属性、键属性和标准同分异构 SMILES 与 RemoveHs 结果一致.
            - passed: bool, 所有上述核查均成立, 否则停止写图以防产生错误化学图.
        - layout: dict, horizontal_layout 返回的确定性二维布局说明.
    """
    # 保留原输入中的显式 H, 使 source_atom_count 与实际输入精确对应.
    parser = Chem.SmilesParserParams()
    parser.removeHs = False
    source_molecule = Chem.MolFromSmiles(smiles, parser)
    if source_molecule is None:
        raise ValueError(f"RDKit 无法解析精确身份 SMILES: {smiles}")

    display_molecule = Chem.RemoveHs(source_molecule)
    baseline_canonical = Chem.MolToSmiles(display_molecule, canonical=True, isomericSmiles=True)
    source_with_h = Chem.AddHs(source_molecule)
    display_with_h = Chem.AddHs(display_molecule)
    hydrogen_roundtrip = (
        source_with_h.GetNumAtoms() == display_with_h.GetNumAtoms()
        and source_with_h.GetNumBonds() == display_with_h.GetNumBonds()
        and source_with_h.HasSubstructMatch(display_with_h, useChirality=True)
        and display_with_h.HasSubstructMatch(source_with_h, useChirality=True)
    )

    # 原子属性列表与键属性列表保持原始重原子顺序, 可核查绘图准备没有改写元素、形式电荷、键型或声明手性.
    atom_properties = [(a.GetAtomicNum(), a.GetIsotope(), a.GetFormalCharge(), a.GetIsAromatic(), int(a.GetChiralTag()), a.GetTotalNumHs()) for a in display_molecule.GetAtoms()]
    bond_properties = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx(), str(b.GetBondType()), b.GetIsAromatic(), int(b.GetStereo())) for b in display_molecule.GetBonds()]
    display_molecule, layout = horizontal_layout(display_molecule, card_width_px)
    drawing_molecule = rdMolDraw2D.PrepareMolForDrawing(display_molecule, kekulize=False, addChiralHs=False, wedgeBonds=True, forceCoords=False)
    drawing_atoms = [(a.GetAtomicNum(), a.GetIsotope(), a.GetFormalCharge(), a.GetIsAromatic(), int(a.GetChiralTag()), a.GetTotalNumHs()) for a in drawing_molecule.GetAtoms()]
    drawing_bonds = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx(), str(b.GetBondType()), b.GetIsAromatic(), int(b.GetStereo())) for b in drawing_molecule.GetBonds()]
    drawing_canonical = Chem.MolToSmiles(drawing_molecule, canonical=True, isomericSmiles=True)
    drawing_isomorphic = atom_properties == drawing_atoms and bond_properties == drawing_bonds and baseline_canonical == drawing_canonical
    input_atom_stereo = sum(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in source_molecule.GetAtoms())
    display_atom_stereo = sum(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in drawing_molecule.GetAtoms())
    input_bond_stereo = sum(b.GetStereo() not in (Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOANY) for b in source_molecule.GetBonds())
    display_bond_stereo = sum(b.GetStereo() not in (Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOANY) for b in drawing_molecule.GetBonds())
    graph = {
        "input_atom_count": source_molecule.GetNumAtoms(),
        "display_atom_count": drawing_molecule.GetNumAtoms(),
        "heavy_atom_count": drawing_molecule.GetNumHeavyAtoms(),
        "removed_display_hydrogens": source_molecule.GetNumAtoms() - drawing_molecule.GetNumAtoms(),
        "formal_charge": Chem.GetFormalCharge(drawing_molecule),
        "input_declared_atom_stereo": input_atom_stereo,
        "display_declared_atom_stereo": display_atom_stereo,
        "input_declared_bond_stereo": input_bond_stereo,
        "display_declared_bond_stereo": display_bond_stereo,
        "canonical_isomeric_smiles": drawing_canonical,
        "remove_hs_roundtrip_isomorphic": hydrogen_roundtrip,
        "drawing_graph_isomorphic": drawing_isomorphic,
        "stereo_preserved": input_atom_stereo == display_atom_stereo and input_bond_stereo == display_bond_stereo,
        "no_new_stereo": display_atom_stereo <= input_atom_stereo and display_bond_stereo <= input_bond_stereo,
    }
    graph["passed"] = all(graph[k] for k in ("remove_hs_roundtrip_isomorphic", "drawing_graph_isomorphic", "stereo_preserved", "no_new_stereo"))
    if not graph["passed"]:
        raise ValueError(f"展示化学图未通过元素/电荷/键/氢/立体化学核查: {smiles}")
    return drawing_molecule, graph, layout


def draw_identity_assets(molecule: Chem.Mol, eligible: bool, output_dir: Path, identity_index: int, atom_font_size_px: int) -> dict[str, str]:
    """把同一个展示分子写成透明与白底的 SVG/PNG, 不在图内添加身份或匹配结论.

    输入参数:
        - molecule: RDKit Mol, describe_chemical_graph 返回的已核查二维分子.
        - eligible: bool, False 时骨架与所有原子文字使用灰色, 表示不参与 Stage3 身份选择.
        - output_dir: Path, 当前例子的 identities 输出目录.
        - identity_index: int, 原始 identity_smiles 的 0-based 下标.
        - atom_font_size_px: int, 已通过元素文字边界检查的字号, 与布局选择阶段保持一致.

    返回值:
        - paths: dict[str, str], transparent_svg、transparent_png、white_svg、white_png 四个 1600 x 720 资产的绝对路径.
    """
    paths = {}
    for background_name, transparent in (("transparent", True), ("white", False)):
        for extension in ("svg", "png"):
            drawer = rdMolDraw2D.MolDraw2DSVG(1600, 720) if extension == "svg" else rdMolDraw2D.MolDraw2DCairo(1600, 720)
            options = drawer.drawOptions()
            options.prepareMolsBeforeDrawing = False
            options.clearBackground = not transparent
            options.setBackgroundColour((1.0, 1.0, 1.0, 0.0 if transparent else 1.0))
            options.padding = 0.06
            options.bondLineWidth = 3.2
            options.fixedBondLength = 90.0
            options.fixedFontSize = atom_font_size_px
            options.minFontSize = 20
            options.maxFontSize = 96
            options.addStereoAnnotation = False
            options.unspecifiedStereoIsUnknown = False
            options.includeAtomTags = False
            if not eligible:
                options.useBWAtomPalette()
                options.setAtomPalette({a.GetAtomicNum(): (0.62, 0.65, 0.69) for a in molecule.GetAtoms()})
            else:
                # 2D 图采用惯用元素色与黑色碳骨架, 不套用三维方法比较的配色.
                options.useDefaultAtomPalette()
                options.updateAtomPalette({6: (0.08, 0.10, 0.13), 1: (0.08, 0.10, 0.13), 0: (0.08, 0.10, 0.13)})
            drawer.DrawMolecule(molecule)
            drawer.FinishDrawing()
            suffix = "" if transparent else "_white"
            path = output_dir / f"identity_{identity_index:02d}{suffix}.{extension}"
            drawing = drawer.GetDrawingText()
            path.write_text(drawing, encoding="utf-8") if extension == "svg" else path.write_bytes(drawing)
            paths[f"{background_name}_{extension}"] = path.resolve().as_posix()
    return paths


def draw_identities(source_root: Path, output_root: Path) -> list[dict]:
    """依原列表顺序绘制每个例子的所有身份, 并记录精确预测匹配与来源可证的标签.

    输入参数:
        - source_root: Path, 旧 E2E_cases_20261003 目录; 每个 <pdb>/data.json 含 prediction、target_occurrence 与 full_matcher_predictions.
        - output_root: Path, 新 E2E_flow_v2_20261003 目录, 仅写各例的 identities 子目录.

    返回值:
        - summaries: list[dict], 每例 pdb、identity_count、eligible_count、matched_identity_indices、manifest_path 与 all_chemical_graphs_passed.
    """
    summaries = []
    drawing_cache = {}
    sources = [(path, json.loads(path.read_text(encoding="utf-8"))) for path in sorted(source_root.glob("*/data.json"))]
    minimum_card_width_by_smiles = {}
    # 先汇总同一 SMILES 的最窄卡片, 避免 ATP 的布局受两例处理先后顺序影响.
    for _, data in sources:
        smiles_list = data["prediction"]["identity_smiles"]
        card_width = (1580 - 28 * (len(smiles_list) - 1)) / len(smiles_list)
        for smiles in smiles_list:
            minimum_card_width_by_smiles[smiles] = min(minimum_card_width_by_smiles.get(smiles, card_width), card_width)
    for source_path, data in sources:
        pdb = data["case"]["pdb"]
        prediction = data["prediction"]
        # (I,), 同一个身份轴: 精确 SMILES、Stage3 范围布尔掩码与 logit, I 是当前例子的身份数.
        smiles_list = prediction["identity_smiles"]
        eligible_mask = prediction["small_molecule_answer_mask"]
        logits = prediction["identity_logits"]
        exact_predicted_smiles = prediction["predicted_smiles_small_molecule"]
        if not len(smiles_list) == len(eligible_mask) == len(logits):
            raise ValueError(f"{pdb} 的 identity_smiles、answer_mask 与 logits 长度不一致")
        matched_indices = [index for index, smiles in enumerate(smiles_list) if smiles == exact_predicted_smiles]
        if len(matched_indices) != 1:
            raise ValueError(f"{pdb} 的精确预测 SMILES 应对应唯一身份下标, 实际为 {matched_indices}")

        # 标签只利用资产中明确声明的 SMILES→occurrence_id 关系, 例如 9wup 的目标字符串→6→CCD:FMN.
        occurrences_path = source_root / "source" / pdb / "occurrences.jsonl"
        occurrences = [json.loads(line) for line in occurrences_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        occurrence_by_id = {occurrence["candidate_id"]: occurrence for occurrence in occurrences}
        exact_labels = {}
        label_evidence = {}
        label_relations = [(data["handoff"]["target_smiles"], data["handoff"]["matched_occurrence_id"], "handoff.target_smiles")]
        label_relations.extend((item["target_smiles"], item["matched_occurrence_id"], f"full_matcher_predictions[{index}].target_smiles") for index, item in enumerate(data["full_matcher_predictions"]) if item["target_smiles"] is not None and item["matched_occurrence_id"] is not None)
        for smiles, occurrence_id, evidence_field in label_relations:
            occurrence = occurrence_by_id[occurrence_id]
            components = occurrence["components"]
            if occurrence["kind"] == "CCD" and len(components) == 1 and occurrence["object_key"] == f"CCD:{components[0]['ccd_id']}":
                label = components[0]["ccd_id"]
                if smiles in exact_labels and exact_labels[smiles] != label:
                    raise ValueError(f"{pdb} 同一精确 SMILES 出现冲突的 CCD 标签")
                exact_labels[smiles] = label
                label_evidence[smiles] = {"source_field": evidence_field, "occurrence_id": occurrence_id, "object_key": occurrence["object_key"], "occurrences_path": occurrences_path.resolve().as_posix()}

        output_dir = output_root / pdb / "identities"
        output_dir.mkdir(parents=True, exist_ok=True)
        identities = []
        for identity_index, smiles in enumerate(smiles_list):
            if smiles not in drawing_cache:
                drawing_cache[smiles] = describe_chemical_graph(smiles, minimum_card_width_by_smiles[smiles])
            molecule, chemical_graph, layout = drawing_cache[smiles]
            eligible = bool(eligible_mask[identity_index])
            paths = draw_identity_assets(molecule, eligible, output_dir, identity_index, layout["atom_font_size_px"])
            bbox = list(Image.open(paths["transparent_png"]).getbbox())
            card_width = (1580 - 28 * (len(smiles_list) - 1)) / len(smiles_list)
            display_scale = min((card_width - 30) / (bbox[2] - bbox[0] + 40), 220 / (bbox[3] - bbox[1] + 40))
            nominal_font_px = layout["atom_font_size_px"] * display_scale
            identities.append({
                "pdb": pdb,
                "identity_index": identity_index,
                "smiles": smiles,
                "eligible": eligible,
                "matched": smiles == exact_predicted_smiles,
                "identity_logit": logits[identity_index],
                "ccd_label": exact_labels.get(smiles),
                "display_label": exact_labels.get(smiles, f"Identity{identity_index + 1}"),
                "ccd_label_evidence": label_evidence.get(smiles),
                "atom_count": chemical_graph["display_atom_count"],
                "content_bbox_px": bbox,
                "layout_2d": layout,
                "card_legibility": {"card_width_px": card_width, "drawing_height_px": 220, "safe_bbox_padding_px": 20, "display_scale": display_scale, "nominal_atom_font_px": nominal_font_px, "nominal_atom_font_pt_at_183mm_figure_width": nominal_font_px * 183 / 1800 * 72 / 25.4, "nominal_atom_font_pt_at_132mm_figure_width": nominal_font_px * 132 / 1800 * 72 / 25.4, "small_at_publication_size": nominal_font_px * 183 / 1800 * 72 / 25.4 < 6, "single_atom_recommended_display_height_px": 80 if chemical_graph["display_atom_count"] == 1 else None},
                "chemical_graph": chemical_graph,
                "paths": paths,
            })

        manifest = {
            "pdb": pdb,
            "source_data_path": source_path.resolve().as_posix(),
            "exact_predicted_smiles": exact_predicted_smiles,
            "prediction_source_field": "prediction.predicted_smiles_small_molecule",
            "matching_rule": "exact_string_equality_against_prediction.identity_smiles_in_original_order",
            "matched_identity_indices": matched_indices,
            "identity_count": len(identities),
            "image_size_px": [1600, 720],
            "rdkit_version": rdBase.rdkitVersion,
            "drawing_settings": {"canvas_px": [1600, 720], "maximum_atom_font_size_px": ATOM_FONT_SIZE_PX, "maximum_bond_length_px": 90, "all_exact_smiles_share_identical_layout": True},
            "identities": identities,
        }
        manifest_path = output_dir / "identity_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summaries.append({"pdb": pdb, "identity_count": len(identities), "eligible_count": sum(eligible_mask), "matched_identity_indices": matched_indices, "manifest_path": manifest_path.resolve().as_posix(), "all_chemical_graphs_passed": all(item["chemical_graph"]["passed"] for item in identities)})
    return summaries


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description="绘制完整 Match 身份轴的 RDKit 图并核查化学图一致性")
    argument_parser.add_argument("--source-root", type=Path, required=True)
    argument_parser.add_argument("--output-root", type=Path, required=True)
    arguments = argument_parser.parse_args()
    print(json.dumps(draw_identities(arguments.source_root, arguments.output_root), ensure_ascii=False, indent=2))
