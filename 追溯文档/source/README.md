# 论文实际使用的服务器原件

这里回答“图、表和正文数字究竟来自服务器的什么文件”。先按下表选择实验，再看对应说明中的原命令、配置、模型、划分、排序和失败记录。每张图的筛选、统计和完整绘图命令放在该 Figure 目录的 `trace.md`；独立数字的算式放在 [`../claim/`](../claim/)。

| 类别 | 阅读入口 | 要区分的条件 |
| --- | --- | --- |
| 内部 Find | [Find.md](Find.md) | GT 与 CryoAtom2；全配体与全部小分子；主模型与输入消融 |
| 内部 Match | [Match.md](Match.md) | 完整模型与三个输入消融；前景评价与精确 SMILES 身份评价 |
| 内部 Build | [Build.md](Build.md) | GT/CA2、Centre/Envelope、官方/无密度/DG；标准 446 实例与共同交集 235 实例 |
| 外部 Emap2lig 无 level | [Emap2lig-nolevel.md](Emap2lig-nolevel.md) | 原输入未显式传 EMDB 推荐 level；仅当前对应补图使用 |
| 外部 Emap2lig 显式 level | [Emap2lig-level.md](Emap2lig-level.md) | 输入推荐 L，官方应用 L/2；保留原过滤和失败资格 |
| 外部 EMERALD-ID | [EMERALD-ID.md](EMERALD-ID.md) | 原查询结果、有效身份、失败状态及原文件时间 |

共同输入见 [原始输入.md](原始输入.md)、[CryoAtom2受体.md](CryoAtom2受体.md)。端到端必须分清三套作用：[受控给定身份的 Find–Build](E2E-受控身份.md)、[实际全身份 Match 的计费与原四构象链](E2E-实际计费.md)、[作者展示所需的补齐构象](E2E-作者构象.md)。它们服务相同页面也不能合并成一份实验。全部沉积实例的 present 重原子原统计见 [重原子统计.md](重原子统计.md)。

## 本地与服务器逐字节相同的十一份说明

下面的两列表也是同步程序读取的唯一说明更新清单。本地路径相对此文件；服务器目标都是已经存在的 `trace.md`。同步只更新这些文件的字节，不同步或清理它们所在的实验目录。

| 本地说明 | 服务器说明 |
| --- | --- |
| [原始输入.md](原始输入.md) | `/storage/penghongen/AdaLigand/Ori_Data/trace.md` |
| [Find.md](Find.md) | `/storage/penghongen/AdaLigand_stage1_inference/trace.md` |
| [Match.md](Match.md) | `/storage/penghongen/Matcher/trace.md` |
| [Build.md](Build.md) | `/storage/penghongen/PocketXMol/trace.md` |
| [Emap2lig-level.md](Emap2lig-level.md) | `/storage/penghongen/Emap2lig/contour_level_20261026/trace.md` |
| [Emap2lig-nolevel.md](Emap2lig-nolevel.md) | `/storage/penghongen/AdaLigand_stage1_inference/Emap2lig/official_find_li/trace.md` |
| [E2E-受控身份.md](E2E-受控身份.md) | `/storage/penghongen/Adaligand_E2E/test/test_0/trace.md` |
| [E2E-作者构象.md](E2E-作者构象.md) | `/storage/penghongen/Adaligand_E2E/actual_display_20261101/trace.md` |
| [重原子统计.md](重原子统计.md) | `/storage/penghongen/备份/原本所有tmp的备份/adaligand_ligand_stats_20260809_Oir8rJ/trace.md` |
| [CryoAtom2受体.md](CryoAtom2受体.md) | `/storage/penghongen/Adaligand_infered_receptor_data/cryoatom2/test_0_chain06/trace.md` |
| [E2E-实际计费.md](E2E-实际计费.md) | `/storage/penghongen/PocketXMol/final_evaluation/end_to_end/trace.md` |

EMERALD-ID 的既有查询与计时说明对应服务器 Matcher 根的说明；准确率和实际启动记录见[独立数字说明](../claim/EMERALD-ID身份准确率.md)。单独阅读入口不构成第十二份服务器镜像。服务器科学原件是结果来源；全面 Git 保存论文文件历史，作者 CXS 保存显示，AI handoff 辅助接续工作，三者不替代实验原件。

## 读取与复核

科学选择和评价规则属于 Figure。`TOOLS/server_io/source.py` 只做明确路径的只读传输和字节校验；D 盘缓存限 `D:/AdaLigand_Visualization` 内的服务器原样副本。转换、统计 JSON、渲染和核查材料只写本次根 `temp/`。不以旧 D 盘加工文件、旧绘图容器或全面 Git 历史作为当前结果的回退输入。

记录中保留的历史 tmp 路径表达当时命令，不代表当前代码仍依赖它。已经具名迁出的必要文件从上述持久位置读取；不能把历史路径文字匹配等同于活动依赖。
