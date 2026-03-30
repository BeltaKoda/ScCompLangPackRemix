import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_remix_ini
import audit_sc_native

REPO_ROOT = get_repo_root()

def load_ini_lines(ini_path: Path) -> List[str]:
    """Load INI file as a list of lines."""
    with open(ini_path, 'r', encoding='utf-8-sig') as f:
        return f.readlines()

def save_ini_lines(ini_path: Path, lines: List[str]):
    """Save lines back to INI file."""
    with open(ini_path, 'w', encoding='utf-8-sig') as f:
        f.writelines(lines)

def map_ini_keys_to_lines(lines: List[str]) -> Dict[str, int]:
    """Map INI keys to their line numbers for in-place updates."""
    key_map = {}
    for i, line in enumerate(lines):
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith(';') or line.startswith('#') or '=' not in line:
            continue

        # Split on first '='
        key = line.split('=', 1)[0].strip()
        key_map[key] = i
    return key_map

def apply_fixes(libs_dir: Path, ini_path: Path, name_dict: Dict[str, str]):
    """Apply naming fixes to the INI file based on extracted component data."""
    print("=" * 60)
    print("Star Citizen Language Pack Fixer")
    print("=" * 60)

    # Load INI lines and build key map
    lines = load_ini_lines(ini_path)
    key_map = map_ini_keys_to_lines(lines)

    print("Scanning components...")
    components = audit_sc_native.walk_component_xmls(libs_dir, name_dict)
    print(f"Found {len(components)} components.")

    # Apply Fixes
    updates_count = 0
    skipped_placeholders = 0

    class_prefix_map = {
        'Military': 'M',
        'Civilian': 'C',
        'Industrial': 'I',
        'Stealth': 'S',
        'Competition': 'R',
    }

    print("\nApplying fixes...")

    for comp in components:
        # Resolve Description to find Class
        desc_token = comp.description_token.lstrip('@')
        description_text = name_dict.get(desc_token, "")

        class_match = re.search(r"Class:\s*(\w+)", description_text, re.IGNORECASE)
        item_class = class_match.group(1).capitalize() if class_match else "Unknown"

        type_prefix = class_prefix_map.get(item_class, 'C') # Default to C

        # Construct Expected Prefix Code
        expected_code = f"{type_prefix}{comp.size}{comp.grade}"

        # Get Current Name
        comp_token = comp.token.lstrip('@')
        if comp_token not in key_map:
            continue

        current_line_idx = key_map[comp_token]
        current_line = lines[current_line_idx]

        # Parse key=value
        parts = current_line.split('=', 1)
        key = parts[0]
        current_value = parts[1].strip()

        # Ignore Placeholders
        if "PLACEHOLDER" in current_value:
            skipped_placeholders += 1
            continue

        # Parse Base Name
        match = re.match(r"^([A-Z][0-9][A-Z])\s+(.*)", current_value)
        if match:
            base_name = match.group(2)
        else:
            base_name = current_value

        # Construct New Value
        new_value = f"{expected_code} {base_name}"

        if new_value != current_value:
            print(f"Updating {comp_token}:")
            print(f"  Old: '{current_value}'")
            print(f"  New: '{new_value}'")
            lines[current_line_idx] = f"{key}={new_value}\n"
            updates_count += 1

    # Save
    print("\n" + "-" * 60)
    print(f"Summary:")
    print(f"  Updates Applied: {updates_count}")
    print(f"  Placeholders Skipped: {skipped_placeholders}")

    if updates_count > 0:
        print(f"Saving updates to {ini_path}...")
        save_ini_lines(ini_path, lines)
        print("Done.")
    else:
        print("No updates needed.")

def main():
    parser = argparse.ArgumentParser(description="Apply naming fixes to Star Citizen language pack")
    parser.add_argument("--channel", default="LIVE", help="Channel (LIVE, PTU, HOTFIX)")
    parser.add_argument("--extract-dir", default=None, help="Directory with extracted XML data")
    args, _ = parser.parse_known_args()

    extract_dir = Path(args.extract_dir) if args.extract_dir else REPO_ROOT / "extracted"
    libs_dir = extract_dir / "dcb" / "Data" / "libs"
    ini_path = get_remix_ini(args.channel)

    if not ini_path.exists():
        print(f"ERROR: INI file not found at {ini_path}")
        sys.exit(1)

    if not libs_dir.exists():
        print(f"ERROR: Extracted XML data not found at {libs_dir}")
        print("Run the extraction step first.")
        sys.exit(1)

    # Load name dict from the INI for resolution
    name_dict = audit_sc_native.parse_global_ini(ini_path)
    if not name_dict:
        print("ERROR: Failed to parse INI file")
        sys.exit(1)

    apply_fixes(libs_dir, ini_path, name_dict)

if __name__ == "__main__":
    main()
