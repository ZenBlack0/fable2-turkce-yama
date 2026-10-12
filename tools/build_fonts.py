#!/usr/bin/env python3
"""Turkce glifleri (ş Ş ğ Ğ ı İ) oyunun .bft fontlarina GERCEK kod noktalariyla ekler.

Mevcut gliflerden bilesim:  ş/Ş = s/S + ç/Ç cengeli,  İ = I + Ż noktasi,
ı = i (noktasi silinmis),  ğ/Ğ = g/G + breve (caron ayni kutuda, parabolik cizim).
Cikti: output/patch/data/language/{en-uk/fonts,fonts}/*.bft  (+ docs/font_preview.png)

Kullanim: python tools/build_fonts.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bft import Bft  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, 'extracted_original/data/language')
OUT_DIR = os.path.join(ROOT, 'output/patch/data/language')
FONTS = ['en-uk/fonts/gui_normal', 'en-uk/fonts/gui_small', 'en-uk/fonts/gui_large',
         'fonts/timesnewroman_16', 'fonts/timesnewroman_10', 'fonts/couriernew_16']
NEW = {'ş': 0x15F, 'Ş': 0x15E, 'ğ': 0x11F, 'Ğ': 0x11E, 'ı': 0x131, 'İ': 0x130}


def cell(b, img, ch):
    x0, y0, x1, y1 = b.rect(b.records[b.glyph_index(ord(ch))])
    return img[y0:y1, x0:x1].copy()


def ink_rows(c, thr=24):
    return [r for r in range(c.shape[0]) if c[r].max() > thr]


def ink_cols(c, thr=24):
    return [k for k in range(c.shape[1]) if c[:, k].max() > thr]


def trim(bm):
    rows = [r for r in range(bm.shape[0]) if bm[r].max() > 0]
    cols = [k for k in range(bm.shape[1]) if bm[:, k].max() > 0]
    return bm[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1], rows[0]


def paste_over(dst, bm, r0, center_col):
    """bm'yi dst uzerine r0 satirindan, center_col etrafinda ortalayarak 'max' ile yapistir."""
    h, w = bm.shape
    c0 = int(round(center_col - (w - 1) / 2.0))
    for r in range(h):
        for k in range(w):
            rr, cc = r0 + r, c0 + k
            if 0 <= rr < dst.shape[0] and 0 <= cc < dst.shape[1]:
                dst[rr, cc] = max(dst[rr, cc], bm[r, k])


def center_of(c, rows=None):
    sub = c if rows is None else c[rows[0]:rows[1] + 1]
    cols = ink_cols(sub)
    return (cols[0] + cols[-1]) / 2.0


def cedilla(b, img, lower):
    base, cc = ('c', 'ç') if lower else ('C', 'Ç')
    cb, cz = cell(b, img, base), cell(b, img, cc)
    bottom = ink_rows(cb)[-1]
    sub = cz[bottom + 1:].copy()
    bm, off = trim(sub)
    return bm, bottom + 1 + off


def dot_above(b, img):
    z, zd = cell(b, img, 'Z'), cell(b, img, 'Ż')
    top = ink_rows(z)[0]
    sub = zd[:top].copy()
    # nokta ile Z arasi bosluk olabilir; yalniz ustteki mürekkep
    sub[sub < 24] = 0
    bm, off = trim(sub)
    return bm, off


def accent_box(b, img, lower):
    """caron kutusu: (ilk satir, son satir, genislik) -- c/C ustundeki isaretten."""
    base, car = ('c', 'č') if lower else ('C', 'Č')
    cb, cz = cell(b, img, base), cell(b, img, car)
    top = ink_rows(cb)[0]
    sub = cz[:top].copy()
    sub[sub < 24] = 0
    bm, off = trim(sub)
    return off, off + bm.shape[0] - 1, bm.shape[1]


