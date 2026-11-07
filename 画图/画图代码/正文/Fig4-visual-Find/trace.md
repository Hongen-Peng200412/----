# Fig4的9NVS来源、编号与作者视角

当前采用页为`stage1-author-global-local-9nvs(v1)`, 图集`画图/PPT/stage1可视化.pptx`。a–c全景及五个局部视图的作者PNG、裁切和原生标注在本目录design中; 对应8个CXS见design.json.native_sessions。它们分别是Emap2lig全景、LigandSeek(CA2)全景、真实区域全景、Emap误报局部、两方法共同实例局部、真实局部和透明真实局部。古法会话原件不移动、不改名或重存。

## 本图直接读取

- `/storage/penghongen/Emap2lig/contour_level_20261026/find/held_out_test_0/evaluation/official_find_li.jsonl`: 选`pdb_id=9nvs`行的`semantic_macro_f1`, 原语义Dice显示0.160。
- `/storage/penghongen/AdaLigand_stage1_inference/Find_1/CryoAtom2受体/artifacts/Find_1/held_out_test_0/evaluation/f2_centered_gaussian_macro_selected.jsonl`: 同一PDB同字段, 原值显示0.757。
- Emap同evaluation根`per_pdb/9nvs.npz`: 用`source_blob_index=2`定位预测轴, `occurrence_id=1`定位真实轴。
- CA2同held_out_test_0根`9nvs/evaluation/f2_centered_gaussian_macro_selected.npz`: 用本侧原`source_blob_index=1`与同一`occurrence_id=1`定位。

交集数组`intersections(P,G)`、`pred_sizes(P,)`和`gt_sizes(G,)`给出该实例IoU=`交集/(预测体素+真实体素−交集)`, 两方法分别显示0.306与0.656。不能把原blob编号当压缩数组行位置, 或把两个方法的blob编号互相连接; 本图不重新匹配候选、删掉背景或更换实例。

## 实验条件与生产说明

Emap是显式推荐level的独立实验, 根为`/storage/penghongen/Emap2lig/contour_level_20261026`。原命令`bash 训练与运行/sh/with_level.sh`, release`/home/penghongen/Feedback/Emap2lig/releases/Emap2lig_3c489443d595/Emap2lig`, launch`/home/penghongen/Feedback/Emap2lig/launches/423330/build_gate_job423330_20261026T202139_a2/`。现存生产说明为该release的`显式level实验/README.md`, 本地对应`C:/Users/15919/Desktop/Emap2lig/显式level实验/README.md`。

LigandSeek(CA2)使用既有Find_1推理根, 原评价、模型条件与CA2受体来源见[Find](../../../../追溯文档/source/Find.md)和[CryoAtom2受体](../../../../追溯文档/source/CryoAtom2受体.md)。代码读取旁直链`C:/Users/15919/Desktop/Pocket_Plus/src/inference/README.md`及`/home/penghongen/Feedback/Pocket_Plus/releases/Pocket_Plus_96938959ed1a/Pocket_Plus/src/inference/README.md`。显式level完整原件与成员资格见[Emap2lig-level](../../../../追溯文档/source/Emap2lig-level.md), 原网格预处理见[原始输入](../../../../追溯文档/source/原始输入.md)。本次只读取既有结果, 不重推理或改写其生产记录。

## 作者显示与会话核对

采用的8份PNG嵌在本图Office闭包, 明确属于作者显示原件。`--render-sessions`以独立原生进程依次打开对应8个古法CXS、完整读取地图、按作者显示画幅导出本次PNG并验证源会话前后SHA256相同。打开、渲染或临时窗口调整不保存回原CXS。科学数字取上述服务器数组, 不从图片或会话标签反推。唯一重建入口见[README](README.md)。
