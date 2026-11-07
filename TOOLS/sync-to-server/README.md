# 项目完整文件历史同步

本套件把一次明确的本地磁盘状态保存到服务器独立 Git，并从提交另行恢复全部文件、核对原字节后才发布成功回执。它属于文件历史运维工具，只处理文件、链接描述和 Git 状态，不解释实验目录、结果数字或评价规则。

项目镜像的正式服务器根固定为 `/home/penghongen/manuscript_full_history/LigandSeek`。另外，完整发布会按作者提供的 `--document-index` 两列表更新明确列出的既有 MD。科学地址只来自项目人读索引，不写进工具源码；工具不理解或改写统计内容。当前精选 Git 和 GitHub 的提交由作者另行管理；本套件不替作者 commit、push 或改写精选历史，也不复制项目 `.git/`，不新建旧状态备份分支。

本轮首次有效版本从**规范化完成后实际捕获并验收的项目状态**开始，不构造旧提交当时没有保存的完整磁盘状态。首次切换完成后，普通同步只沿这条新正式历史追加。

## 收录范围

捕获项目根的全部实体文件，包括精选 Git 忽略的 CXS、`.review/`、固定依赖及作者素材。只排除项目根 `.git` 和根 `temp`；嵌套目录同名文件不因名称而额外排除。Git worktree 的根 `.git` 指针文件同样排除，索引摘要读取该 worktree 实际使用的索引。

文件或目录链接只记录相对位置、链接种类和原目标字符串，不遍历目标、不把目标内容纳入完整版本。完整恢复验收覆盖项目实体文件和链接描述；恢复 Windows junction 时仍需依据记录恢复链接关系，不能宣称链接指向的软件或数据已得到保存。

作者应先保存文件，再暂停源文件及 Git 写操作。看到 `CAPTURE_COMPLETE` 后可以恢复编辑：后续上传读取独立副本，不再读取正在编辑的源文件。该副本与源不共享硬链接。

## 工具与文件位置

```text
论文草稿/
├─ TOOLS/sync-to-server/
│  ├─ sync.py                       # 本地捕获、严格 SSH、传输及四个命令入口
│  ├─ server.py                     # 部署根内的完整版本事务及独立恢复
│  ├─ run_sync.bat                  # 普通 snapshot 的本机便捷入口
│  ├─ test_sync.py                  # 仅本地隔离夹具, 不连接服务器
│  └─ README.md                     # 当前接口与恢复契约
└─ temp/figure-centric/sync-to-server/<syncid>/
   ├─ capture/                      # 与源独立的实体文件副本, 不含链接目标
   └─ manifest.json                 # 已完整复核的路径、原字节摘要和来源 Git 状态
```

```text
/home/penghongen/manuscript_full_history/LigandSeek/
├─ history.git/                     # 独立普通 Git, full-history 为当前正式分支
├─ runs/<syncid>/
│  ├─ project/                      # 本次接收的实体文件, 删除反映在新版本
│  └─ snapshot/manifest.json        # 随本次全面提交保存的完整清单
├─ control/
│  ├─ current.json                  # 唯一有效版本回执, 最后原子发布
│  ├─ sync.lock/                    # 单写者锁及本次事务身份（同步临时状态）
│  ├─ publication.json              # 引用与回执发布中断的收口记录（同步临时状态）
│  ├─ document-stage/<syncid>/       # 本事务旧MD原字节及操作清单, 成功/回滚后清除（同步临时状态）
│  └─ index-<syncid>                # Git 独立索引（同步临时状态）
├─ restore/<syncid>/                # 从提交实际检出的完整版本（恢复临时目录）
└─ original-git/                    # 既有历史材料, 本套件不再新增、修改或删除
```

`project/` 是项目文件副本，目录中各文件的科学含义由项目自身的说明定义。`snapshot/` 和 `control/` 是同步元数据，不是实验结果来源。既有 `runs/`、原归档和旧 Git 对象均不清理，不建立保护旧版本的新分支，也不执行对象回收。

## 正式命令

日常完整同步从论文项目根运行：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/sync-to-server/sync.py snapshot --document-index 追溯文档/source/README.md
```

作者已授权本轮首次切换；执行者完成项目规范化和图表验收后，显式运行：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/sync-to-server/sync.py reset-history --expect-current 1e0f23ad9382692e7529ecb06f41d7b7677fd5bf --document-index 追溯文档/source/README.md
```

`reset-history` 只接受这一个已核对的旧正式提交，且只允许第一次成功切换。新提交没有旧父节点；完整恢复通过后才精确替换正式 `full-history` 引用和有效回执。远端引用变化、已经切换、文件不一致或恢复失败均不继续覆盖。程序的 `complete` 只表示文件捕获完整，不能代替作者对科学结果和目录规范化的验收。

普通 `snapshot` 从未规范化的旧历史开始时会拒绝，不会隐式执行重置。既有旧对象仍保留在服务器；它们不进入新正式分支的祖先链。

## 明确说明文件的同步范围

`run_sync.bat` 默认传入 `追溯文档/source/README.md`。该索引必须包含唯一一张表头为 `| 本地说明 | 服务器说明 |` 的两列表；下例仅说明格式，服务器路径不是本项目的真实地址：

