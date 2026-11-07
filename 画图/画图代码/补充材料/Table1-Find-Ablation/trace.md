# 补充 Table1 的六变体、11份原metrics与36个显示数值

本表使用held-out test0的179-PDB原宏平均, 每行显示CA2和GT两个受体条件的语义Dice、一对一PRAUC0.3、一对一PRAUC0.5. 不使用149-PDB test1派生, 不使用coverage PRAUC, 不套用Build的小分子77-PDB筛选, 不读取716个推理计时文件.

## 每行对应的实验

以下地址均为服务器绝对目录. 表中`GT根`和`CA2根`各自追加`/held_out_test_0/evaluation/<指标文件>`构成实际读取地址, 例如最终GT为`/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1/held_out_test_0/evaluation/f2_centered_gaussian_macro_selected.metrics.json`.

| 表格行 | GT根 | CA2根 | 指标文件 |
| --- | --- | --- | --- |
| Density only | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_c1_pdb_centric_v2/artifacts/unet_c1` | 与本行GT同一根 | `f1_blobs_basic_macro_selected.metrics.json` |
| + Difference density | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_diff/artifacts/unet_diff` | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_diff/CryoAtom2受体/artifacts/unet_diff` | `f1_blobs_basic_macro_selected.metrics.json` |
| + Density bank | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_base/artifacts/unet_base` | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_base/CryoAtom2受体/artifacts/unet_base` | `f1_blobs_basic_macro_selected.metrics.json` |
| + Receptor features | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_full/artifacts/unet_full` | `/storage/penghongen/AdaLigand_stage1_inference/UNET/unet_full/CryoAtom2受体/artifacts/unet_full` | `f1_blobs_basic_macro_selected.metrics.json` |
| + Centroid encoding | `/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1` | `/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1` | `f1_blobs_basic_macro_selected.metrics.json` |
| LigandSeek-Find | `/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1` | `/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1` | `f2_centered_gaussian_macro_selected.metrics.json` |

原件按绝对地址去重, 所以读取11份而不是12份. Density-only两组数字来自同一份不使用受体特征的原件, 原样显示两组, 不伪造第二次实验. 其余模型、受体和F1/F2候选处理条件各自保留, 不能为合并目录而合并真值.

## 原字段与显示列

每份原JSON的`pdb_count`必须为179. `semantic_macro_f1`映射为Dice, `one_to_one_macro_prauc_0p3`映射为PRAUC0.3, `one_to_one_macro_prauc_0p5`映射为PRAUC0.5; 均是同一PDB集合的等权均值. 原实例PRAUC使用交集占预测/真实区域均达到对应阈值的匹配边, 按原候选资格和评分断点做最大一对一匹配. 当前本表读取这些已生产的原汇总, 没有在本地重新定义评估.

`build.py`按表格行顺序、CA2再GT的列顺序取出36个数. CSV保留原精度, Markdown显示三位小数. 不计算新舍入值回写源JSON, 不回写论文或冻结Word. 本表入口不读取图形缓存、旧本地汇总或D盘转换产物.

## 原程序和配置的来源

最终GT和CA2 Find推理分别由`Pocket_Plus_d24c9e99c664`与`Pocket_Plus_96938959ed1a`执行, 原生产说明位于`/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_d24c9e99c664/Pocket_Plus/src/inference/README.md`和同级`Pocket_Plus_96938959ed1a/Pocket_Plus/src/inference/README.md`. 本地阅读入口是`C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md`.

U-Net输入消融的实际原命令脚本已保存在`/storage/penghongen/备份/原本所有tmp的备份/unet_input_ablation_20260926/`的`run_basic.sh`与`run_cryoatom2.sh`, 指定原BEST checkpoint、resolved config、calibration和原正式`训练与运行/sh/infer/stage1_v3.sh`. GT的unet_diff/base使用`Pocket_Plus_d19813b06194`, CA2及unet_full相应实际launch使用`Pocket_Plus_b061106c817c`, 原launch位于`/home/penghongen/Feedback/Pocket_Plus/launches/386111/`、`386112/`、`386151/`. 原记录中的历史tmp命令文字不是当前读取依赖, 不据此重建或改写实验程序.

各变体的具体输入、模型、配置、原launch与保全脚本关系统一见[Find实验来源](../../../../追溯文档/source/Find.md). 此处只定义本表实际选择与列映射, 运行和输出契约见[README](README.md).
