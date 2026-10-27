> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Stage3 构象案例图

显式 EMDB level 条件的病例资产位于 `stage3/output/stage3-cases-main/explicit_emdb_level/`。设置 `FIGURE_SOURCE_ROOT` 为该绝对路径后，以下同一套测量、几何与绘图程序读取新条件；不设置时仍读取原无 level 资产。新条件的 `case_selection.json` 定义两组各五个候选与各三个正文主选，所有新输出写该条件的 `regenerated/`，正式 PPT 由作者批准的追加页流程更新。

新条件 `assets/<pdb>_<occurrence>/` 每例保存 `arrays.npz`、`metadata.json` 和从新运行原评分第一名取得的 `build_top1.cif`。NPZ 字段、世界坐标、原地图推荐阈值、密度覆盖比例 D 与受体碰撞定义沿用下文；元数据新增 `condition="explicit_emdb_level"` 和 `source_files`，后者按服务器原路径保存 `size` 字节数及 `sha256`，如原 CIF、`LIG.npz`、两种 PocketXMol 的 SDF 和受体／地图元数据。`source_map_sha256` 是原完整地图的已冻结身份，不重新散列整个地图。Build CIF 按该次 `LIG.npz.atom_names` 对齐重原子；两种 PocketXMol 仍为 GT 受体、C0 口袋、原评分 Top-1。C0 使用沉积配体中心定义口袋，不是 Find 预测 blob 的中心。

`case_selection.json` 的 `density`、`clash` 为各五个 `[pdb_id,occurrence_id]`，如 `["9q16",0]`；`main_density`、`main_clash` 为其中各三个主选。`screen.json` 保存 181 个满足 DG RMSD <1.5 Å 且低于新 Build 的原指标候选，`shortlist.json` 保存按两类 RMSD 差与原主图优先取得的 31 个实例；`screening/assets/` 与 `screening/case_metrics.json` 保留这 31 例的原件和同定义测量。`selected_case_metrics.json/.csv` 保存十例选择、正文标记以及三种预测的 RMSD、密度比例和碰撞计数；`source_sha256.json` 保存十例资产文件的大小和散列。十例均满足 DG 的 RMSD 最低、Clash 为 0、D 不低于另外两种方法；9WQ3/5 的 D 与 Build 并列。

新条件重建使用下面相同入口，不新增模型推理或绘图后端。`FIGURE_RENDER_ROOT` 可显式指定本次临时生成目录；省略时为该 `FIGURE_SOURCE_ROOT` 下的 `regenerated/`。`FIGURE_BUILD_ROOT` 仅指定候选 PPT 的临时装配位置，不改变科学输入。

```powershell
$env:FIGURE_SOURCE_ROOT=(Resolve-Path '画图/画图代码/stage3/output/stage3-cases-main/explicit_emdb_level').Path
python -X utf8 -B 画图/画图代码/stage3/visualization/stage3-cases-main/measure_cases.py
python -X utf8 -B 画图/画图代码/stage3/visualization/stage3-cases-main/make_geometry.py
python -X utf8 -B 画图/画图代码/stage3/visualization/stage3-cases-main/render_figure.py
```

Node 装配仍使用 `build_deck.mjs`，从同一 `FIGURE_SOURCE_ROOT/captions.json` 读取当前作者主图备注的最小修订副本，生成 `stage3-cases-main` 六例主图和 `stage3-cases-density`／`stage3-cases-clash` 两张各五例候选页。输出画布维持 980×1256 布局像素，与现有正式 PPT 相同。没有整面板位图，配体、受体、网格和碰撞线继续是可编辑原生图形。

## 原无 level 模板与历史记录

以下保留原无 level 版本的病例、资产与发布记录；新条件以本文件开头的独立目录和 `case_selection.json` 为准。

主图比较六个测试实例的原排序 Top-1，三例说明官方 PocketXMol 的密度偏离，三例说明 Emap2lig-Build 的受体碰撞。PPT 第四页依次保留 9LLG、9LFA、9BJJ、30GA 四个备选，与主图六例合计十个不重复实例。正文只引用六例主图；这些案例用于解释结构误差，不代替图 7、图 8 的总体统计。

当前重绘按 `measure_cases.py → make_geometry.py → render_figure.py` 顺序执行，冻结科学输入位于 `stage3/output/stage3-cases-main/assets/`；新 `case_metrics.json`、`cases.json`、`geometry.json`、`deck_layout.json` 和四页图稿全部写入同目录的 `regenerated/`，不覆盖原留档。原始指标和显示几何均已与新生成值完整比较一致，来源见[阶段追溯](../图表追溯.md)。取数与筛选入口在 `source_tools/`，默认离线绘图不访问服务器。

