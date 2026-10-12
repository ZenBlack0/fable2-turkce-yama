#!/usr/bin/env python3
"""Oyuncu paketi: release/Fable2_Turkce_Yama_v<surum>/ klasoru ve ayni adli zip.
Icerik: kurucu exe, OKUBENI.txt, Elle_Kurulum/ (xdelta fark yamalari + bat), SHA256SUMS.txt.
Hicbir pakete oyunun orijinal ya da degistirilmis TAM dosyasi konmaz; yalnizca xdelta fark yamalari.
Her calistirmada xdelta yeniden uretilip dogrulanir (make_xdelta). --no-installer: exe derlenmez/konmaz."""
import hashlib, json, os, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from make_xdelta import make_xdelta  # noqa: E402

VERSION = '1.0.0'
REPO_URL = 'https://github.com/ZenBlack0/fable2-turkce-yama'
NAME = f'Fable2_Turkce_Yama_v{VERSION}'
REL = os.path.join('release', NAME)
SKIP_INSTALLER = '--no-installer' in sys.argv


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


print('=== Fable II Türkçe Yama Paketleme ===')
man = make_xdelta()          # fark yamalari + dogrulama (basarisizsa durur)
if not SKIP_INSTALLER:
    subprocess.check_call([sys.executable, 'tools/installer/build_installer.py'])

shutil.rmtree(REL, ignore_errors=True)
os.makedirs(REL)
elle = os.path.join(REL, 'Elle_Kurulum')
os.makedirs(elle)
shutil.copytree('output/deltas', os.path.join(elle, 'deltas'), ignore=shutil.ignore_patterns('manifest.json'))
shutil.copy('tools/bin/xdelta3.exe', elle)
shutil.copy('tools/installer/LISANSLAR.txt', elle)
if os.path.isfile('output/extract_iso.exe'):
    shutil.copy('output/extract_iso.exe', elle)
if not SKIP_INSTALLER:
    shutil.copy('output/Fable2_Turkce_Kurulum.exe', REL)


def fill(t):
    return t.replace('@VERSION@', VERSION).replace('@REPO_URL@', REPO_URL)


for src, dst in (('OKUBENI.txt', REL), ('ELLE_KURULUM.txt', elle)):
    t = fill(open(f'tools/release_templates/{src}', encoding='utf-8').read())
    open(os.path.join(dst, src), 'w', encoding='utf-8-sig', newline='').write(t.replace('\n', '\r\n'))

# yama_uygula.bat: her dosya icin orijinal hash dogrula -> yedekle -> xdelta -> sonuc hash dogrula
calls = []
for rel, e in sorted(man['files'].items()):
    calls.append('call :apply "%s" %s %s' % (rel.replace('/', chr(92)), e['orig_sha256'], e['patched_sha256']))
    calls.append('if errorlevel 1 exit /b 1')
bat = r'''@echo off
setlocal
chcp 65001 > nul
echo ========================================================
echo   Fable II Turkce Yama - elle kurulum (xdelta)
echo ========================================================
set "GAME=%~1"
if "%GAME%"=="" set "GAME=%CD%"
if not exist "%GAME%\default.xex" (
    echo [HATA] "%GAME%" icinde default.xex yok.
    echo Oyun klasorunu ^(ISO'dan cikardiginiz klasoru^) bu .bat dosyasinin uzerine suruklayin
    echo ya da: yama_uygula.bat D:\Fable2
    pause
    exit /b 1
)
if not exist "%~dp0xdelta3.exe" ( echo [HATA] xdelta3.exe yok & pause & exit /b 1 )
@CALLS@
echo.
echo [BASARILI] Tum dosyalar yamalandi ve dogrulandi.
echo Xenia'da default.xex dosyasini acin; oyunda Dil = English ^(United Kingdom^).
pause
exit /b 0

:hash
set "%~2="
for /f "skip=1 delims=" %%H in ('certutil -hashfile "%~1" SHA256') do if not defined %~2 set "%~2=%%H"
set "%~2=!%~2: =!"
exit /b 0

:apply
setlocal enabledelayedexpansion
set "F=%GAME%\%~1"
set "OLDH=%~2"
set "NEWH=%~3"
if not exist "!F!" ( echo [HATA] Dosya yok: !F! & pause & exit /b 1 )
call :hash "!F!" H
if /i "!H!"=="!NEWH!" ( echo Zaten yamali: %~1 & endlocal & exit /b 0 )
if not exist "!F!.bak" (
    if /i not "!H!"=="!OLDH!" ( echo [HATA] %~1 orijinal surumle eslesmiyor ^(sha256 farkli^). Yeni bir klasore yeniden cikarin. & pause & exit /b 1 )
    copy /y "!F!" "!F!.bak" > nul
)
call :hash "!F!.bak" H
if /i not "!H!"=="!OLDH!" ( echo [HATA] %~1.bak orijinal degil. & pause & exit /b 1 )
"%~dp0xdelta3.exe" -d -f -s "!F!.bak" "%~dp0deltas\%~1.xdelta" "!F!"
if errorlevel 1 ( echo [HATA] xdelta uygulanamadi: %~1 & copy /y "!F!.bak" "!F!" > nul & pause & exit /b 1 )
call :hash "!F!" H
if /i not "!H!"=="!NEWH!" ( echo [HATA] Sonuc dogrulanamadi: %~1 & copy /y "!F!.bak" "!F!" > nul & pause & exit /b 1 )
echo Yamalandi ^(sha256 dogrulandi^): %~1
endlocal & exit /b 0
'''.replace('@CALLS@', '\n'.join(calls)).replace('setlocal\nchcp', 'setlocal enabledelayedexpansion\nchcp')
open(os.path.join(elle, 'yama_uygula.bat'), 'w', encoding='ascii', newline='').write(bat.replace('\n', '\r\n'))

# SHA256SUMS.txt
lines = []
for root, _, fs in os.walk(REL):
    for f in sorted(fs):
        p = os.path.join(root, f)
        lines.append('%s  %s' % (sha(p), os.path.relpath(p, REL).replace(os.sep, '/')))
lines.sort(key=lambda l: l.split('  ', 1)[1])
open(os.path.join(REL, 'SHA256SUMS.txt'), 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')

zp = REL + '.zip'
if os.path.exists(zp):
    os.remove(zp)
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, fs in os.walk(REL):
        for f in sorted(fs):
            p = os.path.join(root, f)
            z.write(p, os.path.join(NAME, os.path.relpath(p, REL)))
print(f'Paket: {zp} ({os.path.getsize(zp):,} bayt)')
with zipfile.ZipFile(zp) as z:
    for i in z.infolist():
        print(f'  {i.filename}  {i.file_size:,}')
