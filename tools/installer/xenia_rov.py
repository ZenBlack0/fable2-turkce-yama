#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kurucunun Xenia'daki TEK müdahalesi: xenia-canary.config.toml içinde render_target_path_d3d12 = "rov".

Altyazıların görünmesi için zorunludur. Başka hiçbir Xenia ayarına, yama dosyasına veya önbelleğe dokunulmaz.
Dosya TOML kütüphanesiyle yeniden yazılmaz: yalnızca ilgili satır (bayt düzeyinde) değiştirilir/eklenir; yorumlar,
sıralama, boşluklar, kodlama (BOM dahil) ve her satırın kendi satır sonu (CRLF/LF) aynen korunur.
"""
import ctypes
import datetime
import os
import re
import stat
import subprocess

CFG_NAME = 'xenia-canary.config.toml'
KEY = 'render_target_path_d3d12'
WANT = '"rov"'
SECTION = b'GPU'        # gerçek Xenia Canary config'inde anahtar [GPU] bölümündedir

_SECT = re.compile(rb'^\s*\[([^\]\r\n]+)\]\s*(?:#.*)?$')
_KEYLINE = re.compile(rb'^(\s*' + KEY.encode() + rb'\s*=\s*)("(?:[^"\\\r\n]|\\.)*"|[^\s#\r\n]+)(.*?)(\r?\n|\r)?$', re.S)
_GPULINE = re.compile(rb'^\s*gpu\s*=\s*("(?:[^"\\\r\n]|\\.)*"|[^\s#\r\n]+)')


class Result(object):
    """status: already | changed | added | nosection | nofile | readonly | running | error"""

    def __init__(self, status, path, **kw):
        self.status = status
        self.path = path
        self.old = kw.get('old')
        self.new = kw.get('new')
        self.backup = kw.get('backup')
        self.gpu = kw.get('gpu')
        self.detail = kw.get('detail', '')

    @property
    def modified(self):
        return self.status in ('changed', 'added')


def xenia_running():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq xenia_canary.exe'], capture_output=True, text=True,
                             creationflags=0x08000000).stdout
        return 'xenia_canary.exe' in out.lower()
    except Exception:
        return False


def find_config_in(xdir):
    """Seçilen Xenia klasörü için config yolu (dosya yoksa da beklenen yol) ve dosyanın var olup olmadığı.
    Xenia sırası: portable.txt -> exe yanındaki config -> Belgeler\\Xenia. Hiçbiri yoksa (None, False)."""
    if os.path.isfile(os.path.join(xdir, 'portable.txt')) or os.path.isfile(os.path.join(xdir, CFG_NAME)):
        p = os.path.join(xdir, CFG_NAME)
        return p, os.path.isfile(p)
    docs = os.path.join(os.path.expanduser('~'), 'Documents', 'Xenia')
    try:
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # CSIDL_PERSONAL
        docs = os.path.join(buf.value, 'Xenia')
    except Exception:
        pass
    p = os.path.join(docs, CFG_NAME)
    if os.path.isfile(p):
        return p, True
    return None, False


def default_roots():
    """Aramanın yapılacağı kökler. Test/geliştirme için F2TR_XENIA_ROOTS (';' ile ayrılmış klasörler) ile değiştirilebilir."""
    env = os.environ.get('F2TR_XENIA_ROOTS')
    if env:
        return [r for r in env.split(';') if r]
    home = os.path.expanduser('~')
    roots = [os.path.join(home, n) for n in ('Desktop', 'Downloads', 'Documents')]
    roots += ['%s:\\' % c for c in 'CDEFG' if os.path.isdir('%s:\\' % c)]
    roots += [os.environ.get('ProgramFiles', 'C:\\Program Files'), os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')]
    return roots


def find_all_xenia(roots=None, max_depth=2):
    """xenia_canary.exe içeren BÜTÜN klasörlerin listesi (tekrarsız, sıralı). Sığ arama; hiçbirine dokunulmaz.
    Bu liste hiçbir zaman sessizce kullanılmaz: kullanıcıya gösterilir ve o seçer."""
    skip = {'windows', '$recycle.bin', 'system volume information', 'node_modules', '.git', 'appdata'}
    found, seen = [], set()
    for root in (roots if roots is not None else default_roots()):
        if not os.path.isdir(root):
            continue
        base_depth = os.path.normpath(root).count(os.sep)
        for cur, dirs, files in os.walk(root):
            if 'xenia_canary.exe' in (f.lower() for f in files):
                key = os.path.normcase(os.path.normpath(cur))
                if key not in seen:
                    seen.add(key)
                    found.append(os.path.normpath(cur))
            depth = os.path.normpath(cur).count(os.sep) - base_depth
            dirs[:] = [d for d in dirs if d.lower() not in skip and depth < max_depth]
    return sorted(found, key=str.lower)


def read_value(cfg):
    """config'teki render_target_path_d3d12 değeri (tırnaklı metin) ya da None (satır yok). Dosyaya yazmaz."""
    sect, first, gpu = None, None, None
    with open(cfg, 'rb') as f:
        for ln in f.read().splitlines(keepends=True):
            m = _SECT.match(ln.rstrip(b'\r\n'))
            if m:
                sect = m.group(1).strip()
                continue
            k = _KEYLINE.match(ln)
            if k:
                v = k.group(2).decode('utf-8', 'replace')
                if sect == SECTION and gpu is None:
                    gpu = v
                if first is None:
                    first = v
    return gpu if gpu is not None else first


