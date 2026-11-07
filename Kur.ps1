[CmdletBinding()]
param([string]$OyunKlasoru = 'C:\Program Files\Epic Games\Flotsam')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Yama.ps1')
$paths = Get-VerifiedGamePaths $OyunKlasoru
$currentHash = Get-Sha256 $paths.Target
if ($currentHash -eq $script:TranslatedHash) {
    Write-Output 'Guncel Turkce yama zaten kurulu.'
    return
}
if ($currentHash -ne $script:OriginalHash) {
    throw 'Oyun dosyasi farkli bir surume ait veya baska bir yama kurulmus. Dosya degistirilmedi.'
}
$delta = Read-VerifiedDelta (Join-Path $PSScriptRoot 'patch\flotsam-tr-v1.0.0.json.gz')
if (Test-Path -LiteralPath $paths.Backup) {
    if ((Get-Item -LiteralPath $paths.Backup).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Yedek bir dosya baglantisi olamaz.' }
    if ((Get-Sha256 $paths.Backup) -ne $script:OriginalHash) { throw 'Mevcut yedek dogrulanamadi; uzerine yazilmadi.' }
} else {
    [IO.File]::Copy($paths.Target, $paths.Backup, $false)
}
$temporary = Join-Path $paths.DataDir ('resources.assets.flotsam-tr-' + [Guid]::NewGuid().ToString('N') + '.tmp')
try {
    Write-TranslatedFile $paths.Target $temporary $delta
    # File.Replace replaces the one verified game file atomically. Backup stays intact.
    [IO.File]::Replace($temporary, $paths.Target, [NullString]::Value)
    if ((Get-Sha256 $paths.Target) -ne $script:TranslatedHash) { throw 'Kurulum sonu dogrulamasi basarisiz.' }
} finally {
    if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) }
}
Write-Output 'Turkce yama kuruldu: 3197/3197 dil girdisi.'
Write-Output 'Oyunu Epic Games uzerinden acip Ayarlar > Dil > Turkce secin.'
Write-Output ('Orijinal dosya yedegi: ' + $paths.Backup)
