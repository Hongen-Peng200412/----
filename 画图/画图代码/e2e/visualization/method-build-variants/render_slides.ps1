param([Parameter(Mandatory=$true)][string]$BuildRoot)
$ErrorActionPreference='Stop'
$taskBuild=[System.IO.Path]::GetFullPath($BuildRoot)
$taskRoot=$PSScriptRoot
while(-not(Test-Path -LiteralPath (Join-Path $taskRoot '论文草稿.md'))){$taskRoot=Split-Path -Parent $taskRoot}
$taskSource=Join-Path $taskRoot '画图\画图代码\e2e\output\method-build-variants\source\author-20261028-ce373d2e.pptx'
$taskRender=Join-Path $taskBuild 'slides'
New-Item -ItemType Directory -Path $taskRender -Force | Out-Null
$taskPpt=New-Object -ComObject PowerPoint.Application
$taskRows=@()
foreach($taskJob in @(@{Name='source';Path=$taskSource},@{Name='candidate';Path=(Join-Path $taskBuild 'candidate.pptx')})){
    $taskDeck=$null
    try{
        $taskDeck=$taskPpt.Presentations.Open($taskJob.Path,-1,0,0)
        for($taskPage=1;$taskPage -le $taskDeck.Slides.Count;$taskPage++){
            $taskImage=Join-Path $taskRender ($taskJob.Name+'-'+$taskPage+'.png')
            $taskDeck.Slides.Item($taskPage).Export($taskImage,'PNG',2400,1655)
            $taskRows+=[pscustomobject]@{deck=$taskJob.Name;page=$taskPage;image=$taskImage;shapes=$taskDeck.Slides.Item($taskPage).Shapes.Count}
        }
    }finally{if($null -ne $taskDeck){$taskDeck.Close()}}
}
$taskRows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskBuild 'native_slides.json') -Encoding utf8
Write-Output 'PowerPoint exported original 5 and candidate 9 pages from read-only files.'
