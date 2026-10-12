#!/usr/bin/env python3
"""
Fable II Translation Validation Tool
Validates translated strings against source for control codes, variable safety,
UI length limits, empty lines, untranslated content, proper noun preservation,
and glossary term consistency.
"""

import os
import sys
import json
import re
import argparse

# Ensure UTF-8 output on Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

TAG_PATTERN = re.compile(r'<[^<>]+>|%[a-zA-Z0-9_]+%|%\d+|%[-+0#]*\d*(?:\.\d+)?[hlL]?[diuoxXfFeEgGaAcspn%]')
VARIABLE_SUFFIX_PATTERN = re.compile(r'%[a-zA-Z0-9]+[\'’][a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+')

def load_glossary_info(glossary_path="translation/glossary.json"):
    """
    Loads proper names and translated terms strictly from glossary.json without hardcoding.
    """
    untranslated_proper = set()
    translated_terms = set()
    glossary_rules = []
    
    if os.path.isfile(glossary_path):
        try:
            with open(glossary_path, 'r', encoding='utf-8') as f:
                gdata = json.load(f)
                
            # Proper names (strictly from glossary)
            for k in gdata.get('proper_names_untranslated', {}).keys():
                if not k.startswith('_'):
                    untranslated_proper.add(k)
                    
            for k in gdata.get('geographical_names', {}).keys():
                if not k.startswith('_'):
                    for word in k.split():
                        if word.lower() not in {'castle', 'gardens', 'coast', 'market', 'town', 'lake', 'island', 'cemetery', 'old', 'bandit'}:
                            untranslated_proper.add(word)
                            
            for cat in ['mechanics_and_attributes', 'spells_and_combat', 'world_and_creatures', 'social_and_expressions']:
                for k, v in gdata.get(cat, {}).items():
                    if not k.startswith('_'):
                        for w in k.split():
                            translated_terms.add(w.lower())
                            
            # Monitored glossary consistency rules:
            # (en_regex, expected_tr_root_regex, description)
            glossary_rules = [
                (r'\bCrucible\b', r'çile', 'Crucible -> Çile'),
                (r'\bSkill\b', r'beceri', 'Skill -> Beceri'),
                (r'\bRenown\b', r'\bün[a-zçğıöşü]*\b', 'Renown -> Ün'),
                (r'\bHollow Men\b|\bHollow Man\b', r'kof adam', 'Hollow Men -> Kof Adamlar'),
                (r'\bCullis Gate[s]?\b', r'cullis', 'Cullis Gate -> Cullis Geçidi'),
                (r'\bTown Crier\b', r'tellal', 'Town Crier -> Tellal'),
                (r'\bDemon Door[s]?\b', r'iblis kapı', 'Demon Door -> İblis Kapısı'),
                (r'\bFlitswitch\b|\bFlit Switch\b', r'uçar şalter', 'Flitswitch -> Uçar Şalter'),
                (r'\bColosseum\b', r'kolezyum', 'Colosseum -> Kolezyum'),
                (r'\bThe Box of Secrets\b', r'sırlar kutu', 'The Box of Secrets -> Sırlar Kutusu'),
                (r'\bWeather Chamber\b', r'hava oda', 'Weather Chamber -> Hava Odası'),
                (r'\bTemple of Light\b', r'ışık tapınak|ışık tapınağ', 'Temple of Light -> Işık Tapınağı'),
                (r'\bTemple of Shadows\b', r'gölgeler tapınak|gölgeler tapınağ', 'Temple of Shadows -> Gölgeler Tapınağı'),
                (r'\bCastle Fairfax\b', r'fairfax kale', 'Castle Fairfax -> Fairfax Kalesi'),
                (r'\bKnothole Island\b', r'knothole ada', 'Knothole Island -> Knothole Adası'),
                (r'\bBower Lake\b', r'bower göl', 'Bower Lake -> Bower Gölü'),
                (r'\bBowerstone Market\b', r'bowerstone pazar', 'Bowerstone Market -> Bowerstone Pazarı'),
                (r'\bBowerstone Old Town\b', r'bowerstone eski şehir', 'Bowerstone Old Town -> Bowerstone Eski Şehir'),
                (r'\bBowerstone Cemetery\b', r'bowerstone mezarlık|bowerstone mezarlığ', 'Bowerstone Cemetery -> Bowerstone Mezarlığı'),
                (r'\bBrightwood Tower\b', r'brightwood kule', 'Brightwood Tower -> Brightwood Kulesi'),
                (r'\bStorm Shrine\b', r'fırtına mabet|fırtına mabed', 'Storm Shrine -> Fırtına Mabedi'),
                (r'\bSun Shrine\b', r'güneş mabet|güneş mabed', 'Sun Shrine -> Güneş Mabedi'),
                (r'\bIce Shrine\b', r'buz mabet|buz mabed', 'Ice Shrine -> Buz Mabedi'),
                (r'\bTime Control\b', r'zaman kontrol', 'Time Control -> Zaman Kontrolü'),
                (r'\bRaise Dead\b', r'ölüleri dirilt', 'Raise Dead -> Ölüleri Dirilt'),
                (r'\bHeroes Guild\b|\bHeroes\' Guild\b', r'kahramanlar lonca|lonca', 'Heroes Guild -> Kahramanlar Loncası'),
                (r'\bMad-dog\b|\bMad-Dog\b', r'kuduz', 'Mad-dog -> Kuduz'),
                (r'\bTroll[s]?\b', r'trol', 'Troll -> trol'),
                (r"\bFortune's Tower\b", r'talih kule', "Fortune's Tower -> Talih Kulesi"),
                (r"\bSpinner Box\b|\bSpinnerbox\b", r'çarkıfelek kutu', "Spinner Box -> Çarkıfelek Kutusu"),
                (r"\bKeystone\b", r'kilit taş', "Keystone -> Kilit Taşı"),
            ]
        except Exception:
            pass
            
    return untranslated_proper, translated_terms, glossary_rules

