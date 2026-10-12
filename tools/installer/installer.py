#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fable II Türkçe Yama — tek tık kurucu (Nuitka ile derlenir).

Adımlar: ISO doğrula -> çıkar -> yamayı uygula (xdelta + font + pubgames) -> Xenia config/yama ayarı -> shader önbelleği.
GUI (tkinter) varsayılan; test için:  --cli --iso X --target Y --xenia Z [--yes]
"""
import ctypes
import datetime
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import urllib.request

APP = 'Fable II Türkçe Kurulum'
TITLE_ID, MEDIA_ID = 0x4D5307F1, 0x716F0A0D
PATCH_URL = ('https://raw.githubusercontent.com/xenia-canary/game-patches/main/patches/'
             '4D5307F1%20-%20Fable%20II%20(GOTY_Platinum%20Edition).patch.toml')
PATCH_NAME = '4D5307F1 - Fable II (GOTY_Platinum Edition).patch.toml'
PATCH_HASH = '4145F96D2DEE2AB5'
WANT_PATCHES = ['Disable Texture Morphing', 'Disable MSAA', 'High Tick Rate']  # ad (öneki) eşleşmesi; "High Tick Rate" tam eşleşir

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
BASE = getattr(sys, '_MEIPASS', None) or os.path.join(HERE, 'stage')
RES = os.path.join(BASE, 'res')

import extract_iso as X  # noqa: E402


class Abort(Exception):
    pass


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ arayüz
def _p(*a):
    try:
        print(*a)
    except Exception:
        pass


class CliUI:
    def __init__(self, a):
        self.a = a

    def log(self, m): _p(m)
    def info(self, t, m): _p('[BİLGİ]', t, '-', m)
    def error(self, t, m): _p('[HATA]', t, '-', m)
    def yesno(self, t, m): _p('[SORU]', t, '-', m, '=> evet'); return True
    def retry(self, t, m):
        _p('[TEKRAR?]', t, '-', m)
        return False
    def pick_file(self, t, types): return self.a['iso']
    def pick_dir(self, t, key): return self.a[key]
    def progress(self, v): pass
    def done(self): pass


class GuiUI:
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk
        self.tk = tk
        self.root = tk.Tk()
        self.root.title(APP)
        self.root.geometry('760x480')
        self.txt = tk.Text(self.root, wrap='word', state='disabled', font=('Segoe UI', 10))
        self.txt.pack(fill='both', expand=True, padx=8, pady=(8, 4))
        self.bar = ttk.Progressbar(self.root, maximum=100)
        self.bar.pack(fill='x', padx=8, pady=(0, 8))
        self.root.protocol('WM_DELETE_WINDOW', self._close)
        self.closed = False

    def _close(self):
        self.closed = True
        os._exit(1)

    def _main(self, fn):
        """fn'i ana (Tk) iş parçacığında çalıştır, sonucu bekle."""
        res = {}
        ev = threading.Event()

        def run():
            try:
                res['v'] = fn()
            finally:
                ev.set()
        self.root.after(0, run)
        ev.wait()
        return res.get('v')

    def log(self, m):
        def f():
            self.txt.config(state='normal')
            self.txt.insert('end', m + '\n')
            self.txt.see('end')
            self.txt.config(state='disabled')
        self.root.after(0, f)

    def progress(self, v):
        self.root.after(0, lambda: self.bar.config(value=v))

    def info(self, t, m):
        from tkinter import messagebox
        self._main(lambda: messagebox.showinfo(t, m))

    def error(self, t, m):
        from tkinter import messagebox
        self._main(lambda: messagebox.showerror(t, m))

    def yesno(self, t, m):
        from tkinter import messagebox
        return self._main(lambda: messagebox.askyesno(t, m))

    def retry(self, t, m):
        from tkinter import messagebox
        return self._main(lambda: messagebox.askretrycancel(t, m))

    def pick_file(self, t, types):
        from tkinter import filedialog
        return self._main(lambda: filedialog.askopenfilename(title=t, filetypes=types))

    def pick_dir(self, t, key):
        from tkinter import filedialog
        return self._main(lambda: filedialog.askdirectory(title=t, mustexist=False))

    def done(self):
        pass

    def run(self, fn):
        def worker():
            try:
                fn()
            except Abort:
                pass
            except Exception as e:  # beklenmeyen
                self.error(APP, 'Beklenmeyen hata:\n%s\n\nKurulum raporunu ve bu mesajı geliştiriciye iletin.' % e)
            self.log('\nKapatabilirsiniz.')
            self.root.after(0, lambda: self.bar.config(value=100))
        threading.Thread(target=worker, daemon=True).start()
        self.root.mainloop()


