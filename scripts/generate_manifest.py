import csv
import os
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_stock_ini, get_remix_ini

parser = argparse.ArgumentParser(description="Generate component manifest from CSV data")
parser.add_argument("--channel", default="LIVE", help="Target channel (LIVE, PTU, HOTFIX)")
parser.add_argument("--ref-channel", default="PTU", help="Reference channel for verified names")
parser.add_argument("--manifest-csv", default=None, help="Path to manifest CSV file")
parser.add_argument("--output", default=None, help="Output markdown file path")
args = parser.parse_args()

REPO_ROOT = get_repo_root()
STOCK_INI = get_stock_ini(args.channel)
PTU_REMIX = get_remix_ini(args.ref_channel)
MANIFEST_CSV = Path(args.manifest_csv) if args.manifest_csv else REPO_ROOT / "dry_run_manifest_ptu.csv"
OUTPUT_MD = Path(args.output) if args.output else REPO_ROOT / f"component_manifest_{args.channel.lower()}.md"

def load_ini(path):
    data = {}
    if not path.exists(): return data
    try:
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
    # Try to find description key
    desc_key = key.replace("Name", "Desc")
    desc = stock_ini_data.get(desc_key, "").lower()

    if "military" in desc: return "Military"
    if "industrial" in desc: return "Industrial"
    if "stealth" in desc: return "Stealth"
    if "competition" in desc: return "Competition"
    if "civilian" in desc: return "Civilian"
    return "Unknown"

def get_prefix(c_type, size, grade, c_class, tracking):
    # Grade mapping for standard components
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
        # Finalized: B[Size], no grade
        return f"B{size}"

    # Standard Components: [Class][Size][Grade]
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
    stock_data = load_ini(STOCK_INI)
    ptu_data = load_ini(PTU_REMIX)

    components = {}
    with open(MANIFEST_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row['key']
            if key in components: continue # Deduplicate

            # Exclusion logic for ship weapons and turrets
            if row['type'] in ["WeaponGun", "Turret", "TurretBase"]:
                continue

            stock_name = stock_data.get(key, "N/A")
            ptu_name = ptu_data.get(key, "N/A")

            c_class = get_class_from_desc(key, stock_data)
            tracking = row.get('tracking', 'N/A')
            proposed_prefix = get_prefix(row['type'], row['size'], row['grade'], c_class, tracking)
            proposed_name = f"{proposed_prefix} {stock_name}"

            # Status Identification
            if ptu_name == "N/A":
                status = "NEW ITEM"
            elif ptu_name == stock_name:
                status = "NEEDS REMIX"
            # Flexible regex to allow IR/EM/CS/BOMB prefixes as Verified if they follow the pattern
            elif re.match(r"^([A-Z]{1,4})\d[A-Z]\s", ptu_name):
                status = "VERIFIED"
                proposed_name = ptu_name # Keep existing remix
            else:
                status = "REMIXED (MISMATCH?)"

            components[key] = {
                "Type": row['type'],
                "Size": row['size'],
                "Grade": row['grade'],
                "Class": c_class,
                "Tracking": tracking,
                "Stock": stock_name,
                "Proposed": proposed_name,
                "Status": status
            }

    # Sort
    sorted_comps = sorted(components.values(), key=lambda x: (x['Type'], x['Size'], x['Stock']))

    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(f"# Component Manifest: {args.channel}\n\n")
        f.write(f"This table compares the **{args.channel} Stock** with your **Verified {args.ref_channel} Remix**.\n")
        f.write("Missiles and Torpedoes now use functional prefixes (**IR/EM/CS**) and Bombs use (**BOMB**).\n\n")
        f.write("| Type | S | G | Tracking | Class | Stock Name | Proposed Remix | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for c in sorted_comps:
            f.write(f"| {c['Type']} | {c['Size']} | {c['Grade']} | {c['Tracking']} | {c['Class']} | {c['Stock']} | **{c['Proposed']}** | {c['Status']} |\n")

    # Append Ground Missiles (GMISL) if any were found in INI but not in manifest
    print("Synching GMISL from INI...")
    g_missiles = []
    for key in stock_data:
        if key.startswith("item_NameGMISL_") and not key.endswith("_short"):
            if key in components: continue

            tracking = "N/A"
            if "_IR_" in key: tracking = "Infrared"
            elif "_EM_" in key: tracking = "Electromagnetic"
            elif "_CS_" in key: tracking = "CrossSection"

            size_match = re.search(r'_S(\d+)_', key)
            size = size_match.group(1) if size_match else "0"

            prefix = get_prefix("GroundMissile", size, "1", "Unknown", tracking)
            stock_name = stock_data[key]

            g_missiles.append({
                "Type": "GroundMissile", "Size": size, "Grade": "1", "Tracking": tracking,
                "Class": "Unknown", "Stock": stock_name, "Proposed": f"{prefix} {stock_name}", "Status": "NEW (INI ONLY)"
            })

    if g_missiles:
        with open(OUTPUT_MD, 'a', encoding='utf-8') as f:
            f.write("\n### Ground-Based Ordnance (Synthetic from INI)\n\n")
            f.write("| Type | S | G | Tracking | Class | Stock Name | Proposed Remix | Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for c in sorted(g_missiles, key=lambda x: (x['Size'], x['Stock'])):
                f.write(f"| {c['Type']} | {c['Size']} | {c['Grade']} | {c['Tracking']} | {c['Class']} | {c['Stock']} | **{c['Proposed']}** | {c['Status']} |\n")

    print(f"Generated manifest with {len(sorted_comps)} unique items at {OUTPUT_MD}.")

if __name__ == "__main__":
    main()
