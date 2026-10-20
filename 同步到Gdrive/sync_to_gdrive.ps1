<#
单向同步入口. Python 运维实现位于 ops/sync_snapshot.py.
优先使用 -PythonExe, 其次使用 CODEX_PYTHON, 最后使用本机 Codex 随附环境.
#>
[CmdletBinding()]
param(
    [string]$SourceRoot = '',
    [string]$DestinationRoot = '',
    [string]$BaselineCommit = '963675351a04a0309509b80759da7a1da4c88306',
    [ValidateSet(0, 1)][int]$CleanOldReports = 1,
    [string]$PythonExe = '',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
try {
    if (-not $SourceRoot) { $SourceRoot = Split-Path -Parent $PSScriptRoot }
    if (-not $DestinationRoot) { $DestinationRoot = Join-Path (Split-Path -Parent $SourceRoot) ((Split-Path -Leaf $SourceRoot) + '-Gdrive') }
    if (-not $PythonExe) { $PythonExe = $env:CODEX_PYTHON }
    if (-not $PythonExe) { $PythonExe = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' }
    if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw '找不到 Python. 请设置 CODEX_PYTHON 或 -PythonExe, 并在该环境安装 reportlab.' }
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $arguments = @('-B', (Join-Path $PSScriptRoot 'ops/sync_snapshot.py'), '--source', $SourceRoot, '--destination', $DestinationRoot, '--baseline', $BaselineCommit, '--clean-old-reports', "$CleanOldReports")
    if ($DryRun) { $arguments += '--dry-run' }
    & $PythonExe @arguments
    exit $LASTEXITCODE
}
catch {
    Write-Host "同步失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}