# 方法图 a、b 的独立配色候选

本目录维护方法图 a、b 的原生位置与配色。当前版本保留作者删页后的5页, 以作者最新第3页为位置基准, 第4页灰化框线, 第5页同时使用灰框和更浅的灰色填充。Match 的12个功能模块框已纳入, 蓝/绿大背景、分子图、特征条、立体块及选中身份颜色保留。Build 不参与修改。

## 当前五页版

```text
e2e/visualization/method-ab-variants/
├─ sync_selected.mjs          # 复制第3页原生对象树, 只改第4/5页框色
├─ audit_selected.py          # 检查全部位置、尺寸、内容、媒体与授权框色
├─ render_native.ps1          # 支持显式作者源, 只读导出5页原件与5页候选
└─ finalize.mjs selected      # 五页包、原画布、字体与一方导入验收
e2e/output/method-ab-variants/
├─ source/
│  ├─ selected-layout.json    # 当前选择的作者文件、散列及页码
│  └─ author-20261028-eca767b6.pptx # 作者最新手调布局, 长期冻结输入
├─ history/selected-out-20261028.pptx # 删除版本的历史来源管理副本
└─ regenerated/20261028-selected-sync/
   ├─ Method总图.pptx         # 最终五页文件留档
   ├─ page-3.png … page-5.png # 位置基准和两个框色档的原生预览
   ├─ selected_operations.json # 全部容器与颜色修改白名单
   ├─ audit.json              # 与第3页严格比较及原页像素核对
   ├─ receipt.json            # 四步骤完整重建回执
   ├─ publication-pixels.json # 最终5页与候选逐像素比较
   └─ final_manifest.json     # 最终散列、页数、来源与改色数量
```

从仓库根运行 `python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure fig-method-ab-a4 --generated-captions`。当前 A1/A4/A5分别对应第3/4/5页, 共用这条完整五页链。`selected-layout.json.pptx` 如 `画图/画图代码/e2e/output/method-ab-variants/source/author-20261028-eca767b6.pptx`, 与 `sha256` 共同固定作者输入; `baseline_page=3`, `target_pages=[4,5]`。

`selected_operations.json.container_ids` 含21个页内原生对象 ID, 如644为 Mean/max pool; `divider_ids` 含3条分隔线。`pages` 以页码字符串为键, 如 `"4"`, 每页的 `colour_edits` 保存 `id`、`name`、`scope`、`before`、`after`, 如 `scope="border"`、`after="BEC7CE"`。第5页填充为 `F4F6F7`, 与边框明确不同。原有函数模块只更改框线和背景, 文字及实际特征内容不变。

`audit.json.passed` 为总体结果, `failures=[]` 表示无错误; 每页的 `exact_page3_geometry_and_content=true` 表示除授权框色外整个对象树与作者第3页严格一致。`final_manifest.json.provenance` 按稳定图名记录与追溯文档的逐字同步结果。当前完整规格见 [五页版方案](../../../../../talk/method_ab_20261028/方案_五页同步.md)。

以下为初轮六版的历史契约, 其中11页页码不再表示当前正式文件。

## 初轮六版的输入、输出与目录

```text
e2e/visualization/method-ab-variants/
├─ build_variants.mjs       # 原生 ZIP/XML 对象补丁, 生成全部六页
├─ render_native.ps1        # PowerPoint 只读导出作者原页和候选页
├─ audit.py                 # 对象白名单、间距、媒体及渲染差异核对
├─ finalize.mjs             # PPT 包、字体、画布及一方导入验收
└─ README.md                # 当前输入、产物与复现契约
e2e/output/method-ab-variants/
├─ source/author-20261028-deb03f10.pptx  # 本轮作者冻结基底, 原第4页仍保留手误
└─ regenerated/20261028-A0-A5/
   ├─ Method总图.pptx        # 本轮原生保存后的11页图集留档
   ├─ A0.png … A5.png        # 六页最终原生预览
   ├─ final_manifest.json    # 最终文件散列、页码与代码版本
   ├─ operations.json        # 具名对象的几何与配色操作
   ├─ variant_manifest.json  # 六个候选的图名和页码
   ├─ audit.json             # 构建对象和媒体保全核对
   ├─ receipt.json           # 独立完整重建回执
   ├─ publication-check.json # 实际保存后的逐像素和来源核对
   ├─ task-provenance-check.json # 本轮六条来源结果与全库外部问题
   └─ checks/                # 构建文件及实际保存文件的工具验收
```

