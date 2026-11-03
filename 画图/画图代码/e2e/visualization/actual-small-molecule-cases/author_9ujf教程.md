# 作者9UJF全景的原生命令教程

论文图采用作者author01.cxs与author01.png的视角。源文件来自`画图/古法Chimera/E2E/9ujf/`，采用时的完整副本保存在`e2e/output/actual-small-molecule-cases/author_9ujf/source/`。

先打开[D盘初始材料会话](D:/AdaLigand_Visualization/9ujf/initial.cxs)。本例参数及[逐文件来源表](D:/AdaLigand_Visualization/9ujf/本例材料来源.csv)记录完整实验密度、GT／CA2模拟密度、受体、沉积配体、模板及构象的服务器来源。初始会话已载入这些材料，下面仅调整显示。

## 一次复制执行

请先保存个人未保存的工作。以下整段可在ChimeraX命令栏粘贴执行，也可打开长期输出中的tutorial.cxc。

```chimerax
open "D:/AdaLigand_Visualization/9ujf/initial.cxs"
ligwork view pipeline
ligwork condition CA2
ligwork budget 100
ligwork filter all
ligwork pose top1
ligwork labels identity off
ligwork labels correctness off
ligwork reset
2dlabels delete all
show #1.1|#1.2 models
hide #1 atoms
cartoon #1.1|#1.2
color #1.1 #ff0000
color #1.2 #00aa00
transparency #1.1|#1.2 90.1960784314 target c
hide #2 models
hide #10|#11 models
show #3 models
show #3 atoms
color #3 #ff0000
color #20 #00aa00
camera ortho
lighting depthCue false
set bgColor white
windowsize 1126 814
wait 1
view matrix camera 0.77631,0.040628,-0.62904,45.223,-0.0042953,0.99824,0.059173,156.34,0.63034,-0.043234,0.77511,267.7
zoom pixelSize 0.1416696269982238
wait 1
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/author_9ujf/tutorial_view.cxs" includeMaps false
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/author_9ujf/tutorial.png" width 1800 height 1295
ligwork status "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/author_9ujf/tutorial_status.json"
```

`ligwork view/condition/budget/filter/pose`固定完整流程、CA2受体、100%原预算、全部候选和模型Top-1，不按正确与否删除构象。`show`与`cartoon`恢复两种受体，`hide #1 atoms`关闭其原子棒；`color`及`transparency`还原红色沉积受体、绿色重建受体和90.196%受体cartoon透明度。`hide #2`隐藏地图，`hide #10|#11`隐藏Find区域，地图与区域材料仍在会话中。`#3`是沉积参考；它包含10个GTP和10个ZN，保留作者参考显示，但正文只报告GTP建模。`#20`保留原预算内全部10个实际Top-1构象。

`view matrix camera`和`zoom pixelSize`恢复作者相机方向与绝对显示比例，不移动任何结构。命令中的相机数值摘自原生日志；不同窗口比例允许少量显示差别。`save`写复现CXS、PNG，`ligwork status`记录真实选择。论文使用作者会话直接重开生成的最终CXS，打开即可显示正式视角。

## 来源与重建

十个构象的原sample_index、原构象池sdf_index、原RMSD、单构象world SDF及服务器原件逐项列于[pose_sources.csv](../../output/actual-small-molecule-cases/author_9ujf/pose_sources.csv)。抽出的world SDF仅有记录0，不能把它与原构象池记录编号混用。

原完成度为10/10，预算为10次计数尝试。十个原RMSD的范围为0.5364181402709665–0.8048328745384161Å，全部低于1Å；正文报告0.54–0.80Å。数值由performance_source.json只读摘录，不重新计算原子RMSD或选择best-of-50。

正式PPT为`画图/全流程小分子案例_作者9UJF.pptx`，图名为`full-pipeline-small-molecule-author-9ujf`。长期脚本`author_9ujf.py`依次读取冻结材料、摘录原值、调用原生命令重绘和装配PPT；图注取caption.json，不依赖旧temp。完整重建入口为`python -B -X utf8 转换工具/ops/rebuild_figures.py --figure full-pipeline-small-molecule-author-9ujf`。
