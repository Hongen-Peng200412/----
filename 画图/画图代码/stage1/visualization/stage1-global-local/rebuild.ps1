# 从长期冻结输入重建筛选、素材、普通会话和预览；所有新产物写入指定的新 temp 目录。
# 不更新正式 PPT、稿件、既有初始化会话或作者 my_sessions。
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$taskProject=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../../..')).Path
$taskOutput=[System.IO.Path]::GetFullPath($OutputDirectory)
$taskTemp=[System.IO.Path]::GetFullPath((Join-Path $taskProject 'temp'))+[System.IO.Path]::DirectorySeparatorChar
if(-not $taskOutput.StartsWith($taskTemp,[System.StringComparison]::OrdinalIgnoreCase)) {
    throw '重建输出必须位于本仓库 temp 下。'
}
if(Test-Path -LiteralPath $taskOutput) { throw '请指定尚不存在的输出目录，保留已有运行和作者会话。' }
New-Item -ItemType Directory -Path $taskOutput | Out-Null
$taskPreviousEnvironment=@{}
foreach($taskVariable in @('FIGURE_VERIFY_ROOT','FIGURE_BUILD_ROOT','PYTHONPATH','PYTHONDONTWRITEBYTECODE')) {
    $taskPreviousEnvironment[$taskVariable]=[System.Environment]::GetEnvironmentVariable($taskVariable,'Process')
}
try {
$env:FIGURE_VERIFY_ROOT=$taskProject
$env:FIGURE_BUILD_ROOT=$taskOutput
$env:PYTHONPATH=(Join-Path $taskProject '转换工具/ops/rebuild_support')
$env:PYTHONDONTWRITEBYTECODE='1'
$taskPython='D:/Anaconda/python.exe'
& $taskPython -X utf8 -B (Join-Path $PSScriptRoot 'screen_cases.py') --output (Join-Path $taskOutput 'screening')
if($LASTEXITCODE -ne 0) { throw '病例筛选失败。' }
& $taskPython -X utf8 -B (Join-Path $PSScriptRoot 'prepare_assets.py') --screening (Join-Path $taskOutput 'screening') --output (Join-Path $taskOutput 'prepared')
if($LASTEXITCODE -ne 0) { throw '本地素材生成失败。' }
$taskRender=(Join-Path $PSScriptRoot 'render_scene.py').Replace('\','/')
$taskPrepared=(Join-Path $taskOutput 'prepared').Replace('\','/')
foreach($taskCase in (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cases.json') -Raw -Encoding UTF8 | ConvertFrom-Json)) {
    $taskPdb=$taskCase.pdb
    $taskScene=(Join-Path $taskOutput ('scenes/'+$taskPdb)).Replace('\','/')
    $taskCxc=Join-Path $taskOutput ($taskPdb+'.cxc')
    'runscript "'+$taskRender+'" "'+$taskPrepared+'" '+$taskPdb+' "'+$taskScene+'"' | Set-Content -LiteralPath $taskCxc -Encoding UTF8
    & (Join-Path $taskProject '转换工具/ops/rebuild_support/run_chimerax.ps1') -CxcPath $taskCxc -LogPrefix (Join-Path $taskOutput ($taskPdb+'_render'))
    $taskReport=Get-Content -LiteralPath (Join-Path $taskScene 'report.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if(-not $taskReport.success -or -not $taskReport.old_temp_read_guard) { throw ($taskPdb+' 原生渲染或旧 temp 屏蔽失败，请看 report.json。') }
}
Write-Output ('完成：'+$taskOutput)
} finally {
    foreach($taskVariable in $taskPreviousEnvironment.Keys) {
        [System.Environment]::SetEnvironmentVariable($taskVariable,$taskPreviousEnvironment[$taskVariable],'Process')
    }
}
