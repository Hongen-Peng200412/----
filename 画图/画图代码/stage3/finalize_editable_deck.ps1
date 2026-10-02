$paper = 'C:\Users\15919\Desktop\论文草稿'
$source = Join-Path $paper 'temp\stage3-deck-build\stage3-native-draft.pptx'
$output = Join-Path $paper '画图\stage3结果图_可编辑.pptx'
$names = @('stage3-top1-full', 'stage3-best-full', 'stage3-find-hit-head-to-head')

$application = New-Object -ComObject PowerPoint.Application
$deck = $application.Presentations.Open($source, $false, $false, $false)
try {
    for ($page = 1; $page -le $names.Count; $page++) {
        $deck.Slides.Item($page).Comments.Add(8, 8, 'Manuscript figure', 'MF', "@@$($names[$page - 1])") | Out-Null
    }
    $deck.SaveAs($output, 24)
}
finally {
    $deck.Close()
    $application.Quit()
}
Write-Output $output
