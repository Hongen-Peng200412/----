# 只读取得服务器原件

`source.py::SourceStore` 接受本次构建目录及原样缓存目录。调用方提供服务器绝对路径，工具经严格主机校验的 SSH/SFTP 读取原字节、核对 SHA-256，再提供 JSON、JSONL、NPZ 解析。凭据取本机既有配置，不输出到日志。

`read_bytes`、`json`、`npz` 读取一种原件，`read_many` 批量预取明确文件，`local_file` 供应需要真实文件路径的读取器。`reads` 记录本次路径、大小和摘要，`close` 关闭连接。字段、维度、实例连接和评价语义由 Figure 解释。

工具不猜最新结果，不选择模型、checkpoint、受体或指标，不写服务器科学文件。D 缓存只存原样服务器副本；转换及读取回执只写本次根 temp。
