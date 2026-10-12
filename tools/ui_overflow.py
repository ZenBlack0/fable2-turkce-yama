"""UI metin genisligi analizi (bft metrikleri). Sinir = Ingilizce orijinalin orijinal fontla piksel genisligi.
Kullanim: py tools/ui_overflow.py  -> translation/reports/ui_overflow.md + ui_overflow.json"""
import glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from bft import Bft
FONTS = {}
for n in ('gui_small', 'gui_normal', 'gui_large'):
    FONTS[n] = (Bft(open('extracted_original/data/language/en-uk/fonts/%s.bft' % n, 'rb').read()),
                Bft(open('output/patch/data/language/en-uk/fonts/%s.bft' % n, 'rb').read()))
def width(b, t):
    tot = 0
    for ch in t:
        g = b.glyph_index(ord(ch))
        if g is None:
            g = b.glyph_index(63)
        tot += b.records[g][6]
    return tot
def clean(s):
    return re.sub(r'<[^>]*>|%\d+%?|%[sd]', lambda m: 'XX' if m.group(0).startswith('%') else '', s)
SRC = {s['id']: s['text'] for s in json.load(open('work/extracted_babel/book_en_strings.json', encoding='utf-8'))}
IDS = set(json.load(open('translation/reports/text_review/subtitle_ids.json')))
prog = json.load(open('translation/progress.json', encoding='utf-8'))['banks']
rows = []
for p in glob.glob('translation/banks_translated/*.json'):
    d = json.load(open(p, encoding='utf-8'))
    cat = prog[d['bank_id']]['category']
    if cat not in ('UI / Menü / Arayüz', 'Kısa İpuçları / HUD / Etiketler', 'Eşya / Büyü / Donanım', 'Görev / Açıklama Metinleri'):
        continue
    for s in d['strings']:
        i = s['id']
        if i not in IDS or i not in SRC:
            continue
        en, tr = clean(SRC[i]), clean(s['text'])
        if '\n' in en or len(en) > 45 or re.search(r'[.!?] \w', en):
            continue
        r = {'id': i, 'bank': d['bank_id'], 'cat': cat, 'en': SRC[i], 'tr': s['text']}
        for n, (b0, b1) in FONTS.items():
            r[n] = (width(b0, en), width(b1, tr))
        rows.append(r)
over = [r for r in rows if r['gui_normal'][1] > r['gui_normal'][0]]
for r in over:
    r['ratio'] = round(r['gui_normal'][1] / max(1, r['gui_normal'][0]), 2)
over.sort(key=lambda r: -r['ratio'])
json.dump(over, open('translation/reports/ui_overflow.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open('translation/reports/ui_overflow.md', 'w', encoding='utf-8') as f:
    f.write('# UI taşma analizi (piksel, gui_normal)\n\nİncelenen tek satırlık etiket: %d; EN genişliğini aşan: %d\n\n| ID | Oran | EN px | TR px | EN | TR |\n|---|---|---|---|---|---|\n' % (len(rows), len(over)))
    for r in over:
        f.write('| %s | %s | %d | %d | %s | %s |\n' % (r['id'], r['ratio'], r['gui_normal'][0], r['gui_normal'][1], r['en'].replace('|', '/'), r['tr'].replace('|', '/')))
print(len(rows), len(over))
import collections
print(collections.Counter(r['cat'] for r in over))
print(sum(1 for r in over if r['ratio'] > 1.3), sum(1 for r in over if r['ratio'] > 1.6))
