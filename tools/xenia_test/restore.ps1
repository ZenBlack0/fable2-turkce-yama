. "$PSScriptRoot\common.ps1"
Assert-XeniaClosed
Restore-Config
Write-Host "Config yedekten geri yuklendi: $Cfg" -ForegroundColor Green
