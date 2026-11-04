# 作者交互式重绘两套案例：初始材料已交付

日期：2026-11-03。

## 当前状态

作者明确要亲手掌握颜色、显示和取景；AI准备完整材料、解释按钮、提供少量必要命令及最终追溯。范围仅9NVS Stage1的a–f和9WUP／2／FAD A:1103 Stage3的g–i，两个E2E作者案例保持。尚未替换正式PPT，不编译Word，不改指标或构象选择。

## 已完成

画图/古法Chimera/stage1与stage3各有初始材料_<PDB>.cxs、教程.md、来源.md、参考显示_<PDB>.cxs。Stage1初始是既有15材料模型会话的字节一致副本；GT与CA2受体均加载。Stage3新建，保留原GT/C0的PocketXMol sample22、DG sample18、显式level Emap rank1，以及完整GT16354原子、整实验密度、参考FAD与原14对碰撞伪键。各姿态53原子与原数组一致，地图值与坐标、伪键端点均已原生重开核对。

常见手动命令.md整理为短速查表；GUI教学不重复来源日志。用户预期Stage1只有a显示真实受体，b/c不显示受体；局部优先严格只平移放大，透明度是备选。这些是后续作者绘图意图，不是初始会话必须达到的外观。

Stage3共同环境需在碰撞标记前保存，g/h/i每次重开它，仅i增加红球／额外主链原子和#7，避免样式串用。原14对涉及8配体与10受体原子，含主链N/C/O/CA；cartoon suppressBackboneDisplay false允许实际主链碰撞原子显示。pocket、clashRec、clashLig已作为命名集合保存，可在Tools→Depiction→Basic Actions点击。

## 验证与后续

新脚本prepare_author_session.py、README及注释通过独立审查；唯一教程问题修复后仅窄查，已通过。全局追溯check通过113条记录／99图。正式图、稿件、Word、E2E会话与Git暂存区未由任务写入；作者期间自行改了draft.md的Methods小标题并更新暂存区，均保留，不恢复。

材料转换及来源在画图/画图代码/stage3/output/stage3-cases-main/explicit_emdb_level/author-session/，qa保存验收。日志talk/author_visualization_20261103/执行记录.md区分正式准备与门控命令。下一步等待作者自行调图，按其当前操作问题给予按钮或少量命令指导，保存最终author会话后再处理正式PPT与追溯。
