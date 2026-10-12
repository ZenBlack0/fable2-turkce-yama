# Katkı rehberi

Teşekkürler! Bu depo yalnızca **çeviri (ID → Türkçe)**, terim sözlüğü ve araçları içerir. Oyun dosyası ve İngilizce metin dökümü **eklemeyin ve PR'a koymayın** (`.gitignore` bunları dışarıda tutar; yine de `git status` ile bakın).

## Hata bildirme
[Issues](../../issues) → şablon seçin:
- **Çeviri hatası:** ekran görüntüsü (altyazıysa görüntü + altyazı birlikte), oyundaki bölge/görev ve konuşan karakter, yanlış metin, önerdiğiniz düzeltme. Biliyorsanız string ID'si.
- **Teknik sorun:** Xenia sürümü, ekran kartı ve sürücü, config'inizdeki `[GPU]` ayarları, `xenia.log`, kurulum raporu.

## Çeviri düzeltme kuralları
Ayrıntısı [`translation/glossary.json`](translation/glossary.json) içindedir; en önemlileri:

1. **Yalnızca açık hata düzeltilir.** Zevke dayalı toplu yeniden çeviri yapılmaz; değişikliğin nedenini PR açıklamasına yazın (yazım, anlam hatası, terim, hitap, ek…).
2. **Terimler:** sözlükteki karşılıkları kullanın (augment → Efsun Taşı, Brute → Zorba, Sandgoose → Kumkazı, Highwayman → Yolkesen, Old Town → Eski Şehir, Hollow Man → kof adam, banshee → banshee, Experience → Deneyim, Strength → Güç). Yeni terim öneriyorsanız önce issue açın.
3. **Hitap ve ağız:** arayüz/sistem metinlerinde "siz"; Theresa ve anlatıcı kahramana "sen" der. NPC'lerin ağzı (köylü, soylu, haydut…) İngilizcedeki üsluba uygun kalır.
4. **Ekler:** yaratık adlarında kesme işareti ve ince ünlü uyumu (`banshee'yi`, `hobbe'ler`, `balverine'ler`; trol → `trolün`, kesmesiz). "-mekte olmak" gibi çeviri kokan kalıplardan kaçının.
5. **Yapı birebir korunur:** satır sonu sayısı, `<...>` etiketleri (`<x_img>`, `<laughs>`…) ve `%d %s %1 %2`, `$değişken` yer tutucuları İngilizcedekiyle aynı olmalıdır; `validate_all.py` bunları denetler.
6. **UI uzunluğu:** menü/HUD etiketleri İngilizceden belirgin uzunsa kısaltın (`python tools/ui_overflow.py`); taşma riskli yerleri PR'da belirtin.
7. **Yazım:** TDK; "kâr/hâlâ" gibi uzatma işaretleri tutarlı.

## PR akışı
1. Depoyu fork'layın, kısa bir dal açın (`duzeltme/<konu>`).
2. README'deki kurulumu yapın (ISO çıkarma + `extract_source.py`).
3. `translation/banks_translated/*.json` (veya `translation/pubgames_tr/*.json`) içinde düzeltin.
4. `python tools/validate_all.py` → **0 hata**; `python tools/subtitle_lint.py rules` yeni bulgu çıkarmamalı.
5. `python tools/build_all.py --no-installer` çalışmalı (xdelta doğrulaması geçmeli). Mümkünse oyunda ilgili yeri kontrol edin.
6. PR açıklamasına: değişen ID'ler, kısaca neden, varsa ekran görüntüsü. Bir PR'da tek konu.
7. `translation/` dışındaki araç değişiklikleri için önce issue açıp tartışalım.

## Yapmayın
- Orijinal oyun dosyası (`.babel`, `.bft`, `.xex`, ses/doku vb.), ISO parçası ya da İngilizce metin dökümü commit etmeyin. `python tools/scan_release.py .` bunları tarar.
- Toplu otomatik çeviri PR'ı göndermeyin.
