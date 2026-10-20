# 一键同步文件、Git 状态和 AI 报告

双击 [run_sync.bat](run_sync.bat)，将 `C:\Users\15919\Desktop\论文草稿` 单向更新到 `C:\Users\15919\Desktop\论文草稿-Gdrive`。脚本同步文件、建立独立浅 Git 仓库、核对 staged 与 unstaged 状态，并覆盖固定位置的 AI 报告。无需 commit 或 push。

默认历史起点为 `963675351a04a0309509b80759da7a1da4c88306`。副本保留该提交的原 SHA、当前分支在该起点以后的历史、当前 HEAD、原始索引和磁盘文件；不复制此前历史、其他分支、tags、stash、reflog、remote 或 hooks。原仓库不被改写。副本不是执行 Git 操作的主仓库，下次同步会重新以母目录为准。

## 固定产物和开关

```text
论文草稿-Gdrive/
├─ .git/                         # 独立浅仓库，可执行 status 和 diff
├─ draft.md 等源文件              # 已保存的当前文件
└─ temp/AI-Git/
   ├─ 当前Git改动报告.pdf         # 给 Drive Gemini 阅读，固定路径
   ├─ 当前Git改动报告.md          # 同内容原始文本，保留差异行
   ├─ Git状态.json               # 快照编号、时间、HEAD 和核对结果
   ├─ Gemini提示词.md             # 持久阅读提示词
   ├─ .sync-report-owner.json     # 专用报告目录的所属源和托管文件清单
   └─ history/                   # 仅关闭清理时归档旧报告
```

`temp/AI-Git/` 是副本专用产物目录；通过副本自身的 Git 排除规则隐藏，不计入 staged、unstaged 或未跟踪改动。Google Drive 仍会正常上传这些文件。请在 Gemini 项目中选择报告 PDF 作为来源，并核对最新快照编号及上传状态。

`run_sync.bat` 中的 `CLEAN_OLD_REPORTS=1` 默认开启清理：新报告成功发布后删除该目录的全部历史归档，仅保留固定的当前报告。改成 `0` 后，旧报告归档到 `history/<旧snapshot_id>/`，固定报告位置保持不变；恢复为 `1` 后会清除全部历史归档。此开关管理报告与报告生成中间文件，不清除用户文件的覆盖和删除备份。

[Gemini提示词.md](Gemini提示词.md) 是源模板，每次同步复制到上述固定位置。它要求 AI 先核对快照时间和 HEAD，分清 staged、unstaged、未跟踪、二进制变化和预览限额；有终端时运行 Git，没有终端时依据报告分析。

`Git状态.json` 是当前报告的元数据对象：