class Candidate(object):
    """Bir Xenia kurulumu: klasör, config yolu (yoksa None) ve ayarın şu anki değeri."""

    def __init__(self, xdir):
        self.dir = os.path.normpath(xdir)
        self.cfg, self.exists = find_config_in(xdir)
        self.value = None
        if self.exists:
            try:
                self.value = read_value(self.cfg)
            except OSError:
                self.value = None

    @property
    def value_txt(self):
        if not self.exists:
            return 'config dosyası yok'
        return self.value if self.value is not None else 'satır yok'

    def detail(self):
        return '%s\n  config: %s\n  render_target_path_d3d12 şu an: %s' % (
            self.dir, self.cfg if self.exists else '(bulunamadı)', self.value_txt)


def make_candidate(xdir):
    return Candidate(xdir)


def _backup_path(path, now=None):
    stamp = (now or datetime.datetime.now()).strftime('%Y%m%d-%H%M%S')
    cand = '%s.yedek-%s' % (path, stamp)
    n = 1
    while os.path.exists(cand):          # var olan yedeğin üstüne asla yazma
        n += 1
        cand = '%s.yedek-%s_%d' % (path, stamp, n)
    return cand


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


def _split(data):
    return data.splitlines(keepends=True)


def set_rov(path):
    """config dosyasında render_target_path_d3d12 = "rov" yapar. Result döner; dosya yalnızca gerektiğinde değişir."""
    if not os.path.isfile(path):
        return Result('nofile', path, detail='config yok (Xenia hiç çalıştırılmamış olabilir)')
    if xenia_running():
        return Result('running', path, detail='Xenia şu anda çalışıyor (kapanırken config dosyasının üzerine yazar)')
    st = os.stat(path)
    if not os.access(path, os.W_OK) or (getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_READONLY):
        return Result('readonly', path, detail='dosya salt okunur')
    try:
        data = _read(path)
    except OSError as e:
        return Result('error', path, detail='dosya okunamadı: %s' % e)
    lines = _split(data)
    sect, gpu_hdr, gpu_last, key_idx, gpu_value = None, None, None, None, None
    for i, ln in enumerate(lines):
        m = _SECT.match(ln.rstrip(b'\r\n'))
        if m:
            sect = m.group(1).strip()
            if sect == SECTION and gpu_hdr is None:
                gpu_hdr = i
            continue
        if sect == SECTION:
            if ln.strip():
                gpu_last = i
            g = _GPULINE.match(ln)
            if g and gpu_value is None:
                gpu_value = g.group(1).decode('utf-8', 'replace')
        if _KEYLINE.match(ln) and (key_idx is None or (sect == SECTION and key_idx[1] != SECTION)):
            key_idx = (i, sect)
    gpu_txt = gpu_value.strip('"') if gpu_value is not None else None
    if key_idx is not None:
        i = key_idx[0]
        m = _KEYLINE.match(lines[i])
        old = m.group(2).decode('utf-8', 'replace')
        if old == WANT:
            return Result('already', path, old=old, new=WANT, gpu=gpu_txt)
        new_lines = lines[:i] + [m.group(1) + WANT.encode() + m.group(3) + (m.group(4) or b'')] + lines[i + 1:]
        status = 'changed'
    else:
        if gpu_hdr is None:
            return Result('nosection', path, gpu=gpu_txt, detail='[%s] bölümü yok' % SECTION.decode())
        anchor = gpu_last if gpu_last is not None else gpu_hdr      # bölümün son dolu satırından sonra (bölümler arası boş satırlar yerinde kalır)
        def _eol(l):
            return b'\r\n' if l.endswith(b'\r\n') else (b'\n' if l.endswith(b'\n') else (b'\r' if l.endswith(b'\r') else None))
        eol = _eol(lines[anchor]) or next((e for e in (_eol(l) for l in lines) if e), b'\n')   # komşu satır, yoksa dosyadaki ilk satır sonu
        head = lines[:anchor + 1]
        if not head[-1].endswith((b'\n', b'\r')):
            head[-1] += eol
        new_lines = head + [(KEY + ' = ' + WANT).encode() + eol] + lines[anchor + 1:]
        old, status = None, 'added'
    new_data = b''.join(new_lines)
    bak = _backup_path(path)
    try:
        with open(bak, 'xb') as f:
            f.write(data)
        with open(path, 'wb') as f:
            f.write(new_data)
        if _read(path) != new_data:
            raise OSError('yazma sonrası doğrulama başarısız')
    except OSError as e:
        try:
            with open(path, 'wb') as f:
                f.write(data)    # eski içeriği geri koy
        except OSError:
            pass
        return Result('error', path, backup=bak, detail='yazılamadı, dosya eski haline getirildi: %s' % e)
    return Result(status, path, old=old, new=WANT, backup=bak, gpu=gpu_txt)


