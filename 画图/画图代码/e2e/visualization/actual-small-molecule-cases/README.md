# 两个大复合物的实际小分子构象图

当前正文已按作者指定改用9BJJ的author04全景，原五面板保留。当前[原生命令教程](author_9bjj教程.md)、[最终会话](../../output/actual-small-molecule-cases/author_9bjj/author_final.cxs)及[来源记录](../../output/actual-small-molecule-cases/author_9bjj/source_receipt.json)可直接查看。新页位于`画图/全流程小分子案例_作者9BJJ.pptx`，稳定图名为`full-pipeline-small-molecule-author-9bjj`。下文描述原五面板基础设施。

本图展示11JB与9BJJ的LigandSeek实际小分子建模输出，固定为CA2受体、100%原尝试预算和模型Top-1。它只补充实际显示，不重新采样已有有效构象、不计算RMSD或完成度、不修改原论文指标。正式图名为`full-pipeline-small-molecule-cases`，PPT为`画图/全流程小分子案例.pptx`。

本图是新建的全景与局部证据组合，只继承已有工作台的字体、颜色、原生导图和PPT装配习惯，不复制原六面板图的统计说明。a/c给出两例的实际全景，b/d/e给出同一预算和构象选择下的AR6、ATP、A1AP0局部。全景与局部使用同一个实际来源构象，没有额外对齐或修改坐标。

## 输入与产物

下面两段列出同一物理数据根中的不同用途文件。正式冻结来源在`e2e/output/actual-small-molecule-cases/`；每轮构建通过显式`--build-root`写入本轮`temp`，不读取旧临时结果。

```text
## <科学产物>
D:/AdaLigand_Visualization/{11jb,9bjj}/
├─ scene.json                       # 原候选、预算、实际构象、原RMSD及材料编号
├─ load.cxc                         # 官方命令加载本例世界坐标材料
└─ assets/                          # 原生受体、密度、沉积参考及实际姿态

画图/画图代码/e2e/output/actual-small-molecule-cases/
├─ scenes.json                      # 生成时两例场景记录
├─ panels.json                      # 五面板固定预算与原姿态连接
├─ native/                          # 长期原生PNG、最终CXS、CXC、命令日志和真实显隐
│  └─ tutorials/                    # 从initial.cxs逐面板复现的命令、会话及来源CSV
└─ full-pipeline-small-molecule-cases.caption.md # 同源双语图注

## <其他文件>
temp/actual_display_20261101/figure/
├─ render_all.cxc                   # 按序执行五组原生命令（可再生工具输入）
├─ {a_11jb,b_11jb,c_9bjj,d_9bjj,e_9bjj}.cxc # 每面板完整官方命令（可再生工具输入）
├─ {a_11jb,b_11jb,c_9bjj,d_9bjj,e_9bjj}.png # 同次实际原生导图（可再生辅助导出）
├─ {a,b,c,d,e}_view.cxs             # 本次各面板可编辑会话（可再生辅助导出）
├─ {a,b,c,d,e}_commands.html         # 官方实际命令与相机矩阵（运行诊断）
├─ {a,b,c,d,e}_status.json           # 本次实际显隐状态（运行诊断）
├─ presentation_data.json           # 180×170 mm联图布局、文字与图注（可再生工具输入）
├─ candidate.pptx                   # 原生可编辑图片、标题、标签及双语备注（可再生辅助导出）
├─ powerpoint-final.pdf             # PowerPoint实际导出（可再生辅助导出）
└─ *.alignment.json / *.collision-audit.json # 实际几何与碰撞核查（外部抽样审计）
```

`panels.json`每项对应一个图面板。`label/pdb/occurrence_id`为面板字母、PDB与局部参考实例；全景的实例为空。`pose`保存原模型编号、原sample_index、原sdf_index、原世界坐标SDF及原RMSD连接，全景为空。`budget`为原100%预算次数，11JB为78、9BJJ为11；`allowed_blobs`是原`before.pipeline < budget`的完整考察集合，不按GT类别过滤。`displayed_pose_keys`连接场景中的原构象key。`x_mm/y_mm/w_mm/h_mm`为联图内的毫米位置和尺寸，例如a为`[3,18,85,65]`。`scale_A`是由ChimeraX原生标尺标定的长度，例如局部5 Å。`expected`仅复制原冻结评价记录，绘制过程不重新汇总。

三个局部固定为11JB／AR6／f:2001／occurrence 16，9BJJ／ATP／B:901／occurrence 4及9BJJ／A1AP0／E:1001／occurrence 16。Top-1采样编号分别为3、21、4；对应原RMSD分别约1.46、0.80、1.06 Å。实际连接仍以冻结`panels.json`中的完整记录为准，不能通过PPT图像反推采样编号。