| 字段 | 类型与含义 | 构造示例 |
|---|---|---|
| `version` | 整数，元数据格式版本 | `1` |
| `snapshot_id` | 字符串，本次同步编号；与报告、运行目录一致 | `run-20261020-140000-a1b2c3d4` |
| `time` | 带时区的 ISO 时间字符串，报告生成时间 | `2026-10-20T14:00:00+08:00` |
| `baseline` | 字符串，浅历史起点 SHA | `963675351a04a0309509b80759da7a1da4c88306` |
| `head` | 字符串，源当前提交 SHA | `963675351a04a0309509b80759da7a1da4c88306` |
| `branch` | 字符串，当前分支名；分离 HEAD 有明确标记 | `main` 或 `(detached HEAD)` |
| `verified` | 布尔值，发布前是否通过源与副本状态核对 | `true` |
| `index_sha256` | 64 位十六进制字符串，原索引文件字节摘要 | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` |

报告逐层列出 staged 和 unstaged 的文本差异；同一文件可同时出现在两层。未跟踪文件单列，UTF-8 文本每文件预览最多 64 KiB、总计 512 KiB；每层差异最多 100 万字符，超限明确标记。二进制文件只报告发生变化，不推断 Word、PPT 等文件的具体语义变化。PDF 使用嵌入的微软雅黑字体，长行自动折行；精确差异行以 Markdown 或终端输出为准。

## 文件同步和安全边界

- 为保持 Git 状态，**已跟踪文件全部复制**，即使后来命中 `.gitignore`；忽略规则只筛选未跟踪文件。这与旧版“忽略已跟踪文件”的行为不同。
- 未保存的编辑不在磁盘文件中，请先保存。同步期间暂停 `add`、commit、checkout、reset 等 Git 操作。脚本发现源状态变化或 Git 锁时停止，不发布新报告。
- 根 `temp/`、`.git/` 和 Drive 内部临时目录不作为源文件复制；若它们仍作为未跟踪文件出现在源状态中，应先在源忽略规则中排除。源已跟踪这些保留目录时直接拒绝同步。
- 同名副本以母目录为准，被覆盖的副本先备份到源 `temp/`。源中删除、重命名、后来被忽略的未跟踪文件，其旧副本会移入删除备份。
- 副本额外文件保留，并在副本本地排除规则中隐藏，避免污染 Git 状态。副本已有非本工具管理的 `.git` 或非空报告目录时拒绝接管。
- 更新采用独立临时文件替换，不透过副本硬链接回写源文件。源与副本须同盘且互不包含；路径上的符号链接、联接和云端占位重解析点不支持。
- 源必须有正常索引和提交；split index、Git 子模块、Git 符号链接暂不支持。HEAD 必须包含起点；切到起点以前、无关分支或绕过起点引入旧历史的合并路径时拒绝同步。
- Git 对象缓存增量抓取并清理不可达旧对象。最终副本没有指向母目录的 alternates、remote 或共享 Git 目录。源仓库和其大体积旧历史不会被整理或删除。
- 整个目录更新不是跨文件的原子事务。失败前的部分副本写入可能已经生效；失败运行不得视为成功快照，请排除问题后重新运行。报告仅在本轮 Git 与文件核对通过后发布，仍应以控制台显示成功为准。

## 入口、依赖与运行记录

本工具依赖 Git、Windows PowerShell、Python 3.11 以上及 `reportlab`。PowerShell 启动器依次使用 `-PythonExe`、环境变量 `CODEX_PYTHON`、本机 Codex 随附 Python。默认这台机器已经具备依赖；需要更换环境时，设置 `CODEX_PYTHON` 并在该环境安装 `reportlab`。PDF 使用 Windows `Fonts/msyh.ttc`。

```powershell
# 预览文件变动，不修改副本、Git 缓存和报告。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\同步到Gdrive\sync_to_gdrive.ps1" -DryRun

# 本次保留历史报告，不修改 bat 的默认设置。
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\同步到Gdrive\sync_to_gdrive.ps1" -CleanOldReports 0
```

源端运行文件均位于 `temp/gdrive-sync/<目标路径摘要>/`。摘要沿用旧版的目标路径小写 SHA256 前 16 位大写字符，旧文件清单自动迁移到版本 2。

```text
论文草稿/temp/gdrive-sync/<目标路径摘要>/
├─ state.json                  # 成功清单：version、source、destination、baseline、files、snapshot_id
├─ sync.lock                   # 防并发锁
├─ cache.git/                  # 独立浅 Git 对象缓存，供增量抓取
└─ run-<时间>-<随机后缀>/
   ├─ sync.log                 # 本次日志
   ├─ replaced/                # 被覆盖的用户副本文件，按原相对路径保存
   └─ removed/                 # 被移出的用户副本文件，按原相对路径保存
```

`state.json` 的 `version` 当前为 `2`；`source`、`destination` 为绝对路径字符串；`baseline` 为固定 SHA；`files` 为相对路径字符串数组，如 `["draft.md", "画图/stage1结果.pptx"]`，可以为空；`snapshot_id` 为最近完整成功运行编号。它只管理源文件，不包含 `.git` 和 AI 报告。清单丢失后不会猜测删除未知副本文件；副本归属仍由 `.git/sync-owner.json` 的 `source` 与 `baseline` 核对。

运行中还会创建 `staged/`、`snapshot.git/`、`bridge.git/`、`reports/` 和索引对象 pack；成功后清除这些大体积中间文件。失败时留证，默认清理开关会在下一次成功运行后清理这些旧中间文件。用户文件备份和短日志保留，需按自己的备份策略管理。

实现位置见 [ops/README.md](ops/README.md)，当前规格见 [规划.md](规划.md)，运行证据见 [执行记录.md](执行记录.md)。