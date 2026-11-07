# 正文 Fig3: Find 主结果

本目录只重建正文Fig3, 完整图名为`stage1-overall-performance(v1)`. 正式图集是[stage1结果.pptx](../../../PPT/stage1结果.pptx). 入口生成一个单页、原生可编辑的候选PPT, 不覆盖作者图集; 当前双语备注在候选装配完成后从正式图集中按完整图名原样复制. 本图的科学输入与筛选口径见[trace.md](trace.md).

## 本次构建文件

运行位置固定在项目根`temp/`内. 无参数时, `run.py`自动新建`temp/figure-build/Fig3-result-Find/<UTC时间>/`; `<UTC时间>`为该次运行的年月日、时分秒和微秒. 以下用`<本次构建目录>`表示这一实际目录, 所有文件都可再生并可整体清空.

```text
<本次构建目录>/
├─ candidate.pptx  # 当前完整图名的一页可编辑候选
├─ data/
│  ├─ plot_data.json  # 本图所需条件的完整逐PDB指标与绘图统计
├─ stage1-overall-performance(v1).svg  # 当前画面的矢量导出
├─ stage1-overall-performance(v1).pdf  # 当前画面的PDF导出
├─ stage1-overall-performance(v1).png  # 当前画面的600dpi导出
├─ scenes.json  # SVG文字和几何转成的单页场景
├─ manifest.json  # 单页标识、画幅与备注占位, 不含图元
├─ source_reads.json  # 本次实际读取的服务器原件地址、字节数和SHA-256
├─ assembly.json  # PPT装配后的图元计数
├─ stage1-overall-performance(v1).alignment.json  # Matplotlib面板几何检查
├─ stage1-overall-performance(v1).alignment.svg  # 面板几何检查的叠加图
├─ candidate.pptx.inspect.ndjson  # 候选PPT结构检查导出
└─ matplotlib/  # 本次字体缓存
```

上述文件均为本次派生材料, 下一次重建从服务器原件或D盘原样缓存读取, 不把这些JSON或图片当成科学来源.

## 绘图数值与画面

### data/plot_data.json

本文件保存本图的单一实验条件和逐PDB指标, 由本目录`build.py`调用正文Fig3的`data.py`写出. `condition="explicit_emdb_level"`. `cohorts.full`有179个PDB, `cohorts.small`有94个PDB; `n`等于相应`ids`列表长度. `full.ids`开始为`["9ter","30yu"]`, `small.ids`开始为`["9lfa","9bjj"]`; 此处只是首两项片段, 文件中保存完整名单.

`models`以`GT`、`Cryo`、`Emap`为键, 分别表示真实受体的LigandSeek-Find、CryoAtom2受体的LigandSeek-Find和本图指定条件的Emap2lig-Find. 本图实际指标键为dice、oto03、precision、recall. `dice`为语义Dice, `oto03/oto05`为双向覆盖阈值0.3/0.5的一对一实例PRAUC, `precision/recall`和带05后缀的字段为最终已选候选在对应阈值下的实例精确率/召回率. 全部数值都是0-1比例.

每个方法的`values[指标]`为长度`n`的float列表, 沿`ids`逐PDB对齐. `bars[指标]`包含PDB等权`mean`与bootstrap区间的`lower/upper`, 只对本图使用的Dice/PRAUC存在. 顶层`bootstrap_replicates=10000`、`bootstrap_seed=20260922`固定重复次数和随机种子. 例如一个条形摘要的结构是`{"mean":0.5,"lower":0.4,"upper":0.6}`, 此例只展示格式, 不是实验观测.

`distribution[指标]`只对本图的precision/recall存在. `grid`是0到1的161个横坐标, `density`是同长度的反射核密度估计, 按自身最大值归一到1, 不是概率质量; `quartiles`依次为25%、50%、75%分位. 顶层`kde_bandwidth=0.045`为估计器的带宽系数. 没有请求的字段不会以零值补齐.

