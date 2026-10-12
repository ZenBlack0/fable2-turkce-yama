#!/usr/bin/env python3
"""
Lionhead Studios Fable II .babel Extractor
Extracts all localized strings, bank associations, offsets, and metadata from .babel files.
"""

import os
import sys
import json
import struct
import zlib
import argparse

def extract_babel(babel_path, output_dir, prefix="book"):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(babel_path, 'rb') as f:
        magic, string_count = struct.unpack('>II', f.read(8))
        print(f"Babel Magic: 0x{magic:08X}, String Count: {string_count}")
        
        # Read string index table
        index_entries = []
        for _ in range(string_count):
            str_id, bank_id, offset = struct.unpack('>III', f.read(12))
            index_entries.append({
                'id_int': str_id,
                'id': f"{str_id:08x}",
                'bank_id_int': bank_id,
                'bank_id': f"{bank_id:08x}",
                'offset': offset
            })
            
        # Read bank table
        bank_count, = struct.unpack('>I', f.read(4))
        print(f"Bank Count: {bank_count}")
        
        banks_order = []
        banks_uncompressed = {}
        banks_compressed_info = {}
        
        for _ in range(bank_count):
            b_id, comp_sz, uncomp_sz = struct.unpack('>III', f.read(12))
            comp_data = f.read(comp_sz)
            
            d = zlib.decompressobj()
            decomp = d.decompress(comp_data, uncomp_sz)
            if len(decomp) != uncomp_sz:
                raise ValueError(f"Decompressed size mismatch for Bank 0x{b_id:08X}: expected {uncomp_sz}, got {len(decomp)}")
                
            b_hex = f"{b_id:08x}"
            banks_order.append(b_hex)
            banks_uncompressed[b_hex] = decomp
            banks_compressed_info[b_hex] = {
                'comp_size': comp_sz,
                'uncomp_size': uncomp_sz
            }
            
        # Read tail section
        tail_data = f.read()
        tail_filename = f"{prefix}_tail.bin"
        tail_path = os.path.join(output_dir, tail_filename)
        with open(tail_path, 'wb') as tf:
            tf.write(tail_data)
        print(f"Tail section saved: {len(tail_data)} bytes -> {tail_path}")

    # Extract all strings
    extracted_strings = []
    for entry in index_entries:
        b_hex = entry['bank_id']
        decomp = banks_uncompressed[b_hex]
        off = entry['offset']
        
        char_len = int.from_bytes(decomp[off:off+4], 'big')
        raw_bytes = decomp[off+4:off+4+char_len*2]
        text = raw_bytes.decode('utf-16-be', errors='replace').rstrip('\x00')
        
        extracted_strings.append({
            'id': entry['id'],
            'bank_id': entry['bank_id'],
            'offset': entry['offset'],
            'text': text
        })

    # Save strings JSON
    strings_json_path = os.path.join(output_dir, f"{prefix}_strings.json")
    with open(strings_json_path, 'w', encoding='utf-8') as jf:
        json.dump(extracted_strings, jf, ensure_ascii=False, indent=2)
    print(f"Extracted {len(extracted_strings)} strings -> {strings_json_path}")
    
    # Save metadata JSON
    meta = {
        'magic': f"{magic:08x}",
        'string_count': string_count,
        'bank_count': bank_count,
        'bank_order': banks_order,
        'tail_file': tail_filename,
        'tail_size': len(tail_data),
        'original_source_babel': os.path.abspath(babel_path).replace('\\', '/')
    }
    meta_json_path = os.path.join(output_dir, f"{prefix}_meta.json")
    with open(meta_json_path, 'w', encoding='utf-8') as mf:
        json.dump(meta, mf, indent=2)
    print(f"Metadata saved -> {meta_json_path}")

def main():
    parser = argparse.ArgumentParser(description="Extract Fable II .babel file to JSON")
    parser.add_argument("babel_file", help="Path to input .babel file")
    parser.add_argument("-o", "--output", default="work/extracted_babel", help="Output directory")
    parser.add_argument("-p", "--prefix", default="book", help="Filename prefix for outputs")
    args = parser.parse_args()
    
    if not os.path.isfile(args.babel_file):
        print(f"Error: File '{args.babel_file}' not found.", file=sys.stderr)
        sys.exit(1)
        
    extract_babel(args.babel_file, args.output, args.prefix)

if __name__ == "__main__":
    main()
