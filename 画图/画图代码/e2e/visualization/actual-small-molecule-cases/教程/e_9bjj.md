# 面板e: A1AP0 (E:1001) | RMSD 1.06 Å

从[9BJJ初始会话](D:/AdaLigand_Visualization/9bjj/initial.cxs)出发, 按下面的完整命令恢复本面板。最终[可编辑会话](C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_view.cxs)打开即显示论文视角; [原生PNG](C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_9bjj.png)为同一次命令生成的图像。本教程保持CA2受体、100%原尝试预算、模型Top-1, 不计算RMSD或改变原构象。

## 一次复制执行

在ChimeraX命令栏粘贴完整块, 或执行`open "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_9bjj.cxc"`。首行恢复已加载材料的initial.cxs, 不重新打开load.cxc。打开会话前请先保存自己的未保存工作。

```chimerax
open "D:/AdaLigand_Visualization/9bjj/initial.cxs"
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
hide #3.3 models
hide #3.4 models
hide #3.7 models
hide #3.8 models
hide #3.11 models
hide #3.12 models
hide #3.15 models
hide #3.16 models
color #20.1.1.1|#20.2.1.1|#20.3.1.1|#20.4.1.1|#20.5.1.1|#20.6.1.1|#20.7.1.1|#20.8.1.1|#20.9.1.1|#20.10.1.1 #009e73
size #20.1.1.1|#20.2.1.1|#20.3.1.1|#20.4.1.1|#20.5.1.1|#20.6.1.1|#20.7.1.1|#20.8.1.1|#20.9.1.1|#20.10.1.1 stickRadius 0.19
color #20.11.1.1 #b56b47
size #20.11.1.1 stickRadius 0.19
color #10.1|#10.2|#10.3|#10.4|#10.5|#10.6|#10.7|#10.8|#10.9|#10.10 #009e73
color #10.11|#10.12|#10.13|#10.14|#10.15 #b56b47
hide #10.12|#10.13|#10.14|#10.15 models
transparency #10 90 target s
volume unzone #2.1
volume #2.1 region all
label delete #3
hide #10|#11|#20|#21 models
hide #3 models
show #3.17 models
show #20.9.1.1 models
windowsize 1700 780
wait 1
ligwork pocket 16
color #1.2 #c0c5cb
size #1.2 stickRadius 0.07
color #3.17 #e69f00
size #3.17 stickRadius 0.14
color #20.9.1.1 #009e73
size #20.9.1.1 stickRadius 0.18
volume #2.1 level 0.02109557576
volume #2.1 meshLighting false
color #2.1 #596773
transparency #2.1 0 target s
turn y 20
turn x -15
zoom 0.68
windowsize 1128 844
wait 1
view matrix camera 0.77003,-0.24904,-0.5874,127.75,-0.088521,0.87007,-0.48492,84.765,0.63184,0.4254,0.64793,160.08
zoom pixelSize 0.0326861702128
scalebar delete
scalebar 5 thickness 7 xpos 0.07 ypos 0.25 color black
2dlabels create scale text "5 Å" xpos 0.07 ypos 0.28 size 28 color black
wait 1
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_9bjj.png" width 1700 height 780 supersample 2
ligwork status "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_status.json"
view matrix
camera
zoom
windowsize
log save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_commands.html"
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_view.cxs" includeMaps false
```

## 每一步在做什么

1. `open .../initial.cxs`恢复全部原材料及对象编号。`camera ortho`采用正交投影; 白底、soft照明、关闭深度雾和轮廓线仅设定显示。
2. `ligwork view pipeline`、`condition CA2`、`budget 100`、`filter all`、`pose top1`固定完整流程、CryoAtom2受体、原100%尝试预算、不按GT类别过滤及模型首选构象。11JB和9BJJ的原预算分别为78次和11次计费尝试。
3. `#1.2`是CA2受体, `#2.1`是实验密度, `#3.(实例号+1)`是沉积参考, `#10.(blob号+1)`是CA2的Find区域, `#20`是CA2构象根。hide/show只改变显隐。沉积参考只显示小分子; 预测按Match身份显示小分子, 并保留相同预算内的背景和错身份实际输出。
4. 橙色为沉积小分子, 青绿色构象有既有合法参考RMSD, 棕色构象没有合法参考RMSD。颜色不等于RMSD是否低于2 Å。`label`给全景中的局部实例或背景区域加字母/状态。
5. `ligwork pocket 16`显示本实例5 Å内的受体残基和实验密度网格, 不是重新对齐。随后的turn/zoom只改变相机。
6. 最后的`windowsize`恢复实际图形区尺寸, `view matrix camera ...`恢复原生日志中的最终相机, `zoom pixelSize`恢复绝对显示比例, 均不移动任何结构。`scalebar`是ChimeraX按世界坐标标定的5 Å原生标尺, `2dlabels`只补单位。宽幅导出的标尺位置已在实际图像中检查。
7. `save ...png`按本面板原生尺寸导图, `ligwork status`保存真实可见模型, `view matrix`与`log save`保存命令和相机, 最后一条保存可直接重开的CXS。`includeMaps false`只让会话引用长期MRC而不把大地图再嵌入会话, 因此请保留D盘材料根。

## 材料与构象来源

全部原子与密度沿实验密度世界坐标, 轴为XYZ, 长度单位Å, 不作刚体叠合。本面板实际构象为#20.9.1.1, 原sample_index=4, sdf_index=4, 原RMSD=1.05807289172 Å。sample_index是原50次采样编号, sdf_index是SDF记录位置, 两者不能互换。

| 本面板材料 | 模型或文件 | 来源与用途 |
|---|---|---|
| 初始会话 | [initial.cxs](D:/AdaLigand_Visualization/9bjj/initial.cxs) | 原始材料分组与全部对象编号的入口 |
| 实验密度 | #2.1; [exp.npy](D:/AdaLigand_Visualization/9bjj/source/exp.npy) | 原实验密度; 阈值0.02109557576; 网格与阈值见exp.npz |
| CA2受体 | #1.2; [CA2_receptor.npz](D:/AdaLigand_Visualization/9bjj/source/CA2_receptor.npz) | CryoAtom2重建受体; 受体坐标不作叠合 |
| 沉积参考 | #3; [ligand_coords.npz](D:/AdaLigand_Visualization/9bjj/source/ligand_coords.npz) | present掩码限定的沉积原子, 参考SDF由原模板与这些坐标生成 |
| 实际模型 | [本面板逐姿态来源表](C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/native/tutorials/e_pose_sources.csv) | 每个实际模型的blob、sample_index、sdf_index、原RMSD、世界坐标SDF及服务器run |
| 全部原件 | [本例材料来源.csv](D:/AdaLigand_Visualization/9bjj/本例材料来源.csv) | 每份NPY/NPZ/MRC/SDF/排名/指标的本地与原服务器路径 |
| 编号规则与地图 | [本例参数.md](D:/AdaLigand_Visualization/9bjj/本例参数.md) | 对象索引、候选索引、构象连接及延迟模拟密度的打开命令 |

逐姿态来源CSV的sdf_index连接source_pool_sdf中的原构象池记录, source_pool_server_sdf是同一构象池的原服务器文件。world_sdf是工作台已抽出的单构象世界坐标文件, 该文件中使用world_sdf_record_index=0。rmsd_A空单元格对应原记录的null, 表示没有合法参考RMSD, 不是0 Å。原构象和原逐姿态RMSD只读复用。新增实际构象无可用参考RMSD时显示模型Top-1, 不补造RMSD, 不进入既有评价的分子集合。最终会话和图像只展示这些材料。
