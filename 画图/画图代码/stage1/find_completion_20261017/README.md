# Stage1全部小分子的Find完成度

本目录只汇总既有Find预测，供正文Fig.4下排比较GT、CA2和Emap2lig。目标为原Stage1全部小分子：94个PDB、821个实例，不施加Stage3的单残基或原子完整性条件。端到端模块和77／446的旧统计保持原样。

`assemble_data.py`只含一个按顺序读取的`main`：读取原Stage1成员及类别，连接完整Find候选，沿原候选顺序记录每个实例首次检出，最后调用AdaLigand原`make_panel`。Emap2lig的唯一对应直接复用Matcher原`_target_from_intersections`；先在全部类别中确定对应，再判断其是否属于小分子。背景保留，对应非小分子的候选跳过；重复命中仍占候选位置，同一实例只增加一次完成度。

输入沿用`画图/formal/Stage1_main_sixpanel_20260929/data/server_metrics_and_pr.json`的94-PDB顺序。GT／CA2的完整Find字段位于`画图/formal/E2E_accounting_20261004/sources/full_matcher.json`；这里只读取其中的Find字段，不使用身份预测。Emap2lig的原生NPZ位于`画图/formal/fmb_20261015/sources/Emap2lig/find_metadata/per_pdb/`。原类别文件保存在`画图/formal/Stage1_find_completion_20261017/sources/occurrences/`，`sources/sources.json`保存服务器路径、大小和SHA256；它们与原Stage1来源记录一致。

输出为`画图/formal/Stage1_find_completion_20261017/panels.json`和`summary.json`。前者的`panels`包含三份原完成度字典，例如`id="find_stage1_small_GT"`、`scope="find_stage1_small"`、`pdb_count=94`、`occurrence_count=821`；这是论文内部标识。`curve`保留精确事件阶梯，`distributions["100"]`保留94个PDB在候选数等于各自真实实例数时的完成比例，`success_events`保留首次检出的实例编号与位置。后者记录各方法的分母、全候选统计及固定相对候选数下的均值和中位数。没有检出的PDB仍在均值和中位数的统计集合中。

从论文仓库根运行：

```powershell
& D:/Anaconda/python.exe -B 画图/画图代码/stage1/find_completion_20261017/assemble_data.py
```

共享图集的装配入口仍在`../../stage3/fmb_20261015/`。该目录只追加读取本目录的三个统计面板，保留旧面板和姿态数据，再由Fig.4明确选择本次全部小分子范围。正式生成、Word编译与验收记录见`RULES/执行记录.md`的2026-10-17条目；一次性核查不进入本目录正式调用链。
