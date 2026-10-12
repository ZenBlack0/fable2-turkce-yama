#!/usr/bin/env python3
"""Altyazi (seslendirilmis) satirlari icin kural tabanli kontrol + yazim denetimi.

  py tools/subtitle_lint.py rules            # kurallari calistir, rapor (uygulamaz)
  py tools/subtitle_lint.py rules --apply    # otomatik duzeltilebilenleri uygular
  py tools/subtitle_lint.py spell            # hunspell tr_TR ile bilinmeyen kelimeler (spell_report.md)
Cikti: translation/reports/subtitle_review/lint_report.md, lint_hits.json
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, 'tools')
D = 'translation/reports/subtitle_review'
IDS = json.load(open(D + '/subtitle_ids.json', encoding='utf-8'))
SRC = {s['id']: s['text'] for s in json.load(open('work/extracted_babel/book_en_strings.json', encoding='utf-8'))}
TR = {}
for p in glob.glob('translation/banks_translated/*.json'):
    for s in json.load(open(p, encoding='utf-8'))['strings']:
        TR[s['id']] = s['text']

W = r"[A-Za-zÇĞİÖŞÜçğıöşü]"
# (ad, TR regex, EN regex veya None, degistirme (str|callable) veya None = yalniz isaretle)
RULES = [
    ('hala->hâlâ', r"\b([Hh])ala\b", r"(?i)\b(still|yet|anymore|any more|even now|continu)", lambda m: m.group(1) + 'âlâ'.replace('â', 'â') if False else ('Hâlâ' if m.group(1) == 'H' else 'hâlâ')),
    ('Hala(teyze) kosulsuz', r"\b[Hh]ala\b", None, None),
    ('abbot->Baskesis', r"\b(Ba[sş]rahip|ba[sş]rahip)(\w*)", r"(?i)\babbot", lambda m: ('Başkeşiş' if m.group(1)[0] == 'B' else 'başkeşiş') + m.group(2).replace('ibi', 'i').replace('ibin', 'in')),
    ('Hemsire->Rahibe', r"\bHem[sş]ire(\w*)", r"(?i)\b(sister|nun)\b", lambda m: 'Rahibe' + m.group(1)),
    ('Divan->Mahkeme', r"\bDivan(\w*)", r"(?i)\bcourt\b", None),
    ('Shard->Kiymik', r"\b([Pp]ar[cç]a|[Kk][ıi]r[ıi]k)(\w*)", r"(?i)\bshard", None),
    ('biscuit->bisküvi', r"(?i)\bkurabiye\w*", r"(?i)\bbiscuit", None),
    ('pitchfork->yaba', r"(?i)\btırpan\w*", r"(?i)\bpitchfork", None),
    ('cullis geçidi kucuk harf', r"\b[Cc]ullis [Gg]eçi\w*", None, None),
    ('Dont-kalibi: yapayim deme', r"(?i)\w+(?:ayım|eyim|ayim|eyim) (?:deme|demeyin)\b", r"(?i)\bdon'?t\b|\bdo not\b|\bnever\b", None),
    ('Dont-kalibi: deme sakin', r"(?i)\b(?:deme|demeyin) sak[ıi]n\b", None, None),
    ('ayrik ek (ın/in/un/ün/nın/nin/nı/ni/ya/ye/na/ne)', r"\b[A-ZÇĞİÖŞÜa-zçğıöşü]{3,} (?:ın|in|un|ün|nın|nin|nun|nün|nı|ni|nu|nü|ndan|nden|yı|yi|yu|yü)\b", None, None),
    ('ayrik ek 2 (ya/ye/na/ne/a/e tek harf)', r"\b[A-ZÇĞİÖŞÜa-zçğıöşü]{3,} (?:a|e|ı|i|u|ü)\b(?! (?:[Bb]ir))", None, None),
    ('troller/Troller buyuk-kucuk', r"\b(?<![.!?] )(?<!^)Troll?\w*", r"(?i)\btrolls?\b", None),
    ('cift bosluk/noktalama', r"  +|\s[,.!?](?!\.)|\.\.\.\.+|,,", None, None),
    ('tireli gecici sozcuk', r"\b\w+-(?:eyim|ayım)\b", None, None),
    ('ayri de/da bitisik', r"\b\w+(?:ki|ya|ye)\s(?:de|da)\s?\b(?=\.)", None, None),
    ('kesme: cins isim', r"\b(?:Tapınak|Kale|Köy|Kasaba|Şehir|Kent|Mağara|Orman|Nehir|Göl|Dağ)'\w+", None, None),
    ('hobbe/balverine kesmesiz', r"\b(?:hobbe|balverine|banshee)(?:ler|lar|yi|ye|nin|yle|den|de)\b", None, None),
    ('Ingilizce kelime kalintisi', r"\b(?:the|and|you|your|with|that|this|have|from|they|there|would|could)\b", None, None),
    ('Kof Adam orta cumle buyuk harf', r"(?<=[a-zçğıöşü,] )Kof Adam", None, lambda m: 'kof adam'),
    ('Kof Adam lik ek', r"(?<=[a-zçğıöşü,] )Kof Adam(\w+)", None, lambda m: 'kof adam' + m.group(1)),
    ('Sever mi/mi', r"Sever m[ıuü]", None, lambda m: 'Sever mi'),
    ('yazim: sapsal/saklaban/cumleniz', r"(?:şapsal\w*|şaklaban\w*|cümleniz)", None, None),
    ('terim: Eski Kasaba/Cöl Kazi/Kaba Kuvvet', r"Eski Kasaba|Çöl Kazı|Kaba Kuvvet|Yol kesenler", None, None),
    ('bozuk: ikile/kancik', r"[İi]kile|kancık", None, None),
    ('uydurma ekler -mekte olmak', r"\b(?:görüm|hedes|tezcan|medarı)\w*", None, None),
]


def run(apply):
    hits = collections.defaultdict(list)
    changed = {}
    for i in IDS:
        t = TR[i]
        e = SRC[i]
        new = t
        for name, rt, re_en, rep in RULES:
            if re_en and not re.search(re_en, e):
                if rep is not None or name in ('Divan->Mahkeme', 'Shard->Kiymik', 'biscuit->bisküvi', 'pitchfork->yaba', 'Dont-kalibi: yapayim deme', 'troller/Troller buyuk-kucuk'):
                    continue
            for m in re.finditer(rt, new):
                hits[name].append(i)
                break
            if apply and rep is not None and re.search(rt, new):
                new = re.sub(rt, rep, new)
        if apply and new != t:
            changed[i] = new
    return hits, changed


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'rules'
    if cmd == 'rules':
        hits, changed = run('--apply' in sys.argv)
        json.dump({k: sorted(set(v)) for k, v in hits.items()}, open(D + '/lint_hits.json', 'w'))
        L = ['# Kural kontrolu (altyazi kumesi: %d satir)\n' % len(IDS), '| Kural | Satir |', '|---|---:|']
        for k, v in hits.items():
            L.append('| %s | %d |' % (k, len(set(v))))
        open(D + '/lint_report.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('\n'.join(L))
        print('otomatik duzeltilecek/duzeltilen:', len(changed))
        if '--apply' in sys.argv and changed:
            sys.argv = ['x']
            import subtitle_review as R
            for i, n in changed.items():
                R.apply_ids([(i, n, 'lint: otomatik kural')]) if hasattr(R, 'apply_ids') else None


_SUF = re.compile(r"(?:sın|sin|sun|sün|siniz|sınız|sunuz|sünüz|ım|im|um|üm|ız|iz|uz|üz|dır|dir|dur|dür|tır|tir|tur|tür|ydı|ydi|ydu|ydü|ymış|ymiş|ymuş|ymüş|yım|yim|yum|yüm|lar|ler|ın|in|un|ün|ı|i|u|ü|a|e|ya|ye|da|de|ta|te|dan|den|tan|ten|la|le|yla|yle|ki|mı|mi|mu|mü|ca|ce|ça|çe|cık|cik|cuk|cük|çık|çik)$")


def norm(w):
    w = w.lower().replace('i̇', 'i')
    return w.replace('â', 'a').replace('î', 'i').replace('û', 'u')


def ok(d, w, depth=0):
    for v in (w, w.lower(), norm(w), norm(w).capitalize()):
        if d.lookup(v):
            return True
    if depth < 3:
        n = norm(w)
        m = _SUF.search(n)
        if m and len(n) - len(m.group(0)) >= 3:
            return ok(d, n[:m.start()], depth + 1)
    return False


def spell():
    from spylls.hunspell import Dictionary
    d = Dictionary.from_files('work/spell/index')
    wl = set()
    if os.path.exists(D + '/spell_whitelist.txt'):
        wl = {x.strip().lower() for x in open(D + '/spell_whitelist.txt', encoding='utf-8') if x.strip() and not x.startswith('#')}
    # EN'deki buyuk harfli sozcukler (ozel isim) ve EN sozcuklerinin kendisi beyaz liste
    en_words = set()
    for i in IDS:
        for w in re.findall(r"[A-Za-z]+", SRC[i]):
            en_words.add(w.lower())
    cnt = collections.Counter()
    ex = {}
    for i in IDS:
        t = re.sub(r"<[^>]*>|%\d+%?|\$[A-Za-z_]+", ' ', TR[i])
        for w in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ]+(?:'[A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ]+)?", t):
            base = w.split("'")[0]
            if len(base) < 2:
                continue
            lw = w.lower()
            if lw in wl or base.lower() in wl or base.lower() in en_words:
                continue
            if "'" in w and base[0].isupper():
                continue
            if ok(d, w):
                continue
            if re.fullmatch(r"[aeıioöuüyhgkpmrfşzvb'ğ]{1,7}", w.lower()) and len(set(w.lower())) <= 4:
                continue  # ünlemler (öff, pöh, hımm, aagh)
            if re.fullmatch(r"(.)\1{2,}.*|.*(.)\2{2,}.*", w.lower()):
                continue  # uzatmalar (ooooh)
            cnt[w.lower()] += 1
            ex.setdefault(w.lower(), i)
    L = ['# Yazim denetimi (hunspell tr_TR) — sozlukte olmayan sozcukler: %d benzersiz, %d gecis\n' % (len(cnt), sum(cnt.values())),
         '| Sozcuk | Sayi | Ornek ID |', '|---|---:|---|']
    for w, c in cnt.most_common():
        L.append('| %s | %d | %s |' % (w, c, ex[w]))
    open(D + '/spell_report.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    json.dump({w: [c, ex[w]] for w, c in cnt.items()}, open(D + '/spell_unknown.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(L[0])
    return cnt, ex


if __name__ == '__main__' and sys.argv[1:2] == ['spell']:
    spell()


VARIANTS = [('dükkan', 'dükkân'), ('mekan(?!ik)', 'mekân'), ('imkan', 'imkân'), ('hikaye', 'hikâye'), ('şikayet', 'şikâyet'), ('tezgah', 'tezgâh'),
            ('bekar', 'bekâr'), ('günahkar', 'günahkâr'), ('rüzgar', 'rüzgâr'), ('yadigar', 'yadigâr'), ('fedakar', 'fedakâr'), ('hilekar', 'hilekâr'),
            ('nikah', 'nikâh'), ('mahkum', 'mahkûm'), ('kağıt', 'kâğıt'), ('mükafat', 'mükâfat'), ('talepkar', 'talepkâr'), ('inkar', 'inkâr'),
            ('yegane', 'yegâne'), ('kahya', 'kâhya'), ('derhal', 'derhâl'), ('afedersin', 'affedersin'), ('hala(?= )', 'hâlâ')]


def variants():
    items = []
    for i in IDS:
        t = TR[i]
        n = t
        for a, b in VARIANTS:
            if a == 'hala(?= )':
                if re.search(r"(?i)\b(still|yet|anymore)\b", SRC[i]) is None:
                    continue
            n = re.sub(r"\b" + a, b, n)
            n = re.sub(r"\b" + a[0].upper() + a[1:], b[0].upper() + b[1:], n)
        if n != t:
            items.append((i, n, 'yazım: TDK (şapkalı/çift ünsüz) tekleştirme'))
    return items


if __name__ == '__main__' and sys.argv[1:2] == ['variants']:
    it = variants()
    print(len(it))
    if '--apply' in sys.argv:
        sys.argv = ['x']
        import subtitle_review as R
        print(R.apply_ids(it))
