# Handoff: Find、Emap2lig公平对接与端到端补充数据

Date: 2026-10-18

## Current State

本轮工作已经完成模型结果统一、缺少的预测区域对接、CPU评价、完成度统计，以及此前获准的中英文图文编译验收。后续重排展示不需要再次推理。当前`main`是作者写作进度；元数据已经获作者认可，但展示方案仍在探索，不应恢复实验分支中的旧稿，也不能把某份PPT或文字当成固定科学事实。

本次在`main`只补充数据归档、这份总handoff和交接执行记录，提交名为`———— 补充数据 & handoff ————`。没有重建Word、改动PPT、修改模型或操作服务器。作者开始交接时暂存的四份中英文稿和`画图/Find-Match-Build公平对比.pptx`不纳入提交；其他仓库的未提交工作保持原样。

科学资料优先从[补充数据目录](../../../补充数据/Find-Match-Build_20261018/README.md)读取。这里实物保存本轮29个面板、逐blob距离、共同实例配对、原Emap2lig逐姿态记录、821实例范围证据及来源散列，避免只从以后可能改写的图注反推结论。服务器完整科学根为`/storage/penghongen/Adaligand_E2E/test/test_0`。这次交接只核对本地已保存证据，没有重新连接服务器或核验当前作业状态。

## Completed

### 前因后果：为何有两批对接比较和三种Find范围

1. **2026-09-29：先评价Emap2lig-Build。** 复用已经完成的Emap2lig-Find，从Stage3的446个含碳、单残基、无缺失重原子实例中找到243个覆盖命中实例，只对其运行原Build。给定冻结精确SMILES，每例50姿态、100步，原`consistency_iou`排序，CPU计算世界坐标RMSD。237例完成，6例未通过原体素数／重原子数比例`[5,25]`，保留243分母。对应文件是补充数据的`metadata/emap_original/`，原服务器为`/storage/penghongen/Emap2lig/stage3_find_hit_build/`。
2. **这批旧比较并未对齐定位输入。** 同243实例上汇总的八条PocketXMol结果使用真实中心C0或真实包络E，分别配GT／CryoAtom2受体；Emap2lig则使用Find预测区域。因此它是已有结果的同实例汇总，不能被后来任何文案或改图变成“双方都用预测区域”的公平比较。
3. **2026-10-15至16日：补齐预测区域元数据。** 作者要求对F2–F1–Gaussian产生的所有blob保留Find和Match事实；只要原唯一对应属于Stage3，就给定正确SMILES并使用该blob中心对接，不受selected、Match是否正确或排名20以内限制。复用旧GT280、CA2268个对接请求，分别补齐24、25个，最终304／293项；Emap2lig243项直接复用。背景、范围外前景、错身份和没有正确候选的PDB仍保留在完整评价轨迹中。
4. **同一批元数据支持不同视图。** 可以只看Find检出、要求实际Match正确，或假定Match正确后比较Find→Build。共同命中两种Find的实例又能形成预测区域公平对接：GT235例、CA2230例，数值配对分别231、228例。这些都不需要为某张新图再次执行模型。
5. **2026-10-17：修正Stage1小分子范围。** 早期方案及图把Stage3的77 PDB／446完整小分子误用为Stage1“寻找小分子”。作者纠正后，从原Stage1全部类别实例和完整Find记录派生94 PDB／821个全部小分子统计；不限制单残基、原子完整性、Match或对接结果。原77／446数据保留，用途仍是Stage3及相应端到端测评。修正代码只在论文Stage1，不增加AdaLigand的`find_all_small`视图，不修改`ligandseek_pipeline/evaluate.py`。

### 科学元数据的真正来源

