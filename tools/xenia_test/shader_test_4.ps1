. "$PSScriptRoot\shader_common.ps1"
Disable-Patch -Name 'Disable MSAA' `
  -Why 'MSAA kapatma yamasi MSAA render hedefi yollarini degistirir; kapatinca oyun MSAA kullanir (ROV''da agirdir, kare dusebilir).' `
  -Watch 'Bozulma kayboluyorsa => MSAA yamasi/ROV etkilesimi. Kare hizi dusmesi beklenen; sadece bozulmaya bakin.'
