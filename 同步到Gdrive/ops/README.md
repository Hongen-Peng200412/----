# 同步运维实现

这些脚本只维护本地副本和 Git／AI 阅读产物，不定义论文科学内容。用户入口、固定路径、清理开关和产物字段以 [上层说明](../README.md) 为准。

| 文件 | 职责 |
|---|---|
| `sync_snapshot.py` | 文件选择、锁、暂存、状态复核、增量发布、备份及报告清理 |
| `git_snapshot.py` | Git 字节接口、三层状态读取、浅历史抓取与索引对象补齐 |
| `ai_report.py` | 当前差异报告和元数据生成，使用 reportlab 排版 PDF |
| `tests/verify_sync.py` | 在源 `temp/` 下建立独立仓库，验证部分暂存、浅历史、删除和报告清理 |

维护时先看 `sync_snapshot.py` 的 `execute`，再按调用位置查看 Git 快照和报告生成。需要调整 Git 命令时保留 `GIT_OPTIONAL_LOCKS=0`、源对象只读和副本无 alternates 的约束。需要调整报告格式时保留 staged 与 unstaged 的独立段落、固定路径、时间和 snapshot_id，并重做 PDF 视觉核对。

在仓库根目录运行验证，所有测试仓库、日志和 PDF 都留在 `temp/git-snapshot-verification/`：

```powershell
$env:PYTHONIOENCODING = 'utf-8'
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -B '.\同步到Gdrive\ops\tests\verify_sync.py'
```

测试只在临时仓库中提交，不对作者工作区 add 或 commit。实际同步的报告路径属于副本；Python 的 `-B` 和入口设置阻止缓存文件散落到源码目录。