PROPER_NAMES_SET, TRANSLATED_TERMS_SET, GLOSSARY_RULES = load_glossary_info()

STOPWORDS_LOWER = {
    'i', 'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'so', 'as', 'at', 'by', 'for', 'in', 'of', 'on', 'to', 'with',
    'from', 'into', 'over', 'after', 'before', 'between', 'through', 'during', 'without', 'within', 'along', 'across',
    'he', 'she', 'it', 'they', 'we', 'you', 'his', 'her', 'its', 'their', 'our', 'my', 'your', 'this', 'that', 'these', 'those',
    'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'than', 'too', 'very',
    'lord', 'lady', 'sir', 'king', 'queen', 'prince', 'princess', 'hero', 'heroes', 'archon', 'archons', 'commandant',
    'old', 'kingdom', 'temple', 'light', 'shadows', 'shadow', 'will', 'strength', 'skill', 'renown', 'spire', 'crucible',
    'troll', 'trolls', 'hobbe', 'hobbes', 'balverine', 'balverines', 'banshee', 'banshees', 'hollow', 'men', 'man',
    'chamber', 'fate', 'experience', 'magic', 'potion', 'potions', 'book', 'books', 'statue', 'statues', 'gate', 'gates',
    'door', 'doors', 'street', 'road', 'way', 'walk', 'bridge', 'square', 'market', 'town', 'lake', 'island', 'gardens',
    'castle', 'coast', 'house', 'manor', 'lodge', 'residence', 'factory', 'stall', 'shop', 'hall', 'office',
    'tattered', 'chasm', 'abyssals', 'abyssal', 'ferals', 'feral', 'radicles', 'radicle', 'clockwork', 'death', 'dark',
    'flames', 'cult', 'blades', 'nomad', 'shaman', 'archer', 'warrior', 'beggar', 'mighty', 'boring', 'nice', 'givings',
    'puffin', 'ghostly', 'hard', 'knocks', 'posh', 'slum', 'cemetery', 'sovereign', 'beautification', 'immortal', 'invisible',
    'skirt', 'pit', 'heart', 'silk', 'moon', 'cow', 'corset', 'pants', 'scum', 'repose', 'mendicant', 'goodwill', 'plenty',
    'pie', 'meat', 'fish', 'fruit', 'veg', 'jewellery', 'drinks', 'stones', 'combat', 'animation', 'none', 'misc', 'dlc',
    'package', 'name', 'assault', 'murder', 'bankruptcy', 'weapon', 'peace', 'payment', 'drunk', 'disorderly', 'extortion',
    'robbing', 'indecency', 'harassment', 'theft', 'trafficking', 'trespassing', 'vagrancy', 'vandalism', 'parole',
    'violation', 'transgressions', 'arrest', 'future', 'see'
}

