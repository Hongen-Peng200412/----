# 按 Figure 整理的迁移清单

本文件规定本轮代码、文档和资产的目标位置。以作者最新边界为准；不新增长期备份，不保留旧总览生成逻辑，不把科学规则放进 TOOLS。运行历史另见 `执行日志.md`。

## 图表单元

绘图代码根仅含正文、补充材料、BACKUP。一个目录就是一个重建单元；只有补 Fig6–8 和 Fig9–10 是作者许可的多图单元。

| 目标目录 | 稳定图名 | 唯一提交标题 |
| --- | --- | --- |
| `正文/Fig1-overview` | `fig-overview-topology` | `recon: overview(Fig1)` |
| `正文/Fig2-method` | `fig-method-color3` | `recon: method(Fig2)` |
| `正文/Fig3-result-Find` | `stage1-overall-performance(v1)` | `recon: result-Find(Fig3)` |
| `正文/Fig4-visual-Find` | `stage1-author-global-local-9nvs(v1)` | `recon: visual-Find(Fig4)` |
| `正文/Fig5-result-Match&Build` | `stage2-stage3-results(v1)` | `recon: result-Match&Build(Fig5)` |
| `正文/Fig6-result-E2E` | `e2e-main-top5(v1)` | `recon: result-E2E(Fig6)` |
| `正文/Fig7-visual-E2E-9BJJ` | `full-pipeline-small-molecule-author-9bjj` | `recon: visual-E2E(Fig7; 9BJJ)` |
| `正文/Fig8-visual-E2E-9UJF` | `full-pipeline-small-molecule-author-9ujf-v2` | `recon: visual-E2E(Fig8; 9UJF)` |
| `正文/Fig9-result-Ablation` | `stage2-stage3-ablation-centre(v1)` | `recon: result-Ablation(Fig9)` |
| `补充材料/Fig1-Find-0.5INS` | `stage1-additional-analysis` | `recon: suppl-Find(Fig1; 0.5INS)` |
| `补充材料/Fig2-Find-Emap2lig_no_level` | `stage1-no-level-comparison-NO_LEVEL` | `recon: suppl-Find(Fig2; Emap2lig_no_level)` |
| `补充材料/Table1-Find-Ablation` | Table1: CSV/Markdown | `recon: suppl-Find(Table1; Ablation)` |
| `补充材料/Fig3-Build-Ablation` | `stage3-ablation-envelope` | `recon: suppl-Build(Fig3; Ablation)` |
| `补充材料/Fig4-rules-E2E-counting` | `e2e-accounting-rules-draft` | `recon: suppl-rules(Fig4; E2E counting)` |
| `补充材料/Fig5-E2E-topk` | `e2e-topk-success` | `recon: suppl-E2E-topk(Fig5)` |
| `补充材料/Fig6~8-E2E-Find-Build` | `supp-find-correct-match-build-emap2lig`、`supp-find-correct-match-build-ca2`、`supp-find-correct-match-build-gt` | `recon: suppl-E2E-Find Build(Fig6~8; completion ratio)` |
| `补充材料/Fig9~10-E2E-Find-Match-Build` | `supp-find-match-build-ca2`、`supp-find-match-build-gt` | `recon: suppl-E2E-Find Match Build(Fig9~10; completion ratio)` |
| `BACKUP/11JB` | `backup-complex-11jb` | `recon: BACKUP(11JB)` |
| `BACKUP/30GA` | `backup-complex-30ga` | `recon: BACKUP(30GA)` |
| `BACKUP/9LOV` | `backup-complex-9lov` | `recon: BACKUP(9LOV)` |

## 共用代码的归属

固定依赖 `.manuscript_deps/` 整体迁至 `TOOLS/runtime/.manuscript_deps/`, 只调整位置, 不升级、重装或替换包内容. 部署在项目外的软件安装不迁移. 依赖仍退出精选 Git, 由全面 Git 收录；外部链接不跟随。