```markdown
| 本地说明 | 服务器说明 |
| --- | --- |
| [说明甲](a.md) | /example-server/run-a/trace.md |
| b.md | /example-server/run-b/trace.md |
```

本地一列相对索引 README，必须是项目内既有 MD；服务器一列必须是明确的绝对 MD 路径，目标必须已经存在且是普通文件。工具读取捕获副本中的表格和 MD 原字节，不在 `CAPTURE_COMPLETE` 后追读已编辑的本地源，也不递归同步服务器实验目录。

项目镜像和说明文件是两个独立写入范围：镜像的删除只限本次 `runs/<syncid>/project/`；说明文件只用既有文件的 `r+b` 写入、截断和复读核对，不创建目标目录、旁边临时文件或备份文件。旧说明字节只短期存入上述论文部署根 `control/document-stage/`，用于同一事务失败时恢复原目标，完成后清除。

所有映射 MD 的原字节一致，且项目 Git 独立恢复通过，才允许发布镜像。项目构造、恢复或发布失败时，工具回滚自己已触及的说明；已有正式回执保持不变。同步期间应暂停同时编辑这些源说明和目标 MD。各目标原位写入不具备跨多个文件的外部可见原子性，成功条件是全部复核后共同发布，不是旁观者永远看不到中间写入。

查看实际完整历史及其对应精选提交：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/sync-to-server/sync.py coverage
```

可以附加 `--source-head` 和一个完整精选 SHA，只查询这个精选提交实际捕获过的完整版本。`covered=false` 表示没有对应快照；不能用当前 CXS、GitHub 的 HEAD 或相邻版本补造它。相同精选 HEAD 可以对应多个完整版本，因为忽略文件仍可能改变。连续多次本地提交后再同步一次同样有效，未同步的中间提交如实显示没有覆盖。

`coverage` 通过严格 SSH 执行只读查询，不上传服务程序、不建接收目录、不改服务器状态。本地 `server.py` 随请求临时执行，程序本身保存在本套件及被捕获的项目版本中，不在服务器额外常驻安装。

再次独立恢复并检验一个正式全面提交时，运行 `verify --commit` 并附完整全面 SHA：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/sync-to-server/sync.py verify --commit 完整全面提交SHA
```

SHA 从 `coverage` 返回的 `commit` 字段取得。验证只在部署根的 `restore/` 写临时检出，成功或报错后清理该次检出；旧正式代之外的提交不会被冒称为本轮有效版本。

## 完整清单与回执

`manifest.json` 的重要字段如下；字段值均指本次实际捕获，不倒填过去的状态。

| 字段 | 类型与含义 | 具体形式 |
| --- | --- | --- |
| `version`、`scope`、`complete` | 清单版本、固定收录边界、捕获是否完整 | `2`、`"project-excluding-root-git-and-temp"`、`true` |
| `syncid` | 本次同步的唯一编号 | `"sync-20261107T010203Z-a1b2c3d4"` |
| `operation` | 首次切换或普通追加 | `"reset-history"` 或 `"snapshot"` |
| `generation` | 本轮正式历史的首次同步编号 | 如 `"sync-20261107T010203Z-a1b2c3d4"` |
| `expected_current` | 本次允许替换的精确正式全面 SHA | 首次为上述 `1e0f23ad...` 完整 SHA |
| `source` | 捕获的本地项目绝对路径 | 如 `"C:\\work\\manuscript"` |
| `head`、`branch` | 捕获时的精选提交及分支 | SHA 格式例为 `"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`；分支如 `"main"`，分离 HEAD 为 `"HEAD"` |
| `dirty`、`status_hex` | 精选 Git 是否有未提交变化及 porcelain 原字节的十六进制 | 干净时为 `false`、`""` |
| `source_index_sha256` | 捕获时真实索引的摘要 | 摘要格式例为 `"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"` |
| `captured_utc` | 完整复核结束的 UTC 时间 | 如 `"2026-11-07T01:02:03+00:00"` |
| `files` | 每个实体文件的相对路径、大小、源 mtime 和原字节摘要 | 下述单文件记录 |
| `links` | 原链接的相对路径、种类和目标 | 下述链接描述 |
| `document_index` | 捕获副本内的人读两列表位置 | 如 `"追溯文档/source/README.md"` |
| `documents` | 表中明确的相对源路径、绝对目标及新字节摘要 | 如 `{"source":"docs/a.md","target":"/example-server/run-a/trace.md","sha256":"edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb"}`，其 MD 原字节仍以 `abc` 加 LF 为格式例 |

上述连续 `a`、`b` 只用于说明摘要长度，不代表正式提交或真实索引。若 `notes.txt` 有未暂存修改，`status_hex` 的格式例为 `"204d206e6f7465732e74787400"`，即 Git 原状态字节 ` M notes.txt` 后跟一个 NUL；不能从 `dirty` 推断忽略文件是否改变。

`files` 中一项的格式例：`notes.txt` 原字节为 `abc` 加一个 LF，大小 4 字节。以下仅说明文件记录格式，不冒充一次正式观测。