青绿色构象具有既有合法参考RMSD，棕色构象没有合法参考RMSD，橙色为沉积小分子。颜色不表示所有青绿色构象均低于2 Å，也不给棕色构象赋予RMSD阈值。在原预算截取后，仅显示Match预测为小分子的blob及其实际构象；小分子以外的沉积参考仅在显示层隐藏。新增预测错误和背景构象按原预算保留，不使用GT的small／eligible过滤来删除它们。

## 重建

先完成实际输出的工作台材料准备，再从论文仓库根运行：

```powershell
D:/Anaconda/python.exe -B -X utf8 画图/画图代码/e2e/visualization/actual-small-molecule-cases/build.py prepare --data-root D:/AdaLigand_Visualization --build-root temp/actual_display_20261101/figure
powershell -File 转换工具/ops/rebuild_support/run_chimerax.ps1 -CxcPath temp/actual_display_20261101/figure/render_all.py -LogPrefix temp/actual_display_20261101/figure/native
D:/Anaconda/python.exe -B -X utf8 画图/画图代码/e2e/visualization/actual-small-molecule-cases/build.py assemble --data-root D:/AdaLigand_Visualization --build-root temp/actual_display_20261101/figure
```

之后用Codex固定Node运行`assemble.mjs <build-root>`，再运行`finish.py --build-root <build-root>`。`assemble.mjs`使用artifact-tool创建单页原生PPT并执行包与几何验收；`finish.py`只打开本轮候选添加传统`@@`批注及双语备注，并通过PowerPoint实际导出。不会打开或改动已有作者PPT。正式发布与八份追溯文档的来源同步由本轮收口处理。

分子、密度、视角、标尺和PNG全部由ChimeraX官方CXC命令完成。Python只整理连接、生成命令和等比排列整张原生图像，不变更原子、密度、局部对比度或图内坐标。全景原生图1700×1300像素，局部1700×780像素；组装只等比缩放，无图像裁切或亮度变换。两个全景的尺寸一致，三个局部的尺寸一致；180mm图宽下最小外部文字为6pt。

装配后运行Nature figure的`validate_figure.py`、`audit_pdf_text.py --min-pt 5`与`audit_figure_collisions.py`，并检查`require_matplotlib_panel_alignment`写出的对齐JSON。PowerPoint实际PDF也需进行字号与碰撞检查，并逐面板人工检查原生图像。相同颜色、正确来源及数值保全仍需结合场景与本次实际显隐核查，不能只凭自动布局通过作结论。

PDF碰撞检查使用仓库固定依赖`.manuscript_deps/figure_runtime`内的PyMuPDF。运行前将此绝对目录加入`PYTHONPATH`，解释器仍为`D:/Anaconda/python.exe`；不向作者Conda环境安装额外包。

## 从初始会话复现五个面板

代码目录下的`教程/{a_11jb,b_11jb,c_9bjj,d_9bjj,e_9bjj}.md`各对应一个面板。每份教程包含从本例`initial.cxs`开始的一次复制命令、逐步解释、实际模型sample_index与sdf_index、原RMSD及材料来源表。长期`native/tutorials/`中的CXS直接打开即显示对应论文视角，MRC引用始终位于D盘长期材料目录。

| 面板 | 教程 | 最终会话 |
|---|---|---|
| a：11JB全景 | [逐步调节](教程/a_11jb.md) | [a_view.cxs](../../output/actual-small-molecule-cases/native/tutorials/a_view.cxs) |
| b：AR6局部 | [逐步调节](教程/b_11jb.md) | [b_view.cxs](../../output/actual-small-molecule-cases/native/tutorials/b_view.cxs) |
| c：9BJJ全景 | [逐步调节](教程/c_9bjj.md) | [c_view.cxs](../../output/actual-small-molecule-cases/native/tutorials/c_view.cxs) |
| d：ATP局部 | [逐步调节](教程/d_9bjj.md) | [d_view.cxs](../../output/actual-small-molecule-cases/native/tutorials/d_view.cxs) |
| e：A1AP0局部 | [逐步调节](教程/e_9bjj.md) | [e_view.cxs](../../output/actual-small-molecule-cases/native/tutorials/e_view.cxs) |

`teach.py --build-root <本轮目录> --output-root 画图/画图代码/e2e/output/actual-small-molecule-cases --teaching-root 画图/画图代码/e2e/visualization/actual-small-molecule-cases/教程`从本次原生CXC和相机日志生成教学。它只恢复官方相机矩阵，不移动结构。随后通过同一个`run_chimerax.ps1`执行`native/tutorials/tutorials_all.py`，实际从initial逐面板复现并保存新的PNG、CXS、状态与日志；完成后对照本轮`panels.json`核查可见构象和blob集合。

`native/tutorials/reopened/reopen_all.py`只打开刚保存的五个最终CXS，查询状态、相机、绝对比例并导图，不执行reset或改变显隐的命令。此项检查用于确认会话打开即可得到论文视角，不能用重新执行完整CXC代替。逐姿态CSV明确区分原构象池的`sdf_index`与抽出单构象文件中的记录0，并链接本例原件的本地和服务器路径。
