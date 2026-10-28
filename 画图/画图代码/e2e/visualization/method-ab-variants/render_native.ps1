param([Parameter(Mandatory=$true)][string]$BuildRoot)
$ErrorActionPreference = 'Stop'
$taskBuild = [System.IO.Path]::GetFullPath($BuildRoot)
$taskRoot = $PSScriptRoot
while (-not (Test-Path -LiteralPath (Join-Path $taskRoot '论文草稿.md'))) {
    $taskParent = Split-Path -Parent $taskRoot
    if ($taskParent -eq $taskRoot) { throw '找不到论文工作区' }
    $taskRoot = $taskParent
}
$taskSource = Join-Path $taskRoot '画图\画图代码\e2e\output\method-ab-variants\source\author-20261028-deb03f10.pptx'
$taskCandidate = Join-Path $taskBuild 'candidate.pptx'
$taskRender = Join-Path $taskBuild 'render'
New-Item -ItemType Directory -Path $taskRender -Force | Out-Null
$taskPpt = New-Object -ComObject PowerPoint.Application
$taskReport = @()
foreach ($taskJob in @(@{Name='reference'; Path=$taskSource}, @{Name='candidate'; Path=$taskCandidate})) {
    $taskDeck = $null
    try {
        $taskDeck = $taskPpt.Presentations.Open($taskJob.Path,-1,0,0)
        for ($taskPage=1; $taskPage -le $taskDeck.Slides.Count; $taskPage++) {
            $taskImage = Join-Path $taskRender ($taskJob.Name + '-' + $taskPage + '.png')
            $taskDeck.Slides.Item($taskPage).Export($taskImage,'PNG',2400,1655)
            $taskReport += [pscustomobject]@{deck=$taskJob.Name; page=$taskPage; image=$taskImage; shapes=$taskDeck.Slides.Item($taskPage).Shapes.Count}
        }
    } finally {
        if ($null -ne $taskDeck) { $taskDeck.Close() }
    }
}
$taskReport | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskBuild 'native-render.json') -Encoding utf8
Write-Output ('PowerPoint rendered ' + $taskReport.Count + ' slides from read-only copies.')
