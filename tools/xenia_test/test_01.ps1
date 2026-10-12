. "$PSScriptRoot\common.ps1"
Set-OneSetting -Key "render_target_path_d3d12" -New '"rov"' -Why "Altyazi/UI metni ozel blending ve render-target kopyalamasiyla ciziliyorsa RTV yolunun dusuk dogrulugu gorunmez yapabilir; ROV tum piksel formatlarini yazilimda isler (en yuksek dogruluk)."
