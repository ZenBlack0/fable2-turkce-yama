#!/usr/bin/env python3
"""
Lionhead Studios Fable II .babel Repacker
Rebuilds valid .babel files from JSON strings, recalculating offsets and bank structures.
"""

import os
import sys
import json
import struct
import zlib
import argparse
import time

def compress_bank_zlib(uncomp_bytes):
    """Compress bank using raw Deflate with sync flush and 0x78DA header."""
    co = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15, memLevel=8, strategy=zlib.Z_DEFAULT_STRATEGY)
    raw_deflate = co.compress(uncomp_bytes) + co.flush(zlib.Z_SYNC_FLUSH)
    return b'\x78\xda' + raw_deflate

def repack_babel(strings_json_path, meta_json_path, output_babel_path, ref_babel_path=None):
    start_time = time.time()
    
    with open(strings_json_path, 'r', encoding='utf-8') as sf:
        strings = json.load(sf)
        
    with open(meta_json_path, 'r', encoding='utf-8') as mf:
        meta = json.load(mf)
        
    meta_dir = os.path.dirname(os.path.abspath(meta_json_path))
    tail_file_path = os.path.join(meta_dir, meta['tail_file'])
    if not os.path.isfile(tail_file_path):
        raise FileNotFoundError(f"Tail binary file not found at: {tail_file_path}")
        
    with open(tail_file_path, 'rb') as tf:
        tail_data = tf.read()

    # Read reference original babel if available (for bit-perfect unchanged banks)
    orig_bank_chunks = {}
    if not ref_babel_path and 'original_source_babel' in meta:
        candidate = meta['original_source_babel']
        if os.path.isfile(candidate):
            ref_babel_path = candidate
            
    if ref_babel_path and os.path.isfile(ref_babel_path):
        with open(ref_babel_path, 'rb') as rf:
            rf.seek(8 + meta['string_count'] * 12 + 4)
            for _ in range(meta['bank_count']):
                b_id, c_sz, u_sz = struct.unpack('>III', rf.read(12))
                c_data = rf.read(c_sz)
                orig_bank_chunks[f"{b_id:08x}"] = (c_sz, u_sz, c_data)
        print(f"Loaded reference bank chunks from: {ref_babel_path}")

    # Group strings by bank_id
    strings_by_bank = {}
    for s in strings:
        bid = s['bank_id']
        if bid not in strings_by_bank:
            strings_by_bank[bid] = []
        strings_by_bank[bid].append(s)

    # Sort each bank's strings by original offset to preserve exact sequence
    for bid in strings_by_bank:
        strings_by_bank[bid].sort(key=lambda x: x.get('offset', 0))

    rebuilt_banks = {}
    updated_entries = [] # (id_int, bank_id_int, new_offset)
    modified_bank_count = 0

    for bid in meta['bank_order']:
        bank_strs = strings_by_bank.get(bid, [])
        uncomp_buf = bytearray()
        
        for item in bank_strs:
            str_offset = len(uncomp_buf)
            item_text = item['text'] + '\x00'
            utf16_bytes = item_text.encode('utf-16-be')
            char_len = len(item_text)
            
            uncomp_buf.extend(struct.pack('>I', char_len))
            uncomp_buf.extend(utf16_bytes)
            
            updated_entries.append((
                int(item['id'], 16),
                int(bid, 16),
                str_offset
            ))
            
        uncomp_bytes = bytes(uncomp_buf)
        
        # Check if identical to reference bank
        if (bid in orig_bank_chunks and len(uncomp_bytes) == orig_bank_chunks[bid][1]
                and zlib.decompressobj().decompress(orig_bank_chunks[bid][2]) == uncomp_bytes):
            # Content (not just length) identical to the original bank
            orig_c_sz, orig_u_sz, orig_c_data = orig_bank_chunks[bid]
            rebuilt_banks[bid] = (orig_c_sz, orig_u_sz, orig_c_data)
        else:
            # Recompress modified bank
            c_data = compress_bank_zlib(uncomp_bytes)
            rebuilt_banks[bid] = (len(c_data), len(uncomp_bytes), c_data)
            modified_bank_count += 1

    # Sort index entries strictly by string ID in ascending order (crucial for bsearch)
    updated_entries.sort(key=lambda x: x[0])

    # Build final binary output
    os.makedirs(os.path.dirname(os.path.abspath(output_babel_path)), exist_ok=True)
    with open(output_babel_path, 'wb') as out_f:
        # 1. Header (8 bytes)
        out_f.write(struct.pack('>II', int(meta['magic'], 16), len(updated_entries)))
        
        # 2. String Index Table (12 bytes per entry)
        for str_id, bank_id, offset in updated_entries:
            out_f.write(struct.pack('>III', str_id, bank_id, offset))
            
        # 3. Bank count (4 bytes)
        out_f.write(struct.pack('>I', len(meta['bank_order'])))
        
        # 4. Bank data chunks
        for bid in meta['bank_order']:
            c_sz, u_sz, c_data = rebuilt_banks[bid]
            out_f.write(struct.pack('>III', int(bid, 16), c_sz, u_sz))
            out_f.write(c_data)
            
        # 5. Tail metadata section
        out_f.write(tail_data)

    out_size = os.path.getsize(output_babel_path)
    elapsed = time.time() - start_time
    print(f"Repack complete in {elapsed:.2f}s:")
    print(f"  Strings: {len(updated_entries)}")
    print(f"  Banks: {len(meta['bank_order'])} ({modified_bank_count} recompressed, {len(meta['bank_order'])-modified_bank_count} cached)")
    print(f"  Output: '{output_babel_path}' ({out_size:,} bytes)")

def main():
    parser = argparse.ArgumentParser(description="Repack Fable II .babel file from JSON")
    parser.add_argument("strings_json", help="Path to input _strings.json file")
    parser.add_argument("-m", "--meta", default=None, help="Path to _meta.json file (defaults to matching prefix)")
    parser.add_argument("-o", "--output", default="work/repacked.babel", help="Path to output .babel file")
    parser.add_argument("--ref-babel", default=None, help="Optional original .babel to preserve bit-perfect unchanged banks")
    args = parser.parse_args()
    
    meta_path = args.meta
    if not meta_path:
        base, _ = os.path.splitext(args.strings_json)
        if base.endswith("_strings"):
            meta_path = base[:-8] + "_meta.json"
        else:
            meta_path = base + "_meta.json"
            
    if not os.path.isfile(args.strings_json):
        print(f"Error: Strings JSON '{args.strings_json}' not found.", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(meta_path):
        print(f"Error: Meta JSON '{meta_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    repack_babel(args.strings_json, meta_path, args.output, args.ref_babel)

if __name__ == "__main__":
    main()
