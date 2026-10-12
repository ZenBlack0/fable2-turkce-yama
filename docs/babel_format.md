# Lionhead Studios `.babel` Dosya Formatı Spesifikasyonu
**Oyun:** Fable II (Xbox 360)  
**Hedef Dosya:** `data/language/<dil>/text/book.babel`  
**Platform Mimarisi:** Xbox 360 (Big-Endian, PowerPC)  

---

## 1. Genel Bakış

Lionhead Studios `.babel` formatı, Fable II'nin tüm yerelleştirilmiş metinlerini (görevler, diyaloglar, kitaplar, arayüz butonları, eşya açıklamaları) tek bir ikili veritabanında saklayan özel bir formattır.

Dosya 5 ana bölümden oluşur:
1. **Dosya Başlığı (Header)**: Sihirli bayt ve toplam metin sayısı.
2. **Metin İndeks Tablosu (String Index Table)**: Metin ID'lerini Banka ve ofsetlere eşleyen sıralı ikili arama tablosu.
3. **Banka Sayısı (Bank Count)**: Sıkıştırılmış metin bloklarının sayısı.
4. **Banka Veri Blokları (Compressed Banks Pool)**: Zlib ile sıkıştırılmış UTF-16 BE metin havuzları.
5. **Kuyruk / Meta Veri Bölümü (Tail Metadata)**: Ses/altyazı eşleşmeleri ve ters arama tabloları (dilden bağımsız statik bölüm).

---

## 2. Bölüm Detayları ve Bayt Düzeni

Tüm çok baytlı tamsayılar **Big-Endian** (`>I` / `>H`) formatındadır.

### 2.1 Dosya Başlığı (8 Bayt)

| Ofset | Boyut | Tür | Açıklama |
|---|---|---|---|
| `0x00` | 4 B | `uint32_be` | **Sihirli Bayt (Magic):** `0x5B010000` (ASCII `[` ardından versiyon/bayraklar) |
| `0x04` | 4 B | `uint32_be` | **Toplam Metin Sayısı ($N$):** `en-uk` için `56.000` (`0x0000DAC0`) |

---

### 2.2 Metin İndeks Tablosu ($N \times 12$ Bayt)

Başlangıç ofseti: `0x08`.  
Toplam boyut: $N \times 12$ bayt (56.000 metin için 672.000 bayt).

Tablodaki her girdi tam olarak 12 bayttır:

| Alan | Boyut | Tür | Açıklama |
|---|---|---|---|
| `string_id` | 4 B | `uint32_be` | Benzersiz 32-bit metin kimliği. Tabloda **kesin olarak artan sırada (ascending)** sıralıdır. Oyun motoru $O(\log N)$ ikili arama (`bsearch`) ile metni bulur. |
| `bank_id` | 4 B | `uint32_be` | Metnin bulunduğu bankanın (kategorinin) 32-bit kimliği (örn. `0x20499600`). |
| `string_offset`| 4 B | `uint32_be` | Metnin ilgili bankanın **açılmış (uncompressed)** veri bloğu içindeki bayt ofseti. |

---

### 2.3 Banka Sayısı (4 Bayt)

Başlangıç ofseti: `8 + (N * 12)` (56.000 metin için `0x000A4108` = 672.008).

| Alan | Boyut | Tür | Açıklama |
|---|---|---|---|
| `bank_count` | 4 B | `uint32_be` | Toplam banka sayısı ($M$). Orijinal oyunda `333` (`0x0000014D`). |

---

### 2.4 Banka Veri Blokları (Değişken Boyut)

$M$ adet ardışık banka bloku bulunur. Her bankanın başlığı ve verisi şu şekildedir:

| Alan | Boyut | Tür | Açıklama |
|---|---|---|---|
| `bank_id` | 4 B | `uint32_be` | Banka kimliği (İndeks tablosundaki `bank_id` ile eşleşir). |
| `compressed_size` | 4 B | `uint32_be` | Zlib sıkıştırılmış veri blokunun bayt uzunluğu ($C$). |
| `uncompressed_size` | 4 B | `uint32_be` | Açılmış metin havuzunun bayt uzunluğu ($U$). |
| `compressed_data` | $C$ B | Bayt Dizisi | Deflate ile sıkıştırılmış akış. `0x78DA` başlığı ile başlar ve `01 00 00 FF FF` (`Z_SYNC_FLUSH`) ile biter. |

#### Açılmış Metin Havuzu İçi Düzeni:
Banka açıldığında ($U$ bayt) içindeki her metin ardışık olarak şu düzendedir:
1. `char_count` (4 bayt, `uint32_be`): Metindeki UTF-16 karakter sayısı (sonundaki `\0` null sonlandırıcı dahil).
2. `string_data` ($char\_count \times 2$ bayt): **UTF-16 Big-Endian** kodlu karakter dizisi. Son 2 bayt `0x0000` (null karakterdir).

---

### 2.5 Kuyruk / Meta Veri Bölümü (670.498 Bayt)

Son bankanın sıkıştırılmış verisinden sonra başlar (orijinal `en-uk` dosyasında `1.960.949` ofsetinde).

- **Boyut:** 670.498 bayt (sabit).
- **İçerik:** Ses/altyazı çapraz referansları (`speech.adb` ile bağlantılı hashler) ve ters indeks arama tabloları.
- **Kritik Doğrulama:** Bu bölümün Portekizce (`PT-BR`) `book.babel` dosyası ile orijinal `en-uk` dosyası arasında **birebir (%100 byte-for-byte)** aynı olduğu doğrulanmıştır. Yerelleştirmede değiştirilmez; repack sırasında orijinal kuyruk korunarak dosya sonuna eklenir.
