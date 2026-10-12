#!/usr/bin/env python3
"""Kisinin KENDI oyun kopyasindan Ingilizce kaynak metni cikarir (depoda Ingilizce metin YOKTUR).

Uretilen dosyalar (hepsi .gitignore'da, commit EDILMEZ):
  work/extracted_babel/book_en_strings.json, book_en_meta.json, book_en_tail.bin
  translation/source.json              (banka bazli kaynak; validate_all.py icin)
  translation/pubgames_src/*.json      (Pub Games kaynak metinleri)
Kullanim:  python tools/extract_source.py [--game extracted_original]
  --game: ISO'dan cikarilmis Fable II GOTY klasoru (icinde default.xex ve data/ olan).
"""
import argparse, glob, hashlib, json, os, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_SHA256 = '437636e2cf4ca9bf3eaf5109bd2867998f2352ae8a6c901b698e2992bf64e4e7'   # Fable II GOTY (Media ID 716F0A0D) en-uk/text/book.babel


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=os.path.join(ROOT, 'extracted_original'))
    a = ap.parse_args()
    game = os.path.abspath(a.game)
    book = os.path.join(game, 'data', 'language', 'en-uk', 'text', 'book.babel')
    if not os.path.isfile(book):
        sys.exit('[HATA] %s yok. Once ISO\'yu cikarin (tools/extract_iso.py) ve --game ile klasoru gosterin.' % book)
    if sha(book) != BOOK_SHA256:
        sys.exit('[HATA] book.babel beklenen (orijinal GOTY) surumle ayni degil; baska surum ya da degistirilmis dosya.')
    os.chdir(ROOT)
    out = os.path.join(ROOT, 'work', 'extracted_babel')
    subprocess.check_call([sys.executable, 'tools/babel_extract.py', book, '-o', out, '-p', 'book_en'])
    # prepare_translation.py progress.json'u da yazar; depodaki dosyayi bozmamak icin gecici klasorde calistirilir
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(out, os.path.join(td, 'work', 'extracted_babel'))
        os.makedirs(os.path.join(td, 'translation', 'banks'))
        subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'prepare_translation.py')], cwd=td)
        shutil.copyfile(os.path.join(td, 'translation', 'source.json'), os.path.join(ROOT, 'translation', 'source.json'))
    print('translation/source.json yazildi')
    os.makedirs(os.path.join(ROOT, 'translation', 'pubgames_src'), exist_ok=True)
    for g in ('common', 'keystone', 'magedice', 'wizardstower'):
        p = os.path.join(game, 'data', 'pubgames', g, 'localization.en.xml')
        content = open(p, 'r', encoding='utf-16').read().replace('encoding="unicodeFFFE"', 'encoding="utf-8"')
        root = ET.fromstring(content.encode('utf-8'))
        items = []
        for d in root.findall('.//data'):
            v = d.find('value')
            items.append({'id': d.get('id'), 'text': v.text if v is not None else ''})
        json.dump(items, open(os.path.join(ROOT, 'translation', 'pubgames_src', g + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
    print('Kaynak metin hazir. Simdi: python tools/build_all.py')


if __name__ == '__main__':
    main()
