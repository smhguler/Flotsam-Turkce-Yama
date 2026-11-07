# Shared patch routines. Windows PowerShell 5.1 and PowerShell 7 compatible.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:OriginalHash = '2B8ED949FB1ADA4D4F4AF2B1DC10DB9BD24DF987826D0780600CC566D1170F71'
$script:TranslatedHash = '00CAFA58ABB6DCA798FFC16207143BC8985BE06B5814DEE48224A40F2F57F935'
$script:DeltaHash = '79EF7D9377AD16AEABC48AC9AC1879F7BC4D03B2D54AEF47397F5B58AC967808'

function Get-VerifiedGamePaths {
    param([Parameter(Mandatory = $true)][string]$Root)
    $resolved = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).ProviderPath
    $gameExe = Join-Path $resolved 'Flotsam.exe'
    $dataDir = Join-Path $resolved 'Flotsam_Data'
    $target = Join-Path $dataDir 'resources.assets'
    if (!(Test-Path -LiteralPath $gameExe -PathType Leaf) -or !(Test-Path -LiteralPath $target -PathType Leaf)) {
        throw 'Bu klasorde Flotsam.exe ve Flotsam_Data\resources.assets bulunamadi.'
    }
    foreach ($path in @($dataDir, $target)) {
        if (((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Baglanti yerine oyunun gercek dosya konumunu secin.'
        }
    }
    if (Get-Process -Name Flotsam -ErrorAction SilentlyContinue) {
        throw 'Once oyunu kaydedip normal sekilde kapatin.'
    }
    return @{ Target = $target; DataDir = $dataDir; Backup = (Join-Path $dataDir 'resources.assets.flotsam-tr.bak') }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Read-VerifiedDelta {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ((Get-Item -LiteralPath $Path).Length -gt 2MB -or (Get-Sha256 $Path) -ne $script:DeltaHash) {
        throw 'Yama dosyasi eksik veya degistirilmis. Resmi depo paketini yeniden indirin.'
    }
    $file = [IO.File]::OpenRead($Path)
    $gzip = $null
    $reader = $null
    try {
        $gzip = New-Object IO.Compression.GZipStream($file, [IO.Compression.CompressionMode]::Decompress)
        $reader = New-Object IO.StreamReader($gzip, [Text.Encoding]::UTF8)
        $json = $reader.ReadToEnd()
        if ($json.Length -gt 8MB) { throw 'Yama verisi izin verilen boyutu asiyor.' }
        $delta = $json | ConvertFrom-Json
        if ($delta.format -ne 'flotsam-delta-v1' -or $delta.source_sha256 -ne $script:OriginalHash -or $delta.target_sha256 -ne $script:TranslatedHash) {
            throw 'Bu yama desteklenen surume ait degil.'
        }
        if ($delta.source_size -ne 57332536 -or $delta.target_size -ne 57403448 -or $delta.operations.Count -gt 100000) {
            throw 'Yama boyut bilgisi gecersiz.'
        }
        return $delta
    } finally {
        if ($null -ne $reader) { $reader.Dispose() }
        elseif ($null -ne $gzip) { $gzip.Dispose() }
        $file.Dispose()
    }
}

function Write-TranslatedFile {
    param([string]$Source, [string]$Destination, $Delta)
    $inputStream = [IO.File]::Open($Source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    $outputStream = $null
    try {
        if ($inputStream.Length -ne $Delta.source_size -or (Get-Sha256 $Source) -ne $script:OriginalHash) {
            throw 'Orijinal oyun dosyasi desteklenen surumle eslesmiyor.'
        }
        $outputStream = [IO.File]::Open($Destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $buffer = New-Object byte[] 81920
        foreach ($op in $Delta.operations) {
            if ($op[0] -eq 0 -and $op.Count -eq 3) {
                [long]$offset = $op[1]
                [long]$remaining = $op[2]
                if ($offset -lt 0 -or $offset -gt $inputStream.Length -or $remaining -lt 0 -or $remaining -gt ($inputStream.Length - $offset)) {
                    throw 'Gecersiz kaynak araligi.'
                }
                if ($remaining -gt ($Delta.target_size - $outputStream.Length)) { throw 'Cikti boyutu asildi.' }
                $inputStream.Position = $offset
                while ($remaining -gt 0) {
                    $count = [int][Math]::Min($remaining, $buffer.Length)
                    $read = $inputStream.Read($buffer, 0, $count)
                    if ($read -eq 0) { throw 'Kaynak dosya beklenmedik yerde sona erdi.' }
                    $outputStream.Write($buffer, 0, $read)
                    $remaining -= $read
                }
            } elseif ($op[0] -eq 1 -and $op.Count -eq 2) {
                $bytes = [Convert]::FromBase64String([string]$op[1])
                if ($bytes.Length -gt ($Delta.target_size - $outputStream.Length)) { throw 'Cikti boyutu asildi.' }
                $outputStream.Write($bytes, 0, $bytes.Length)
            } else {
                throw 'Gecersiz yama islemi.'
            }
        }
        if ($outputStream.Length -ne $Delta.target_size) { throw 'Cikti boyutu dogrulanamadi.' }
        $outputStream.Flush()
    } finally {
        if ($null -ne $outputStream) { $outputStream.Dispose() }
        $inputStream.Dispose()
    }
    if ((Get-Sha256 $Destination) -ne $script:TranslatedHash) { throw 'Olusturulan Turkce dosya dogrulanamadi.' }
}
