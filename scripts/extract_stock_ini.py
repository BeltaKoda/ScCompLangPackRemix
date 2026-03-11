#!/usr/bin/env python3
"""
Extract stock global.ini from Star Citizen's Data.p4k.

Uses a built-in P4K reader (no external dependencies beyond zstandard).

Usage:
    # Auto-detect SC installation and extract:
    python scripts/extract_stock_ini.py --version 4.7.0 --channel LIVE

    # Provide a local file instead of extracting:
    python scripts/extract_stock_ini.py --version 4.7.0 --channel LIVE --local-file /path/to/stock-global.ini
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_data_p4k, get_version_dir


TARGET_PATHS = [
    "Data/Localization/english/global.ini",
    "Data/Libs/Localization/English/global.ini",
]


def extract_from_p4k(p4k_path: Path, output_path: Path) -> bool:
    """Extract global.ini from Data.p4k using the built-in P4K reader."""
    try:
        from p4k_reader import P4KFile
    except ImportError as e:
        print(f"ERROR: Failed to import P4K reader: {e}")
        print("Make sure zstandard is installed: pip install zstandard")
        return False

    print(f"Opening Data.p4k ({p4k_path})...")
    print("Parsing central directory (this takes a moment for 143GB files)...")

    try:
        p4k = P4KFile(p4k_path)
    except Exception as e:
        print(f"Failed to open Data.p4k: {e}")
        return False

    print(f"Loaded {len(p4k.entries):,} entries from P4K")

    for target in TARGET_PATHS:
        entry = p4k.find(target)
        if entry:
            print(f"Found: {entry.filename} ({entry.file_size:,} bytes)")
            try:
                data = p4k.read(entry)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as out:
                    out.write(data)
                print(f"Extracted to {output_path}")
                return True
            except Exception as e:
                print(f"Failed to extract: {e}")
                return False

    print("Could not find global.ini in Data.p4k")
    return False


def from_local_file(source: Path, output_path: Path) -> bool:
    """Copy a local stock INI file to the expected repo location."""
    if not source.exists():
        print(f"ERROR: Source file not found: {source}")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output_path)
    print(f"Copied {source} -> {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract stock global.ini for a new patch")
    parser.add_argument("--version", required=True, help="Game version (e.g., 4.7.0)")
    parser.add_argument("--channel", required=True, help="Channel: LIVE or PTU")
    parser.add_argument("--local-file", type=Path, default=None,
                        help="Path to a pre-downloaded stock global.ini (skips extraction)")
    parser.add_argument("--p4k-path", type=Path, default=None,
                        help="Override path to Data.p4k (auto-detected by default)")
    args = parser.parse_args()

    output_path = get_version_dir(args.version, args.channel) / "stock-global.ini"

    if output_path.exists():
        print(f"WARNING: {output_path} already exists. It will be overwritten.")

    if args.local_file:
        success = from_local_file(args.local_file, output_path)
    else:
        p4k_path = args.p4k_path or get_data_p4k(args.channel)
        if p4k_path is None:
            print(f"ERROR: Could not find Data.p4k for channel {args.channel}")
            print("Either install Star Citizen or use --local-file or --p4k-path")
            sys.exit(1)

        print(f"Using Data.p4k at: {p4k_path}")
        success = extract_from_p4k(p4k_path, output_path)

    if success:
        # Verify the file looks like a valid INI
        try:
            with open(output_path, "r", encoding="utf-8-sig", errors="replace") as f:
                first_lines = [f.readline() for _ in range(5)]
            has_equals = any("=" in line for line in first_lines)
            if has_equals:
                print("Verification: File looks like a valid INI.")
            else:
                print("WARNING: File does not appear to contain key=value pairs.")
        except Exception:
            pass

        print(f"\nStock INI saved to: {output_path}")
        print(f"Next step: run process-new-patch.py to merge with previous remix.")
    else:
        print("\nERROR: Extraction failed.")
        print("You can provide a stock INI manually with --local-file")
        sys.exit(1)


if __name__ == "__main__":
    main()
