# 补充Fig9~10的实际Find-Match-Build口径

本目录按作者指定作为两页组合, 完整图名依次为`supp-find-match-build-ca2`与`supp-find-match-build-gt`. 每页6组, 合计12组; 每行原Top1/Top5/best50, 每列严格2/3Å. 只读取77-PDB原全身份预测、候选与实际构象评价, 不读取Emap原交集或受控正确身份姿态. 正式作者页保存在[E2E结果.pptx](../../../PPT/E2E结果.pptx).

## 完整目标与科学实现的唯一归属

全配体范围为179个PDB、2502个真实实例; 建模合格小分子为77个PDB、446个实例, 定义为单残基、相对于模板无缺失原子的有机小分子. 小分子成员来自`/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl`的`stage3_occurrence_ids`, 原实例按PDB归并去重. 全配体分母来自`/storage/penghongen/AdaLigand/held_out/split/held_out_06_chain/held_out_identity.jsonl`中`selection.test_0`为真的记录及`ligands.total_count`. 当前图不需要全配体时不读取这一清单. 未检出、身份错误、输入失败、无姿态与无成功PDB都保留在各自完整范围内.

原预测blob键为受体条件+PDB+`source_blob_index`, 原真实实例键为PDB+`occurrence_id`或`matched_occurrence_id`. 如blob编号11不是该数组的第11行, 真实编号0也不是背景标记; 背景由scope/归属None声明. `attempt_index`是跳过免费候选后的1基计费号, `raw_rank/find_rank`是含免费项的原候选排名, 不能交换.

正文Fig6唯一拥有`cohorts.py`的成员归并、`accounting.py`的计费、`controlled_inputs.py`与`actual_inputs.py`的科学读取、`prepare.py`的显式条件组装、`completion.py`的预算统计和`completion_artists.py`的完成度画法. 关联补图通过明确路径调用, 不是复制另一套规则. 区域到真实实例的固定双向0.3归属唯一引用正文Fig3的`matching.py::target_from_intersections`, 不在E2E再建一份. TOOLS仅运输原字节、SVG/原生PPT和作者显示, 不拥有这些定义.

## 预算、原排名与失败

每个PDB真实目标数为N, 百分比预算b允许`b*N//100`次计费尝试. 同一原真实实例只记第一次成功; 完成比例为不同成功实例数/N, 再对完整PDB集合等权求均值或中位数. 0%、50%、100%、200%、300%的逐PDB记录均保留. 事件曲线使用精确有理数K/N, 事件处取已发生后的值并向右保持; 300%只是显示范围, 完整候选用尽统计不受此截断.

Top1、Top5、best-of-50分别使用模型原排名前1、5、50个姿态中的最低重原子RMSD, 严格`<2Å`或`<3Å`. 不按真实RMSD重排模型姿态, 不根据RMSD改Match身份, 不把null或失败填成0. 区间为10000次PDB等权bootstrap均值的2.5%/97.5%分位, 种子20261020. 统计摘要以百分比保存, 逐PDBcompletion与curve.mean/median以0-1比例保存.

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

## 重建、显示与生产说明

[README](README.md)定义稳定命令与每种输出. 本目录display.json只保存对应页的作者图层、样式、分组与显示偏移, 科学曲线路径和数字来自本次原件重算; 模板中的数字占位绑定新图元, 不冻结成另一套数值. 保留原总画布, 候选完成后复制正式作者PPT当前双语备注, 并写入本目录TRACE来源指路. 不自动改正式PPT, 不把PPT图元反推成科学真值.

原实验模型、配置、release和launch的完整资产指路见[Match](../../../../追溯文档/source/Match.md)、[Build](../../../../追溯文档/source/Build.md)、[E2E-实际计费](../../../../追溯文档/source/E2E-实际计费.md)、[原始输入](../../../../追溯文档/source/原始输入.md). 本图trace解释当前读取与选择, source说明解释原实验生产.
