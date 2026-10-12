#!/usr/bin/env python3
"""Yayin paketlerinde / depoda telifli oyun verisi ve Ingilizce metin dokumu kalmadigini dogrular.

Kontroller (hicbiri gecmezse cikis kodu 1):
 1. Yasakli dosya adi/uzantisi: *.xex *.bnk *.iso *.xma *.wav *.dds *.xpr *.babel *.bft(yalniz TAM dosya) ...
 2. Hash: hicbir dosya, oyunun orijinal dosyalarinin (extracted_original: .babel .bft .xml .xex .bnk) SHA-256 degeriyle ayni olamaz
    (ayrica yamali output/patch dosyalariyla da ayni olamaz).
 3. Ingilizce metin: oyunun Ingilizce metin kumesiyle (work/extracted_babel/book_en_strings.json + pubgames_src)
    birebir ortusen >=40 karakterlik deger/satir sayisi esigi asarsa isaretlenir.
 4. Zip'lerin icindeki dosyalar ayni kurallarla (bellekte) taranir.
Kullanim: python tools/scan_release.py <klasor|zip> [...]   (EN kaynak yoksa 3. kontrol atlanir ve belirtilir)"""
import glob, hashlib, json, os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD_EXT = {'.xex', '.bnk', '.iso', '.xma', '.wav', '.dds', '.xpr', '.babel', '.xur', '.xnb', '.bin'}
TEXT_EXT = {'.json', '.md', '.txt', '.py', '.bat', '.ps1', '.toml', '.yml', '.yaml', '.csv', '.xml', '.html'}
MIN_LEN = 40
THRESH = 3


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def load_refs():
    hashes = {}
    for pat in ('data/language/**/*.babel', 'data/language/**/*.bft', 'data/pubgames/**/*.xml', 'default.xex', 'data/*.bnk'):
        for p in glob.glob(os.path.join(ROOT, 'extracted_original', pat), recursive=True):
            hashes[sha_b(open(p, 'rb').read())] = os.path.relpath(p, os.path.join(ROOT, 'extracted_original'))
    for p in glob.glob(os.path.join(ROOT, 'output/patch/**/*.*'), recursive=True):
        if os.path.isfile(p):
            hashes[sha_b(open(p, 'rb').read())] = 'output/patch/' + os.path.relpath(p, os.path.join(ROOT, 'output/patch'))
    en = set()
    f = os.path.join(ROOT, 'work/extracted_babel/book_en_strings.json')
    if os.path.isfile(f):
        for s in json.load(open(f, encoding='utf-8')):
            for part in s['text'].split('\n'):
                if len(part.strip()) >= MIN_LEN:
                    en.add(part.strip())
            if len(s['text'].strip()) >= MIN_LEN:
                en.add(s['text'].strip())
    for p in glob.glob(os.path.join(ROOT, 'translation/pubgames_src/*.json')):
        for it in json.load(open(p, encoding='utf-8')):
            t = (it.get('text') or '').strip()
            if len(t) >= MIN_LEN:
                en.add(t)
    return hashes, en


def strings_of(name, data):
    """Metin dosyasindan karsilastirilacak degerler: JSON ise tum string degerler, degilse satirlar."""
    try:
        txt = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return []
    out = []
    if name.lower().endswith('.json'):
        try:
            def walk(o):
                if isinstance(o, str):
                    out.append(o.strip())
                    out.extend(x.strip() for x in o.split('\n'))
                elif isinstance(o, dict):
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(json.loads(txt))
            return out
        except Exception:
            pass
    return [l.strip() for l in txt.splitlines()]


def check(name, data, hashes, en, problems, stats):
    ext = os.path.splitext(name)[1].lower()
    base = os.path.basename(name).lower()
    stats['files'] += 1
    if ext in BAD_EXT:
        problems.append(f'YASAKLI UZANTI: {name}')
    h = sha_b(data)
    if h in hashes:
        problems.append(f'ORIJINAL/YAMALI TAM DOSYA (hash eslesti: {hashes[h]}): {name}')
    if ext == '.bft' and not name.endswith('.xdelta'):
        problems.append(f'TAM .bft dosyasi: {name}')
    if en and (ext in TEXT_EXT):
        hit = [s for s in strings_of(name, data) if s in en]
        if len(set(hit)) >= THRESH:
            problems.append(f'INGILIZCE METIN ({len(set(hit))} eslesme, ornek: "{sorted(set(hit))[0][:60]}"): {name}')
        stats['en_hits'] += len(set(hit))


def scan(target, hashes, en, problems, stats):
    if os.path.isdir(target):
        for root, dirs, fs in os.walk(target):
            dirs[:] = [d for d in dirs if d != '.git']
            for f in fs:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, target).replace(os.sep, '/')
                data = open(p, 'rb').read()
                if f.lower().endswith('.zip'):
                    scan_zip(p, hashes, en, problems, stats)
                check(rel, data, hashes, en, problems, stats)
    elif target.lower().endswith('.zip'):
        scan_zip(target, hashes, en, problems, stats)


def scan_zip(path, hashes, en, problems, stats):
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            if not i.is_dir():
                check(os.path.basename(path) + '!' + i.filename, z.read(i), hashes, en, problems, stats)


def main():
    targets = sys.argv[1:]
    if not targets:
        sys.exit(__doc__)
    hashes, en = load_refs()
    print(f'Referans: {len(hashes)} orijinal/yamali dosya hash\'i, {len(en)} Ingilizce metin parcasi'
          + ('' if en else '  (UYARI: EN kaynak yok, metin kontrolu atlandi)'))
    bad = 0
    for t in targets:
        problems, stats = [], {'files': 0, 'en_hits': 0}
        scan(t, hashes, en, problems, stats)
        print(f'\n== {t}: {stats["files"]} dosya taranidi, {stats["en_hits"]} tekil EN eslesmesi (esik: dosya basina {THRESH})')
        for p in problems:
            print('  [SORUN]', p)
        print('  SONUC:', 'TEMIZ' if not problems else f'{len(problems)} SORUN')
        bad += len(problems)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
