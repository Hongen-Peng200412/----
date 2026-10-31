# Match–Build 合图与消融图重建

本目录从已冻结的逐实例结果生成三张联图：`stage2-stage3-results` 为三行三列主结果图，`stage2-stage3-ablation-centre` 为两行两列正文消融图，`stage3-ablation-envelope` 为一行两列补充消融图。程序不重新训练、采样或评价候选构象。主图最后一行复用9WUP的FAD（A:1103）原生PPT视图，其余面板从数值输入重绘。

## 冻结输入和派生数据

下列目录均相对于论文仓库根目录。`output`保存可离线复现的冻结输入及数值快照；`temp`仅保存本次构建产生的文件，可整体清空。

```text
画图/画图代码/e2e/output/stage2-stage3-results/
├─ data.json                         # 全部绘图数组的冻结快照
├─ summary.json                      # 固定分母成功率、中位数及分位数快照
├─ source_manifest.json              # 各实际输入、来源版本和SHA256
└─ sources/
   ├─ 9WUP-case.pptx                 # 作者原PPT快照，保存可编辑分子与密度对象
   ├─ 9WUP-case.json                 # 9wup/2身份、三个视图条件和原始指标
   └─ nodensity/
      ├─ {GT,CA2}_{C0,E}.json        # 四份未经重写的原始occurrences.json
      ├─ manifest.json              # 四份原件的远端路径、字节数和SHA256
      ├─ CA2_acceptance_center.json  # Centre逐候选验收报告
      ├─ CA2_acceptance_envelope.json# Envelope逐候选验收报告
      └─ experiment_logs/            # 无密度实验总日志、Centre日志及Envelope日志快照
```

两组花括号展开为`GT_C0.json`、`CA2_C0.json`、`GT_E.json`、`CA2_E.json`四份文件。`C0`表示真实配体中心确定的标准Centre口袋，`E`表示标准Envelope口袋。GT为沉积受体，CA2为CryoAtom2重建受体。

### data.json

`prepare_data.py`写出该JSON；`plot.py`读取本次构建目录`data/data.json`，不直接依赖旧临时结果。根字段及其用途如下。

| 字段 | 内容和对齐关系 | 真实值示例 |
|---|---|---|
| `match.categories` | GT、CA2下的Overall、小分子、金属离子和糖类准确率；每项给出正确数、支持数及百分比 | `GT.overall = {"correct":1087,"total":1238,"accuracy_pct":87.80290791599354}` |
| `match.by_candidate_count` | 候选SMILES身份数为1、2、3、4、≥5时的分组结果；`correct`、`total`和`accuracy_pct`均为长度5的并列数组 | GT的Overall正确数为`[419,415,100,63,90]`，支持数为`[419,459,113,85,162]` |
| `match.ablation` | `strongest`、`voxel`、`density`、`pocket`四个Match变体在相同四类轴上的结果 | `GT.pocket.sugar`为`159/284` |
| `match.foreground_f1` | 仅供正文简要报告的前景分类指标，不用于绘图轴 | GT为`0.8604898828541001` |
| `main_build.keys` | 长度235的`[pdb_id, occurrence_id]`身份列表；实例编号沿用原冻结清单 | 首项为`["11jb",0]` |
| `main_build.selected_blobs` | 三种方法原来选定的blob编号，数组与`main_build.keys`逐项对齐；不同方法不要求使用相同几何区域 | 字典键为`GT`、`CA2`、`Emap2lig` |
| `main_build.series` | 各方法的`top1`、`top5`、`best50`连续RMSD数组，每个数组长度235，单位Å | GT的Top-1中位数为`0.8677762817846789` Å |
| `main_build.win_pct` | 未截断配对RMSD中，DG严格小于Emap2lig的实例百分比 | GT的Top-1为`88.93617021276596` |
| `ablation` | `C0/E → GT/CA2 → official/nodensity/DG`嵌套的标准消融；每组含长度446的身份列表及三个姿态范围的RMSD数组 | `C0.GT.official.denominator = 446` |
| `source_paths` | 本次实际读取的仓库相对文件位置，连接原始输入和上述派生数组 | `emap_build`指向显式EMDB level的`build_occurrences.jsonl` |

隐藏肽类展示不改变Overall的原始支持集合。分组Overall由各类别正确数相加后除以支持数之和得到，不是类别准确率的平均值。雷达图只保留四个身份匹配轴，径向范围为40%–95%。

主Build集合取三种方法预测blob所对应配体身份的交集。Emap2lig输入先满足双向覆盖均不低于30%，并通过闭区间`[5,25]`的blob体素数／配体重原子数比例筛选。被该筛选剔除的blob不计作Build失败；独立Find评价保持其自身定义。连接身份后保留各方法原先选中的blob，不对三种几何掩码求交，也不按RMSD重新选区域。

标准消融固定保留446个实例。GT下原始PocketXMol有一项失败：`["9qkz",0]`的RMSD为`null`，不是0，也不补造数值。该实例仍在成功率分母中；中位数、箱线和小提琴使用445个有限数值。其他组均有446个有限数值。

### summary.json

