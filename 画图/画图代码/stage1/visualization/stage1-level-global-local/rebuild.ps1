# 从冻结 GT/CA2 与显式 level 原件重建五套案例, 不覆盖作者正式图集或个人会话. 
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
# project 是论文仓库; output 必须是它的全新 temp 子目录, 便于屏蔽旧运行. 
$project=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../../..')).Path
$output=[IO.Path]::GetFullPath($OutputDirectory)
$tempRoot=[IO.Path]::GetFullPath((Join-Path $project 'temp'))+[IO.Path]::DirectorySeparatorChar
if(-not $output.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $output)){throw '输出必须是本仓库 temp 中尚不存在的目录。'}
New-Item -ItemType Directory -Path $output | Out-Null
$previous=@{}
foreach($name in @('FIGURE_VERIFY_ROOT','FIGURE_BUILD_ROOT','FIGURE_SCENE_ROOT','PYTHONPATH','PYTHONDONTWRITEBYTECODE')){$previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
try {
    $env:FIGURE_VERIFY_ROOT=$project
    $env:FIGURE_BUILD_ROOT=$output
    $env:PYTHONPATH=Join-Path $project '转换工具/ops/rebuild_support'
    $env:PYTHONDONTWRITEBYTECODE='1'
    # shared 是旧病例继续共用的科学取数／MRC转换; 本轮只通过独立配置切换输入. 
    $shared=Join-Path $PSScriptRoot '../stage1-global-local'
    $cohort=Join-Path $project '画图/画图代码/stage1/output/stage1-results-revision/explicit_emdb_level/data/plot_data.json'
    & 'D:/Anaconda/python.exe' -X utf8 -B (Join-Path $PSScriptRoot 'screen_test_set.py') --output (Join-Path $output 'screening_all.json')
    if($LASTEXITCODE -ne 0){throw '完整测试集初筛失败。'}
    & 'D:/Anaconda/python.exe' -X utf8 -B (Join-Path $shared 'screen_cases.py') --sources (Join-Path $PSScriptRoot 'sources.json') --cohort $cohort --output (Join-Path $output 'screening')
    if($LASTEXITCODE -ne 0){throw '原始体素、交集或论文统计核对失败。'}
    & 'D:/Anaconda/python.exe' -X utf8 -B (Join-Path $shared 'prepare_assets.py') --sources (Join-Path $PSScriptRoot 'sources.json') --cases (Join-Path $PSScriptRoot 'cases.json') --screening (Join-Path $output 'screening') --output (Join-Path $output 'prepared')
    if($LASTEXITCODE -ne 0){throw '原生材料转换失败。'}
    & 'D:/Anaconda/python.exe' -X utf8 -B (Join-Path $PSScriptRoot 'make_scenes.py') --prepared (Join-Path $output 'prepared') --output (Join-Path $output 'scenes')
    if($LASTEXITCODE -ne 0){throw '原生命令或教程生成失败。'}
    foreach($case in (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'cases.json') -Raw -Encoding utf8 | ConvertFrom-Json)){
        $scene=(Join-Path $output ('scenes/'+$case.pdb)).Replace('\','/')
        $renderer=(Join-Path $PSScriptRoot 'render_native.py').Replace('\','/')
        $cxc=Join-Path $output ($case.pdb+'.cxc')
        # Windows PowerShell 5.1 的 UTF8 默认带 BOM; ChimeraX 原生命令文件需要无 BOM 的 UTF8. 
        [IO.File]::WriteAllText($cxc,('runscript "'+$renderer+'" "'+$scene+'"'+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))
        & (Join-Path $project '转换工具/ops/rebuild_support/run_chimerax.ps1') -CxcPath $cxc -LogPrefix (Join-Path $output $case.pdb)
        $report=Get-Content -LiteralPath (Join-Path $scene 'view_state.json') -Raw -Encoding utf8 | ConvertFrom-Json
        if(-not $report.success -or -not $report.old_temp_read_guard){throw ($case.pdb+'原生会话或旧temp屏蔽失败。')}
    }
    # Node 只装配本次原生图片和可编辑标注; 不读取已发布截图缓存.
    $env:FIGURE_SCENE_ROOT=Join-Path $output 'scenes'
    & 'C:/Users/15919/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' (Join-Path $PSScriptRoot 'build_deck.mjs')
    if($LASTEXITCODE -ne 0){throw '原生PPT装配或包/布局检查失败。'}
    Write-Output ('五套案例与六面板PPT已完整重建：'+$output)
} finally {
    foreach($name in $previous.Keys){[Environment]::SetEnvironmentVariable($name,$previous[$name],'Process')}
}