# ------------------------------------------------------------------ ISO
def read_xex_ids(blob):
    """default.xex başından (Media ID, Title ID)."""
    if blob[:4] != b'XEX2':
        return None
    n = struct.unpack('>I', blob[0x14:0x18])[0]
    for k in range(n):
        i, v = struct.unpack('>II', blob[0x18 + 8 * k:0x20 + 8 * k])
        if i == 0x40006 and v + 16 <= len(blob):
            m, _ver, _bv, t = struct.unpack('>IIII', blob[v:v + 16])
            return m, t
    return None


def open_iso(path):
    f = open(path, 'rb')
    base, magic = X.find_partition(f)
    if base is None:
        f.close()
        return None
    f.seek(magic + 20)
    root_sector, root_size = struct.unpack('<II', f.read(8))
    return f, base, root_sector, root_size


def verify_iso(ui, iso):
    r = open_iso(iso)
    if r is None:
        ui.error(APP, 'Seçtiğiniz dosya bir Xbox 360 ISO\'su gibi görünmüyor.\n\nÇözüm: Fable II GOTY (Game of the Year / Platinum) ISO\'sunu seçtiğinizden emin olun. Dosya bozuk ya da eksik indirilmiş olabilir.')
        raise Abort()
    f, base, rs, rz = r
    try:
        f.seek(base + rs * X.SECTOR_SIZE)
        ents = X.parse_directory(f.read(rz))
        xe = [e for e in ents if e['name'].lower() == 'default.xex' and not e['is_dir']]
        if not xe:
            ui.error(APP, 'ISO içinde default.xex bulunamadı. Bu bir Xbox 360 oyun diski değil.')
            raise Abort()
        f.seek(base + xe[0]['sector'] * X.SECTOR_SIZE)
        ids = read_xex_ids(f.read(0x10000))
    finally:
        f.close()
    if ids is None:
        ui.error(APP, 'default.xex okunamadı. ISO bozuk olabilir; yeniden indirin/oluşturun.')
        raise Abort()
    media, title = ids
    ui.log('ISO: Title ID %08X, Media ID %08X' % (title, media))
    if title != TITLE_ID or media != MEDIA_ID:
        ui.error(APP, 'Bu ISO yamayla uyumlu değil.\n\nBulunan: Title ID %08X / Media ID %08X\nGereken: Title ID 4D5307F1 / Media ID 716F0A0D (Fable II GOTY, ABD/Avrupa diski).\n\nFarklı bir sürüm (başka bölge, ek yama, ya da Fable II normal sürümü) olabilir. Kurulum durduruldu; hiçbir şey değiştirilmedi.' % (title, media, ))
        raise Abort()
    return True


def extract_all(ui, iso, out):
    f, base, rs, rz = open_iso(iso)
    try:
        items = X.scan_all_files(f, base, rs, rz)
        files = [(p, e) for p, e in items if not e['is_dir']]
        total = sum(e['size'] for _, e in files) or 1
        done = 0
        outabs = os.path.abspath(out)
        for p, e in items:
            if e['is_dir']:
                tgt = os.path.abspath(os.path.join(out, p))
                if not tgt.startswith(outabs):
                    continue
                os.makedirs(tgt, exist_ok=True)
        t0 = time.time()
        last = 0
        for p, e in files:
            tgt = os.path.abspath(os.path.join(out, p))
            if not tgt.startswith(outabs):
                continue
            X.extract_file(f, base, e['sector'], e['size'], tgt)
            done += e['size']
            ui.progress(done * 70 / total)
            if time.time() - last > 5:
                ui.log('  çıkarılıyor... %%%d (%.0f MB)' % (done * 100 / total, done / 1048576))
                last = time.time()
        ui.log('Çıkarma bitti: %d dosya, %.1f GB, %.0f sn' % (len(files), done / 1073741824, time.time() - t0))
        return len(files)
    finally:
        f.close()


