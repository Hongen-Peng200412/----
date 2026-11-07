# 补充Fig5的Top-k观察量与18条曲线

本图`e2e-topk-success`的a/b分别是179-PDB全配体、77-PDB合格小分子的Find/Match成功PDB比例, c/d分别是CA2/GT实际Find-Match-Build构象成功PDB比例. K为1到10次计费尝试, 同一PDB只要至少成功一个目标即算成功, 与该PDB成功了多少目标无关. 分母始终是完整179或77个PDB. 只计算本图18条曲线, 不建立预算完成度40面板或统计未使用的Top5与其他方法.

## 完整目标与科学实现的唯一归属

全配体范围为179个PDB、2502个真实实例; 建模合格小分子为77个PDB、446个实例, 定义为单残基、相对于模板无缺失原子的有机小分子. 小分子成员来自`/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl`的`stage3_occurrence_ids`, 原实例按PDB归并去重. 全配体分母来自`/storage/penghongen/AdaLigand/held_out/split/held_out_06_chain/held_out_identity.jsonl`中`selection.test_0`为真的记录及`ligands.total_count`. 当前图不需要全配体时不读取这一清单. 未检出、身份错误、输入失败、无姿态与无成功PDB都保留在各自完整范围内.

原预测blob键为受体条件+PDB+`source_blob_index`, 原真实实例键为PDB+`occurrence_id`或`matched_occurrence_id`. 如blob编号11不是该数组的第11行, 真实编号0也不是背景标记; 背景由scope/归属None声明. `attempt_index`是跳过免费候选后的1基计费号, `raw_rank/find_rank`是含免费项的原候选排名, 不能交换.

正文Fig6唯一拥有`cohorts.py`的成员归并、`accounting.py`的计费、`controlled_inputs.py`与`actual_inputs.py`的科学读取、`prepare.py`的显式条件组装、`completion.py`的预算统计和`completion_artists.py`的完成度画法. 关联补图通过明确路径调用, 不是复制另一套规则. 区域到真实实例的固定双向0.3归属唯一引用正文Fig3的`matching.py::target_from_intersections`, 不在E2E再建一份. TOOLS仅运输原字节、SVG/原生PPT和作者显示, 不拥有这些定义.

## 实际全身份Match计费与原姿态

完整身份预测来自`/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json`. `predictions.real_receptor/cryoatom2_receptor`保留原PDB候选、精确`predicted_smiles`、原目标与排序字段. 77-PDB原完整候选顺序来自`/storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/strongest-1/train_strongest1_revised_job378587_20260920T230727/evaluation.json`的`traces.source_probability_mean`. 原真实类别和Stage3范围来自`/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/{identities,real_candidates,cryoatom2_candidates}.jsonl`. 精确SMILES在同一PDB内连接; 原重叠候选的全身份答案相互核对, 不用RMSD决定身份.

原构象评价分别来自`/storage/penghongen/PocketXMol/final_evaluation/end_to_end/GT`和`CA2`, 每根的`evaluation.json`保存原轨迹的`docking_stage`, `docking_results.jsonl`按PDB+原blob编号保存逐候选methods. 当前只采用`methods.local_cov-C`, 即第一轮DG Centre, 不把第二轮Centre或Envelope结果写进该方法. 读取`pose_min_rmsd_A["1"/"5"/"50"]`与对应`success["2.0"/"3.0"][排名数]`, 原`status`及缺失值保持. 原request与姿态不变, 仅在本地按全身份答案重建计费号.

实际计费动作如下, 每个“计费”都消耗一次, 每个“跳过”都不消耗:

| 真实候选范围 | Match输出条件 | 动作 |
| --- | --- | --- |
| 背景 | 任意身份 | 计费 |
| 非小分子前景 | 预测为小分子 | 计费 |
| 非小分子前景 | 预测为非小分子 | 跳过 |
| Stage3范围外的真实小分子 | 精确身份正确 | 跳过 |
| Stage3范围外的真实小分子 | 精确身份错误 | 计费 |
| Stage3合格目标 | 任意身份, 包括预测为非小分子 | 计费 |

Find-Match成功要求合格目标和精确身份正确; 完整构象成功还要求同一请求原`local_cov-C.status="success"`及原RMSD严格过阈值. 成功事件用新计费号, 免费项不能挤进预算. 背景、错误身份和原失败候选都不从候选序列或目标分母消失. 原evaluation的`answer_scope="small_molecule"`是原记录事实, 当前派生的`match-aware-stage3-v2`不会上传覆盖原件.

Matcher生产说明为`/home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md`, 本地`C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md`. 原实际构象评价程序为`/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/scripts/evaluate_end_to_end.py`, 该release的`scripts/README.md`存在并解释该流程, 完整地址为`/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/scripts/README.md`; 本地`C:/Users/15919/Desktop/PocketXMol/scripts/README.md`. 此实际实验与Adaligand_E2E受控正确身份根分开, 不因都叫local-c1而合并.

## 本图独有的定位和Top-k提取

全配体GT/CA2四条Find/Match曲线沿用`/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json`的`curves.source_probability_mean`原整数计数, K=1到10; 真实范围完整179-PDB. 小分子GT/CA2定位从`/storage/penghongen/Matcher/evaluation/test_smallmolecule_v1/stage1_only/stage1_only.json`的完整原候选轨迹重算: 真实范围外前景免费, 背景与合格目标计费, 前K有一次合格定位即成功. 小分子Find-Match与构象曲线则使用上节的实际全身份计费, 不能挪用定位诊断的免费集合.

Emap2lig五图共享的区域归属规则唯一在正文Fig3 matching.py. 归属要求交集占预测与真实区域均至少0.3, 取两覆盖率几何平均最大者, 并列取较小原实例编号. 本图从`/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/evaluation/per_pdb/<pdb>.npz`扫描179份原交集, selected段优先、candidate_score降序、原blob编号升序. 全配体按包含全部候选的rank取首次定位, 小分子免费跳过归属非合格真实前景, 以charged_attempt取首次定位. 两条曲线均逐K统计至少命中一次的完整PDB数. 本图不需要Emap Build, 不读取find_hit_subset或build_occurrences.

c/d只采用`methods.local_cov-C`, Top1与best-of-50、严格2/3Å四条/域; 原success布尔值与原排名保持. 图中成功数除以77后乘100, 数据点不因右侧文字避让而移动. 正式PPT当前双语备注和作者显示保留, [README](README.md)定义短命令与全部文件字段.

原实验详情见[Match](../../../../追溯文档/source/Match.md)、[实际计费E2E](../../../../追溯文档/source/E2E-实际计费.md)、[Emap2lig-level](../../../../追溯文档/source/Emap2lig-level.md)和[原始输入](../../../../追溯文档/source/原始输入.md).
