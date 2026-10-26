# Stage 1 全局到局部案例

本目录准备 9BJJ 主案例和 9WUP 备选：完整 map 的真实配体区域与全部预测、受体上的误报，以及配体实例附近的局部形状。这里保存实际数据转换和 ChimeraX 原生命令，不建设额外交互界面。本轮结果尚未写入正式 PPT 或论文。

先读[病例依据](病例依据.md)，再按[手动调整教程](手动调整教程.md)打开初始化会话。模型编号在两个病例中完全一致。

## 文件与阅读顺序

```text
stage1-global-local/
├─ sources.json            七个已有完整 map 的冻结来源
├─ screen_cases.py         全候选、冻结匹配、受体距离与当前论文统计核对
├─ cases.json              两个病例的 occurrence、原生 blob 与起始视角
├─ prepare_assets.py       MRC、配体和受体 CIF；不设置颜色或相机
├─ render_scene.py         ChimeraX 内执行，保存原生命令、命名视角、PNG 和 CXS
├─ rebuild.ps1             从冻结输入完整重建到一个新 temp 目录
├─ 病例依据.md              选择理由、全部候选数量和局部身份
└─ 手动调整教程.md          可逐条输入的命令与参数解释

../../output/stage1-global-local/
├─ source_audit.json        98 件输入与原始服务器来源清单的散列核对
├─ screening/               七病例全部选中 blob 的 CSV/JSON 与 21 组正文口径核对
├─ prepared/<pdb>/          完整密度、各掩码、受体/配体 CIF、evidence.json
│  └─ my_sessions/          作者个人保存位置；重建脚本不写此处
└─ initial/<pdb>/           本轮初始化会话、预览、原生命令与执行报告
```

`initial` 是本轮交付快照。以后重建写新的 `temp` 目录，不能覆盖这里或作者会话。模型、颜色、透明度、相机和显隐保存于普通 `.cxs` 文件，地图通过 `includeMaps true` 嵌入，可离线重开。三维场景在 ChimeraX 内继续编辑。

## 来源、判定和坐标

七病例只使用已有本地完整冻结输入，源地址和原始 SHA-256 在 `source_audit.json`。直接来源包含 `data/{exp.npy,exp.npz,ligand_area.npz,occurrences.jsonl,ligand_coords.npz,receptor_tokens.npz,<pdb>.cif}`、`cryo/receptor_tokens.npz` 及 `cryo/real/emap` 各自的 `blobs.npz`、`evaluation.npz`。共享的是旧 `stage1-fourcase-main` 的冻结原件，本目录不执行其带顶层副作用的转换脚本，也不读取旧截图。

CA2/GT 来自 Find_1、held_out_test_0、F2_blobs 和 `f2_centered_gaussian_macro_selected`；Emap2lig 来自 `official_find_li/held_out_test_0` 的 mapped official blobs 与逐 PDB evaluation。`source_blob_index` 连接评价行与原生 blob，不能把评价行号当 blob 编号。`occurrence_id` 连接真值实例与 intersections 列。

全部预测严格为 `candidate_selected`；实例 TP/FP 读取 `coverage_thresholds=0.3` 对应的 `one_to_one_match_offsets` 和 `one_to_one_match_pred_index`。`coverage_pred_hit_mask` 另记是否存在满足原评价规则的真值，不将其当成一对一 TP。选定的两处受体上误报、两处远处误报均与所有真值零交集。

空间筛查使用沉积受体重原子。最近距离为每个预测体素中心到最近受体原子的距离；“远处”汇总使用最小距离 >8 Å，展示候选在零真值交集且最小距离 >10 Å 的候选中按原始分数最高选择。1.5 Å 邻近比例描述体素中心与原子位置，不等于范德华体积交集或新的匹配标准。局部病例在有真实交集的候选中按 Dice 选该实例的最佳候选。

`screen_cases.py` 对七病例的每个选中 blob 核对体素数及全部实例交集，并将七病例 × 三条件的 P/R/Dice 与当前 `stage1-main-sixpanel/v5/data/plot_data.json` 的 full cohort 逐项对齐。候选筛查范围是已有七个完整 map，不是重新评测全部 179 个 PDB。

体素索引是 ZYX，原子坐标是 XYZ Å。体素中心为 `corner_origin_xyz + (index_xyz+0.5)*spacing_xyz`；MRC origin 写首体素中心。局部裁零同步平移 origin，不改变非零体素位置。二值掩码统一 0.5 等值面、step 1、关闭表面平滑。密度使用原 `contour_canonical`。受体 CIF 来自推理 token，链 C<n> 与残基数字是 token 编号；只有配体 CIF 的 auth 链/残基用于报告沉积身份。

## 重建

在仓库根 PowerShell 运行，输出路径必须尚不存在：

```powershell
& '画图/画图代码/stage1/visualization/stage1-global-local/rebuild.ps1' -OutputDirectory "$PWD/temp/stage1_cases_rebuild_01"
```

依赖为 `D:/Anaconda/python.exe` 中的 numpy、scipy、mrcfile、Biopython，以及 `D:/ChimeraX 1.10.1/bin/ChimeraX.exe`。原生进程调用仅共用 `转换工具/ops/rebuild_support/run_chimerax.ps1`，病例选择和渲染逻辑在本目录。每病例的 `report.json` 必须 `success=true`，有 18 个顶层模型和三个命名视角；不能只凭进程退出码判断成功。

重建时 Anaconda 和 ChimeraX 共用 `rebuild_support/sitecustomize.py` 的文件审计，禁止读取旧 temp 或改写本次目录外的冻结输入。PowerShell 退出本轮构建时恢复原环境变量，保护不会延续到作者后续操作。冻结的 `all_native_commands.cxc` 保存当次真实路径，仅作执行记录；再次重建用上面的正式入口。

本轮完整重建和离线重开验证见[执行记录](../../../../../talk/stage1_visualization_20261025/执行记录.md)。追溯入口为[可视化追溯](../图表追溯.md)的 `stage1-global-local-case-preparation` 条目。
