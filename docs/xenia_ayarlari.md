# Xenia Canary ayarları ve Fable II yamaları

Ayarlar `xenia-canary.config.toml` içindedir. **Xenia kapalıyken** düzenleyin (kapanırken dosyanın üzerine yazar). Kurucu (`Fable2_Turkce_Kurulum.exe`) bunları otomatik yapar, yalnızca config'de **var olan** anahtarları değiştirir ve zaman damgalı yedek alır.

| Bölüm | Ayar | Değer | Neden |
|---|---|---|---|
| `[GPU]` | `render_target_path_d3d12` | `"rov"` | Altyazılar için şart (aşağıda) |
| `[GPU]` | `framerate_limit` | `60` | GPU %99 sorunu (aşağıda) |
| `[GPU]` | `vsync` | `false` | Sınırlayıcıyla eşit aralıklı kareler; yırtılma görürseniz `true` deneyin |
| `[GPU]` | `async_shader_compilation` | `false` | Kısa görüntü bozulmalarını önler (aşağıda) |
| `[APU]` | `apu` / `use_dedicated_xma_thread` | `"xaudio2"` / `false` | Ses uyumu |
| `[Content]` | `license_mask` | `-1` | Lisanslı içerik (DLC) açık |
| `[General]` | `apply_patches` | `true` | Xenia oyun yamaları |

Oyun içi dil: **English (United Kingdom)**. Xenia config'inde `user_language` diye bir ayar yoktur.

## ROV ve altyazılar
Xenia'nın varsayılan Direct3D 12 render-target yolu (RTV) Fable II'nin altyazı katmanını **göstermez** — yamasız orijinal oyunda da aynıdır, çeviriyle ilgisi yoktur. `render_target_path_d3d12 = "rov"` (rasterizer-ordered views: piksel paketleme/blending yazılımla) ile altyazılar görünür. Doğrulama: orijinal oyun + varsayılan → altyazı yok; orijinal + ROV → İngilizce altyazı var; yamalı + ROV → Türkçe altyazı var. ROV bazı sistemlerde daha yavaştır ve nadiren görsel hata verebilir. Ayrıntı: [altyazi_arastirmasi.md](altyazi_arastirmasi.md).

## FPS sınırı
`framerate_limit = 0` kare hızını sınırsız bırakır ve GPU sürekli %99 çalışır. `framerate_limit = 60`, monitör 144 Hz olsa da kareleri 60'ta tutar (config açıklaması: "Maximum frames per second"). `vsync = true` 144 Hz'de 60'a eşit bölünmez ve düzensiz kare aralığı üretir; bu yüzden `false` bırakılıp sınırlayıcı kullanılır.

## Shader derlemesi
`async_shader_compilation = true` iken pipeline'lar arka planda oluşturulur; config açıklamasına göre "hazır olana kadar kısa süreli görüntü bozulması" olabilir. Haritanın bazı yerlerinde ekran görüntüsü alınamayacak kadar kısa bozulmalar vardı; ayar kapatılınca (`false`) kayboldu. Bedeli: **yeni bir bölgeye ilk girişte kısa donmalar** olabilir. `store_shaders = true` olduğu için oynadıkça shader önbelleği (`cache_host/shaders`) dolar ve donmalar azalır. Ayar değiştirince önbelleği silmek gerekmez.

## Xenia oyun yamaları (`patches/4D5307F1 - Fable II (GOTY_Platinum Edition).patch.toml`)
Kurucu dosyayı resmi `xenia-canary/game-patches` deposundan indirir (pakette bulunmaz) ve şunları açar:
- **Disable Texture Morphing:** kahraman/köpek dokularındaki bozulmayı giderir (makyaj hâlâ bozuk olabilir).
- **Disable MSAA (Margen67):** MSAA'yı kapatır, ROV'da performansı korur.
- **High Tick Rate (Guy):** oyun mantığı tick'ini 30 Hz'e çıkarır; arayüz akıcılığı ve girdi gecikmesi düzelir. GPU yüküne etkisi yoktur (CPU/simülasyon tarafı).

Diğer yamalar (60 FPS, çözünürlük, geniş ekran…) kapalı bırakılır.

## Shader bozulması teşhisi
`tools/xenia_test/shader_test_1..6.ps1` tek değişiklikli testlerdir (async derleme, RTV, yamalar, readback, bindless); `shader_restore.ps1` tabana döner. Bozulma "aynı yere ikinci girişte" kayboluyorsa shader'ın ilk kullanımıyla ilgilidir, aynen tekrarlıyorsa kalıcı bir render yolu (ROV/yama/readback) sorunudur.
