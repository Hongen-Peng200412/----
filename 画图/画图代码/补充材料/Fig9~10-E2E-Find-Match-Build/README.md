# 补充 Fig9~10: 实际 Find-Match-Build

本目录是作者指定的两图组合单元, 页序为CA2、GT. 每页六面板, 三行分别是原Top1、Top5、best-of-50, 两列分别要求重原子RMSD严格小于2Å和3Å. 这里只重建自动身份匹配的12组统计, 不读取受控正确身份实验或Emap2lig原件. 正式作者图集为[E2E结果.pptx](../../../PPT/E2E结果.pptx), 科学选择与计费口径见[trace.md](trace.md). 稳定入口只生成本目录的2页候选, 不覆盖正式作者PPT.

## 本次输出位置

无参数时, `run.py`新建项目根`temp/figure-build/Fig9~10-E2E-Find-Match-Build/<UTC时间>/`, 时间含年月日、时分秒与微秒. 显式`--build`只能指向根temp内全新或全空的目录. 以下所有文件都属于本次派生材料, 可整体清空; 后续重建不以旧temp为输入.

```text
<本次构建目录>/
├─ candidate.pptx  # 仅含本目录声明图名的可编辑作者版候选
├─ data/
│  ├─ master.json  # 当前请求的12组完整条件统计、逐PDB事件和均值区间
│  ├─ source_data.csv  # 条件、预算和PDB的逐项数值
│  └─ server_reads.json  # 本次实际原件地址、SHA-256和字节数
├─ figures/
│  ├─ <stem>.svg / .pdf / .png  # 同一画面的矢量稿及栅格预览
│  ├─ <stem>.alignment.json  # 面板几何检查
│  ├─ <stem>.alignment.svg  # 面板几何检查叠加图
├─ manifest.json  # 当前页的文件前缀、画幅与备注占位
├─ native-shapes.json  # SVG转原生形状的逐页数量
├─ source-comment-before/  # 本次来源批注更新的临时比对副本
└─ matplotlib/  # 本次字体缓存
```

`<stem>`逐项等于`figure.json`声明图名; 正文主图的临时图稿前缀特为`e2e-main-top5`, 正式完整图名为`e2e-main-top5(v1)`, 对应关系由本目录`display.json`明确给出. 其他图的前缀与完整图名相同. 本次原始读取仅在内存中解析, 不另建长期raw或accounting镜像.

## 科学条件与逐PDB数值

### data/master.json

顶层`metadata`记录本次实际采用的条件、对应范围和统计方法, `panels`按完整条件ID保存12组统计, `summaries`保存同组条件的固定预算摘要. 这里的一个`panel`是一组任务、受体、原排名数和RMSD阈值的统计, 不等于画面中的一块坐标轴. 例如`actual_CA2_pose5_rmsd3.0`表示CA2实际全身份计费、模型原排名前5姿态的最低重原子RMSD严格小于3Å.

`metadata.conditions`只列本次实际请求的条件, 每项包含`scope/domain/pdb_count/occurrence_count`. 仅有Emap2lig条目才附`emap2lig_level="explicit_emdb_level"`; 不为仅含实际GT/CA2曲线的输出添加Emap或全配体范围. `bootstrap_replicates=10000`与`bootstrap_seed=20261020`固定PDB bootstrap, `ranking`声明原Top1/Top5/best50, `completion_unit`声明PDB等权完成度.

每组`panels[ID]`有以下契约:

| 字段 | 容器、含义及具体示例 |
| --- | --- |
| `id/scope/domain` | 字符串, 如`actual_CA2_pose5_rmsd3.0`、`actual`、`CA2`; scope区分`find_full/full/find_small/find_match_small/assume/actual`, domain区分`GT/CA2/Emap2lig` |
| `threshold_A/pose_limit` | float/int或null, 如3.0/5; 定位或身份统计不涉及构象时两者为null |
| `pdb_count/occurrence_count` | int, 本组完整目标分母, 如77/446, 不按当前成功数缩小 |
| `success_events` | dict[PDB,list], 每个PDB保留完整键; 列表每项含原真实`occurrence_id`与首次成功计费号`first_success_attempt`, 如0/58; 零成功PDB为空列表 |
| `curve` | dict, 同长度的`budget_percent/budget_numerator/budget_denominator/mean/median`; 比例端点由精确分数保存, 见下文 |
| `distributions` | dict, 字符串键`0/50/100/200/300`, 每键含完整PDB逐项记录, 按PDB名排序, 不只保留成功项 |
| `all_candidates_final` | dict, 完整原候选全部用尽后的计数与比例, 不被300%显示范围截断, 见下文 |
| `polyline` | dict, `is_step=true`, `budget_percent`与curve相同, `mean_percent=100*curve.mean`, 只用于阶梯显示 |

`curve`的`budget_numerator/budget_denominator`表达相对预算`K/N`, `budget_percent`为该值乘100. 例如分数`1/78`显示为约1.282051%, 而不是将一个浮点近似值再向下取整决定预算. `mean/median`是对应事件完成后的PDB等权完成比例, 范围0-1; 曲线向右保持, 不平滑成功事件. `curve`只显示0到300%, 完整候选末态另存`all_candidates_final`.

