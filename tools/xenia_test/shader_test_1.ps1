. "$PSScriptRoot\shader_common.ps1"
Set-OneSetting -Key 'async_shader_compilation' -New 'false' `
  -Why 'Esenkron derleme: pipeline hazir olana kadar cizim atlanir/eksik cizilir (config aciklamasi: "brief rendering artifacts"). Kapaliysa derleme senkron olur, takilma olur ama bozulma olmaz.' `
  -Watch 'Bozulma HIC yok ama bolgeye ilk giriste kisa donma varsa => neden esenkron derleme. Bozulma suruyorsa => neden derleme degil (testler 2-6).'
