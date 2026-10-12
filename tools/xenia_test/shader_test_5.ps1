. "$PSScriptRoot\shader_common.ps1"
Set-OneSetting -Key 'readback_resolve' -New '"fast"' `
  -Why 'Resolve (render-to-texture) sonuclari CPU''ya okunmuyor (none). Oyun bir hedefi sonraki karede dokuya cevirip kullanirken eksik veri kisa bozulma yapabilir; "fast" bir kare gecikmeyle okur.' `
  -Watch 'Bozulma azalir/kaybolursa => resolve/readback kaynakli. Kare hizi bir miktar duser (GPU yuku artar).'
