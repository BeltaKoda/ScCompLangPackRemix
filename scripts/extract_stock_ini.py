#!/usr/bin/env python3
"""
Extract stock global.ini from Star Citizen's Data.p4k.

Extraction methods (tried in order):
1. scdatatools (pure Python, if installed and compatible)
2. unp4k.exe via Wine (Linux) or directly (Windows)
3. Manual: user provides --local-file

Usage:
    # Auto-detect SC installation and extract:
    python scripts/extract_stock_ini.py --version 4.7.0 --channel LIVE

    # Provide a local file instead of extracting:
    python scripts/extract_stock_ini.py --version 4.7.0 --channel LIVE --local-file /path/to/stock-global.ini
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_data_p4k, get_version_dir, get_tools_dir, IS_LINUX, IS_WINDOWS


def _find_wine() -> str | None:
    """Find a working wine binary. Checks LUG Helper runner first, then system wine."""
    # Check LUG Helper runner
    lug_prefix = Path.home() / "Games" / "star-citizen"
    if lug_prefix.exists():
        runners_dir = lug_prefix / "runners"
        if runners_dir.exists():
            for runner in sorted(runners_dir.iterdir(), reverse=True):
                wine_bin = runner / "bin" / "wine"
                if wine_bin.exists():
                    return str(wine_bin)

    # Fall back to system wine
    wine_path = shutil.which("wine")
    if wine_path:
        return wine_path

    return None


def extract_with_scdatatools(p4k_path: Path, output_path: Path) -> bool:
    """Extract global.ini from Data.p4k using scdatatools (pure Python)."""
    try:
        from scdatatools.p4k import P4KFile
    except ImportError:
        return False
    except Exception:
        return False

    print(f"Opening Data.p4k with scdatatools ({p4k_path})...")
    print("This may take a moment for a large file...")

    try:
        p4k = P4KFile(str(p4k_path))
    except Exception as e:
        print(f"scdatatools failed to open Data.p4k: {e}")
        return False

    target_patterns = [
        "Data/Localization/english/global.ini",
        "Data/Libs/Localization/English/global.ini",
    ]

    for pattern in target_patterns:
        print(f"Looking for {pattern}...")
        try:
            matching = [f for f in p4k.filelist if pattern.lower() in f.filename.lower()]
            if matching:
                entry = matching[0]
                print(f"Found: {entry.filename}")
                data = p4k.read(entry)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as out:
                    out.write(data)
                print(f"Extracted to {output_path}")
                return True
        except Exception as e:
            print(f"  Failed with pattern {pattern}: {e}")
            continue

    print("scdatatools: Could not find global.ini in Data.p4k")
    return False


def extract_with_unp4k(p4k_path: Path, output_path: Path) -> bool:
    """Extract global.ini using unp4k.exe (via Wine on Linux, directly on Windows)."""
    unp4k_exe = get_tools_dir() / "unp4k.exe"
    if not unp4k_exe.exists():
        print(f"unp4k.exe not found at {unp4k_exe}")
        return False

    # Build command
    if IS_LINUX:
        wine_bin = _find_wine()
        if wine_bin is None:
            print("ERROR: No Wine binary found. Install Wine or use --local-file.")
            return False
        print(f"Using Wine: {wine_bin}")
        cmd = [wine_bin, str(unp4k_exe), str(p4k_path), "Data/Localization/english/global.ini"]
        env = os.environ.copy()
        env["WINEPREFIX"] = str(Path.home() / "Games" / "star-citizen")
        env["WINEDEBUG"] = "-all"
    else:
        cmd = [str(unp4k_exe), str(p4k_path), "Data/Localization/english/global.ini"]
        env = None

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Running unp4k.exe to extract global.ini...")
        try:
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )

            if result.returncode != 0:
                print(f"unp4k.exe failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"  stderr: {result.stderr[:500]}")
                return False

            # Find the extracted global.ini
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    if f.lower() == "global.ini":
                        extracted = Path(root) / f
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(extracted, output_path)
                        print(f"Extracted to {output_path}")
                        return True

            print("unp4k.exe ran but global.ini was not found in output")
            return False

        except subprocess.TimeoutExpired:
            print("ERROR: unp4k.exe timed out")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
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

        # Try scdatatools first (pure Python, cross-platform)
        print("\nAttempting extraction with scdatatools...")
        success = extract_with_scdatatools(p4k_path, output_path)

        if not success:
            # Fall back to unp4k.exe (via Wine on Linux)
            print("\nscdatatools unavailable or failed. Trying unp4k.exe...")
            success = extract_with_unp4k(p4k_path, output_path)

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
        print("\nERROR: All extraction methods failed.")
        print("You can provide a stock INI manually with --local-file")
        sys.exit(1)


if __name__ == "__main__":
    main()
