# Fig5的科学来源与重建口径

Fig5完整标识为`stage2-stage3-results(v1)`, 正式页面在`画图/PPT/stage2-stage3结果.pptx`。本说明描述本图直接读取和统计, 不把作者显示资产或本次输出当作实验真值。分组来源进一步见[Match](../../../../追溯文档/source/Match.md)、[Build](../../../../追溯文档/source/Build.md)、[显式level的Emap2lig](../../../../追溯文档/source/Emap2lig-level.md)、[受控Find–Build](../../../../追溯文档/source/E2E-受控身份.md)、[原始输入](../../../../追溯文档/source/原始输入.md)和[CryoAtom2受体](../../../../追溯文档/source/CryoAtom2受体.md)。

## a–c: 身份匹配

原评价为`/storage/penghongen/Matcher/evaluation/final_smiles/strongest-1/frozen_test.json`。`metrics.{real_receptor,cryoatom2_receptor}.smiles_match`提供Overall、small_molecule、ion和sugar的原correct_count及eligible_count。准确率为正确数除支持数乘100; GT和CA2的Overall支持分别为1238和1160个blob。

b/c从同文件`predictions`保留`candidate_selected && foreground_target && identity_supported`行, 精确比较`predicted_smiles == target_smiles`。按`/storage/penghongen/Matcher/manifests/{test0_real_smiles_v1,test0_cryoatom2_smiles_v1}/manifest.json`所指的`held_out_test_0.identities`计算每PDB不同SMILES字符串数, 分为1、2、3、4和≥5; 分类与Overall分别累加正确数/支持数, 不平均各PDB准确率。无支持组显示0, 原支持数仍保存。

原生产解释位于`C:/Users/15919/Desktop/Matcher/matcher/evaluation/README.md`及`configs/experiments/final_smiles/README.md`; 历史release的现存说明是`/home/penghongen/Feedback/Matcher/releases/Matcher_cab21d9ceea5/Matcher/matcher/evaluation/README.md`。冻结评价内的模型、条件与预测是历史事实, 本次不训练或推理。

## d–f: 235个共同实例

Emap2lig原根为`/storage/penghongen/Emap2lig/contour_level_20261026`。从`build/find_hit_subset.jsonl`保留`status=ready`且`5 <= voxel_atom_ratio <= 25`的251实例; `build/build_occurrences.jsonl`提供这些实例的原Top1/5/50 RMSD。GT和CA2分别读`/storage/penghongen/Adaligand_E2E/test/test_0/evaluation/{GT,CA2}/docking_results.jsonl`, 保留`status=success`且`matched_occurrence_id`非空的结果。三方以`(pdb_id, occurrence_id)`取交集并排序, 得235实例; 三方法共用这条轴和完整235分母。每一侧原blob编号另存`selected_blobs`, 不能用blob编号跨方法连接。

Emap原字段为`top1_rmsd_A/top5_rmsd_A/oracle_rmsd_A`; GT/CA2为`pose_min_rmsd_A['1'/'5'/'50']`, 单位Å。它们均保留原评分排名, Top-5只取原前五的最低RMSD, best-of-50才取全部50。累计成功率采用严格`RMSD < t`; 柱图阈值为1和2Å。散点显示将≥5Å放到边界, 胜率仍由未截断的原值计算。

Emap实验显式传入EMDB推荐level L, 官方有效阈值为L/2。正式命令为`bash 训练与运行/sh/with_level.sh`; release为`/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig`, launch为`/home/penghongen/Feedback/Emap2lig/launches/423330/build_gate_job423330_20261026T202139_a2/`。现存生产README为该release的`显式level实验/README.md`, 本地对应`C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md`。

受控GT/CA2历史命令分别为`bash 测评数据代码/端到端测评/sh/run.sh GT`及`CA2`, release为`/home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand`。GT launch为`/home/penghongen/Feedback/AdaLigand/launches/403776/submit_task_job403776_20261016T043310_a4/`; CA2为`/home/penghongen/Feedback/AdaLigand/launches/403774/submit_task_job403774_20261016T042314_a4/`。该release的`ligandseek_pipeline/README.md`实际存在, 原配置在结果根`configs/{GT,CA2,Emap2lig}.yml`。这是给定身份的受控Find–Build来源, 不能冒充标准446实例或实际全身份Match计费曲线。

## g–i: 9WUP的FAD A:1103

实例为`9wup, occurrence_id=2`, 共53重原子。`/storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl`的`prepared_smiles`定义原子/键轴; `/storage/penghongen/AdaLigand/Ori_Data/smiles_assets/SMILE_coords/v1/9wup.npz`按candidate_ids及coord_offsets切出沉积世界XYZ坐标。PocketXMol-official和DG分别来自`/storage/penghongen/PocketXMol/sampling/{official-SMILES,local_cov-C-T0-RA}/test/C0/9wup/2/poses.sdf`, 由对应occurrences.json的top1_sample_index选择原sample22和18, 不按真实距离挑选。Emap原Top1为`/storage/penghongen/Emap2lig/contour_level_20261026/build/build/9wup/2/build_gate_job423330_20261026T202139_a2/build_struct/blob_4/blob_4_LIG_27.cif`; LIG.npz的atom_names连接CIF原子名。

沉积受体来自`/storage/penghongen/AdaLigand/Ori_Data/parse/9wup/receptor_tokens.npz`; 密度来自`/storage/penghongen/AdaLigand/Ori_Data/density/9wup/{exp.npy,exp.npz}`。生产说明为`C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/Ori_Data/README.md`、`C:/Users/15919/Desktop/AdaLigand/Data_Preprocessing/PocketXmol_compat/README.md`及`C:/Users/15919/Desktop/PocketXMol/docking/README.md`; PocketXMol历史说明位于`/home/penghongen/Feedback/PocketXMol/releases/PocketXMol_f4d72bbea387/PocketXMol/docking/README.md`。

保留res_type<28且距任一展示构象8Å内的受体原子, 密度裁到全部构象包围盒±9Å。源密度为ZYX数组, origin/voxel_size为XYZÅ边界角点与间距; 三线性取样索引为`((xyz-origin)/voxel_size - 0.5)[:, ::-1]`。D是配体重原子值≥contour_canonical的比例; Clash按真实三维距离严格小于`0.75*(配体VDW半径+受体VDW半径)`计原子对, 不由二维交叉决定。RMSD直接取原评价, 不新叠合。

四个构象共同确定PCA相机并保持右手系, 三方法共享缩放与取景。密度marching-cubes顶点按半体素中心转回世界坐标, 只显示三个顶点均距沉积配体<2Å的已有面片; 背景显示邻近沉积配体3.5Å或涉及真实碰撞的整残基。上述都是本图既有科学/显示定义, 不搬进TOOLS或改写服务器。

## 重建边界

本目录[README](README.md)给出唯一短命令和阅读顺序。所有统计、局部数组、网格、候选PPT和预览都只写本次根temp, D盘只供应与服务器完整SHA核对的原件。作者布局保存显示信息; 正式PPT备注是当前图注原件。Fig9与补图3只复用本图标准Build读取/分布定义, 不执行本图235交集或9WUP。独立claim不从本图绘制入口另起计算系统。