CREATURE_LIST = ['Hobbe', 'Balverine', 'Troll', 'Banshee', 'Trol']
CREATURE_BACK_VOWEL_SUFFIX_PATTERN = re.compile(r"\b([hH]obbe|[bB]alverine)'(lar[a-zçğıöşü]*|u[a-zçğıöşü]*|un[a-zçğıöşü]*|a\b|da\b|dan\b|ı[a-zçğıöşü]*|ın[a-zçğıöşü]*|ya\b|yı[a-zçğıöşü]*|yu[a-zçğıöşü]*)")

PRONUNCIATION_EXCEPTIONS = {
    'reaver': 'ı', 'giles': 'ı', 'hammer': 'ı', 'ripper': 'ı', 'greaser': 'ı', 'rupert': 'ı', 'charles': 'ı',
    'bowerstone': 'u', 'bloodstone': 'u', 'knothole': 'u', 'rose': 'u', 'theodore': 'u', 'andrew': 'u', 'sparrow': 'o',
    'harry': 'i', 'johnny': 'i', 'monty': 'i', 'tommy': 'i', 'murray': 'i', 'charlie': 'i', 'barnie': 'i',
    'oakvale': 'e', 'oakfield': 'i', 'jack': 'e', 'sam': 'e', 'dash': 'e', 'hobbe': 'e', 'balverine': 'e',
    'trol': 'e', 'spire': 'a', 'wraithmarsh': 'a', 'thag': 'a', 'dread': 'e', 'head': 'e',
    'house': 'u', 'iq': 'u'
}

TURKISH_ER_OR_EXCEPTIONS = {
    'ömer', 'enver', 'zafer', 'ender', 'soner', 'caner', 'taner', 'kader', 'ejder',
    'lider', 'asker', 'değer', 'fener', 'rehber', 'server', 'traktör', 'sektör', 'faktör', 'motor', 'dekor',
    'gölgeler', 'seçenekler', 'şalter', 'köpeksever', 'sever', 'silahşor'
}


try:
    if os.path.isfile("translation/glossary.json"):
        with open("translation/glossary.json", "r", encoding="utf-8") as _gf:
            _gdata = json.load(_gf)
            if "pronunciation_exceptions" in _gdata:
                for _k, _v in _gdata["pronunciation_exceptions"].items():
                    if isinstance(_v, dict) and "effective_vowel" in _v:
                        PRONUNCIATION_EXCEPTIONS[_k.lower()] = _v["effective_vowel"]
except Exception:
    pass

def get_stem_vowel(stem):
    low = stem.lower()
    if low in PRONUNCIATION_EXCEPTIONS:
        return PRONUNCIATION_EXCEPTIONS[low]
    # English names ending in consonant + y (e.g. Matty, Harry, Billy) are pronounced with [i]
    if len(low) > 2 and low.endswith('y') and low[-2] not in 'aeıioöuü':
        return 'i'
    # English/foreign proper names ending in -er or -or (e.g. Wicker, Reaver, Ripper, Connor, Peter) are pronounced with [ır/ur] -> effective vowel 'ı'
    if len(low) > 2 and (low.endswith('er') or low.endswith('or')) and stem[0].isupper() and not low.endswith('ler') and low not in TURKISH_ER_OR_EXCEPTIONS:
        return 'ı'
    vowels = re.findall(r'[aeıioöuüAEIİOÖUÜ]', stem)
    if not vowels:
        return None
    v = vowels[-1].lower()
    if v == 'i' or v == 'İ': return 'i'
    if v == 'ı' or v == 'I': return 'ı'
    return v

def check_turkish_vowel_harmony(stem, suf):
    sv = get_stem_vowel(stem)
    if not sv:
        return True, None
    suf_vowels = re.findall(r'[aeıioöuü]', suf)
    if not suf_vowels:
        return True, None
    fv = suf_vowels[0]
    if fv == 'a' and sv in 'eiöü':
        return False, f"İnce ünlü '{sv}' sonrasında kalın '-a' eki gelemez."
    if fv == 'e' and sv in 'aıou':
        return False, f"Kalın ünlü '{sv}' sonrasında ince '-e' eki gelemez."
    if fv == 'ı' and sv not in 'aı':
        return False, f"'{sv}' sonrasında düz kalın '-ı/-ın' eki gelemez (doğrusu: '-u/-un' veya ince ek)."
    if fv == 'i' and sv not in 'ei':
        return False, f"'{sv}' sonrasında düz ince '-i/-in' eki gelemez."
    if fv == 'u' and sv not in 'ou':
        return False, f"'{sv}' sonrasında yuvarlak kalın '-u/-un' eki gelemez."
    if fv == 'ü' and sv not in 'öü':
        return False, f"'{sv}' sonrasında yuvarlak ince '-ü/-ün' eki gelemez."
    return True, None

