#!/usr/bin/env python3
"""Tek komutla tum zincir: validate_all -> build_patch -> build_fonts (gerekirse) -> build_pubgames
-> xdelta + dogrulama -> kurucu exe -> release/ oyuncu paketi (klasor + zip) -> SHA-256 ozeti.
Kullanim: python tools/build_all.py [--fonts] [--no-installer]
  --fonts: fontlari zorla yeniden uret;  --no-installer: kurucu derlenmez (Nuitka + MSVC gerekmez)
Herhangi bir adim basarisiz olursa zincir durur."""
import hashlib, os, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PY = sys.executable


def run(title, *args):
    print(f'\n##### {title} #####', flush=True)
    subprocess.check_call([PY, *args])


def sha(b):
    return hashlib.sha256(b).hexdigest()


font_probe = 'output/patch/data/language/en-uk/fonts/gui_normal.bft'
run('1. Dogrulama (validate_all)', 'tools/validate_all.py')
run('2. Yama (build_patch)', 'tools/build_patch.py')
if '--fonts' in sys.argv or not os.path.isfile(font_probe):
    run('3. Fontlar (build_fonts)', 'tools/build_fonts.py')
else:
    print('\n##### 3. Fontlar: mevcut, atlandi (--fonts ile zorla) #####')
run('4. Pub Games (build_pubgames)', 'tools/build_pubgames.py')

pr = ['tools/package_release.py'] + (['--no-installer'] if '--no-installer' in sys.argv else [])
run('5. xdelta + kurucu + oyuncu paketi (package_release)', *pr)

print('\n##### 6. SHA-256 ozeti #####')
rel = [d for d in sorted(os.listdir('release')) if d.startswith('Fable2_Turkce_Yama_v') and d.endswith('.zip')][-1]
lines = []
for f in ('release/' + rel, 'output/Fable2_Turkce_Kurulum/Fable2_Turkce_Kurulum.exe', 'output/extract_iso/extract_iso.exe'):
    if os.path.isfile(f):
        lines.append(f'{sha(open(f, "rb").read())}  {os.path.basename(f)}')
with zipfile.ZipFile('release/' + rel) as z:
    for n in sorted(z.namelist()):
        lines.append(f'    {sha(z.read(n))}  {rel}!{n}')
open('release/SHA256SUMS.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(l for l in lines if not l.startswith('    ')))
print('\nTum dosya ozetleri: release/SHA256SUMS.txt')
