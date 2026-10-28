"""生成五套六视角的 ChimeraX 原生命令与逐视角中文教程. 

先运行共享 prepare_assets.py, 再运行本文件. --prepared 是每例 assets/ 与 evidence.json 的冻结目录; --output 接收每例 initial.cxc、commands/*.cxc 和 tutorials/*.md. 所有外观与相机操作都写在 CXC 中, 不通过 Python 属性修改. 
实际 CXS、PNG 与只读相机记录由 render_native.py 执行这些命令后写出. 
"""
from pathlib import Path
import argparse
import json


# ================================================================================================
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prepared',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
# code 是本图的长期病例清单; prepared 是由冻结原件转换出的原生地图与原子材料. 
code=Path(__file__).resolve().parent
# project 是论文仓库根; receipts 指向长期冻结来源清单, 使临时重建中的教程也能追溯原件. 
project=code.parents[4]
receipts=project/'画图/画图代码/stage1/output/stage1-level-global-local/explicit_emdb_level'
cases=json.loads((code/'cases.json').read_text(encoding='utf-8'))
panels=[('a_reference','真实受体、配体和真实区域'),('b_emap_global','Emap2lig-level 的全局预测'),('c_ca2_global','LigandSeek-CA2 的全局预测'),('d_receptor_fp','Emap2lig 在受体上的假阳性'),('e_emap_local','Emap2lig 的局部真实命中'),('f_ca2_local','LigandSeek-CA2 对同一实例的预测')]
models=[('density.mrc','原实验密度'),('reference_receptor.cif','沉积受体'),('ca2_receptor.cif','实际CA2输入受体'),('ligands_all.cif','全部沉积配体'),('truth_all.mrc','全部真实配体区域'),('cryo_all.mrc','CA2全部保留预测'),('emap_all.mrc','Emap2lig_level全部保留预测'),('ligand_target.cif','当前沉积配体'),('truth_local.mrc','当前配体真实区域'),('cryo_local.mrc','CA2实际匹配的完整blob'),('emap_local.mrc','Emap2lig实际匹配的完整blob'),('emap_receptor_fp.mrc','Emap2lig受体上完整FP_blob'),('receptor_pocket.cif','GT配体邻域受体原子'),('ca2_pocket.cif','CA2同位置受体原子'),('receptor_fp_neighbours.cif','GT误报邻域受体原子')]
for case in cases:
    pdb=case['pdb']
    # destination 是长期交付或本次完整重建的独立目录, 命令中的绝对路径由它确定. 
    destination=(args.output/pdb).resolve()
    assets=(args.prepared/pdb/'assets').resolve()
    evidence=json.loads((args.prepared/pdb/'evidence.json').read_text(encoding='utf-8'))
    for child in ('commands','tutorials','views','my_sessions'): (destination/child).mkdir(parents=True,exist_ok=True)
    initial=['close all','set bgColor white','camera ortho','lighting soft','material dull','graphics silhouettes false','windowsize 1000 800']
    initial += [f'open "{(assets/name).as_posix()}" id #{i} name "{label}"' for i,(name,label) in enumerate(models,1)]
    initial += ['hide models','hide #2-4,8,13-15 atoms','hide #13-15 cartoons','hide #13-15 pseudobonds','cartoon #2,3','color #2,3 #adb5bd target c','transparency #2,3 30 target c','style #4,8,13-15 stick','color #4,8 byelement','color #4,8 & C #374151','size #4,8 stickRadius 0.17','color #13-15 #7c8797','size #13-15 stickRadius 0.13',
        f'volume #1 style mesh step 1 level {evidence["contour"]:.10g} color #b4b9bf transparency 0.75 surfaceSmoothing false',
        'volume #5-7,9-12 style surface level 0.5 step 1 surfaceSmoothing false','volume #5,9 color #009E73 transparency 0.55','volume #6,10 color #5975bd transparency 0.40','volume #7,11,12 color #D55E00 transparency 0.40','show #2,4,5 models','show #4 atoms','view #2-7 orient','view #2-7 pad 0.10','clip off','wait 2',f'save "{(destination/"initial.cxs").as_posix()}" includeMaps true']
    (destination/'initial.cxc').write_text('\n'.join(initial)+'\n',encoding='utf-8')
    model_table='\n'.join(f'| #{i} | {label} | `{name}` |' for i,(name,label) in enumerate(models,1))
    source_text=f'''# {pdb.upper()} 初始会话与材料来源

本例属于 `explicit_emdb_level`。Emap2lig 显式输入原 EMDB 推荐 level L，原管线实际阈值为 L/2；预测不在这里重新计算。CA2 和 GT 公共材料保持原实验坐标。原子为 XYZ Å，掩码为全局 ZYX 体素；MRC origin 为首体素中心，裁零时同步平移，预测 0.5 等值面不平滑。

当前配体 occurrence 为 {case['occurrence_id']}，CA2 / Emap2lig 原生 blob 为 {case['local_blobs']['cryo']} / {case['local_blobs']['emap']}；受体 FP 为 Emap2lig blob {case['receptor_fp_blob']}。准确沉积身份、全部候选计数、距离及匹配证据见同目录 `evidence.json`；其原生成依据为 `{(args.prepared/pdb/'evidence.json').resolve().as_posix()}`。下表所有原生材料文件名均相对实际目录 `{assets.as_posix()}`。

| 编号 | 科学对象 | 原生材料 |
| --- | --- | --- |
{model_table}

`density.mrc` 由该例 Ori_Data 的 `density/<pdb>/exp.npy` 转换，使用 `exp.npz` 内的 `contour_canonical`，是统一网格上的预处理连续密度；它的显示阈值不能当成原 EMDB 推荐 level L。#5–7、#9–12 为 0/1 区域掩码，统一用 0.5 等值面。论文六幅视角隐藏连续密度 #1，但初始会话保留它以供独立查看。

两份受体 CIF 从各自推理 token 的原子坐标重建，`C<n>` 链名和 `res_index+1` 是 token 编号，不是沉积链号／残基号；配体 CIF 则保留沉积 auth 标识。不能直接用受体 token 编号与配体 auth 编号配对。CA2 局部受体按同一沉积配体周围 6 Å 选取 CA2 原子，不使用 GT 受体原子替代 CA2。

原件来源见[元数据来源](<{(receipts/'metadata_source_receipt.json').as_posix()}>)、[密度来源](<{(receipts/'density_source_receipt.json').as_posix()}>)和[公共材料复用](<{(receipts/'local_reuse_receipt.json').as_posix()}>)。前两份的 `local` 相对冻结条件根目录的 `sources/`，复用清单的 `local` 相对条件根目录；`source` 为只读服务器原始绝对路径。新 Emap2lig 原件来自论文仓库的 `补充数据/Emap2lig_双条件/explicit_emdb_level/find/held_out_test_0/`。原材料不会被视角命令改写。`initial.cxs` 与六份 `views/*.cxs` 均嵌入地图，可离线重开；作者修改请另存到 `my_sessions/`，重建不写该目录。

## 六幅视角的独立教学入口

| 面板 | 从初始材料开始的教程 | 打开即显示目标视角 |
| --- | --- | --- |
{chr(10).join(f'| {name[0]}：{title} | [命令与讲解](tutorials/{name}.md) | [最终会话](views/{name}.cxs) |' for name,title in panels)}
'''
    (destination/'来源与模型.md').write_text(source_text,encoding='utf-8')
    (destination/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    for name,title in panels:
        commands=['close all',f'open "{(destination/"initial.cxs").as_posix()}"','windowsize 1000 800','hide models','clip off']
        if name.startswith(('a_','b_','c_')):
            visible={'a_reference':'#2,4,5','b_emap_global':'#2,7','c_ca2_global':'#3,6'}[name]
            # view 可能忽略隐藏模型的边界; 先同时显示共同参照定相机, 再切换本图对象. 
            commands += ['show #2-7 models','show #4 atoms','view #2-7 orient']+[f'turn {axis} {angle}' for axis,angle in case['global_turns']]+['view #2-7 pad 0.10','hide models',f'show {visible} models']
            if name=='a_reference': commands += ['show #4 atoms']
            explanation='先暂时同时显示 #2-7，用全部共同参照确定相机；三张全局图使用同一 turn、pad 和裁剪。最后 hide/show 切换到本图科学对象，此后不再 fit，因此 GT/CA2 背景差异不会改变视角或尺度。'
        elif name=='d_receptor_fp':
            commands += ['show #12,15 models','show #15 atoms','hide #15 cartoons','view #12,15 orient']+[f'turn {axis} {angle}' for axis,angle in case['fp_turns']]+['view #12,15 pad 0.20']
            explanation='橙色 #12 是完整假阳性 blob，灰色 #15 是其附近的沉积受体重原子。此 blob 与全部真实配体区域零交集；受体距离用于解释位置，不替换正式 TP/FP 判定。'
        else:
            visible='#8,9,11,13' if name=='e_emap_local' else '#8,9,10,14'
            atoms='#8,13' if name=='e_emap_local' else '#8,14'
            commands += ['show #8-11 models','show #8 atoms','volume #9 style mesh transparency 0.15','view #8-11 orient']+[f'turn {axis} {angle}' for axis,angle in case['local_turns']]+['view #8-11 pad 0.20','hide models',f'show {visible} models',f'show {atoms} atoms']
            explanation='绿色网格 #9 是同一实例的真实区域；橙／蓝面是双方实际匹配的完整 blob。e 用 GT 受体邻域 #13，f 用 CA2 邻域 #14；方向、并集范围与比例相同。turn 不指定 atoms，只旋转整个显示场景，不改变分子内部坐标。'
        commands += ['clip off','wait 2',f'save "{(destination/"views"/(name+".cxs")).as_posix()}" includeMaps true',f'save "{(destination/"views"/(name+".png")).as_posix()}" width 1600 height 1280 supersample 2']
        (destination/'commands'/(name+'.cxc')).write_text('\n'.join(commands)+'\n',encoding='utf-8')
        tutorial=f'''# {pdb.upper()} {name}：{title}

从本例 `initial.cxs` 出发。下面完整命令块会重开该初始会话，重置显隐与相机，再生成对应最终会话和图片；请先另存自己尚未保存的调整。模型编号和材料来源见[来源与模型](../来源与模型.md)。

## 一次粘贴完成

在 ChimeraX 底部命令栏一次粘贴下面这一行，即执行同名明文 CXC：

```chimerax
open "{(destination/'commands'/(name+'.cxc')).as_posix()}"
```

这份 CXC 的全部内容如下，也可以逐条执行。命令使用生成时的绝对路径，不依赖 ChimeraX 当前工作目录；本教程相对链接以教程文件所在目录为基准。这里没有隐藏的 Python 相机操作，也不依靠已保存的最终命名视角。

```chimerax
{chr(10).join(commands)}
```

## 命令如何形成这个视角

1. `close all`、`open` 从同一初始材料重新开始；`windowsize` 固定导出长宽比。地图、原子和预测均已在初始会话内，之后不再取数或重新推理。
2. `hide models`、`show ... models` 选择本图科学对象；`show ... atoms` 显示棒状原子。隐藏不会删除或筛掉预测。`volume ... style mesh` 只把真值表面切成网格，不改阈值或体素。
3. {explanation}
4. `turn x/y` 的数字是角度；`pad` 是视野边距比例；`clip off` 保留完整边界。改变这些显示参数后也可另存自己的版本。所有对应比较应采用相同参数。
5. `wait 2` 等待绘图更新。第一条 `save` 保存包含地图的最终 CXS；第二条保存 1600×1280 PNG，`supersample 2` 改善边缘，数据不变。重新打开 `views/{name}.cxs` 即显示这个视角。

PPT 中面板字母、指标、比例尺和定位框为独立原生组件；本教程重建的是三维子图及其视角。编辑后请另存 `my_sessions/`，保留本份交付。原生命令参考：[ChimeraX turn](https://www.cgl.ucsf.edu/chimerax/docs/user/commands/turn.html)。
'''
        (destination/'tutorials'/(name+'.md')).write_text(tutorial,encoding='utf-8')
    print(pdb+'：初始与六视角命令、逐视角教程已生成。',flush=True)
