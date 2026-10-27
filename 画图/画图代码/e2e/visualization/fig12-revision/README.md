# Fig1、Fig2 及共用备选组件

本目录在作者保存的原生 PPT 基底上落实两轮编号意见及后续布局意见。两份正式 PPT 均为四页，前三页只切换整图配色，第四页为内容相同的组件备选。Pocket 表示与配色解耦。原始节点、路径、分子坐标和模型首选顺序不因调版改变。

## 正式页与生成物

| 页码 | 总览图、方法图的共同职责 | 稳定图名后缀 |
|---|---|---|
| 1 | 默认：统一装饰文字，保留身份与特征颜色 | 无后缀 |
| 2 | 原有配色 | original |
| 3 | 进一步收敛中性色及装饰背景 | unified |
| 4 | 16例 pose、两处 Pocket 的三种表示、SMILES 组件 | components |

图名基干分别是 fig-overview_v3、fig-method-v9。前三页的方法图均使用2B口袋；切换局部表示时从第4页复制同类组件。作者基底在 source/ 完整保留，不另占正式页面。

~~~text
画图/
├─ 总览图.pptx
└─ Method总图.pptx
画图/画图代码/e2e/output/fig12-revision/
├─ source/
│  ├─ overview-author.pptx、method-author.pptx
│  ├─ Fig1-annotations.png、Fig2-annotations.png
│  ├─ Fig1-corrections.png、Fig2-corrections.png
│  ├─ layout-followup-1.png … layout-followup-5.png
│  ├─ source_manifest.json
│  ├─ candidate_cases.json
│  └─ rcsb/*.cif、*.cif.gz
└─ regenerated/
   ├─ render/poses/<病例>.png、*.pse
   ├─ render/pockets/{match,build}-{surface,atoms,cartoon}.png、*.pse
   ├─ render/method-output.png、*.pse
   ├─ render/render_manifest.json
   ├─ selection.json、variant_manifest.json
   ├─ native_component_operations.json、component-audit.json
   └─ receipt*.json
~~~

source_manifest.json 保存作者素材的原路径、冻结路径、散列，以及公开受体的下载地址。candidate_cases.json 是16个有序病例键；它连接 Stage3 原始冻结输入，不以文件名猜测配体。

运行目录由 FIGURE_BUILD_ROOT 指定。geometry.json、新增原生组件、裁边显示图、候选 PPT、PowerPoint 预览和检查报告均写入本次 temp。正式逻辑不读取其他 temp；regenerated/ 是生成留档。

## 冻结坐标、身份及对齐

每个病例连接 stage3/output/stage3-cases-main/screening/assets/<病例>/{arrays.npz,metadata.json}。arrays.tuned 为形状 (N,3)、单位 Å 的模型自评分首位坐标；element、bonds 沿同一原子轴保存元素和连接。metadata.metrics.tuned.sample_index 记录原采样下标，不按参考 RMSD 重挑。公开 CIF 仅补充沉积受体背景，渲染前与冻结口袋坐标核对。

采用的四个实例为9BJJ的 A1AP0（E:1001）、9LLG的 CLR（R:603）、30GA的 ATP（L:401）和9WUP的 FAD（A:1103）。主图不在图下添加病例文字，备选页通过实例标签及绿色边框定位。其余12例保留在同页，图形分别成组。

方法图输出来自9BJJ的 CryoAtom2 受体与 ATP（B:901）原首选构象。两处 Pocket 读取同一受体，但分别保留实际输入选择：Match 为冻结 Find blob 的10 Å包络，Build 为原 Find 质心的15 Å球。sticks 显示空腔附近的输入原子；外围 cartoon 只交代折叠。surface 为辅助显示。

render_manifest.json 的 pockets 字段记录角色、显示方式、输入原子数、显示的侧链原子数、相机和片段选择。cartoon 版隐藏配体及全部 sticks；方案1为 cartoon、sticks 与半透明 surface，2B关闭 surface。所有模式与方法图输出共用1500×1100画布及同一相机；selection.json 保存统一透明裁边矩形，避免切换组件时改变折叠尺度。

## 既有组件与本轮边界

Fig1 的9HJX背景、受体、原生 blob 及文字组件取自作者基底。B1、B2 对应同一身份；B2复用作者已有黄色 blob 网格并转为同一绿色，以区分轮廓，不重画网格。全局标签位于图内，灰色 B3 居中拒绝，黄色 B4、粉色 B5。身份顺序为黄、绿、拒绝、粉；五条匹配线均为直线并保留交叉。三个二维身份使用 CCO、Cc1ccccc1、CC(N)=O，输入列表另有 CC(=O)O。

Fig2 仅替换获认可的 density bank 图示，保留原预处理框、分隔、56 channels、embedding 邻域节点图及原有输入拓扑。Find 的预处理、网络和输出分别平移以分摊间距；Match 作为完整块平移，内部连接和布局不变。三个 Find 预览使用相同组件框并保留图像长宽比；全局四个 blob 随全局密度等比变换。a、b左右边界相同，c与整体上下边界对齐。Build 使用4条 SMILES、一个三点省略号及 Cc1ccccc1 选中框，上下保留间距。

字号调整只作用于被缩放的文字组件及少量原始小字；保留字体、符号、上下标关系和节点含义。原色页保留全部既有色值；text 档只统一装饰文字。unified 档将 Fig1 的非身份结构背景转为中性灰，并收敛 Fig2 的装饰背景，不改变身份、特征矩阵、模态颜色和真实结构图片。

## 重建及检查

从仓库根运行：

~~~powershell
D:/Anaconda/python.exe -X utf8 -B 转换工具/ops/rebuild_figures.py --figure fig-overview_v3 --figure fig-method-v9
~~~

顺序为 prepare_geometry.py、render_structures.py、build_components.mjs、assemble.py。几何准备及装配使用项目 Python，原生结构渲染使用 D:/Pymol/python.exe，JavaScript 使用 Codex 固定 Node 与 Artifact Tool。Python、PyMOL及 Node 均屏蔽旧 temp；重建器不覆盖正式 PPT。

ops/audit_components.py 比较实际 OOXML：原节点与路径保留、Match 块内布局、全局编号、直线交叉、三幅预览尺寸、面板对齐、两份组件页一致性及真实候选数量。ops/check_revision.py 用本机 PowerPoint 导出全部页面，并按正文6.27英寸宽度和转换器相同裁边规则检查字体、碰撞与输出对齐。原生三维背景内部的 B 标签为作者指定叠加，原始碰撞报告与逐项审读理由同时保留，不把它们改成外置引线。

finalize.mjs 对候选执行文件包、页面几何、参考字体及 Artifact Tool 导入检查，仅将通过的副本写入本次 published/。正式发布前再次核对作者基底，来源批注由[追溯记录](../图表追溯.md)同步；正文只切换对应稳定图名。
