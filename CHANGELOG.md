# Değişiklik günlüğü

## v1.0.1
Kurucu antivirüs yanlış alarmlarını azaltmak için yeniden derlendi; çeviri metni değişmedi.
- Kurucu **Nuitka `--standalone`** (klasör çıktısı) ile derlendi (PyInstaller tek dosya yerine); VirusTotal'da exe 0/71, tüm paket 1/68 tespit. Ayrıntı: `docs/antivirus.md`.
- Paket düzeni: `Kurulum/` (kurucu klasörü), `Elle_Kurulum/` (exe'siz yol; `extract_iso` da Nuitka ile derlendi), `OKUBENI.txt`, `SHA256SUMS.txt`.
- Kurucu: sürüm bilgisi eklendi; `--selftest` modu; komut satırı modunda mesajların görünmemesi hatası giderildi (GUI etkilenmiyordu).
- README/OKUBENI'ye "Antivirüs uyarıları" bölümü, `docs/antivirus.md`.

## v1.0.0
İlk kararlı sürüm.
- **Kapsam:** 333 banka, 56.000 metin parçası: ana senaryo, yan görevler, Knothole Island ve See the Future DLC'leri, kitaplar, günlükler, eşyalar, arayüz, ipuçları, NPC diyalogları ve altyazılar; Pub Games (Kilit Taşı, Çarkıfelek Kutusu, Talih Kulesi + ortak arayüz).
- **Denetim:** 37.026 altyazı çifti (a/b/c/d sınıfları) ve altyazı dışı tüm metin kaynakla karşılaştırmalı okundu; 872 altyazı çiftinde ve ≈1.100 diğer satırda açık hata düzeltildi. Otomatik kural denetimi (`subtitle_lint.py`) tüm metne uygulandı.
- **Terim kararları:** Deneyim (Tecrübe değil), Güç (kategori; "Kuvvet" yalnız Kuvvet İtişi), banshee, Efsun Taşı, Zorba, Kumkazı, Eski Şehir, Yolkesen, kof adam.
- **Fontlar:** `ş Ş ğ Ğ ı İ` glifleri 6 `.bft` dosyasına eklendi.
- **UI:** 4.849 etiket ölçüldü, taşma riski olanların kısaltılabilenleri kısaltıldı; kalan adaylar `tools/ui_overflow.py` ile listelenir.
- **Dağıtım:** yalnızca xdelta fark yamaları (11 dosya) + SHA-256 doğrulamalı tek tık kurucu (`Fable2_Turkce_Kurulum.exe`) ve elle kurulum betiği. Orijinal/yamalı tam oyun dosyası dağıtılmaz.
- **Xenia ayarları:** ROV (altyazı), `framerate_limit = 60`, `async_shader_compilation = false`; kurucu bunları otomatik yapar.
- **Bilinen sorunlar:** altyazılar yalnızca ROV ile görünür; yeni bölgeye ilk girişte kısa donmalar; küçük fontta (`timesnewroman_10`) `ğ Ğ ş Ş` sıkışık görünebilir; bazı UI metinleri İngilizceden uzun.
