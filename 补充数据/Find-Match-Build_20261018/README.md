# Find、预测区域对接与端到端评价的补充数据

本目录保存截至2026-10-17已完成并验收的统计与元数据，供作者重新选图、重排正文或改变展示形式时使用，不需要再次运行模型。科学依据是逐blob结果、原实例类别、首次成功事件、来源清单和对应代码版本；正文、PPT及Word只是这些事实的展示，均可继续修改。

这次归档复制140个既有文件，合计13,011,026字节；没有重新推理、重新评价或操作服务器作业。完整姿态、概率图和全部候选轨迹仍位于原服务器统一目录。本目录没有把这些大型文件冒充为已经全部纳入Git。逐文件原位置、字节数和SHA-256见`provenance/source_manifest.json`；`SHA256SUMS`同时覆盖本目录归档文件及这份说明。目录内`.gitattributes`禁止换行转换，使Git中的副本也保留原始字节及来源散列。

## 目录与入口

以下是同一物理目录，分开列出科学数据和来源、历史与验收材料。

```text
## <科学产物>
补充数据/Find-Match-Build_20261018/
├─ metadata/
│  ├─ figure_data/
│  │  ├─ data.json                    # 29个完成度面板，以及GT/CA2各自的共同命中姿态配对
│  │  ├─ paired_pose.csv              # 全部235+230条配对，缺失RMSD留空
│  │  └─ summary.json                 # 配对摘要及固定相对候选数下的完成度
│  ├─ stage1_all_small/
│  │  ├─ panels.json                  # Stage1全部小分子的三个面板：94 PDB、821实例
│  │  └─ summary.json                 # 三个面板的分母、全候选计数与宏平均
│  ├─ pipeline/{GT,CA2,Emap2lig}/
│  │  ├─ docking_results.jsonl        # 每个合格blob的原排名姿态结果及成功判定
│  │  ├─ completion.json              # 原评价入口输出的逐PDB事件、曲线与分布
│  │  └─ summary.json                 # 原评价入口的全部候选用尽后统计
│  └─ emap_original/
│     ├─ find_hit_subset.jsonl        # 最初243个Emap2lig-Find命中实例及Build输入
│     ├─ find_hit_summary.json        # 对完整446实例的Find覆盖命中数
│     ├─ build_occurrences.jsonl      # 243实例、原评分顺序的逐姿态距离与CIF来源
│     ├─ build_summary.json           # 原243分母的Build成功计数
│     └─ pocket_comparison.json       # 8条真实位点C0/E结果的旧同子集比较
│
## <其他文件>
补充数据/Find-Match-Build_20261018/
├─ metadata/emap_original/
│  ├─ build_status.jsonl              # 原运行状态与实际输出目录（运行记录）
│  └─ SHA256SUMS                      # 原Emap2lig结果副本的散列（来源证据）
├─ provenance/
│  ├─ source_manifest.json            # 140个副本到原文件的映射（来源证据）
│  ├─ git_endpoints.json              # 各仓库提交和关键代码散列（来源证据）
│  ├─ configs/{GT,CA2,Emap2lig}.yml    # 已提交正式配置的快照（配置证据）
│  ├─ find/{inventory.json,identities.jsonl,sources.json}
│  │                                  # 全配体轴、Stage3身份轴及182份原Find文件来源（来源证据）
│  └─ stage1_all_small/
│     ├─ occurrences/<pdb>.jsonl       # 94份原实例类别文件，含范围外类别（来源证据）
│     ├─ sources.json                 # 94份文件的服务器路径与原散列（来源证据）
│     └─ provenance.json              # Stage1统计、完整Find字段容器等来源（来源证据）
├─ reference_logs/{AdaLigand,Emap2lig}/
│                                    # 7份已提交历史日志，不改写旧状态（执行记录快照）
├─ evidence/
│  ├─ archive-integrity.json           # 本次复制、分母和作者修改保护的核对（归档验收）
│  ├─ pipeline/git-equivalence.json   # 实现线与学习线的端点等价记录（验收证据）
│  ├─ figures_20261016/               # 10月16日图文输出结构与散列（历史验收证据）
│  └─ fig4_20261017/                  # 范围、原结果保护、合成样例及版面检查（历史验收证据）
└─ SHA256SUMS                         # 本归档的逐文件SHA-256（归档校验）
```

