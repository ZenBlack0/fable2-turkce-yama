import glob
import json
import os
import sys

# Ensure tools directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import validate_bank_translation

def validate_all():
    source_file = "translation/source.json"
    with open(source_file, "r", encoding="utf-8") as sf:
        all_sources = json.load(sf)

    # Load categories from progress.json
    bank_categories = {}
    if os.path.isfile("translation/progress.json"):
        with open("translation/progress.json", "r", encoding="utf-8") as pf:
            pdata = json.load(pf)
            for bid, binfo in pdata.get("banks", {}).items():
                bank_categories[bid] = binfo.get("category", "General")

    banks = glob.glob("translation/banks_translated/*.json")
    print(f"Validating {len(banks)} translated banks against source...")
    total_errors = 0
    total_warnings = 0
    total_term_warnings = 0
    all_too_long = []
    
    for b_path in sorted(banks):
        bank_id = os.path.basename(b_path).replace(".json", "")
        with open(b_path, "r", encoding="utf-8") as f:
            b_data = json.load(f)
        tr_strings = b_data.get("strings", [])
        src_strings = all_sources.get(bank_id, [])
        cat = bank_categories.get(bank_id, "General")
        is_valid, errors, warnings, too_long = validate_bank_translation(src_strings, tr_strings, category=cat)
        if errors:
            print(f"[FAILED] Bank [{bank_id}] has {len(errors)} error(s):")
            for err in errors:
                print(f"  {err['type']}: {err['message']}")
            total_errors += len(errors)
        total_warnings += len(warnings)
        term_warns = [w for w in warnings if w['type'] in ('GLOSSARY_TERM_MISMATCH', 'CREATURE_CASING_WARN')]
        total_term_warnings += len(term_warns)
        
        for item in too_long:
            item['bank_id'] = bank_id
            all_too_long.append(item)
        
    print(f"Terim tutarlılık uyarısı sayısı: {total_term_warnings}")
    print(f"Gerçek UI taşma adayı (too_long) sayısı: {len(all_too_long)}")
    
    # Sort by ratio descending
    all_too_long.sort(key=lambda x: x.get('ratio', 1.0), reverse=True)
    
    # Write translation/reports/ui_too_long.md
    os.makedirs("translation/reports", exist_ok=True)
    with open("translation/reports/ui_too_long.md", "w", encoding="utf-8") as rf:
        rf.write("# Gerçek UI Taşma Adayları Raporu\n\n")
        rf.write("Bu rapor yalnızca UI/Menü, HUD, buton, unvan ve kısa eşya adı metinlerindeki uzunluk oranlarını listeler.\n")
        rf.write(f"Toplam Aday Sayısı: **{len(all_too_long)}**\n\n")
        rf.write("| Banka | ID | Oran | EN Uzunluk | TR Uzunluk | EN Metin | TR Metin |\n")
        rf.write("|---|---|---|---|---|---|---|\n")
        for item in all_too_long:
            src_clean = item['source'].replace('\n', ' ').replace('|', '\\|')
            tr_clean = item['target'].replace('\n', ' ').replace('|', '\\|')
            rf.write(f"| `{item['bank_id']}` | `{item['id']}` | **{item['ratio']}x** | {item['src_len']} | {item['tr_len']} | {src_clean} | {tr_clean} |\n")
    
    if total_errors == 0:
        print(f"\n[PASSED] ALL {len(banks)} BANKS PASSED VALIDATION WITH 0 ERRORS! ({total_warnings} total warnings, {len(all_too_long)} UI overflow candidates)")
    else:
        print(f"\n[FAILED] Total {total_errors} error(s) found across banks.")
        sys.exit(1)

if __name__ == "__main__":
    validate_all()
