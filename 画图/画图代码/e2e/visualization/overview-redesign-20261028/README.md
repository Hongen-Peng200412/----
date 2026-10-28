# 总览图独立组件与 ChimeraX 编辑包

本目录从冻结作者基底和 RCSB 原子坐标生成总览图备选页。三个左侧、五个右侧方案使用相同坐标与相机，可按原坐标直接复制组合。A/B 组使用密度表面，C 左侧与 D35/D55/D70 右侧配套使用密度网格；正文仍引用作者第 2 页 baseline。

## 主要产物

```text
画图/
├─ 总览图.pptx                         # 第 1、2 页保留作者版本，第 3–12 页为本轮备选
└─ 总览图_ChimeraX/                    # 可独立使用的三维编辑包
   ├─ A_完整受体.cxs                   # 完整 cartoon、密度与四个 pose，打开即全局画面
   ├─ B_局部剖切.cxs                   # 隐藏遮挡配体的前景 ribbon；全部原子仍在
   ├─ C_密度网格.cxs                   # 密度网格、完整受体和四个 pose
   ├─ D35_完整受体半透明.cxs            # 完整受体为 35% 透明，密度为浅灰疏网格
   ├─ D55_完整受体半透明.cxs            # 完整受体为 55% 透明，推荐起始版本
   ├─ D70_完整受体半透明.cxs            # 完整受体为 70% 透明的对照
   ├─ README.md                        # 命令、按钮、鼠标编辑与 PPT 替换教程
   ├─ 同步导出.py                       # 从当前世界坐标同步示意密度、blob 与四张主图
   ├─ assets/
   │  ├─ scene.json                    # 同一原子轴的化学身份、键、游离及结合 XYZ
   │  ├─ receptor.pdb                  # 原始四聚体蛋白重原子
   │  ├─ B1.sdf、B2.sdf、B4.sdf、B5.sdf # 四个结合配体及其真实键表
   │  └─ native-manifest.json           # 相机、模型编号、投影与剖切残基
   └─ examples/                        # 三种表示及两个备选视角的原生导出
```

每次重建的候选、透明 PNG、PSE、CXS、PDF 和验证文件统一写入 `FIGURE_BUILD_ROOT` 指定的新 temp。`editing-package/` 是该次完整交付包，发布时复制到上面的正式目录。长期来源位于 `e2e/output/overview-redesign-20261028/source/`，不依赖 temp 中的旧图或源文件。

## PPT 页码

| 页码 | 内容 | 稳定图名 |
|---|---|---|
| 1 | 作者历史版本 | 原作者图名 |
| 2 | 作者 baseline | fig-overview_v3 |
| 3 | 左 A：按身份分组，两栏边框 | fig-overview-v4-left-a |
| 4 | 右 A：完整受体 cartoon | fig-overview-v4-right-a |
| 5 | 左 B：B1–B5 数字顺序，横向 SMILES | fig-overview-v4-left-b |
| 6 | 右 B：原生局部 ribbon 剖切 | fig-overview-v4-right-b |
| 7 | 左 A 与右 A 默认组合预览 | fig-overview-v4-preview |
| 8 | 左 C：55% 透明受体与密度疏网格 | fig-overview-v4-left-c |
| 9 | 右 D55：完整受体 55% 透明 | fig-overview-v4-right-d55 |
| 10 | 左 C 与右 D55 组合预览 | fig-overview-v4-preview-transparent |
| 11 | 右 D35：完整受体 35% 透明 | fig-overview-v4-right-d35 |
| 12 | 右 D70：完整受体 70% 透明 | fig-overview-v4-right-d70 |

左侧组合框为 `(0,0,647,360)` 点，右侧为 `(647,0,290.5,360)` 点。Candidate 与 Ligand poses 共用 177.6×222 点图片框，Input 密度与受体共用 72×90 点框；所有三维主图来自同一 1200×1500 像素画布。

## 身份、坐标与密度契约

`scene.json` 是 object。`identities` 是长度 3 的列表，每个分子保存规范立体 `smiles`、沿该 SMILES 重新解析后原子轴排列的 `elements`、CCD `atom_names`、`bonds` 和 `ideal_xyz`。例如 BTN 的 `bonds` 中 `[0,1,2.0]` 表示第 0、1 个重原子之间的双键；`ideal_xyz` 为 `(N,3)`、XYZ、单位 Å。`bound_poses` 是长度 4 的列表，`blob` 为 B1/B2/B4/B5，`identity` 连接同名身份，`xyz` 沿同一原子轴。每个 bound pose 的 3D 手性与 Input SMILES 相同。

受体为 1STP 生物学四聚体的 3604 个蛋白重原子，BTN 两个实例保留沉积坐标；DTB、IMI 从 3RDQ、2RTL 的供体链按序列对应 CA 叠合。场景表达示意混合占据，不是一个真实沉积复合物。B3 为构造的假阳性，没有 pose。所有密度为坐标高斯场：间距 0.7 Å，蛋白/配体合并地图的 sigma=1.8 Å，各 blob 的 sigma 由 prepare_scene.py 固定；数组为 ZYX，原点和间距为 XYZ。整体阈值 0.17，blob 阈值 0.20，均基于各自最大值归一化场。

`native/manifest.json` 保存各次主图的完整相机矩阵、场宽、统一画布及 B1–B5 投影中心。`cutaway_residues` 保存 B 版只隐藏 ribbon 的残基列表；分子原子坐标和数量不改变。

## 入口与验收

```powershell
D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure fig-overview-v4-preview-transparent
```

完整顺序为 `prepare_scene.py`、`render_native.py`（PyMOL）、`render_chimerax.py` 与 `render_transparent.py`（ChimeraX）、`assemble.py`（PowerPoint）、`package_delivery.py`。同一链生成全部十个备选图名；重建器只选择与补全目标图名，正式 PPT 只读。

默认沿用正式 PPT 的作者图注；只有本轮同时重写图注时才加 `--generated-captions`。原生 CXS 起始场宽为 128 Å，以便桌面横向窗口打开时显示全局；命名视图 Fig1 保存与 PNG/PPT 一致的瘦长画布相机与缩放。

`check_native.py` 在独立 ChimeraX 进程验证六份 CXS 的内嵌地图、模型显隐、4 个 pose 的坐标、教程命令，以及移动 B1 后整套同步导出和重新打开。验证时禁止读取外部 MRC。逐页预览及作者前两页保全检查由实际 PowerPoint 导出完成。

完整来源由[图表追溯](../图表追溯.md)中的五个 v4 条目维护；方案、实际验证与发布记录见[执行记录](../../../../../talk/overview_redesign_20261028/执行记录.md)。