该JSON由同次`prepare_data.py`计算，结构对应`main_build`和`ablation`各方法的三个姿态范围。每项含`denominator`、`valid_count`、`missing_count`、`q10/q25/median/q75/q85`、`success_counts`及`success_pct`。分位数和RMSD单位为Å；成功计数键`lt1/lt2/lt3/lt4`均使用严格小于阈值。

例如，`ablation.C0.GT.official.top1`的固定分母为446、有效值445、缺失值1；`success_counts.lt2 = 199`，对应成功率`44.61883408071749%`。箱体跨第25–75百分位，须端点直接使用第10及85百分位；不会把显示范围以外的RMSD删除后重算。

### source_manifest.json与sources/nodensity/manifest.json

前者登记Match冻结结果、两组预测blob Build结果、Emap2lig输入资格清单及Build结果、标准消融原件和日志证据。`path`为仓库相对位置，`bytes`为原文件字节数，`sha256`为原始字节散列。后者专门保存四份无密度原件在服务器上的绝对位置及原始散列，如`GT_C0`来自`/storage/penghongen/PocketXMol/sampling/B-C-T0-RA-SMILES/test/C0/occurrences.json`。日志快照保留检查点选择、实际源码release、原排序与实验条件。

### sources/9WUP-case.pptx与sources/9WUP-case.json

PPT快照来自作者`画图/stage3可视化.pptx`，本图只复制其中`9wup/2`、FAD、链A、残基1103的三个现有视图。JSON明确记录原PPT页、对象定位、视图次序、指标和比较条件。原始PocketXMol及DG使用沉积受体、标准Centre C0和原评分Top-1；Emap2lig使用显式EMDB推荐level条件及其原Top-1。该实例用于解释密度与受体约束的互补性，不改称235实例预测blob对照中的同条件病例。

## 构建流程与共享实现

| 文件 | 实际职责 | 主要输出 |
|---|---|---|
| `prepare_data.py` | 从明确的冻结原件重算身份对齐、完整RMSD数组和固定分母统计 | 指定输出目录中的`data.json`、`summary.json` |
| `plot.py` | Python后端绘制统计面板，保留病例视图位置，并将同源SVG几何转为可运输形状 | `results/ablation/envelope.{svg,pdf,png}`、`scenes.json`、`manifest.json`、`case_rects.json`和对齐报告 |
| `assemble.mjs` | 将Python生成的文本、曲线、柱形、箱线、小提琴逐组件运输为原生PPT对象；不重新计算科学统计 | `candidate.pptx` |
| `finish.py` | 注入9WUP原生病例视图，调用实际PowerPoint导出；仅操作本次候选 | `candidate.pdf`、`ppt_preview/`、`case_reuse_receipt.json` |
| `finalize.mjs` | 可选的PPT文件结构、Arial字体和Artifact Tool可导入性检查；不重绘图形 | `validated/stage2-stage3.pptx`、`presentation-validation.json` |

`plot.py`共享[SVG显示几何读取器](../find-build-shared/svg_shapes.py)；它不从该共享模块读取实验统计或改写成员资格。三张新图共同使用本目录计算与绘图实现，通过稳定图名区分面板选择。

病例复制由[case_reuse.py](../../visualization/stage2-stage3-results/case_reuse.py)完成，只读取上述长期冻结PPT。原生形状与文本保留可编辑性，视图使用整体等比缩放；病例坐标、姿态排序和评价指标不重算。长期代码及输入不依赖旧`temp`。

构建使用Python的NumPy、Matplotlib、SciPy、pywin32，以及固定安装的Node与`@oai/artifact-tool`。PowerPoint必须可用。PDF审计需要PyMuPDF，可通过`PYTHONPATH`读取仓库固定`.manuscript_deps/figure_runtime`，不能把临时目录中的包作为长期依赖。

从仓库根进行一次显式构建：

```powershell
$env:FIGURE_BUILD_ROOT = Join-Path (Get-Location) 'temp/stage23_rebuild'
python -X utf8 -B 画图/画图代码/e2e/calculate/stage2-stage3-results/prepare_data.py --repo-root . --output-dir "$env:FIGURE_BUILD_ROOT/data"
python -X utf8 -B 画图/画图代码/e2e/calculate/stage2-stage3-results/plot.py
node 画图/画图代码/e2e/calculate/stage2-stage3-results/assemble.mjs
python -X utf8 -B 画图/画图代码/e2e/calculate/stage2-stage3-results/finish.py
```

候选构建不会自行发布到作者正式PPT。完整重建登记、来源批注、正式PPT和验证状态由[计算追溯](../图表追溯.md)及[可视化追溯](../../visualization/图表追溯.md)维护。本README说明当前输入输出契约，不把生成文件存在视为已完成PDF碰撞检查、可编辑性核查或Word图注分页验收。


作者(v1)局部优化使用`refine_author_v1.py --output <本次temp候选.pptx>`。输入为独立冻结的作者5页PPT及原始统计`data.json`；它按冻结准确率重建b/c的0起始纵轴并完善第2/4页双语图注，其它作者对象与旧页面不改。程序输出候选和逐点数值/部件变更回执，不读取旧temp。
