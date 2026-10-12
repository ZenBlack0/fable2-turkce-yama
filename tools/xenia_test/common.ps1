# Ortak yardimci: yedekten geri yukler, TEK satiri degistirir ve eski -> yeni degeri yazar.
$XeniaDir = if ($env:XENIA_DIR) { $env:XENIA_DIR } else { 'C:\xenia_canary_windows' }  # kendi Xenia klasorunuz: $env:XENIA_DIR
$Cfg = Join-Path $XeniaDir 'xenia-canary.config.toml'
$Bak = "$Cfg.bak"

function Assert-XeniaClosed {
    if (Get-Process -Name 'xenia_canary' -ErrorAction SilentlyContinue) {
        Write-Host '[HATA] Xenia acik. Kapatip tekrar calistirin (kapanirken config uzerine yazar).' -ForegroundColor Red
        exit 1
    }
}

function Restore-Config {
    if (-not (Test-Path $Bak)) { Write-Host "[HATA] Yedek yok: $Bak" -ForegroundColor Red; exit 1 }
    Copy-Item $Bak $Cfg -Force
}

# $Key: ayar adi (satir basinda), $New: yeni deger metni (TOML, ornegin '"rov"' ya da 'false')
function Set-OneSetting([string]$Key, [string]$New, [string]$Why) {
    Assert-XeniaClosed
    Restore-Config
    $lines = Get-Content $Cfg -Encoding UTF8
    $idx = @(0..($lines.Count - 1) | Where-Object { $lines[$_] -match ('^' + [regex]::Escape($Key) + '\s*=') })
    if ($idx.Count -ne 1) { Write-Host "[HATA] '$Key' satiri $($idx.Count) kez bulundu (1 bekleniyordu). Degisiklik yapilmadi." -ForegroundColor Red; exit 1 }
    $i = $idx[0]
    $m = [regex]::Match($lines[$i], '^(' + [regex]::Escape($Key) + '\s*=\s*)(\S+)(.*)$')
    $old = $m.Groups[2].Value
    $lines[$i] = $m.Groups[1].Value + $New + $m.Groups[3].Value
    [IO.File]::WriteAllLines($Cfg, $lines, (New-Object Text.UTF8Encoding $false))
    Write-Host "Degisen ayar : $Key" -ForegroundColor Green
    Write-Host "Eski -> yeni : $old -> $New"
    Write-Host "Neden        : $Why"
    Write-Host 'Simdi Xenia''yi acin, yeni oyun / Rose & Barnum sahnesi, Subtitles = On. Sonra Xenia''yi kapatin.'
    Write-Host 'Diger ayarlar yedekteki (orijinal) degerlerinde; geri almak icin restore.ps1'
}