```json
{"path":"notes.txt","bytes":4,"mtime_ns":1794013323000000000,"sha256":"edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb"}
```

链接描述的格式例：

```json
{"path":"runtime-link","kind":"directory","target":"C:\\tools\\runtime"}
```

`mtime_ns` 记录源文件时间；恢复判定核对路径集合、文件大小、SHA-256 和完整清单，不要求 Git checkout 恢复文件系统时间。链接目标只作为字符串保存。

成功回执包含 `history_format=2`、`generation`、`history_root`、`syncid`、全面 `commit`、`source_head`、`source_branch`、`source_dirty`、`captured_utc`、文件数、字节数、链接数、接收位置以及 `complete=true`、`restored_verified=true`。`documents` 回执如 `{"mapped":11,"live_verified":true,"changed":11}`，表示映射数量、发布时是否核对现场目标、实际改写数量。`history_root` 是本轮孤儿起点的全面 SHA。`source_dirty=false` 只说明精选 Git 干净；被精选忽略的会话变化由 `files` 摘要识别。

检验历史全面提交时，项目中保存的说明字节和映射会独立恢复核对，不把今天的服务器说明误称为旧版内容，也不回写旧目标。该次 `verify` 回执的 `documents.live_verified=false`；现场说明一致性由发布事务负责。

## 失败、恢复与发布顺序

捕获期间源文件、路径集合、HEAD、分支、索引或 Git 状态变化时，不生成完整清单、不上传项目文件。上传按内容增量进行，使用新接收目录，删除只作用于本次 `project/`；不使用 `--inplace`，不改上一版本的文件。

服务器先核对接收目录，再创建提交，然后在另一个 `restore/` 目录实际检出全部项目文件和清单，逐件核对。通过后以精确旧 SHA 更新正式引用，最后原子替换 `current.json`。发布前失败，旧有效回执保持不变；引用更新后若回执替换失败，会按精确新旧 SHA 回滚引用。

若进程或网络在发布阶段中断，`publication.json`、说明短期暂存和同步锁可能保留。它们只是同一次事务的短期收口材料，不是旧项目备份。使用该次原 `manifest.json` 所在目录恢复：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/sync-to-server/sync.py snapshot --resume temp/figure-centric/sync-to-server/实际同步编号
```

首次切换的恢复命令仍使用 `reset-history`，并附原 `--expect-current`。恢复会复核独立副本的路径、元数据和全部文件摘要，不重新读取已编辑的源。只允许本事务拥有者收口；不会抢别人的锁，也不会自动把预期旧 SHA 改成较新的远端 SHA。

如果服务端已经发布且仅成功响应丢失，恢复同一次事务会识别真实成功回执，核对并清除说明暂存，不把已发布的说明误回滚。若尚未发布，则先回滚本事务的说明及未发布引用，再继续同一次捕获。捕获副本在成功后删除；失败现场保留在项目 `temp/`，供同一次恢复使用，不能把失败接收目录称为有效版本。

正式引用和有效回执均已发布后，即使删除发布记录或同步锁失败，也保持已经校验的新说明；使用同一次 `--resume` 完成收尾。发布前失败才回滚旧说明，避免项目已是新版本、说明却退回旧字节。

## 阅读实现与本地测试

先读 `sync.py::main` 的命令分派，再读 `capture` 的独立捕获和源复核；网络部分看 `request`、`transfer`。服务器从 `server.py::main` 的只读查询、事务开始、正式构造、独立恢复和最终发布顺序阅读；`check_tree` 只核对文件边界和摘要，不包含科学定义。

本地需要 Python 3.11 以上、Paramiko，以及既有 MSYS2 的 rsync、sshpass、ssh、cygpath；MSYS2 查找顺序为 `PROJECT_MSYS_ROOT`、`MSYS2_ROOT`、`C:/msys64`、`D:/msys64`。本机便捷入口使用既有 `D:/Anaconda/python.exe`。服务端使用 Python 3.10 及兼容 Git 1.8.3 的命令，不要求升级公共环境。

连接固定 endpoint 时严格读取本机 `.ssh/known_hosts`；未知或变化的主机密钥立即拒绝。凭据来自本机私有 `.ssh/pocket_plus_sshpass.txt` 或调用者临时提供的 `CODEX_SSH_PASSWORD`，不写项目、命令参数、清单或日志。

测试命令与正式命令分开：

```powershell
D:/Anaconda/python.exe -X utf8 -B TOOLS/sync-to-server/test_sync.py
```

测试在 `temp/figure-centric/sync-tests/` 创建隔离源仓库、隔离服务器仓库和本地 rsync 镜像，并在同一 `temp/figure-centric/` 下检查捕获副本的限定清理，不连接服务器。覆盖原字节、中文路径、忽略文件、链接不跟随、worktree、首次孤儿历史、增改删、失败不发布、发布回滚、中断后同事务恢复、重复恢复、源索引改变、旧版本独立恢复、缺失覆盖及相同 HEAD 下不同忽略文件状态。测试结束清除其创建的夹具，不触真实项目 Git 引用或既有服务器档案。
