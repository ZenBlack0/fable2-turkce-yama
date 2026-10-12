# Shader bozulma testleri icin ortak yardimci. Her test TEK degisiklik yapar; taban = ilk calistirmada alinan yedek.
# Taban: config + Fable II yama dosyasi (framerate_limit=60 dahil guncel hali). Geri almak icin shader_restore.ps1.
$XeniaDir = if ($env:XENIA_DIR) { $env:XENIA_DIR } else { 'C:\xenia_canary_windows' }  # kendi Xenia klasorunuz: $env:XENIA_DIR
$Cfg   = Join-Path $XeniaDir 'xenia-canary.config.toml'
$Patch = Join-Path $XeniaDir 'patches\4D5307F1 - Fable II (GOTY_Platinum Edition).patch.toml'
$BaseCfg   = "$Cfg.shader_taban"
$BasePatch = "$Patch.shader_taban"

function Assert-XeniaClosed {
    if (Get-Process -Name 'xenia_canary' -ErrorAction SilentlyContinue) {
        Write-Host '[HATA] Xenia acik. Kapatip tekrar calistirin.' -ForegroundColor Red; exit 1 }
}
function Restore-Base {
    Assert-XeniaClosed
    if (-not (Test-Path $BaseCfg))   { Copy-Item $Cfg $BaseCfg;     Write-Host "Taban config alindi: $BaseCfg" }
    if (-not (Test-Path $BasePatch)) { Copy-Item $Patch $BasePatch; Write-Host "Taban yama alindi : $BasePatch" }
    Copy-Item $BaseCfg $Cfg -Force; Copy-Item $BasePatch $Patch -Force
}
function Write-Lines($path, $lines) { [IO.File]::WriteAllLines($path, $lines, (New-Object Text.UTF8Encoding $false)) }

function Set-OneSetting([string]$Key, [string]$New, [string]$Why, [string]$Watch) {
    Restore-Base
    $lines = Get-Content $Cfg -Encoding UTF8
    $idx = @(0..($lines.Count - 1) | Where-Object { $lines[$_] -match ('^' + [regex]::Escape($Key) + '\s*=') })
    if ($idx.Count -ne 1) { Write-Host "[HATA] '$Key' $($idx.Count) kez bulundu." -ForegroundColor Red; exit 1 }
    $m = [regex]::Match($lines[$idx[0]], '^(' + [regex]::Escape($Key) + '\s*=\s*)(\S+)(.*)$')
    $lines[$idx[0]] = $m.Groups[1].Value + $New + $m.Groups[3].Value
    Write-Lines $Cfg $lines
    Write-Host "Degisen ayar : $Key  ($($m.Groups[2].Value) -> $New)" -ForegroundColor Green
    Show-Info $Why $Watch
}
# Yama adini (name = "...") bulup hemen altindaki ilk is_enabled satirini false yapar
function Disable-Patch([string]$Name, [string]$Why, [string]$Watch) {
    Restore-Base
    $lines = Get-Content $Patch -Encoding UTF8
    $n = -1
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match ('name = "' + [regex]::Escape($Name))) { $n = $i; break } }
    if ($n -lt 0) { Write-Host "[HATA] Yama bulunamadi: $Name" -ForegroundColor Red; exit 1 }
    for ($j = $n; $j -lt $n + 6; $j++) { if ($lines[$j] -match 'is_enabled = true') { $lines[$j] = $lines[$j] -replace 'true', 'false'; break } }
    Write-Lines $Patch $lines
    Write-Host "Kapatilan yama: $Name" -ForegroundColor Green
    Show-Info $Why $Watch
}
function Show-Info($Why, $Watch) {
    Write-Host "Neden        : $Why"
    Write-Host "Gozlem       : $Watch" -ForegroundColor Yellow
    Write-Host 'Yontem: ayni bolgeye ayni yoldan gidin, Oyun Cubugu (Win+Alt+R) ile kaydedin. Digerleri tabanda; geri almak icin shader_restore.ps1.'
}
