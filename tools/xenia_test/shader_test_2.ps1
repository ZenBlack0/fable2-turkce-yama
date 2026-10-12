. "$PSScriptRoot\shader_common.ps1"
Set-OneSetting -Key 'render_target_path_d3d12' -New '"rtv"' `
  -Why 'ROV yerine varsayilan RTV yolu: bozulma ROV yaziliminden mi geliyor ayirir. NOT: RTV''de altyazilar gorunmez (bilinen), yalniz bozulmaya bakin.' `
  -Watch 'Bozulma kayboluyorsa => ROV kaynakli (o zaman test 1 ile birlestirip ROV''da kalmanin bedeli degerlendirilir). Suruyorsa => ROV degil.'