def validate_bank_translation(source_strings, translated_strings, category="General", max_ui_ratio=1.35):
    """
    Validate a single bank's translations.
    Returns: (is_valid, errors, warnings, too_long_items)
    """
    errors = []
    warnings = []
    too_long = []
    
    # Map by ID
    trans_map = {item['id']: item['text'] for item in translated_strings}
    
    for src in source_strings:
        sid = src['id']
        src_text = src['text']
        is_skip = src.get('is_skippable', False)
        
        if is_skip:
            continue
            
        if sid not in trans_map:
            errors.append({
                'id': sid,
                'type': 'MISSING_STRING',
                'message': f"ID {sid} bulunamadı / çevrilmemiş."
            })
            continue
            
        tr_text = trans_map[sid]
        
        # 1. Empty Check
        if not tr_text.strip() and src_text.strip():
            errors.append({
                'id': sid,
                'type': 'EMPTY_TRANSLATION',
                'message': f"ID {sid} çevirisi boş bırakılmış."
            })
            continue
            
        # 2. Control codes & Format specifiers check
        src_tags = TAG_PATTERN.findall(src_text)
        tr_tags = TAG_PATTERN.findall(tr_text)
        
        if src_tags != tr_tags:
            if len(src_tags) != len(tr_tags):
                errors.append({
                    'id': sid,
                    'type': 'TAG_COUNT_MISMATCH',
                    'message': f"Etiket sayısı uyuşmuyor: Kaynak {src_tags} vs Hedef {tr_tags}",
                    'source': src_text,
                    'target': tr_text
                })
            else:
                errors.append({
                    'id': sid,
                    'type': 'TAG_ORDER_MISMATCH',
                    'message': f"Etiket sırası/türü uyuşmuyor: Kaynak {src_tags} vs Hedef {tr_tags}",
                    'source': src_text,
                    'target': tr_text
                })
                
        # 3. Variable suffix check (%s'nin, %d'ye vb.)
        bad_suffixes = VARIABLE_SUFFIX_PATTERN.findall(tr_text)
        if bad_suffixes:
            errors.append({
                'id': sid,
                'type': 'VARIABLE_SUFFIX_ATTACHED',
                'message': f"Değişkene doğrudan ek getirilmiş ({bad_suffixes}). Cümleyi değişken ek almayacak şekilde kurun.",
                'source': src_text,
                'target': tr_text
            })
            
        # 4. Untranslated warning (if identical to English and length > 5)
        if tr_text == src_text and len(src_text.strip()) > 5:
            if re.search(r'[a-zA-Z]', src_text):
                warnings.append({
                    'id': sid,
                    'type': 'UNTRANSLATED_SUSPECT',
                    'message': f"Metin kaynakla birebir aynı (İngilizce kalmış olabilir): '{src_text}'"
                })
                
        # 5. UI Length overflow check (only UI/Menü, HUD, button, title, and item names; not dialogue, books, letters, descriptions)
        if category in ["UI / Menü / Arayüz", "Kısa İpuçları / HUD / Etiketler"]:
            is_ui = True
        elif category in ["Eşya / Büyü / Donanım", "General"]:
            # Only item names / titles: short, no newlines, not ending in full stop/punctuation sentence
            is_ui = len(src_text) < 40 and '\n' not in src_text and not src_text.endswith('.') and not any(src_text.endswith(p) for p in ['!', '?', '"', "'", '...'])
        else:
            is_ui = False

        if is_ui and len(src_text) > 3:
            ratio = len(tr_text) / len(src_text)
            diff = len(tr_text) - len(src_text)
            if ratio > max_ui_ratio and diff > 5:
                too_long.append({
                    'id': sid,
                    'source': src_text,
                    'target': tr_text,
                    'src_len': len(src_text),
                    'tr_len': len(tr_text),
                    'ratio': round(ratio, 2),
                    'category': category
                })

        # 6. Proper Nouns Check (strictly from glossary)
        for name in PROPER_NAMES_SET:
            if re.search(r'\b' + re.escape(name) + r'\b', src_text):
                first_word = name.split()[0]
                if not re.search(r'\b' + re.escape(first_word), tr_text, re.IGNORECASE):
                    warnings.append({
                        'id': sid,
                        'type': 'PROPER_NAME_MISSING',
                        'message': f"Kaynakta geçen '{name}' özel ismi çeviride bulunamadı veya değiştirilmiş olabilir.",
                        'source': src_text,
                        'target': tr_text
                    })
                    
        # Check dynamic mid-sentence capitalized words (outside tags and quotes)
        clean_src = TAG_PATTERN.sub(' ', src_text)
        words = clean_src.split()
        is_title_case = (len(words) <= 8 and sum(1 for w in words if w and w[0].isupper()) >= len(words) * 0.5)
        if not is_title_case and len(words) > 3:
            matches = re.findall(r'(?<=[a-z,]\s)([A-Z][a-z]+)', clean_src)
            for m in matches:
                m_low = m.lower()
                if m_low in STOPWORDS_LOWER or m_low in TRANSLATED_TERMS_SET:
                    continue
                if not re.search(r'\b' + re.escape(m), tr_text, re.IGNORECASE):
                    warnings.append({
                        'id': sid,
                        'type': 'PROPER_NAME_SUSPECT',
                        'message': f"Kaynakta geçen '{m}' ismi hedef metinde bulunamadı veya değiştirilmiş olabilir.",
                        'source': src_text,
                        'target': tr_text
                    })

        # 7. Glossary Term Consistency Check
        for en_pat, tr_pat, desc in GLOSSARY_RULES:
            if re.search(en_pat, src_text, re.IGNORECASE):
                # Exception: for Skill, only match capitalized Skill
                if en_pat == r'\bSkill\b' and not re.search(r'\bSkill\b', src_text):
                    continue
                if not re.search(tr_pat, tr_text, re.IGNORECASE):
                    warnings.append({
                        'id': sid,
                        'type': 'GLOSSARY_TERM_MISMATCH',
                        'message': f"Sözlük terimi tutarsızlığı [{desc}]: Onaylı karşılık hedef metinde bulunamadı.",
                        'source': src_text,
                        'target': tr_text
                    })

        # 8. Creature casing check: mid-sentence creatures should be lowercase
        for c in CREATURE_LIST:
            matches = list(re.finditer(r'(?<![.!?]\s)(?<!^)(?<!\n)\b' + c + r'\b', tr_text))
            for m in matches:
                start = m.start()
                prefix = tr_text[:start].strip()
                if prefix and not prefix.endswith(('.', '!', '?', ':', '>', '"', '“', "'", '—', '-')):
                    warnings.append({
                        'id': sid,
                        'type': 'CREATURE_CASING_WARN',
                        'message': f"Yaratık adı '{c}' cümle içinde küçük harfle yazılmalıdır ('{c.lower()}').",
                        'source': src_text,
                        'target': tr_text
                    })

        # 9. Creature and Noun spelling checks (trol, Tapınakta kesme)
        if re.search(r'\btroll', tr_text, re.IGNORECASE):
            warnings.append({
                'id': sid,
                'type': 'TROLL_SPELLING_WARN',
                'message': "Troll kelimesinin Türkçe yazımı 'trol' (tek l) olmalıdır.",
                'source': src_text,
                'target': tr_text
            })
        if re.search(r'\b[tT]rol\'', tr_text):
            warnings.append({
                'id': sid,
                'type': 'TROL_APOSTROPHE_WARN',
                'message': "Trol kelimesi kesme işareti almaz ('trolün', 'trole', 'trolden').",
                'source': src_text,
                'target': tr_text
            })
        if re.search(r'\b[tT]apınak\'', tr_text):
            warnings.append({
                'id': sid,
                'type': 'TAPINAK_APOSTROPHE_WARN',
                'message': "Tapınak kelimesine gelen ekler kesmesiz yazılmalıdır ('tapınakta', 'tapınağa', 'tapınaktan').",
                'source': src_text,
                'target': tr_text
            })

        # 10. Creature suffix error check: hobbe' and balverine' must never take back vowels (kalın ünlü)
        c_suffix_match = CREATURE_BACK_VOWEL_SUFFIX_PATTERN.search(tr_text)
        if c_suffix_match:
            c_name = c_suffix_match.group(1)
            wrong_suffix = c_suffix_match.group(2)
            errors.append({
                'id': sid,
                'type': 'CREATURE_SUFFIX_ERROR',
                'message': f"{c_name}' sonrasında kalın ünlülü ek ('{wrong_suffix}') kullanılamaz. İnce ünlü ek kullanılmalıdır (örn: {c_name.lower()}'ler, {c_name.lower()}'yi, {c_name.lower()}'nin, {c_name.lower()}'ye, {c_name.lower()}'den).",
                'source': src_text,
                'target': tr_text
            })

        # 11. Proper noun / Apostrophe vowel harmony check
        for stem_match, suf_match in re.findall(r"\b([A-Za-zÇĞİÖŞÜçğıöşü]+)'([a-zçğıöşü]+)\b", tr_text):
            if stem_match.lower() in ('o', 'd', 'ur', 'cyrandorando'):
                continue
            is_harmonious, harm_msg = check_turkish_vowel_harmony(stem_match, suf_match)
            if not is_harmonious:
                errors.append({
                    'id': sid,
                    'type': 'VOWEL_HARMONY_ERROR',
                    'message': f"Kesme işareti sonrası ünlü uyumu hatası: '{stem_match}\'{suf_match}'. {harm_msg}",
                    'source': src_text,
                    'target': tr_text
                })

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, too_long

