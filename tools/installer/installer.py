#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fable II Türkçe Yama — tek tık kurucu (Nuitka ile derlenir).

Adımlar: ISO doğrula -> çıkar -> yamayı uygula (xdelta, SHA-256 doğrulamalı) -> (izin verilirse) Xenia'da TEK ayar:
render_target_path_d3d12 = "rov" (altyazılar için; bkz. xenia_rov.py). Başka hiçbir Xenia ayarına/yamasına/önbelleğine dokunulmaz.
GUI (tkinter) varsayılan; test için:  --cli --iso X --target Y [--xenia KLASOR] [--xenia-rov evet|hayir|sor]
"""
import datetime
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import threading
import time

APP = 'Fable II Türkçe Kurulum'
TITLE_ID, MEDIA_ID = 0x4D5307F1, 0x716F0A0D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
BASE = getattr(sys, '_MEIPASS', None) or os.path.join(HERE, 'stage')
RES = os.path.join(BASE, 'res')

import xenia_rov  # noqa: E402

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
    def warn(self, t, m): _p('[UYARI]', t, '-', m)
    def yesno(self, t, m): _p('[SORU]', t, '-', m, '=> evet'); return True

    def ask_rov(self, m):
        """--xenia-rov evet|hayir|sor (varsayılan sor: terminalde sorar; etkileşimli değilse hayır sayılır)."""
        mode = self.a.get('xenia_rov', 'sor')
        if mode in ('evet', 'hayir'):
            return mode == 'evet'
        if sys.stdin is not None and sys.stdin.isatty():
            _p(m)
            return input('Değiştirilsin mi? [e/H] ').strip().lower() in ('e', 'evet')
        _p('[BİLGİ] etkileşimli terminal yok; Xenia ayarı atlandı (--xenia-rov evet ile zorlayın).')
        return False

    def retry(self, t, m):
        _p('[TEKRAR?]', t, '-', m)
        return False
    def pick_file(self, t, types): return self.a['iso']
    def pick_dir(self, t, key):
        v = self.a.get(key)
        if v is None and key == 'xenia' and sys.stdin is not None and sys.stdin.isatty():
            v = input('Xenia klasörü (boş = iptal): ').strip() or None
        return v

    def choose_xenia(self, cands):
        """(eylem, aday, not): eylem 'use' | 'pick' | 'skip'. Hiçbir zaman sessizce karar vermez: adaylar her zaman listelenir."""
        mode = self.a.get('xenia_rov', 'sor')
        for i, c in enumerate(cands, 1):
            _p('[%d] %s' % (i, c.detail()))
        if mode == 'evet':
            if len(cands) == 1:
                _p('[BİLGİ] --xenia-rov evet: tek aday bulundu, bu Xenia kullanılacak.')
                return ('use', cands[0], '')
            why = 'Xenia klasörü bulunamadı' if not cands else '%d Xenia bulundu, hangisinin seçileceği belirsiz' % len(cands)
            _p('[BİLGİ] --xenia-rov evet: %s; hiçbir şey değiştirilmedi. Klasörü --xenia ile belirtin.' % why)
            return ('skip', None, why)
        if sys.stdin is not None and sys.stdin.isatty():
            ans = input('Numara seçin / d = başka klasör / a = atla [a]: ').strip().lower()
            if ans.isdigit() and 1 <= int(ans) <= len(cands):
                return ('use', cands[int(ans) - 1], '')
            if ans == 'd':
                return ('pick', None, '')
            return ('skip', None, 'kullanıcı atladı')
        _p('[BİLGİ] etkileşimli terminal yok; hiçbir şey değiştirilmedi (klasörü --xenia ile belirtin).')
        return ('skip', None, 'etkileşimli terminal yok')
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

    def warn(self, t, m):
        from tkinter import messagebox
        self._main(lambda: messagebox.showwarning(t, m))

    def yesno(self, t, m):
        from tkinter import messagebox
        return self._main(lambda: messagebox.askyesno(t, m))

    def ask_rov(self, m):
        return self.yesno(APP, m)

    def choose_xenia(self, cands):
        """Xenia seçim penceresi: (eylem, aday, not). Tek aday: onay sorusu; çok aday: liste. Her durumda [Başka klasör seç] ve [Atla]."""
        def dlg():
            import tkinter as tk
            top = tk.Toplevel(self.root)
            top.title(APP)
            top.transient(self.root)
            top.grab_set()
            res = {'v': ('skip', None, 'pencere kapatıldı')}
            if len(cands) == 1:
                c = cands[0]
                msg = ("Şu Xenia'nın ayarı değiştirilecek: %s. Oyunu bu Xenia ile mi oynuyorsunuz?\n\n"
                       "Config: %s\nrender_target_path_d3d12 şu an: %s" % (c.dir, c.cfg if c.exists else '(bulunamadı)', c.value_txt))
            else:
                msg = "Birden fazla Xenia bulundu. Ayarı hangisinde değiştirelim? (Her birinin şimdiki ayarı yanında yazıyor.)"
            tk.Label(top, text=msg, justify='left', wraplength=680).pack(padx=12, pady=(12, 6), anchor='w')
            lb = None
            if len(cands) > 1:
                lb = tk.Listbox(top, width=100, height=min(8, len(cands)), exportselection=False)
                for c in cands:
                    lb.insert('end', '%s    [ayar: %s]' % (c.dir, c.value_txt))
                lb.pack(padx=12, pady=6)
            bar = tk.Frame(top)
            bar.pack(pady=12)

            def done(v):
                res['v'] = v
                top.destroy()

            def use():
                if lb is None:
                    done(('use', cands[0], ''))
                elif lb.curselection():
                    done(('use', cands[lb.curselection()[0]], ''))
            tk.Button(bar, text='Evet' if lb is None else 'Seçileni kullan', width=18, command=use).pack(side='left', padx=6)
            tk.Button(bar, text='Başka klasör seç', width=18, command=lambda: done(('pick', None, ''))).pack(side='left', padx=6)
            tk.Button(bar, text='Atla', width=18, command=lambda: done(('skip', None, 'kullanıcı atladı'))).pack(side='left', padx=6)
            top.protocol('WM_DELETE_WINDOW', lambda: done(('skip', None, 'pencere kapatıldı')))
            top.wait_window()
            return res['v']
        return self._main(dlg)

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
def main_flow(ui, args):
    rep = ['Fable II Türkçe Kurulum Raporu', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '']
    manifest = json.load(open(os.path.join(RES, 'manifest.json'), encoding='utf-8'))
    ui.info(APP, 'Bu kurucu sırayla şunları yapar:\n1) Fable II ISO\'nuzu doğrular ve klasöre çıkarır\n2) Türkçe yamayı uygular\n3) İsterseniz, yalnızca sizin onayınızla, Xenia\'da altyazılar için gereken TEK ayarı yapar\n\nİlk adım: ISO dosyanızı seçin.')
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
        ui.info(APP, 'Uyarı: default.xex beklenenden farklı. Oyun farklı bir sürüm olabilir; yama çalışmayabilir.')
    ui.progress(85)
    # d) Xenia: yalnızca altyazı ayarı (izinle)
    rov_ok = xenia_step(ui, rep, args)
    ui.progress(95)
    finish(ui, rep, target, rov_ok)


ROV_QUESTION = ("Xenia'da altyazıların görünmesi için 'render_target_path_d3d12' ayarının 'rov' olması gerekir. "
                "Bu ayar olmadan oyunda altyazılar görünmez (orijinal oyunda da böyledir). Kurucu yalnızca bu tek satırı "
                "değiştirecek; diğer bütün Xenia ayarlarınız olduğu gibi kalacak ve dosyanın yedeği alınacak. Değiştirilsin mi?")


def xenia_step(ui, rep, args):
    """Evet/Hayır -> Xenia kopyası (bulunan HER aday kullanıcıya gösterilir ve o seçer; sessiz karar yok) -> tek satır.
    Ayar tamamsa True. Seçilmeyen hiçbir Xenia'ya dokunulmaz."""
    if not ui.ask_rov(ROV_QUESTION):
        rep.append('Xenia ayarı: atlandı (kullanıcı değiştirmek istemedi). Hiçbir Xenia dosyasına dokunulmadı.')
        return False
    chosen = None
    explicit = args.get('xenia')        # yalnızca CLI: kullanıcı klasörü kendisi belirtti
    if explicit:
        if not os.path.isfile(os.path.join(explicit, 'xenia_canary.exe')):
            ui.error(APP, 'Belirtilen klasörde xenia_canary.exe yok:\n%s' % explicit)
            rep.append('Xenia ayarı: atlandı (belirtilen klasörde xenia_canary.exe yok). Hiçbir Xenia dosyasına dokunulmadı.')
            return False
        chosen = xenia_rov.make_candidate(explicit)
        ui.log('Xenia (kullanıcının belirttiği): ' + chosen.detail())
    else:
        ui.log('Xenia klasörleri aranıyor...')
        cands = [xenia_rov.make_candidate(d) for d in xenia_rov.find_all_xenia()]
        ui.log('%d Xenia bulundu.' % len(cands))
        while chosen is None:
            if cands:
                action, c, note = ui.choose_xenia(cands)
            else:
                ui.info(APP, 'Xenia klasörü otomatik bulunamadı. Şimdi xenia_canary.exe dosyasının bulunduğu klasörü seçin.\n\nAtlamak için klasör seçme penceresini iptal edin; kurulum yine başarılı sayılır.')
                action, c, note = 'pick', None, ''
            if action == 'skip':
                rep.append('Xenia ayarı: atlandı (%s). Hiçbir Xenia dosyasına dokunulmadı.' % (note or 'kullanıcı atladı'))
                return False
            if action == 'use':
                chosen = c
                continue
            d = ui.pick_dir('Xenia Canary klasörünü seçin (xenia_canary.exe olan) — atlamak için İptal', 'xenia')
            if not d:
                if not cands:
                    rep.append('Xenia ayarı: atlandı (klasör seçilmedi). Hiçbir Xenia dosyasına dokunulmadı.')
                    return False
                continue
            if not os.path.isfile(os.path.join(d, 'xenia_canary.exe')):
                ui.error(APP, 'Seçilen klasörde xenia_canary.exe yok:\n%s' % d)
                continue
            cands = [xenia_rov.make_candidate(d)]       # seçilen klasör de değiştirilmeden önce gösterilip onaylatılır
    rep.append('Seçilen Xenia: %s (config: %s; ayarın önceki değeri: %s)' % (chosen.dir, chosen.cfg if chosen.exists else 'yok', chosen.value_txt))
    if not chosen.exists:
        res = xenia_rov.Result('nofile', chosen.cfg or os.path.join(chosen.dir, xenia_rov.CFG_NAME))
    else:
        res = xenia_rov.set_rov(chosen.cfg)
    text, ok = xenia_rov.describe(res)
    ui.log(text)
    rep.append('Xenia ayarı (render_target_path_d3d12):')
    rep.extend('  ' + l for l in text.split('\n'))
    return ok