# ------------------------------------------------------------------ yama
def apply_patch(ui, target, manifest):
    """Her oyun dosyasina xdelta fark yamasi uygular; TAM yamali dosya dagitilmaz.
    Once dosyanin orijinal sha256 degeri, sonra uygulanan sonucun sha256 degeri dogrulanir."""
    files = manifest['files']
    tmpd = os.path.join(os.environ.get('TEMP', target), 'f2tr_xdelta')
    os.makedirs(tmpd, exist_ok=True)
    xd = os.path.join(tmpd, 'xdelta3.exe')
    shutil.copyfile(os.path.join(RES, 'xdelta3.exe'), xd)
    cf = 0x08000000 if os.name == 'nt' else 0
    for n, (rel, ent) in enumerate(sorted(files.items())):
        dst = os.path.join(target, rel.replace('/', os.sep))
        if not os.path.isfile(dst):
            ui.error(APP, '%s bulunamadı. Çıkarma yarım kalmış olabilir; hedef klasörü silip kurucuyu yeniden çalıştırın.' % rel)
            raise Abort()
        h = sha256(dst)
        if h == ent['patched_sha256']:
            ui.log('%s zaten yamalı; atlandı.' % rel)
            continue
        if h != ent['orig_sha256']:
            ui.error(APP, '%s orijinal sürümle eşleşmiyor (sha256 farklı). Yama uygulanamaz.\n\nÇözüm: farklı/değiştirilmiş bir oyun klasörü olabilir. Hedef olarak YENİ bir klasör seçip ISO\'dan yeniden çıkarın.' % rel)
            raise Abort()
        out = os.path.join(tmpd, 'yeni.bin')
        r = subprocess.run([xd, '-d', '-f', '-s', dst, os.path.join(RES, ent['delta'].replace('/', os.sep)), out],
                           capture_output=True, text=True, creationflags=cf)
        if r.returncode != 0 or not os.path.isfile(out):
            ui.error(APP, 'xdelta yamayı uygulayamadı (%s):\n%s\n\nAntivirüs xdelta3.exe\'yi engellemiş olabilir; geçici olarak kapatıp tekrar deneyin.' % (rel, r.stderr or r.stdout))
            raise Abort()
        if sha256(out) != ent['patched_sha256']:
            ui.error(APP, '%s için yama sonucu beklenen sha256 ile eşleşmedi; dosya değiştirilmedi.' % rel)
            raise Abort()
        shutil.move(out, dst)
        ui.log('%s yamalandı (xdelta, sha256 doğrulandı).' % rel)
        ui.progress(60 + int(20 * (n + 1) / len(files)))
    shutil.rmtree(tmpd, ignore_errors=True)
    ui.progress(80)
    ui.log('Doğrulama: %d dosyanın yama sonrası sha256 değeri beklenenle birebir aynı.' % len(files))
    xex = os.path.join(target, 'default.xex')
    xh = sha256(xex) if os.path.isfile(xex) else None
    return xh


# ------------------------------------------------------------------ Xenia
def xenia_running():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq xenia_canary.exe'], capture_output=True, text=True,
                             creationflags=0x08000000).stdout
        return 'xenia_canary.exe' in out.lower()
    except Exception:
        return False


def find_xenia_data(xdir):
    """(veri klasörü, config yolu) ya da (None, None). Xenia sırası: portable.txt -> exe yanındaki config -> Belgeler\\Xenia."""
    cfg = 'xenia-canary.config.toml'
    if os.path.isfile(os.path.join(xdir, 'portable.txt')) or os.path.isfile(os.path.join(xdir, cfg)):
        return xdir, os.path.join(xdir, cfg)
    docs = os.path.join(os.path.expanduser('~'), 'Documents', 'Xenia')
    try:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # CSIDL_PERSONAL
        docs = os.path.join(buf.value, 'Xenia')
    except Exception:
        pass
    if os.path.isfile(os.path.join(docs, cfg)):
        return docs, os.path.join(docs, cfg)
    return None, None


SECT = re.compile(r'^\s*\[([^\]]+)\]\s*(?:#.*)?$')


