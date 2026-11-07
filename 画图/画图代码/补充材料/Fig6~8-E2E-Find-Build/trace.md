# 补充Fig6~8的正确身份Find-Build口径

本目录按作者指定作为三页组合, 完整图名依次为`supp-find-correct-match-build-emap2lig`、`supp-find-correct-match-build-ca2`、`supp-find-correct-match-build-gt`. 每页6组, 合计18组; 每行原Top1/Top5/best50, 每列严格2/3Å. 只读取77-PDB正确身份与Emap原件, 不加载实际全身份Match计费文件. 正式作者页保存在[E2E结果.pptx](../../../PPT/E2E结果.pptx).

## 完整目标与科学实现的唯一归属

全配体范围为179个PDB、2502个真实实例; 建模合格小分子为77个PDB、446个实例, 定义为单残基、相对于模板无缺失原子的有机小分子. 小分子成员来自`/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl`的`stage3_occurrence_ids`, 原实例按PDB归并去重. 全配体分母来自`/storage/penghongen/AdaLigand/held_out/split/held_out_06_chain/held_out_identity.jsonl`中`selection.test_0`为真的记录及`ligands.total_count`. 当前图不需要全配体时不读取这一清单. 未检出、身份错误、输入失败、无姿态与无成功PDB都保留在各自完整范围内.

原预测blob键为受体条件+PDB+`source_blob_index`, 原真实实例键为PDB+`occurrence_id`或`matched_occurrence_id`. 如blob编号11不是该数组的第11行, 真实编号0也不是背景标记; 背景由scope/归属None声明. `attempt_index`是跳过免费候选后的1基计费号, `raw_rank/find_rank`是含免费项的原候选排名, 不能交换.

正文Fig6唯一拥有`cohorts.py`的成员归并、`accounting.py`的计费、`controlled_inputs.py`与`actual_inputs.py`的科学读取、`prepare.py`的显式条件组装、`completion.py`的预算统计和`completion_artists.py`的完成度画法. 关联补图通过明确路径调用, 不是复制另一套规则. 区域到真实实例的固定双向0.3归属唯一引用正文Fig3的`matching.py::target_from_intersections`, 不在E2E再建一份. TOOLS仅运输原字节、SVG/原生PPT和作者显示, 不拥有这些定义.

## 预算、原排名与失败

每个PDB真实目标数为N, 百分比预算b允许`b*N//100`次计费尝试. 同一原真实实例只记第一次成功; 完成比例为不同成功实例数/N, 再对完整PDB集合等权求均值或中位数. 0%、50%、100%、200%、300%的逐PDB记录均保留. 事件曲线使用精确有理数K/N, 事件处取已发生后的值并向右保持; 300%只是显示范围, 完整候选用尽统计不受此截断.

Top1、Top5、best-of-50分别使用模型原排名前1、5、50个姿态中的最低重原子RMSD, 严格`<2Å`或`<3Å`. 不按真实RMSD重排模型姿态, 不根据RMSD改Match身份, 不把null或失败填成0. 区间为10000次PDB等权bootstrap均值的2.5%/97.5%分位, 种子20261020. 统计摘要以百分比保存, 逐PDBcompletion与curve.mean/median以0-1比例保存.

## 给定正确身份的Find-Build

GT/CA2原件根分别为`/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/GT`和`/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/CA2`. `completion.json`的`find_small_<域>_poseNone_rmsdNone`提供同范围原Find首次定位事件与完整候选总数; `docking_results.jsonl`提供给定正确身份后的逐原实例构象评价, 以PDB+`matched_occurrence_id`连接. 原`pose_min_rmsd_A`和`success`逐项一致, 只读取`status="success"`且RMSD有效并严格过阈值的请求. 构象成功绑定原Find首次定位计费号, 不从另一个实际Match实验借姿态.

本条件假定身份正确, 真实范围外前景免费跳过, 背景和合格目标候选计费; 重复候选也消耗尝试次数. 原GT/CA2 Find顺序为selected段优先、`source_probability_mean`降序、原blob编号升序, 不能用Gaussian交集NPZ的评分替换原概率均值. 原实际CLI是`bash 测评数据代码/端到端测评/sh/run.sh GT`或`CA2`, release为`AdaLigand_0e2ed5a4829f`. 已存在的该release说明为`/home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand/ligandseek_pipeline/README.md`, 本地入口`C:/Users/15919/Desktop/AdaLigand/ligandseek_pipeline/README.md`; 说明目录不抹去原CLI的旧目录事实.

Emap2lig固定显式实验地图level, 原根`/storage/penghongen/Emap2lig/contour_level_20261026`. `find/held_out_test_0/evaluation/per_pdb/<pdb>.npz`提供原完整交集及预测/真实两轴编号, `candidate_selected`是原选择掩码, `candidate_score`是原评分; 如`intersections`形状`(N_pred,N_gt)`, 每项为交集体素数. 原编号`source_blob_index/occurrence_id`分别对应两轴, `pred_sizes/gt_sizes`是完整区域体素数, 不用交集作为分母. 候选按selected优先、原分数降序、原blob编号升序. 唯一真实归属要求两向覆盖均至少0.3, 最大覆盖几何平均优先, 并列取较小原实例编号. 真实范围外前景免费, 背景保留计费.

`build/find_hit_subset.jsonl`的`blob_id`固定每个PDB+原真实实例的实际Build请求. `build/build_occurrences.jsonl`的`poses`保留原排序, `top1_rmsd_A/top5_rmsd_A/oracle_rmsd_A`对应前1/5/50最低RMSD. 成功步必须是这一请求blob的`charged_attempt`, 不能取包含免费项的find_rank, 也不能挪到同实例更早的另一个候选. 本图只扫描本图所需范围, 77-PDB补图不扫描其余102个PDB. 生产说明为`/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig/显式level实验/README.md`, 本地`C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md`.

## 重建、显示与生产说明

[README](README.md)定义稳定命令与每种输出. 本目录display.json只保存对应页的作者图层、样式、分组与显示偏移, 科学曲线路径和数字来自本次原件重算; 模板中的数字占位绑定新图元, 不冻结成另一套数值. 保留原总画布, 候选完成后复制正式作者PPT当前双语备注, 并写入本目录TRACE来源指路. 不自动改正式PPT, 不把PPT图元反推成科学真值.

原实验模型、配置、release和launch的完整资产指路见[Match](../../../../追溯文档/source/Match.md)、[Build](../../../../追溯文档/source/Build.md)、[E2E-受控身份](../../../../追溯文档/source/E2E-受控身份.md)、[Emap2lig-level](../../../../追溯文档/source/Emap2lig-level.md)、[原始输入](../../../../追溯文档/source/原始输入.md). 本图trace解释当前读取与选择, source说明解释原实验生产.
