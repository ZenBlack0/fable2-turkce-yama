# Lionhead `.bft` yazı tipi biçimi (Fable II, Xbox 360)

Çözümleme: `tools/bft.py` (okuma/yazma, `Bft` sınıfı). Tüm değerler **big-endian**. 6 dosya:
`data/language/en-uk/fonts/gui_small|gui_normal|gui_large.bft`, `data/language/fonts/couriernew_16|timesnewroman_10|timesnewroman_16.bft`.
`cs/hu/pl/sk` dilleri de en-uk fontunu kullanır (kendi font klasörleri yok).

## Dosya düzeni
| Bölüm | Boyut | İçerik |
|---|---|---|
| Başlık | 25 B | `u32 sürüm=1`, `u32 satır yüksekliği` (27/24/32/21/13/16), `u32 (400 veya 100, kullanılmıyor)`, `u32 0`, `u8 ?`, `u32 ?`, **`u32 glif sayısı`** (@0x15; gui için 307, tnr/courier için 291) |
| Glif kayıtları | N × 22 B | `f32 u0, v0, u1, v1` (doku koordinatı = piksel/(boyut−1)), `u16 xoffset, u16 genişlik (kutu), u16 ilerleme (advance)` |
| Kod→glif tablosu | 2×(2+0x2123) B | `u16 ilk=0`, `u16 son=0x2123`, ardından kod noktası 0…0x2122 için `u16 glif indeksi`; boş = `0x3434` (gui) / `0x2424` (tnr/courier). Giriş = `tablo[kod+2]` |
| Doku başlığı | 88 B | Xbox 360 doku sabiti; `u32 @+16 = genişlik`, `u32 @+20 = yükseklik` (512×256, gui_large 512×512, tnr_10 256×128, courier 256×256) |
| Doku | G×Y/2 B | **BC4 / DXT5A** (4×4 blok başına 8 bayt, tek kanal = alfa), **Xbox 360 tiled** (blok birimi, 2D macro/micro swizzle) ve **16-bit byte-swap** |

* Her glif kutusu satır yüksekliği kadar uzundur (tüm glifler aynı üst satırdan başlar; dikey konum kutu içinde pişmiştir). Kutular atlasta `satır_yüksekliği+1` aralıklı satırlara dizilir; kutular arası 1–2 px boşluk bırakılır.
* Glif kaydı alanları: `xoffset` sol boşluk, ikinci alan kutu genişliği, üçüncü alan imleç ilerlemesi (ör. `s` = 1,5,6).
* Tiled adres: Xenia/UModel formülü (`tools/bft.py::_tiled_offset`, `log2(bpp)=3`).
* BC4: `a0,a1` + 16×3 bit indeks (little-endian bit sırası). `a0>a1` → 8 seviye, aksi halde 6 seviye + 0 + 255.
* Geri-yazım doğrulaması: değiştirilmemiş dosya `Bft(...).to_bytes()` ile **bayt bayt aynı** çıkar.

## Orijinal glif kapsamı
Latin-1 + Latin Ek-A'nın Çekçe/Lehçe/Macarca/Slovakça için gereken kısmı (Č č Ď ď Ę ę Ě ě Ł ł Ń ń Ň ň Ő ő Ř ř Ś ś Š š Ť ť Ů ů Ű ű Ź ź Ż ż Ž ž, Ć ć, Ą ą …), Kiril, Yunan harfleri ve işaretler (… ™ € vb.).
**Türkçe için eksik:** `ş Ş ğ Ğ ı İ` (tablo girişleri boş) — Xenia testiyle doğrulandı. `ç Ç ö Ö ü Ü â î û` mevcut.

## Çözüm (yöntem a): gerçek kod noktaları
`tools/build_fonts.py`, her font için 6 yeni kayıt ekler ve tabloyu U+015F, U+015E, U+011F, U+011E, U+0131, U+0130 için günceller. Glifler atlasta son glif satırının sağındaki boş alana çizilir
(yalnızca dokunulan 4×4 bloklar yeniden kodlanır; eski piksellerde fark 0):

| Glif | Bileşim |
|---|---|
| ş / Ş | `s` / `S` + `ç` / `Ç` çengeli (baz harfin altında ortalı) |
| İ | `I` + `Ż` noktası |
| ı | `i`'nin noktası silinmiş hali |
| ğ / Ğ | `g` / `G` + breve (c/C üstündeki caron kutusuyla aynı yerde, parabolik "U"; kalınlık font boyuna göre) |

Önizleme: `docs/font_preview.png` (orijinal/yeni, her font), `docs/font_atlas_gui_normal.png` (atlas önce/sonra).
`char_map.json` bu yüzden boş. Pub Games `fonts_en.swf` (DefineFont3, 1894 glif) zaten tüm Türkçe harfleri içerir; değişiklik gerekmedi.
Test: `python tools/build_test_font.py` → `output/test_font/` (menüde "Şişli Ğ ğ ı İ ş ç ö ü" içeren test satırları).