构建目录由 `FIGURE_BUILD_ROOT` 指定, 完整重建入口自动创建全新 `temp/figure_rebuild/` 子目录。既有 temp 不参与读取。

```text
本次构建目录/
├─ candidate.pptx           # 11页候选: 原有5页及A0–A5, 第4页恢复
├─ variant_manifest.json    # 6个版本与页码、图名的对应
├─ operations.json          # 源散列、配色白名单、平移及颜色操作
├─ native-render.json       # 16张原生导出图的页码、路径及对象数
├─ render/                  # 原5页与新11页的PowerPoint PNG
├─ audit.json               # 对象保全、颜色和间距核对
├─ published/Method总图.pptx # 完成PPT包验收的待发布副本
├─ checks/                  # 一方工具的私有验收报告
└─ receipt.json             # 完整重建的命令与通过状态
```

### 候选及页码

`variant_manifest.json` 是6项数组, 每项对应一张新增页。`code` 如 `"A1"`, `page` 为从1开始的页码, 如 `7`; `figure` 如 `"fig-method-ab-a1"`。`arrow`、`border`、`fill` 三个布尔值分别表示是否收敛普通箭头、容器边框和容器填充, 如 A1 为 `true,false,false`。`objects` 为包含组在内的原生对象数量; `source_slide=3` 固定连接同一作者基底。

### 修改记录

`operations.json` 的 `shifts_mm` 保存 `find`、`candidate`、`identity` 三组水平平移, 单位 mm, 负数向左。`movements` 的普通记录以页内原生 `id` 连接对象, 如 `id=644` 为 Mean/max pool; `dx_mm` 表示其所属组的平移。`kind="bridge_stretch"` 对应 `id=1395`, 只让既有折线的起点随 candidate、终点随 identity 平移。

`colour_changes` 以 `A0` 至 `A5` 为键; A0 对应空数组。每项保存对象 `id`、`name`、修改属性 `scope` 和六位 RGB `before`、`after`, 如箭头填充由 `"4083B4"` 改为 `"77828C"`。`original_ab` 与 `positioned_ab` 使用相同页内 ID, `box_mm=[left,top,width,height]` 保存考虑嵌套组变换后的整页位置。受保护的功能模块及特征颜色不得出现在操作白名单中。

### 核对与原生预览

`audit.json.passed` 表示本轮局部审计是否通过; `failures` 为具体错误列表, 无错误时为空数组。`checks.balanced_gutters_mm` 记录 Find 两侧卡片间距及两个 encoder 相对各自区域的内容间距。`checks.unchanged_native_render` 按页码记录第1、2、3、5页原生导出是否逐像素一致, 如 `"5":true`。核对不重新预测构象或计算实验指标。

留档中的 `final_manifest.json` 用 `variant_pages` 连接版本与实际保存页码, 如 `"A0":6`; `published_sha256` 固定本轮保存的正式文件内容, `source_code_sha256` 固定构建时的代码版本。`publication-check.json.native_pixels` 比较原生插页保存后的11页与验收候选, 如 `"11":true`; `provenance` 按独立图名记录批注与文档是否逐字一致。`task-provenance-check.json.task_errors` 只记录本轮方法图的错误, `unrelated_global_errors` 单独保留全库中其他工作的未闭合问题。上述回执中的 temp 路径是运行历史, 不是重建输入; 唯一作者基底已冻结在 source/。

## 运行与共享关系

在仓库根运行:

```powershell
python -X utf8 -B 转换工具/ops/rebuild_figures.py --figure fig-method-ab-a0 --generated-captions
```

初轮 A0/A2/A3 仍可从旧冻结基底重建历史六版比较; 当前 A1/A4/A5已改用上文的五页同步链。历史装配不恢复作者删除的正式页面。源节点和媒体来自 `fig-method-v9` 的作者保存版本, 不更换病例、不共享新统计。

运行环境沿用项目 Node 运行时的 `jszip`、`xml-js` 和 `@oai/artifact-tool`, 项目 Python 的 lxml、Pillow 及本机 PowerPoint。渲染只打开只读副本; 正式图集的发布单独核对作者新修改后进行。范围与执行证据见 [本轮方案](../../../../../talk/method_ab_20261028/方案.md) 和 [执行记录](../../../../../talk/method_ab_20261028/执行记录.md)。
