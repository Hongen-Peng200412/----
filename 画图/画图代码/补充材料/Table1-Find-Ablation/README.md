# 补充 Table1: Find 六变体消融

本目录只读取11份服务器原始metrics, 生成六模型×六指标的表格, 不调用任何图的重建或计时统计. `table.csv`保留原精度, `table.md`用于人工核对三位小数. 入口不覆盖论文原表或Word, 实验来源与六行含义见[trace.md](trace.md).

## 本次输出

无参数时, `run.py`新建项目根`temp/figure-build/Table1-Find-Ablation/<UTC时间>/`, 时间含年月日、时分秒和微秒. 也可显式指定一个全新的空`--build`目录. 所有输出可再生、可整体清空.

```text
<本次构建目录>/
├─ table.csv  # 六变体的36个原精度数值, UTF-8 BOM的CSV
├─ table.md  # 同行同列的三位小数Markdown表
└─ source_reads.json  # 11份原件的服务器绝对地址、字节数和SHA-256
```

### table.csv

第一行为列名, 随后六行依次是`Density only`、`+ Difference density`、`+ Density bank`、`+ Receptor features`、`+ Centroid encoding`、`LigandSeek-Find`. 第一列`模型`是标签; 六个float列依次为`CA2 Dice`、`CA2 PRAUC0.3`、`CA2 PRAUC0.5`、`GT Dice`、`GT PRAUC0.3`、`GT PRAUC0.5`. CA2是CryoAtom2预测受体条件, GT是真实受体条件. 所有指标为0-1比例, 每个原metrics的`pdb_count=179`, 是PDB等权宏平均, 不按实例数加权. CSV保留Python对原JSON数字的完整写出精度, 不用格式化后的Markdown数字反向计算.

六行分别表示仅密度、增加差分密度、增加密度库、增加受体特征、增加质心编码和最终Find候选处理. 第一行不读受体特征, CA2/GT两组显示值实际来自同一份原metrics, 不能把相同数字解释为两次独立受体实验.

### table.md

列名、行名、顺序与CSV完全相同, 只将数值格式化为三位小数. 例如实际`LigandSeek-Find`行为`0.477 | 0.541 | 0.447 | 0.584 | 0.663 | 0.558`, 原精度见同次CSV. Markdown没有新增分母或缺失占位, 六行36个数都直接来自原metrics.

### source_reads.json

顶层`reads`为长11的列表. 每项`remote`是原metrics的绝对服务器路径, `sha256`是原字节SHA-256, `bytes`为原字节数. 例如GT最终Find读取`/storage/penghongen/AdaLigand_stage1_inference/Find_1/真实受体/artifacts/Find_1/held_out_test_0/evaluation/f2_centered_gaussian_macro_selected.metrics.json`. 此文件用于核对原件身份, 不作为下一次重建的数值输入.

## 稳定入口

在项目根执行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/补充材料/Table1-Find-Ablation/run.py"
```

`figure.json`声明类型`table`、入口与两份主要输出. `build.py`直接拥有此表的原metrics地址和列映射, 只调用`TOOLS/server_io`提供的中性原字节读取. 科学指标是原实验已生产的汇总, 此表不需要调用正文Fig3的图形统计或把表格伪装成某张图的副作用. 指定D盘原样缓存为`D:/AdaLigand_Visualization/server`.

生产命令、原release和配置由[Find实验来源](../../../../追溯文档/source/Find.md)维护; 本表的显示选择见[trace.md](trace.md). 逐次验收过程见[整理执行记录](../../../../talk/refactor/执行日志.md).
