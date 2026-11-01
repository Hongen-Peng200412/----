"""以原生 ChimeraX 命令渲染两例实际小分子输出, 再等比装配五面板论文图.

prepare 写每面板 CXC, 冻结连接清单及批处理入口; assemble 读取同次原生 PNG 生成 180x170 mm 的 PDF/PNG/SVG 和可编辑 PPT 布局.
本模块不调用模型、参考 RMSD 或完成度计算; 所有数值来自 scene.json 中原样保留的既有记录. 新构象没有合法 RMSD 时仅以棕色显示.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '论文草稿.md').is_file())
IDENTIFIER = 'full-pipeline-small-molecule-cases'
PANELS = [('a', '11jb', None), ('b', '11jb', 16), ('c', '9bjj', None), ('d', '9bjj', 4), ('e', '9bjj', 16)]
POSITIONS_MM = {'a': [3, 18, 85, 65], 'b': [92, 18, 85, 39], 'c': [3, 94, 85, 65], 'd': [92, 69, 85, 39], 'e': [92, 120, 85, 39]}


def main():
    """从显式原生材料和冻结记录生成命令或联图, 所有中间产物均写本次 build-root.

    CLI 输入参数:
        - step: str, prepare 写原生命令, assemble 检查本次实际显隐后组装图片和文字.
        - data-root: Path, 含 11jb/scene.json, 9bjj/scene.json 及官方 load.cxc 的长期材料根.
        - build-root: Path, 本次可清空的构建目录; prepare 拒绝其中已有五面板原生 PNG.
        - frozen-root: Path | None, 含 scenes.json 的冻结输入根; 正式重建据此核对候选, 预算, sample_index, sdf_index 和原 RMSD.
    写出文件:
        - panels.json: list[dict], 五面板的 label, pdb, occurrence_id, 原 pose 连接, 预算, 允许及实际显示 blob, 毫米位置和标尺长度.
        - scenes.json: dict[str, dict], 11jb/9bjj 的完整场景记录副本, 保留候选, 参考, 原排名与 RMSD.
        - render_all.cxc, render_all.py 和逐面板 CXC: 官方命令及其逐条提交包装器, 不修改输入原子或密度.
        - native_display_validation.json: list[dict], 每面板原生可见 pose/blob 集合及固定显示条件的核对结果.
        - presentation_data.json: dict, 180x170 mm 的 panels, texts, 双语 caption 和稳定图名.
        - full-pipeline-small-molecule-cases.pdf/svg/png/tiff, caption.md 和 alignment.json: 当前联图, 双语图注及最终渲染几何记录.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step', choices=('prepare', 'assemble'))
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--build-root', type=Path, required=True)
    parser.add_argument('--frozen-root', type=Path)
    args = parser.parse_args()
    build = args.build_root.resolve()
    build.mkdir(parents=True, exist_ok=True)
    if args.step == 'prepare':
        if any((build / f'{label}_{pdb}.png').exists() for label, pdb, _ in PANELS):
            raise FileExistsError('本次 prepare 需要新的构建目录, 防止读取上次原生导图')
        live = {p: json.loads((args.data_root / p / 'scene.json').read_text(encoding='utf-8')) for p in ('11jb', '9bjj')}
        scenes = json.loads((args.frozen_root / 'scenes.json').read_text(encoding='utf-8')) if args.frozen_root else live
        for pdb, frozen in scenes.items():
            if frozen['counts'] != live[pdb]['counts'] or frozen['domains']['CA2']['candidates'] != live[pdb]['domains']['CA2']['candidates']:
                raise ValueError(f'{pdb}: 长期材料的候选或预算字段与冻结输入不符')
            current_models = {m['key']: m for m in live[pdb]['models']}
            for model in frozen['models']:
                if model['kind'] == 'pose' and any(model.get(k) != current_models[model['key']].get(k) for k in ('id', 'sample_index', 'sdf_index', 'rmsd_A')):
                    raise ValueError(f'{pdb}/{model["key"]}: 原姿态连接与冻结输入不符')
        if any(not any(r.get('actual_build') is not None for r in s['domains']['CA2']['candidates']) for s in scenes.values()):
            raise ValueError('正式图必须读取已接入 actual_build 的新场景, 不能以旧构象图代替')
        records, batch = [], []
        previous_pdb = None
        for label, pdb, oid in PANELS:
            scene = scenes[pdb]
            budget = scene['counts']['eligible']
            allowed = {r['source_blob_index'] for r in scene['domains']['CA2']['candidates'] if r['before']['pipeline'] < budget}
            small_smiles = {i['smiles'] for i in scene['identities'] if i['type_tag'] == 'small_molecule'}
            shown_blobs = {r['source_blob_index'] for r in scene['domains']['CA2']['candidates'] if r['source_blob_index'] in allowed and r['predicted_smiles'] in small_smiles}
            poses = [m for m in scene['models'] if m['kind'] == 'pose' and m['domain'] == 'CA2' and 'pipeline' in m['views'] and 'top1' in m.get('pose_modes', [m['pose']]) and m['blob'] in allowed]
            local = None
            if oid is not None:
                occurrence = next(o for o in scene['occurrences'] if o['candidate_id'] == oid)
                matching = {r['source_blob_index'] for r in scene['domains']['CA2']['candidates'] if r['matched_occurrence_id'] == oid}
                local = next(m for m in poses if m['blob'] in matching and m['rmsd_A'] is not None)
            commands = [f'open "{(args.data_root / pdb / "load.cxc").resolve().as_posix()}"', '2dlabels delete all', 'camera ortho', 'set bgColor white', 'lighting soft', 'lighting depthCue false', 'graphics silhouettes false', 'ligwork view pipeline', 'ligwork condition CA2', 'ligwork budget 100', 'ligwork filter all', 'ligwork pose top1', 'ligwork labels identity off', 'ligwork labels correctness off', 'ligwork reset', 'hide #1 models', 'show #1.2 models', 'hide #1 atoms', 'cartoon #1.2', 'color #1.2 #b9c1cb', 'transparency #1.2 20 target c', 'hide #2 models', 'hide #!4 models', 'show #3 models', 'style #3 stick', 'size #3 stickRadius 0.18', 'color #3 #e69f00']
            for occurrence_record in scene['occurrences']:
                if occurrence_record['type_tag'] != 'small_molecule':
                    commands.append(f'hide #3.{occurrence_record["candidate_id"] + 1} models')
            # 同色模型合并为一个官方 atomspec, 避免大复合物逐条着色时反复刷新.
            for has_reference, color in [(True, '#009e73'), (False, '#b56b47')]:
                selected = '|'.join('#' + m['id'] for m in poses if (m['rmsd_A'] is not None) == has_reference)
                if selected:
                    commands += [f'color {selected} {color}', f'size {selected} stickRadius 0.19']
            for correct, color in [(True, '#009e73'), (False, '#b56b47')]:
                selected = '|'.join(f'#10.{candidate["source_blob_index"] + 1}' for candidate in scene['domains']['CA2']['candidates'] if candidate['identity_correct'] == correct)
                if selected:
                    commands.append(f'color {selected} {color}')
            hidden = '|'.join(f'#10.{candidate["source_blob_index"] + 1}' for candidate in scene['domains']['CA2']['candidates'] if candidate['source_blob_index'] not in shown_blobs)
            if hidden:
                commands.append(f'hide {hidden} models')
            commands += ['transparency #10 90 target s', 'volume unzone #2.1', 'volume #2.1 region all']
            width, height, scale_A = 1700, 1300, (100 if pdb == '11jb' else 50)
            if oid is None:
                commands += [f'windowsize {width} {height}', 'wait 1', 'view', 'zoom 0.96']
                for local_label, local_oid in ([('b', 16)] if pdb == '11jb' else [('d', 4), ('e', 16)]):
                    offset = 15 if pdb == '11jb' else 4
                    commands.append(f'label #3.{local_oid+1} residues text "{local_label}" height fixed size 32 color #222222 offset 0,{offset},0 onTop true')
                if pdb == '9bjj' and 10 in shown_blobs:
                    background = next(r for r in scene['domains']['CA2']['candidates'] if r['source_blob_index'] == 10)
                    if background['foreground_target']:
                        raise ValueError('9BJJ blob 10 的冻结背景标签发生变化')
                    commands += ['show #41.11 models', 'label #41.11 atoms text "Background" height fixed size 28 color #7a4c34 offset 0,-30,0']
                heading = f'{pdb.upper()} | {scene["counts"]["small"]} deposited small molecules'
            else:
                width, height, scale_A = 1700, 780, 5
                commands += ['label delete #3', 'hide #10|#11|#20|#21 models', 'hide #3 models', f'show #3.{oid+1} models', f'show #{local["id"]} models', f'windowsize {width} {height}', 'wait 1', f'ligwork pocket {oid}', 'color #1.2 #c0c5cb', 'size #1.2 stickRadius 0.07', f'color #3.{oid+1} #e69f00', f'size #3.{oid+1} stickRadius 0.14', f'color #{local["id"]} #009e73', f'size #{local["id"]} stickRadius 0.18', f'volume #2.1 level {scene["contour"]:.10g}', 'volume #2.1 meshLighting false', 'color #2.1 #596773', 'transparency #2.1 0 target s', 'turn y 20', 'turn x -15', 'zoom 0.68']
                heading = f'{occurrence["display_name"]} ({occurrence["site"]}) | RMSD {local["rmsd_A"]:.2f} Å'
            image = build / f'{label}_{pdb}.png'
            cxc = build / f'{label}_{pdb}.cxc'
            scale_y, text_y = (0.055, 0.085) if oid is None else (0.25, 0.28)
            commands += ['scalebar delete', f'scalebar {scale_A} thickness 7 xpos 0.07 ypos {scale_y} color black', f'2dlabels create scale text "{scale_A} Å" xpos 0.07 ypos {text_y} size 28 color black', 'wait 1', f'save "{image.as_posix()}" width {width} height {height} supersample 2', f'ligwork status "{(build / (label + "_status.json")).as_posix()}"', 'view matrix', 'camera', 'zoom', 'windowsize', f'log save "{(build / (label + "_commands.html")).as_posix()}"', f'save "{(build / (label + "_view.cxs")).as_posix()}" includeMaps false']
            cxc.write_text('\n'.join(commands) + '\n', encoding='utf-8')
            # 单面板命令各自可从冷启动重建; 同次总批处理中每例只加载一次, 11JB 仅打开 exp 而延迟两张 sim.
            batch.extend(commands if previous_pdb != pdb else commands[1:])
            previous_pdb = pdb
            records.append({'label': label, 'pdb': pdb, 'occurrence_id': oid, 'heading': heading, 'image': str(image), 'command_file': str(cxc), 'x_mm': POSITIONS_MM[label][0], 'y_mm': POSITIONS_MM[label][1], 'w_mm': POSITIONS_MM[label][2], 'h_mm': POSITIONS_MM[label][3], 'scale_A': scale_A, 'pose': local, 'budget': budget, 'allowed_blobs': sorted(allowed), 'shown_small_molecule_blobs': sorted(shown_blobs), 'displayed_pose_keys': [m['key'] for m in poses] if local is None else [local['key']], 'expected': scene['domains']['CA2']['expected']['pipeline']['100']})
        (build / 'render_all.cxc').write_text('\n'.join(batch) + '\n', encoding='utf-8')
        # Python 包装器只逐条提交同一组官方命令并留证, 不调用分子、地图或图形修改 API.
        wrapper = '''from pathlib import Path
import json, runpy, traceback
from chimerax.core.commands import run
runpy.run_path(SUPPORT)
report = {"passed": False}
def execute(command):
    if command.startswith('open "') and command.endswith('.cxc"'):
        for line in Path(command[6:-1]).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                execute(line)
    else:
        Path(PROGRESS_FILE).write_text(command + "\\n", encoding="utf-8")
        run(session, command, log=True)
try:
    for line in Path(COMMAND_FILE).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            execute(line)
    report["passed"] = True
except Exception:
    report["error"] = traceback.format_exc()
finally:
    run(session, 'log save "' + LOG_FILE + '"', log=True)
    Path(REPORT_FILE).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
'''
        wrapper = wrapper.replace('SUPPORT', repr(str(ROOT / '转换工具/ops/rebuild_support/sitecustomize.py'))).replace('COMMAND_FILE', repr(str(build / 'render_all.cxc'))).replace('LOG_FILE', repr((build / 'chimerax.html').as_posix())).replace('REPORT_FILE', repr(str(build / 'native-completion.json'))).replace('PROGRESS_FILE', repr(str(build / 'native-progress.txt')))
        (build / 'render_all.py').write_text(wrapper, encoding='utf-8')
        (build / 'panels.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        (build / 'scenes.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding='utf-8')
        print('PREPARED_NATIVE_COMMANDS', len(records), flush=True)
        return

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    sys.path.insert(0, str(Path.home() / '.codex/skills/nature-figure/scripts'))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    records = json.loads((build / 'panels.json').read_text(encoding='utf-8'))
    completion = build / 'native-completion.json'
    if completion.exists() and not json.loads(completion.read_text(encoding='utf-8'))['passed']:
        raise RuntimeError('原生命令有错误, 见 native-completion.json')
    native_checks = []
    for record in records:
        if not Path(record['image']).is_file():
            raise FileNotFoundError(record['image'])
        actual = json.loads((build / (record['label'] + '_status.json')).read_text(encoding='utf-8'))
        for key, expected in [('view', 'pipeline'), ('condition', 'CA2'), ('budget', '100'), ('filter', 'all'), ('pose', 'top1')]:
            if actual['config'][key] != expected:
                raise ValueError(f'{record["label"]}: 原生 {key} 与固定条件不符')
        visible = set(actual['visible'])
        visible_poses = {key for key in visible if '_pose_' in key}
        expected_poses = set(record['displayed_pose_keys'])
        visible_blobs = {key for key in visible if '_blob_' in key}
        expected_blobs = {f'CA2_blob_{bid}' for bid in record['shown_small_molecule_blobs']} if record['occurrence_id'] is None else set()
        if visible_poses != expected_poses or visible_blobs != expected_blobs:
            raise ValueError(f'{record["label"]}: 原生实际显隐与原构象连接不符')
        native_checks.append({'panel': record['label'], 'pose_keys': sorted(visible_poses), 'blob_keys': sorted(visible_blobs), 'passed': True})
    (build / 'native_display_validation.json').write_text(json.dumps(native_checks, ensure_ascii=False, indent=2), encoding='utf-8')
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 7, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    figure = plt.figure(figsize=(7.086614173228347, 6.692913385826772), facecolor='white')
    axes, texts = [], []
    for r in records:
        x, y, w, h = r['x_mm'], r['y_mm'], r['w_mm'], r['h_mm']
        ax = figure.add_axes([x/180, 1-(y+h)/170, w/180, h/170], label=r['label'])
        ax.imshow(mpimg.imread(r['image']), interpolation='none', aspect='auto')
        ax.set_axis_off()
        ax.text(0, 1 + 1.5/h, r['label'], transform=ax.transAxes, fontsize=8, weight='bold', va='bottom', ha='left', color='#222222')
        figure.text((x+4)/180, 1-(y-1.5)/170, r['heading'], fontsize=7, weight='bold', ha='left', va='bottom', color='#222222')
        texts.extend([{'text': r['label'], 'x_mm': x, 'y_mm': y-5, 'w_mm': 4, 'h_mm': 3.5, 'size_pt': 8, 'bold': True}, {'text': r['heading'], 'x_mm': x+4, 'y_mm': y-5, 'w_mm': w-4, 'h_mm': 3.5, 'size_pt': 7, 'bold': True}])
        axes.append(ax)
    title = 'Small-molecule modelling in large complexes'
    subtitle = 'CryoAtom2 receptor | 100% attempt budget | Model top-1'
    footer = 'Teal, poses with reference RMSD; brown, poses without reference RMSD; orange, deposited poses.'
    for value, x, y, size, bold in [(title, 3, 2, 9, True), (subtitle, 3, 7, 6.5, False), (footer, 3, 164, 6, False)]:
        figure.text(x/180, 1-y/170, value, fontsize=size, weight='bold' if bold else 'normal', ha='left', va='top', color='#222222')
        texts.append({'text': value, 'x_mm': x, 'y_mm': y, 'w_mm': 174, 'h_mm': 4, 'size_pt': size, 'bold': bold})
    figure.canvas.draw()
    require_matplotlib_panel_alignment(figure, axes=axes, panel_ids=[r['label'] for r in records], row_groups=[], column_groups=[['a','c'],['b','d','e']], require_panel_labels=True, json_out=build / f'{IDENTIFIER}.alignment.json', strict=True)
    figure.savefig(build / f'{IDENTIFIER}.pdf', dpi=400)
    figure.savefig(build / f'{IDENTIFIER}.svg', dpi=400)
    figure.savefig(build / f'{IDENTIFIER}.png', dpi=350)
    figure.savefig(build / f'{IDENTIFIER}.tiff', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    plt.close(figure)
    local = {r['label']: r for r in records if r['pose'] is not None}
    en = ('Small-molecule modelling by the complete LigandSeek workflow in large complexes. a,c, Actual outputs of LigandSeek-Find (Find), LigandSeek-Match (Match) and LigandSeek-Build (Build) in 11JB and 9BJJ, respectively, using CryoAtom2-reconstructed receptors and DG-PocketXMol. The 100% attempt budgets are 78 and 11 charged attempts, respectively; model top-1 poses are shown. The display contains candidates assigned small-molecule identities by Match and their actual outputs, including false-positive regions within the same budgets. Deposited small molecules are orange. Predicted poses with a valid reference heavy-atom root-mean-square deviation (RMSD) are teal; outputs without a reference RMSD are brown. Letters in the overview panels mark the sites shown in the local panels. b,d,e, Corresponding local views of AR6 (f:2001), ATP (B:901) and A1AP0 (E:1001), respectively, with deposited poses, top-1 predictions, experimental cryo-EM density (grey mesh) and receptor residues within 5 Å. Their original top-1 RMSDs are ' + ', '.join(f'{local[k]["pose"]["rmsd_A"]:.2f}' for k in ('b','d','e')) + ' Å, respectively. All poses and RMSDs are in the experimental map coordinate system without rigid-body superposition. Scale bars: a, 100 Å; c, 50 Å; b,d,e, 5 Å.')
    zh = ('LigandSeek完整流程在大复合物中的小分子建模。a、c，分别展示采用CryoAtom2重建受体和DG-PocketXMol时，11JB与9BJJ的LigandSeek-Find（Find）、LigandSeek-Match（Match）和LigandSeek-Build（Build）实际输出。两例沿用100%尝试预算，分别为78次和11次计费尝试，构象采用模型首选结果。显示Match指派为小分子的候选及其实际输出，包括同一预算内的假阳性区域。橙色为沉积小分子，青绿色为具有既有合法参考重原子RMSD的预测构象，棕色为无合法参考RMSD的新增实际预测构象。全景中的字母标出对应局部位点。b、d、e，分别为AR6（f:2001）、ATP（B:901）和A1AP0（E:1001）的对应局部，展示沉积构象、首选预测构象、实验冷冻电镜密度（灰色网格）及5 Å内受体残基。原首选构象RMSD依次为' + '、'.join(f'{local[k]["pose"]["rmsd_A"]:.2f}' for k in ('b','d','e')) + ' Å。构象与RMSD均沿实验密度图坐标系，不作刚体叠合。比例尺：a，100 Å；c，50 Å；b、d、e，5 Å。')
    page = {'id': IDENTIFIER, 'width_mm': 180, 'height_mm': 170, 'panels': records, 'texts': texts, 'caption_en': en, 'caption_zh': zh}
    (build / 'presentation_data.json').write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding='utf-8')
    (build / f'{IDENTIFIER}.caption.md').write_text(zh + '\n\nENGLISH:\n' + en + '\n', encoding='utf-8')
    print('ASSEMBLED_ACTUAL_CASES', IDENTIFIER, flush=True)


if __name__ == '__main__':
    main()