## 成品与来源

- [stage3可视化.pptx](../../../../stage3可视化.pptx)：四页分别为主图、三例密度偏离、三例受体碰撞、四例备选。图名是各页 `@@stage3-cases-*` 批注，图注在备注中。分子键、原子、密度网格、受体、碰撞线、比例尺和文字均为 PowerPoint 原生图形，无整面板位图。
- [cases.json](../../output/stage3-cases-main/cases.json)：十个实例的身份、四种构象指标、来源与显示视角。`official`、`tuned`、`build` 是预测，`gt` 是沉积参考。
- [case_metrics.csv](../../output/stage3-cases-main/case_metrics.csv)：三种预测的 RMSD、密度覆盖百分比、碰撞原子对数、碰撞配体原子数、最短受体距离，按 PDB/occurrence/方法对齐。
- `画图/画图代码/stage3/output/stage3-cases-main/assets/<PDB>_<occurrence>/arrays.npz`：冻结的三维坐标及局部实验密度；同目录 `metadata.json` 保存精确 SMILES、候选编号、原评价值和服务器来源。`source_sha256.json` 保存这二十个本地文件的 SHA-256。
- `geometry.json`：十例的统一显示投影，保存线段、原子圆形、视角、每 Å 像素数。`deck_layout.json` 保存四页的文字与图形位置，`captions.json` 保存图注。
- `stage3-cases-*.png/svg/pdf`：Python 预览、可编辑 SVG 与矢量 PDF。`*.powerpoint.png` 是 PowerPoint 实际导出预览。`*.alignment.json` 与 `*.pdf.collisions.json` 是面板对齐、文字遮挡核查报告。

数组字段：`gt/official/tuned/build` 为 `(N, 3)` 配体重原子世界 XYZ 坐标，单位 Å；`element` 为 `(N,)` 原子序数；`bonds` 为 `(B, 3)` 原子索引对及键级。`receptor_xyz` 为 `(R, 3)` 标准蛋白质/核酸重原子坐标，其他 `receptor_*` 字段按同一受体索引对齐。`density` 为 `(Z, Y, X)` 实验密度；`origin` 为裁取后的 XYZ 边界角点，`voxel_size` 为实际 XYZ 间距，体素中心为 `origin+(index_XYZ+0.5)*voxel_size`。`contour` 为源资产的 `contour_canonical` 推荐阈值。每例密度裁取范围覆盖参考与三种预测的联合包围盒并向外增加 9 Å；不依方法更换密度。

PocketXMol-official 对应 `official-SMILES/test/C0`，PocketXMol-tuned 对应 `local_cov-C-T0-RA/test/C0`，均使用真实受体。两者使用既有 `top1_sample_index`；Build 使用 `consistency_iou` 原排序首位，源路径为 `/storage/penghongen/Emap2lig/stage3_find_hit_build/`。各路径逐例保存在 `metadata.json.sources`。本任务只读获取冻结产物，没有新推理、重新排名或刚体叠合。

## 指标与取景

RMSD 直接读取既有重原子对称校正评价。D 是在每个预测重原子处三线性插值实验密度、再统计达到推荐阈值的比例；它不是 Q-score。Clash 沿用 PocketXMol 的距离严格小于 `0.75*(r_ligand+r_receptor)` 的重原子对定义；范德华半径已与服务器 RDKit `GetRvdw` 逐项核对。受体副本保留距四种构象联合原子集合 8 Å 内的标准受体原子，足以覆盖该阈值下全部碰撞。UNK、水及其他非标准受体类别不进入计数。

网格来自原实验密度在推荐阈值下的等值面，只显示距沉积配体重原子 2 Å 内的已有面片，不增加人为封口。受体背景使用距沉积配体 3.5 Å 内或任一方法涉及碰撞的残基，显示其中位于取景范围内的原子与键。三列共用取景、正交相机、网格和 5 Å 比例尺。PCA 仅确定显示方向，不用于计算 RMSD。视野边缘的背景线段作二维裁切。

受体使用橄榄绿色（`#7B8C55`，透明度 0.85），密度网格保持灰色。预测配体的全部原子及键统一使用方法颜色：官方 PocketXMol 为橙色、微调版为蓝色、Build 为紫色；沉积参考为青绿色，不再按元素另着色。红色仅表示实际碰撞的虚线接触及受体原子标记；Clash 为 0 的面板没有这些红色标记。

先依据冻结指标筛查 28 个实例，`screening_metrics.json` 保存筛查结果。主图取三个官方 RMSD 高、tuned RMSD 低且密度覆盖提高的例子，以及三个 Build 有碰撞、tuned 无碰撞且 RMSD 较低的例子。未将碰撞最多作为唯一选择标准，也未改变原候选排序。

