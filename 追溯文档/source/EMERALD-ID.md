# EMERALD-ID 外部身份预测原件

服务器实验根为 `/storage/penghongen/Matcher/evaluation/test_EMERALD-ID/`。本项在沉积真实小分子位点查询同一 PDB 内的候选身份，当前采用位置是补充材料中的独立文字分析。查询范围、截尾规则、有效评分分母及精确身份准确率见 [独立数字说明](../claim/EMERALD-ID身份准确率.md)。

原 `manifest/nxu/pdbs.jsonl` 保存 PDB 与候选精确 SMILES，`manifest/nxu/queries.jsonl` 保存沉积位点及评估答案，`manifest/nxu/excluded_pdbs.jsonl` 保存按成本排除的完整 PDB。GT 逐点结果位于 `EMERALD-ID/nxu/<pdb>/<occurrence>/result.json`，CA2 位于 `CryoAtom2/EMERALD-ID/nxu/<pdb>/<occurrence>/result.json`；两条件均通过 PDB 与真实 occurrence 编号连接相同冻结查询。

现存生产说明见 `C:/Users/15919/Desktop/Matcher/test_真实场景(Structure)/known_site/README.md`；已核对的冻结说明位于 Matcher 的 `491e58a92021`、`efecbf567afe` release 下相同目录，完整绝对位置及其解释的步骤见独立数字说明。原查询结果、官方排名和失败状态保持原位。

实际 `launch.json`、`run_cmd.sh`、绑定 release 和链名补跑清单的绝对位置见[实际启动记录](../claim/EMERALD-ID身份准确率.md#实际启动参数与补跑记录)。部分启动目录沿用旧任务名，实际动作由原 `run_cmd.sh` 和绑定入口解释；逐点结果本身没有保存 launch、release 与完整 argv，不能把整批最终结果归于单次运行。

既有查询与计时说明的服务器镜像入口为 [Match.md 的“EMERALD-ID 原查询”](Match.md#emerald-id-原查询)，对应 `/storage/penghongen/Matcher/trace.md`；身份准确率及实际启动、补跑记录见前述独立数字说明。独立耗时数字见 [运行时间.md](../claim/运行时间.md)。本页只提供外部结果的阅读入口，不建立第十二份服务器说明镜像或另一套结果缓存。
