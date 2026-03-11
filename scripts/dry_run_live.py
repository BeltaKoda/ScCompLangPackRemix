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
EXTRACT_DIR = REPO_ROOT / "extracted_live"

class ComponentData:
    def __init__(self, key: str, stock_name: str, size: str, grade: str, type: str, raw_xml: str):
        self.key = key
        self.stock_name = stock_name
        self.size = size
        self.grade = grade
        self.type = type
        self.raw_xml = raw_xml

def track_step(name, func, *args, **kwargs):
    print(f"[METRIC] Starting {name}...")
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    duration = end - start
    print(f"[METRIC] Finished {name} in {duration:.2f} seconds.")
    return result, duration

def extract_dcb():
    p4k_path = get_data_p4k("LIVE")
    if p4k_path is None:
        print("ERROR: Data.p4k not found for LIVE channel")
        return False

    try:
        from scdatatools.p4k import P4KFile
    except ImportError:
        print("ERROR: scdatatools not installed. Install with: pip install scdatatools")
        return False

    output_dir = EXTRACT_DIR / "dcb"
    output_dir.mkdir(parents=True, exist_ok=True)

    p4k = P4KFile(str(p4k_path))

    # Try Game2.dcb first (4.4.0+)
    for dcb_name in ["Data/Game2.dcb", "Data/Game.dcb"]:
        matching = [f for f in p4k.filelist if dcb_name.lower() in f.filename.lower()]
        if matching:
            data = p4k.read(matching[0])
            out_path = output_dir / matching[0].filename
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as out:
                out.write(data)
            print(f"Extracted: {matching[0].filename}")
            return True

    print("ERROR: Could not find Game2.dcb or Game.dcb in Data.p4k")
    return False

def convert_dcb():
    dcb_file = EXTRACT_DIR / "dcb" / "Data" / "Game2.dcb"
    if not dcb_file.exists():
        dcb_file = EXTRACT_DIR / "dcb" / "Data" / "Game.dcb"

    if not dcb_file.exists():
        print(f"ERROR: No DCB file found")
        return False

    try:
        from scdatatools.forge import DataCoreBinary
        dcb = DataCoreBinary(dcb_file)
        dcb.dump_to(EXTRACT_DIR / "dcb" / "Data")
        return True
    except ImportError:
        print("ERROR: scdatatools not installed")
        return False
    except Exception as e:
        print(f"ERROR: DCB conversion failed: {e}")
        return False

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

                    # Extract Tracking Type for Missiles/Torpedoes
                    tracking_type = "N/A"
                    missile_params = root.find(".//SCItemMissileParams") or root.find(".//SCItemTorpedoParams")
                    if missile_params is not None:
                        target_params = missile_params.find("targetingParams")
                        if target_params is not None:
                            tracking_type = target_params.get("trackingSignalType", "N/A")

                    # Fallback: check if the name contains IR/EM/CS
                    if tracking_type == "N/A":
                        if "_IR_" in str(xml_file).upper(): tracking_type = "Infrared"
                        elif "_EM_" in str(xml_file).upper(): tracking_type = "Electromagnetic"
                        elif "_CS_" in str(xml_file).upper(): tracking_type = "CrossSection"

                    if name_key:
                        name_key = name_key.lstrip('@')
                        # Deduplicate by key, keep the most 'specific' one (ignore templates)
                        if "template" in str(xml_file).lower() and name_key in [c['key'] for c in components]:
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

    # Step 1: Extract (P4K -> DCB)
    dcb_output_path_game2 = EXTRACT_DIR / "dcb" / "Data" / "Game2.dcb"
    dcb_output_path_game = EXTRACT_DIR / "dcb" / "Data" / "Game.dcb"

    if not dcb_output_path_game2.exists() and not dcb_output_path_game.exists():
        _, metrics["extraction"] = track_step("Extraction (P4K -> DCB)", extract_dcb)
    else:
        print("[SKIP] DCB already exists in extracted_live/dcb/Data.")
        metrics["extraction"] = 0

    # Step 2: Convert (DCB -> XML)
    xml_check_path = EXTRACT_DIR / "dcb" / "Data" / "libs" / "foundry" / "records"

    if not xml_check_path.exists() or not any(xml_check_path.rglob("*.xml")):
        _, metrics["conversion"] = track_step("Conversion (DCB -> XML)", convert_dcb)
    else:
        print("[SKIP] XMLs already exist in extracted_live/dcb/Data/libs/foundry/records.")
        metrics["conversion"] = 0

    # Step 3: Parse
    (components, scanned, parsed), duration = track_step("Parsing Components", parse_xmls)
    metrics['parsing'] = duration
    metrics['scanned'] = scanned
    metrics['parsed'] = parsed

    print("\n" + "="*40)
    print("RESUME OF METRICS")
    print("="*40)
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # Output manifest to CSV for secondary processing
    import csv
    with open("dry_run_manifest.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["key", "size", "grade", "type", "tracking", "path"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(components)

if __name__ == "__main__":
    main()