def gpu_note(res):
    if res.gpu is not None and res.gpu.lower() != 'd3d12':
        return ('Not: config\'inizde gpu = "%s". render_target_path_d3d12 yalnızca Direct3D 12 arka ucunda etkilidir; '
                'Xenia başka bir arka uç (ör. Vulkan) kullanıyorsa bu ayar altyazıları göstermeyebilir.' % res.gpu)
    return ''


MANUAL = ('Elle yapmak için: Xenia\'yı KAPATIN, xenia-canary.config.toml dosyasını Not Defteri ile açın, [GPU] bölümündeki\n'
          '    render_target_path_d3d12 = ""\nsatırını şu hale getirin (satır yoksa [GPU] bölümüne ekleyin) ve kaydedin:\n'
          '    render_target_path_d3d12 = "rov"')

WARN = ('ÖNEMLİ: Altyazılar için Xenia ayarlarında render_target_path_d3d12 = "rov" yapın. Yapmazsanız altyazılar görünmez.')


def describe(res):
    """(kullanıcıya gösterilecek metin, ayar_tamam_mı)"""
    s = res.status
    note = gpu_note(res)
    if s == 'already':
        return ('Ayar zaten doğru: render_target_path_d3d12 = "rov" (%s). Hiçbir şey değiştirilmedi, yedek alınmadı.' % res.path, True)
    if s in ('changed', 'added'):
        txt = 'Xenia ayarı değiştirildi:\n  Dosya: %s\n  Eski değer: %s\n  Yeni değer: render_target_path_d3d12 = "rov"\n  Yedek: %s' % (
            res.path, ('render_target_path_d3d12 = ' + res.old) if s == 'changed' else '(satır yoktu, [GPU] bölümüne eklendi)', res.backup)
        return (txt + ('\n  ' + note if note else '') + '\nBaşka hiçbir Xenia ayarı değiştirilmedi.', True)
    why = {'nofile': 'Xenia ayar dosyası (%s) bulunamadı. Xenia\'yı bir kez açıp kapatın, sonra kurucuyu tekrar çalıştırın ya da ayarı elle yapın.' % CFG_NAME,
           'nosection': 'Dosyada [GPU] bölümü yok; dosya değiştirilmedi (%s).' % res.path,
           'readonly': 'Dosya salt okunur olduğu için değiştirilmedi (%s).' % res.path,
           'running': 'Xenia şu anda çalışıyor; kapanırken ayar dosyasının üzerine yazacağı için dosya değiştirilmedi. Xenia\'yı kapatıp kurucuyu tekrar çalıştırın.',
           'error': 'Ayar yapılamadı: %s (%s)' % (res.detail, res.path)}[s]
    return (why + '\n' + MANUAL, False)
