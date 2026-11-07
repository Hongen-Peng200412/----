# 在隐藏的独立ChimeraX进程中执行本次脚本，日志留在本次目录。
param([Parameter(Mandatory=$true)][string]$CxcPath,[Parameter(Mandatory=$true)][string]$LogPrefix)
$ErrorActionPreference='Stop'
$taskExecutable=if($env:FIGURE_CHIMERAX){$env:FIGURE_CHIMERAX}else{'D:/ChimeraX 1.10.1/bin/ChimeraX.exe'}
$taskSavedPythonPath=$env:PYTHONPATH
$taskSavedBytecode=$env:PYTHONDONTWRITEBYTECODE
try {
    # 原生软件使用其自身Python311依赖, 不继承统计程序的cp312运行包.
    $env:PYTHONPATH=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../figure_runner/guards'))
    $env:PYTHONDONTWRITEBYTECODE='1'
    $taskProcess=Start-Process -FilePath $taskExecutable -ArgumentList @('--exit','--script',('"'+$CxcPath.Replace([char]92,[char]47)+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput ($LogPrefix+'.stdout.txt') -RedirectStandardError ($LogPrefix+'.stderr.txt')
    # Windows PowerShell 5.1须在等待前保留原生句柄, 才能在退出后可靠读取ExitCode.
    $taskNativeHandle=$taskProcess.Handle
    $taskTimeoutSeconds=if($env:FIGURE_NATIVE_TIMEOUT_SECONDS){[int]$env:FIGURE_NATIVE_TIMEOUT_SECONDS}else{600}
    if (-not $taskProcess.WaitForExit($taskTimeoutSeconds*1000)) {
        # 仅结束本工具刚创建并持有句柄的进程, 不按进程名查杀作者窗口.
        $taskProcess.Kill()
        throw "本次独立ChimeraX进程超时, 保留现场: $LogPrefix"
    }
    $taskProcess.WaitForExit()
} finally {
    $env:PYTHONPATH=$taskSavedPythonPath
    $env:PYTHONDONTWRITEBYTECODE=$taskSavedBytecode
}
if($taskProcess.ExitCode -ne 0){throw "ChimeraX退出码: $($taskProcess.ExitCode)，日志: $LogPrefix"}