def edit_config(path, settings):
    """Yalnızca var olan anahtarların değerini değiştirir. (değişenler, atlananlar, değişmeyenler) döner."""
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    changed, skipped, same = [], [], []
    for sect, kv in settings.items():
        if sect.startswith('_'):
            continue
        for key, val in kv.items():
            cur = None
            found = False
            for n, ln in enumerate(lines):
                m = SECT.match(ln)
                if m:
                    cur = m.group(1).strip()
                    continue
                if cur != sect:
                    continue
                m = re.match(r'^(\s*' + re.escape(key) + r'\s*=\s*)("(?:[^"\\]|\\.)*"|[^\s#]+)(.*)$', ln)
                if m:
                    found = True
                    new = json_to_toml(val)
                    old = m.group(2)
                    if old == new:
                        same.append('[%s] %s = %s' % (sect, key, old))
                    else:
                        lines[n] = m.group(1) + new + m.group(3)
                        changed.append('[%s] %s: %s -> %s' % (sect, key, old, new))
                    break
            if not found:
                skipped.append('[%s] %s (config\'de yok, eklenmedi)' % (sect, key))
    out = nl.join(lines).encode('utf-8')
    if bom:
        out = b'\xef\xbb\xbf' + out
    with open(path, 'wb') as f:
        f.write(out)
    return changed, skipped, same


