# 当前方法图第5页的重建与素材

`assemble.py` 重放作者基底上的局部原生对象编辑，再调用 `ops/replace_density.py` 补入最终9LLG实验密度。输出是 `temp/fig-method-v8/candidate.pptx`；正式 `画图/Method总图.pptx` 与冻结基底不被覆盖。当前图名、病例、地图阈值、坐标、选择范围及完整来源以[所属追溯条目](../图表追溯.md#fig-method-v8共享输入与三阶段网络架构)为准。

```text
e2e/output/fig-method-v8/
├─ disk-before.pptx                # 原作者第5页基底，含原生形状与原媒体
├─ late-density-20261022/          # 最终密度PNG、PSE、阈值/相机、晚期发布证据
│  └─ source_receipt.json          # 21份新增冻结文件的原位置、散列与字节数
├─ receptor-9llg/                  # Find/Match受体PNG、PSE和完整相机向量
└─ build-pose-9bjj/                # Build输出的实际9BJJ PNG、PSE和残基片段/相机
```

基底中既有历史留证保持原状。晚期密度替换后，第5页Find／Match受体与三幅密度属于9LLG，Build底部配体结构图属于9BJJ；整页是网络流程示意，不宣称所有素材来自同一次推理。

从仓库根运行：

```powershell
python -X utf8 -B 画图/画图代码/e2e/visualization/fig-method-v8/assemble.py
```

过程另保存 `candidate_before_density.pptx`、`assembly.json` 和 `density_assembly.json`，便于区分形状编辑与密度替换。当前候选的第5页、备注、关系及全部媒体已与正式图集核对为字节相同；来源批注由项目同步器统一维护。

`ops/render_density.py`、`ops/render_receptor.py`、`ops/render_build_pose.py` 是可选重渲染入口，需要可导入 `pymol2` 的环境；它们只读取已冻结原坐标与原地图，分别写入 `temp/fig-method-v8/rendered/` 及其子目录。无需重渲染即可从冻结PNG重建最终候选，本轮没有启动PyMOL。
