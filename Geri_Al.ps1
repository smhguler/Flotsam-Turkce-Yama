[CmdletBinding()]
param([string]$OyunKlasoru = 'C:\Program Files\Epic Games\Flotsam')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Yama.ps1')
$paths = Get-VerifiedGamePaths $OyunKlasoru
$currentHash = Get-Sha256 $paths.Target
if ($currentHash -eq $script:OriginalHash) { Write-Output 'Orijinal dosya zaten yuklu.'; return }
if ($currentHash -ne $script:TranslatedHash) { throw 'Oyun dosyasi sonradan degismis; uzerine yazilmadi.' }
if (!(Test-Path -LiteralPath $paths.Backup -PathType Leaf)) { throw 'Bu kurulumun orijinal dosya yedegi bulunamadi.' }
if ((Get-Item -LiteralPath $paths.Backup).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Yedek bir dosya baglantisi olamaz.' }
if ((Get-Sha256 $paths.Backup) -ne $script:OriginalHash) { throw 'Orijinal dosya yedegi dogrulanamadi.' }
$temporary = Join-Path $paths.DataDir ('resources.assets.flotsam-restore-' + [Guid]::NewGuid().ToString('N') + '.tmp')
try {
    [IO.File]::Copy($paths.Backup, $temporary, $false)
    [IO.File]::Replace($temporary, $paths.Target, [NullString]::Value)
    if ((Get-Sha256 $paths.Target) -ne $script:OriginalHash) { throw 'Geri yukleme dogrulamasi basarisiz.' }
} finally {
    if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
}
Write-Output 'Orijinal oyun dosyasi geri yuklendi. Yedek korundu.'
