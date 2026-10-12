. "$PSScriptRoot\shader_common.ps1"
Set-OneSetting -Key 'd3d12_bindless' -New 'false' `
  -Why 'Bindless kaynak yolu surucu hatalarina duyarli olabilir; kapatinca klasik descriptor tablolari kullanilir (daha yavas olabilir).' `
  -Watch 'Bozulma kayboluyorsa => bindless/surucu kaynakli. Suruyorsa => bu degil.'
