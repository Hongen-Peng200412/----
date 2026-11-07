# 实际预测身份的补齐构象与作者复合物

服务器产物根：`/storage/penghongen/Adaligand_E2E/actual_display_20261101`。本地副本：`追溯文档/source/E2E-作者构象.md`。两份文件必须逐字节相同；本地与服务器不能分别手改成近似文字。

本说明解释已经存在的实验原件、原生产命令及论文如何读取它们，不是新的实验数据来源。AI 接续 handoff 和论文全面 Git 只辅助工作与恢复历史，不替代这里列出的服务器原件。本说明保存原实验事实和可定位的生产记录。此前获准迁出的六份旧 tmp 脚本、元数据仍按下文的持久位置读取。

本地中性传输工具为 `TOOLS/server_io/source.py`，只负责按明确地址取得原字节。每图的输入选择、统计规则及展示入口见 `画图/画图代码/正文/`、`补充材料/` 或 `BACKUP/` 下对应 Figure 的 `trace.md`。独立数字的解释见 `追溯文档/claim/`。D 盘仅可保存服务器原文件的逐字节副本；转换、裁切和渲染写入本次 `temp/`，不长期保存为另一套科学输入。

## 原始正式命令和源码

真实命令为 `bash ligandseek_pipeline/ops/run_actual.sh`，不是重新执行旧评价。实际冻结代码在本根 `control/releases/AdaLigand_e15f82b50271/AdaLigand/`；`control/launches/441686/actual_display_job441686_20261101T155310/{run_cmd.sh,launch.json}` 保存真实命令和H200/16CPU身份。run_cmd中引用的旧allocation路径只是当时控制记录；读取已发布结果不依赖继续保留该allocation。当前共享服务器AdaLigand主目录没有这两个ops模块，本轮不为了整理而上传或改服务器源码，直接沿保存的release解释原运行。

`GT/requests.jsonl` 为505条，`CA2/requests.jsonl` 为540条。每域 `display_results.jsonl` 是完整实际输出索引；逐项以domain+PDB+source_blob_index连接。每项output_dir/metrics_file/ranking_file明确定位 `build/test/local-c1/<pdb>/<blob>/` 下的 `scientific_input.json/result.json/candidates.json/poses.sdf/confidence.npz/evaluation_metrics.json/ranking.json`。

GT的280请求复用原构象、202新增成功、23输入失败；CA2为268复用、248新增成功、24输入失败。复用条件是原精确SMILES、世界中心、原模型及50姿态/100步一致。新增pose不读取真实参考坐标，其RMSD为null，不是0；原输入失败保留失败原因，不伪造构象。`control/final_audit.json` 是原生产收口核查，不替代具体pose和请求。

## 作者图与 BACKUP 如何选择

当前9BJJ/9UJF保护会话保持原CA2、原100%预算、原Top-1显示事实。合法参考评价仍来自原 `test/test_0/` 构象；新增背景或错身份构象从本根补齐，只作为真实实际输出显示，不追加到成功数或RMSD范围。9BJJ10/11，十个有参考Top-1范围0.5034656633–1.1161003298Å，背景输出的RMSD不参与；9UJF十个原GTP实例范围0.5364181403–0.8048328745Å。

30GA BACKUP需读取 `CA2/display_results.jsonl` 中本PDB/blob5的实际成功pose；其背景身份没有合法参考RMSD。其余三例预算与成功数由原E2E traces决定，不在这里重新定义。

作者会话的保留范围、原生重开方法和显示保护要求见正文 Fig7、Fig8 的 trace.md；本说明只说明会话所显示对象的科学来源。显示原件不是独立实验真值，原科学文件与上述请求始终可定位。
