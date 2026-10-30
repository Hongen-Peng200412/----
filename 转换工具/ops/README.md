# 图表来源检查与完整重建

`figure_provenance.py`维护八份追溯文档到正式PPT来源批注的同步；`rebuild_figures.py`从冻结实验结果和原生素材生成新的图稿与可编辑候选。正式图形始终保留；完整重建默认屏蔽所有旧temp读取。

```text
转换工具/ops/
├─ figure_provenance.py       # 登记、导入关系、图名及双写检查；只修改专用批注
├─ rebuild_figures.py         # 稳定图名到准备、渲染、绘图及装配的完整顺序
└─ rebuild_support/
   ├─ source_dependencies.py # 静态读取Python/JS/CXC依赖，不执行科学模块
   ├─ sitecustomize.py       # 子进程文件审计：屏蔽旧temp，冻结输入只读
   ├─ node_guard.cjs         # Node的同类文件审计
   ├─ run_chimerax.ps1       # 隐藏的独立原生渲染进程；UTF-8 BOM供PowerShell 5读取
   └─ requirements.txt       # 固定依赖目录中的补充包版本
```

建议先读八份追溯记录中的“共享关系与本图选择”，再读`rebuild_figures.py::commands_for`及实际绘图函数，最后读来源同步器。共享实现可以服务多图；同名薄入口只选择图名，不意味着从临时目录读取源码。

## 产物与原始输入

```text
temp/figure_rebuild/<运行号>/
├─ summary.json                     # 本批各图运行结果
└─ <稳定图名>/
   ├─ render/、figures/、display/    # 本次绘图、原生渲染、身份卡片或统计派生文件
   ├─ *.svg、*.png、*.pdf           # 本次产生的图稿，实际位置依共享程序职责
   ├─ candidate*.pptx、published/   # 既有构造器产生的候选，可能包含同组辅助页
   ├─ rebuilt.pptx                  # 含指定图名、作者双语备注和完整来源的最终候选
   ├─ step-*.log                    # 每个实际命令的控制台输出
   ├─ python-reads.jsonl、node-reads.jsonl # 所读长期文件的路径；不保存新的实验真值
   └─ receipt.json                  # 图名、命令、退出码、图稿、候选及通过状态
```

每次运行使用新目录，拒绝复用非空单图目录。`receipt.json.passed=true`表示本次命令全部成功，指定`@@图名`存在，图稿真实生成，来源批注和作者备注已写入候选。它不表示重新运行了模型实验，也不表示作者手工排版与AI重建逐像素相同。科学数字、单位、分母、筛选和原排序沿所属追溯记录。

冻结输入来自四阶段output；图形专属选择和科学定义仍在原程序。三维图从冻结坐标、密度、SDF、相机和原生显示命令渲染，不以复制原实验PNG冒充重绘。方法图的手工原生基底作为作者素材保留，真实受体、密度和构象素材重新渲染后嵌入。PPT备注以正式作者稿为准，仅复制文字与原生公式，不回写正式图形。

## 运行环境与命令

本机使用`D:/Anaconda/python.exe`提供既有NumPy、Matplotlib、SciPy、scikit-image及Office COM；Node来自Codex固定运行时。三维显示使用`D:/ChimeraX 1.10.1/bin/ChimeraX.exe`和`D:/Pymol/python.exe`，可用`FIGURE_NODE`、`FIGURE_CHIMERAX`、`FIGURE_PYMOL_PYTHON`显式指定已安装程序。PyMOL、ChimeraX各自使用自己的Python环境，不混入其他版本的Pillow或lxml扩展。

RDKit和PyMuPDF位于仓库固定依赖目录`.manuscript_deps/figure_runtime`，版本由`rebuild_support/requirements.txt`记录，不进入Git、不从temp导入。需要重新安装补充包时使用相同Python：

```powershell
python -m pip install --no-deps --target .manuscript_deps/figure_runtime -r 转换工具/ops/rebuild_support/requirements.txt
python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure supp-e2e-completion-small
python -X utf8 -B 转换工具/ops/rebuild_figures.py --all
python -X utf8 -B 转换工具/ops/figure_provenance.py --sync
python -X utf8 -B 转换工具/ops/figure_provenance.py --check
```

