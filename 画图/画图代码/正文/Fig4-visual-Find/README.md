# Fig4: 9NVS的Find作者视图

本目录只构造完整图名`stage1-author-global-local-9nvs(v1)`这一页。正式图集是`画图/PPT/stage1可视化.pptx`; 双语图注从该页作者备注完整复制。candidate从本图design中的当前采用PNG与透明DrawingML直接构造; 不回退旧PPT或stage目录。科学数值同时从明确服务器原件复核, PNG不承担科学真值职责。

## 运行与核对

在项目根运行:

```powershell
D:/Anaconda/python.exe -X utf8 -B "画图/画图代码/正文/Fig4-visual-Find/run.py"
```

入口新建根temp中的本次目录。`--build temp/<新空目录>`可指定位置。成功输出为一页`candidate.pptx`、`scientific_receipt.json`、绝对服务器路径/完整SHA256的`source_reads.json`和本次显示收据。正式PPT、古法CXS和作者图片不改写。

实际重开采用CXS时加`--render-sessions`。工具使用自己新建的独立ChimeraX进程, 不关闭作者已有窗口; 完整读取每个地图数组后保存本次PNG、模型/地图记录及源CXS前后SHA256。本图依次重开8个采用视角。原会话只读, 新PNG只写本次`author-native/`。

## 阅读顺序与职责

1. 读[trace.md](trace.md), 对照本图服务器原件、原编号与科学口径。
2. 读`case.json`, 确认PDB、受体、固定实验条件和作者显示尺寸。它描述本图选择, 不切换服务器默认实验。
3. 读`run.py → build.py`。`science.py`只读取本图9NVS的两份逐PDB评价和两份交集NPZ, 用原source_blob_index与occurrence_id定位, 复核语义Dice/实例IoU。
4. 读`design/design.json → drawing.xml`。`package/`只保留当前一页及必需Office关系、备注、主题和采用媒体; `drawing.xml`保存作者原生形状和图片裁切。

原会话路径逐一列于design/design.json.native_sessions; 古法目录中的原文件保留原名、原位置和原内容。与服务器科学输入、作者采用显示、本次渲染各自的职责都在本图目录解释, 不另建stage调度层。

本轮实际验收: 本图独立入口成功, 全部采用CXS实际重开并完整读取地图, 会话前后SHA256一致; 候选单页与当前正式页的PowerPoint 2000像素宽整页导出为0像素差, 双语备注的全部元素、属性和文字相同。
