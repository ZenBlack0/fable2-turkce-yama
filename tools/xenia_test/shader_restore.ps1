. "$PSScriptRoot\shader_common.ps1"
Assert-XeniaClosed
if (-not (Test-Path $BaseCfg)) { Write-Host 'Taban yok; geri alinacak bir sey yok.'; exit 0 }
Copy-Item $BaseCfg $Cfg -Force; Copy-Item $BasePatch $Patch -Force
Write-Host 'Config ve yama dosyasi shader testleri oncesindeki tabana donduruldu.' -ForegroundColor Green
