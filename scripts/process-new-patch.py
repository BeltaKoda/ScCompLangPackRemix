#!/usr/bin/env python3
"""
Process new Star Citizen patch global.ini file.
Preserves existing remix formatting and keeps new entries in stock format.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict

def read_ini_file(file_path: Path) -> Dict[str, str]:
    """Read an ini file and return a dict of key=value pairs."""
    entries = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith(';'):
                    key, value = line.split('=', 1)
                    entries[key] = value
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)
    return entries

def main():
    parser = argparse.ArgumentParser(description='Merge Star Citizen global.ini files.')
    parser.add_argument('--old-remix', type=Path, default=Path('LIVE/data/Localization/english/global.ini'),
                        help='Path to the previous remixed global.ini')
    parser.add_argument('--new-stock', type=Path, default=Path('LIVE/stock-global.ini'),
                        help='Path to the new stock global.ini')
    parser.add_argument('--old-stock', type=Path, default=None,
                        help='Path to the previous stock global.ini (used to detect intentional remixes)')
    parser.add_argument('--output', type=Path, default=Path('LIVE/data/Localization/english/global.ini'),
                        help='Path to save the merged global.ini')

    args = parser.parse_args()

    current_remix_path = args.old_remix
    new_stock_path = args.new_stock
    old_stock_path = args.old_stock
    output_path = args.output
    output_dir = output_path.parent

    print(f"Old Remix: {current_remix_path}")
    print(f"New Stock: {new_stock_path}")
    if old_stock_path:
        print(f"Old Stock: {old_stock_path}")
    print(f"Output:    {output_path}")

    if not current_remix_path.exists():
        print(f"Warning: Old remix file not found at {current_remix_path}")
    if not new_stock_path.exists():
        print(f"Warning: New stock file not found at {new_stock_path}")

    print("\nReading current remixed ini...")
    current_remix = read_ini_file(current_remix_path)
    print(f"  Loaded {len(current_remix)} entries")

    print("Reading new stock ini...")
    new_stock = read_ini_file(new_stock_path)
    print(f"  Loaded {len(new_stock)} entries")

    old_stock = {}
    if old_stock_path and old_stock_path.exists():
        print("Reading old stock ini...")
        old_stock = read_ini_file(old_stock_path)
        print(f"  Loaded {len(old_stock)} entries")
    elif old_stock_path:
        print(f"Warning: Old stock file not found at {old_stock_path}, preserving all old remix values")

    # Process: start with new stock, overlay remixed values where keys match
    print("Processing entries...")
    new_remix = {}
    kept_remix_count = 0
    new_entry_count = 0
    stale_count = 0

    # Keys to always take from new stock (do not preserve old remix value)
    force_new_keys = {
        'Frontend_PU_Version'
    }

    for key, stock_value in new_stock.items():
        if key == 'Frontend_PU_Version':
            # Special handling for version: use stock value + branding
            new_remix[key] = f"{stock_value} - ScCompLangPackRemix"
            new_entry_count += 1
        elif key in current_remix and key not in force_new_keys:
            if old_stock and key in old_stock:
                # We can compare: was this key intentionally remixed?
                if current_remix[key] != old_stock[key]:
                    # Intentionally remixed — preserve the remix value
                    new_remix[key] = current_remix[key]
                    kept_remix_count += 1
                else:
                    # Never remixed, just carried forward — use new stock
                    new_remix[key] = stock_value
                    stale_count += 1
            else:
                # No old stock to compare — preserve old remix value (safe default)
                new_remix[key] = current_remix[key]
                if current_remix[key] != stock_value:
                    kept_remix_count += 1
        else:
            # New key, keep stock value
            new_remix[key] = stock_value
            new_entry_count += 1

    print(f"  Kept {kept_remix_count} intentionally remixed values")
    if stale_count:
        print(f"  Replaced {stale_count} stale carry-forward values with new stock")
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
