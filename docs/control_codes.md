# Fable II Kontrol Kodları, Değişkenler ve Etiketler Kılavuzu

Bu belge, `book.babel` içerisindeki tüm metinlerde bulunan değişken yer tutucuları, kontrol etiketleri, düğme görselleri ve biçimlendirme kodlarını listeler. Çeviri sürecinde bu kodların **birebir korunması zorunludur**.

---

## 1. Düğme ve Arayüz Görsel Etiketleri (Button & UI Icons)

Oyun metin içerisinde Xbox 360 kontrolcüsü düğmelerini ve çubuklarını özel görsel etiketleriyle render eder:

| Etiket | Açıklama | Örnek Kullanım |
|---|---|---|
| `<a_img>` | Xbox A Butonu | `Press <a_img> to talk.` |
| `<b_img>` | Xbox B Butonu | `Press <b_img> to cancel.` |
| `<x_img>` | Xbox X Butonu | `Attack with <x_img>.` |
| `<y_img>` | Xbox Y Butonu | `Hold <y_img> to enter Aim mode.` |
| `<left.img>` | Sol Analog Çubuk | `...aim using <left.img>.` |
| `<right.img>` | Sağ Analog Çubuk | `Rotate camera with <right.img>.` |
| `<dpad.img>` | Yön Tuşları (D-Pad) | `Select expression with <dpad.img>.` |
| `<lefttrigger.img>` | Sol Tetik (LT) | `Lock-on with <lefttrigger.img>.` |
| `<righttrigger.img>`| Sağ Tetik (RT) | `Cast spell with <righttrigger.img>.` |
| `<start.img>` | Start Düğmesi | `Pause with <start.img>.` |

> [!CAUTION]
> Bu etiketler kesinlikle tercüme edilmemeli, küçük harf ve alt çizgi/nokta yapıları (`<a_img>`, `<left.img>`) olduğu gibi bırakılmalıdır.

---

## 2. Standart Değişken Yer Tutucuları (Format Specifiers)

Metinler C/C++ `printf` tarzı yer tutucular içerir:

| Belirteç | Tür | Toplam Adet | Açıklama / Örnek |
|---|---|---|---|
| `%s` | String (Metin) | 38 | Karakter adı, bölge adı veya nesne adı |
| `%d` | Integer (Tamsayı) | 26 | Altın miktarı, eşya adedi (`Dereliction of Payment x%d`) |
| `%i` | Integer | 2 | Tamsayı değişken |
| `\n` | Satır Sonu | 955 | Diyaloglarda ve menülerde satır sonu ayracı |

---

## 3. Biçimlendirme ve Stil Etiketleri (Formatting Tags)

| Etiket | Kapanış | Açıklama |
|---|---|---|
| `<b>` | `</b>` | Kalın metin (Bold) |
| `<s4>` | `</s4>` | Yazı tipi boyutu / stili (Font size/style 4) |

---

## 4. Ses ve Canlandırma İpuçları (Audio & Animation Cues)

Lionhead diyalog sistemi, konuşma zamanlaması ve mimik senkronizasyonu için metin içine köşeli/açılı ayraçlarla yönlendirmeler gömmüştür:

| Etiket Türü | Örnekler | Davranış Kuralı |
|---|---|---|
| Açı Parantezi (`<...>`) | `<laughs>`, `<whimpers>`, `<mutters>`, `<sighs>`, `<hums>`, `<screams>`, `<giggles>`, `<worried moans>` | **Değiştirilmeden korunmalıdır.** PT-BR projesi de bu etiketleri İngilizce olarak orijinal haliyle korumuştur. |
| Köşeli Parantez (`[...]`) | `[whimpers]`, `[Laughs]`, `[snores]`, `[chants]`, `[sighs]` | **Değiştirilmeden korunmalıdır.** |

---

## 5. Çevirmen Kuralları ve Doğrulama Kriterleri

1. Çeviri grubu tamamlandığında `tools/validate.py` betiği çalıştırılarak kaynak ve hedef metindeki etiket sayısı birebir karşılaştırılmalıdır.
2. `<` ve `>` işaretleri arasına Türkçe karakter veya boşluk eklenmemelidir.
3. Satır sonu (`\n`) karakterlerinin sayısı ve yerleşimi kaynak metne uygun olmalıdır.
