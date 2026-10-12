# Fable II Türkçe Yama

**Fable II (Xbox 360, Game of the Year / Platinum)** için tam Türkçe yerelleştirme: menüler, görevler, kitaplar, eşyalar, NPC konuşmaları, altyazılar ve Pub Games mini oyunları. Xenia Canary'de çalışır.

> **Durum: v1.0.2** — 333 metin bankası, 56.000 metin parçası çevrildi ve denetlendi (altyazıların tamamı ID bazında kaynakla karşılaştırmalı okundu). Bildirilen hatalar düzeltilmektedir.

<!-- Ekran görüntüleri: docs/ekran/ klasörüne koyup buraya ekleyin
![Ana menü](docs/ekran/menu.png)
![Altyazı](docs/ekran/altyazi.png)
-->

*English summary:* Turkish translation patch for Fable II GOTY (Xbox 360, Title ID 4D5307F1 / Media ID 716F0A0D) for Xenia Canary. This repository contains **only translations (string ID → Turkish), a glossary and build tools**. It contains no game files and no English game text; the build tools read the English source from *your own* copy of the game and ship binary **xdelta deltas** only. Players: download the installer from [Releases](../../releases). Contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

---

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

- Bu sürümün dosyaları henüz VirusTotal'a yüklenmedi; yüklendiğinde raporlar buraya eklenecek.
- Dosya bütünlüğü (release dosyaları):
```
SHA-256 (Kurulum/Fable2_Turkce_Kurulum.exe): f89c3d3b5b6421fe2691adbcc90d06ee4cbc31ba64207412e88c1d01a862881a
SHA-256 (Fable2_Turkce_Yama_v1.0.2.zip): 240aa13f210802179a61d3662c508cb4b345f388f7a8ccf57a978d6dabf8505a
```
  (Windows: `certutil -hashfile Fable2_Turkce_Kurulum.exe SHA256`.)
- **Güvenmek istemezseniz exe'siz yol:** pakette `Elle_Kurulum/yama_uygula.bat` vardır; ISO'yu çıkarıp bat dosyasını çalıştırmanız yeterlidir (her dosya SHA-256 ile doğrulanır). Ayrıntı: [docs/antivirus.md](docs/antivirus.md).
- Kurucuyu kendiniz derleyebilirsiniz: `python tools/build_all.py` (Nuitka + Visual Studio Build Tools gerekir).

