#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xenia_rov.py (kurucunun Xenia'daki TEK müdahalesi) için testler.

Gerçek bir xenia-canary.config.toml'un KOPYALARI üzerinde çalışır (ortam değişkeni XENIA_CFG ile verilir; verilmezse
bilinen yerlerde aranır, yoksa testler küçük bir örnek config ile çalışır). Gerçek dosyaya hiçbir şey yazılmaz.
Kullanım: python tools/installer/test_xenia_rov.py
"""
import hashlib
from pathlib import Path
import os
import shutil
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xenia_rov as X  # noqa: E402

SAMPLE = (b'# Xenia ornek config\r\n[APU]\r\napu = "any"   # ses\r\n\r\n[D3D12]\r\nd3d12_bindless = true\r\n\r\n'
          b'[GPU]\r\ngpu = "d3d12"                     # grafik\r\nrender_target_path_d3d12 = ""   \t# RTV/ROV secimi\r\nvsync = true\r\n\r\n'
          b'[Storage]\r\nmount_cache = true\r\n')


def real_config_bytes():
    cand = [os.environ.get('XENIA_CFG'), r'C:\deneme\xenia_canary_windows\xenia-canary.config.toml.bak',
            r'C:\deneme\xenia_canary_windows\xenia-canary.config.toml']
    for c in cand:
        if c and os.path.isfile(c):
            return open(c, 'rb').read(), c
    return SAMPLE, 'ORNEK'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def tree_hashes(root):
    out = {}
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            out[os.path.relpath(p, root)] = sha(p)
    return out


def set_value(data, value):
    """Gerçek config'te render_target_path_d3d12 değerini (yalnızca değeri) verilen değere çevirir."""
    import re
    return re.sub(rb'(?m)^(render_target_path_d3d12\s*=\s*)("[^"]*"|\S+)', lambda m: m.group(1) + value, data, count=1)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='xrov_')
        self.real, self.src = real_config_bytes()
        self._run = X.xenia_running
        X.xenia_running = lambda: False
        self.roots = os.path.join(self.tmp, 'aramakoku')
        os.makedirs(self.roots)
        self._env = os.environ.get('F2TR_XENIA_ROOTS')
        os.environ['F2TR_XENIA_ROOTS'] = self.roots       # find_all_xenia() varsayılanı bile yalnızca bu klasörü tarar

    def tearDown(self):
        X.xenia_running = self._run
        if self._env is None:
            os.environ.pop('F2TR_XENIA_ROOTS', None)
        else:
            os.environ['F2TR_XENIA_ROOTS'] = self._env
        for r, _, fs in os.walk(self.tmp):
            for f in fs:
                os.chmod(os.path.join(r, f), stat.S_IWRITE | stat.S_IREAD)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cfg(self, data):
        p = os.path.join(self.tmp, X.CFG_NAME)
        open(p, 'wb').write(data)
        return p

    def backups(self):
        return sorted(f for f in os.listdir(self.tmp) if '.yedek-' in f)


