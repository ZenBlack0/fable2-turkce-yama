#!/usr/bin/env python3
"""'Desteklenen oyun surumu' metni: degerler projeden okunur (installer.py sabitleri, output/deltas/manifest.json,
Xenia yama dosyasi hash'i, tools/ref_iso.json). Kullanim: python tools/supported_version.py --make-ref ISO   (bir kez)
tools/ref_iso.json: yamanin gelistirildigi/test edildigi ISO'nun boyutu ve SHA-256 degeri."""
import hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# default.xex modül hash'i (Xenia oyun yama dosyalarındaki 'hash' alanı; oyun sürümünü tanımlar)
XEX_MODULE_HASH = '4145F96D2DEE2AB5'


def _const(name):
    src = open(os.path.join(ROOT, 'tools', 'installer', 'installer.py'), encoding='utf-8').read()
    m = re.search(r"^%s\s*=\s*(.+)$" % name, src, re.M)
    return m.group(1).strip()


def info():
    src = open(os.path.join(ROOT, 'tools', 'installer', 'installer.py'), encoding='utf-8').read()
    m = re.search(r"^TITLE_ID, MEDIA_ID = 0x([0-9A-Fa-f]+), 0x([0-9A-Fa-f]+)", src, re.M)
    title, media = m.group(1).upper(), m.group(2).upper()
    patch_hash = XEX_MODULE_HASH
    man = json.load(open(os.path.join(ROOT, 'output', 'deltas', 'manifest.json'), encoding='utf-8'))
    xex = os.path.join(ROOT, 'extracted_original', 'default.xex')
    ref = json.load(open(os.path.join(ROOT, 'tools', 'ref_iso.json'), encoding='utf-8'))
    return dict(title=title, media=media, patch_hash=patch_hash, xex_sha=man['xex_sha256'],
                xex_size=os.path.getsize(xex), iso_size=ref['size'], iso_sha=ref['sha256'], n=len(man['files']))


def _n(x):
    return '{:,}'.format(x).replace(',', '.')


def markdown():
    v = info()
    return f'''## Desteklenen oyun sürümü
Yama **yalnızca** şu sürümle çalışır:

| | |
|---|---|
| Oyun | Fable II — Game of the Year / Platinum Edition (Xbox 360, tek disk ISO) |
| Title ID | `{v['title']}` |
| Media ID | `{v['media']}` (Xenia yama dosyasında "Disc (USA, Europe)" olarak geçen disk) |
| `default.xex` modül hash'i (Xenia yama dosyası) | `{v['patch_hash']}` |
| `default.xex` SHA-256 | `{v['xex_sha']}` ({_n(v['xex_size'])} bayt) |
| Yamanın geliştirildiği/test edildiği ISO | {_n(v['iso_size'])} bayt (≈{('%.1f' % (v['iso_size']/2**30)).replace('.', ',')} GiB), SHA-256 `{v['iso_sha']}` |

**Kurucu ISO'yu nasıl doğrular?** ISO'nun SHA-256 değerine bakmaz; ISO içindeki `default.xex` dosyasından **Title ID ve Media ID** değerlerini okur ve ikisi de yukarıdakiyle aynı değilse reddeder. Ardından yamalanan {v['n']} oyun dosyasının her birinin orijinal SHA-256 değerini uygulamadan önce, sonucunu uyguladıktan sonra doğrular; uyuşmayan dosyaya yama uygulanmaz ve kurulum durur. `default.xex` hash'i beklenenden farklıysa yalnızca uyarı verir.

**Kendi ISO'nuzu kontrol edin** (PowerShell):
```powershell
Get-FileHash -Algorithm SHA256 "ISO_YOLU"
```
Sonuç yukarıdaki ISO değeriyle aynıysa birebir aynı dökümdür. Farklıysa bu tek başına sorun değildir (dökümler farklı araçlarla alınmış olabilir); asıl doğrulama Title/Media ID ve oyun dosyalarının hash'leriyle yapılır.

**Desteklenmeyen sürümler** (yama bunlarda test edilmedi):
- Standart (Game of the Year olmayan) Fable II — Title ID ve Media ID yukarıdakilerle eşleşmediği için kurucu "Bu ISO yamayla uyumlu değil" diyerek reddeder.
- Media ID'si `{v['media']}` olmayan diskler (ör. Xenia yama dosyasında ayrıca listelenen Almanya, İtalya ve İspanya diskleri, NTSC-J ve diğer bölge/dil baskıları) — kurucu reddeder.
- Xbox One / Xbox Series dijital sürümleri — ISO olmadıkları için kurucu "Xbox 360 ISO'su gibi görünmüyor" diyerek reddeder.

Elle kurulum yolu (`yama_uygula.bat`) Title/Media ID'ye bakmaz, ama her dosyayı SHA-256 ile doğrular ve orijinal GOTY dosyası değilse durur.

> **Yasal not:** Oyunun hiçbir dosyası yamada bulunmaz; kurucu ve yama dosyaları yalnızca fark yamaları içerir. Yamayı kullanmak için yasal bir Fable II kopyasına (kendi diskinizden aldığınız ISO) sahip olmanız gerekir. Bu belge ve proje oyunu edinmek için bir kaynak göstermez.
'''


def text():
    md = markdown()
    md = md.replace('## Desteklenen oyun sürümü', 'DESTEKLENEN OYUN SÜRÜMÜ\n-----------------------')
    md = re.sub(r'\| \| \|\n\|---\|---\|\n', '', md)
    md = re.sub(r'^\| (.+?) \| (.+?) \|$', lambda m: ' * %s: %s' % (m.group(1), m.group(2).replace('`', '')), md, flags=re.M)
    md = md.replace('```powershell\n', '    ').replace('```\n', '').replace('`', '').replace('**', '').replace('> Yasal not:', 'YASAL NOT:')
    return md


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--make-ref':
        h = hashlib.sha256()
        with open(sys.argv[2], 'rb') as f:
            for b in iter(lambda: f.read(1 << 24), b''):
                h.update(b)
        json.dump({'size': os.path.getsize(sys.argv[2]), 'sha256': h.hexdigest()}, open(os.path.join(ROOT, 'tools', 'ref_iso.json'), 'w'))
        print('ref_iso.json yazildi')
    else:
        print(markdown())