图名可重复指定；`--build-root temp/<新目录>`可显式选择新批次根。构建目录通过环境参数传给全部前后步骤，SVG、manifest、scenes及候选必须属于同次运行。Python和Node对旧temp实际读取及冻结输入写入报错；原生渲染也加载相同Python审计并只执行本次生成、路径已重定向的脚本。它不会清空用户已有temp。

默认保留正式 PPT 中已有的作者图注，新增加的备选页沿用本次生成图注。本轮明确同时修订图注时，可加 `--generated-captions` 保留本次新图注，避免旧图注覆盖新版面板编号或结构实例；该选项只影响候选，不回写正式 PPT。

检查器只读验证登记、代码文件、Python符号、静态可识别的传递导入、共享关系和批注一致；无法穷举任意动态代码或自然语言实验断言。完整验收须实际执行重建命令。测试入口为`转换工具/test_figure_provenance.py`与`转换工具/test_figure_rebuild.py`，覆盖批注保全、并发保存、共享导入、旧temp读取和冻结写保护。

## 作者版本与示意图原件

`figure_provenance.py::base_figure` 只识别末尾 `(v数字)`。`load_records` 从当前 PPT 展开没有独立记录的作者版, 继承基础记录并标记 `author_origin`, 如 `foo-NO_LEVEL(v2)` 的来源仍为 `foo-NO_LEVEL`。已存在的作者版专用记录保留其补充说明。检查和同步按实际页区分来源批注, 合法复制页上的旧批注原位更名, 不新增第二份。源码阅读顺序为名称归一、文档读取与继承、科学来源检查、逐页批注同步。

请求作者版本重建时, 执行基础科学入口, `rebuilt.pptx` 中仍使用基础图名。`receipt.figure` 保存请求名, `scientific_figure` 保存基础名, `author_layout` 指向保留手工排版的正式 PPT。科学重建不回写作者排版。

当前六张颜色示意图的 `rebuild.mode="author_native"`, `author_source` 是作者对象原件的仓库相对路径, 例如 `画图/画图代码/e2e/output/overview-redesign-20261028/source/author-colors-20261030.pptx`。它也列入本条 `inputs`, 供独立读取和恢复。对应方法图原件位于 `e2e/output/method-ab-variants/source/author-colors-20261030.pptx`。两个文件保存作者当前整套可编辑页面、媒体与备注, 不仅是截图。重建器复制到当前构建目录, 原生渲染指定页, 保存 `author-render.json`（PPT路径及页码/PNG输出列表）和 `author_native_source` 回执字段, 然后同步当前图注与来源。旧素材生成入口继续由记录的 `entries` 保存；不为示意图重跑模型或编造指标。

同步只归并 `Figure Editor` 占位作者至 `Hongen Peng`（HP）, 复用已有作者ID；若只存在占位身份则原位更名。其他作者身份和批注正文保持不变。

本轮 `author-render.json` 的实际结构如下。`path` 是当前可清空构建目录内的 PPT 绝对路径, `slides` 是待导出的页列表, `page` 为从1开始的实际页码, `output` 为 PNG 绝对路径：

```json
[{"path":"C:/Users/15919/Desktop/论文草稿/temp/stage1_layout_provenance_20261030/author_schematics/fig-overview-color1/candidate.pptx","slides":[{"page":11,"output":"C:/Users/15919/Desktop/论文草稿/temp/stage1_layout_provenance_20261030/author_schematics/fig-overview-color1/fig-overview-color1.png"}]}]
```

版本请求的 `author_layout` 字段构造示例为 `{"pptx":"画图/stage1结果.pptx","figure":"stage1-overall-performance(v1)","preserved_in_formal_ppt":true}`。`pptx` 是正式作者图集的仓库相对路径, `figure` 是作者版实际名称, 布尔值表示重建器没有回写该正式页面；不表示已经逐像素重建作者排版。