| 事实 | 已保存的原始依据 | 本次归档位置 |
|---|---|---|
| 完整目标轴 | 原held-out实例清单；全配体179 PDB／2,502实例 | `provenance/find/inventory.json`，保存原路径与SHA-256 |
| Stage1全部小分子 | 原Stage1的94-PDB集合；`Ori_Data/parse/<pdb>/occurrences.jsonl`中的原`small_molecule`类别 | `provenance/stage1_all_small/`含94份原文件、源散列及统计来源 |
| GT／CA2完整Find候选 | `画图/formal/E2E_accounting_20261004/sources/full_matcher.json`中的Find字段；源SHA-256以归档provenance为准 | 94／821已派生到`metadata/stage1_all_small/`；完整原容器留在本地原位 |
| Emap2lig完整Find | `/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/held_out_test_0/`的原逐PDB交集、区域大小、概率和blob | `provenance/find/sources.json`逐项列182份原文件；原NPZ仍在本地`画图/formal/fmb_20261015/sources/Emap2lig/find_metadata/` |
| 精确化学身份 | `/storage/penghongen/PocketXMol/data/smiles-v1/frozen/test.jsonl`与原Stage3 typed清单 | `metadata/emap_original/find_hit_subset.jsonl`、`provenance/find/identities.jsonl` |
| 真实坐标，仅供评价 | `/storage/penghongen/AdaLigand/Ori_Data/smiles_assets/SMILE_coords/v1` | 运行配置及原指标文件指向此共享输入，不把参考坐标送入采样模型 |
| 原Build50姿态和评分 | 原Emap2lig结果根的`build/<pdb>/<occurrence>/<launch>/` | `metadata/emap_original/build_occurrences.jsonl`逐姿态原CIF路径、评分和RMSD |
| 统一逐blob对接及CPU判定 | 统一根`evaluation/{GT,CA2,Emap2lig}/docking_results.jsonl` | `metadata/pipeline/<domain>/docking_results.jsonl`，原样复制 |
| 完整候选成功与失败轨迹 | 统一根`evaluation/<domain>/evaluation.json`及`match/all_ligand/{GT,CA2}/evaluation.json` | 大型轨迹保留服务器；归档保留其派生事件、分母和逐blob结果，不声称这些大型文件全部入Git |

上述原始数据和代码函数先于图文表达。`provenance/source_manifest.json`记录每个副本原路径、字节数和SHA-256；`provenance/git_endpoints.json`记录代码定位。论文PPT页、自然语言结论和自动图号只是消费这些数据的界面。

### 数据规模与已经完成的计算

| 条件 | 全部Find blob | Stage3 PDB内全部blob | 合格Stage3对应blob | 实际补跑 |
|---|---:|---:|---:|---|
| LigandSeek2 GT | 2,251 | 598 | 304 | 旧280项之外补24项 |
| LigandSeek2 CA2 | 2,407 | 632 | 293 | 旧268项之外补25项 |
| Emap2lig | 63,342 | 30,561 | 243 | 全部复用；237姿态成功、6原筛选失败 |

正式统一目录实际复制了Find最终概率、blob和对应，Match结果，以及Build姿态、置信度、评分、科学输入和指标；不是只存旧路径链接。原始密度、受体特征、SMILES图／语言表征和权重仍作为共享输入保留原处。没有删除旧结果。

原Build权重为`KiharaLab/Emap2lig`的`emap2lig-build-v0.0.1.safetensors`，115,242,996字节，SHA-256为`e9af59c83fe5d5d5b63c4c6edb6cf2002d8e576b9c96490ab08d2fa14dcf968b`。服务器直连下载失败后通过镜像取得相同文件，哈希核验后使用。CentOS原GCC4.8.5导致Triton缺少`stdatomic.h`的门控失败，改用既有conda GCC11.4.0后原Build正常运行；没有因此改科学计算。

### 预测区域公平对接的确定结果

两侧都使用各自Find预测区域：PocketXMol-tuned给定blob中心，Emap2lig-Build给定原生blob。两者使用正确精确SMILES、50姿态、100步。下表中位数只计算四项距离均有效的同一配对集合，成功率分母保留全部共同命中实例。

| 比较条件 | 数值配对／共同命中 | 方法 | Top-1中位RMSD (Å) | best中位RMSD (Å) | Top-1 <2 Å | Top-1 <3 Å |
|---|---:|---|---:|---:|---:|---:|
| GT | 231／235 | PocketXMol-tuned | 0.853 | 0.634 | 202／235 | 210／235 |
| GT | 231／235 | Emap2lig-Build | 1.827 | 1.320 | 133／235 | 197／235 |
| CA2 | 228／230 | PocketXMol-tuned | 1.020 | 0.707 | 187／230 | 201／230 |
| CA2 | 228／230 | Emap2lig-Build | 1.826 | 1.324 | 132／230 | 195／230 |

