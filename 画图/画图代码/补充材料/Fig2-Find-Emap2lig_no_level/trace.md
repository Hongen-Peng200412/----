# 补充 Fig2 的无level独立对照

本图对应[stage1结果.pptx](../../../PPT/stage1结果.pptx)中的`stage1-no-level-comparison-NO_LEVEL`. Emap2lig使用没有显式给定实验地图level的独立旧运行, GT/CA2仍使用原Find条件. 本图只重建Dice、0.3/0.5一对一PRAUC及两阈值的最终候选P/R, 不读取显式level结果、预算候选表或地图分辨率.

## 两个评估范围与原始编号

全配体范围是179个PDB、2502个真实实例; 小分子范围是94个PDB、821个真实小分子实例. 小分子PDB名单来自`/storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/provenance.json`的`cohort_pdb_ids`. 真实实例类别来自`/storage/penghongen/AdaLigand/Ori_Data/parse/<pdb>/occurrences.jsonl`, 其中`candidate_id`是原真实实例编号, `type_tag="small_molecule"`表示小分子. 此处`<pdb>`逐个取完整名单中的PDB, 如`9nvs`. 不能用Build评价的77-PDB、446实例范围替换Find范围.

每个PDB的原NPZ以`intersections`保存预测候选×真实实例的体素交集数, 形状`(N_pred,N_gt)`; `pred_sizes/gt_sizes`分别沿两轴保存完整区域体素数. `source_blob_index`是预测轴的原blob编号, 如11, `occurrence_id`是真实轴的原实例编号, 如7; 二者都不等于紧凑数组下标. `candidate_selected`是原最终选择掩码, `candidate_prauc_eligible`是原PRAUC扫描资格掩码, 两者都是沿预测轴的bool数组, 作用不同. `candidate_score`是原预测轴评分, 并列的原评分在一个断点处理.

小分子分析先按固定双向覆盖0.3决定候选的唯一归属: 交集分别除以预测区域体素数和真实区域体素数, 两者均不低于0.3时才合格; 取两覆盖率几何平均最大者, 并列取较小原`occurrence_id`. 固定归属于非小分子的候选整项忽略, 无合格归属的背景仍保留为可能的假阳性. 这一归属只在正文Fig3的`matching.py::target_from_intersections`实现一次, 不随之后0.3/0.5的实例匹配阈值重定.

## 共同原件与科学实现

- GT根: `/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1/held_out_test_0`.
- CA2根: `/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1/held_out_test_0`.
- 这两根的`evaluation/f2_centered_gaussian_macro_selected.jsonl`每行一个PDB, 保存全配体宏平均指标; `<pdb>/evaluation/f2_centered_gaussian_macro_selected.npz`保存上述完整两轴交集、原编号和选择.
- GT/CA2的小分子原逐PDB汇总在`/storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/{find_real_f2_gaussian,find_cryo_f2_gaussian}.per_pdb.jsonl`, 当前P/R从原交集重算, 不能把旧范围汇总直接当作所有指标的替代.

正文Fig3唯一拥有`data.py`的具名条件读取与统计、`matching.py`的候选归属、`instance_metrics.py`的覆盖边/最大一对一匹配/阶梯PRAUC、`semantic.py`的语义并集, 以及`artists.py`的方法配色和P/R画法. 补充Fig1与Fig2明确调用这些文件, 各图的`build.py`独立声明输入条件和所需指标, 各自`plot.py`拥有本图显示. 文件之间没有通过TOOLS传播科学阈值或候选选择. `TOOLS/server_io/source.py`只负责原字节读取, 指定D盘缓存是`D:/AdaLigand_Visualization/server`, 缓存内容必须与服务器原件相同.

原GT/CA2推理的生产说明分别为`/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_d24c9e99c664/Pocket_Plus/src/inference/README.md`和`/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_96938959ed1a/Pocket_Plus/src/inference/README.md`; 本地阅读入口为`C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md`. 两种release对应不同受体, 不以当前HEAD或另一个受体版本替代.

## 无level实验身份

本图Emap2lig根为`/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0`. `evaluation/official_find_li.jsonl`保存完整179-PDB指标, `evaluation/per_pdb/<pdb>.npz`保存原预测与真实实例交集. 小分子Dice和PRAUC沿用`/storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/emap_official_li.per_pdb.jsonl`的94-PDB同条件重评结果, P/R从原交集按固定归属和两阈值重算.

该根实际保留`reports/find_run_summary.json`及`raw_find_outputs/<pdb>/status.json`; 原status字段为`input_map/output_dir/blobs_dir/status_code/blob_count`, 没有完整argv或release字段. 这是原运行记录的事实边界, 不能用显式level的release或当前源码HEAD补造其运行身份. 例如`9nvs`的原输入是`/storage/penghongen/AdaLigand/Ori_Data/raw/emdb_maps/emd_49849.map.gz`, 原`status_code=0`, 原blob数55. `mapped/9nvs/mapping.json`记录原1.0Å体素图到共同实验网格1.0017391443252563Å体素图的映射. 本图读取已经保存的区域、交集和同条件指标, 不重跑旧Emap2lig.

## 统计与显示

Dice为预测与真实语义并集的Dice; 0.3/0.5 PRAUC均使用对应双向覆盖匹配边、最大一对一匹配和原资格/分数组扫描, 两阈值仍共用固定0.3非小分子归属. 最终P/R只使用原`candidate_selected`. 全配体与小分子分别PDB等权求均值, 使用10,000次PDB bootstrap, 种子20260922, 95%百分位区间. P/R用0/1反射、带宽系数0.045的核密度, 标出25/50/75%分位. 本目录`plot.py`只拥有本图2×2面板, 共享科学实现由正文Fig3显式提供.

[README](README.md)给出单图命令和逐文件契约. 本图的实验保存记录见[Emap2lig-nolevel](../../../../追溯文档/source/Emap2lig-nolevel.md), GT/CA2与真实集合见[Find](../../../../追溯文档/source/Find.md)和[原始输入](../../../../追溯文档/source/原始输入.md). 当前作者双语备注从正式PPT复制到单页候选, 不在本目录另建维护副本.
