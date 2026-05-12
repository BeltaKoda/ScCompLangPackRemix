#!/usr/bin/env python3
import argparse
import csv
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_data_p4k, get_repo_root


REPO_ROOT = get_repo_root()


def track_step(name, func, *args, **kwargs):
    print(f"[METRIC] Starting {name}...")
    start = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start
    print(f"[METRIC] Finished {name} in {duration:.2f} seconds.")
    return result, duration


def extract_dcb(channel: str, extract_dir: Path):
    p4k_path = get_data_p4k(channel)
    if p4k_path is None:
        print(f"ERROR: Data.p4k not found for {channel} channel")
        return False

    from p4k_reader import P4KFile

    output_dir = extract_dir / "dcb" / "Data"
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


def count_xml_files(xml_root: Path) -> int:
    if not xml_root.exists():
        return 0
    return sum(1 for _ in xml_root.rglob("*.xml"))


def convert_dcb(extract_dir: Path, timeout_seconds: int = 1200, progress_interval: int = 30, min_xml_count: int = 10000):
    dcb_file = extract_dir / "dcb" / "Data" / "Game2.dcb"
    if not dcb_file.exists():
        dcb_file = extract_dir / "dcb" / "Data" / "Game.dcb"

    if not dcb_file.exists():
        print("ERROR: No DCB file found")
        return False

    unforge = REPO_ROOT / "tools" / "unforge.exe"
    if not unforge.exists():
        print(f"ERROR: unforge.exe not found at {unforge}")
        return False

    data_dir = extract_dir / "dcb" / "Data"
    xml_root = data_dir / "libs" / "foundry" / "records"

    print(f"Converting {dcb_file.name} with unforge.exe via Wine...")
    print(f"Progress: reporting XML file count every {progress_interval}s (timeout {timeout_seconds}s)")

    stdout_path = extract_dir / "unforge.stdout.log"
    stderr_path = extract_dir / "unforge.stderr.log"
    with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
        proc = subprocess.Popen(["wine", str(unforge), str(dcb_file)], stdout=stdout, stderr=stderr, text=True)
        start = time.time()
        last_report = -progress_interval
        while proc.poll() is None:
            elapsed = int(time.time() - start)
            if elapsed - last_report >= progress_interval:
                last_report = elapsed
                count = count_xml_files(xml_root)
                print(f"[CONVERT] {elapsed // 60:02d}:{elapsed % 60:02d} XML files: {count:,}", flush=True)
            if elapsed > timeout_seconds:
                proc.kill()
                proc.wait()
                print(f"ERROR: unforge.exe timed out after {timeout_seconds}s")
                print(f"See logs: {stdout_path}, {stderr_path}")
                return False
            time.sleep(1)
        returncode = proc.returncode

    if returncode != 0:
        print(f"ERROR: unforge.exe failed with exit code {returncode}")
        print(f"See logs: {stdout_path}, {stderr_path}")
        return False

    xml_count = count_xml_files(xml_root)
    if xml_count < min_xml_count:
        print(f"ERROR: XML extraction looks partial ({xml_count:,} XML files; expected at least {min_xml_count:,}).")
        print("Use --force-convert to remove partial output and rerun conversion.")
        print(f"See logs: {stdout_path}, {stderr_path}")
        return False

    print(f"Conversion complete. XML files: {xml_count:,}")
    return True


def parse_xmls(extract_dir: Path):
    libs_dir = extract_dir / "dcb" / "Data" / "libs"
    scitem_root = libs_dir / "foundry" / "records" / "entities" / "scitem"
    components = []
    total_scanned = 0
    total_parsed = 0
    seen_keys = set()

    targets = [
        scitem_root / "ships" / "powerplant",
        scitem_root / "ships" / "cooler",
        scitem_root / "ships" / "shieldgenerator",
        scitem_root / "ships" / "quantumdrive",
        scitem_root / "ships" / "radar",
        scitem_root / "ships" / "weapons",
    ]

    for target in targets:
        if not target.exists():
            continue
        for xml_file in target.rglob("*.xml"):
            total_scanned += 1
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                attach_def = root.find(".//AttachDef")
                if attach_def is None:
                    continue

                comp_type = attach_def.get("Type")
                size = attach_def.get("Size")
                grade = attach_def.get("Grade")
                loc = attach_def.find("Localization")
                name_key = loc.get("Name") if loc is not None else None

                if not name_key:
                    continue

                name_key = name_key.lstrip("@")
                if "template" in str(xml_file).lower() and name_key in seen_keys:
                    continue

                tracking_type = "N/A"
                missile_params = root.find(".//SCItemMissileParams")
                if missile_params is None:
                    missile_params = root.find(".//SCItemTorpedoParams")
                if missile_params is not None:
                    target_params = missile_params.find("targetingParams")
                    if target_params is not None:
                        tracking_type = target_params.get("trackingSignalType", "N/A")

                if tracking_type == "N/A":
                    upper_path = str(xml_file).upper()
                    if "_IR_" in upper_path:
                        tracking_type = "Infrared"
                    elif "_EM_" in upper_path:
                        tracking_type = "Electromagnetic"
                    elif "_CS_" in upper_path:
                        tracking_type = "CrossSection"

                components.append(
                    {
                        "key": name_key,
                        "size": size,
                        "grade": grade,
                        "type": comp_type,
                        "tracking": tracking_type,
                        "path": str(xml_file.relative_to(scitem_root)),
                    }
                )
                seen_keys.add(name_key)
                total_parsed += 1
            except Exception:
                continue

    return components, total_scanned, total_parsed


