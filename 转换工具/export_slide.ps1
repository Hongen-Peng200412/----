param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [Parameter(Mandatory = $true)][int]$WidthPx
)

$ErrorActionPreference = 'Stop'
$decks = ConvertFrom-Json -InputObject (Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8)
$application = $null
$presentation = $null
$exportError = $null
$closeError = $null
try {
    $application = New-Object -ComObject PowerPoint.Application
    foreach ($deck in $decks) {
        $pending = @($deck.slides | Where-Object {
            -not (Test-Path -LiteralPath $_.output -PathType Leaf) -or
            (Get-Item -LiteralPath $_.output).Length -le 0
        })
        if ($pending.Count -eq 0) { continue }
        $presentation = $application.Presentations.Open([string]$deck.path, -1, 0, 0)
        $heightPx = [int][Math]::Round($WidthPx * $presentation.PageSetup.SlideHeight / $presentation.PageSetup.SlideWidth)
        foreach ($slide in $pending) {
            $presentation.Slides.Item([int]$slide.page).Export([string]$slide.output, 'PNG', $WidthPx, $heightPx)
            $exportedFile = Get-Item -LiteralPath $slide.output -ErrorAction Stop
            if ($exportedFile.Length -le 0) {
                throw "PowerPoint did not write a non-empty PNG for slide $($slide.page) in $($deck.path)."
            }
        }
        try { $presentation.Close() } catch { $closeError = $_ }
        $presentation = $null
    }
} catch {
    $exportError = $_
} finally {
    if ($null -ne $presentation) {
        try { $presentation.Close() } catch { $closeError = $_ }
    }
}
if ($null -ne $closeError) { Write-Warning "PowerPoint presentation cleanup failed: $($closeError.Exception.Message)" }
if ($null -ne $exportError) { throw $exportError }
