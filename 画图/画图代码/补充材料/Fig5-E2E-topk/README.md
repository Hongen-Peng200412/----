# 补充 Fig5: 18条端到端Top-k曲线

本目录只重建`e2e-topk-success`这一页, 正式作者页在[E2E结果.pptx](../../../PPT/E2E结果.pptx). 每条曲线表示前K次计费尝试内至少成功一个目标的PDB比例, K固定1到10; 这不同于每PDB全部目标的完成比例, 不生成相对预算master. 科学条件见[trace.md](trace.md).

## 输出位置与文件

在项目根执行短命令, 默认新建`temp/figure-build/Fig5-E2E-topk/<UTC时间>/`; 时间含年月日、时分秒、微秒. 所有输出可整体清空, 可用`--build temp/自定空目录`固定本次位置.

```text
<本次构建目录>/
├─ candidate.pptx  # 本图一页可编辑作者候选
├─ data/
│  ├─ topk_data.json  # 恰好18条K1到10整数计数
│  ├─ plotted_series.json  # 画线时实际使用的K、分母、计数与百分比
│  └─ server_reads.json  # 服务器原件绝对地址、摘要与字节数
├─ figures/
│  ├─ e2e-topk-success.svg / .pdf / .png  # 同一四面板画面, PNG为600dpi
│  ├─ e2e-topk-success.alignment.json  # 面板几何核对
│  └─ e2e-topk-success.alignment.svg  # 面板几何核对叠加图
├─ manifest.json  # 一页图稿的标识与pt画幅
├─ native-shapes.json  # 作者显示前的原生图元数
├─ source-comment-before/  # 本次来源批注更新的临时副本
└─ matplotlib/  # 本次字体缓存
```

### data/topk_data.json

`full`有`real_stage1_only/real_stage1_matcher/cryo_stage1_only/cryo_stage1_matcher/emap2lig`共5条曲线, 全配体分母179. real/cryo分别表示GT/CA2受体, stage1_only为Find定位, stage1_matcher为Find加精确身份. `small_find`含`real_receptor/cryoatom2_receptor/emap2lig`三条, `small_match`含`real_receptor/cryoatom2_receptor`两条, 分母均77. `build.GT.local_cov-C`与`build.CA2.local_cov-C`各含`pose1_lt2/pose1_lt3/pose50_lt2/pose50_lt3`四条, 使用实际Match计费与第一轮DG Centre原姿态, 不计算Top5或其他三种方法. 合计18条, 每条是长度10的int列表, 轴位置0对应K=1, 位置9对应K=10.

`denominators`固定`{"full":179,"small":77}`, 零成功PDB仍在分母. `accounting_rule="match-aware-stage3-v2"`标明实际Match计费, `provenance.emap2lig_condition="explicit_emdb_level"`标明Emap输入条件. Find-only的小分子诊断使用真实范围外前景免费策略, 与实际Match计费分开, 不因共享文件就把两种序列混用.

### data/plotted_series.json

长度18的列表, 每项是实际画出的一条线. `panel`为a/b/c/d, `label`为原显示标签, `denominator`是179或77, `counts`为长度10的整数列表, `K`为1.0到10.0的float列表, `y_percent=counts/denominator*100`. 例如实际a面板`Find only · GT`的counts为`[148,160,165,165,166,166,167,167,167,167]`, 首点148/179约82.681564%. 文字末端避让只移动标签, 不移动这些纵坐标或数据点.

### candidate.pptx 与图稿

候选仅含本图一页, 原生文字和图形从本次SVG构造. `display.json`保留原作者图集6591300×8640763 EMU总画布和本页显示参数, 不将画布缩成较矮的SVG. 当前正式PPT双语备注原样复制, 本目录README/trace通过TRACE v3来源批注指路, 不覆盖作者图集. `manifest.json`为长度1的列表, `id/stem=e2e-topk-success`, width/height单位pt, notes为空构造占位; `native-shapes.json`保存转换前后定位用的原生形状数及pt画幅, 不代表预测候选数.

### data/server_reads.json

原件记录列表每项有`remote`绝对服务器文件地址、`sha256`原字节摘要和`bytes`原字节数. 实际姿态根为`/storage/penghongen/PocketXMol/final_evaluation/end_to_end/{GT,CA2}`, 正确身份受控根不参与本图. 本次不生成长期raw/accounting副本, D盘如有缓存只能是指定`D:/AdaLigand_Visualization/server`内的服务器原样文件.

## 稳定入口与职责

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/补充材料/Fig5-E2E-topk/run.py"
```

`data.py`只计算这18条曲线, `plot.py`只画本图. 计费和目标成员显式复用正文Fig6的`accounting.py/cohorts.py/actual_inputs.py/controlled_inputs.py`, 区域归属唯一复用正文Fig3的matching.py. SVG、PPT、文字避让和物理缩放等中性操作来自TOOLS, 不包含科学阈值. [trace](trace.md)定义完整科学选择, [执行记录](../../../../talk/refactor/执行日志.md)保存验收过程.
