<#
将源仓库的当前文件单向复制到 Gdrive 副本. 主入口在文件末尾.
默认源目录是本脚本所在文件夹的上一级, 目标是同级的 <源目录名>-Gdrive.
Git 决定忽略范围, SHA256 决定是否更新; 不读取提交中的旧文件内容.
temp/gdrive-sync/<目标路径摘要>/state.json 保存 source、destination 和 files(相对路径数组).
运行日志、覆盖备份、删除备份和复制暂存文件全部保存在同一状态目录的 run-* 子目录.
#>
[CmdletBinding()]
param(
    [string]$SourceRoot = '',
    [string]$DestinationRoot = '',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false, $true)

function Get-FullPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
}

function Assert-PlainPath([string]$Path) {
    # 拒绝符号链接和目录联接, 防止目标路径间接指回源稿; 普通硬链接由替换写入拆开.
    $cursor = $Path
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "路径含重解析点, 请使用普通本地目录: $cursor"
            }
        }
        $parent = Split-Path -Parent $cursor
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}

function Get-ChildPath([string]$Root, [string]$Relative) {
    # Git 清单和状态清单都只允许普通相对路径, 例如 画图/stage1结果.pptx.
    if ([string]::IsNullOrWhiteSpace($Relative) -or [IO.Path]::IsPathRooted($Relative) -or
        $Relative.Contains(':') -or ($Relative -split '[/\\]' | Where-Object { $_ -in '.', '..', '' })) {
        throw "无效相对路径: $Relative"
    }
    $full = Get-FullPath (Join-Path $Root $Relative)
    if (-not $full.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "文件越过指定目录: $Relative"
    }
    Assert-PlainPath $full
    return $full
}

function Test-ReservedPath([string]$Relative) {
    # Drive 自动产生的内部目录和本工具运行目录固定排除, 不依赖作者额外修改 .gitignore.
    return $Relative -match '(^|/)(\.git|\.tmp\.driveupload|\.tmp\.drivedownload)(/|$)|^temp(/|$)'
}

function Invoke-GitText([string]$Arguments) {
    # 直接解码 Git 的 UTF-8 字节并保留 NUL 分隔符, 避免中文、空格和换行文件名被 shell 拆开.
    $start = New-Object Diagnostics.ProcessStartInfo
    $start.FileName = $script:gitPath
    $start.Arguments = '--no-optional-locks ' + $Arguments
    $start.WorkingDirectory = $script:SourceRoot
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $start
    $buffer = New-Object IO.MemoryStream
    try {
        [void]$process.Start()
        $copyTask = $process.StandardOutput.BaseStream.CopyToAsync($buffer)
        $errorTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        [void]$copyTask.GetAwaiter().GetResult()
        $errorText = $errorTask.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw "Git 执行失败: $errorText" }
        return $script:utf8.GetString($buffer.ToArray())
    }
    finally {
        $buffer.Dispose()
        $process.Dispose()
    }
}

function Get-SyncFiles {
    $candidates = Invoke-GitText 'ls-files --cached --others --exclude-standard --exclude=.tmp.driveupload/ --exclude=.tmp.drivedownload/ -z'
    $ignoredTracked = Invoke-GitText 'ls-files --cached --ignored --exclude-standard -z'
    $ignored = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $ignoredTracked.Split([char]0)) { [void]$ignored.Add($name) }
    $seen = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $candidates.Split([char]0)) {
        if (-not $name -or (Test-ReservedPath $name) -or $ignored.Contains($name) -or -not $seen.Add($name)) { continue }
        $path = Get-ChildPath $script:SourceRoot $name
        if (Test-Path -LiteralPath $path -PathType Container) { throw "暂不展开 Git 子模块或目录项: $name" }
        if (Test-Path -LiteralPath $path -PathType Leaf) { $name }
    }
}

function Get-Sha256([string]$Path) {
    # 直接使用 .NET, 避免 bat 启动环境的 PowerShell 模块自动加载差异.
    $stream = [IO.File]::Open($Path, 'Open', 'Read', 'Read')
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '') }
    finally { $hasher.Dispose(); $stream.Dispose() }
}

function New-Parent([string]$Path) {
    [void][IO.Directory]::CreateDirectory((Split-Path -Parent $Path))
}

