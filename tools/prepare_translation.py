#!/usr/bin/env python3
"""
Fable II Translation Preparation Tool
Processes extracted strings into bank-grouped units, detects duplicates,
identifies non-translatables, classifies banks, and initializes progress tracking.
"""

import os
import sys
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

TAG_PATTERN = re.compile(r'<[^<>]+>|%[-+0 #]*\d*(?:\.\d+)?[hlL]?[diuoxXfFeEgGaAcspn%]')

def extract_control_codes(text):
    """Find all control codes and format specifiers in text."""
    return TAG_PATTERN.findall(text)

def is_skippable(text):
    """Check if a string should be skipped from human translation."""
    stripped = text.strip()
    if not stripped:
        return True, "empty_or_whitespace"
    
    # Pure numbers or symbols
    if re.fullmatch(r'[-+0-9.,/:;#$%&*()_=\[\]{}|\\]+', stripped):
        return True, "numeric_or_symbol_only"
        
    # Pure control code or audio cue tag only (e.g. <laughs>, <a_img>, <s4>)
    cleaned = TAG_PATTERN.sub('', text).strip()
    if not cleaned:
        return True, "control_codes_only"
        
    # Pure ellipsis or placeholder
    if stripped in ['...', '---', '--', '-', '***', '..', '????', '???', '??', '?']:
        return True, "placeholder_punctuation"
        
    return False, None

def classify_bank(strings, skippable_ids):
    """Classify the primary content type of a bank based on heuristics."""
    texts = [s['text'] for s in strings if s['id'] not in skippable_ids]
    if not texts:
        return "Empty / Technical"
        
    total_len = sum(len(t) for t in texts)
    avg_len = total_len / len(texts)
    all_text = " ".join(texts).lower()
    
    # Keyword checks
    ui_keywords = ['press <', 'select', 'cancel', 'accept', 'option', 'menu', 'screen', 'button', 'save', 'load', 'paused']
    item_keywords = ['damage:', 'cost:', 'value:', 'potion', 'sword', 'hammer', 'pistol', 'rifle', 'augment', 'clothing', 'dye']
    book_keywords = ['chapter', 'volume', 'diary', 'journal', 'history of', 'tale of', 'book', 'written by', 'poem']
    dialogue_cues = ['<laughs>', '<sighs>', '<whimpers>', '<mutters>', '<hums>', '<screams>', '<giggles>']
    
    ui_score = sum(all_text.count(k) for k in ui_keywords)
    item_score = sum(all_text.count(k) for k in item_keywords)
    book_score = sum(all_text.count(k) for k in book_keywords)
    dialogue_score = sum(all_text.count(k) for k in dialogue_cues)
    
    # Check quotes and conversational cues
    quote_count = sum(t.count('"') + t.count("'") for t in texts)
    
    if ui_score > 5 and avg_len < 35:
        return "UI / Menü / Arayüz"
    elif book_score > 3 or (avg_len > 120 and quote_count < len(texts)):
        return "Kitap / Günlük / Tarihçe"
    elif item_score > 5 or (avg_len < 30 and ('weapon' in all_text or 'armour' in all_text or 'cost:' in all_text)):
        return "Eşya / Büyü / Donanım"
    elif dialogue_score > 3 or quote_count > len(texts) * 0.4:
        return "Diyalog / Görev Konuşmaları"
    elif avg_len > 70:
        return "Görev / Açıklama Metinleri"
    elif avg_len < 40:
        return "Kısa İpuçları / HUD / Etiketler"
    else:
        return "Halk Dedikoduları / Çevre Diyalogları"

