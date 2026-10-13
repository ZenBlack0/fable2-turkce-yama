# Fable II Türkçe Yama

**Fable II (Xbox 360, Game of the Year / Platinum)** için tam Türkçe yerelleştirme: menüler, görevler, kitaplar, eşyalar, NPC konuşmaları, altyazılar ve Pub Games mini oyunları. Xenia Canary'de çalışır.

> **Durum: v1.0.2** — 333 metin bankası, 56.000 metin parçası çevrildi ve denetlendi (altyazıların tamamı ID bazında kaynakla karşılaştırmalı okundu). Bildirilen hatalar düzeltilmektedir.

<!-- Ekran görüntüleri: docs/ekran/ klasörüne koyup buraya ekleyin
![Ana menü](docs/ekran/menu.png)
![Altyazı](docs/ekran/altyazi.png)
-->

*English summary:* Turkish translation patch for Fable II GOTY (Xbox 360, Title ID 4D5307F1 / Media ID 716F0A0D) for Xenia Canary. This repository contains **only translations (string ID → Turkish), a glossary and build tools**. It contains no game files and no English game text; the build tools read the English source from *your own* copy of the game and ship binary **xdelta deltas** only. Players: download the installer from [Releases](../../releases). Contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Desteklenen oyun sürümü
Yama **yalnızca** şu sürümle çalışır:

| | |
|---|---|
| Oyun | Fable II — Game of the Year / Platinum Edition (Xbox 360, tek disk ISO) |
| Title ID | `4D5307F1` |
| Media ID | `716F0A0D` (Xenia yama dosyasında "Disc (USA, Europe)" olarak geçen disk) |
| `default.xex` modül hash'i (Xenia yama dosyası) | `4145F96D2DEE2AB5` |
| `default.xex` SHA-256 | `88c4ef2e18e65409444d1b068eff921d1f7e180a5ae64edc64ba6b0872372662` (21.217.280 bayt) |
| Yamanın geliştirildiği/test edildiği ISO | 7.838.695.424 bayt (≈7,3 GiB), SHA-256 `2cdaafead95680e2c6fe8886a89f1ae3d5e41549857c7fc125a12aab1cb99ad9` |

**Kurucu ISO'yu nasıl doğrular?** ISO'nun SHA-256 değerine bakmaz; ISO içindeki `default.xex` dosyasından **Title ID ve Media ID** değerlerini okur ve ikisi de yukarıdakiyle aynı değilse reddeder. Ardından yamalanan 11 oyun dosyasının her birinin orijinal SHA-256 değerini uygulamadan önce, sonucunu uyguladıktan sonra doğrular; uyuşmayan dosyaya yama uygulanmaz ve kurulum durur. `default.xex` hash'i beklenenden farklıysa yalnızca uyarı verir.

**Kendi ISO'nuzu kontrol edin** (PowerShell):
```powershell
Get-FileHash -Algorithm SHA256 "ISO_YOLU"
```
Sonuç yukarıdaki ISO değeriyle aynıysa birebir aynı dökümdür. Farklıysa bu tek başına sorun değildir (dökümler farklı araçlarla alınmış olabilir); asıl doğrulama Title/Media ID ve oyun dosyalarının hash'leriyle yapılır.

**Desteklenmeyen sürümler** (yama bunlarda test edilmedi):
- Standart (Game of the Year olmayan) Fable II — Title ID ve Media ID yukarıdakilerle eşleşmediği için kurucu "Bu ISO yamayla uyumlu değil" diyerek reddeder.
- Media ID'si `716F0A0D` olmayan diskler (ör. Xenia yama dosyasında ayrıca listelenen Almanya, İtalya ve İspanya diskleri, NTSC-J ve diğer bölge/dil baskıları) — kurucu reddeder.
- Xbox One / Xbox Series dijital sürümleri — ISO olmadıkları için kurucu "Xbox 360 ISO'su gibi görünmüyor" diyerek reddeder.

Elle kurulum yolu (`yama_uygula.bat`) Title/Media ID'ye bakmaz, ama her dosyayı SHA-256 ile doğrular ve orijinal GOTY dosyası değilse durur.

> **Yasal not:** Oyunun hiçbir dosyası yamada bulunmaz; kurucu ve yama dosyaları yalnızca fark yamaları içerir. Yamayı kullanmak için yasal bir Fable II kopyasına (kendi diskinizden aldığınız ISO) sahip olmanız gerekir. Bu belge ve proje oyunu edinmek için bir kaynak göstermez.

## Oyuncular için

