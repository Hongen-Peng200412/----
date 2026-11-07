# 正文 Fig3 的科学输入、统计与显示

本图比较显式实验地图level条件的Emap2lig-Find与GT/CA2两种LigandSeek-Find, 保留原图`stage1-overall-performance(v1)`的六面板. 正式作者页位于[stage1结果.pptx](../../../PPT/stage1结果.pptx). 当前图只请求Dice、0.3一对一PRAUC、0.3最终候选精确率/召回率及Dice配对散点, 不计算补图的0.5结果或预算完成度.

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

## 显式level与本图计算

Emap2lig原件根是`/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0`. `evaluation/official_find_li.jsonl`保存179-PDB全配体逐PDB指标, `evaluation/per_pdb/<pdb>.npz`保存原交集和选择. 本图94-PDB小分子Emap2lig的Dice和PRAUC从原件重算; 显式level的结果不与无level旧运行混合.

小分子语义Dice取原最终选中且未被固定非小分子归属忽略的预测blob并集, 与全部真实小分子掩码并集比较: `Dice=2TP/(2TP+FP+FN)`. 真实掩码在`/storage/penghongen/AdaLigand/Ori_Data/density/<pdb>/ligand_area.npz`, `grid_shape_zyx`声明完整Z/Y/X网格, `mask_<原实例编号>`保存全图ZYX体素坐标. Emap2lig预测区域在上述level根的`mapped/<pdb>/official_blobs.npz`, `voxel_offsets`相邻端点切分`voxel_index_global_zyx`的同一blob, 首值0, 末值等于坐标总行数. 使用共同原网格, 重叠体素在并集中只计一次. 预处理说明为`C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/Ori_Data/README.md`.

实例匹配要求交集占预测区域和真实区域均至少0.3, 以最大二分匹配得到一对一命中数. 最终候选P/R只使用`candidate_selected`, PRAUC则按`candidate_prauc_eligible`及原评分遍历断点, 每个断点做最大一对一匹配并累加新增recall乘precision, 不能把P/R单点代替PRAUC曲线.

全配体和小分子分别以PDB为等权单位求条形均值, 10,000次PDB bootstrap, 种子20260922, 取2.5/97.5分位. P/R显示为在0/1两端反射的核密度分布, 带宽系数0.045, 同时标出25/50/75%分位, 不以候选数量加权PDB. 配对散点始终是同一PDB的Emap2lig Dice横轴与CA2 Dice纵轴. 颜色来自`/storage/penghongen/AdaLigand/held_out/held_out_base.jsonl`的`quality.map_resolution`, 单位Å, 不据此删除PDB.

显式level的生产说明为`/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md`, 本地为`C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md`. 实验命令、模型和受体完整来源见[Find](../../../../追溯文档/source/Find.md)、[Emap2lig-level](../../../../追溯文档/source/Emap2lig-level.md)、[原始输入](../../../../追溯文档/source/原始输入.md)与[CryoAtom2受体](../../../../追溯文档/source/CryoAtom2受体.md).

## 重建入口与作者显示

[README](README.md)说明单图命令及每个派生文件的契约. 本目录`display.json`和`plot.py`共同保留本图布局与颜色, 候选完成后从正式PPT复制当前双语备注. 图内统计可从服务器原件重建, 作者PPT仍是作者图注和手工展示的维护位置; 本地重建不会覆盖它.
