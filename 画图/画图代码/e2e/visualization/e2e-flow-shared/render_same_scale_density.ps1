# 七例完整原地图沿用原 global_structure 相机; 导图仅写 v2, 临时启动与控制台记录统一写 temp.
$ErrorActionPreference = 'Stop'
$taskProject = 'C:/Users/15919/Desktop/论文草稿'
$taskTemp = "$taskProject/temp/e2e_flow_v2_20261003"
$env:PYTHONIOENCODING = 'utf-8'
$taskResults = @()
foreach ($taskPdb in @('9llg','9bjj','30ga','9qru','9rd8','9wup','9xzl')) {
    $taskCxc = "$taskProject/画图/画图代码/e2e/visualization/e2e-flow-shared/$($taskPdb)_global_density_same_scale.cxc"
    $taskWrapper = "$taskTemp/run_density_same_scale_$taskPdb.cxc"
    [IO.File]::WriteAllText($taskWrapper,"open `"$taskCxc`"`nexit`n",[Text.UTF8Encoding]::new($false))
    $taskStarted = Get-Date
    $taskProcess = Start-Process -FilePath 'D:/ChimeraX 1.10.1/bin/ChimeraX.exe' -ArgumentList @('--cmd',('"open '+$taskWrapper+'"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$taskTemp/$taskPdb.density.stdout.txt" -RedirectStandardError "$taskTemp/$taskPdb.density.stderr.txt"
    $taskFolder = "$taskProject/画图/画图代码/e2e/output/e2e-flow/display/$taskPdb"
    foreach ($taskName in @('renders/global_density_same_scale.png','global_density_same_scale_commands.html')) { if ((Get-Item -LiteralPath "$taskFolder/$taskName").LastWriteTime -lt $taskStarted) { throw "stale output: $taskPdb/$taskName" } }
    $taskResults += [pscustomobject]@{pdb=$taskPdb;exit_code=$taskProcess.ExitCode;fresh_outputs=$true}
    $taskResults | ConvertTo-Json | Set-Content -LiteralPath "$taskTemp/render_same_scale_density_execution.json" -Encoding UTF8
    Write-Output "$taskPdb : complete density rendered with receptor camera; fresh PNG/log, process exit=$($taskProcess.ExitCode)"
}
