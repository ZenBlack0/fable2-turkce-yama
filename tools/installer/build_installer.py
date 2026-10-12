#!/usr/bin/env python3
"""Kurucuyu derler: manifest + kaynaklar -> tools/installer/stage/res, sonra PyInstaller ile tek dosya exe.
Çıktı: output/Fable2_Turkce_Kurulum.exe ve output/extract_iso.exe
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
# kurucu
sep = ';'
cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--noconsole', '--name', 'Fable2_Turkce_Kurulum',
       '--paths', 'tools', '--add-data', os.path.abspath(RES) + sep + 'res',
       '--distpath', 'output', '--workpath', 'work/pyi', '--specpath', 'work/pyi', INS + '/installer.py']
subprocess.check_call(cmd)
# ISO çıkarıcı (komut satırı)
subprocess.check_call([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--name', 'extract_iso',
                       '--distpath', 'output', '--workpath', 'work/pyi', '--specpath', 'work/pyi', 'tools/extract_iso.py'])
print('tamam')