完整前因后果和接续边界见[本轮handoff](../../CLAUDE/memory/handoffs/2026-10-18-supplemental-find-build-e2e.md)。

## 三套目标范围

| 数据范围 | PDB数 | 实例数 | 用途 |
|---|---:|---:|---|
| 全配体Find | 179 | 2,502 | 全类别区域检出，不要求身份或姿态 |
| Stage1全部小分子 | 94 | 821 | 小分子区域检出，不限制残基数和原子完整性 |
| Stage3完整小分子 | 77 | 446 | 单残基、含碳、无缺失重原子的对接及相应端到端视图 |

三套分母不能互换。`find_small`是历史Stage3的77／446视图；论文内部`find_stage1_small`是94／821视图，不是AdaLigand新增的运行选项。唯一对应先在全部真实配体中按双向覆盖均不低于0.3、几何均值最大确定，再判断所属范围；不能过滤类别后重新选择对应。

## 逐blob姿态与原始Build记录

### `metadata/pipeline/<domain>/docking_results.jsonl`

GT、CA2、Emap2lig分别有304、293、243条记录。键为`(pdb_id, source_blob_index)`；`matched_occurrence_id`是在该PDB中的真实实例编号，不能和blob编号混用。三个条件的这批记录各自也具有唯一的`(pdb_id, matched_occurrence_id)`，可以连接共同命中实例。

例如GT的真实首条记录是`pdb_id="11jb"`、`source_blob_index=0`、`matched_occurrence_id=64`、`status="success"`、`top1_sample_index=9`。`output_dir`指向原逐blob目录；`pose_min_rmsd_A`的`"1"`、`"5"`、`"50"`分别是原模型排名前1、5、50姿态的最低有效重原子RMSD，单位Å。例如该记录的`"1"=0.7976016427672366`。距离不做刚体叠合；`null`表示没有有效距离。

`success["2.0"]["1"]`等字段是严格小于阈值的布尔值；等于2 Å或3 Å不算成功，距离为`null`也为`false`。PocketXMol按原self-ranking选择Top-1，Emap2lig按原`consistency_iou`选择Top-1；真实距离不参与排序。

完整50个姿态及置信度不在本文件中，沿`output_dir`读取服务器的`result.json`、`candidates.json`、`poses.sdf`、`confidence.npz`、`scientific_input.json`、`ranking.json`或原Emap2lig CIF／评分文件。

### `metadata/emap_original/`

这组文件对应2026-09-29的243实例实验，不等同于后来两种Find共同命中的公平比较。`find_hit_subset.jsonl`保留精确`prepared_smiles`、原生`blob_path`、Find排名以及体素／重原子数比筛选状态。`build_occurrences.jsonl`的`poses`保存按`consistency_iou`降序的50个姿态、`rmsd_A`与原CIF路径；`top1_rmsd_A`、`top5_rmsd_A`和`oracle_rmsd_A`分别对应Top-1、Top-5和best-of-50。

六个`build_filter_failed`实例为`9llg/3`、`9lw1/2`、`9o8p/0`、`9q05/4`、`9ui6/5`、`9uwi/3`。它们的`poses=[]`、距离为`null`，仍保留在243的成功率分母中。旧237实例距离分布只使用已有有效距离，不制造替代值。

`pocket_comparison.json`保存official／local_cov × GT／CA2 × C0／E八条旧结果。每项有`source`、`denominator=243`、六项阈值成功数和逐实例`occurrences`。这些PocketXMol输入使用真实中心或真实包络，不能替代预测blob引导的公平对接数据。

