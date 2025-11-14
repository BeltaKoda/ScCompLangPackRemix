#!/usr/bin/env python3
"""
Build ScCompLangPackRemix from vanilla global.ini

Transforms component names from verbose format to compact format:
  From: XL-1 S2 Military A
  To:   M2A XL-1

Format: [Type][Size][Quality] [Component Name]
"""

import re
import sys
from pathlib import Path

# Type mappings
TYPE_MAP = {
    'Military': 'M',
    'Industrial': 'I',
    'Civilian': 'C',
    'Competition': 'R',  # R for Racing (avoid conflict with Civilian)
    'Stealth': 'S'
}

def transform_component_name(line):
    """
    Transform component name from vanilla format to remix format.

    Pattern: component_Name=ComponentName S[0-4] Type [A-D]
    Example: item_DescCOOL_AEGS_S01_Avenger=FrostStar S1 Civilian C
    To:      item_DescCOOL_AEGS_S01_Avenger=C1C FrostStar
    """
    # Match pattern: Name=ComponentName S[Size] Type Quality
    match = re.match(r'^(item_Desc[^=]+)=(.+?)\s+S(\d)\s+(\w+)\s+([A-D])\s*$', line)

    if not match:
        return line  # Not a component line, return unchanged

    key, component_name, size, type_name, quality = match.groups()

    # Get type abbreviation
    type_abbr = TYPE_MAP.get(type_name)
    if not type_abbr:
        # Unknown type, return unchanged
        return line

    # Build compact format: [Type][Size][Quality] [ComponentName]
    compact_name = f"{type_abbr}{size}{quality} {component_name}"

    return f"{key}={compact_name}\n"


def build_language_pack(vanilla_file, output_file):
    """
    Build remix language pack from vanilla global.ini

    Args:
        vanilla_file: Path to vanilla global.ini
        output_file: Path to output remix global.ini
    """
    vanilla_path = Path(vanilla_file)
    output_path = Path(output_file)

    if not vanilla_path.exists():
        print(f"Error: Vanilla file not found: {vanilla_file}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    transformed_lines = 0
    total_lines = 0

    print(f"Reading vanilla file: {vanilla_file}")

    with open(vanilla_path, 'r', encoding='utf-8') as infile:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for line in infile:
                total_lines += 1
                transformed = transform_component_name(line)

                if transformed != line:
                    transformed_lines += 1

                outfile.write(transformed)

    print(f"✓ Transformation complete!")
    print(f"  Total lines: {total_lines}")
    print(f"  Transformed: {transformed_lines}")
    print(f"  Output: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: build-language-pack.py <vanilla-global.ini> <output-global.ini>")
        print("\nExample:")
        print("  build-language-pack.py stock-global-ini/StockGlobal-4-4-0-PTU.ini data/Localization/english/global.ini")
        sys.exit(1)

    vanilla_file = sys.argv[1]
    output_file = sys.argv[2]

    build_language_pack(vanilla_file, output_file)
