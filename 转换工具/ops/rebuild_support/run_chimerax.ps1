# 在隐藏的独立ChimeraX进程中执行本次脚本，日志留在本次目录。
param([Parameter(Mandatory=$true)][string]$CxcPath,[Parameter(Mandatory=$true)][string]$LogPrefix)
$ErrorActionPreference='Stop'
$taskExecutable=if($env:FIGURE_CHIMERAX){$env:FIGURE_CHIMERAX}else{'D:/ChimeraX 1.10.1/bin/ChimeraX.exe'}
$taskProcess=Start-Process -FilePath $taskExecutable -ArgumentList @('--exit','--script',('"'+$CxcPath.Replace([char]92,[char]47)+'"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput ($LogPrefix+'.stdout.txt') -RedirectStandardError ($LogPrefix+'.stderr.txt')
if($taskProcess.ExitCode -ne 0){throw "ChimeraX退出码: $($taskProcess.ExitCode)，日志: $LogPrefix"}
