param(
    [Parameter(Mandatory = $true)][string]$DeckPath,
    [Parameter(Mandatory = $true)][int]$SlideNumber,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [Parameter(Mandatory = $true)][int]$WidthPx
)

$ErrorActionPreference = 'Stop'
$runningBefore = [bool](Get-Process -Name POWERPNT -ErrorAction SilentlyContinue)
$application = $null
$presentation = $null
$exportError = $null
$closeError = $null
$quitError = $null
try {
    $application = New-Object -ComObject PowerPoint.Application
    $presentation = $application.Presentations.Open($DeckPath, -1, 0, 0)
    $heightPx = [int][Math]::Round($WidthPx * $presentation.PageSetup.SlideHeight / $presentation.PageSetup.SlideWidth)
    $presentation.Slides.Item($SlideNumber).Export($OutputPath, 'PNG', $WidthPx, $heightPx)
    $exportedFile = Get-Item -LiteralPath $OutputPath -ErrorAction Stop
    if ($exportedFile.Length -le 0) {
        throw "PowerPoint did not write a non-empty PNG for slide $SlideNumber."
    }
} catch {
    $exportError = $_
} finally {
    if ($null -ne $presentation) {
        try { $presentation.Close() } catch { $closeError = $_ }
    }
    if ($null -ne $application -and -not $runningBefore) {
        try { $application.Quit() } catch { $quitError = $_ }
    }
}
if ($null -ne $closeError) { Write-Warning "PowerPoint presentation cleanup failed: $($closeError.Exception.Message)" }
if ($null -ne $quitError) { Write-Warning "PowerPoint application cleanup failed: $($quitError.Exception.Message)" }
if ($null -ne $exportError) { throw $exportError }