def draw_breve(width, height, thick):
    """Parabolik U (breve). Dondurulen: (height x width) uint8, 8x supersample."""
    S = 8
    W, H = width * S, height * S
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    rad = thick * S / 2.0
    cx = (W - 1) / 2.0
    pts = []
    n = 200
    for i in range(n + 1):
        t = -1 + 2.0 * i / n
        x = cx + t * (W / 2.0 - rad)
        y = rad + (1 - t * t) * (H - 2 * rad) * 1.0
        pts.append((x, y))
    for x, y in pts:
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=255)
    small = im.resize((width, height), Image.BOX)
    return np.array(small, np.uint8)


def thickness(b):
    lh = b.line_height
    return 1.2 if lh <= 16 else 1.5 if lh <= 21 else 1.8 if lh <= 24 else 2.0 if lh <= 27 else 2.3


def build_glyph(b, img, ch):
    if ch in 'şŞ':
        low = ch == 'ş'
        base = cell(b, img, 's' if low else 'S')
        bm, r0 = cedilla(b, img, low)
        paste_over(base, bm, r0, center_of(base))
        return base
    if ch == 'İ':
        base = cell(b, img, 'I')
        bm, r0 = dot_above(b, img)
        paste_over(base, bm, r0, center_of(base))
        return base
    if ch == 'ı':
        base = cell(b, img, 'i')
        rows = ink_rows(base, 8)
        groups, cur = [], [rows[0]]
        for r in rows[1:]:
            if r == cur[-1] + 1:
                cur.append(r)
            else:
                groups.append(cur)
                cur = [r]
        groups.append(cur)
        if len(groups) >= 2:
            for r in groups[0]:
                base[r, :] = 0
        return base
    if ch in 'ğĞ':
        low = ch == 'ğ'
        base = cell(b, img, 'g' if low else 'G')
        r0, r1, w = accent_box(b, img, low)
        h = r1 - r0 + 1
        # taban harfin ustte kalan govdesi: kutuyu x-yuksekligi / cap ustu ile hizala
        br = draw_breve(max(w, 3), max(h, 2), thickness(b))
        top = ink_rows(base)[0]
        paste_over(base, br, r0, center_of(base, (top, min(base.shape[0] - 1, top + 6))))
        return base
    raise ValueError(ch)


