# B bölümü — Tam metin denetimi: nihai rapor

## Kapsam (%100)
| Küme | Çift | Okunan | Düzeltilen çift |
|---|---:|---:|---:|
| a — hikâye / sinematik | 1.298 | 1.298 | 56 |
| b — banka 284–333 | 3.839 | 3.839 | 87 |
| c — görev / NPC | 14.252 | 14.252 | 491 |
| d — ortam / örnek (barklar) | 17.637 | 17.637 | 238 |
| **Altyazı toplamı** | **37.026** | **37.026** | **872** |
| Altyazı dışı tüm metin (menü, sistem, eşya, görev, UI) | ≈10.476 | ≈10.476 | ≈1.100+ |

Her çift EN kaynakla yan yana okundu; toplu yeniden çeviri yapılmadı, yalnızca açık hatalar düzeltildi.

## Tipik hata türleri
- **Hitap tutarlılığı:** sen/siz karışması (Theresa ve ana anlatıcı "sen"), kişi için "bunu/bununla".
- **Terim sapmaları:** augment→Efsun Taşı, Brute→Zorba (Kaba Kuvvet kalmadı), Sandgoose→Kumkazı ("Çöl Kazı" düzeltildi), Highwayman→Yolkesen, Old Town→Eski Şehir ("Eski Kasaba" 5 yerde), ranger→korucu, monk→keşiş, nekromansır, kof adam (cümle ortası küçük harf).
- **Anlam/çeviri hataları:** deyimlerin düz çevrilmesi (up your sleeve, safety on/off, roll in the hay, rug, ablutions→abdest), olumsuz soru kayması, bozuk cümleler.
- **Yazım:** şapsal/şaklaban/emi/kar→kâr, ünlü uyumu (Sever mı), ayrık ekler, "akılalmaz", "ikile", "kancık".
- **Tutarlılık:** lakaplar (Sonsuz Istıraplı İşkencenin Gölge İblisi), warrant=yakalama emri.
- Kalan bilinçli bırakılanlar: etiketli satırlar (`<sighs>` vb. — etiket sayısı korunmalı), banshee/Ölüm Perisi adlandırması, "Tecrübe/Deneyim" ve "Kuvvet/Güç" ikilisi.

## Otomatik kurallar
`tools/subtitle_lint.py` yeni kurallarla genişletildi (kof adam, "Sever mi", şapşal/şaklaban, terim sapmaları, ikile/kancık) ve tüm metne uygulandı; `spell` yeniden çalıştırıldı (880 benzersiz bilinmeyen sözcük — büyük kısmı sözlükte olmayan çekimli/konuşma biçimleri; gerçek hatalar elle düzeltildi).

## UI taşma sonuçları
Tek satırlık 4.849 etiket piksel metrikleriyle ölçüldü (`tools/ui_overflow.py`, `translation/reports/ui_overflow.md/.json`). EN genişliğini aşan 1.667 etiketin kısaltılabilenleri kısaltıldı (Şişman Düşmanı, Kas Düşmanı vb. ve ~yüzlerce UI/HUD/eşya etiketi). Doğrulayıcı hâlâ ≈970 "aday" bildiriyor; çoğu oyunun kaydırma/çok satırlı alanlarında sorun çıkarmayabilir. En riskli kalanlar (oran >1.6): kredilerdeki başlıklar ("Görsel Tasarım", "Ana Seslendirme Kadrosu"), "Zührevi Hastalık", "Cehennem Ateşi", "Blok yapmak için <x_img> tuşunu basılı tutun", "Belediye Başkanı", "İstatistikler".

## Paketler
`output/Fable2_Turkce_Yama.zip`, `Fable2_Turkce_Yama_xdelta.zip`, `book.babel.xdelta`, `Fable2_Turkce_Kurulum.exe/.zip` yeniden üretildi; validate_all: 333 banka, 0 hata.

## Oyunda bakılacak ekranlar
1. Krediler (Görsel Tasarım / Ana Seslendirme Kadrosu başlıkları taşıyor mu).
2. Yetenek ekranı: Cehennem Ateşi, Defetme, Kuvvet İtişi, Uçuşan Çark, Gösterişli Vuruş.
3. İstatistikler, Hediyeler, Yara İzleri, Kız/Erkek Çocuk etiketleri (karakter/aile ekranları).
4. Savaşta "<x_img> tuşunu basılı tutun" ipucu satırı.
5. Eşya/efsun taşı mağaza ekranları (Efsun Taşı adları).
6. Pub Games (Kilit Taşı, Çarkıfelek Kutusu, Talih Kulesi) menü ve altyazıları.
7. Tapınak (Işık/Gölge) ve Kule (Spire) sahneleri: hitap ve terim tutarlılığı.
8. Eski Şehir bölgesi yol/giriş etiketleri ve görev günlüğü.
9. Köylü/tüccar/çocuk barkları: altyazı satır uzunluğu ve ekran dışına taşma.

## Terim kararları (son tur)
- **Deneyim:** oyun mekaniği olan tüm "Tecrübe" kullanımları "Deneyim" yapıldı (57 satır; Deneyim Puanı, deneyim küresi, Deneyim iksiri, Hoggins-McGuffy Deneyim Ölçeği); glossary güncellendi. Doğal kullanımlar (tecrübeli, geçmiş tecrübelerim, tecrübe etmek, "Ne acı verici bir tecrübe") korundu.
- **Güç:** kategori olarak "Kuvvet" geçen 9 satır "Güç" yapıldı (Güç Kahramanı ×6, "Güç (mavi)" HUD/yardım metinleri ×3). "Kuvvet" yalnız Kuvvet İtişi'nde (3 satır) ve sıradan sözcük olarak (kuvvetli, kolluk kuvvetleri) kalır.
- **Banshee (karar bekliyor):** glossary "Ölüm Perisi" der, ama creature_suffixes kuralı küçük harfli "banshee" der; metinde 30 yerde "banshee" (13 yalın + ekli biçimler), 2 yerde "Ölüm Perisi" (174af83c "Ölüm Perisi Paçavraları", 0b9f7b5c "Öldürülen Ölüm Perisi") geçiyor, yani iki ad karışık.
- **Banshee (karar verildi):** her yerde küçük harfli "banshee" (cümle başı büyük; ekler kesmeli: banshee'yi, banshee'ler). 13 satırdaki "Ölüm Perisi/ölüm perileri" biçimleri düzeltildi (önceki "2 satır" sayımı büyük harfli Ö'yü atlamıştı); glossary girdisi "banshee" yapıldı.
- **xdelta boyutu:** 1,69 → 1,51 MB düşüşü çeviriden değil sıkıştırma ayarından: eski dosya varsayılan ayarla, yenisi `-9` ile üretildi (aynı yamayı varsayılan ayarla üretmek 1,69 MB verir). Artık xdelta, `package_release.py` içinde her seferinde `-9` ile yeniden üretilip orijinale uygulanarak SHA-256 ile doğrulanıyor; tek komut: `python tools/build_all.py`.
