# 总览图的三种拓扑身份

本目录修改作者总览图第13页。三个身份分别为无环的 geraniol、单环的 ibuprofen 和双环的 naproxen。三维结构由有效 SMILES 生成；它们在受体中的放置是流程示意，不是实际对接、已知结合或新的实验结果。受体、密度、五个候选区域和版式继承作者第13页。

## 生成顺序

1. `prepare.py` 生成规范 SMILES、环数、游离构象和四份位点 SDF。作者当前编号 B1/B3 指向绿色身份，B2 指向黄色身份，B5 指向红色身份，B4 被排除。
2. `render_identities.py` 在 PyMOL 内渲染三个身份的透明 PNG，并保存 PSE；每个分子全部原子使用一种材质，保留三维光照。
3. `render_poses.py` 在 ChimeraX 原会话中替换四个配体，保留 Fig1 相机、55%透明受体和密度网格，输出 `poses.png` 和 `topology.cxs`。
4. `assemble.py` 只更换第13页的三个单行 SMILES、四张图片、受影响图注和定位批注。图片关系独立，前12页和原共享媒体逐字节保留。

冻结输入位于 `../../output/overview-topology-20261101/source/`：`author-before.pptx` 为修改前13页，`baseline.cxs` 为旧原生三维场景，`scene-before.json` 为原四个位点坐标。`author-final.pptx` 保存完成后的可编辑原件，供标准 `author_native` 入口恢复。所有输出写入当次 `FIGURE_BUILD_ROOT`，旧 temp 可整体清空。

从仓库根运行以下命令。`ops/rebuild.py` 设置新的 `FIGURE_BUILD_ROOT`，配置固定依赖目录和旧 temp 屏蔽，按上述四步顺序生成候选。它不覆盖正式 PPT。

```powershell
D:/Anaconda/python.exe -X utf8 -B 画图/画图代码/e2e/visualization/overview-topology-20261101/ops/rebuild.py --build-root temp/overview-topology-new-run
```

正式发布时只替换第13页的包成员，并核对作者是否并发保存。当前编辑资产在 `../../output/overview-topology-20261101/delivery/`：`topology.cxs` 为打开即全局的 ChimeraX 会话，`preview.png` 为当前整图，`scene.json` 为三种身份与四个构象的坐标。

新会话中 #1 为受体，#2/#3 为绿色 B1/B3，#4 为黄色 B2，#5 为红色 B5，#6 为密度。其余编辑方法沿用原 [ChimeraX 详细教程](../../../../总览图_ChimeraX/README.md)，但以这里的编号为准。输入 `transparency #1 55 target c` 调整受体透明度；`turn y 10` 旋转全局；`move x 1 models #2` 只移动 B1。`windowsize 1200 1500` 后执行 `view Fig1` 可恢复图中视角与画幅。需要记录自己调整后的位置时，先执行 `view name MyEdit`，再另存编辑会话。

完成的作者示意图重开入口：

```powershell
D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure fig-overview-topology
```

## 构象字段

`scene.json` 的 `identities` 每项包含 `id`、完整规范 `smiles`、图中截短的 `display_smiles`、`color`、整数 `rings`、环原子索引 `ring_atoms`、重原子 `elements`、同轴 `atom_names`、键表 `bonds` 和 `(N,3)` 的 `ideal_xyz`。`ring_atoms` 用于单环正面定向，索引同一重原子轴。`bonds` 的前三列为起点原子索引、终点索引及键阶；`1.5` 表示芳香键。`bound_poses` 每项包含作者 `blob` 编号、指向上述 `id` 的 `identity` 和 `(N,3)` 的 `xyz`。坐标均为 XYZ、Å；原子轴与规范 SMILES 重新解析后的顺序一致。

`ideal_bound_best_rmsd_A` 为游离和位点示意构象在最优刚性对齐后的重原子 RMSD，用于确认内部构象差异；不作为模型性能指标。三个身份环数必须为0、1、2，每份位点 SDF 的分子图须与对应完整 SMILES 一致。显示省略号不属于实际 SMILES 输入。