- 网络与原字节读取归 TOOLS/server_io；不选择实验根、成员或评价规则。
- Office、SVG 与中性几何装配归 TOOLS/ppt；科学字段、阈值、预算和显示选择归 Figure。
- Find 科学规则由正文 Fig3 唯一拥有；关联补图与表显式复用。
- Match/Build 共用科学规则由正文 Fig5 唯一拥有；正文 Fig9 与补 Fig3 引用所需规则。
- E2E 计费、匹配和预算统计由正文 Fig6 唯一拥有；相关补图显式复用，单图不计算整个 stage。
- Workbench 中性 UI 与保存机制归 TOOLS/chimerax，科学选择归 Fig7，Fig8 显式引用。

## 当前逐文件清单

表中列明调用职责和本轮验证方式。分拆结果已落实到表列Figure目录，各目录的README与trace列明实际入口和共享所有者；CXS已从采用图片反向核定，古法范围外五个仍由作者手动处理。必要显示媒体与 CXS 单独按采用图片来源核定。

| 现有文件 | 当前职责与调用 | 生命周期 | 目标与动作 | 验证方式 | 理由 |
| --- | --- | --- | --- | --- | --- |
| `manuscript_conversion.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `md_to_word.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `md_to_word_operation.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `nature_article.csl` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/history-map.tsv` | 旧历史重排与映射；同步入口 | 一次任务元数据 | 本次 temp 内历史重建工具；仅当前规范后的对应关系留文档；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/README.md` | 全面 Git 同步或相关运维；同步入口 | 正式代码或显示契约 | TOOLS/sync-to-server/README.md；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/rewrite_selected_history.py` | 旧历史重排与映射；同步入口 | 一次任务元数据 | 本次 temp 内历史重建工具；仅当前规范后的对应关系留文档；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/run_sync.bat` | 全面 Git 同步或相关运维；同步入口 | 正式代码或显示契约 | TOOLS/sync-to-server/run_sync.bat；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/server.py` | 全面 Git 同步或相关运维；同步入口 | 正式代码或显示契约 | TOOLS/sync-to-server/server.py；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/sync.py` | 全面 Git 同步或相关运维；同步入口 | 正式代码或显示契约 | TOOLS/sync-to-server/sync.py；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `sync-to-server/test_sync.py` | 全面 Git 同步或相关运维；同步入口 | 正式代码或显示契约 | TOOLS/sync-to-server/test_sync.py；提纯、分拆或退场 | 同步隔离测试和真实恢复校验 | 按单图科学职责和中性工具边界组织 |
| `word_to_md.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/design.json` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/drawing.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/layout-index.json` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/[Content_Types].xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/_rels/.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/docProps/app.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/docProps/core.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/_rels/presentation.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/authors.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/comments/modernComment_100_63A79E61.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/notesMasters/_rels/notesMaster1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/notesMasters/notesMaster1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/notesSlides/_rels/notesSlide1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/notesSlides/notesSlide1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/presentation.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/presProps.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout10.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout11.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout2.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout3.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout4.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout5.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout6.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout7.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout8.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/_rels/slideLayout9.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout10.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout11.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout3.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout4.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout5.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout6.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout7.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout8.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideLayouts/slideLayout9.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideMasters/_rels/slideMaster1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slideMasters/slideMaster1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slides/_rels/slide1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/slides/slide1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/tableStyles.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/theme/theme1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/theme/theme2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9bjj/package/ppt/viewProps.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/design.json` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/drawing.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/layout-index.json` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/[Content_Types].xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/_rels/.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/docProps/app.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/docProps/core.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/_rels/presentation.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/authors.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/comments/modernComment_101_3922E268.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/notesMasters/_rels/notesMaster1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/notesMasters/notesMaster1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/notesSlides/_rels/notesSlide2.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/notesSlides/notesSlide2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/presentation.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/presProps.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout10.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout11.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout2.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout3.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout4.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout5.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout6.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout7.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout8.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/_rels/slideLayout9.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout10.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout11.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout3.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout4.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout5.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout6.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout7.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout8.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideLayouts/slideLayout9.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideMasters/_rels/slideMaster1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slideMasters/slideMaster1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slides/_rels/slide2.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/slides/slide2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/tableStyles.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/theme/theme1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/theme/theme2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/full-pipeline-small-molecule-author-9ujf-v2/package/ppt/viewProps.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/design.json` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/drawing.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/layout-index.json` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/[Content_Types].xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/_rels/.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/docProps/app.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/docProps/core.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/_rels/presentation.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/authors.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/comments/modernComment_111_15A59CE2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/notesMasters/_rels/notesMaster1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/notesMasters/notesMaster1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/notesSlides/_rels/notesSlide7.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/notesSlides/notesSlide7.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/presentation.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/presProps.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slideLayouts/_rels/slideLayout1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slideLayouts/_rels/slideLayout2.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slideLayouts/slideLayout1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slideLayouts/slideLayout2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slideMasters/_rels/slideMaster1.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slideMasters/slideMaster1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slides/_rels/slide7.xml.rels` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/slides/slide7.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/tableStyles.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/theme/theme1.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/theme/theme2.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/作者显示原件/stage1-author-global-local-9nvs(v1)/package/ppt/viewProps.xml` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/备用完整复合物/11jb/caption.json` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/备用完整复合物/30ga/caption.json` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/备用完整复合物/9lov/caption.json` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/B1.sdf` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/B2.sdf` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/B4.sdf` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/B5.sdf` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/native-manifest.json` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/receptor.pdb` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/assets/scene.json` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/delivery.json` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/README.md` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/总览图_ChimeraX/同步导出.py` | 旧总览人工示意编辑；旧同步导出入口 | 拟退出，保留资产另列 | 非采用旧生成逻辑退出；会话和图片由实际来源核定；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/author_display_pptx.py` | 中性 Office 容器装配；作者图与示意图构造 | 正式代码或显示契约 | TOOLS/ppt/author_display.py；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/author_display.json` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/display.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/prepare_data.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/README.md` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/rebuild.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/render.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/rules_display.json` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/rules_plot.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/server_data.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/__init__.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/accounting.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/completion_artists.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/completion_statistics.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/main_artists.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/native_shapes.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/supplement_actual.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/support/supplement_correct.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/e2e-current/topk_plot.py` | 端到端规则、统计或显示；原 E2E 八图入口 | 正式代码或显示契约 | 正文/Fig6-result-E2E 及对应补充图；中性 SVG/Office 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/experiment_claims/README.md` | 独立数字核验；旧 claim CLI | 本轮只用临时核验，不进入新主线 | 退出代码树；文字移至追溯文档/claim/；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/experiment_claims/server_claims.py` | 独立数字核验；旧 claim CLI | 本轮只用临时核验，不进入新主线 | 退出代码树；文字移至追溯文档/claim/；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/experiment_claims/sources.json` | 独立数字核验；旧 claim CLI | 本轮只用临时核验，不进入新主线 | 退出代码树；文字移至追溯文档/claim/；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/assemble.mjs` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/author_layout.json` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/axis_geometry.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/build.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/case_9wup.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/case_deck.mjs` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/case_geometry.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/case_native.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/match_build_data.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/plot_primitives.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/README.md` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/calculate/stage2-stage3-current/svg_scene.py` | Match/Build 科学与 9WUP 显示；原 Match/Build 三图入口 | 正式代码或显示契约 | 正文/Fig5-result-Match&Build、正文/Fig9-result-Ablation、补充材料/Fig3-Build-Ablation；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/backup-complex-cases/assemble.py` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/backup-complex-cases/build.py` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/backup-complex-cases/display.json` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/backup-complex-cases/README.md` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/backup-complex-cases/render_native.py` | 完整复合物选留图；BACKUP 构造 | 正式代码或显示契约 | BACKUP/11JB、30GA、9LOV；会话图片归画图/Chimera/BACKUP；提纯、分拆或退场 | 三病例真实重建和原生重开 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-author-figures/build.py` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-author-figures/README.md` | 作者已采用显示定义；当前作者图构造 | 正式代码或显示契约 | 正文 Fig4、Fig7、Fig8 各自设计与读取；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/build.py` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/design.json` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/drawing.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/[Content_Types].xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/_rels/.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/docProps/app.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/docProps/core.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/_rels/presentation.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/authors.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/comments/modernComment_10B_DE9E33F8.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/notesMasters/_rels/notesMaster1.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/notesMasters/notesMaster1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/notesSlides/_rels/notesSlide10.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/notesSlides/notesSlide10.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/presentation.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/presProps.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/slideLayouts/_rels/slideLayout1.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/slideLayouts/slideLayout1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/slideMasters/_rels/slideMaster1.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/slideMasters/slideMaster1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/slides/_rels/slide10.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/slides/slide10.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/tableStyles.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/theme/theme1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/theme/theme2.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-method-color3/package/ppt/viewProps.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/design.json` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/drawing.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/[Content_Types].xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/_rels/.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/docProps/app.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/docProps/core.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/_rels/presentation.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/authors.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/comments/modernComment_11D_85773CCB.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/notesMasters/_rels/notesMaster1.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/notesMasters/notesMaster1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/notesSlides/_rels/notesSlide13.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/notesSlides/notesSlide13.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/presentation.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/presProps.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slideLayouts/_rels/slideLayout1.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slideLayouts/_rels/slideLayout2.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slideLayouts/slideLayout1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slideLayouts/slideLayout2.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slideMasters/_rels/slideMaster1.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slideMasters/slideMaster1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slides/_rels/slide13.xml.rels` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/slides/slide13.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/tableStyles.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/theme/theme1.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/theme/theme2.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/fig-overview-topology/package/ppt/viewProps.xml` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/current-schematics/README.md` | 当前采用示意图设计；当前示意图构造 | 正式代码或显示契约 | 正文/Fig1-overview 或正文/Fig2-method；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/multiligand-workbench/chimerax_bundle/README.md` | 作者会话面板和科学显示选择；ChimeraX 自定义面板 | 正式代码或显示契约 | 中性界面归 TOOLS/chimerax；科学选择归正文 Fig7，Fig8 显式引用；提纯、分拆或退场 | 原会话实际重开与状态比较 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/multiligand-workbench/chimerax_bundle/setup.py` | 作者会话面板和科学显示选择；ChimeraX 自定义面板 | 正式代码或显示契约 | 中性界面归 TOOLS/chimerax；科学选择归正文 Fig7，Fig8 显式引用；提纯、分拆或退场 | 原会话实际重开与状态比较 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/multiligand-workbench/chimerax_bundle/src/__init__.py` | 作者会话面板和科学显示选择；ChimeraX 自定义面板 | 正式代码或显示契约 | 中性界面归 TOOLS/chimerax；科学选择归正文 Fig7，Fig8 显式引用；提纯、分拆或退场 | 原会话实际重开与状态比较 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/multiligand-workbench/chimerax_bundle/src/docs/user/commands/ligwork.html` | 作者会话面板和科学显示选择；ChimeraX 自定义面板 | 正式代码或显示契约 | 中性界面归 TOOLS/chimerax；科学选择归正文 Fig7，Fig8 显式引用；提纯、分拆或退场 | 原会话实际重开与状态比较 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/multiligand-workbench/chimerax_bundle/src/selection.py` | 作者会话面板和科学显示选择；ChimeraX 自定义面板 | 正式代码或显示契约 | 中性界面归 TOOLS/chimerax；科学选择归正文 Fig7，Fig8 显式引用；提纯、分拆或退场 | 原会话实际重开与状态比较 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/e2e/visualization/multiligand-workbench/chimerax_bundle/src/tool.py` | 作者会话面板和科学显示选择；ChimeraX 自定义面板 | 正式代码或显示契约 | 中性界面归 TOOLS/chimerax；科学选择归正文 Fig7，Fig8 显式引用；提纯、分拆或退场 | 原会话实际重开与状态比较 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/figure_commands.py` | 旧总登记；旧统一入口 | 正式代码或显示契约 | TOOLS/figure_runner 与每图 figure.json；原 stage 组退出；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/figure_support/__init__.py` | 共享几何检查或区域匹配；各绘图入口 | 正式代码或显示契约 | TOOLS/ppt 或正文 Fig6 科学规则，按实际职责分拆；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/figure_support/audit_panel_alignment.py` | 共享几何检查或区域匹配；各绘图入口 | 正式代码或显示契约 | TOOLS/ppt 或正文 Fig6 科学规则，按实际职责分拆；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/figure_support/region_matching.py` | 共享几何检查或区域匹配；各绘图入口 | 正式代码或显示契约 | TOOLS/ppt 或正文 Fig6 科学规则，按实际职责分拆；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/server_sources.py` | 中性只读传输与格式解析；各科学 reader | 正式代码或显示契约 | TOOLS/server_io/source.py；提纯、分拆或退场 | 真实原件读取与原样缓存 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/author_layout.json` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/build_deck.mjs` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/captions.json` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/plot.py` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/README.md` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/rebuild.py` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/current_figures/svg_scene.py` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/find_science.py` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `画图/画图代码/stage1/calculate/server_find_inputs.py` | Find 原件、科学规则或显示；原 Find 三图入口 | 正式代码或显示契约 | 正文/Fig3-result-Find、补充材料/Fig1、Fig2、Table1；中性 SVG 支撑归 TOOLS/ppt；提纯、分拆或退场 | 本轮对应图重建与显示核对 | 按单图科学职责和中性工具边界组织 |
| `转换工具/export_slide.ps1` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/current_figure_trace.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/current_rebuild.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/figure_provenance.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/README.md` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/rebuild_figures.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/rebuild_support/node_guard.cjs` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/rebuild_support/requirements.txt` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/rebuild_support/run_chimerax.ps1` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/rebuild_support/sitecustomize.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ops/rebuild_support/source_dependencies.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/ppt_figures.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/README.md` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/snapshot_open_word.ps1` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_cross_file_figrefs.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_english_captions.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_figure_provenance.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_figure_rebuild.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_front_matter.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_picture_pixels.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_roundtrip.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/test_table_layout.py` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/执行记录.md` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |
| `转换工具/映射索引.md` | 文稿转换、图集解析或入口编排；文稿转换和绘图入口 | 正式代码或显示契约 | TOOLS/word/ 或 TOOLS/figure_runner/、TOOLS/ppt/；提纯、分拆或退场 | 原有转换测试与隐藏来源迁移专项 | 按单图科学职责和中性工具边界组织 |

## 正式图集迁移

以下文件只改位置, 不拆页或改名. 迁移前后完整文件摘要必须一致；随后仅按页更新获准的来源批注。

| 原文件 | 正式位置 |
| --- | --- |
| `画图/BACKUP.pptx` | `画图/PPT/BACKUP.pptx` |
| `画图/E2E结果.pptx` | `画图/PPT/E2E结果.pptx` |
| `画图/E2E评价计费规则.pptx` | `画图/PPT/E2E评价计费规则.pptx` |
| `画图/Method总图.pptx` | `画图/PPT/Method总图.pptx` |
| `画图/stage1可视化.pptx` | `画图/PPT/stage1可视化.pptx` |
| `画图/stage1结果.pptx` | `画图/PPT/stage1结果.pptx` |
| `画图/stage2-stage3结果.pptx` | `画图/PPT/stage2-stage3结果.pptx` |
| `画图/全流程小分子案例_作者9BJJ.pptx` | `画图/PPT/全流程小分子案例_作者9BJJ.pptx` |
| `画图/全流程小分子案例_作者9UJF.pptx` | `画图/PPT/全流程小分子案例_作者9UJF.pptx` |
| `画图/总览图.pptx` | `画图/PPT/总览图.pptx` |
