# 作者author04的9BJJ全景

论文采用作者指定的[author04.cxs](C:/Users/15919/Desktop/论文草稿/画图/古法Chimera/E2E/9bjj/author04.cxs)及同名PNG；其冻结副本和原生重开会话见`../../output/actual-small-molecule-cases/author_9bjj/`。原始材料从[D盘初始会话](D:/AdaLigand_Visualization/9bjj/initial.cxs)载入，逐文件服务器来源见[材料来源表](D:/AdaLigand_Visualization/9bjj/本例材料来源.csv)。

## 从初始材料调节

保存个人工作后，将下面命令块一次粘贴至ChimeraX命令栏。它恢复作者全景的构象选择、颜色、透明度和相机，不移动分子。作者原始最终会话直接打开即可查看精确手工视角；命令复现允许窗口比例产生小幅显示差别。

```chimerax
open "D:/AdaLigand_Visualization/9bjj/initial.cxs"
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
color #1.2 #2bbf23
transparency #1.1|#1.2 90.1960784314 target c
hide #2 models
hide #10|#11 models
hide #3 atoms
show #3.1|#3.2|#3.3|#3.4|#3.5|#3.6|#3.7|#3.8|#3.9|#3.10|#3.11|#3.12|#3.13|#3.14|#3.15|#3.16|#3.17|#3.18|#3.19 atoms
color #3 #ff0000
color #20 #009e73
camera ortho
lighting depthCue false
set bgColor white
windowsize 1126 814
wait 1
view matrix camera -0.4467,0.8156,0.36777,200.05,-0.86663,-0.49658,0.048634,133.58,0.22229,-0.29699,0.92865,335.88
zoom pixelSize 0.19651865008880995
wait 1
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/tutorial_view.cxs" includeMaps false
save "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/tutorial.png" width 1868 height 1312
ligwork status "C:/Users/15919/Desktop/论文草稿/画图/画图代码/e2e/output/actual-small-molecule-cases/author_9bjj/tutorial_status.json"
```

前七项ligwork命令固定完整流程、CA2受体、原100%预算、全部类别和Top-1，未按正确与否筛选构象。show/cartoon打开沉积与预测受体；color及transparency还原红色沉积结构、浅绿色重建受体和90.196%受体透明度。hide只隐藏密度和Find区域，不删除背景构象；绿色20号构象树保留全部11个输出。参考配体按作者会话的原子显隐恢复。view matrix camera和zoom只调节相机及显示比例，不作刚体叠合。最后save保存可直接打开的复现会话与PNG，ligwork status保存实际选择。

## 构象与原评价

原scene.json中的CA2.expected.pipeline[100]记录成功10、目标11、预算11；本轮只读取，不重新计算。可见模型连接为CA2_pose_0_0_top1至CA2_pose_10_0_top1，原sample_index、sdf_index和RMSD均见D盘scene.json。blob10是背景ATP实际Top-1，原参考RMSD为空。其原文件位于`/storage/penghongen/Adaligand_E2E/actual_display_20261101/CA2/build/test/local-c1/9bjj/10/`，其余来源沿各模型output_dir及材料来源表查询。
