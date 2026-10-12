#!/usr/bin/env python3
"""
Fable II (Xbox 360) ISO Extractor (Pure Python XDVDFS Extractor)
Extracts Xbox 360 ISO partitions and files without third-party dependencies.
"""

import os
import sys
import struct
import argparse
import time

SECTOR_SIZE = 2048
XDVDFS_MAGIC = b"MICROSOFT*XBOX*MEDIA"

def find_partition(f):
    """Locate the XDVDFS partition header in the ISO."""
    # Check common known offsets first (XGD2: 0x0FDA0000, 0x02060000, 0x00010000)
    candidate_offsets = [0x0FDA0000, 0x02060000, 0x00010000, 0x00000000]
    for off in candidate_offsets:
        f.seek(off)
        sig = f.read(20)
        if sig == XDVDFS_MAGIC:
            return off - (32 * SECTOR_SIZE), off

    # Fallback: scan in 16MB blocks across the first 512MB
    f.seek(0)
    chunk_size = 16 * 1024 * 1024
    pos = 0
    max_scan = 512 * 1024 * 1024
    while pos < max_scan:
        buf = f.read(chunk_size)
        if not buf:
            break
        idx = buf.find(XDVDFS_MAGIC)
        if idx != -1:
            magic_off = pos + idx
            return magic_off - (32 * SECTOR_SIZE), magic_off
        pos += len(buf)

    return None, None

def parse_directory(data):
    """Parse binary search tree of directory entries in an XDVDFS table."""
    entries = []
    visited = set()

    def walk(off):
        if off in visited or off + 14 > len(data):
            return
        visited.add(off)
        l, r, sec, sz, attr, nlen = struct.unpack('<HHIIBB', data[off:off+14])
        if nlen == 0 or off + 14 + nlen > len(data):
            return
        name = data[off+14:off+14+nlen].decode('ascii', errors='replace')
        entries.append({
            'name': name,
            'sector': sec,
            'size': sz,
            'is_dir': bool(attr & 0x10),
            'attributes': attr
        })
        if l != 0:
            walk(l * 4)
        if r != 0:
            walk(r * 4)

    walk(0)
    return entries

def scan_all_files(f, base_offset, root_sector, root_size):
    """Scan and return all files and directories hierarchically."""
    all_items = []

    def recurse(sector, size, cur_path):
        f.seek(base_offset + sector * SECTOR_SIZE)
        dir_data = f.read(size)
        entries = parse_directory(dir_data)
        for e in entries:
            rel_path = os.path.join(cur_path, e['name']) if cur_path else e['name']
            all_items.append((rel_path, e))
            if e['is_dir']:
                recurse(e['sector'], e['size'], rel_path)

    recurse(root_sector, root_size, "")
    return all_items

def extract_file(f_in, base_offset, sector, size, out_path, buffer_size=4*1024*1024):
    """Extract a single file efficiently using buffered stream reads."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    f_in.seek(base_offset + sector * SECTOR_SIZE)
    remaining = size
    with open(out_path, 'wb') as f_out:
        while remaining > 0:
            to_read = min(remaining, buffer_size)
            chunk = f_in.read(to_read)
            if not chunk:
                break
            f_out.write(chunk)
            remaining -= len(chunk)

def main():
    parser = argparse.ArgumentParser(description="Extract Xbox 360 ISO contents")
    parser.add_argument("iso", help="Path to Xbox 360 .iso file")
    parser.add_argument("-o", "--output", default="extracted_original", help="Output directory")
    parser.add_argument("--list", action="store_true", help="List files without extracting")
    parser.add_argument("--filter", default="", help="Case-insensitive path prefix filter (e.g. data/language)")
    args = parser.parse_args()

    if not os.path.isfile(args.iso):
        print(f"Error: ISO file '{args.iso}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Opening ISO: {args.iso}")
    with open(args.iso, 'rb') as f:
        base_offset, magic_offset = find_partition(f)
        if base_offset is None:
            print("Error: Could not find XDVDFS partition header in ISO.", file=sys.stderr)
            sys.exit(1)

        print(f"Found XDVDFS Partition Header at: 0x{magic_offset:08X} (Base: 0x{base_offset:08X})")

        f.seek(magic_offset + 20)
        root_sector, root_size = struct.unpack('<II', f.read(8))
        print(f"Root Directory Table at Sector: {root_sector}, Size: {root_size} bytes")

        print("Scanning directory tree...")
        items = scan_all_files(f, base_offset, root_sector, root_size)
        print(f"Total directory items found: {len(items)}")

        filter_str = args.filter.replace('\\', '/').lower()
        matched = []
        for rel_path, entry in items:
            norm = rel_path.replace('\\', '/').lower()
            if not filter_str or norm.startswith(filter_str):
                matched.append((rel_path, entry))

        if args.list:
            print(f"\nListing matching files ({len(matched)} items):")
            for rel_path, entry in matched:
                kind = "<DIR> " if entry['is_dir'] else f"{entry['size']:10d} B"
                print(f"  {kind}  {rel_path}")
            return

        print(f"\nExtracting {len(matched)} items to: '{args.output}'...")
        start_time = time.time()
        file_count = 0
        total_bytes = 0

        for rel_path, entry in matched:
            out_target = os.path.join(args.output, rel_path)
            if entry['is_dir']:
                os.makedirs(out_target, exist_ok=True)
            else:
                extract_file(f, base_offset, entry['sector'], entry['size'], out_target)
                file_count += 1
                total_bytes += entry['size']
                if file_count % 10 == 0 or entry['size'] > 50 * 1024 * 1024:
                    mb = total_bytes / (1024 * 1024)
                    print(f"  [{file_count}] Extracted: {rel_path} ({entry['size'] / (1024*1024):.1f} MB) - Total: {mb:.1f} MB")

        elapsed = time.time() - start_time
        mb = total_bytes / (1024 * 1024)
        rate = mb / elapsed if elapsed > 0 else 0
        print(f"\nExtraction complete in {elapsed:.1f}s ({file_count} files, {mb:.1f} MB, {rate:.1f} MB/s).")

if __name__ == "__main__":
    main()
