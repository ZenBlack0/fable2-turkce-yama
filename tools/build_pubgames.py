import os
import sys
import re
import subprocess
import json
import xml.etree.ElementTree as ET

# Step 1: Run translation scripts
subprocess.run([sys.executable, 'tools/translate_pubgames_wizardstower.py'], check=True)
subprocess.run([sys.executable, 'tools/translate_pubgames_magedice.py'], check=True)
subprocess.run([sys.executable, 'tools/translate_pubgames_keystone.py'], check=True)
subprocess.run([sys.executable, 'tools/translate_pubgames_common.py'], check=True)

games = ['common', 'keystone', 'magedice', 'wizardstower']

# font glif eslemesi (build_patch.py ile ayni tablo)
_cm = json.load(open('tools/char_map.json', encoding='utf-8')).get('mappings', {})

def _cmap(t):
    for a, b in _cm.items():
        t = t.replace(a, b)
    return t

# Step 2: kaynakla ayni kalan satirlar icin eklenen ceviriler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubgames_fixes import FIXES
for g in games:
    p = f'translation/pubgames_tr/{g}.json'
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
    d.update(FIXES.get(g, {}))
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

for g in games:
    src_xml = f'extracted_original/data/pubgames/{g}/localization.en.xml'
    tr_json = f'translation/pubgames_tr/{g}.json'
    out_dir = f'output/patch/data/pubgames/{g}'
    out_xml = f'{out_dir}/localization.en.xml'
    os.makedirs(out_dir, exist_ok=True)
    
    with open(tr_json, 'r', encoding='utf-8') as f:
        translations = json.load(f)
        
    with open(src_xml, 'r', encoding='utf-16', newline='') as f:
        content = f.read()
        
    # Text-level substitution: keeps comments, CRLF line endings and
    # formatting of the original file byte-identical outside <value> text.
    from xml.sax.saxutils import escape
    modified_count = 0
    def repl_data(m):
        global_did = m.group(1)
        if translations.get(global_did) is None:
            return m.group(0)
        body = m.group(2)
        new_body, n = re.subn(r'<value>.*?</value>',
                              lambda _: '<value>' + escape(_cmap(translations[global_did])) + '</value>',
                              body, count=1, flags=re.S)
        if n:
            counter[0] += 1
        return m.group(0).replace(body, new_body)
    counter = [0]
    final_body = re.sub(r'<data id="([^"]+)">(.*?)</data>', repl_data, content, flags=re.S)
    modified_count = counter[0]
    final_text = final_body
    test_root = ET.fromstring(final_text.replace('encoding="unicodeFFFE"', 'encoding="utf-8"').encode('utf-8'))

    # Encode as UTF-16-BE with BOM (b'\xfe\xff')
    # Big Endian BOM + utf-16-be bytes
    bom = b'\xfe\xff'
    encoded_bytes = bom + final_text.encode('utf-16-be')
    
    with open(out_xml, 'wb') as f:
        f.write(encoded_bytes)
        
    print(f"[SUCCESS] {g}: {modified_count} strings translated and written to {out_xml} (Valid XML)")

print("\nAll 4 Pub Games XML localizations built and verified successfully!")
