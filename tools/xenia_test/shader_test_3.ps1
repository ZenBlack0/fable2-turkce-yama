. "$PSScriptRoot\shader_common.ps1"
Disable-Patch -Name 'Disable Texture Morphing' `
  -Why 'Yama kahraman/kopek doku morph''unu kapatiyor; kapatinca morph geri gelir ve kisa doku bozulmalari yama yan etkisi mi anlasilir.' `
  -Watch 'Bozulma kayboluyorsa => yama yan etkisi (ama kahraman/kopek dokulari bozuk gorunebilir, bu beklenen). Suruyorsa => yama degil.'
