# Handoff：端到端案例图与 ChimeraX 复现

日期：2026-10-03。

## 当前状态

端到端案例图、Results 段落、PPT 备注图注及两版新 Word 已完成。七个 CA2 案例组成十页图集，前两页作为图 12、13 插入正文；范围门禁组合及七个独立详页保留在 PPT 中。

## 已完成

- 首位成功：9BJJ、9LLG、9RD8；背景后成功：30GA、9QRU；范围外前景后成功：9WUP、9XZL。
- 七例均显示已有第一次 local_cov-C 的实际 self-ranking Top-1，RMSD 为 0.52–1.04 Å，没有选择 best-of-50 或重新推理。
- 原生 ChimeraX `.cxc` 制备八种图；每例 `.cxs` 含地图，原子、密度与 blob 可分别编辑。PPT 原生文字、布局、箭头和编号可编辑，三维截图不拆成原子对象。
- 来源、排名、SDF、MRC 坐标和颜色经过主代理检查及独立审查；最终十页 PDF 对齐与碰撞审计通过。
- Word 采用原仓库转换器，原生 Word PDF 实际分页已检查，图 12、13 与图注同页。Nature 新稿 46 页，Operation 新稿 36 页。

## 已定口径

背景消耗尝试但未进入 Match/Build；非 Stage3 前景由冻结门禁免费跳过。9WUP 前两项仍是 small_molecule，不能统称“非小分子”。9QRU 第二项 `selected=false` 但由完整候选顺序进入实际对接。另一个全配体 Matcher 的成功身份只作单独来源说明，不拼成 Stage3 调用。

Python 仅做下载、加载和标准格式转换，科学显示必须继续用原生 ChimeraX 命令。相机、颜色或密度轮廓调整应修改 `.cxc`、导出 PNG、回 PPT 替换图片，不能用 Python 重画分子或投影体素。图注改 PPT 备注，正文改 Markdown。

## 后续操作

用户可以在十页图集中选择最终案例，或依据 README 在 ChimeraX 调整公共视角。当前正文采用 9BJJ/30GA 与 9LLG/9QRU；备选未自动加入主文。已有 `论文草稿.operation.docx` 的其他修改保留，本轮新稿使用独立 `.E2E可视化.docx` 文件名；未提交 Git。

## 重新打开的文件

- [正文](../../../论文草稿.md)
- [图集](../../../画图/E2E案例可视化.pptx)
- [原生命令教程](../../../画图/画图代码/e2e_cases_20261003/README.md)
- [执行记录](../../../画图/画图代码/e2e_cases_20261003/执行记录.md)
- [来源清单](../../../画图/formal/E2E_cases_20261003/source_manifest.json)
- [Nature 新稿](../../../论文草稿.nature.E2E可视化.docx)
- [Operation 新稿](../../../论文草稿.operation.E2E可视化.docx)
