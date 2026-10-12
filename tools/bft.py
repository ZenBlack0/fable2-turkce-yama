#!/usr/bin/env python3
"""Lionhead .bft (Fable II) font reader/writer. Format: docs/bft_format.md

Dosya: [25B baslik][N x 22B glif kaydi][u16 kod->glif tablosu][88B doku basligi][doku verisi]
Doku: Xbox 360 tiled + 16-bit byte-swapped BC4 (DXT5A, tek kanal, blok basina 8 bayt).
"""
import struct

import numpy as np

HDR = 25
REC = 22
TEX_HDR = 88
NONE = 0x3434 if False else None  # bos giris degeri dosyaya gore degisir (0x3434 / 0x2424)


def _tiled_offset(x, y, width, log2bpp):
    """Xbox 360 2D tiled adres (x,y blok birimi). Xenia/UModel ile ayni formul."""
    width = (width + 31) & ~31
    macro = ((x >> 5) + (y >> 5) * (width >> 5)) << (log2bpp + 7)
    micro = ((x & 7) + ((y & 0xE) << 2)) << log2bpp
    off = macro + ((micro & ~0xF) << 1) + (micro & 0xF) + ((y & 1) << 4)
    return (((off & ~0x1FF) << 3) + ((y & 16) << 7) + ((off & 0x1C0) << 2)
            + (((((y & 8) >> 2) + (x >> 3)) & 3) << 6) + (off & 0x3F)) >> 0


def _block_order(bw, bh):
    """tiled sirada her blok icin (x,y) -> bayt ofseti (blok 8 bayt: log2=3)."""
    return {(x, y): _tiled_offset(x, y, bw, 3) for y in range(bh) for x in range(bw)}


def bc4_decode_block(b):
    a0, a1 = b[0], b[1]
    bits = int.from_bytes(bytes(b[2:8]), 'little')
    pal = [a0, a1]
    if a0 > a1:
        pal += [((8 - i) * a0 + (i - 1) * a1) // 7 for i in range(2, 8)]
    else:
        pal += [((6 - i) * a0 + (i - 1) * a1) // 5 for i in range(2, 6)] + [0, 255]
    return [pal[(bits >> (3 * i)) & 7] for i in range(16)]


def _pal(a0, a1):
    if a0 > a1:
        return [a0, a1] + [((8 - i) * a0 + (i - 1) * a1) // 7 for i in range(2, 8)]
    return [a0, a1] + [((6 - i) * a0 + (i - 1) * a1) // 5 for i in range(2, 6)] + [0, 255]


def bc4_encode_block(px, orig=None, w=None):
    """16 deger (0..255) -> 8 bayt BC4. Aday uc noktalari arasinda agirlikli en kucuk hata.
    orig: blogun eski 8 baytlik verisi (eski piksellerin birebir korunmasi icin aday olur),
    w: piksel agirliklari (eski pikseller buyuk agirlik)."""
    w = w or [1] * 16
    lo, hi = min(px), max(px)
    cands = {(hi, lo), (lo, hi)}
    if orig is not None:
        cands.add((orig[0], orig[1]))
    best = None
    for A0, A1 in cands:
        pal = _pal(A0, A1)
        idx = [min(range(8), key=lambda k: abs(pal[k] - p)) for p in px]
        err = sum(wi * (pal[i] - p) ** 2 for i, p, wi in zip(idx, px, w))
        if best is None or err < best[0]:
            best = (err, A0, A1, idx)
    _, A0, A1, idx = best
    bits = 0
    for i, v in enumerate(idx):
        bits |= v << (3 * i)
    return bytes([A0, A1]) + bits.to_bytes(6, 'little')


class Bft:
    def __init__(self, data):
        self.raw = bytes(data)
        d = self.raw
        self.header = bytearray(d[:HDR])
        self.count = struct.unpack('>I', d[0x15:0x19])[0]
        self.line_height = struct.unpack('>I', d[4:8])[0]
        p = HDR
        self.records = []
        for _ in range(self.count):
            u0, v0, u1, v1 = struct.unpack('>ffff', d[p:p + 16])
            a, b, c = struct.unpack('>HHH', d[p + 16:p + 22])
            self.records.append([u0, v0, u1, v1, a, b, c])
            p += REC
        first, last = struct.unpack('>HH', d[p:p + 4])
        self.tab_first, self.tab_last = first, last
        n = 2 + last
        self.table = list(struct.unpack('>%dH' % n, d[p:p + 2 * n]))
        self.none = self.table[2]  # kod 0 her zaman bos
        p += 2 * n
        self.tex_hdr = bytearray(d[p:p + TEX_HDR])
        self.width, self.height = struct.unpack('>II', self.tex_hdr[16:24])
        self.tex = d[p + TEX_HDR:]
        assert len(self.tex) == self.width * self.height // 2, (len(self.tex), self.width, self.height)

    # ---- kod -> glif
    def glyph_index(self, code):
        v = self.table[code + 2]
        return None if v == self.none else v

    def set_glyph(self, code, idx):
        self.table[code + 2] = idx

    # ---- doku
    def _swapped(self):
        a = np.frombuffer(self.tex, dtype='>u2').astype('<u2')  # 16-bit byte swap
        return a.tobytes()

    def decode(self):
        bw, bh = self.width // 4, self.height // 4
        data = self._swapped()
        order = _block_order(bw, bh)
        img = np.zeros((self.height, self.width), np.uint8)
        for (x, y), off in order.items():
            blk = bc4_decode_block(data[off:off + 8])
            img[y * 4:y * 4 + 4, x * 4:x * 4 + 4] = np.array(blk, np.uint8).reshape(4, 4)
        return img

    def encode_into(self, img, only_blocks=None, weights=None):
        """img: (H,W) uint8. only_blocks: {(bx,by)} -> yalniz bu bloklari yeniden kodla."""
        bw, bh = self.width // 4, self.height // 4
        data = bytearray(self._swapped())
        order = _block_order(bw, bh)
        for (x, y), off in order.items():
            if only_blocks is not None and (x, y) not in only_blocks:
                continue
            px = img[y * 4:y * 4 + 4, x * 4:x * 4 + 4].reshape(-1).tolist()
            wt = None if weights is None else weights[y * 4:y * 4 + 4, x * 4:x * 4 + 4].reshape(-1).tolist()
            data[off:off + 8] = bc4_encode_block(px, bytes(data[off:off + 8]), wt)
        sw = np.frombuffer(bytes(data), dtype='<u2').astype('>u2').tobytes()
        self.tex = sw

    def to_bytes(self):
        h = bytearray(self.header)
        h[0x15:0x19] = struct.pack('>I', len(self.records))
        out = bytearray(h)
        for r in self.records:
            out += struct.pack('>ffff', *r[:4]) + struct.pack('>HHH', *r[4:7])
        out += struct.pack('>%dH' % len(self.table), *self.table)
        out += self.tex_hdr + self.tex
        return bytes(out)

    # ---- glif yardimcilari
    def rect(self, rec):
        u0, v0, u1, v1 = rec[:4]
        W, H = self.width, self.height
        return (round(u0 * (W - 1)), round(v0 * (H - 1)), round(u1 * (W - 1)), round(v1 * (H - 1)))

    def uv(self, x0, y0, x1, y1):
        return (x0 / (self.width - 1), y0 / (self.height - 1), x1 / (self.width - 1), y1 / (self.height - 1))
