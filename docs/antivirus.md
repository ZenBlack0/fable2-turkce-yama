# Antivirüs yanlış alarmları

Kurucu, Python ile yazılmış ve paketlenmiş **açık kaynaklı** bir programdır (`tools/installer/installer.py`). İmzasız Python paketleri ve içlerinde fark yaması aracı (`xdelta3.exe`) bulunan kurucular, bazı antivirüs motorlarının **statik makine öğrenmesi** (ML/AI) sezgilerinde sık sık yanlış pozitif verir. Kurucunun yaptığı işler: ISO'yu doğrulayıp çıkarmak, oyunun 11 dosyasına xdelta fark yaması uygulamak (SHA-256 doğrulamalı), Xenia ayar dosyasını düzenlemek ve (internet varsa) resmî `xenia-canary/game-patches` deposundan Fable II yama dosyasını indirmek.

## Karşılaştırma (VirusTotal, 12 Ekim 2026, v1.0.0 → v1.0.1 arası denemeler)
Aynı kaynak kodu farklı yöntemlerle derlenip VirusTotal'a yüklendi:

| Yöntem | Tespit | Not |
|---|---|---|
| PyInstaller `--onefile` (v1.0.0'daki yöntem) | 6/70 | Arctic Wolf, Bkav, DeepInstinct, Elastic, SecureAge, SentinelOne (Static ML) |
| PyInstaller `--onefile` + sürüm bilgisi + manifest | 5/70 | Bkav, Elastic, SecureAge, SentinelOne, Zillya |
| PyInstaller `--onefile`, önyükleyici kaynaktan derlenmiş | 8/71 | |
| PyInstaller `--onedir` (zip) | 2/67 | MaxSecure, Zillya |
| Nuitka `--onefile` | 9/71 | AhnLab, Bkav, CrowdStrike, Elastic, McAfee, Microsoft (`Wacatac!ml`), SentinelOne, Symantec, Trapmine |
| **Nuitka `--standalone` (v1.0.1'de kullanılan)** | **exe 0/71; tüm zip 1/68** | zip: MaxSecure ("susgen" genel imza) |

Kalan tek işaret genel/sezgisel bir etikettir (belirli bir kötü amaçlı yazılım ailesi adı değildir). Tek dosyalık (`--onefile`) paketler kendini geçici klasöre açtığı için ML motorlarına daha şüpheli görünür; klasör çıktısı bu yüzden tercih edildi.

## Kendiniz doğrulama
- `Fable2_Turkce_Yama_v*.zip` içindeki `SHA256SUMS.txt` ve release sayfasındaki `SHA256SUMS.txt` ile dosya özetlerini karşılaştırın.
- Kaynak kodundan kendiniz derleyin: `python tools/build_all.py`.
- Hiç exe çalıştırmak istemezseniz: `Elle_Kurulum/yama_uygula.bat` (ISO'yu çıkarın, bat dosyasını çalıştırın; her dosya SHA-256 ile doğrulanır, uyuşmazsa durur).
- Yanlış alarmı ilgili antivirüs sağlayıcısına "false positive" olarak bildirebilirsiniz.
