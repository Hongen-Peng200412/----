# Stage1作者第15页草案已重绘并入稿

日期：2026-11-03。

## 当前状态

按作者授权采用画图/stage1可视化.pptx第15页草案的三幅整体和五幅局部视图。正式八面板图追加为第17页，稳定图名为`stage1-author-global-local-9nvs`；第15页草案、原16页及手工墨迹保留。draft.md和论文草稿.md均已引用新图，本轮未编译Word。

## 已完成

八份作者CXS、初始材料与草案PPT冻结于画图/画图代码/stage1/output/stage1-author-global-local-9nvs/source/。原Emap共同实例PNG为6000×4108，普通参考局部为6000×4486，多数其余为6000×4337；八份CXS均已是1126×814窗口。原生重开每份会话，保持相机、外观及材料，以3378×2442统一导出，五幅局部全幅等比放置。三幅全景仅统一裁外围空白，全部前景保留。最终八份CXS、PNG及原生命令在同图native/；作者目录论文图说明.md逐幅连接。

a/b/c为Emap整体／共同实例／误报窗口，d/e为CA2整体／共同实例，f/g/h为参考整体／真实区域局部／透明区域与沉积配体。全景共用相机和尺度；b/e/g/h共用相机和尺度；全部保持相同观察方向。定位框i/ii是完整局部画幅在全景的投影。c另细框标记原评价的Emap blob3，窗口内另一预测不冒充该误报。

PPT保存中英文图注与新页完整来源批注。两稿仅替换该图名及全局a,c,d、局部b,e的引用；逆替换后其他内容逐字节一致。旧PPT313个非容器部件保持，四个容器仅追加页；其他PPT、全部Word与八份作者CXS散列保持。

## 科学边界与验收

原显式EMDB level条件保持；语义Dice为Emap0.160／CA2 0.757；A1B32（B:1001）、occurrence1的原实例IoU为0.306／0.656，沿原Emap blob2／CA2 blob1。原Emap FP为blob3、32体素、与全部真值无交集。没有重新计算任何指标、筛选预测或运行模型。

完整隔离重建、八会话科学材料逐体素／原点／间距／模型变换核查通过；实际PPT对齐5组通过，PDF最小字号6.96pt，碰撞检查0 fail／0 warn。主代理自查后由stage1_author15_review独立全面审查，唯一图注指涉和坐标注释问题修复后仅定向复核，已批准。正式PPT只读原生打开、双语图注精确一致和新页目视通过；全局追溯check为114条记录／100图通过。

## 后续与文件入口

本任务已完成。作者若继续调图，保留原始作者会话，更新正式PPT及追溯；Stage3和两个E2E作者案例保持。本轮没有Git暂存、提交、分支或远端操作。

- 画图/古法Chimera/stage1/论文图说明.md：八会话导航及比例修复说明。
- 画图/画图代码/stage1/visualization/stage1-author-global-local-9nvs/：build.py、README及ops/publish.py。
- 画图/画图代码/stage1/output/stage1-author-global-local-9nvs/：冻结输入、最终会话、预览及qa证据。
- 画图/画图代码/stage1/visualization/图表追溯.md：同名正式记录。
- talk/author_visualization_20261103/执行记录.md：本实验沿用日志，正式制图／发布与门控命令分开。
- RULES/执行记录.md：共享总日志状态。
