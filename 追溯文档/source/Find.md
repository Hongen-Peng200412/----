# Find 主结果、小分子分析与六变体消融

服务器产物根：`/storage/penghongen/AdaLigand_stage1_inference`。本地副本：`追溯文档/source/Find.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 当前原始结果

GT 与 CA2 的最终评价分别位于 `Find_1/{真实受体,CryoAtom2受体}/artifacts/Find_1/held_out_test_0/`。目录中的 `evaluation/f2_centered_gaussian_macro_selected.{metrics.json,jsonl}` 保存汇总和逐 PDB 指标；每个 PDB 的 `evaluation/f2_centered_gaussian_macro_selected.npz` 保存候选×真实实例交集、体素数、原分数、最终 selected 及 PRAUC 资格。`blobs/F2_blobs.npz` 保存原始 blob 完整体素。

`small_molecule_only/test_0/` 下 `find_real_f2_gaussian`、`find_cryo_f2_gaussian`、`emap_official_li` 的 `.metrics.json` 与 `.per_pdb.jsonl` 是原无 level 小分子统计。其 `provenance.json` 固定 94 PDB 范围、来源和类别规则。当前新 level Emap 原件另在 `/storage/penghongen/Emap2lig/contour_level_20261026/`，不能写回这里覆盖旧条件。

Table 1 的 11 组原 metrics 位于：`UNET/unet_c1_pdb_centric_v2/artifacts/unet_c1/...`（两受体共用一份）、`UNET/{unet_diff,unet_base,unet_full}/[CryoAtom2受体/]artifacts/<模型>/...`（各两份），以及 Find_1 两受体的 F1-basic 和最终 F2-Gaussian。均取 `held_out_test_0/evaluation/*.metrics.json`，字段为 `semantic_macro_f1/one_to_one_macro_prauc_0p3/one_to_one_macro_prauc_0p5`，六模型×六显示值，不能误用149-PDB test_1或 coverage PRAUC。

## 实际命令、源码与权重

Find 模型来自训练 Job368455，原训练 launch `Find_1_pdb_centric_2_job368455_20260909T071535_a2`，对应原恢复脚本和 `Pocket_Plus_2ca40d551603`。原run根为 `/home/penghongen/Feedback/Pocket_Plus/logs/AdaLigand_Stage1_pdb_centric_resume-Find_1-pdb_centric_2/Find_1-pdb_centric_2_resume____Find_1_pdb_centric_2_job368455_20260909T071535_a2_pdb_centric_2_resume`，直接保留 `config.yaml` 与 `checkpoints/TOP_epoch_04_score_0.6654.ckpt`（epoch4/global_step38623，W&B完成步38622）。实际源码由原release与原恢复task_root界定，不自动搜索最新权重。

GT 实际推理命令是 `bash 训练与运行/sh/infer/find1_real_receptor_evaluation.sh`，原 release `Pocket_Plus_d24c9e99c664`，launch `/home/penghongen/Feedback/Pocket_Plus/launches/368455/Find_1_pdb_centric_2_job368455_20260912T230920_a5/`。CA2 对应 `find1_cryoatom2_receptor_evaluation.sh`、release `Pocket_Plus_96938959ed1a`、launch `Find_1_pdb_centric_2_job368455_20260915T150255_a16`。两处 `run_cmd.sh/launch.json` 已从服务器原件读取，正式源码仍在各 release，不以当前 HEAD 冒充当年版本。

U-Net 三输入消融实际调用 `bash /storage/penghongen/tmp/unet_input_ablation_20260926/run_basic.sh <unet_diff|unet_base|unet_full>` 和对应 `run_cryoatom2.sh`。这两份真实 CLI 元数据按获准具名清单保全到 `/storage/penghongen/备份/原本所有tmp的备份/unet_input_ablation_20260926/`；历史命令仍写原路径。脚本选择原 BEST.ckpt、原 resolved config、calibration清单及原正式 `训练与运行/sh/infer/stage1_v3.sh`。GT 的 unet_diff/base 使用 `Pocket_Plus_d19813b06194`，CA2及unet_full相应实际 launch 使用 `Pocket_Plus_b061106c817c`；原 launch 在 `/home/penghongen/Feedback/Pocket_Plus/launches/{386111,386112,386151}/`。149-PDB `derive*_test1`、门控和恢复尝试不参与当前表，不随此保全。

保全脚本逐字节身份：`run_basic.sh` 为 `d7e2b46e240d4ca9752d46171e3c8fc5f3e62f203dfa41b1887c39b10eac569b`，`run_cryoatom2.sh` 为 `6902a69c4dd3a77789a340677874bb7cf5ae2104be26a1435d080e6e85be7e2b`。两份脚本作为原实际运行元数据读取，不在服务器修改其功能或重新执行实验。

## 指标、排序和失败

全配体179 PDB、小分子94 PDB均逐PDB等权。语义Dice直接对预测并集与真实并集计数，不使用实例匹配阈值。候选实例双向覆盖均至少0.3；归属取覆盖率几何均值最大者，并列取较小 occurrence_id。小分子评价先以全部类别确定归属，忽略归属于非小分子的候选；未归属的背景和重复命中保留。P/R对原最终selected做最大一对一匹配；PRAUC按原float32分数并列组和原PRAUC资格扫描，不等于最终selected的P/R。

完成度在每PDB按selected优先、原概率均值 `source_probability_mean` 降序、原blob编号升序累计首次检出；GT/CA2直接使用原strongest-1/frozen_test中的Find元数据，不用评价NPZ的Gaussian `candidate_score`替换该排序。Emap两条件使用各自NPZ的原概率分数。背景与重复仍占候选位置。100%/300%预算为floor(比例×本PDB真实实例数)，未检出及零候选保留0。逐PDB数组顺序不改；bootstrap为10,000次、seed20260922，KDE使用边界反射、bw=.045、161点。0.5 P/R只提高匹配阈值，不重新决定类别归属。

本地 `画图/画图代码/正文/Fig3-result-Find/` 唯一拥有候选归属与指标规则。补充材料 Fig1、Fig2 和 Table1 分别拥有自己的输入及完整入口，显式引用必要的共同规则；具体关系见各图 `trace.md`。旧 `server_metrics_and_pr.json/plot_data.json` 只是既往本地派生容器，不是服务器真值，不上传成为输入。

Find运行时间来自两受体179×2个PDB的 `status/probability/performance.json` 与 `status/F2_centered/performance.json` 两段wall_seconds之和，358观测均值213.2958286864秒；不含外部加载、blob提取及最终发布，不当作作业总墙钟时间。