逐实例数据在`metadata/figure_data/paired_pose.csv`，完整均值、分位数、best成功数及配对差在`data.json::pairs`。GT与CA2分别取交集，不擅自缩成三者共同228个数值实例。

### Find与假定Match正确的完成度

完成度以每个PDB成功的不同实例数除以该PDB完整目标数，再在完整PDB轴上取等权宏平均。下表是已有数据的100%／300%快照，不是新的模型运行，也不表示只有这些横轴位置可以画。

| 范围 | 方法 | 100%宏平均 (%) | 300%宏平均 (%) |
|---|---|---:|---:|
| 全配体179／2502 | GT | 66.40 | 71.72 |
| 全配体179／2502 | CA2 | 55.56 | 63.29 |
| 全配体179／2502 | Emap2lig | 25.91 | 30.09 |
| Stage1全部小分子94／821 | GT | 70.53 | 73.30 |
| Stage1全部小分子94／821 | CA2 | 59.82 | 68.51 |
| Stage1全部小分子94／821 | Emap2lig | 44.18 | 51.55 |

| 假定身份正确，严格RMSD <3 Å；均为77／446 | Top-1 100% (%) | Top-1 300% (%) | best 100% (%) | best 300% (%) |
|---|---:|---:|---:|---:|
| Emap2lig | 38.24 | 43.28 | 42.52 | 49.97 |
| LigandSeek2 CA2 | 49.62 | 55.03 | 58.04 | 66.27 |
| LigandSeek2 GT | 63.22 | 64.20 | 70.49 | 71.46 |

严格2 Å及实际Match视图也已经存在`data.json::panels`。原实际Match的8个小分子面板已与旧`E2E_completion_20261011/completion.json`的完整曲线、逐PDB分布、事件及全候选统计逐项核对一致，不因这轮补充比较而改写。

## Decisions

### 必须保留的科学与实现边界

- **对应**：始终先在全部真实配体中确定唯一对应，再判断类别或Stage3范围。双向覆盖均至少0.3，取几何均值最大者；直接复用Matcher原`_target_from_intersections`及原并列规则。不再向作者重复求证这一已固定定义。
- **顺序**：当前评价为selected在前，每段按原blob概率均值降序，同分按原blob编号升序；不是Gaussian分数降序。扩展`evaluation.json`另存`gaussian_rank`供以后选择。unselected、排名20以后或错Match的候选不截去；完整轨迹不能由成功姿态文件代替。
- **Find范围**：179／2502是全配体，94／821是Stage1全部小分子，77／446是Stage3完整小分子。Stage1统计不受残基数、完整性、SMILES支持、Match或姿态成败约束。
- **正确身份视图**：Build使用对应目标的精确SMILES，只以预测区域中心定位；这是assume-matched条件，不冒充实际Match输出。实际Match视图另要求预测字符串正确，并沿原实际尝试规则统计。
- **背景与范围外候选**：纯Find小分子／assume视图中背景占一次尝试，已唯一对应到范围外真实配体的前景跳过；全配体Find每个blob均占位置。实际Match视图按原`accounting_action`区分：背景始终计数，非小分子被错判小分子计数，范围外小分子正确识别可跳过，错误身份仍计数，Stage3目标始终计数。不得把这几种口径简化成同一条规则。
- **ratio统计**：PDB有$N$个目标时，相对预算$\rho$允许$\lfloor\rho N\rfloor$次当前视图的计数尝试。重复命中仍占位置，但每个真实实例只增加一次完成度。零候选、零成功及失败保留分母；PDB宏平均不等于微平均。原绘图曲线到300%，原完整事件和最终统计不以300%或20次为上界。
- **姿态与评价**：严格RMSD <2／3 Å，不做额外刚体叠合；沿用原图同构、`CalcRMS(maxMatches=30000)`及原回退与异常口径。Top-1由各模型自己的评分选择，Top-5和best只在该排名范围内取最低有效距离；参考RMSD不参与采样、身份预测或姿态排名。显式立体检查只约束精确SMILES明确声明的立体信息。
- **PocketXMol**：RA＋T0、官方FP32推理路径、预测中心选袋及模型原点均复用原入口，不加新评分器或噪声机制。中心口袋严格15 Å，模型世界坐标只还原一次；密度使用local_cov既有80³外围裁块／每块11³局部读取机制，不因后续作图改变采样输入。
- **共享入口**：复用原Find、Matcher Dataset和采样／评价代码，不另建prediction Dataset或主逻辑校验框架。原Matcher `mode=test`仍打开未参与模型前向的监督字段，这是已接受的复用边界；不能声称整个加载栈完全不读评价标签。Build采样请求本身不带参考构象，评价阶段单独读真实坐标。
- **范围**：通用入口面向已经准备的密度、受体特征、SMILES图及语言资产，不承诺任意原始MRC／CIF／新SMILES的自动准备。原生失败和缓存语义保留，不能为提高展示数字自动重试或删除失败。

