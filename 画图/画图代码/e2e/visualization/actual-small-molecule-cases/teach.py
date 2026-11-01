"""把本次已验收的五组原生命令转为从 initial.cxs 出发的教学与长期会话命令."""

import argparse
import csv
import html
import json
import re
from pathlib import Path


def main():
    """读取同次 panels/scenes/原生命令日志, 写五份教程和对应长期 CXC.

    CLI 的 build-root 包含已完成渲染的 panels.json, scenes.json 及 a-e_commands.html.
    output-root 是长期冻结输入根, teaching-root 是代码旁的教程目录.
    每份教程首行打开本例 initial.cxs, 随后只使用官方命令恢复预算, 显隐, 颜色和相机.
    native/tutorials 保存逐面板 CXC、验证时写出的 CXS/PNG/status/log 及完整逐姿态来源 CSV.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--teaching-root', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, default=Path('D:/AdaLigand_Visualization'))
    args = parser.parse_args()
    output = args.output_root.resolve() / 'native' / 'tutorials'
    output.mkdir(parents=True, exist_ok=True)
    args.teaching_root.mkdir(parents=True, exist_ok=True)
    records = json.loads((args.build_root / 'panels.json').read_text(encoding='utf-8'))
    scenes = json.loads((args.build_root / 'scenes.json').read_text(encoding='utf-8'))
    batch, reopen_batch = [], []
    reopened = output / 'reopened'
    reopened.mkdir(parents=True, exist_ok=True)
    for record in records:
        label, pdb = record['label'], record['pdb']
        source = args.build_root / f'{label}_{pdb}.cxc'
        commands = source.read_text(encoding='utf-8').splitlines()
        commands[0] = f'open "{(args.data_root / pdb / "initial.cxs").as_posix()}"'
        log = html.unescape((args.build_root / f'{label}_commands.html').read_text(encoding='utf-8'))
        matrices = re.findall(r'view matrix camera ([^<#\n]+)', log)
        if not matrices:
            raise ValueError(f'{label}: 原生日志缺少相机矩阵')
        matrix = matrices[-1].strip().rstrip(',')
        fields = re.findall(r'field width: ([0-9.eE+-]+)', log)
        sizes = re.findall(r'window size ([0-9]+) ([0-9]+)', log)
        if not fields or not sizes:
            raise ValueError(f'{label}: 原生日志缺少正交视野宽度或实际窗口尺寸')
        actual_width, actual_height = map(int, sizes[-1])
        pixel_size = float(fields[-1]) / actual_width
        # 原子与密度坐标保持不变, 只恢复官方命令记录的观察相机.
        cut = next(i for i, command in enumerate(commands) if command == 'scalebar delete')
        commands[cut:cut] = [f'windowsize {actual_width} {actual_height}', 'wait 1', 'view matrix camera ' + matrix, f'zoom pixelSize {pixel_size:.12g}']
        (output / f'{label}_camera.json').write_text(json.dumps({'matrix': matrix, 'window_size': [actual_width, actual_height], 'field_width_A': float(fields[-1]), 'pixel_size_A': pixel_size}, indent=2), encoding='utf-8')
        commands = [line.replace(args.build_root.resolve().as_posix(), output.as_posix()) for line in commands]
        (output / f'{label}_{pdb}.cxc').write_text('\n'.join(commands) + '\n', encoding='utf-8')
        batch.extend(commands)
        reopen_batch += [f'open "{(output / (label + "_view.cxs")).as_posix()}"', 'wait 1', f'ligwork status "{(reopened / (label + "_status.json")).as_posix()}"', 'view matrix', 'camera', 'zoom', 'windowsize', f'save "{(reopened / f"{label}_{pdb}.png").as_posix()}" width 1700 height {1300 if record["occurrence_id"] is None else 780} supersample 2', f'log save "{(reopened / (label + "_commands.html")).as_posix()}"']
        scene = scenes[pdb]
        models = {m['key']: m for m in scene['models']}
        used = [models[key] for key in record['displayed_pose_keys']]
        with (args.data_root / pdb / '本例材料来源.csv').open(encoding='utf-8-sig', newline='') as stream:
            originals = {row['original_server_file']: row['local_file'] for row in csv.DictReader(stream)}
        source_csv = output / f'{label}_pose_sources.csv'
        with source_csv.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['pdb', 'model_id', 'blob_index', 'sample_index', 'sdf_index', 'rmsd_A', 'source_pool_sdf', 'source_pool_server_sdf', 'world_sdf', 'world_sdf_record_index', 'server_output_dir', 'coordinate_system'])
            writer.writeheader()
            for model in used:
                server_sdf = model['output_dir'] + '/poses.sdf'
                writer.writerow({'pdb': pdb, 'model_id': model['id'], 'blob_index': model['blob'], 'sample_index': model['sample_index'], 'sdf_index': model['sdf_index'], 'rmsd_A': model['rmsd_A'], 'source_pool_sdf': originals[server_sdf], 'source_pool_server_sdf': server_sdf, 'world_sdf': (args.data_root / pdb / model['file']).as_posix(), 'world_sdf_record_index': 0, 'server_output_dir': model['output_dir'], 'coordinate_system': 'experimental map world XYZ, angstrom; no rigid-body superposition'})
        local = record['pose']
        pose_text = ('本面板包含同一预算内所有Match预测为小分子的实际构象, 每个模型的sample_index、sdf_index、原RMSD和SDF见逐姿态来源表。' if local is None else f'本面板实际构象为#{local["id"]}, 原sample_index={local["sample_index"]}, sdf_index={local["sdf_index"]}, 原RMSD={local["rmsd_A"]:.12g} Å。sample_index是原50次采样编号, sdf_index是SDF记录位置, 两者不能互换。')
        specific = ('全景中的小写字母标明其他局部面板对应的参考实例。Find的区域按原100%尝试预算截取, 再显示Match预测为小分子的候选, 背景和错身份小分子仍在图中。' if local is None else f'`ligwork pocket {record["occurrence_id"]}`显示本实例5 Å内的受体残基和实验密度网格, 不是重新对齐。随后的turn/zoom只改变相机。')
        relative_cxc = (output / f'{label}_{pdb}.cxc').as_posix()
        text = f'''# 面板{label}: {record['heading']}

从[{pdb.upper()}初始会话]({(args.data_root / pdb / 'initial.cxs').as_posix()})出发, 按下面的完整命令恢复本面板。最终[可编辑会话]({(output / (label + '_view.cxs')).as_posix()})打开即显示论文视角; [原生PNG]({(output / f'{label}_{pdb}.png').as_posix()})为同一次命令生成的图像。本教程保持CA2受体、100%原尝试预算、模型Top-1, 不计算RMSD或改变原构象。

## 一次复制执行

在ChimeraX命令栏粘贴完整块, 或执行`open "{relative_cxc}"`。首行恢复已加载材料的initial.cxs, 不重新打开load.cxc。打开会话前请先保存自己的未保存工作。

```chimerax
{chr(10).join(commands)}
```

## 每一步在做什么

1. `open .../initial.cxs`恢复全部原材料及对象编号。`camera ortho`采用正交投影; 白底、soft照明、关闭深度雾和轮廓线仅设定显示。
2. `ligwork view pipeline`、`condition CA2`、`budget 100`、`filter all`、`pose top1`固定完整流程、CryoAtom2受体、原100%尝试预算、不按GT类别过滤及模型首选构象。11JB和9BJJ的原预算分别为78次和11次计费尝试。
3. `#1.2`是CA2受体, `#2.1`是实验密度, `#3.(实例号+1)`是沉积参考, `#10.(blob号+1)`是CA2的Find区域, `#20`是CA2构象根。hide/show只改变显隐。沉积参考只显示小分子; 预测按Match身份显示小分子, 并保留相同预算内的背景和错身份实际输出。
4. 橙色为沉积小分子, 青绿色构象有既有合法参考RMSD, 棕色构象没有合法参考RMSD。颜色不等于RMSD是否低于2 Å。`label`给全景中的局部实例或背景区域加字母/状态。
5. {specific}
6. 最后的`windowsize`恢复实际图形区尺寸, `view matrix camera ...`恢复原生日志中的最终相机, `zoom pixelSize`恢复绝对显示比例, 均不移动任何结构。`scalebar`是ChimeraX按世界坐标标定的{record['scale_A']} Å原生标尺, `2dlabels`只补单位。宽幅导出的标尺位置已在实际图像中检查。
7. `save ...png`按本面板原生尺寸导图, `ligwork status`保存真实可见模型, `view matrix`与`log save`保存命令和相机, 最后一条保存可直接重开的CXS。`includeMaps false`只让会话引用长期MRC而不把大地图再嵌入会话, 因此请保留D盘材料根。

## 材料与构象来源

全部原子与密度沿实验密度世界坐标, 轴为XYZ, 长度单位Å, 不作刚体叠合。{pose_text}

| 本面板材料 | 模型或文件 | 来源与用途 |
|---|---|---|
| 初始会话 | [initial.cxs]({(args.data_root / pdb / 'initial.cxs').as_posix()}) | 原始材料分组与全部对象编号的入口 |
| 实验密度 | #2.1; [exp.npy]({(args.data_root / pdb / 'source/exp.npy').as_posix()}) | 原实验密度; 阈值{scene['contour']:.10g}; 网格与阈值见exp.npz |
| CA2受体 | #1.2; [CA2_receptor.npz]({(args.data_root / pdb / 'source/CA2_receptor.npz').as_posix()}) | CryoAtom2重建受体; 受体坐标不作叠合 |
| 沉积参考 | #3; [ligand_coords.npz]({(args.data_root / pdb / 'source/ligand_coords.npz').as_posix()}) | present掩码限定的沉积原子, 参考SDF由原模板与这些坐标生成 |
| 实际模型 | [本面板逐姿态来源表]({source_csv.as_posix()}) | 每个实际模型的blob、sample_index、sdf_index、原RMSD、世界坐标SDF及服务器run |
| 全部原件 | [本例材料来源.csv]({(args.data_root / pdb / '本例材料来源.csv').as_posix()}) | 每份NPY/NPZ/MRC/SDF/排名/指标的本地与原服务器路径 |
| 编号规则与地图 | [本例参数.md]({(args.data_root / pdb / '本例参数.md').as_posix()}) | 对象索引、候选索引、构象连接及延迟模拟密度的打开命令 |

逐姿态来源CSV的sdf_index连接source_pool_sdf中的原构象池记录, source_pool_server_sdf是同一构象池的原服务器文件。world_sdf是工作台已抽出的单构象世界坐标文件, 该文件中使用world_sdf_record_index=0。rmsd_A空单元格对应原记录的null, 表示没有合法参考RMSD, 不是0 Å。原构象和原逐姿态RMSD只读复用。新增实际构象无可用参考RMSD时显示模型Top-1, 不补造RMSD, 不进入既有评价的分子集合。最终会话和图像只展示这些材料。
'''
        (args.teaching_root / f'{label}_{pdb}.md').write_text(text, encoding='utf-8')
    (output / 'tutorials_all.cxc').write_text('\n'.join(batch) + '\n', encoding='utf-8')
    wrapper = (args.build_root / 'render_all.py').read_text(encoding='utf-8')
    wrapper = wrapper.replace(repr(str(args.build_root.resolve() / 'render_all.cxc')), repr(str(output / 'tutorials_all.cxc')))
    wrapper = wrapper.replace(args.build_root.resolve().as_posix(), output.as_posix()).replace(str(args.build_root.resolve()).replace('\\', '\\\\'), str(output).replace('\\', '\\\\'))
    (output / 'tutorials_all.py').write_text(wrapper, encoding='utf-8')
    (reopened / 'reopen_all.cxc').write_text('\n'.join(reopen_batch) + '\n', encoding='utf-8')
    reopen_wrapper = wrapper.replace('tutorials_all.cxc', 'reopen_all.cxc')
    reopen_wrapper = reopen_wrapper.replace(output.as_posix(), reopened.as_posix()).replace(str(output).replace('\\', '\\\\'), str(reopened).replace('\\', '\\\\'))
    (reopened / 'reopen_all.py').write_text(reopen_wrapper, encoding='utf-8')
    print('PREPARED_INITIAL_SESSION_TUTORIALS', len(records), flush=True)


if __name__ == '__main__':
    main()

