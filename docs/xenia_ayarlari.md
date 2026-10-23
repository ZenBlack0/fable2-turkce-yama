# Xenia Canary ayarları ve Fable II yamaları

Ayarlar `xenia-canary.config.toml` içindedir. **Xenia kapalıyken** düzenleyin (kapanırken dosyanın üzerine yazar).

**Kurucu yalnızca bir ayarı değiştirir ve yalnızca siz izin verirseniz; hangi Xenia'nın değiştirileceğine de siz karar verirsiniz:** bulunan bütün Xenia kurulumlarını listeler (tek bir tane bulsa bile değiştirmeden önce sorar: Evet / Başka klasör seç / Atla), seçmediğinize dokunmaz. Değişecek ayar: `[GPU] render_target_path_d3d12 = "rov"` (altyazılar için zorunlu). Dosyayı TOML kütüphanesiyle yeniden yazmaz; yalnızca o satırı metin olarak değiştirir (yorumlar, sıralama, kodlama ve satır sonları aynen kalır), önce `xenia-canary.config.toml.yedek-<tarih-saat>` yedeğini alır. Ayar zaten `"rov"` ise dosyaya yazmaz, yedek de almaz; dosya yoksa oluşturmaz; Xenia açıksa veya dosya salt okunursa değiştirmez. Satır yoksa `[GPU]` bölümünün altına ekler; bölüm yoksa dosyaya dokunmaz ve elle yapılacak adımı gösterir. `gpu` ayarı `d3d12` değilse yine değiştirir ama ayarın yalnızca D3D12'de etkili olduğunu belirtir. Başka ayar, oyun yaması (`patches`) veya önbellek (`cache_host`) kurucu tarafından değiştirilmez.

| Bölüm | Ayar | Değer | Kim yapar | Neden |
|---|---|---|---|---|
| `[GPU]` | `render_target_path_d3d12` | `"rov"` | kurucu (izinle) / elle | Altyazılar için şart (aşağıda) |
| `[GPU]` | `async_shader_compilation` | `false` | elle (isteğe bağlı) | Kısa görüntü bozulmalarını önler (aşağıda) |
| `[GPU]` | `framerate_limit` | `60` | elle (isteğe bağlı) | GPU %99 sorunu (aşağıda) |
| `[General]` | `apply_patches` | `true` | elle (isteğe bağlı) | Xenia oyun yamaları |

Oyun içi dil: **English (United Kingdom)**. Xenia config'inde `user_language` diye bir ayar yoktur.

## ROV ve altyazılar
Xenia'nın varsayılan Direct3D 12 render-target yolu (RTV) Fable II'nin altyazı katmanını **göstermez** — yamasız orijinal oyunda da aynıdır, çeviriyle ilgisi yoktur. `render_target_path_d3d12 = "rov"` (rasterizer-ordered views: piksel paketleme/blending yazılımla) ile altyazılar görünür. Doğrulama: orijinal oyun + varsayılan → altyazı yok; orijinal + ROV → İngilizce altyazı var; yamalı + ROV → Türkçe altyazı var. ROV bazı sistemlerde daha yavaştır ve nadiren görsel hata verebilir. Ayrıntı: [altyazi_arastirmasi.md](altyazi_arastirmasi.md).

## FPS sınırı
`framerate_limit = 0` kare hızını sınırsız bırakır ve GPU sürekli %99 çalışır. `framerate_limit = 60`, monitör 144 Hz olsa da kareleri 60'ta tutar (config açıklaması: "Maximum frames per second"). `vsync = true` 144 Hz'de 60'a eşit bölünmez ve düzensiz kare aralığı üretir; bu yüzden `vsync` `false` bırakılıp sınırlayıcı kullanılır (bu ayarlar isteğe bağlıdır ve kurucu tarafından yapılmaz).

## Shader derlemesi
`async_shader_compilation = true` iken pipeline'lar arka planda oluşturulur; config açıklamasına göre "hazır olana kadar kısa süreli görüntü bozulması" olabilir. Haritanın bazı yerlerinde ekran görüntüsü alınamayacak kadar kısa bozulmalar vardı; ayar kapatılınca (`false`) kayboldu. Bedeli: **yeni bir bölgeye ilk girişte kısa donmalar** olabilir. `store_shaders = true` olduğu için oynadıkça shader önbelleği (`cache_host/shaders`) dolar ve donmalar azalır. Ayar değiştirince önbelleği silmek gerekmez.

## Xenia oyun yamaları (isteğe bağlı; `patches/4D5307F1 - Fable II (GOTY_Platinum Edition).patch.toml`)
Kurucu bunları yapmaz (yama dosyasını indirmez, `patches` klasörüne yazmaz). Dosyayı resmî `xenia-canary/game-patches` deposundan kendiniz alıp Xenia'nın `patches` klasörüne koyabilir ve şu yamaları açabilirsiniz:
- **Disable Texture Morphing:** kahraman/köpek dokularındaki bozulmayı giderir (makyaj hâlâ bozuk olabilir).
- **Disable MSAA (Margen67):** MSAA'yı kapatır, ROV'da performansı korur.
- **High Tick Rate (Guy):** oyun mantığı tick'ini 30 Hz'e çıkarır; arayüz akıcılığı ve girdi gecikmesi düzelir. GPU yüküne etkisi yoktur (CPU/simülasyon tarafı).
- **High Tick Rate Stairs & Ledge Fix (Ultra):** High Tick Rate ile merdiven ve çıkıntılarda takılmayı önler.

"60 FPS" yaması deneysel olup varsayılan olarak kapalıdır; bu projede test edilmemiştir. Diğer yamalar (çözünürlük, geniş ekran…) kapalı bırakılır.

## Shader bozulması teşhisi
`tools/xenia_test/shader_test_1..6.ps1` tek değişiklikli testlerdir (async derleme, RTV, yamalar, readback, bindless); `shader_restore.ps1` tabana döner. Bozulma "aynı yere ikinci girişte" kayboluyorsa shader'ın ilk kullanımıyla ilgilidir, aynen tekrarlıyorsa kalıcı bir render yolu (ROV/yama/readback) sorunudur.

## v1.0.0–v1.0.2 kurucularının yaptıkları ve geri dönüş
Eski kurucu `xenia-canary.config.toml` içinde `gpu = "d3d12"`, `render_target_path_d3d12 = "rov"`, `vsync = false`, `framerate_limit = 60`, `async_shader_compilation = false`, `apu = "xaudio2"`, `use_dedicated_xma_thread = false`, `license_mask = -1` (ve gerekirse `mount_cache = true`, `apply_patches = true`) ayarlarını değiştirmiş, Fable II yama dosyasını `patches` klasörüne yazıp 3 yamayı açmış ve (izinle) `cache_host\shaders` içeriğini silmişti. Yedekler config'in bulunduğu Xenia klasöründe `xenia-canary.config.toml.yedek-<tarih-saat>` ve (o dosya zaten varsa) `patches\4D5307F1 - Fable II (GOTY_Platinum Edition).patch.toml.yedek-<tarih-saat>` adlarıyla durur; hangi ayarın eski değerden yeniye değiştiği kurulum klasöründeki `kurulum_raporu.txt` içindedir. Geri dönmek için Xenia kapalıyken yedeği asıl adının üstüne kopyalayın ya da config'i elle düzeltin.
