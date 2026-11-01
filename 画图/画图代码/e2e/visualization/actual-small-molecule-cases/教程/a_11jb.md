# 面板a: 11JB | 78 deposited small molecules

从[11JB初始会话](D:/AdaLigand_Visualization/11jb/initial.cxs)出发, 按下面的完整命令恢复本面板。最终[可编辑会话](C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_view.cxs)打开即显示论文视角; [原生PNG](C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_11jb.png)为同一次命令生成的图像。本教程保持CA2受体、100%原尝试预算、模型Top-1, 不计算RMSD或改变原构象。

## 一次复制执行

在ChimeraX命令栏粘贴完整块, 或执行`open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_11jb.cxc"`。首行恢复已加载材料的initial.cxs, 不重新打开load.cxc。打开会话前请先保存自己的未保存工作。

```chimerax
open "D:/AdaLigand_Visualization/11jb/initial.cxs"
2dlabels delete all
camera ortho
set bgColor white
lighting soft
lighting depthCue false
graphics silhouettes false
ligwork view pipeline
ligwork condition CA2
ligwork budget 100
ligwork filter all
ligwork pose top1
ligwork labels identity off
ligwork labels correctness off
ligwork reset
hide #1 models
show #1.2 models
hide #1 atoms
cartoon #1.2
color #1.2 #b9c1cb
transparency #1.2 20 target c
hide #2 models
hide #!4 models
show #3 models
style #3 stick
size #3 stickRadius 0.18
color #3 #e69f00
color #20.1.1.1|#20.2.1.1|#20.3.1.1|#20.4.1.1|#20.5.1.1|#20.6.1.1|#20.7.1.1|#20.8.1.1|#20.9.1.1|#20.10.1.1|#20.11.1.1|#20.12.1.1|#20.13.1.1|#20.14.1.1|#20.15.1.1|#20.16.1.1|#20.17.1.1|#20.18.1.1|#20.19.1.1|#20.20.1.1|#20.21.1.1|#20.22.1.1|#20.23.1.1|#20.24.1.1|#20.25.1.1|#20.26.1.1|#20.27.1.1|#20.28.1.1|#20.29.1.1|#20.30.1.1|#20.31.1.1|#20.32.1.1|#20.33.1.1|#20.34.1.1|#20.35.1.1|#20.36.1.1|#20.37.1.1|#20.38.1.1|#20.39.1.1|#20.40.1.1|#20.41.1.1|#20.42.1.1|#20.43.1.1|#20.44.1.1|#20.45.1.1|#20.46.1.1|#20.47.1.1|#20.48.1.1|#20.49.1.1|#20.50.1.1|#20.51.1.1|#20.52.1.1|#20.53.1.1|#20.54.1.1|#20.55.1.1|#20.56.1.1|#20.57.1.1|#20.58.1.1|#20.59.1.1|#20.60.1.1|#20.61.1.1|#20.62.1.1|#20.63.1.1|#20.64.1.1|#20.65.1.1|#20.66.1.1|#20.67.1.1|#20.68.1.1|#20.69.1.1|#20.70.1.1|#20.71.1.1|#20.72.1.1|#20.73.1.1|#20.74.1.1|#20.75.1.1|#20.76.1.1|#20.77.1.1|#20.78.1.1 #009e73
size #20.1.1.1|#20.2.1.1|#20.3.1.1|#20.4.1.1|#20.5.1.1|#20.6.1.1|#20.7.1.1|#20.8.1.1|#20.9.1.1|#20.10.1.1|#20.11.1.1|#20.12.1.1|#20.13.1.1|#20.14.1.1|#20.15.1.1|#20.16.1.1|#20.17.1.1|#20.18.1.1|#20.19.1.1|#20.20.1.1|#20.21.1.1|#20.22.1.1|#20.23.1.1|#20.24.1.1|#20.25.1.1|#20.26.1.1|#20.27.1.1|#20.28.1.1|#20.29.1.1|#20.30.1.1|#20.31.1.1|#20.32.1.1|#20.33.1.1|#20.34.1.1|#20.35.1.1|#20.36.1.1|#20.37.1.1|#20.38.1.1|#20.39.1.1|#20.40.1.1|#20.41.1.1|#20.42.1.1|#20.43.1.1|#20.44.1.1|#20.45.1.1|#20.46.1.1|#20.47.1.1|#20.48.1.1|#20.49.1.1|#20.50.1.1|#20.51.1.1|#20.52.1.1|#20.53.1.1|#20.54.1.1|#20.55.1.1|#20.56.1.1|#20.57.1.1|#20.58.1.1|#20.59.1.1|#20.60.1.1|#20.61.1.1|#20.62.1.1|#20.63.1.1|#20.64.1.1|#20.65.1.1|#20.66.1.1|#20.67.1.1|#20.68.1.1|#20.69.1.1|#20.70.1.1|#20.71.1.1|#20.72.1.1|#20.73.1.1|#20.74.1.1|#20.75.1.1|#20.76.1.1|#20.77.1.1|#20.78.1.1 stickRadius 0.19
color #10.1|#10.2|#10.3|#10.4|#10.5|#10.6|#10.7|#10.8|#10.9|#10.10|#10.11|#10.12|#10.13|#10.14|#10.15|#10.16|#10.17|#10.18|#10.19|#10.20|#10.21|#10.22|#10.23|#10.24|#10.25|#10.26|#10.27|#10.28|#10.29|#10.30|#10.31|#10.32|#10.33|#10.34|#10.35|#10.36|#10.37|#10.38|#10.39|#10.40|#10.41|#10.42|#10.43|#10.44|#10.45|#10.46|#10.47|#10.48|#10.49|#10.50|#10.51|#10.52|#10.53|#10.54|#10.55|#10.56|#10.57|#10.58|#10.59|#10.60|#10.61|#10.62|#10.63|#10.64|#10.65|#10.66|#10.67|#10.68|#10.69|#10.70|#10.71|#10.72|#10.73|#10.74|#10.75|#10.76|#10.77|#10.78 #009e73
color #10.79|#10.80|#10.82|#10.81|#10.83 #b56b47
hide #10.79|#10.80|#10.82|#10.81|#10.83 models
transparency #10 90 target s
volume unzone #2.1
volume #2.1 region all
windowsize 1700 1300
wait 1
view
zoom 0.96
label #3.17 residues text "b" height fixed size 32 color #222222 offset 0,15,0 onTop true
windowsize 1128 891
wait 1
view matrix camera 1,0,0,427.97,0,1,0,427.59,0,0,1,1300.7
zoom pixelSize 0.48835106383
scalebar delete
scalebar 100 thickness 7 xpos 0.07 ypos 0.055 color black
2dlabels create scale text "100 Å" xpos 0.07 ypos 0.085 size 28 color black
wait 1
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_11jb.png" width 1700 height 1300 supersample 2
ligwork status "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_status.json"
view matrix
camera
zoom
windowsize
log save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_commands.html"
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_view.cxs" includeMaps false
```

