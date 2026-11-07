# Fig7/8 的作者工作台科学适配

Fig7（9BJJ）拥有本目录中的 E2E 显示选择规则，Fig8（9UJF）显式复用。两图各自的 `../case.json` 和 `../../Fig8-visual-E2E-9UJF/case.json` 声明 PDB、CryoAtom2 受体、受控测试条件、100% 预算和模型 Top-1 等出版条件。打开作者 CXS 时，这些出版条件只用于绑定和指路，不覆盖作者保存的当前控件、显隐、颜色或视角。

这里读取的是当前 CXS 内嵌的 `scene` 与模型引用，不访问服务器、D 盘加工材料或 `scene.folder` 指向的旧目录。实验原件与生成条件见本图 [trace.md](../trace.md) 及项目 [E2E 作者构象来源](../../../../../追溯文档/source/E2E-作者构象.md)。不重新计算 Find 对应、Match 预测、RMSD、原始姿态排序或评价分母。

## 代码与内存字段

```text
workbench/
├─ selection.py  # 原累计计费、候选类别过滤和已存在构象档位选择
├─ display.py    # 手动覆盖后的显隐计划、状态报告与科学控件说明
├─ adapter.py    # 两图显式绑定、科学控件枚举与作者主动操作
└─ __init__.py   # 本图科学包标识
```

建议按 `selection.py` → `display.py` → `adapter.py` 阅读。通用窗口、Qt 信号、模型监听、CXS v1 恢复和另存机制位于 [TOOLS/chimerax/workbench](../../../../../TOOLS/chimerax/workbench/README.md)，不在此目录复制。

`scene` 顶层包含 `pdb_id`（如 `9bjj`）、`counts`、`domains`、`models`、`occurrences`，以及可选的 `pose_modes`。其余既存字段随 CXS 原样保存，不作为新外部读取位置。

| 字段 | 实体、类型与对齐关系 | 示例 |
|---|---|---|
| `counts.all/small/eligible` | 整数，全部配体、小分子、合格小分子的实例数，分别用于相应模式预算分母 | 9BJJ 的 `eligible=11` |
| `domains[受体条件].candidates` | 候选列表，`CA2` 与 `GT` 分别表示 CryoAtom2 与沉积受体条件 | `domains.CA2.candidates` |
| `source_blob_index` | 原始候选编号，与 `models[].blob` 对齐，不重新紧凑编号 | `0` |
| `before[模式]` | 该候选之前已经消耗的累计尝试次数，严格 `<预算` 才纳入 | `before.pipeline=0` |
| `foreground_target/is_small/is_eligible` | 布尔值，分别表示真实前景、小分子、可评价小分子类别，决定画面过滤 | `is_small=true` |
| `predicted_smiles` | 原 Match 预测身份字符串，随候选保存，不重新规范化 | 9BJJ 的 blob 0 为 ATP 对应的显式氢 SMILES |
| `actual_build.status/failure_reason` | 原 Build 状态及失败原因，仅当前 pipeline 可见候选进入状态报告 | 9BJJ 的 blob 0 为 `status=success`、`failure_reason=null` |
| `models[].key/id` | 字符串，稳定模型 key 与 ChimeraX 点分模型编号；模型引用按编号接回 | `CA2_blob_0` 对应 `10.1` |
| `models[].kind` | 模型类别；管理 `blob/pose/identity/correctness`，`area` 仅供主动 home 命令处理 | `blob` |
| `models[].domain/blob` | 受体条件与原候选编号，联结候选列表 | `CA2`、`0` |
| `models[].views/pose/pose_modes` | 可用模式和原构象档位；不按当前 RMSD 重新排名 | `CA2_pose_0_0_top1` 为 `pose=top1`、`views=[find_build,pipeline]` |
| `models[].note` | 既有构象备注；可见且备注非空者进入缺参考 RMSD 的 Top-1 提示 | 9BJJ 的 `CA2_pose_0_0_top1` 为 `note=""`，无缺失提示 |
| `occurrences` | 聚焦菜单列表，每项含 `display_name/site/candidate_id`；编号沿用原会话 | `ATP`、`A:901`、`candidate_id=0` 对应原参考组 `#3.1` |

`config` 保存七项：`view`、`condition`、`budget`、`filter`、`pose`、`identity`、`correctness`。`view` 包含全部 Find、小分子 Find、Find+Match、给定正确身份的 Find+Build，以及实际 Find+Match+Build；前两种分母分别为全部配体和小分子，Find+Match 为全部配体，后两种为合格小分子。预算为分母乘 50/100/200/300% 后向下取整，`all` 表示全部候选；过滤发生在预算截断之后，不回填更后候选。

构象选择沿用会话已有 `top1/top5/best/both` 档位：模型首选、原评分前五中 RMSD 最小、原评价 best-of-50，以及同时显示 top1 与 best。缺少 `top5` 内嵌材料时明确报错，不读取外部材料补齐。切换模式/受体/预算清空手动显隐覆盖；切换构象只清理构象覆盖，保留 blob 和标签覆盖；标签按钮只改标签，不重新显示手动隐藏的 blob。

`display.report` 返回 `pdb_id/config/status`、实际可见 `visible`、相对预设多出的 `extra`、缺少的 `hidden`、`manual_overrides`，以及当前可见候选的 `build_states` 和有备注的 `rmsd_unavailable_top1`。这些是对画面的说明，不生成新的科学评价结果。

## 作者操作与输出

打开既有作者会话即可恢复工作台。`ligwork show` 显示面板，`ligwork status` 将真实显示状态写入 Log。只有主动 `focus/pocket/home/overview/unzone` 命令才改变相机、局部地图或表示；自动恢复和状态刷新不触发这些操作。`upgrade` 只核对当前内嵌模型，不从旧 `folder` 读取材料。

`ligwork save` 在 `画图/Chimera/<pdb>/` 另存新编号 CXS 并内嵌地图；`ligwork export` 另存 PNG。原 `古法Chimera` 会话不被改写。状态诊断 JSON 只允许进入本次项目 `temp`，完成验收后可整体清空。
