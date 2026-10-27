> 本轮目录与当前追溯入口：本目录已按固定5×3结构迁移。当前图名、输入、科学口径、实际命令及生成位置以[所属追溯文档](../图表追溯.md)为准；下文有日期或历史版本的装配命令只作历史说明。冻结输入在所属output，重绘写temp或regenerated，正式PPT仍在画图根目录。

# Find–Build 共享实现

本目录保存三张论文图共同读取的冻结结果组装、完成度图元及同源SVG转原生PPT工具。每张图的布局入口位于所属阶段的同名目录，统计定义不在多个目录复制。

| 图 | 独立绘图入口 | 临时构建目录 |
|---|---|---|
| 纯Find实例完成度 | ../../../stage1/calculate/find-only-instance-completion/plot.py | temp/find-only-instance-completion |
| 预测区域引导的对接比较 | ../../../stage3/calculate/stage3-predicted-region-head-to-head/plot.py | temp/stage3-predicted-region-head-to-head |
| 正确身份Find–Build补充曲线 | ../supp-find-correct-match-build/plot.py | temp/supp-find-correct-match-build |

`assemble_data.py`连接两种Find命中实例与原构象结果；`completion_plot.py::draw_panel`只画冻结的逐PDB分布和精确事件阶梯；`save_figure`接受调用图的构建目录，输出SVG/PDF/PNG与图名、物理尺寸和双语图注。RMSD仍为原模型排序的Top-1或best-of-50，失败保留完整成功率分母；GT共同命中235、有效配对231，CA2共同命中230、有效配对228。

## 显式 EMDB level 条件

上述 235／231、230／228 是原 `no_level` 条件。新条件 `explicit_emdb_level` 的共享输入独立保存在 `e2e/output/find-build-shared/explicit_emdb_level/`，不覆盖原 `data.json`、`sources/` 或旧结果归档。新配对为 GT 共同命中247、有效数值241，CA2共同命中243、有效数值237；这些追溯计数用于区分集合，正文只保留对应论点需要的最终数值。

从仓库根运行：

```powershell
python -X utf8 -B 画图/画图代码/e2e/calculate/find-build-shared/assemble_data.py --condition explicit_emdb_level
```

输入实物是 `补充数据/Emap2lig_双条件/explicit_emdb_level/` 内的179份逐PDB交集、260份原Build请求及逐姿态结果、固定446实例身份。GT／CA2 的原面板和原姿态保留，新的公平比较在新的共同子集上重新汇总。94／821 的全部小分子面板读取 `stage1/output/stage1-results-revision/explicit_emdb_level/data/completion_panels.json`；它由Stage1入口独立生成，不能由77／446的Build范围替代。

同一物理输出根按科学输入与核对证据分列如下。

```text
## <科学产物>
e2e/output/find-build-shared/explicit_emdb_level/
├─ data.json                    # panels为29个完成度面板；pairs为GT／CA2共同实例与数值配对
├─ paired_pose.csv              # 全部247＋243个共同实例，缺失RMSD留空
├─ selected_blob_events.json    # 260个实际Build请求的blob、原Find排名与计费号
└─ topk_data.json               # 仅替换Emap两条曲线的十档PDB成功整数计数

## <其他文件>
e2e/output/find-build-shared/explicit_emdb_level/
├─ summary.json                 # 配对摘要和完整分母固定预算统计（运行统计）
├─ number_changes.json          # 原值和新值对照，不是另一套统计定义（核对导出）
└─ statistics_validation.json   # 旧条件回归、函数身份和新blob绑定核对（验收证据）
```

`data.json.condition="explicit_emdb_level"` 明确科学条件；`panels` 的字段、完整分母、精确相对预算及失败语义与原输入完全相同。`pairs.GT.numeric_rows`如一项真实实例，`tuned_top1/emap_top1/tuned_best/emap_best` 是原模型排名对应的世界坐标重原子RMSD，单位Å；只有四项均非null的实例进入数值分布。CSV的`(domain,pdb_id,occurrence_id)`是连接键，`tuned_blob/emap_blob`是各自原预测候选编号，不相互对应。

`selected_blob_events.json` 每项有 `pdb_id`、`occurrence_id`、`source_blob_index`、`find_rank`、`charged_attempt`、`status`。例如11jb/0对应原生`blob_56`、`find_rank=50`；计费号在跳过真实范围外前景后计算，不能直接使用50代替。一个blob先在全部真实类别中按原双向覆盖规则唯一归属；真正有姿态的只会是该实例实际提交Build的blob。不能把同一实例较早命中的其他blob也记成Build成功。背景和范围内重复候选仍计费，未检出及失败实例始终留在77 PDB／446实例的分母。

`topk_data.json` 的 `full.emap2lig` 是179-PDB全配体在K=1…10的成功数，新值为`[76,92,97,98,100,101,102,102,102,104]`；`small_find.emap2lig` 是77-PDB合格小分子范围的成功数，新值为`[46,53,57,57,59,59,59,59,59,59]`。成功表示前K个计费候选中至少有一个实例命中，不是恢复实例比例；其余GT／CA2匹配和姿态曲线保持原样。

绘图时用 `FIND_BUILD_DATA` 显式指向本条件 `data.json`；两个top-k页用 `E2E_TOPK_DATA` 显式指向 `topk_data.json`。所有候选由 `FIGURE_BUILD_ROOT` 指定到本次构建目录。未传数据环境变量时保留原无level入口，不能以文件日期猜测条件。先读本节条件与字段，再读 `assemble_data.py::main` 的显式条件分支，最后按上表选择原有图形入口；共享绘图函数只消费冻结结果。

冻结输入位于 `../../output/find-build-shared/`，字段和版本见所属阶段图表追溯记录及原产物README。重建数据默认写regenerated，不覆盖原件。建议依次读取冻结data.json契约、所属图plot.py，再读共用图元；场景运输不参与科学计数。

在仓库根先运行某张图的plot.py，再运行 `python -B 画图/画图代码/e2e/calculate/find-build-shared/svg_shapes.py --build-root temp/<该图名>`，随后执行 `node 画图/画图代码/e2e/calculate/find-build-shared/assemble.mjs temp/<该图名>`。场景字段保持原有pt坐标、文字、独立散点和路径；新候选位于对应output/regenerated，不自动覆盖作者图集。需要PowerPoint实际渲染时再显式调用ppt_metadata.py的同一--build-root参数。

旧三图联合生成器已归档；当前各图只生成自身布局。正式图集的来源批注通过仓库转换工具ops/figure_provenance.py同步。