def main():
    parser = argparse.ArgumentParser(description="Validate Fable II translation against source")
    parser.add_argument("translated_file", help="Path to translated JSON file (single bank or full strings)")
    parser.add_argument("-b", "--bank-id", default=None, help="Bank ID (if validating a single bank)")
    parser.add_argument("--source", default="translation/source.json", help="Path to translation/source.json")
    args = parser.parse_args()
    
    if not os.path.isfile(args.translated_file):
        print(f"Error: {args.translated_file} not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.source, 'r', encoding='utf-8') as sf:
        all_sources = json.load(sf)
        
    with open(args.translated_file, 'r', encoding='utf-8') as tf:
        translated_data = json.load(tf)
        
    if isinstance(translated_data, dict) and 'strings' in translated_data:
        bank_id = args.bank_id or translated_data.get('bank_id')
        tr_strings = translated_data['strings']
        src_strings = all_sources.get(bank_id, [])
    elif isinstance(translated_data, list):
        if args.bank_id:
            bank_id = args.bank_id
            src_strings = all_sources.get(bank_id, [])
            tr_strings = [s for s in translated_data if s.get('bank_id') == bank_id]
        else:
            bank_id = "ALL"
            src_strings = [item for b_list in all_sources.values() for item in b_list]
            tr_strings = translated_data
    else:
        print("Error: Unrecognized translation file format.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Validating {len(tr_strings)} strings for Bank [{bank_id}]...")
    is_valid, errors, warnings, too_long = validate_bank_translation(src_strings, tr_strings)
    
    term_warnings = [w for w in warnings if w['type'] in ('GLOSSARY_TERM_MISMATCH', 'CREATURE_CASING_WARN')]
    
    if errors:
        print(f"\n[FAILED] {len(errors)} ERROR(S) FOUND:")
        for err in errors[:10]:
            print(f"  [ERROR] [{err['type']}] {err['message']}")
            if 'source' in err:
                print(f"     SRC: {repr(err['source'])}")
                print(f"     TR : {repr(err['target'])}")
        if len(errors) > 10:
            print(f"  ...and {len(errors)-10} more errors.")
    else:
        print("\n[PASSED] All validation checks passed successfully!")
        
    print(f"Terim tutarlılık uyarısı sayısı: {len(term_warnings)}")
    if term_warnings:
        print(f"\n[TERM WARNINGS] {len(term_warnings)} terim uyarısı bulundu:")
        for tw in term_warnings:
            print(f"  [{tw['type']}] {tw['message']}")
            if 'source' in tw:
                print(f"     SRC: {repr(tw['source'])}")
                print(f"     TR : {repr(tw['target'])}")
        print(f"\n[WARNING] {len(warnings)} total warning(s):")
        for w in warnings[:10]:
            print(f"  [WARN] [{w['type']}] {w['message']}")
            if 'source' in w:
                print(f"     SRC: {repr(w['source'][:60])}")
                print(f"     TR : {repr(w['target'][:60])}")
        if len(warnings) > 10:
            print(f"  ...and {len(warnings)-10} more warnings.")
            
    if too_long:
        print(f"\n[NOTICE] {len(too_long)} string(s) exceed UI length limit (>{135}%):")
        for item in too_long[:5]:
            print(f"  [LONG] ID {item['id']}: ({item['src_len']} -> {item['tr_len']} chars, ratio {item['ratio']})")
            print(f"     EN: {repr(item['source'])}")
            print(f"     TR: {repr(item['target'])}")
            
        too_long_path = "translation/too_long.json"
        existing = []
        if os.path.isfile(too_long_path):
            try:
                with open(too_long_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing_ids = {x['id'] for x in existing}
        for item in too_long:
            if item['id'] not in existing_ids:
                existing.append(item)
        with open(too_long_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
            
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
