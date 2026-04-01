import time
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import re

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_sc_install_path, get_data_p4k

# Configuration
REPO_ROOT = get_repo_root()
EXTRACT_DIR = REPO_ROOT / "extracted_ptu"

def track_step(name, func, *args, **kwargs):
    print(f"[METRIC] Starting {name}...")
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    duration = end - start
    print(f"[METRIC] Finished {name} in {duration:.2f} seconds.")
    return result, duration

def extract_dcb():
    """Extract Game2.dcb from Data.p4k using the built-in P4K reader."""
    p4k_path = get_data_p4k("PTU")
    if p4k_path is None:
        print("ERROR: Data.p4k not found for PTU channel")
        return False

    from p4k_reader import P4KFile

    output_dir = EXTRACT_DIR / "dcb" / "Data"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Opening {p4k_path}...")
    p4k = P4KFile(p4k_path)
    print(f"Loaded {len(p4k.entries):,} entries from P4K")

    for dcb_name in ["Data/Game2.dcb", "Data/Game.dcb"]:
        entry = p4k.find(dcb_name)
        if entry:
            print(f"Found: {entry.filename} ({entry.file_size:,} bytes)")
            out_path = output_dir / Path(dcb_name).name
            data = p4k.read(entry)
            with open(out_path, "wb") as out:
                out.write(data)
            print(f"Extracted to {out_path}")
            return True

    print("ERROR: Could not find Game2.dcb or Game.dcb in Data.p4k")
    return False

def convert_dcb():
    """Convert Game2.dcb to XML using unforge.exe via Wine."""
    dcb_file = EXTRACT_DIR / "dcb" / "Data" / "Game2.dcb"
    if not dcb_file.exists():
        dcb_file = EXTRACT_DIR / "dcb" / "Data" / "Game.dcb"

    if not dcb_file.exists():
        print(f"ERROR: No DCB file found")
        return False

    unforge = REPO_ROOT / "tools" / "unforge.exe"
    if not unforge.exists():
        print(f"ERROR: unforge.exe not found at {unforge}")
        return False

    import subprocess
    print(f"Converting {dcb_file.name} with unforge.exe via Wine...")
    result = subprocess.run(
        ["wine", str(unforge), str(dcb_file)],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        print(f"ERROR: unforge.exe failed: {result.stderr[:500]}")
        return False

    print("Conversion complete.")
    return True

def parse_xmls():
    libs_dir = EXTRACT_DIR / "dcb" / "Data" / "libs"
    scitem_root = libs_dir / "foundry" / "records" / "entities" / "scitem"
    components = []
    total_scanned = 0
    total_parsed = 0

    # Target specific directories for components
    targets = [
        scitem_root / "ships" / "powerplant",
        scitem_root / "ships" / "cooler",
        scitem_root / "ships" / "shieldgenerator",
        scitem_root / "ships" / "quantumdrive",
        scitem_root / "ships" / "radar",
        scitem_root / "ships" / "weapons"
    ]

    for target in targets:
        if not target.exists(): continue
        for xml_file in target.rglob("*.xml"):
            total_scanned += 1
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                attach_def = root.find(".//AttachDef")
                if attach_def is not None:
                    comp_type = attach_def.get("Type")
                    size = attach_def.get("Size")
                    grade = attach_def.get("Grade")
                    loc = attach_def.find("Localization")
                    name_key = loc.get("Name") if loc is not None else "Unknown"

                    tracking_type = "N/A"
                    missile_params = root.find(".//SCItemMissileParams") or root.find(".//SCItemTorpedoParams")
                    if missile_params is not None:
                        target_params = missile_params.find("targetingParams")
                        if target_params is not None:
                            tracking_type = target_params.get("trackingSignalType", "N/A")

                    if tracking_type == "N/A":
                        if "_IR_" in str(xml_file).upper(): tracking_type = "Infrared"
                        elif "_EM_" in str(xml_file).upper(): tracking_type = "Electromagnetic"
                        elif "_CS_" in str(xml_file).upper(): tracking_type = "CrossSection"

                    if name_key:
                        name_key = name_key.lstrip('@')
                        if "template" in str(xml_file).lower() and any(c['key'] == name_key for c in components):
                            continue

                        components.append({
                            "key": name_key,
                            "size": size,
                            "grade": grade,
                            "type": comp_type,
                            "tracking": tracking_type,
                            "path": str(xml_file.relative_to(scitem_root))
                        })
                        total_parsed += 1
            except:
                continue

    return components, total_scanned, total_parsed

def main():
    metrics = {}
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract (P4K -> DCB)
    dcb_output_game2 = EXTRACT_DIR / "dcb" / "Data" / "Game2.dcb"
    dcb_output_game = EXTRACT_DIR / "dcb" / "Data" / "Game.dcb"

    if not dcb_output_game2.exists() and not dcb_output_game.exists():
        _, metrics["extraction"] = track_step("Extraction (P4K -> DCB)", extract_dcb)
    else:
        print("[SKIP] DCB already exists in extracted_ptu/dcb/Data.")
        metrics["extraction"] = 0

    # Step 2: Convert (DCB -> XML)
    xml_check_path = EXTRACT_DIR / "dcb" / "Data" / "libs" / "foundry" / "records"
    if not xml_check_path.exists() or not any(xml_check_path.rglob("*.xml")):
        _, metrics["conversion"] = track_step("Conversion (DCB -> XML)", convert_dcb)
    else:
        print("[SKIP] XMLs already exist in extracted_ptu/dcb/Data/libs/foundry/records.")
        metrics["conversion"] = 0

    # Step 3: Parse
    (components, scanned, parsed), duration = track_step("Parsing Components", parse_xmls)
    metrics['parsing'] = duration
    metrics['scanned'] = scanned
    metrics['parsed'] = parsed

    print("\n" + "="*40)
    print("METRICS: PTU")
    print("="*40)
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # Output manifest
    import csv
    manifest_file = REPO_ROOT / "dry_run_manifest_ptu.csv"
    with open(manifest_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["key", "size", "grade", "type", "tracking", "path"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(components)
    print(f"Manifest written to {manifest_file}")

if __name__ == "__main__":
    main()
