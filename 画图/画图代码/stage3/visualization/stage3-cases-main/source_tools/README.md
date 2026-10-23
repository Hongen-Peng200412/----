# 冻结案例的取数与选择来源

本目录保留从完整测试评价筛查、只读提取和核对案例的入口；默认离线制图直接读取 `stage3/output/stage3-cases-main/assets/`，不调用这些取数工具、不访问服务器。

按以下顺序冷读：`screen.py` 从冻结官方／微调／Build评价选择误差对照候选；`fetch_cases.py` 将原top-1姿态、沉积坐标、标准受体和局部实验密度从服务器只读复制；`analyze.py` 计算该筛选集合的密度覆盖和碰撞；`finalize_source.py` 比对正式十例的离线指标、写CSV和资产SHA；`check_frozen_metrics.py` 对十例PocketXMol的原评价做只读核对。前四个是来源重建工具，不是模型实验入口。

完整历史筛选依据位于 `stage3/output/stage3-cases-main/screening/`：`screen.json` 为完整冻结指标筛选，`shortlist.json` 为28例取数清单，`case_metrics.json` 为28例测量，`assets/<pdb>_<occurrence>/` 保存相应56份坐标／密度数组和元数据。原正式十例独立保留，未来换例不得用同PDB的其他实例代替。

`screen.py`、`fetch_cases.py`、`analyze.py` 的可再生工作目录固定为仓库 `temp/stage3-case-sources/`。`fetch_cases.py` 会调用项目只读SSH helper，重新取数前应按项目服务器规则核对执行环境；它不重新推理、重排候选或评价RMSD。真实取数逻辑从原 `temp/stage3_cases/` 救回，远端科学字段、top-1选择和坐标裁取未改变。

日常核对只需：

```powershell
python 画图/画图代码/stage3/visualization/stage3-cases-main/source_tools/check_frozen_metrics.py
```

它对 `cases.json` 中每个实例的官方／微调原 `sample_index`、RMSD及碰撞计数逐项核对，不改任何产物。完整三维字段、单位、坐标及显示定义见所属 `../README.md` 和阶段 `../../图表追溯.md`。
