#!/usr/bin/env python3
"""
Fable II Patch Builder
Assembles translated banks, applies char_map.json, and repacks into a ready-to-test .babel file.
"""

import os
import sys
import json
import glob
import subprocess
import argparse

def apply_char_map(text, mappings):
    """Replace characters according to char_map table."""
    if not mappings:
        return text
    for src, dst in mappings.items():
        text = text.replace(src, dst)
    return text

def build_patch(output_dir="output/patch", char_map_file="tools/char_map.json"):
    print("=== Building Fable II Turkish Patch ===")
    
    # 1. Load source strings as base
    with open('work/extracted_babel/book_en_strings.json', 'r', encoding='utf-8') as f:
        all_strings = json.load(f)
        
    string_map = {item['id']: item for item in all_strings}
    
    # 2. Load translations from translation/banks_translated/
    trans_dir = 'translation/banks_translated'
    translated_count = 0
    translated_banks = 0
    
    if os.path.isdir(trans_dir):
        for b_path in glob.glob(os.path.join(trans_dir, '*.json')):
            try:
                with open(b_path, 'r', encoding='utf-8') as bf:
                    b_data = json.load(bf)
                b_strings = b_data.get('strings', [])
                for item in b_strings:
                    sid = item['id']
                    if sid in string_map:
                        string_map[sid]['text'] = item['text']
                        translated_count += 1
                translated_banks += 1
            except Exception as e:
                print(f"Warning: Failed to load {b_path}: {e}")
                
    print(f"Loaded {translated_count} translated strings from {translated_banks} banks.")
    
    # 3. Apply character mappings
    mappings = {}
    if os.path.isfile(char_map_file):
        try:
            with open(char_map_file, 'r', encoding='utf-8') as cmf:
                cm = json.load(cmf)
                mappings = cm.get('mappings', {})
        except Exception as e:
            print(f"Warning: Could not read char_map.json: {e}")
            
    if mappings:
        print(f"Applying character map with {len(mappings)} rules: {mappings}")
        for item in string_map.values():
            item['text'] = apply_char_map(item['text'], mappings)
    else:
        print("Char map is empty. Preserving native Turkish characters.")
        
    # 4. Prepare repack payload
    work_json_path = 'work/build_payload_strings.json'
    with open(work_json_path, 'w', encoding='utf-8') as wf:
        json.dump(list(string_map.values()), wf, ensure_ascii=False, indent=2)
        
    # 5. Output path
    out_babel_path = os.path.join(output_dir, 'data/language/en-uk/text/book.babel')
    os.makedirs(os.path.dirname(out_babel_path), exist_ok=True)
    
    # 6. Invoke babel_repack.py
    cmd = [
        sys.executable, 'tools/babel_repack.py',
        work_json_path,
        '-m', 'work/extracted_babel/book_en_meta.json',
        '-o', out_babel_path,
        '--ref-babel', 'extracted_original/data/language/en-uk/text/book.babel'
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print("Error during repack:", res.stderr, file=sys.stderr)
        sys.exit(1)
        
    print(f"\n[SUCCESS] Patch successfully built at: '{out_babel_path}'")
    print(f"File size: {os.path.getsize(out_babel_path):,} bytes")

def main():
    parser = argparse.ArgumentParser(description="Build Fable II Turkish Patch")
    parser.add_argument("-o", "--output", default="output/patch", help="Output patch root directory")
    parser.add_argument("-c", "--char-map", default="tools/char_map.json", help="Path to char_map.json")
    args = parser.parse_args()
    
    build_patch(args.output, args.char_map)

if __name__ == "__main__":
    main()