def main():
    parser = argparse.ArgumentParser(description="Generate a manifest CSV from a channel's current Data.p4k")
    parser.add_argument("--channel", required=True, help="Channel: LIVE, PTU, or HOTFIX")
    parser.add_argument(
        "--extract-dir",
        default=None,
        help="Directory for extracted DCB/XML data (defaults to repo/extracted_<channel>)",
    )
    parser.add_argument(
        "--manifest-csv",
        default=None,
        help="Output manifest CSV path (defaults to repo/dry_run_manifest_<channel>.csv)",
    )
    parser.add_argument("--force-convert", action="store_true", help="Delete existing XML output and rerun DCB->XML conversion")
    parser.add_argument("--timeout", type=int, default=1200, help="DCB conversion timeout in seconds")
    parser.add_argument("--min-xml-count", type=int, default=10000, help="Minimum XML count required after conversion")
    parser.add_argument("--allow-partial", action="store_true", help="Allow low XML count without failing")
    args = parser.parse_args()

    channel = args.channel.upper()
    extract_dir = Path(args.extract_dir) if args.extract_dir else REPO_ROOT / f"extracted_{channel.lower()}"
    manifest_csv = Path(args.manifest_csv) if args.manifest_csv else REPO_ROOT / f"dry_run_manifest_{channel.lower()}.csv"

    metrics = {}
    extract_dir.mkdir(parents=True, exist_ok=True)

    dcb_output_game2 = extract_dir / "dcb" / "Data" / "Game2.dcb"
    dcb_output_game = extract_dir / "dcb" / "Data" / "Game.dcb"
    if not dcb_output_game2.exists() and not dcb_output_game.exists():
        _, metrics["extraction"] = track_step("Extraction (P4K -> DCB)", extract_dcb, channel, extract_dir)
    else:
        print(f"[SKIP] DCB already exists in {extract_dir / 'dcb' / 'Data'}.")
        metrics["extraction"] = 0

    xml_check_path = extract_dir / "dcb" / "Data" / "libs" / "foundry" / "records"
    min_xml_count = 0 if args.allow_partial else args.min_xml_count
    existing_xml_count = count_xml_files(xml_check_path)

    if args.force_convert and (extract_dir / "dcb" / "Data" / "libs").exists():
        print(f"[FORCE] Removing existing XML output under {extract_dir / 'dcb' / 'Data' / 'libs'}")
        shutil.rmtree(extract_dir / "dcb" / "Data" / "libs")
        existing_xml_count = 0

    if existing_xml_count == 0:
        _, metrics["conversion"] = track_step("Conversion (DCB -> XML)", convert_dcb, extract_dir, args.timeout, 30, min_xml_count)
    elif not args.allow_partial and existing_xml_count < args.min_xml_count:
        print(f"ERROR: Existing XML output looks partial ({existing_xml_count:,} XML files; expected at least {args.min_xml_count:,}).")
        print("Rerun with --force-convert to remove partial output and convert again.")
        sys.exit(1)
    else:
        print(f"[SKIP] XMLs already exist in {xml_check_path} ({existing_xml_count:,} XML files).")
        metrics["conversion"] = 0

    (components, scanned, parsed), duration = track_step("Parsing Components", parse_xmls, extract_dir)
    metrics["parsing"] = duration
    metrics["scanned"] = scanned
    metrics["parsed"] = parsed

    with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["key", "size", "grade", "type", "tracking", "path"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(components)

    print("\n" + "=" * 40)
    print(f"METRICS: {channel}")
    print("=" * 40)
    for k, v in metrics.items():
        print(f"{k}: {v}")
    print(f"Manifest written to {manifest_csv}")


if __name__ == "__main__":
    main()
