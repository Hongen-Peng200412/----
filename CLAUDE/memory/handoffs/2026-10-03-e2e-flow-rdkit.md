# Handoff：端到端流程版案例图

日期：2026-10-03。

## 当前状态

用户要求按桌面的端到端流程草图重画同一批七个案例，现已完成。新图集按 Input → Find → Match → Build 逐步排列，每页一个案例；正文原两张组合图替换为四张独立流程图，图号为 12–15。原 PPT 和已暂存的原 Word 均保持不变。

## 已完成

- 新 PPT 为 `画图/E2E案例可视化-端到端流程版.pptx`，页序是 9BJJ、30GA、9LLG、9QRU、9RD8、9WUP、9XZL。前四页引用到正文，其余为备选。
- 七例完整实验地图只读取得，CA2／GT 受体、全部原始 blob 的全局分布均画出，35 项取景核查通过。原生 ChimeraX 共生成 76 张三维 PNG 和每例的局部、全局 CXS；每例一个 `<pdb>_reproduce.cxc` 即可完整复现。
- Match 是独立步骤，全部 22 个输入 SMILES 身份按原顺序呈现 RDKit SVG；蓝框标出精确匹配，范围外身份保留为灰色。化学图、电荷与已声明手性逐项核对。
- Build 使用原冻结 `local-c1` self-ranking Top-1；受体表面、密度网格、GT 叠加三种外观使用同一份世界坐标。未重跑推理或重新筛选姿态。
- PPT 保留原生文字、箭头、身份框与独立图片组件；三维原子层编辑回到 CXS，不宣称 PNG 已成为 PPT 原子对象。七页最终原生 PDF 对齐与碰撞审计通过。
- 已生成 `论文草稿.nature.E2E流程版.docx`（49 页）与 `论文草稿.operation.E2E流程版.docx`（38 页）。新图及完整图注同页；Nature 对应第 28、29、31、32 页，Operation 对应第 22–25 页。

## 当前约定

Python 仅制备基础科学资产；本轮用户另外明确要求 RDKit 二维身份图，因此二维结构使用 RDKit，三维相机、受体、密度和配体均继续由原生 ChimeraX 命令制备。完整地图与受体全景采用适合各自范围的相机；局部 GT／Find 对照以及同一姿态三种 Build 视图分别共用相机。

背景消耗尝试，但没有实际 Match／Build。9WUP、9XZL 的范围外前景沿冻结 Stage3 门禁免费跳过；9WUP 的前序实例仍属于 small_molecule，不能称为“非小分子”。9QRU 的 `selected=false` 候选仍由完整顺序进入评价。图注中的 50 姿态／100 步预算仅适用于所示成功目标。

生成 Nature Word 后必须运行 `fit_word_layout.py`：只对四个新图在该副本中等比缩放至 148 mm 高，并使用单倍图片段落行距；正文和图注保持原 Nature 版式。脚本同步 PPT 回转证据，序列化时排除关系编号，实际图片的 `r:embed` 保留。共享转换器未改。Operation 不需要该后处理。

## Git 与后续

未创建提交、分支或 worktree；用户原已暂存的旧 PPT、旧 handoff、Markdown 和 Operation Word 保留。`论文草稿.md` 仅增加四处新 PPT 引用并同步图号，属于当前未暂存修改。代码、formal 产物及新 Word 的忽略规则维持原状；若用户要求 Git 归档，再明确整理范围，不能默认提交别人的暂存内容。

本轮没有待完成任务。后续改图回到新 PPT 或原生 CXC，改图注回到 PPT 备注；正文回到 Markdown，再按教程生成两版 Word。原 `2026-10-03-e2e-cases-chimerax.md` 是旧风格的历史交接，不能用其图号或 Word 页数覆盖当前记录。

## 重新打开的文件

- [新七页图集](../../../画图/E2E案例可视化-端到端流程版.pptx)
- [正文源稿](../../../论文草稿.md)
- [原生命令与 RDKit 复现教程](../../../画图/画图代码/e2e_flow_20261003/README.md)
- [本轮执行记录](../../../画图/画图代码/e2e_flow_20261003/执行记录.md)
- [Nature 新稿](../../../论文草稿.nature.E2E流程版.docx)
- [Operation 新稿](../../../论文草稿.operation.E2E流程版.docx)
- [全局地图来源](../../../画图/formal/E2E_flow_20261003/full_density_manifest.json)
- [原生三维图记录](../../../画图/formal/E2E_flow_20261003/native_render_manifest.json)