### 作者当前写作状态及尚未定案的展示方向

作者保留`main`作为论文写作进度，并有意让它与实验分支交叉：同一批代码和数据可以保留，而正文、图注、页面组织继续编辑。`main`包含这轮成果，不要求成为旧实验分支的提交后继；这不是待修复的Git拓扑。

作者**可能**考虑：Stage3只展示一组公平比较；E2E ratio进入正文、top-k移至附录并弱化；再调整abstract和introduction的宣称。这些只是探索方向，**不是最终决定，不构成后续执行命令**。GT／CA2两组配对、ratio与top-k相关原数据都须保留，不能提前删去未选中的结果，也不能替作者决定“仅保留一组”究竟指哪组。

本次没有修改这些写作内容，没有重建或覆盖作者工作稿。以后明确获得相应写作授权时，再以当时`main`和作者意见为准，不回填旧叙述作为新稿。

## 逻辑与代码接续

| 仓库与代码 | 现有职责 | 接续时优先阅读 |
|---|---|---|
| AdaLigand `ligandseek_pipeline/run.py` | 按Find→Match→Build→evaluate调用各组件独立环境，进程内数值库线程设1 | `ligandseek_pipeline/README.md`、3份正式YAML |
| `find.py`、`match.py` | 复用已有完整Find／Match结果；缺少时才调用原组件 | 原Matcher `test_set.py`与Dataset，不新造推理栈 |
| `build.py` | `known`给正确身份，`match`使用实际预测身份；调用PocketXMol `ConditionedDockingDataset`、`sample_occurrence`或Emap2lig `run_one` | `scientific_input.json`的精确字符串、给定中心和种子 |
| `evaluate.py` | 逐blob读取或计算指标，按输入序接回完整候选，扩展轨迹并派生Find／assume／actual | `evaluate_candidate`、`evaluate_pipeline`；本轮Stage1纠偏未改此文件 |
| `completion.py` | 原计数动作、精确有理数事件、固定预算分布和全候选统计 | `accounting_action`、`make_panel`，不另实现均值或去重逻辑 |
| Matcher `test_smallmolecule/build_manifest.py` | 原冻结清单、原Find中心及唯一对应 | `_target_from_intersections`，不是作图时重贴标签 |
| Emap2lig `测试Find出来的Build/main-code/` | 原Build输入、推理、CIF及评分评价适配 | `run_build.py`、`evaluate_build.py` |
| 论文 `画图/画图代码/stage1/find_completion_20261017/` | 从完整Find及原类别得到94／821的三个面板 | 独立`assemble_data.py`和README |
| 论文 `画图/画图代码/stage3/fmb_20261015/` | 连接原评价结果形成29面板及预测区域姿态配对 | `assemble_data.py`，不是图形或图注本身 |

正式统一运行代码release为`/home/penghongen/Feedback/AdaLigand/releases/AdaLigand_0e2ed5a4829f/AdaLigand`，内容SHA-256为`0e2ed5a4829f6a4312dbf49c0d59536f4da364cbd8d203cb0422a6a254dffd9a`；运行配置修正提交`759fee9`。PocketXMol组件使用`PocketXMol_f4d72bbea387`，中心best为`/storage/penghongen/PocketXMol/training/local_cov-C-T0-RA-b72/checkpoints/step=24800.ckpt`。Matcher是`strongest-1`，精确checkpoint等路径已保存在归档配置。