class Tests(Base):
    def test1_rtv_tek_satir_degisir(self):
        orig = set_value(self.real, b'"rtv"')
        p = self.cfg(orig)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'changed')
        new = open(p, 'rb').read()
        ol, nl = orig.splitlines(keepends=True), new.splitlines(keepends=True)
        self.assertEqual(len(ol), len(nl))
        diff = [i for i, (a, b) in enumerate(zip(ol, nl)) if a != b]
        self.assertEqual(len(diff), 1, 'tam olarak tek satir degismeli')
        self.assertIn(b'"rov"', nl[diff[0]])
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual(Path(self.tmp, self.backups()[0]).read_bytes(), orig)
        self.assertEqual(r.old, '"rtv"')

    def test2_zaten_rov_dosya_ve_yedek_degismez(self):
        orig = set_value(self.real, b'"rov"')
        p = self.cfg(orig)
        h = sha(p)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'already')
        self.assertEqual(sha(p), h)
        self.assertEqual(self.backups(), [])
        self.assertIn('zaten doğru', X.describe(r)[0])

    def test3_satir_yok_gpu_altina_tek_satir_eklenir(self):
        import re
        orig = re.sub(rb'(?m)^render_target_path_d3d12[^\r\n]*\r?\n', b'', self.real, count=1)
        self.assertNotIn(b'render_target_path_d3d12', orig)
        p = self.cfg(orig)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'added')
        new = open(p, 'rb').read()
        ol, nl = orig.splitlines(keepends=True), new.splitlines(keepends=True)
        self.assertEqual(len(nl), len(ol) + 1)
        added = [i for i in range(len(nl)) if nl[i].startswith(b'render_target_path_d3d12')]
        self.assertEqual(len(added), 1)
        i = added[0]
        self.assertEqual(nl[:i] + nl[i + 1:], ol, 'yalnizca bir satir eklenmeli, gerisi ayni')
        # eklenen satir [GPU] bolumunde mi?
        sect = None
        for ln in nl[:i]:
            m = X._SECT.match(ln.rstrip(b'\r\n'))
            if m:
                sect = m.group(1).strip()
        self.assertEqual(sect, b'GPU')

    def test4_yorum_ve_crlf_korunur(self):
        p = self.cfg(SAMPLE)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'changed')
        new = open(p, 'rb').read()
        self.assertEqual(new, SAMPLE.replace(b'render_target_path_d3d12 = ""   \t# RTV/ROV secimi',
                                              b'render_target_path_d3d12 = "rov"   \t# RTV/ROV secimi'))
        self.assertNotIn(b'\n', new.replace(b'\r\n', b''))      # tek bir LF satir sonu bile olmamali
        # karisik satir sonu + BOM
        mixed = b'\xef\xbb\xbf[GPU]\ngpu = "d3d12"\r\nrender_target_path_d3d12 = "rtv" # x\nvsync = true'
        p2 = self.cfg(mixed)
        X.set_rov(p2)
        self.assertEqual(open(p2, 'rb').read(), mixed.replace(b'"rtv"', b'"rov"'))

    def test4b_son_satirda_satir_sonu_yok_ve_eksik_anahtar(self):
        mixed = b'[GPU]\r\ngpu = "d3d12"'
        p = self.cfg(mixed)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'added')
        self.assertEqual(open(p, 'rb').read(), b'[GPU]\r\ngpu = "d3d12"\r\nrender_target_path_d3d12 = "rov"\r\n')

    def test5_config_yok_dosya_olusturulmaz(self):
        d = tempfile.mkdtemp(prefix='xrov_nocfg_', dir=self.tmp)
        open(os.path.join(d, 'xenia_canary.exe'), 'wb').write(b'x')
        cfg, exists = X.find_config_in(d)
        before = tree_hashes(d)
        res = X.Result('nofile', cfg or os.path.join(d, X.CFG_NAME)) if not exists else X.set_rov(cfg)
        self.assertFalse(os.path.exists(os.path.join(d, X.CFG_NAME)))
        self.assertEqual(tree_hashes(d), before)
        self.assertEqual(res.status, 'nofile')
        text, ok = X.describe(res)
        self.assertFalse(ok)
        self.assertIn('Xenia\'yı bir kez açıp kapatın', text)
        self.assertEqual(X.set_rov(os.path.join(d, X.CFG_NAME)).status, 'nofile')
        self.assertFalse(os.path.exists(os.path.join(d, X.CFG_NAME)))

    def test7_bolum_yok_dosya_degismez(self):
        orig = b'[APU]\r\napu = "any"\r\n'
        p = self.cfg(orig)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'nosection')
        self.assertEqual(open(p, 'rb').read(), orig)
        self.assertEqual(self.backups(), [])
        self.assertIn('Elle yapmak için', X.describe(r)[0])

    def test8_salt_okunur_ve_xenia_acik(self):
        p = self.cfg(set_value(self.real, b'"rtv"'))
        h = sha(p)
        os.chmod(p, stat.S_IREAD)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'readonly')
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
        X.xenia_running = lambda: True
        r = X.set_rov(p)
        self.assertEqual(r.status, 'running')
        self.assertEqual(sha(p), h)
        self.assertEqual(self.backups(), [])

    def test9_gpu_notu_ve_yedek_ustune_yazmaz(self):
        orig = SAMPLE.replace(b'gpu = "d3d12"', b'gpu = "vulkan"')
        p = self.cfg(orig)
        r = X.set_rov(p)
        self.assertEqual(r.status, 'changed')           # vulkan'da da degisir
        self.assertIn('yalnızca Direct3D 12', X.describe(r)[0])
        first = self.backups()
        self.assertEqual(len(first), 1)
        Path(p).write_bytes(orig)                   # ayni saniyede ikinci kez
        X.set_rov(p)
        second = self.backups()
        self.assertEqual(len(second), 2, 'var olan yedegin ustune yazilmamali')
        self.assertEqual(Path(self.tmp, first[0]).read_bytes(), orig)

    # ---- yardımcılar: sahte Xenia klasörleri ----
    def fake_xenia(self, name, value=b'"rtv"'):
        xdir = os.path.join(self.roots, name)
        os.makedirs(os.path.join(xdir, 'patches'))
        os.makedirs(os.path.join(xdir, 'cache_host', 'shaders', 'shareable'))
        open(os.path.join(xdir, 'xenia_canary.exe'), 'wb').write(b'x')
        open(os.path.join(xdir, X.CFG_NAME), 'wb').write(set_value(self.real, value))
        open(os.path.join(xdir, 'patches', '4D5307F1 - Fable II (GOTY_Platinum Edition).patch.toml'), 'w').write('hash = "x"\n')
        open(os.path.join(xdir, 'cache_host', 'shaders', 'shareable', 'a.bin'), 'wb').write(b'cache')
        return xdir

    class UI(object):
        """Senaryolu sahte arayüz: choose = choose_xenia yanıtları sırayla (eylem, aday_indeksi)."""
        def __init__(self, rov=True, choose=(), pick=None):
            self.rov, self.choose, self.pick, self.msgs, self.shown = rov, list(choose), pick, [], []

        def ask_rov(self, m): return self.rov
        def pick_dir(self, t, k): return self.pick
        def info(self, t, m): self.msgs.append(m)
        def error(self, t, m): self.msgs.append(m)
        def log(self, m): self.msgs.append(m)

        def choose_xenia(self, cands):
            self.shown.append([c.dir for c in cands])
            act, idx = self.choose.pop(0)
            return (act, cands[idx] if idx is not None else None, '' if act != 'skip' else 'kullanıcı atladı')

    def test6_hayir_ve_atla_xenia_klasorunde_hicbir_sey_degismez(self):
        import installer as I
        a = self.fake_xenia('XeniaA')
        before = tree_hashes(a)
        # Hayır
        rep = []
        self.assertFalse(I.xenia_step(self.UI(rov=False), rep, {}))
        self.assertEqual(tree_hashes(a), before)
        # Evet -> liste gösterilir -> Atla
        ui = self.UI(choose=[('skip', None)])
        rep = []
        self.assertFalse(I.xenia_step(ui, rep, {}))
        self.assertEqual(ui.shown, [[os.path.normpath(a)]])
        self.assertIn('atlandı', ' '.join(rep))
        self.assertEqual(tree_hashes(a), before)
        # Evet -> tek aday gösterilir -> Evet: yalnızca config satırı değişir; patches ve cache_host aynı
        ui = self.UI(choose=[('use', 0)])
        rep = []
        self.assertTrue(I.xenia_step(ui, rep, {}))
        after = tree_hashes(a)
        self.assertEqual(sorted(k for k in before if before[k] != after.get(k)), [X.CFG_NAME])
        added = sorted(k for k in after if k not in before)
        self.assertEqual(len(added), 1)
        self.assertTrue(added[0].startswith(X.CFG_NAME + '.yedek-'))
        for k in before:
            if k.startswith(('patches', 'cache_host')):
                self.assertEqual(before[k], after[k])

    def test10_iki_xenia_ikisi_de_listelenir_secilmeyene_dokunulmaz(self):
        import installer as I
        a = self.fake_xenia('XeniaA', b'"rtv"')
        b = self.fake_xenia('XeniaB', b'""')
        found = X.find_all_xenia()
        self.assertEqual(sorted(found), sorted([os.path.normpath(a), os.path.normpath(b)]))
        ha, hb = tree_hashes(a), tree_hashes(b)
        # B seçilir -> A'ya HİÇ dokunulmaz
        ui = self.UI(choose=[('use', 1)])
        rep = []
        self.assertTrue(I.xenia_step(ui, rep, {}))
        self.assertEqual(sorted(ui.shown[0]), sorted(found), 'ikisi de kullanıcıya gösterilmeli')
        self.assertEqual(tree_hashes(a), ha)
        hb2 = tree_hashes(b)
        self.assertEqual(sorted(k for k in hb if hb[k] != hb2.get(k)), [X.CFG_NAME])
        self.assertIn('ayarın önceki değeri: ""', ' '.join(rep))
        # ikisi de Atla -> hiçbirine dokunulmaz
        ha, hb = tree_hashes(a), tree_hashes(b)
        self.assertFalse(I.xenia_step(self.UI(choose=[('skip', None)]), [], {}))
        self.assertEqual((tree_hashes(a), tree_hashes(b)), (ha, hb))

    def test11_baska_klasor_sec_onaylatilir_ve_adaylar_degismez(self):
        import installer as I
        a = self.fake_xenia('XeniaA')
        other = os.path.join(self.tmp, 'baska')
        os.makedirs(other)
        open(os.path.join(other, 'xenia_canary.exe'), 'wb').write(b'x')
        open(os.path.join(other, X.CFG_NAME), 'wb').write(set_value(self.real, b'"rtv"'))
        ha, ho = tree_hashes(a), tree_hashes(other)
        ui = self.UI(choose=[('pick', None), ('use', 0)], pick=other)
        rep = []
        self.assertTrue(I.xenia_step(ui, rep, {}))
        self.assertEqual(tree_hashes(a), ha)                       # listedeki aday seçilmediği için değişmedi
        self.assertEqual(ui.shown[1], [os.path.normpath(other)])   # seçilen klasör değiştirilmeden önce yeniden gösterildi
        self.assertNotEqual(tree_hashes(other), ho)
        # xenia_canary.exe olmayan klasör reddedilir, sonra atlanır
        junk = os.path.join(self.tmp, 'bos')
        os.makedirs(junk)
        ui = self.UI(choose=[('pick', None), ('skip', None)], pick=junk)
        self.assertFalse(I.xenia_step(ui, [], {}))
        self.assertTrue(any('xenia_canary.exe yok' in m for m in ui.msgs))
        self.assertEqual(os.listdir(junk), [])

    def test12_hic_xenia_yoksa_secici_cikarilmaz_ve_dosya_olusmaz(self):
        import installer as I
        ui = self.UI(pick=None)
        rep = []
        self.assertFalse(I.xenia_step(ui, rep, {}))
        self.assertEqual(ui.shown, [])
        self.assertIn('atlandı', ' '.join(rep))
        self.assertEqual(os.listdir(self.roots), [])

    def test13_cli_modlari(self):
        import installer as I
        a = self.fake_xenia('XeniaA')
        b = self.fake_xenia('XeniaB')
        ha, hb = tree_hashes(a), tree_hashes(b)
        # evet + iki aday: değişiklik YOK, sebep yazılı
        rep = []
        cli = I.CliUI({'xenia_rov': 'evet'})
        self.assertFalse(I.xenia_step(cli, rep, {}))
        self.assertEqual((tree_hashes(a), tree_hashes(b)), (ha, hb))
        self.assertIn('2 Xenia bulundu', ' '.join(rep))
        # sor + etkileşimsiz: değişiklik YOK
        cli = I.CliUI({'xenia_rov': 'sor'})
        rep = []
        orig_ask = I.CliUI.ask_rov
        I.CliUI.ask_rov = lambda self_, m: True       # evet cevabı verilmiş sayılsın; seçici etkileşimsiz sonuç vermeli
        import io
        old_stdin, sys.stdin = sys.stdin, io.StringIO('')
        try:
            self.assertFalse(I.xenia_step(cli, rep, {}))
        finally:
            I.CliUI.ask_rov = orig_ask
            sys.stdin = old_stdin
        self.assertEqual((tree_hashes(a), tree_hashes(b)), (ha, hb))
        # hayir
        self.assertFalse(I.xenia_step(I.CliUI({'xenia_rov': 'hayir'}), [], {}))
        self.assertEqual((tree_hashes(a), tree_hashes(b)), (ha, hb))
        # evet + tek aday: o değişir
        shutil.rmtree(b)
        self.assertTrue(I.xenia_step(I.CliUI({'xenia_rov': 'evet'}), [], {}))
        self.assertNotEqual(tree_hashes(a), ha)
        # evet + --xenia: yalnızca belirtilen
        c = self.fake_xenia('XeniaC')
        d = self.fake_xenia('XeniaD')
        hc, hd = tree_hashes(c), tree_hashes(d)
        self.assertTrue(I.xenia_step(I.CliUI({'xenia_rov': 'evet', 'xenia': d}), [], {'xenia': d}))
        self.assertEqual(tree_hashes(c), hc)
        self.assertNotEqual(tree_hashes(d), hd)

    def test14_find_all_derinlik_ve_tekrarsizlik(self):
        a = self.fake_xenia('XeniaA')
        deep = os.path.join(self.roots, 'x', 'y', 'z', 'derin')
        os.makedirs(deep)
        open(os.path.join(deep, 'xenia_canary.exe'), 'wb').write(b'x')
        r = X.find_all_xenia(roots=[self.roots, self.roots])
        self.assertEqual(r, [os.path.normpath(a)])
        self.assertEqual(X.find_all_xenia(roots=[os.path.join(self.tmp, 'yok')]), [])
        c = X.make_candidate(a)
        self.assertEqual(c.value_txt, '"rtv"')
        os.remove(os.path.join(a, X.CFG_NAME))
        self.assertEqual(X.make_candidate(a).value_txt, 'config dosyası yok')


if __name__ == '__main__':
    print('config kaynagi:', real_config_bytes()[1])
    unittest.main(verbosity=2)