| 用途 | PDB/occurrence | 配体与链/残基 |
|---|---|---|
| 密度偏离 | 9q16/0、9ub7/3、9r3d/0 | XG4 A:1201、Y01 A:701、IHP A:2401 |
| 受体碰撞 | 9u7j/2、9wup/2、9wq3/5 | GDU A:801、FAD A:1103、1SY G:401 |
| 备选密度偏离 | 9llg/2、9lfa/0 | CLR R:603、A1EJF A:401 |
| 备选受体碰撞 | 9bjj/16、30ga/7 | A1AP0 E:1001、ATP L:401 |

原主图中的 9bjj/16、30ga/7 现列入第四页 c/d，冻结来源、坐标及指标仍保存在十例资产包中。互换只改变展示位置，不改变任何模型候选、原排序或计算指标。

## 重绘与编译

离线测量与绘图使用本机 `D:/Anaconda/python.exe` 的 NumPy、SciPy、Matplotlib、scikit-image。以下是绘图命令，不是模型实验命令：

```powershell
D:/Anaconda/python.exe 画图/画图代码/stage3/visualization/stage3-cases-main/measure_cases.py
D:/Anaconda/python.exe 画图/画图代码/stage3/visualization/stage3-cases-main/make_geometry.py
D:/Anaconda/python.exe 画图/画图代码/stage3/visualization/stage3-cases-main/render_figure.py
```

`build_deck.mjs` 使用 bundled Node 的 `@oai/artifact-tool`，读取 `regenerated/deck_layout.json` 与冻结 `captions.json`，直接写入独立图名和备注，经过结构检查后把新候选保存到 `output/stage3-cases-main/regenerated/`。正式图注仍在作者PPT备注中维护；当前输入及命令见[阶段追溯](../图表追溯.md)。

旧 [publish_ppt.ps1](../../../archive/visualization/publication-history/stage3/stage3-cases-main/publish_ppt.ps1) 已归档，不作为当前调用入口。它会重复追加图名并覆盖正式PPT，不能用于更新作者当前图集。

正文编译命令：

```powershell
python md_to_word.py --output 论文草稿.nature.Stage3可视化.docx
python md_to_word_operation.py --output 论文草稿.operation.Stage3可视化.docx
```

2026-10-03 初版：已完成两类各三例主图、四个备选、正文与 PPT 图注；离线复算与筛查值逐项相同。四页对齐及 PDF 文字遮挡报告通过，最小 PDF 字号 7.41 pt。源代码预检查的唯一提示是没有 TIFF：本图为矢量线图，PDF/SVG 为矢量导出，600 dpi PNG 只作预览。初版 Nature Word 为 42 页、Operation Word 为 33 页，图分别位于第 22 页和第 17 页；两份 Word 均保留全部 13 张 PPT 引用和 209 个原生公式，Nature Word 回转恢复了本图的 PPT 引用。

2026-10-03 按作者确认修订：受体改为橄榄绿色，取消配体元素杂色，主图 d/e 从 9BJJ、30GA 换为第四页的 9U7J、9WUP，第四页案例及顺序保留。以作者当前 PPT 备注为底稿，仅替换案例名称及“受体为浅灰色”一词，其余图注逐字保留；正文只同步对应案例与数值。主图六例中 tuned 的 RMSD 均低于另外两种方法。二十个冻结来源文件的 SHA-256 均保持不变。

本次四页对齐、PDF 字号及文字遮挡核查通过；PPT 版式核查无越界对象，四页分别有 2364、1000、1375、1568 个原生图形，均没有位图面板。重新编译当前 Markdown 后，Nature Word 为 45 页，主图在第 24 页、图注在第 25 页；Operation Word 为 35 页，主图在第 18 页、图注在第 19 页。已核查全稿页面总览及新图、图注、对应正文页面；两份 Word 图注均与批准后的 PPT 备注逐字相同，保留 13 张 PPT 引用及 209 个原生公式。作者原稿、原 PPT 备注及旧 Word 备份位于 `temp/stage3_cases/revision_20261003/`，编译和页面核查产物位于 `temp/stage3_cases/word_nature/`、`word_operation/`。


2026-10-03 备用页互换：第四页 c/d 改为主图换下的 9BJJ–A1AP0、30GA–ATP，并同步该页备注；a/b、前三页及其备注保留。主图六例与第四页四例合计十个不同实例。已通过原生 PowerPoint 导出、版式、字号及文字遮挡检查。正文和 Word 未改动，本次无需重编译；副本及核查记录位于 `temp/stage3_cases/side_alternatives_20261003/`。
