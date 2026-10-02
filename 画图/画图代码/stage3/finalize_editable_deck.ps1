# 原备注直接取自用户修改过的 PPT；只把原图 9 的编号改为获准的图 8。
$paper = 'C:\Users\15919\Desktop\论文草稿'
$original = Join-Path $paper 'temp\stage3-deck-build\user-stage3-before-merge.pptx'
$draft = Join-Path $paper 'temp\stage3-deck-build\stage3-native-draft.pptx'
$candidate = Join-Path $paper 'temp\stage3-deck-build\stage3-optimized-candidate.pptx'
$names = @('stage3-official-tuned', 'stage3-find-hit-head-to-head')

$application = New-Object -ComObject PowerPoint.Application
$sourceDeck = $application.Presentations.Open($original, $false, $true, $false)
$deck = $application.Presentations.Open($draft, $false, $false, $false)
try {
    $sourceSlides = @(1, 3)
    for ($page = 1; $page -le $names.Count; $page++) {
        $originalNotes = $sourceDeck.Slides.Item($sourceSlides[$page - 1]).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text
        if ($page -eq 2) {
            $originalNotes = $originalNotes -replace '^图 9', '图 8'
        }
        $deck.Slides.Item($page).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = $originalNotes
        $deck.Slides.Item($page).Comments.Add(8, 8, 'Manuscript figure', 'MF', "@@$($names[$page - 1])") | Out-Null
    }
    $deck.SaveAs($candidate, 24)
}
finally {
    $deck.Close()
    $sourceDeck.Close()
    $application.Quit()
}
Write-Output $candidate