> **Kurulumdan önce:**
> - **Zip'i önce bir klasöre çıkarın.** Zip'in içinden exe'ye çift tıklarsanız kurucu çalışmaz.
> - **`Kurulum/` klasöründeki dosyaları silmeyin veya ayırmayın**, exe yalnızca klasörün içinde çalışır.
> - Windows SmartScreen uyarı çıkarırsa: **Ek bilgi → Yine de çalıştır** (kurucu imzasız, açık kaynaklı bir programdır; aşağıdaki "Antivirüs uyarıları" bölümüne bakın).

**İndirme:** [Releases](../../releases) sayfasından `Fable2_Turkce_Yama_v1.0.2.zip` dosyasını indirin, içindeki **`OKUBENI.txt`** dosyasındaki adımları izleyin (tek tık kurucu: `Kurulum/Fable2_Turkce_Kurulum.exe`). Kendi Fable II GOTY ISO'nuza ve [Xenia Canary](https://github.com/xenia-canary/xenia-canary-releases/releases)'ye ihtiyacınız var; oyunun kendisi pakette **yoktur**.

## Katkı verenler için

Hata mı buldunuz? [Issues](../../issues) → "Çeviri hatası" şablonu. Düzeltme göndermek istiyorsanız [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun. Kısa özet:

### Kurulum
1. Python 3.11+ ve `pip install numpy pillow nuitka ordered-set zstandard` (kurucuyu derlemek için ayrıca Visual Studio Build Tools / MSVC; yalnızca çeviri için `--no-installer` yeterli)
2. `xdelta3.exe` (3.x, Windows) dosyasını [xdelta-gpl](https://github.com/jmacd/xdelta-gpl/releases) sürümlerinden indirip `tools/bin/xdelta3.exe` olarak koyun.
3. Kendi Fable II GOTY ISO'nuzu çıkarın:
   `python tools/extract_iso.py "Fable II.iso" -o extracted_original`
4. İngilizce kaynak metni **kendi oyununuzdan** çıkarın (depoda yoktur):
   `python tools/extract_source.py`
   (`work/extracted_babel/`, `translation/source.json` ve `translation/pubgames_src/` oluşur; hepsi `.gitignore`'dadır.)

### Çeviri düzeltme iş akışı
- Çeviriler `translation/banks_translated/<banka>.json` içindedir: `{"id": "<string id>", "text": "<Türkçe>"}`. İngilizce karşılığı görmek için `work/extracted_babel/book_en_strings.json` içinde aynı `id`'yi arayın.
- Düzeltmeyi JSON'da yapın. Satır sonları (`\n`), `<...>` etiketleri ve `%d`/`%s`/`$değişken` gibi yer tutucular **İngilizcedekiyle birebir aynı** kalmalıdır.
- `python tools/validate_all.py` — 333 bankayı kaynakla karşılaştırır (etiket/yer tutucu/satır sayısı, terim uyarıları, UI uzunluğu). Hata sayısı 0 olmalı.
- `python tools/subtitle_lint.py rules` — bilinen yazım/terim kalıplarını tarar (`--apply` ile otomatik düzeltir).
- `python tools/build_all.py` — doğrulama → yama → font → Pub Games → xdelta (+hash doğrulaması) → kurucu → `release/` paketi. Yalnızca test için `--no-installer`.
- Terim ve üslup kuralları: [`translation/glossary.json`](translation/glossary.json) (Efsun Taşı, Zorba, Kumkazı, banshee… hitap ve ek kuralları dâhil).

### Teknik notlar
- `.babel` (yerelleştirme kapsayıcısı) ve `.bft` (bitmap font) biçimleri: [docs/babel_format.md](docs/babel_format.md), [docs/bft_format.md](docs/bft_format.md); kontrol kodları: [docs/control_codes.md](docs/control_codes.md); altyazı araştırması: [docs/altyazi_arastirmasi.md](docs/altyazi_arastirmasi.md).
- Oyun fontlarında olmayan `ş Ş ğ Ğ ı İ` glifleri `tools/build_fonts.py` ile 6 `.bft` dosyasına eklenir.
- Dağıtım **yalnızca xdelta fark yamasıdır**; her dosya uygulamadan önce (orijinal mi?) ve sonra (beklenen mi?) SHA-256 ile doğrulanır. Orijinal/yamalı tam dosya hiçbir pakete konmaz (`python tools/scan_release.py <klasör|zip>` bunu denetler).

### Xenia ayarları ve nedenleri
Ayrıntı: [docs/xenia_ayarlari.md](docs/xenia_ayarlari.md). Özet (`xenia-canary.config.toml`, Xenia kapalıyken):

| Ayar | Değer | Neden |
|---|---|---|
| `[GPU] render_target_path_d3d12` | `"rov"` | Varsayılan RTV yolunda altyazılar **görünmez** (orijinal oyunda da). |
| `[GPU] framerate_limit` | `60` | Sınırsız kare hızı GPU'yu sürekli %99 yükler. |
| `[GPU] async_shader_compilation` | `false` | Açıkken haritanın bazı yerlerinde çok kısa görüntü bozulmaları oluşur; kapalıyken yeni bölgeye ilk girişte kısa donmalar olabilir, önbellek doldukça azalır. |
| `[General] apply_patches` | `true` | Fable II Xenia yamaları (Disable Texture Morphing, Disable MSAA, High Tick Rate). |

Oyun içi dil: **English (United Kingdom)** (yama bu dil dosyasının yerine geçer).

## Teşekkürler
- **Fable II PT-BR çeviri projesi** — `.babel` düzeni ve yerelleştirme mimarisi için referans.
- **Fable2Modding topluluğu** — dosya biçimleri ve tersine mühendislik notları.
- **xenia-fable2-patches** (JustSomeGuy1234) ve **xenia-canary/game-patches** yazarları — Fable II Xenia yamaları.
- **Xenia / Xenia Canary** geliştiricileri.
- **xdelta** (Joshua MacDonald, Apache-2.0).
- Fable II, Lionhead Studios / Microsoft'a aittir; bu proje resmi değildir.

## Lisans
- **Araç kodu** (`tools/` ve diğer kod): [MIT](LICENSE) — Copyright (c) 2026 Kerim.
- **Çeviri metni** (`translation/` altındaki çeviriler ve sözlük): [CC BY-NC-SA 4.0](translation/LICENSE) — atıf, ticari olmayan kullanım, aynı lisansla paylaşım.
- **Oyun metninin ve oyunun hakları** Microsoft / Lionhead Studios'a aittir. Bu proje resmi değildir; çeviri, oyunun metninden türetilmiş bir yapıdır ve oyunun hiçbir dosyasını içermez.

## Antivirüs uyarıları
Kurucu (`Kurulum/Fable2_Turkce_Kurulum.exe`) **açık kaynaktır** (kaynak kodu bu depoda: [`tools/installer/installer.py`](tools/installer/installer.py)); Python ile yazılmış ve [Nuitka](https://nuitka.net) ile derlenmiştir. İmzasız olduğu ve içinde fark yaması aracı (`xdelta3.exe`) bulunduğu için bazı **yapay zekâ/makine öğrenmesi tabanlı** antivirüs motorları yanlış alarm verebilir. Aynı kaynağın farklı yöntemlerle derlenmiş sürümleri VirusTotal'da 70 kadar motorun yalnızca birkaçı tarafından ve hep genel "şüpheli/ML" etiketleriyle işaretlendi; bu yöntemde (Nuitka klasör çıktısı) deneme derlemesinin exe'si **0/71**, zip'i 1/68 tespit aldı (ayrıntı aşağıda ve `docs/antivirus.md` içinde).

- **Release dosyalarının VirusTotal raporları:** [kurucu exe — 0/71](https://www.virustotal.com/gui/file/f89c3d3b5b6421fe2691adbcc90d06ee4cbc31ba64207412e88c1d01a862881a) · [zip — 1/67](https://www.virustotal.com/gui/file/240aa13f210802179a61d3662c508cb4b345f388f7a8ccf57a978d6dabf8505a)
  MaxSecure'un “susgen” etiketi genel (sezgisel) bir şüphe tespitidir, belirli bir zararlı ailesi değildir; önceki Nuitka standalone zip derlemelerinde de (v1.0.1 öncesi deneme derlemesi dahil) aynı etiket çıkmıştı.
- Dosya bütünlüğü (release dosyaları):
```
SHA-256 (Kurulum/Fable2_Turkce_Kurulum.exe): f89c3d3b5b6421fe2691adbcc90d06ee4cbc31ba64207412e88c1d01a862881a
SHA-256 (Fable2_Turkce_Yama_v1.0.2.zip): 240aa13f210802179a61d3662c508cb4b345f388f7a8ccf57a978d6dabf8505a
```
  (Windows: `certutil -hashfile Fable2_Turkce_Kurulum.exe SHA256`.)
- **Güvenmek istemezseniz exe'siz yol:** pakette `Elle_Kurulum/yama_uygula.bat` vardır; ISO'yu çıkarıp bat dosyasını çalıştırmanız yeterlidir (her dosya SHA-256 ile doğrulanır). Ayrıntı: [docs/antivirus.md](docs/antivirus.md).
- Kurucuyu kendiniz derleyebilirsiniz: `python tools/build_all.py` (Nuitka + Visual Studio Build Tools gerekir).