def main():
    extracted_strings_path = 'work/extracted_babel/book_en_strings.json'
    extracted_meta_path = 'work/extracted_babel/book_en_meta.json'
    
    if not os.path.isfile(extracted_strings_path):
        print(f"Error: {extracted_strings_path} not found. Run babel_extract.py first.", file=sys.stderr)
        sys.exit(1)
        
    print("Loading extracted strings...")
    with open(extracted_strings_path, 'r', encoding='utf-8') as f:
        all_strings = json.load(f)
        
    with open(extracted_meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        
    total_count = len(all_strings)
    print(f"Total raw strings: {total_count}")
    
    # 1. Group by Bank
    banks_data = defaultdict(list)
    text_to_ids = defaultdict(list)
    skipped_items = []
    skipped_id_set = set()
    
    for item in all_strings:
        sid = item['id']
        bid = item['bank_id']
        txt = item['text']
        codes = extract_control_codes(txt)
        
        skip, reason = is_skippable(txt)
        if skip:
            skipped_items.append({
                'id': sid,
                'bank_id': bid,
                'text': txt,
                'reason': reason
            })
            skipped_id_set.add(sid)
            
        record = {
            'id': sid,
            'bank_id': bid,
            'offset': item.get('offset', 0),
            'text': txt,
            'control_codes': codes,
            'is_skippable': skip
        }
        banks_data[bid].append(record)
        
        if not skip:
            text_to_ids[txt].append({'id': sid, 'bank_id': bid})
            
    print(f"Skipped non-translatable strings: {len(skipped_items)}")
    
    # 2. Duplicate Detection
    duplicates = {}
    duplicate_total_strings = 0
    for txt, occurrences in text_to_ids.items():
        if len(occurrences) > 1:
            duplicates[txt] = occurrences
            duplicate_total_strings += len(occurrences) - 1 # count savings
            
    unique_translatable_texts = len(text_to_ids)
    print(f"Unique translatable texts: {unique_translatable_texts} (Savings from duplicates: {duplicate_total_strings} strings)")
    
    # Save skipped.json
    with open('translation/skipped.json', 'w', encoding='utf-8') as f:
        json.dump(skipped_items, f, ensure_ascii=False, indent=2)
    print("Saved translation/skipped.json")
    
    # Save duplicates.json
    duplicates_summary = [
        {'text': txt, 'count': len(occ), 'occurrences': occ}
        for txt, occ in sorted(duplicates.items(), key=lambda x: -len(x[1]))
    ]
    with open('translation/duplicates.json', 'w', encoding='utf-8') as f:
        json.dump(duplicates_summary, f, ensure_ascii=False, indent=2)
    print(f"Saved translation/duplicates.json ({len(duplicates_summary)} distinct duplicated texts)")

    # Save translation/source.json
    with open('translation/source.json', 'w', encoding='utf-8') as f:
        json.dump(banks_data, f, ensure_ascii=False, indent=2)
    print("Saved translation/source.json")
    
    # Save individual bank files in translation/banks/
    for bid, b_strings in banks_data.items():
        bank_file = f"translation/banks/{bid}.json"
        with open(bank_file, 'w', encoding='utf-8') as bf:
            json.dump({
                'bank_id': bid,
                'total_strings': len(b_strings),
                'strings': b_strings
            }, bf, ensure_ascii=False, indent=2)
    print(f"Saved 333 individual bank files to translation/banks/")

    # 3. Classify Banks & Create Overview
    bank_classifications = {}
    progress_data = {
        'total_banks': len(meta['bank_order']),
        'total_strings': total_count,
        'translatable_strings': total_count - len(skipped_items),
        'unique_translatable_texts': unique_translatable_texts,
        'duplicate_savings': duplicate_total_strings,
        'completed_banks': 0,
        'completed_strings': 0,
        'last_updated': datetime.now().isoformat(),
        'banks': {}
    }
    
    overview_lines = [
        "# Fable II Bankalar Genel Bakışı ve İçerik Sınıflandırması\n",
        "Bu belge, oyundaki 333 metin bankasının içerik türlerini, satır sayılarını ve örnek içeriklerini listeler.\n",
        "| Banka ID | İçerik Türü | Toplam Satır | Çevrilecek | Örnek Metin |",
        "|---|---|---|---|---|"
    ]
    
    category_counts = Counter()
    for bid in meta['bank_order']:
        b_strings = banks_data[bid]
        cat = classify_bank(b_strings, skipped_id_set)
        category_counts[cat] += 1
        bank_classifications[bid] = cat
        
        trans_count = len([s for s in b_strings if not s['is_skippable']])
        
        # Sample text
        sample = next((s['text'] for s in b_strings if not s['is_skippable'] and len(s['text']) > 15), "")
        sample_clean = sample.replace('\n', ' ').replace('|', '/')[:60] + ('...' if len(sample) > 60 else '')
        
        overview_lines.append(f"| `{bid}` | {cat} | {len(b_strings)} | {trans_count} | \"{sample_clean}\" |")
        
        progress_data['banks'][bid] = {
            'status': 'pending', # pending | in_progress | translated | validated
            'category': cat,
            'total_strings': len(b_strings),
            'translatable_strings': trans_count,
            'translated_strings': 0,
            'validated_strings': 0,
            'updated_at': None
        }

    # Add summary at beginning of overview
    summary_section = [
        "## Kategori Dağılımı\n",
        "| Kategori | Banka Sayısı |",
        "|---|---|"
    ]
    for c, cnt in category_counts.most_common():
        summary_section.append(f"| **{c}** | {cnt} |")
    summary_section.append("\n---\n")
    
    full_overview = overview_lines[:3] + summary_section + overview_lines[3:]
    with open('translation/banks_overview.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(full_overview))
    print("Saved translation/banks_overview.md")

    # Save translation/progress.json
    with open('translation/progress.json', 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
    print("Saved translation/progress.json")
    
    print("\nPreparation complete!")

if __name__ == "__main__":
    main()