$lock = $null
$transcribing = $false
try {
    if (-not $SourceRoot) { $SourceRoot = Split-Path -Parent $PSScriptRoot }
    $SourceRoot = Get-FullPath $SourceRoot
    if (-not $DestinationRoot) {
        $DestinationRoot = Join-Path (Split-Path -Parent $SourceRoot) ((Split-Path -Leaf $SourceRoot) + '-Gdrive')
    }
    $DestinationRoot = Get-FullPath $DestinationRoot
    if ($SourceRoot -eq $DestinationRoot -or
        $DestinationRoot.StartsWith($SourceRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $SourceRoot.StartsWith($DestinationRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw '源目录和副本目录必须分离, 且不能互相包含.'
    }
    if ([IO.Path]::GetPathRoot($SourceRoot) -ne [IO.Path]::GetPathRoot($DestinationRoot)) {
        throw '副本与源目录需位于同一盘符, 以便通过原子替换写入并在 temp/ 保存备份.'
    }
    Assert-PlainPath $SourceRoot
    Assert-PlainPath $DestinationRoot
    $gitPath = (Get-Command git.exe -ErrorAction Stop).Source
    $gitRoot = (Invoke-GitText 'rev-parse --show-toplevel').TrimEnd("`r", "`n")
    if ((Get-FullPath $gitRoot) -ne $SourceRoot) { throw '源目录必须是 Git 仓库根目录.' }

    $sha = [Security.Cryptography.SHA256]::Create()
    try { $stateKey = ([BitConverter]::ToString($sha.ComputeHash($utf8.GetBytes($DestinationRoot.ToLowerInvariant())))).Replace('-', '').Substring(0, 16) }
    finally { $sha.Dispose() }
    $stateDir = Join-Path $SourceRoot "temp\gdrive-sync\$stateKey"
    Assert-PlainPath $stateDir
    [void][IO.Directory]::CreateDirectory($stateDir)
    try { $lock = [IO.File]::Open((Join-Path $stateDir 'sync.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { throw '同一副本已有同步进程运行, 请等待其完成后再试.' }
    $runDir = Join-Path $stateDir ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 6))
    [void][IO.Directory]::CreateDirectory($runDir)
    $logPath = Join-Path $runDir 'sync.log'
    [void](Start-Transcript -LiteralPath $logPath)
    $transcribing = $true
    Write-Host "源目录: $SourceRoot"
    Write-Host "副本目录: $DestinationRoot"
    Write-Host "运行日志: $logPath"
    if ($DryRun) { Write-Host '预览模式: 不修改副本和同步状态.' }

    $statePath = Join-Path $stateDir 'state.json'
    $previous = @()
    if (Test-Path -LiteralPath $statePath) {
        $state = [IO.File]::ReadAllText($statePath, $utf8) | ConvertFrom-Json
        if ($state.version -ne 1 -or $state.source -ne $SourceRoot -or $state.destination -ne $DestinationRoot) {
            throw '同步状态的版本或路径不匹配, 请检查 state.json.'
        }
        $previous = @($state.files)
        foreach ($name in $previous) {
            if (Test-ReservedPath $name) { throw "状态包含保留路径: $name" }
            [void](Get-ChildPath $DestinationRoot $name)
        }
    }

    $files = @(Get-SyncFiles | Sort-Object)
    $current = New-Object 'Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $updates = New-Object Collections.Generic.List[object]
    $unchanged = 0
    foreach ($name in $files) {
        [void]$current.Add($name)
        $source = Get-ChildPath $SourceRoot $name
        $target = Get-ChildPath $DestinationRoot $name
        if (Test-Path -LiteralPath $target -PathType Container) { throw "副本中同名位置是目录, 请先处理: $target" }
        $sourceHash = Get-Sha256 $source
        if ((Test-Path -LiteralPath $target -PathType Leaf) -and (Get-Sha256 $target) -eq $sourceHash) {
            $unchanged++
            continue
        }
        Write-Host "[更新] $name"
        if (-not $DryRun) {
            # 先完整复制并校验到 temp/, 再替换副本; 替换不会透过硬链接改写源稿.
            $staged = Get-ChildPath (Join-Path $runDir 'staged') $name
            New-Parent $staged
            [IO.File]::Copy($source, $staged, $false)
            if ((Get-Sha256 $staged) -ne $sourceHash -or (Get-Sha256 $source) -ne $sourceHash) {
                throw "复制期间源文件发生变化, 请保存后重新运行: $name"
            }
        }
        $updates.Add([pscustomobject]@{ relative = $name; hash = $sourceHash })
    }
    $removed = @($previous | Where-Object { -not $current.Contains($_) })
    foreach ($name in $removed) { Write-Host "[移出副本] $name" }

    if (-not $DryRun) {
        [void][IO.Directory]::CreateDirectory($DestinationRoot)
        foreach ($update in $updates) {
            $name = $update.relative
            $staged = Get-ChildPath (Join-Path $runDir 'staged') $name
            $target = Get-ChildPath $DestinationRoot $name
            New-Parent $target
            if (Test-Path -LiteralPath $target -PathType Leaf) {
                $backup = Get-ChildPath (Join-Path $runDir 'replaced') $name
                New-Parent $backup
                [IO.File]::Replace($staged, $target, $backup)
            }
            else { [IO.File]::Move($staged, $target) }
            if ((Get-Sha256 $target) -ne $update.hash) { throw "副本写入后校验失败: $name" }
        }
        # 只移走上次成功同步清单中的文件; 副本额外文件和未知目录从不递归删除.
        foreach ($name in $removed) {
            $target = Get-ChildPath $DestinationRoot $name
            if (Test-Path -LiteralPath $target -PathType Container) { throw "待移除文件已变为目录, 请先处理: $target" }
            if (Test-Path -LiteralPath $target -PathType Leaf) {
                $backup = Get-ChildPath (Join-Path $runDir 'removed') $name
                New-Parent $backup
                [IO.File]::Move($target, $backup)
            }
        }
        $newState = [ordered]@{ version = 1; source = $SourceRoot; destination = $DestinationRoot; files = @($files) }
        $pendingState = Join-Path $runDir 'state.json'
        [IO.File]::WriteAllText($pendingState, ($newState | ConvertTo-Json -Depth 4), $utf8)
        if (Test-Path -LiteralPath $statePath) { [IO.File]::Replace($pendingState, $statePath, (Join-Path $runDir 'previous-state.json')) }
        else { [IO.File]::Move($pendingState, $statePath) }
    }
    Write-Host "完成: 文件 $($files.Count), 更新 $($updates.Count), 无变化 $unchanged, 移出清单 $($removed.Count)." -ForegroundColor Green
    if ($DryRun) { Write-Host '预览完成, 副本未修改.' }
    else { Write-Host '本地副本已处理; 云端上传进度请查看 Google Drive 桌面版.' }
    $exitCode = 0
}
catch {
    Write-Host "同步失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host '源稿未被回写; 请处理上述问题后重新运行. 已生成的备份和日志保留在 temp/gdrive-sync/.'
    $exitCode = 1
}
finally {
    if ($transcribing) { [void](Stop-Transcript) }
    if ($null -ne $lock) { $lock.Dispose() }
}
exit $exitCode
