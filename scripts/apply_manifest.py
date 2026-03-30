import csv
import os
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_stock_ini, get_remix_ini

parser = argparse.ArgumentParser(description="Apply manifest CSV data to generate a remixed INI")
parser.add_argument("--channel", default="LIVE", help="Target channel (LIVE, PTU, HOTFIX)")
parser.add_argument("--ref-channel", default="PTU", help="Reference channel for verified names")
parser.add_argument("--manifest-csv", default=None, help="Path to manifest CSV file")
parser.add_argument("--branding", default=None, help="Custom branding string for Frontend_PU_Version")
args = parser.parse_args()

REPO_ROOT = get_repo_root()
STOCK_INI = get_stock_ini(args.channel)
PTU_REMIX = get_remix_ini(args.ref_channel)
MANIFEST_CSV = Path(args.manifest_csv) if args.manifest_csv else REPO_ROOT / "dry_run_manifest_ptu.csv"
OUTPUT_INI = get_remix_ini(args.channel)

BRANDING_VERSION = args.branding or f"{args.channel} - BeltaKoda's ScCompLangPackRemix"

def load_ini(path):
    data = {}
    if not path.exists(): return data
    try:
        # Stock files often have BOM, remix files might not. Using utf-8-sig for reading.
        with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        k, v = parts
                        data[k.strip()] = v.strip()
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return data

def get_class_from_desc(key, stock_ini_data):
    desc_key = key.replace("Name", "Desc")
    desc = stock_ini_data.get(desc_key, "").lower()

    if "military" in desc: return "Military"
    if "industrial" in desc: return "Industrial"
    if "stealth" in desc: return "Stealth"
    if "competition" in desc: return "Competition"
    if "civilian" in desc: return "Civilian"
    return "Unknown"

def get_prefix(c_type, size, grade, c_class, tracking):
    grade_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
    prefix_grade = grade_map.get(grade, "A")

    if c_type in ["Missile", "Torpedo", "GroundMissile"]:
        track_map = {
            "Infrared": "IR",
            "Electromagnetic": "EM",
            "CrossSection": "CS"
        }
        track_prefix = track_map.get(tracking, "MSL")
        if c_type == "GroundMissile":
            return f"G-{track_prefix}"
        return track_prefix

    if c_type == "Bomb":
        return f"B{size}"

    class_prefix_map = {
        'Military': 'M',
        'Civilian': 'C',
        'Industrial': 'I',
        'Stealth': 'S',
        'Competition': 'R',
    }
    prefix_class = class_prefix_map.get(c_class, 'C')
    return f"{prefix_class}{size}{prefix_grade}"

def main():
    print(f"Loading stock data from {STOCK_INI}...")
    stock_data = load_ini(STOCK_INI)

    print(f"Loading reference data from {PTU_REMIX}...")
    ptu_data = load_ini(PTU_REMIX)

    print(f"Processing manifest from {MANIFEST_CSV}...")
    final_data = stock_data.copy()

    # Counter for stats
    counts = {"Verified": 0, "New/Ordnance": 0}

    with open(MANIFEST_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row['key']
            # Exclusion logic for ship weapons and turrets
            if row['type'] in ["WeaponGun", "Turret", "TurretBase"]:
                continue

            stock_name = stock_data.get(key)
            if not stock_name: continue

            ptu_name = ptu_data.get(key)
            is_ordnance = row['type'] in ["Missile", "Torpedo", "Bomb"]

            # Derive prefix for any item meeting the criteria
            c_class = get_class_from_desc(key, stock_data)
            tracking = row.get('tracking', 'N/A')
            prefix = get_prefix(row['type'], row['size'], row['grade'], c_class, tracking)

            if ptu_name and ptu_name != stock_name and not is_ordnance:
                # Use the verified PTU remix for standard components
                final_data[key] = ptu_name
                counts["Verified"] += 1
            else:
                # 2. Apply functional names to Main and Short names for Ordnance
                final_data[key] = f"{prefix} {stock_name}"

                if is_ordnance:
                    short_key = f"{key}_short"
                    if short_key in stock_data:
                        stock_short = stock_data[short_key]
                        final_data[short_key] = f"{prefix} {stock_short}"

                counts["New/Ordnance"] += 1

    # 2.5 Handle Ground Missiles (GMISL) that might be missing from manifest
    print("Checking for Ground Missiles (GMISL)...")
    for key in list(stock_data.keys()):
        if key.startswith("item_NameGMISL_") and not key.endswith("_short"):
            if key in final_data and final_data[key] != stock_data[key]:
                continue # Already processed

            # Infer tracking and size from key
            tracking = "N/A"
            if "_IR_" in key: tracking = "Infrared"
            elif "_EM_" in key: tracking = "Electromagnetic"
            elif "_CS_" in key: tracking = "CrossSection"

            size_match = re.search(r'_S(\d+)_', key)
            size = size_match.group(1) if size_match else "0"

            prefix = get_prefix("GroundMissile", size, "1", "Unknown", tracking)
            stock_name = stock_data[key]
            final_data[key] = f"{prefix} {stock_name}"

            short_key = f"{key}_short"
            if short_key in stock_data:
                final_data[short_key] = f"{prefix} {stock_data[short_key]}"
            counts["New/Ordnance"] += 1

    # 3. Apply Branding
    print(f"Applying branding: {BRANDING_VERSION}")
    # Update both the plain key and the ,P variant if they exist
    branding_found = False
    for k in list(final_data.keys()):
        if k.startswith("Frontend_PU_Version"):
            final_data[k] = BRANDING_VERSION
            branding_found = True

    if not branding_found:
        final_data["Frontend_PU_Version"] = BRANDING_VERSION

    # 4. Save final INI
    print(f"Saving remixed INI to {OUTPUT_INI}...")
    OUTPUT_INI.parent.mkdir(parents=True, exist_ok=True)

    # Write with utf-8-sig to match Star Citizen expectations
    with open(OUTPUT_INI, 'w', encoding='utf-8-sig') as f:
        for k, v in final_data.items():
            f.write(f"{k}={v}\n")

    print(f"Successfully applied manifest names.")
    print(f" - Preserved {counts['Verified']} verified names from reference.")
    print(f" - Applied {counts['New/Ordnance']} new/functional names.")

if __name__ == "__main__":
    main()