## 完成度、共同样本与绘图数据

### `metadata/figure_data/data.json`

`panels`有29项：原管线24项、Emap2lig全配体与Stage3 Find-only两项、Stage1全部小分子三项。`pairs.GT`和`pairs.CA2`分别保留235、230个共同命中实例。

`pairs.<domain>.all_rows`中每条以`pdb_id`和`occurrence_id`连接两模型，`tuned_blob`与`emap_blob`保留各自原区域编号。`tuned_top1`、`tuned_best`、`emap_top1`、`emap_best`都是Å单位距离，缺失为`null`。`numeric_rows`只保留四个距离均有效的配对，GT231、CA2228条，用于距离分布与中位数；`statistics.*.success_denominator`仍是235／230。不能把231／228作为成功率分母。

`paired_pose.csv`保留235+230=465条全部共同实例，不删除失败；CSV空单元格对应JSON的`null`。`summary.json`中的`pairs`保留同一配对摘要，`budgets[panel_id]["100"]`等保留固定相对候选数下的PDB等权均值和中位数。

### `metadata/pipeline/<domain>/completion.json`与Stage1 `panels.json`

它们都以`panels`列表保存相同完成度字典。`id`标识具体条件，例如`assume_GT_pose1_rmsd3.0`；`scope`区分`find_full`、`find_small`、`assume`、`actual`，新增Stage1文件还使用`find_stage1_small`。`pose_limit=1/50`和`threshold_A=2.0/3.0`指定姿态与阈值，纯Find二者为`null`。

`success_events[pdb_id]`保存`occurrence_id`及首次成功序号`first_success_attempt`。同一实例只计一次；重复blob仍保留候选位置。例如`{"occurrence_id":7,"first_success_attempt":3}`表示该PDB的实例7在第三次纳入统计的候选处首次成功，这是字段格式示例，不是正式新增观测。

`distributions["100"]`等列表对每个PDB保存`target_count`、`attempt_budget`、`success_count`和`completion`。设该PDB真实目标数为$N$，相对数量为$\rho$，则允许考察$\lfloor\rho N\rfloor$个计入该视图的候选，完成度为成功的不同实例数除以$N$。`curve.budget_numerator/denominator`保存精确事件比值，`budget_percent/mean/median`与之逐位置对齐；均值是PDB等权，不是实例合并后的微平均。零候选和零成功PDB保留。

`all_candidates_final`统计完整候选用尽后的成功，含300%以后的事件；300%只是既有图示范围，20也不是候选尝试上界。背景和范围外候选如何进入尝试序号，见handoff中的科学契约。原始顺序与Gaussian备选排名保存在服务器扩展`evaluation.json`，不能仅靠曲线还原全部失败候选。

## 事实来源和版本

`provenance/source_manifest.json`逐项记录`file`、`bytes`、`sha256`、原`source`，必要时还有`server_source`或来源`git_commit`。例如`metadata/pipeline/GT/docking_results.jsonl`直接追溯到`/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/GT/docking_results.jsonl`。

`provenance/git_endpoints.json`记录交接时六个仓库的HEAD及关键已提交代码SHA-256。AdaLigand的正式运行版本还由历史日志中的不可变release确定；不能把作者后续的注释修改或当前其他仓库HEAD误称为当时执行的release。配置副本只保留已经提交的版本，不纳入作者暂存工作。

`reference_logs/`保留两批实验的原因、运行命令、release、launch和验收来源，历史日志中的早期2×2排布、77／446的旧Find-small图范围及页数是当时记录；后来的Stage1纠偏见本次handoff，不能把旧历史叙述覆盖为现行科学范围。

本目录`evidence/`是历史验收副本，不代表作者2026-10-18工作区PPT或稿件已经重新编译。重新展示时直接读取上述元数据；绘图、PPT编辑和Word编译入口见[handoff](../../CLAUDE/memory/handoffs/2026-10-18-supplemental-find-build-e2e.md)。
