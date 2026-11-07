# 补充 Fig4: E2E计费规则图

本目录只构造`e2e-accounting-rules-draft`这一页流程图, 正式作者页为[E2E评价计费规则.pptx](../../../PPT/E2E评价计费规则.pptx). 它表达候选计费和成功定义, 不含实验成功率, 不读取服务器候选、交集、身份预测或姿态结果. 图中的`+1`是一次尝试的计费定义, 科学含义见[trace.md](trace.md).

## 文件与构建输出

本目录`display.json`保存作者当前采用的73个原生XML图层和主题:

| 字段 | 格式与含义 |
| --- | --- |
| `description` | str, 当前图层职责的文字描述 |
| `canvas` | 长2的int列表`[9144000,6223000]`, 画布宽高EMU, 1pt=12700EMU |
| `nodes` | 长73的str列表, 每项是一个原生PowerPoint形状XML, 按图层叠放顺序运输; 包括流程节点、箭头、静态规则文字与位置, 不保存实验曲线 |
| `theme` | str, 完整PPT主题XML, 保留原作者字体和色彩 |

`figure.json`声明图名、正式PPT、入口和`candidate.pptx`主要输出. `build.py`将这些明确图层交给TOOLS/ppt/svg_native的中性XML装配, 不在TOOLS内定义任何计费动作. 无参数时, `run.py`新建`temp/figure-build/Fig4-rules-E2E-counting/<UTC时间>/`; 时间含年月日、时分秒与微秒, 所有输出可整体清空.

```text
<本次构建目录>/
├─ candidate.pptx  # 仅本图一页, 原生可编辑规则节点与箭头
└─ source-comment-before/  # 本次TRACE来源批注更新的临时比对副本
```

候选保留9144000×6223000 EMU原画布. 当前正式作者PPT的双语备注按完整图名原样复制, 来源短批注指向本目录README和trace. 不覆盖正式作者PPT, 不生成master、Top-k、server_reads或科学原件缓存.

## 稳定命令

在项目根执行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/补充材料/Fig4-rules-E2E-counting/run.py"
```

需要固定临时位置时追加`--build temp/自定空目录`. 具体规则的可执行定义唯一位于正文Fig6的accounting.py, 这里的静态文字只表达同一科学定义, 不建立另一份计费代码. 逐次验收见[整理执行记录](../../../../talk/refactor/执行日志.md).
