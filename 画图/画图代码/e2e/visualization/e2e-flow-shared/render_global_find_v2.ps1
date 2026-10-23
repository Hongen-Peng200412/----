# 七例仅删除原生排名标签; 所有临时启动文件和控制台输出统一位于 temp.
$taskProject = 'C:/Users/15919/Desktop/论文草稿'
$taskTemp = "$taskProject/temp/e2e_flow_v2_20261003"
$env:PYTHONIOENCODING = 'utf-8'
$taskResults = @()
foreach ($taskPdb in @('9bjj','30ga','9llg','9rd8','9qru','9wup','9xzl')) {
    $taskCxc = "$taskProject/画图/画图代码/e2e/visualization/e2e-flow-shared/$($taskPdb)_global_find.cxc"
    $taskWrapper = "$taskTemp/run_$taskPdb.cxc"
    [IO.File]::WriteAllText($taskWrapper,"open `"$taskCxc`"`nexit`n",[Text.UTF8Encoding]::new($false))
    $taskStarted = Get-Date
    $taskProcess = Start-Process -FilePath 'D:/ChimeraX 1.10.1/bin/ChimeraX.exe' -ArgumentList @('--cmd',('"open '+$taskWrapper+'"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$taskTemp/$taskPdb.stdout.txt" -RedirectStandardError "$taskTemp/$taskPdb.stderr.txt"
    $taskFolder = "$taskProject/画图/画图代码/e2e/output/e2e-flow/display/$taskPdb"
    foreach ($taskName in @('renders/global_find.png','global_session.cxs','commands.html')) { if ((Get-Item -LiteralPath "$taskFolder/$taskName").LastWriteTime -lt $taskStarted) { throw "stale output: $taskPdb/$taskName" } }
    $taskResults += [pscustomobject]@{pdb=$taskPdb;exit_code=$taskProcess.ExitCode;fresh_outputs=$true}
    $taskResults | ConvertTo-Json | Set-Content -LiteralPath "$taskTemp/render_execution.json" -Encoding UTF8
    Write-Output "$taskPdb : native labels removed; fresh global_find PNG/session/log, process exit=$($taskProcess.ExitCode)"
}
