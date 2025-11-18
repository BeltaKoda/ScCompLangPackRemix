#!/usr/bin/env python3
"""
Process new Star Citizen patch global.ini file.
Preserves existing remix formatting and keeps new entries in stock format.
"""

from pathlib import Path
from typing import Dict

def read_ini_file(file_path: Path) -> Dict[str, str]:
    """Read an ini file and return a dict of key=value pairs."""
    entries = {}
    with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith(';'):
                key, value = line.split('=', 1)
                entries[key] = value
    return entries

def main():
    # Paths
    current_remix_path = Path('4.3.2/LIVE/data/Localization/english/global.ini')
    new_stock_path = Path('/mnt/c/SCExtractor/StockGlobal-4-4-0-PTU.ini')
    output_dir = Path('4.4.0/PTU/data/Localization/english')
    output_path = output_dir / 'global.ini'

    print("Reading current remixed ini...")
    current_remix = read_ini_file(current_remix_path)
    print(f"  Loaded {len(current_remix)} entries")

    print("Reading new stock ini...")
    new_stock = read_ini_file(new_stock_path)
    print(f"  Loaded {len(new_stock)} entries")

    # Process: start with new stock, overlay remixed values where keys match
    print("Processing entries...")
    new_remix = {}
    kept_remix_count = 0
    new_entry_count = 0

    for key, stock_value in new_stock.items():
        if key in current_remix:
            # This key exists in the old remix, use the remixed value
            new_remix[key] = current_remix[key]
            # Check if it was actually remixed (different from stock)
            if current_remix[key] != stock_value:
                kept_remix_count += 1
        else:
            # New key, keep stock value
            new_remix[key] = stock_value
            new_entry_count += 1

    print(f"  Kept {kept_remix_count} existing remixed values")
    print(f"  Added {new_entry_count} new stock entries")
    print(f"  Total entries: {len(new_remix)}")

    # Write output
    print(f"Writing new ini to {output_path}...")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8-sig') as f:
        for key in sorted(new_remix.keys()):
            f.write(f"{key}={new_remix[key]}\n")

    print("Done!")

    # Report on removed entries
    removed_keys = set(current_remix.keys()) - set(new_stock.keys())
    if removed_keys:
        print(f"\nNote: {len(removed_keys)} entries from old remix not in new stock (removed from game)")

if __name__ == '__main__':
    main()
