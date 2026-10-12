# Altyazı araştırması (özet)

**Belirti:** Xenia Canary'de Fable II'nin altyazıları hiç görünmüyordu.

**Elenen nedenler**
- Yama/çeviri: yamasız orijinal oyunda da altyazı yoktu.
- Font ve glifler: Türkçe glifler altyazı fontunda da doğru çizilir.
- PT-BR projesiyle yapısal fark ve Xenia oyun yamaları (Disable Texture Morphing, Disable MSAA, High Tick Rate): etkisiz.
- Dil ayarı: Xenia config'inde `user_language` yoktur; oyun içi dil English (United Kingdom) olmalıdır.

**Neden:** Xenia'nın varsayılan Direct3D 12 render-target yolu (RTV) altyazı katmanını göstermiyordu.

**Çözüm:** `[GPU] render_target_path_d3d12 = "rov"`.

| Oyun | `render_target_path_d3d12` | Sonuç |
|---|---|---|
| Orijinal (yamasız) | varsayılan (RTV) | Altyazı yok |
| Orijinal | `"rov"` | İngilizce altyazı var |
| Yamalı | `"rov"` | Türkçe altyazı var, glifler doğru |

Tek değişkenli test düzeni için `tools/xenia_test/` betiklerine bakın. ROV bazı sistemlerde daha yavaş olabilir ve nadiren görsel hata verebilir; sorun olursa değeri `""` yapın (altyazılar kaybolur). Vulkan karşılığı (`render_target_path_vulkan = "fsi"`) denenmedi.
