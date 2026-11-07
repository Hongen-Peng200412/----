param(
    [Parameter(Mandatory = $true)][string]$ReferencePath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$name = [System.IO.Path]::GetFileName($ReferencePath)
$application = [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
$documents = @($application.Documents | Where-Object { $_.Name -ieq $name })
$exact = @($documents | Where-Object { $_.FullName -ieq $ReferencePath })
if ($exact.Count -eq 1) {
    $document = $exact[0]
} elseif ($documents.Count -eq 1) {
    # OneDrive may expose the same local document through a cloud URL.
    $document = $documents[0]
} else {
    throw "Cannot uniquely locate the open Word document $name ($($documents.Count) matches)."
}
[System.IO.File]::WriteAllText(
    $OutputPath,
    $document.WordOpenXML,
    (New-Object System.Text.UTF8Encoding($false))
)