def json_to_toml(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    return '"%s"' % v


def edit_patches(path, want):
    """is_enabled değerlerini ad eşleşmesine göre ayarla. [(ad, durum)] döner."""
    raw = open(path, 'rb').read().decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in raw else '\n'
    lines = raw.split(nl)
    res = []
    cur = None
    idx = {}
    for n, ln in enumerate(lines):
        if ln.strip() == '[[patch]]':
            cur = None
        m = re.match(r'^\s*name\s*=\s*"(.*)"', ln)
        if m:
            cur = m.group(1)
        if re.match(r'^\s*is_enabled\s*=', ln) and cur is not None:
            idx[cur] = n
    for name, n in idx.items():
        on = any((name == w) if w == 'High Tick Rate' else name.startswith(w) for w in want)
        lines[n] = re.sub(r'(is_enabled\s*=\s*)(true|false)', lambda m: m.group(1) + ('true' if on else 'false'), lines[n])
        res.append((name, on))
    with open(path, 'wb') as f:
        f.write(nl.join(lines).encode('utf-8'))
    return res


def fetch_patch(ui, dst):
    try:
        req = urllib.request.Request(PATCH_URL, headers={'User-Agent': 'Fable2TR-Installer'})
        data = urllib.request.urlopen(req, timeout=25).read()
        if b'4D5307F1' not in data or PATCH_HASH.encode() not in data:
            raise ValueError('beklenmeyen içerik')
        with open(dst, 'wb') as f:
            f.write(data)
        return True
    except Exception as e:
        ui.log('Yama dosyası indirilemedi: %s' % e)
        return False


def clear_shader_cache(ui, ddir, rep):
    sh = os.path.join(ddir, 'cache_host', 'shaders')
    if not os.path.isdir(sh):
        rep.append('Shader önbelleği: bulunamadı (%s), temizlenecek bir şey yok.' % sh)
        return
    items = os.listdir(sh)
    if not items:
        rep.append('Shader önbelleği boş: %s' % sh)
        return
    if not os.path.abspath(sh).lower().endswith(os.path.join('cache_host', 'shaders').lower()):
        return
    if not ui.yesno(APP, 'Eski shader önbelleği temizlensin mi?\n\nSilinecek klasörün İÇERİĞİ:\n%s\n\n(Oyun kayıtlarınıza, profile ve yamalara dokunulmaz; önbellek oyun açılırken yeniden oluşur.)' % sh):
        rep.append('Shader önbelleği: kullanıcı silmeyi reddetti (%s).' % sh)
        return
    n = 0
    for it in items:
        p = os.path.join(sh, it)
        try:
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
            n += 1
        except Exception as e:
            ui.log('Silinemedi: %s (%s)' % (p, e))
    rep.append('Shader önbelleği temizlendi: %s (%d öğe silindi)' % (sh, n))


# ------------------------------------------------------------------ ana akış
def main_flow(ui, args):
    rep = ['Fable II Türkçe Kurulum Raporu', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '']
    manifest = json.load(open(os.path.join(RES, 'manifest.json'), encoding='utf-8'))
    settings = json.load(open(os.path.join(RES, 'xenia_settings.json'), encoding='utf-8'))
    ui.info(APP, 'Bu kurucu sırayla şunları yapar:\n1) Fable II ISO\'nuzu doğrular ve klasöre çıkarır\n2) Türkçe yamayı uygular\n3) Xenia Canary ayarlarını (altyazılar dahil) yapar\n\nİlk adım: ISO dosyanızı seçin.')
    # a) ISO
    iso = ui.pick_file('Fable II ISO dosyasını seçin', [('ISO dosyası', '*.iso'), ('Tüm dosyalar', '*.*')])
    if not iso:
        raise Abort()
    verify_iso(ui, iso)
    rep.append('ISO: %s (Title ID 4D5307F1, Media ID 716F0A0D doğrulandı)' % iso)
    # b) hedef
    target = ui.pick_dir('Oyunun çıkarılacağı HEDEF klasörü seçin (yaklaşık 8 GB boş yer gerekir)', 'target')
    if not target:
        raise Abort()
    target = os.path.abspath(target)
    os.makedirs(target, exist_ok=True)
    free = shutil.disk_usage(target).free
    if free < 9 * 1024 ** 3 and not os.path.isfile(os.path.join(target, 'default.xex')):
        ui.error(APP, 'Hedef sürücüde yeterli boş yer yok (%.1f GB var, ~9 GB gerekir). Başka bir klasör/sürücü seçin.' % (free / 1024 ** 3))
        raise Abort()
    if os.path.isfile(os.path.join(target, 'default.xex')):
        if not ui.yesno(APP, 'Bu klasörde zaten bir oyun çıkarılmış görünüyor:\n%s\n\nÜzerine yazılsın mı? (Hayır = çıkarma atlanır, yalnızca yama uygulanır)' % target):
            ui.log('Çıkarma atlandı (mevcut klasör kullanılıyor).')
        else:
            extract_all(ui, iso, target)
    else:
        ui.log('ISO çıkarılıyor, bu işlem birkaç dakika sürebilir...')
        extract_all(ui, iso, target)
    rep.append('Hedef klasör: %s' % target)
    # c) yama
    xh = apply_patch(ui, target, manifest)
    rep.append('Yama (xdelta) uygulandı ve sha256 ile doğrulandı (%d dosya).' % len(manifest['files']))
    xex_ok = (xh == manifest['xex_sha256'])
    rep.append('default.xex sha256: %s (%s)' % (xh, 'beklenen' if xex_ok else 'FARKLI'))
    if not xex_ok:
        ui.info(APP, 'Uyarı: default.xex beklenenden farklı. Xenia yama dosyası (hash 4145F96D2DEE2AB5) bu sürümde çalışmayabilir.')
    ui.progress(85)
    # d) Xenia
    ui.info(APP, 'Şimdi Xenia Canary klasörünü seçin (içinde xenia_canary.exe bulunan klasör).\n\nXenia\'yı henüz indirmediyseniz kurucuyu kapatın, Xenia Canary\'yi indirip açın ve kurucuyu tekrar çalıştırın. Oyun dosyaları ve yama hazır, tekrar çıkarmanız gerekmez.')
    while True:
        xdir = ui.pick_dir('Xenia Canary klasörünü seçin (xenia_canary.exe olan)', 'xenia')
        if not xdir:
            rep.append('Xenia: seçilmedi; yalnızca oyun dosyaları yamalandı.')
            finish(ui, rep, target)
            return
        if os.path.isfile(os.path.join(xdir, 'xenia_canary.exe')):
            break
        ui.error(APP, 'Seçilen klasörde xenia_canary.exe yok:\n%s\n\nXenia Canary\'yi indirdiğiniz klasörü seçin.' % xdir)
    while xenia_running():
        if not ui.retry(APP, 'Xenia şu anda çalışıyor. Xenia kapanırken ayar dosyasının üzerine yazdığı için önce KAPATIN, sonra Tekrar Dene\'ye basın.'):
            raise Abort()
    while True:
        ddir, cfg = find_xenia_data(xdir)
        if cfg and os.path.isfile(cfg):
            break
        if not ui.retry(APP, 'Xenia\'nın ayar dosyası (xenia-canary.config.toml) henüz yok.\n\nXenia\'yı bir kez açıp kapatın, sonra Tekrar Dene\'ye basın.'):
            rep.append('Xenia ayar dosyası bulunamadı; Xenia ayarı yapılmadı (README_TR.md\'deki elle kurulum bölümüne bakın).')
            finish(ui, rep, target)
            return
        while xenia_running():
            if not ui.retry(APP, 'Xenia hâlâ çalışıyor, kapatıp Tekrar Dene\'ye basın.'):
                raise Abort()
    rep.append('Xenia: %s | veri klasörü: %s' % (xdir, ddir))
    ui.log('Xenia veri klasörü: %s' % ddir)
    # f) config
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    bak = cfg + '.yedek-' + stamp
    shutil.copyfile(cfg, bak)
    ui.log('Config yedeği: %s' % bak)
    rep.append('Config yedeği: %s' % bak)
    changed, skipped, same = edit_config(cfg, settings)
    ui.log('\nConfig değişiklikleri (eski -> yeni):')
    rep.append('Config değişiklikleri:')
    for c in changed:
        ui.log('  ' + c)
        rep.append('  ' + c)
    for c in same:
        rep.append('  (zaten ayarlı) ' + c)
    for c in skipped:
        ui.log('  ATLANDI: ' + c)
        rep.append('  ATLANDI: ' + c)
    if not changed:
        ui.log('  (değişiklik gerekmedi)')
    # g) yamalar
    pdir = os.path.join(ddir, 'patches')
    os.makedirs(pdir, exist_ok=True)
    ppath = os.path.join(pdir, PATCH_NAME)
    if os.path.isfile(ppath):
        pb = ppath + '.yedek-' + stamp
        shutil.copyfile(ppath, pb)
        rep.append('Mevcut yama dosyası yedeklendi: %s' % pb)
    got = fetch_patch(ui, ppath) or os.path.isfile(ppath)
    if got:
        res = edit_patches(ppath, WANT_PATCHES)
        on = [n for n, v in res if v]
        rep.append('Xenia yamaları (%s): açık: %s' % (ppath, ', '.join(on) if on else 'yok'))
        rep.append('  kapalı: ' + ', '.join(n for n, v in res if not v))
        ui.log('Açılan Xenia yamaları: ' + ', '.join(on))
        missing = [w for w in WANT_PATCHES if not any((n == w) if w == 'High Tick Rate' else n.startswith(w) for n, _ in res)]
        if missing:
            rep.append('  UYARI: dosyada bulunamayan yamalar: ' + ', '.join(missing))
        if not xex_ok:
            rep.append('  UYARI: default.xex farklı, yamalar uygulanmayabilir.')
    else:
        msg = ('Xenia yama dosyası internetten indirilemedi.\n\nElle kurulum: https://github.com/xenia-canary/game-patches/tree/main/patches adresinden\n"%s"\ndosyasını indirip şu klasöre koyun:\n%s\nsonra içinde %s yamalarını is_enabled = true yapın.' % (PATCH_NAME, pdir, ', '.join(WANT_PATCHES)))
        ui.info(APP, msg)
        rep.append('Yama dosyası indirilemedi (internet yok?). Elle kurulum:\n' + msg)
    ui.progress(95)
    # h) shader
    clear_shader_cache(ui, ddir, rep)
    finish(ui, rep, target)


def finish(ui, rep, target):
    ui.progress(100)
    rp = os.path.join(target, 'kurulum_raporu.txt')
    rep.append('')
    rep.append('Xenia\'da %s açın. Oyunda Seçenekler -> Dil = English (United Kingdom) seçili olsun.' % os.path.join(target, 'default.xex'))
    with open(rp, 'w', encoding='utf-8-sig') as f:
        f.write('\r\n'.join(rep) + '\r\n')
    ui.log('\nKurulum raporu: ' + rp)
    ui.info(APP, 'Kurulum tamamlandı!\n\nXenia\'da şu dosyayı açın:\n%s\n\nOyunda Seçenekler → Dil = English (United Kingdom) seçili olsun.\nAltyazılar için ayar otomatik yapıldı.\n\nKurulum raporu: %s' % (os.path.join(target, 'default.xex'), rp))


class _RecUI:
    """Kendi kendine test icin sessiz arayuz: mesajlari listeye yazar."""
    def __init__(self):
        self.lines = []

    def log(self, m): self.lines.append(m)
    def info(self, t, m): self.lines.append('INFO ' + m)
    def error(self, t, m): self.lines.append('HATA ' + m)
    def progress(self, v): pass


def selftest(a):
    """--selftest [OYUN_KLASORU] --out DOSYA : paketlenmis kaynaklari ve (klasor verilirse) yama uygulamayi dener.
    Derleme yontemleri (PyInstaller/Nuitka vb.) karsilastirilirken ayni islevi gordugunu dogrulamak icindir."""
    out = a[a.index('--out') + 1] if '--out' in a else None
    gdir = None
    i = a.index('--selftest')
    if i + 1 < len(a) and not a[i + 1].startswith('--'):
        gdir = a[i + 1]
    ui = _RecUI()
    ok = True
    try:
        manifest = json.load(open(os.path.join(RES, 'manifest.json'), encoding='utf-8'))
        ui.log('manifest: %d dosya' % len(manifest['files']))
        for rel, e in manifest['files'].items():
            p = os.path.join(RES, e['delta'].replace('/', os.sep))
            if not (os.path.isfile(p) and os.path.getsize(p) > 0):
                ok = False
                ui.log('EKSIK delta: ' + rel)
        json.load(open(os.path.join(RES, 'xenia_settings.json'), encoding='utf-8'))
        tmpd = os.path.join(os.environ.get('TEMP', '.'), 'f2tr_selftest')
        os.makedirs(tmpd, exist_ok=True)
        xd = os.path.join(tmpd, 'xdelta3.exe')
        shutil.copyfile(os.path.join(RES, 'xdelta3.exe'), xd)
        r = subprocess.run([xd, '-V'], capture_output=True, text=True, creationflags=0x08000000 if os.name == 'nt' else 0)
        ui.log('xdelta3 -V -> %d %s' % (r.returncode, (r.stdout + r.stderr).strip().splitlines()[0] if (r.stdout + r.stderr).strip() else ''))
        ok = ok and r.returncode == 0
        import tkinter
        _r = tkinter.Tk()
        _r.withdraw()
        _r.update()
        _r.destroy()
        ui.log('tkinter: Tk penceresi olusturuldu')
        ui.log('extract_iso modulu: ' + str(hasattr(X, 'scan_all_files')))
        if gdir:
            xh = apply_patch(ui, gdir, manifest)
            ui.log('apply_patch tamam, default.xex sha256 ' + str(xh)[:12])
    except Abort:
        ok = False
    except Exception as e:  # noqa: BLE001
        ok = False
        import traceback
        ui.log('ISTISNA %r' % (e,))
        ui.log(traceback.format_exc())
    ui.log('SONUC ' + ('OK' if ok else 'BASARISIZ'))
    if out:
        open(out, 'w', encoding='utf-8').write('\n'.join(ui.lines) + '\n')
    return 0 if ok else 1


def check_install_dir():
    """Kurucu zip'in icinden ya da eksik dosyalarla calistirildiysa anlasilir Turkce hata verir; sorun yoksa None doner."""
    here = os.path.normpath(HERE).lower()
    problem = None
    if 'temp1_' in here or ('.zip' + os.sep) in here:
        problem = 'Kurucu zip dosyasının içinden çalıştırılmış gibi görünüyor.'
    else:
        need = ['manifest.json', 'xdelta3.exe', 'xenia_settings.json']
        miss = [n for n in need if not os.path.isfile(os.path.join(RES, n))]
        try:
            man = json.load(open(os.path.join(RES, 'manifest.json'), encoding='utf-8'))
            miss += [e['delta'] for e in man['files'].values() if not os.path.isfile(os.path.join(RES, e['delta'].replace('/', os.sep)))]
        except Exception:
            pass
        if miss:
            problem = 'Kurucunun yanında gerekli dosyalar eksik (%d dosya, ör. %s).' % (len(miss), miss[0])
    if problem:
        return (problem + '\n\nLütfen zip\'i önce bir klasöre çıkarın (sağ tık → Tümünü ayıkla), sonra çıkan "Kurulum" klasöründeki '
                'Fable2_Turkce_Kurulum.exe dosyasını çalıştırın.\nKurulum klasöründeki dosyaları silmeyin veya ayırmayın; '
                'exe yalnızca klasörün içinde çalışır.')
    return None


def main():
    a = sys.argv[1:]
    if '--selftest' in a:
        sys.exit(selftest(a))
    msg = check_install_dir()
    if msg:
        if '--cli' in a:
            _p('[HATA]', msg)
        else:
            import tkinter
            from tkinter import messagebox
            r = tkinter.Tk()
            r.withdraw()
            messagebox.showerror(APP, msg)
        sys.exit(3)
    if '--cli' in a:
        d = {'iso': a[a.index('--iso') + 1], 'target': a[a.index('--target') + 1], 'xenia': a[a.index('--xenia') + 1]}
        ui = CliUI(d)
        try:
            main_flow(ui, d)
        except Abort:
            _p('Kurulum iptal edildi.')
            sys.exit(2)
        return
    ui = GuiUI()
    ui.run(lambda: main_flow(ui, {}))


if __name__ == '__main__':
    main()
