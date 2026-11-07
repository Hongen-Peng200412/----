# BACKUP: 9LOV完整复合物

本目录只构造完整图名`backup-complex-9lov`这一页。正式图集是`画图/PPT/BACKUP.pptx`; 双语图注从该页作者备注完整复制。入口还从服务器坐标和化学模板生成本次CIF/SDF, 在独立ChimeraX进程中绘制`scientific-input/native-output/complex.png`与全内嵌`complex.cxs`。这些是本次科学重建产物; candidate使用当前采用的作者PNG和DrawingML布局, 不覆盖正式作者原件。

## 运行与核对

在项目根运行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/BACKUP/9LOV/run.py"
```

入口新建根temp中的本次目录。`--build temp/<新空目录>`可指定位置。成功输出为一页`candidate.pptx`、`scientific_receipt.json`、绝对服务器路径/完整SHA256的`source_reads.json`和本次显示收据。本次完整原生重建及诊断也全部在上述目录。正式PPT、古法CXS和作者图片不改写。

实际重开采用CXS时加`--render-sessions`。工具使用自己新建的独立ChimeraX进程, 不关闭作者已有窗口; 完整读取每个地图数组后保存本次PNG、模型/地图记录及源CXS前后SHA256。本图重开design.json所列当前采用会话。原会话只读, 新PNG只写本次`author-native/`。

## 阅读顺序与职责

1. 读[trace.md](trace.md), 对照本图服务器原件、原编号与科学口径。
2. 读`case.json`, 确认PDB、受体、固定实验条件和作者显示尺寸。它描述本图选择, 不切换服务器默认实验。
3. 读`run.py → build.py`。`正文/Fig7-visual-E2E-9BJJ/selection.py`唯一持有作者病例的原100%预算与Top1选择; 合格成员直接复用Fig6/cohorts.py。正文/Fig7-visual-E2E-9BJJ/ 的 `atoms.py → native.py`还负责CA2世界坐标与化学模板的原生输入转换及完整复合物重绘。
4. 读`design/design.json → drawing.xml`。`package/`只保留当前一页及必需Office关系、备注、主题和采用媒体; `drawing.xml`保存作者原生形状和图片裁切。

当前采用作者原件位于`画图/Chimera/BACKUP/9LOV/complex.cxs`与`complex.png`, 已在最小迁位时逐文件核对大小和完整SHA256。与服务器科学输入、作者采用显示、本次渲染各自的职责都在本图目录解释, 不另建stage调度层。

本轮实际验收: 本图独立入口成功, 全部采用CXS实际重开并完整读取地图, 会话前后SHA256一致; 候选单页与当前正式页的PowerPoint 2000像素宽整页导出为0像素差, 双语备注的全部元素、属性和文字相同。服务器坐标重新生成的完整复合物PNG与采用原PNG也逐像素相同。
