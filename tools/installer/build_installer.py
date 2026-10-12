#!/usr/bin/env python3
"""Kurucuyu derler: manifest + kaynaklar -> tools/installer/stage/res, sonra Nuitka --standalone ile klasor (exe + dll'ler).
Çıktı: output/Fable2_Turkce_Kurulum/ (Fable2_Turkce_Kurulum.exe) ve output/extract_iso/ (extract_iso.exe)
Önkoşul: output/deltas güncel olmalı (make_xdelta.py)."""
import hashlib, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
INS = 'tools/installer'
STAGE = INS + '/stage'
RES = STAGE + '/res'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


shutil.rmtree(STAGE, ignore_errors=True)
os.makedirs(RES)
# Yalnizca xdelta fark yamalari (TAM oyun dosyasi YOK) + manifest (orijinal/yamali sha256)
man = json.load(open('output/deltas/manifest.json', encoding='utf-8'))
shutil.copytree('output/deltas', RES + '/deltas', ignore=shutil.ignore_patterns('manifest.json'))
json.dump(man, open(RES + '/manifest.json', 'w', encoding='utf-8'), indent=1)
shutil.copyfile('tools/bin/xdelta3.exe', RES + '/xdelta3.exe')
shutil.copyfile(INS + '/xenia_settings.json', RES + '/xenia_settings.json')
# Nuitka --standalone (PyInstaller exe'leri antivirus ML motorlarinda daha cok yanlis alarm veriyordu; bkz. docs/antivirus.md)
# Onkosul: pip install nuitka ordered-set zstandard ve Visual Studio Build Tools (MSVC)
env = dict(os.environ, PYTHONPATH=os.path.abspath('tools'))
NAME = 'Fable2_Turkce_Kurulum'
d = os.path.abspath('work/nuitka_installer')
shutil.rmtree(d, ignore_errors=True)
common = ['--assume-yes-for-downloads', '--windows-console-mode=disable', '--company-name=ZenBlack0',
          '--product-name=Fable_II_Turkce_Yama', '--file-version=1.0.1.0', '--product-version=1.0.1.0', '--msvc=latest']
subprocess.check_call([sys.executable, '-m', 'nuitka', '--standalone', '--include-package=tkinter', '--include-module=_tkinter',
                       '--include-module=extract_iso', '--include-data-dir=%s=stage/res' % os.path.abspath(RES),
                       '--include-data-files=%s=stage/res/xdelta3.exe' % os.path.abspath(RES + '/xdelta3.exe'),  # data-dir .exe/.dll atlar
                       '--file-description=Fable_II_Turkce_Yama_Kurucusu', '--output-filename=%s.exe' % NAME,
                       '--output-dir=' + d + '/inst'] + common + [INS + '/installer.py'], env=env)
shutil.rmtree('output/' + NAME, ignore_errors=True)
shutil.copytree(d + '/inst/installer.dist', 'output/' + NAME)
# ISO cikarici (komut satiri, ayri klasor)
subprocess.check_call([sys.executable, '-m', 'nuitka', '--standalone', '--windows-console-mode=force', '--output-filename=extract_iso.exe',
                       '--file-description=Fable_II_ISO_Cikarici', '--output-dir=' + d + '/iso'] + common + ['tools/extract_iso.py'], env=env)
shutil.rmtree('output/extract_iso', ignore_errors=True)
shutil.copytree(d + '/iso/extract_iso.dist', 'output/extract_iso')
print('tamam')