正文Fig3另有`resolution`, float列表, 长度等于本范围PDB数, 单位Å, 与`ids`逐项对应. `paired_counts`的`find_higher/equal/emap_higher`表示CA2相对Emap2lig的逐PDB Dice比较, 相等容差为1e-12. 实际full计数是141/15/23, 三项和179; small为68/7/19, 三项和94. `paired_metric="dice"`明确散点和计数没有混用PRAUC.



### candidate.pptx

PPT仅含`stage1-overall-performance(v1)`这一张图. 画面布局由`plot.py`及`display.json`决定; 后者声明`canvas`画幅、`viewport`绘图区域、`layouts`面板位置和`author`显示设置. 标准方法顺序、色彩和P/R画法来自正文Fig3的`artists.py`. 备注正文来自正式作者PPT, 不是从本目录再维护一份图注.

### stage1-overall-performance(v1).svg / .pdf / .png

三份文件对应同一Matplotlib画面. SVG保留文字及路径, PDF为矢量导出, PNG为600dpi栅格预览. 可编辑PPT由该SVG转换后装配, 而不是把PNG嵌入冒充可编辑图元.

## 装配与读取证据

### scenes.json

顶层是长度1的列表. 单页的`id/stem`均为`stage1-overall-performance(v1)`, `width/height`是Matplotlib画幅的点数, 1点=1/72英寸; `notes`在图元阶段为空字符串, 当前作者备注由`run.py`在装配后复制. `shapes`按SVG绘制顺序保存文字和几何, 供通用PPT装配工具读取, 不能据此重新定义科学候选或真实成员.

### manifest.json

顶层也是长度1的列表, 保存同一页的`id/stem/width/height/notes`, 不含`shapes`. 它描述当前派生画面, 不包含服务器实验身份.

### source_reads.json

顶层`reads`为列表, 每项含`remote`服务器绝对文件地址、`sha256`原始字节摘要和`bytes`原始字节数. 例如实际读取的`/storage/penghongen/AdaLigand_stage1_inference/small_molecule_only/test_0/provenance.json`为3328字节, SHA-256为`c10a04fa6dd25728a202a9808f40c4a04dc41f789ac70d2253f3ffeccae5b1dc`. 此记录用于核对原样读取, 不替代实验源文档.

### assembly.json / .alignment.json / .alignment.svg

`assembly.json`记录原生PPT装配的图名和图元计数; `alignment.json`记录面板边界及对齐检查, 对应SVG用于人工查看. 任一正式构建步骤失败, 命令以非零状态结束, 不把不完整目录称为完成结果. PNG生成不等于候选备注复制完成, 应以`run.py`成功退出为准.

## 稳定命令与代码职责

在项目根执行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/正文/Fig3-result-Find/run.py"
```

需要明确临时目录时添加`--build temp/自定的空目录`, 目录必须全新或全空. `figure.json`声明正式PPT地址、完整图名、入口和主要输出. `build.py`只请求本图需要的条件和指标; `plot.py`只负责本图面板. 科学共用实现唯一位于正文Fig3的`data.py`、`matching.py`、`instance_metrics.py`与`semantic.py`, 通用传输、SVG转换和PPT装配分别由`TOOLS/server_io`与`TOOLS/ppt`提供.

实际实验资产的生产命令、原release与元数据见[Find](../../../../追溯文档/source/Find.md)、[Emap2lig显式level](../../../../追溯文档/source/Emap2lig-level.md)、[Emap2lig无level](../../../../追溯文档/source/Emap2lig-nolevel.md)、[原始输入](../../../../追溯文档/source/原始输入.md)和[CryoAtom2受体](../../../../追溯文档/source/CryoAtom2受体.md). 代码所有权与本图选择见本目录trace, 本轮实际验收过程见[整理执行记录](../../../../talk/refactor/执行日志.md).