`distributions`每项含`pdb_id/success_count/target_count/attempt_budget/completion`. 以下是实际产物中`actual_CA2_pose5_rmsd3.0`、100%预算的一条完整记录:

```json
{"pdb_id":"11jb","success_count":78,"target_count":78,"attempt_budget":78,"completion":1.0}
```

`target_count`是该PDB完整合格目标数, `attempt_budget=budget_percent*target_count//100`, `success_count`是在预算内首次成功的不同原实例数, `completion=success_count/target_count`. 所有当前PDB都有非零目标, 无成功时比例为0, 原失败或未检出不会成为缺失PDB.

`all_candidates_final.mean/median`是完整候选用尽后的PDB等权完成比例, `success_occurrence_count`是去重成功实例总数, `zero_completion_pdb_count/full_completion_pdb_count`分别是零完成和全完成PDB数, `raw_candidate_count`是包含免费跳过项的原候选总数, `charged_attempt_count`是完整扫描消耗的计费尝试总次数. 这些整数不是300%预算内的次数.

`summaries[ID][预算]`包含`mean/median/ci_low/ci_high`, 四项单位均为百分比. 例如格式`{"mean":50.0,"median":50.0,"ci_low":40.0,"ci_high":60.0}`仅为构造示例; 实验观测取本次JSON. CI对同一完整PDB轴做10000次等权重采样, 取均值的2.5%/97.5%分位. 各组相同PDB数使用相同随机索引, 不把实例合并成另一分母.

### data/source_data.csv

每行表示一个具名条件、一个固定百分比预算、一个PDB. 列为`panel_id/budget_percent/pdb_id/success_count/target_count/attempt_budget/completion`, 含义与上面相同. 通过`panel_id`和`pdb_id`连接, 不按不同文件中的行位置猜测对应关系. CSV使用UTF-8 BOM; completion仍为0-1比例, 未乘100.

## 可编辑候选与来源核对

### candidate.pptx

候选仅含本目录声明的2页. 每页先由本次SVG转换为独立可编辑文字、线条、散点和路径, 再用`display.json`恢复作者图层、样式和位置. 统计图统一保留原作者图集的6591300×8640763 EMU画布, 不因拆成单页改用更矮的SVG画幅. 1pt=12700 EMU. 作者当前双语备注按完整图名从正式PPT原样复制; 来源短批注由本目录声明生成TRACE v3, 指向README和trace. 入口不会覆盖作者图集.

### figures/<stem>.svg / .pdf / .png

三种文件对应相同科学画面, SVG与PDF为矢量稿, PNG为预览; 正文主图PNG为450dpi, 补图为600dpi. 作者版候选还应用了原图集的显示模板, 所以SVG单独画幅和最终PPT总画布不同. `alignment.json`与同名叠加SVG只描述面板几何, 不参与科学评价.

### manifest.json / native-shapes.json

manifest列表按本目录页序保存`id/stem/width/height/notes`, 宽高单位pt, notes在科学图元阶段是空占位. native-shapes列表保存同页`id/shapes/width_pt/height_pt`, shapes为作者显示作用前的SVG原生形状数量, 不能用来推断候选blob数或成功实例数.

### data/server_reads.json

顶层为原件记录列表, 每项`remote`为服务器绝对文件地址、`sha256`为原字节摘要、`bytes`为原字节数. 例如小分子成员来源是`/storage/penghongen/Matcher/manifests/test_smallmolecule_v1/identities.jsonl`. 记录只核对本次实际读取, 下一次不能把它或本次master当成科学输入. 指定D盘原样缓存仅限`D:/AdaLigand_Visualization/server`.

## 稳定运行与代码职责

在项目根执行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/补充材料/Fig9~10-E2E-Find-Match-Build/run.py"
```

`figure.json`声明当前页与正式图集, `build.py`逐项列出本图条件, `plot.py`拥有本图组合. 正文Fig6唯一拥有`cohorts.py`完整目标成员、`accounting.py`全身份计费、`actual_inputs.py`实际实验读取、`controlled_inputs.py`受控实验及Emap原交集读取、`prepare.py`具名条件组装、`completion.py`精确预算与PDB统计、`completion_artists.py`完成度画法. 关联补图显式调用这些科学文件, 不复制规则; 中性供应和图元运输分别由TOOLS/server_io及TOOLS/ppt负责.

[trace.md](trace.md)保存本图选择和科学含义. 实验生产命令、原release与资产见[Find](../../../../追溯文档/source/Find.md)、[Match](../../../../追溯文档/source/Match.md)、[Build](../../../../追溯文档/source/Build.md)、[受控身份E2E](../../../../追溯文档/source/E2E-受控身份.md)、[实际计费E2E](../../../../追溯文档/source/E2E-实际计费.md)、[Emap2lig显式level](../../../../追溯文档/source/Emap2lig-level.md). 实际验收过程见[整理执行记录](../../../../talk/refactor/执行日志.md).