def process(font):
    path = os.path.join(SRC_DIR, font + '.bft')
    b = Bft(open(path, 'rb').read())
    img = b.decode()
    img0 = img.copy()
    H = b.line_height
    # serbest alan: son glif satirinin sagi
    rects = [b.rect(r) for r in b.records]
    ys = sorted({r[1] for r in rects})
    y = ys[-1]
    x = max(r[2] for r in rects if r[1] == y) + 2
    cell_h = rects[0][3] - rects[0][1]
    touched = set()
    newrects = []
    for ch, code in NEW.items():
        c = build_glyph(b, img, ch)
        w = c.shape[1]
        if x + w + 1 >= b.width:  # sonraki satira gec
            y += (ys[1] - ys[0])
            x = 1
        if y + cell_h > b.height:
            raise RuntimeError('%s: atlasta yer yok' % font)
        assert c.shape[0] == cell_h, (font, ch, c.shape, cell_h)
        img[y:y + cell_h, x:x + w] = c
        newrects.append((x, y, x + w, y + cell_h))
        for by in range(y // 4, (y + cell_h - 1) // 4 + 1):
            for bx in range(x // 4, (x + w - 1) // 4 + 1):
                touched.add((bx, by))
        base_rec = b.records[b.glyph_index(ord({'ş': 's', 'Ş': 'S', 'İ': 'I', 'ı': 'i', 'ğ': 'g', 'Ğ': 'G'}[ch]))]
        uv = b.uv(x, y, x + w, y + cell_h)
        b.records.append([uv[0], uv[1], uv[2], uv[3], base_rec[4], w, base_rec[6]])
        b.set_glyph(code, len(b.records) - 1)
        x += w + 2
    wt = np.full(img.shape, 20.0)
    for x0, y0, x1, y1 in newrects:
        wt[y0:y1, x0:x1] = 1.0
    b.encode_into(img, only_blocks=touched, weights=wt)
    out = os.path.join(OUT_DIR, font + '.bft')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(b.to_bytes())
    # dogrulama: yeniden oku
    b2 = Bft(open(out, 'rb').read())
    img2 = b2.decode()
    diff = np.abs(img2.astype(int) - img0.astype(int))
    # yeni alan disinda yalniz dokunulan bloklarda fark olmali
    mask = np.ones_like(diff, bool)
    for x0, y0, x1, y1 in newrects:
        mask[y0:y1, x0:x1] = False
    worst = int(diff[mask].max())
    assert worst <= 2, 'eski piksellerde beklenmeyen fark: %d' % worst
    print('%-26s +%d glif, %d blok, eski piksellerde maks fark (BC4 yeniden kodlama): %d'
          % (font, len(NEW), len(touched), worst))
    return b0_b(path), b2, img0, img2


def b0_b(path):
    return Bft(open(path, 'rb').read())


def render(b, img, text, scale=3, color=255):
    adv_total = 0
    cells = []
    for ch in text:
        gi = b.glyph_index(ord(ch))
        if gi is None:
            gi = b.glyph_index(ord('?'))
            miss = True
        else:
            miss = False
        r = b.records[gi]
        x0, y0, x1, y1 = b.rect(r)
        cells.append((img[y0:y1, x0:x1], r[4], r[6], miss))
        adv_total += r[6]
    H = max(c.shape[0] for c, *_ in cells)
    canvas = np.zeros((H, adv_total + 10), np.uint8)
    x = 2
    for c, xo, adv, miss in cells:
        w = c.shape[1]
        reg = canvas[:, x + xo:x + xo + w]
        wmax = reg.shape[1]
        reg[:, :] = np.maximum(reg, c[:H, :wmax])
        x += adv
    im = Image.fromarray(canvas).resize((canvas.shape[1] * scale, H * scale), Image.NEAREST)
    return im


def main():
    rows = []
    for font in FONTS:
        b0, b2, i0, i2 = process(font)
        rows.append((font, b0, b2, i0, i2))
    # onizleme
    sample = 'Şişli Ğ ğ ı İ ş ç ö ü  ÇŞĞİÖÜ çşğıöü'
    ims = []
    for font, b0, b2, i0, i2 in rows:
        for lab, b, im in (('ORIJINAL', b0, i0), ('YENI', b2, i2)):
            r = render(b, im, sample, 2 if b.line_height > 24 else 3)
            ims.append((font.split('/')[-1] + ' ' + lab, r))
    W = max(r.width for _, r in ims) + 20
    Hh = sum(r.height + 18 for _, r in ims) + 10
    sheet = Image.new('RGB', (W, Hh), (30, 24, 20))
    d = ImageDraw.Draw(sheet)
    yy = 6
    for lab, r in ims:
        d.text((6, yy), lab, fill=(180, 160, 120))
        yy += 14
        rgb = Image.merge('RGB', [r, r, r])
        sheet.paste(rgb, (6, yy))
        yy += r.height + 4
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    sheet.save(os.path.join(ROOT, 'docs/font_preview.png'))
    # atlas yan yana (gui_normal)
    font, b0, b2, i0, i2 = rows[0]
    both = Image.new('L', (b0.width, b0.height * 2 + 6), 40)
    both.paste(Image.fromarray(i0), (0, 0))
    both.paste(Image.fromarray(i2), (0, b0.height + 6))
    both.save(os.path.join(ROOT, 'docs/font_atlas_gui_normal.png'))
    print('docs/font_preview.png, docs/font_atlas_gui_normal.png yazildi')


if __name__ == '__main__':
    main()
