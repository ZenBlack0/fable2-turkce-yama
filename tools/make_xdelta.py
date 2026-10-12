#!/usr/bin/env python3
"""Oyunun orijinal dosyalarindan yamali dosyalara xdelta FARK yamalari uretir ve dogrular.

Dagitima orijinal ya da degistirilmis TAM oyun dosyasi konmaz; yalnizca fark yamalari dagitilir.
Cikti: output/deltas/<oyun icindeki yol>.xdelta  ve  output/deltas/manifest.json
  manifest: her dosya icin orijinal sha256, yamali sha256, delta yolu/boyutu (+ default.xex sha256).
Dogrulama: her delta orijinale uygulanir; sonuc output/patch'teki dosyayla sha256 olarak
karsilastirilir. Eslesmezse hata verip durur."""
import hashlib, json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_DIR = os.path.join(ROOT, 'extracted_original')
PATCH_DIR = os.path.join(ROOT, 'output/patch')
OUT = os.path.join(ROOT, 'output/deltas')
EXE = os.path.join(ROOT, 'tools/bin/xdelta3.exe')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def make_xdelta():
    if not os.path.isfile(EXE):
        sys.exit(f'[HATA] xdelta3.exe yok: {EXE}  (https://github.com/jmacd/xdelta-gpl/releases adresinden xdelta3 3.x Windows exe indirip tools/bin/xdelta3.exe olarak kaydedin)')
    rels = []
    for root, _, fs in os.walk(PATCH_DIR):
        for f in fs:
            rels.append(os.path.relpath(os.path.join(root, f), PATCH_DIR).replace(os.sep, '/'))
    rels.sort()
    if not rels:
        sys.exit('[HATA] output/patch bos; once build_patch/build_fonts/build_pubgames calistirin.')
    import shutil
    shutil.rmtree(OUT, ignore_errors=True)
    files = {}
    with tempfile.TemporaryDirectory() as td:
        for rel in rels:
            orig = os.path.join(ORIG_DIR, rel)
            new = os.path.join(PATCH_DIR, rel)
            if not os.path.isfile(orig):
                sys.exit(f'[HATA] orijinal dosya yok: {orig}')
            dlt = os.path.join(OUT, rel + '.xdelta')
            os.makedirs(os.path.dirname(dlt), exist_ok=True)
            subprocess.check_call([EXE, '-e', '-9', '-f', '-s', orig, new, dlt])
            tmp = os.path.join(td, 'v.bin')
            subprocess.check_call([EXE, '-d', '-f', '-s', orig, dlt, tmp])
            a, b = sha(tmp), sha(new)
            os.remove(tmp)
            if a != b:
                sys.exit(f'[HATA] xdelta dogrulamasi basarisiz ({rel}): uygulanan {a[:12]} != patch {b[:12]}')
            files[rel] = {'orig_sha256': sha(orig), 'patched_sha256': b,
                          'delta': 'deltas/' + rel + '.xdelta', 'delta_size': os.path.getsize(dlt)}
            print(f'  {rel}: delta {files[rel]["delta_size"]:,} bayt, dogrulandi {b[:12]}')
    man = {'files': files, 'xex_sha256': sha(os.path.join(ORIG_DIR, 'default.xex'))}
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'), indent=1)
    print(f'xdelta tamam: {len(files)} dosya, hepsi dogrulandi.')
    return man


if __name__ == '__main__':
    make_xdelta()
