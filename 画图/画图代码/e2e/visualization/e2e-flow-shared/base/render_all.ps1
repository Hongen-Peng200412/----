# 本次七例资产的原生 ChimeraX 渲染入口. 临时启动文件和控制台日志统一放在 temp/e2e_flow.
param([string[]]$Cases = @('9bjj','30ga','9llg','9rd8','9qru','9wup','9xzl'))
$taskProject = 'C:/Users/15919/Desktop/论文草稿'
$taskCodeRoot = Join-Path $taskProject '画图/画图代码/e2e/visualization/e2e-flow-shared/base'
$taskTempRoot = Join-Path $taskProject 'temp/e2e_flow'
$env:PYTHONIOENCODING = 'utf-8'
$taskResults = @()
foreach ($taskPdb in $Cases) {
    & 'D:/Anaconda/python.exe' (Join-Path $taskCodeRoot 'prepare_flow_assets.py') --case $taskPdb
    if ($LASTEXITCODE -ne 0) { throw "基础资产转换失败: $taskPdb" }
    $taskWrapper = Join-Path $taskTempRoot "run_$taskPdb.cxc"
    $taskCommand = (Join-Path $taskCodeRoot "$($taskPdb)_reproduce.cxc").Replace('\','/')
    [IO.File]::WriteAllText($taskWrapper, "open `"$taskCommand`"`nexit`n", [Text.UTF8Encoding]::new($false))
    $taskArgs = @('--cmd', ('"open ' + $taskWrapper.Replace('\','/') + '"'))
    $taskStarted = Get-Date
    $taskProcess = Start-Process -FilePath 'D:/ChimeraX 1.10.1/bin/ChimeraX.exe' -ArgumentList $taskArgs -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $taskTempRoot "chimerax_$taskPdb.stdout.txt") -RedirectStandardError (Join-Path $taskTempRoot "chimerax_$taskPdb.stderr.txt")
    $taskFolder = Join-Path $taskProject "画图/画图代码/e2e/output/e2e-flow/views/$taskPdb"
    $taskImages = @(Get-ChildItem -LiteralPath (Join-Path $taskFolder 'renders') -Filter '*.png')
    $taskExpected = if ($taskPdb -in @('30ga','9qru')) { 13 } else { 10 }
    $taskComplete = $taskImages.Count -eq $taskExpected -and @($taskImages | Where-Object LastWriteTime -LT $taskStarted).Count -eq 0 -and (Get-Item -LiteralPath (Join-Path $taskFolder 'session.cxs')).LastWriteTime -ge $taskStarted -and (Get-Item -LiteralPath (Join-Path $taskFolder 'global_session.cxs')).LastWriteTime -ge $taskStarted -and (Get-Item -LiteralPath (Join-Path $taskFolder 'commands.html')).LastWriteTime -ge $taskStarted
    $taskResults += [pscustomobject]@{pdb=$taskPdb;exit_code=$taskProcess.ExitCode;render_count=$taskImages.Count;expected_count=$taskExpected;complete_files=$taskComplete}
    $taskResults | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskTempRoot 'render_execution.json') -Encoding UTF8
    Write-Output "$taskPdb : $($taskImages.Count)/$taskExpected images, session and log complete=$taskComplete, process exit=$($taskProcess.ExitCode)"
    if (-not $taskComplete) { throw "原生制图未完整落盘: $taskPdb" }
}