## 每一步在做什么

1. `open .../initial.cxs`恢复全部原材料及对象编号。`camera ortho`采用正交投影; 白底、soft照明、关闭深度雾和轮廓线仅设定显示。
2. `ligwork view pipeline`、`condition CA2`、`budget 100`、`filter all`、`pose top1`固定完整流程、CryoAtom2受体、原100%尝试预算、不按GT类别过滤及模型首选构象。11JB和9BJJ的原预算分别为78次和11次计费尝试。
3. `#1.2`是CA2受体, `#2.1`是实验密度, `#3.(实例号+1)`是沉积参考, `#10.(blob号+1)`是CA2的Find区域, `#20`是CA2构象根。hide/show只改变显隐。沉积参考只显示小分子; 预测按Match身份显示小分子, 并保留相同预算内的背景和错身份实际输出。
4. 橙色为沉积小分子, 青绿色构象有既有合法参考RMSD, 棕色构象没有合法参考RMSD。颜色不等于RMSD是否低于2 Å。`label`给全景中的局部实例或背景区域加字母/状态。
5. 全景中的小写字母标明其他局部面板对应的参考实例。Find的区域按原100%尝试预算截取, 再显示Match预测为小分子的候选, 背景和错身份小分子仍在图中。
6. 最后的`windowsize`恢复实际图形区尺寸, `view matrix camera ...`恢复原生日志中的最终相机, `zoom pixelSize`恢复绝对显示比例, 均不移动任何结构。`scalebar`是ChimeraX按世界坐标标定的100 Å原生标尺, `2dlabels`只补单位。宽幅导出的标尺位置已在实际图像中检查。
7. `save ...png`按本面板原生尺寸导图, `ligwork status`保存真实可见模型, `view matrix`与`log save`保存命令和相机, 最后一条保存可直接重开的CXS。`includeMaps false`只让会话引用长期MRC而不把大地图再嵌入会话, 因此请保留D盘材料根。

## 材料与构象来源

全部原子与密度沿实验密度世界坐标, 轴为XYZ, 长度单位Å, 不作刚体叠合。本面板包含同一预算内所有Match预测为小分子的实际构象, 每个模型的sample_index、sdf_index、原RMSD和SDF见逐姿态来源表。

| 本面板材料 | 模型或文件 | 来源与用途 |
|---|---|---|
| 初始会话 | [initial.cxs](D:/AdaLigand_Visualization/11jb/initial.cxs) | 原始材料分组与全部对象编号的入口 |
| 实验密度 | #2.1; [exp.npy](D:/AdaLigand_Visualization/11jb/source/exp.npy) | 原实验密度; 阈值0.1632595807; 网格与阈值见exp.npz |
| CA2受体 | #1.2; [CA2_receptor.npz](D:/AdaLigand_Visualization/11jb/source/CA2_receptor.npz) | CryoAtom2重建受体; 受体坐标不作叠合 |
| 沉积参考 | #3; [ligand_coords.npz](D:/AdaLigand_Visualization/11jb/source/ligand_coords.npz) | present掩码限定的沉积原子, 参考SDF由原模板与这些坐标生成 |
| 实际模型 | [本面板逐姿态来源表](C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/a_pose_sources.csv) | 每个实际模型的blob、sample_index、sdf_index、原RMSD、世界坐标SDF及服务器run |
| 全部原件 | [本例材料来源.csv](D:/AdaLigand_Visualization/11jb/本例材料来源.csv) | 每份NPY/NPZ/MRC/SDF/排名/指标的本地与原服务器路径 |
| 编号规则与地图 | [本例参数.md](D:/AdaLigand_Visualization/11jb/本例参数.md) | 对象索引、候选索引、构象连接及延迟模拟密度的打开命令 |

逐姿态来源CSV的sdf_index连接source_pool_sdf中的原构象池记录, source_pool_server_sdf是同一构象池的原服务器文件。world_sdf是工作台已抽出的单构象世界坐标文件, 该文件中使用world_sdf_record_index=0。rmsd_A空单元格对应原记录的null, 表示没有合法参考RMSD, 不是0 Å。原构象和原逐姿态RMSD只读复用。新增实际构象无可用参考RMSD时显示模型Top-1, 不补造RMSD, 不进入既有评价的分子集合。最终会话和图像只展示这些材料。
