# BACKUP: 30GA完整复合物的科学来源与当前显示

完整图名`backup-complex-30ga`, 正式图集`画图/PPT/BACKUP.pptx`。本图采用PDB=30GA, CryoAtom2受体(CA2), 受控test0, 原100%合格小分子计费预算, 原模型Top-1; 不是实际全身份Find–Match–Build重计费曲线。原合格分母为7, 恢复5个实例, 成功要求身份正确且原世界坐标重原子RMSD严格小于2Å。

## 成员、预算和原Top1

成员复用正文Fig6的`cohorts.py::read_cohorts(store,False)`, 读取`/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl`的stage3_occurrence_ids, 固定77 PDB/446实例。原受控输入副本位于`/storage/penghongen/Adaligand_E2E/test/test_0/inputs/stage3/identities.jsonl`; 本轮核对两处合格成员相同, 不按检出或构象成功缩小分母。

选择读取`/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/CA2/evaluation.json::traces.30ga`。保留attempt_index非空且≤7的原尝试; `source_blob_index`是区域编号, `matched_occurrence_id`是真实实例, 二者不可互换。身份正确且真实实例属于合格集的候选沿原docking_stage.output_dir读取ranking.json/evaluation_metrics.json。ranking.top1_sample_index连接metrics.sample_index, 取其原rmsd_A; 不按真实RMSD另选姿态。多个预测恢复同一真实实例只计一次。

实际背景输出另由`/storage/penghongen/Adaligand_E2E/actual_display_20261101/CA2/display_results.jsonl`的PDB+source_blob_index定位。其成功输出可用于当前显示, 无合法参考RMSD的姿态不进入成功集合或合法RMSD范围。30GA blob5是明确例子; blob0没有可用actual构象, 不能补造。背景和错身份仍按原traces尝试预算, 非合格类别沿原跳过记录, 不重排候选。

## 真实生产记录

受控根为`/storage/penghongen/Adaligand_E2E/test/test_0`。历史正式命令`bash 测评数据代码/端到端测评/sh/run.sh CA2`, release`/home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand`, launch`/home/penghongen/Feedback/AdaLigand/launches/403774/submit_task_job403774_20261016T042314_a4/`。该release的`ligandseek_pipeline/README.md`实际存在; 当前本地阅读入口是`C:/Users/15919/Desktop/AdaLigand/ligandseek_pipeline/README.md`及README_Build.md。

额外实际构象的现存生产说明在`/storage/penghongen/Adaligand_E2E/actual_display_20261101/control/releases/AdaLigand_e15f82b50271/AdaLigand/ligandseek_pipeline/README.md`。这些release位置经实际读取确认, 不把不存在的/home同名路径写成事实。完整科学来源见[受控身份](../../../../追溯文档/source/E2E-受控身份.md)、[作者构象](../../../../追溯文档/source/E2E-作者构象.md)、[CryoAtom2受体](../../../../追溯文档/source/CryoAtom2受体.md)和[原始输入](../../../../追溯文档/source/原始输入.md)。

## 当前画面与重建

本图采用PNG及DrawingML明确保存在本目录design, 其中仅一页及其必需Office依赖。当前采用CXS路径见design.json.native_sessions; 原complex.cxs和complex.png已原字节迁至画图/Chimera/BACKUP/30GA/。图注从正式PPT当前备注完整复制; 来源短批注只指本图README/trace, 不复制另一套实验解释。候选PPT、科学数组、渲染和日志只写本次根temp。

BACKUP默认还从服务器原CA2 receptor_tokens.npz的XYZÅ坐标/原子属性生成本次受体CIF, 从沉积ligand_coords.npz与ligand_objects模板按present掩码生成全部沉积配体SDF, 从上述原Top1的poses.sdf按metrics.sdf_index取对应分子。sample_index不是SDF位置。原子、电荷、键、世界坐标和缺失状态保持; 不叠合、不补原子。独立ChimeraX使用本例case.json保存的正交相机、颜色与画幅, 在本次scientific-input/native-output生成新PNG和全内嵌CXS, 不覆盖当前采用显示。唯一短命令与代码阅读顺序见[README](README.md)。
