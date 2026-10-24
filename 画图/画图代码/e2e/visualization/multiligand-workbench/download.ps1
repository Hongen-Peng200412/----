<# 读取明确清单, 续传原服务器文件到 D 盘; 不删除任何本地或远端文件. #>
param([string]$Manifest, [string]$DataRoot)
$ErrorActionPreference = 'Stop'
$msys = @($env:PROJECT_MSYS_ROOT, $env:MSYS2_ROOT, 'C:\msys64', 'D:\msys64') | Where-Object { $_ -and (Test-Path (Join-Path $_ 'usr\bin\rsync.exe')) } | Select-Object -First 1
if (-not $msys) { throw '没有找到 MSYS2 rsync' }
$bin = Join-Path $msys 'usr\bin'
$items = Get-Content -LiteralPath $Manifest -Encoding UTF8 -Raw | ConvertFrom-Json
$root = [System.IO.Path]::GetFullPath($DataRoot)
$repo = (Get-Item -LiteralPath $PSScriptRoot).Parent.Parent.Parent.Parent.Parent.FullName
$scratch = Join-Path $repo 'temp\multiligand-workbench\transfer'
New-Item -ItemType Directory -Force -Path $root,$scratch | Out-Null
$listPath = Join-Path $scratch 'rsync-files.txt'
$relativeRemote = @($items | ForEach-Object { $_.remote.TrimStart('/') })
[System.IO.File]::WriteAllText($listPath, ($relativeRemote -join "`n") + "`n", (New-Object System.Text.UTF8Encoding($false)))
$cygpath = Join-Path $bin 'cygpath.exe'
$listPosix = (& $cygpath -u $listPath).Trim()
$cache = Join-Path $root '_server'
New-Item -ItemType Directory -Force -Path $cache | Out-Null
$cachePosix = (& $cygpath -u $cache).Trim()
$passwordPosix = (& $cygpath -u (Join-Path $env:USERPROFILE '.ssh\pocket_plus_sshpass.txt')).Trim()
$knownPosix = (& $cygpath -u (Join-Path $env:USERPROFILE '.ssh\known_hosts')).Trim()
$remoteShell = "sshpass -f $passwordPosix ssh -p 10022 -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$knownPosix -o WarnWeakCrypto=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -o NumberOfPasswordPrompts=1"
$env:MSYS2_ARG_CONV_EXCL = '*'
$env:Path = "$bin;$env:Path"
& (Join-Path $bin 'rsync.exe') -rltz --partial --append-verify --info=progress2 --files-from=$listPosix -e $remoteShell 'penghongen@10.102.33.220:/' "$cachePosix/"
if ($LASTEXITCODE -ne 0) { throw "rsync 下载失败: $LASTEXITCODE" }
# 用硬链接连接唯一服务器缓存与逐案例清单, 大地图不在磁盘复制两遍. 同一 D 盘支持 NTFS 硬链接.
foreach ($item in $items) {
    $source = Join-Path $cache ($item.remote.TrimStart('/') -replace '/', '\')
    $destination = Join-Path $root ($item.local -replace '/', '\')
    New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
    if (-not (Test-Path -LiteralPath $destination)) { New-Item -ItemType HardLink -Path $destination -Target $source | Out-Null }
}
Write-Output "Downloaded/linked $($items.Count) source files into $root"