def finish(ui, rep, target, rov_ok):
    ui.progress(100)
    rp = os.path.join(target, 'kurulum_raporu.txt')
    xex = os.path.join(target, 'default.xex')
    rep.append('')
    rep.append("Xenia'da %s açın. Oyunda Seçenekler -> Dil = English (United Kingdom) seçili olsun." % xex)
    if not rov_ok:
        rep.append(xenia_rov.WARN)
        rep.append(xenia_rov.MANUAL)
    with open(rp, 'w', encoding='utf-8-sig') as f:
        f.write('\r\n'.join(rep) + '\r\n')
    ui.log('\nKurulum raporu: ' + rp)
    msg = ("Kurulum tamamlandı!\n\nXenia'da şu dosyayı açın:\n%s\n\nOyunda Seçenekler → Dil = English (United Kingdom) seçili olsun.\n\nKurulum raporu: %s" % (xex, rp))
    if rov_ok:
        ui.info(APP, msg)
    else:
        ui.warn(APP, msg + '\n\n' + xenia_rov.WARN + '\n\n' + xenia_rov.MANUAL)


class _RecUI:
    """Kendi kendine test icin sessiz arayuz: mesajlari listeye yazar."""
    def __init__(self):
        self.lines = []

    def log(self, m): self.lines.append(m)
    def info(self, t, m): self.lines.append('INFO ' + m)
    def warn(self, t, m): self.lines.append('UYARI ' + m)
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
        need = ['manifest.json', 'xdelta3.exe']
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
        d = {'iso': a[a.index('--iso') + 1], 'target': a[a.index('--target') + 1],
             'xenia': a[a.index('--xenia') + 1] if '--xenia' in a else None,
             'xenia_rov': a[a.index('--xenia-rov') + 1] if '--xenia-rov' in a else 'sor'}
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