AdaLigand共同基点`81c87aa736b5907aa32b47ddf4e28171386a9558`，实现线`codex/find-match-build-pipeline`，学习线`Learn/find-match-build-pipeline`端点`91bdf0e`。两线最终树、AST、配置与测试等价后已推进累计分支，证据见归档`evidence/pipeline/git-equivalence.json`。本次读取的累计HEAD为`ec91aa11859608164f662e31ce81b96f8b9fc0a5`，作者随后已有5份暂存注释及一份未暂存计划修正；本次均未提交或覆盖。

论文研究实现由`7f13967`、`c5e0b2d`、`dc8818b`依次保存公平比较、Emap2lig Find补充、Stage1范围纠偏；研究分支后来到`5f8a9a5`。本次开始`main=54aa38455678afedcfd71eabfd3f7d144242fef3`；它与研究分支的已提交树差异仅在四份写作Markdown，代码已经保留。没有执行merge、cherry-pick、rebase或重新创建学习分支。

## 论文制图、presentation与编译接续

绘图数据入口是`metadata/figure_data/data.json`、`paired_pose.csv`及`metadata/stage1_all_small/`；不应从PPT散点坐标或正文四舍五入数字反推统计。当前正式绘图代码读取本地`画图/formal/fmb_20261015/`和`画图/formal/Stage1_find_completion_20261017/`；这些原目录仍在。本归档提供独立稳定副本，没有为归档修改原入口或作者文件。

`plot.py`只决定布局、颜色、双语图注；`completion_plot.py`保留既有完成度画法；`svg_shapes.py`和`assemble.mjs`把同源SVG展开为原生PPT文字、散点、路径及箱体，组件保持可编辑。`ppt_metadata.py`只对temp候选稿写双语备注和传统`@@`图名批注，再用PowerPoint实际渲染；不关闭作者原文件。

这轮已经制作过三类展示：全配体／全部小分子的Find完成度2×3；GT／CA2共同命中姿态2×2；assume-matched完成度2列6行（Emap2lig、CA2、GT各四条件）。稳定图名分别为`find-only-instance-completion`、`stage3-predicted-region-head-to-head`和`supp-find-correct-match-build`。这些是**已实现展示入口**，不是作者必须保留的布局。既有顶层PPT为`画图/Find-Match-Build公平对比.pptx`；作者正在编辑它，不要用候选稿覆盖。

PPT图注从备注中的中文段和`ENGLISH:`后英文段读取，`@@图名`决定Markdown引用；以`pptfig`插图、`figref`引用，转换器自动编号。图号随文章顺序改变，不以本handoff中的日期或旧Fig.4／Fig.14序号锁死。数学写为`$...$`，转换为Word原生公式。

论文源稿为`论文草稿.md`／`draft.md`，补充材料为`补充材料.md`／`supplementary.md`。Stage1新增统计、Stage3公平对接、assume-matched补充分析曾按作者当时要求分别进入这些章节；现在如何迁移由作者继续决定。语言沿用论文RULES和Nature相关skills，不追加过度限定。

### 历史正式运行与生成命令

以下是已经执行并留证的入口，供复现和定位；**本次handoff没有重新运行**。测试、门控见下一节，不混作正式实验命令。

```bash
# Emap2lig原243实例Build，Emap2lig正式release内
bash 训练与运行/sh/stage3_build.sh
# AdaLigand统一管线，分别调用同名正式配置
bash 测评数据代码/端到端测评/sh/run.sh GT
bash 测评数据代码/端到端测评/sh/run.sh CA2
bash 测评数据代码/端到端测评/sh/run.sh Emap2lig
```

论文仓库内的历史正式统计与制图顺序：

```powershell
python -B 画图/画图代码/stage1/find_completion_20261017/assemble_data.py
python -B 画图/画图代码/stage3/fmb_20261015/assemble_data.py
python -B 画图/画图代码/stage3/fmb_20261015/plot.py
python -B 画图/画图代码/stage3/fmb_20261015/svg_shapes.py
node 画图/画图代码/stage3/fmb_20261015/assemble.mjs
python -B 画图/画图代码/stage3/fmb_20261015/ppt_metadata.py
```

绘图使用`D:/Anaconda/python.exe`，Node使用Codex工作区运行时。候选输出在`temp/fmb_20261015/`，检查后再按获准范围发布；不能因这份旧命令序列而覆盖作者当前PPT。

