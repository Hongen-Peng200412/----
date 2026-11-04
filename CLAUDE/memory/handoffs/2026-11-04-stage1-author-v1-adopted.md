# Stage1第17页作者v1已采用

日期：2026-11-04。

## 当前状态

正文采用画图/stage1可视化.pptx第17页作者手工调整版，稳定图名为`stage1-author-global-local-9nvs(v1)`。原生成版现在第16页，原始八份ChimeraX素材保持。中英文稿图名、面板引用、PPT双语图注和来源批注已同步；未编译Word。

## 已完成与科学边界

整体a/b/c依次为Emap2lig-Find、LigandSeek-Find（CA2）、参考；下方五幅局部无字母，左起为误报窗口、Emap匹配位点、CA2匹配位点、真实区域、透明真实区域及沉积配体。正文全局比较引用a,b，局部比较引用整图。图注不再使用旧a–h或i／ii。

作者指出最左窗口两块都是FP。已由原候选体素投影确定为blob1（下方较大，350体素）与blob3（上方较小，32体素）；冻结screening/selected_blobs.csv原记录确认两者均未匹配，且与所有真实配体区域零交集。因此新图注直接写两块均为假阳性，不加框。不是仅上方一块，也未重新评价。

八张嵌入媒体与已验收原生PNG逐字节相同；Dice0.160／0.757、IoU0.306／0.656保持。最终PPT仅改变两个来源批注部件和第17页备注（包内notesSlide16.xml）；图片、图形、布局、页数及其他部件原样保持。两稿除对应图引用外不变，其他PPT、Word与暂存区散列保持。

作者排版原件、8媒体映射、双语图注、预览及qa冻结在画图/画图代码/stage1/output/stage1-author-global-local-9nvs/author_v1/；初始材料与八份最终CXS沿基础版source/与native/。source/author-edited.pptx保存采用时作者原件，图注最终文本另见author_v1/caption.json；正式PPT继续作为作者维护源。

## 重建与检查

完整隔离科学重建通过，八幅重新渲染PNG与原采用图逐像素一致；作者三列排版保留于正式PPT，不用基础版重建布局覆盖。首次重建的第5份会话嵌图保存遇到MemoryError；build.py仅增加原生关闭旧会话后的gc.collect，解除累积占用，参数和图像保持。该修复经主代理自查及独立窄查批准，新的完整重建实际通过。

独立图文核查与作者FP更正窄查通过。全局追溯check通过115条记录／101图。首次写回因PPT占用失败，作者保存关闭后重新确认文件与基线完全一致，再用同一命令成功写回；未关闭或操作作者窗口。失败与成功沿用同一实验日志。

## 后续与文件入口

任务完成。继续调图时保留作者版与两块FP事实；不使用旧a–h图注覆盖本页。

- 画图/stage1可视化.pptx：第17页v1。
- draft.md及论文草稿.md：对应9NVS段落。
- 画图/古法Chimera/stage1/论文图说明.md：当前位置与最终会话导航。
- 画图/画图代码/stage1/visualization/图表追溯.md：基础版历史与v1当前记录。
- 画图/画图代码/stage1/output/stage1-author-global-local-9nvs/author_v1/qa/：采用、FP投影、重建及范围保全证据。
- talk/author_visualization_20261103/执行记录.md、RULES/执行记录.md：正式写入／重建门控分别记录。
