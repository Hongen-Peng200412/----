# 补充 Fig1 的严格匹配与预算口径

本图对应正式图集[stage1结果.pptx](../../../PPT/stage1结果.pptx)中的`stage1-additional-analysis`. 本图只重建双向覆盖0.5的实例PRAUC及最终候选P/R, 外加100%/300%候选预算完成度. 0.5用于严格实例匹配; 候选类别归属与预算成功归属仍固定为0.3, 这三种职责不能混为同一个阈值.

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

## 严格0.5面板

Emap2lig使用显式level根`/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0`, 读取`evaluation/official_find_li.jsonl`和`evaluation/per_pdb/<pdb>.npz`. 生产说明为`/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md`, 本地入口`C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md`.

在固定0.3非小分子归属过滤之后, 0.5面板的匹配边要求交集占预测与真实区域的比例均至少0.5. P/R使用原最终选择, PRAUC按原资格和原评分的并列断点做最大一对一匹配及阶梯积分. 图中均值与95%区间按PDB等权、10,000次bootstrap、种子20260922; P/R密度使用0/1反射、0.045带宽系数. 当前入口不请求Dice, 因而不读取显式level的原密度和mapped blob坐标.

## 预算面板

GT/CA2的完整候选表来自`/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json`的`predictions.real_receptor`和`predictions.cryoatom2_receptor`. `candidate_selected`保留原选择段, `source_probability_mean`是原Find排序用的概率均值, `source_blob_index`是原blob编号. 此表的`matched_occurrence_id/foreground_target`保留原真实归属. 实际生产说明见`/home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md`, 本地为`C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md`. GT/CA2不能拿Gaussian交集NPZ的`candidate_score`替换原排序字段.

Emap2lig从完整原交集NPZ重建候选, 以同一固定双向覆盖0.3、最大几何平均、最小原实例编号规则决定唯一归属, `candidate_score`作为其原评分. 三方法都按原selected段优先、概率评分降序、原blob编号升序扫描. 完整范围以全部原真实实例为分母, 小分子范围以94-PDB内全部821个小分子为分母. 归属于当前范围以外真实类别的候选跳过, 背景和重复候选仍消耗尝试次数, 同一真实实例只算第一次命中.

预算100%/300%表示每个PDB可尝试`target_count*budget//100`个候选. 例如实际`10ft`全配体GT记录中完整目标数4, 100%预算4次, 命中2个不同真实实例, 完成度0.5. 每个PDB完成度的分母保留全部目标, 不只保留成功实例或有候选的实例. 先按PDB求完成比例, 再PDB等权取均值和同一种子10,000次bootstrap区间, 不合并所有PDB实例再求比例.

本目录`completion.py`拥有本图候选排序、范围选择和100/300两个预算的统计组合, 不建立其它预算或整条阶段曲线. 整数预算与去重记录唯一调用正文Fig6的`completion.py::fixed_budget_records`, 本图仍使用179/94个PDB及自己的20260922 bootstrap. [README](README.md)给出`completion_panels.json`全部字段. 科学归属唯一调用正文Fig3的`matching.py`, 不复制同责实现.

资产完整来源见[Find](../../../../追溯文档/source/Find.md)、[Emap2lig-level](../../../../追溯文档/source/Emap2lig-level.md)、[Match](../../../../追溯文档/source/Match.md)、[原始输入](../../../../追溯文档/source/原始输入.md). 当前双语备注从正式作者PPT复制, 候选不自动覆盖该文件.
