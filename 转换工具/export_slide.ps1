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
try {
    $application = New-Object -ComObject PowerPoint.Application
    $presentation = $application.Presentations.Open($DeckPath, -1, 0, 0)
    $heightPx = [int][Math]::Round($WidthPx * $presentation.PageSetup.SlideHeight / $presentation.PageSetup.SlideWidth)
    $presentation.Slides.Item($SlideNumber).Export($OutputPath, 'PNG', $WidthPx, $heightPx)
} finally {
    if ($null -ne $presentation) { $presentation.Close() }
    if ($null -ne $application -and -not $runningBefore) { $application.Quit() }
}