Word继续使用根目录`md_to_word.py`及`md_to_word_operation.py`，英文加`--english`；Python为Codex bundled Python，命令细节见`RULES/执行记录.md`的2026-10-16／17条目。修改或编译前读`转换工具/README.md`。两份英文阅读版因作者原文件占用，旧轮新输出命名`draft.operation.fmb.docx`和`supplementary.operation.fmb.docx`，不能把标准同名旧Word当作该轮新输出，也不能自动关闭作者窗口。

## 验收、异常与历史资源

- **逻辑验收**：原管线3项CPU测试通过；串行／两进程逐候选结果和顺序一致，严格阈值、零候选分母、异常传播与缓存跳过均已验收。非测试示例与原计数函数一致，8个实际Match面板保持不变。
- **GPU验收**：validation `5irx/0`以50姿态、100步验收；新入口和原入口的45项首步输入、权重、模型eval状态及CPU／CUDA随机状态一致，均100次前向、50个姿态。原生计算自身不是逐位可重复：新旧最大坐标差0.1315 Å，原入口自身重复最大差2.28 Å；结论是输入和T0机制实质对齐，不宣称最终姿态逐元素相同。完整原因及报告路径保存在原AdaLigand日志。
- **已解决分叉**：第一次GPU门控错误地用绝对差0.001 Å作为最终构象门槛，未开始正式测试；查明原生重复性后才继续。后来GT／CA2已补齐对接，但CPU汇总的类别清单指错为无`type_tag`的语言清单；指回原typed身份清单后从缓存完成，未重复推理。保留全部旧release、日志和产物。
- **Stage1纠偏验收**：94份类别文件原SHA匹配；每PDB候选数与原Stage1一致；原26面板及所有姿态配对完全不变；合成非测试例覆盖背景、零候选、全类别优先对应和重复命中。三路独立审查已完成，本次只归档，不机械重审。
- **图文历史验收**：10月16日八份Word共249页已逐页检查；10月17日纠偏后四份正文共206页，200页正文区域与旧版逐像素相同，6页实际查看。历史PPT三页为3,504／1,998／4,123个可编辑原生对象，无整页栅格；这些结构证据用于追溯当时的输出，不约束作者未来合并页面。本次没有给作者当前改稿重新出具版面验收。
- **资源历史**：原Emap2lig正式任务是H200 `390405/hnode03`；统一管线GT为`403776/gnode11` A6000、4 CPU，CA2后接Emap2lig为`403774/hnode02` H100、16 CPU。2026-10-16最后成功核对时已回`try_lock`且`after_lock`保留。此处是历史，不是2026-10-18实时状态；不据此重新接管资源。

本次归档的只读／散列核查与Git保护记录在`temp/handoff_20261018/`；正式实验命令与这些检查命令分开。全部复制文件逐字节核对原文件，JSON／JSONL、29面板与配对分母另作静态核对。本次没有运行模型、改评价算法或重新提交任何作业。

## Next Actions

本轮计算没有待续跑事项。作者可以基于已接受元数据继续研究展示方式；是否只留一组公平比较、是否迁移ratio／top-k、怎样同步abstract／intro均等待作者进一步选择，不能从本handoff自行推导为获准写作任务。

接续时先读`main`现稿和作者最新意见，再从元数据取数；若只改展示，不触碰原科学结果、重跑模型或改分母。保留旧研究分支和其他仓库历史，不为使Git图形线性而合并回旧稿。

## Files To Reopen

- [补充数据README](../../../补充数据/Find-Match-Build_20261018/README.md)：目录、文件字段、分母与来源。
- [科学文件来源清单](../../../补充数据/Find-Match-Build_20261018/provenance/source_manifest.json)及同目录`git_endpoints.json`。
- `AdaLigand/测评数据代码/端到端测评/结果与日志/总日志.md`及GT／CA2／Emap2lig逐实验日志；归档内有已提交快照。
- `Emap2lig/测试Find出来的Build/结果与日志/`：原243实例实验的前因后果、原生环境和50姿态评价；归档内有已提交快照。
- [论文执行记录](../../../RULES/执行记录.md)：历次正式统计、制图、编译和验收命令。
- [Stage1统计入口说明](../../../画图/画图代码/stage1/find_completion_20261017/README.md)和[共享制图入口说明](../../../画图/画图代码/stage3/fmb_20261015/README.md)。
