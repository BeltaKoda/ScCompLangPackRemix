#!/usr/bin/env python3
"""
Consolidated workflow for processing a new Star Citizen patch.

Usage:
    # Full workflow — extract stock INI from Data.p4k and merge with previous remix:
    python scripts/new_patch.py --channel LIVE --old-channel LIVE

    # Using a pre-downloaded stock INI:
    python scripts/new_patch.py --channel LIVE --stock-file /path/to/stock.ini

    # Specify custom title bar branding:
    python scripts/new_patch.py --channel LIVE --branding "4.7.0 LIVE - BeltaKoda's ScCompLangPackRemix"
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_channel_dir, get_stock_ini, get_remix_ini

REPO_ROOT = get_repo_root()
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_script(script_name: str, args: list, description: str) -> bool:
    """Run a Python script from the scripts directory."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False

    print(f"\n{'=' * 60}")
    print(f"  {description}")
    print(f"{'=' * 60}")

    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Process a new Star Citizen patch")
    parser.add_argument("--channel", required=True, help="Channel: LIVE, PTU, or HOTFIX")
    parser.add_argument("--old-channel", default=None, help="Previous channel (defaults to same as --channel)")
    parser.add_argument("--stock-file", type=Path, default=None, help="Path to pre-downloaded stock global.ini")
    parser.add_argument("--branding", default=None, help="Custom Frontend_PU_Version branding string")
    parser.add_argument("--skip-extract", action="store_true", help="Skip extraction (stock-global.ini must already exist)")
    args = parser.parse_args()

    old_channel = args.old_channel or args.channel

    print(f"Channel:        {args.channel}")
    print(f"Old Channel:    {old_channel}")

    # Verify old remix exists
    old_remix_path = get_remix_ini(old_channel)
    if not old_remix_path.exists():
        print(f"ERROR: Previous remix not found at {old_remix_path}")
        sys.exit(1)

    # Step 1: Obtain stock global.ini
    stock_ini_path = get_stock_ini(args.channel)

    if not args.skip_extract:
        if args.stock_file:
            extract_args = [
                "--channel", args.channel,
                "--local-file", str(args.stock_file),
            ]
        else:
            extract_args = [
                "--channel", args.channel,
            ]

        if not run_script("extract_stock_ini.py", extract_args, "Step 1: Obtain Stock global.ini"):
            print("FAILED: Could not obtain stock global.ini")
            sys.exit(1)
    else:
        if not stock_ini_path.exists():
            print(f"ERROR: --skip-extract used but {stock_ini_path} does not exist")
            sys.exit(1)
        print(f"Using existing stock INI: {stock_ini_path}")

    # Step 2: Create directory structure
    remix_path = get_remix_ini(args.channel)
    remix_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 3: Run process-new-patch.py
    merge_args = [
        "--old-remix", str(old_remix_path),
        "--new-stock", str(stock_ini_path),
        "--output", str(remix_path),
    ]

    if not run_script("process-new-patch.py", merge_args, "Step 2: Merge Old Remix + New Stock"):
        print("FAILED: Merge step failed")
        sys.exit(1)

    # Step 4: Apply custom branding if specified
    if args.branding:
        print(f"\nApplying custom branding: {args.branding}")
        try:
            with open(remix_path, "r", encoding="utf-8-sig", errors="replace") as f:
                lines = f.readlines()

            with open(remix_path, "w", encoding="utf-8-sig") as f:
                for line in lines:
                    if line.startswith("Frontend_PU_Version="):
                        f.write(f"Frontend_PU_Version={args.branding}\n")
                    else:
                        f.write(line)
            print("Branding applied.")
        except Exception as e:
            print(f"WARNING: Failed to apply branding: {e}")

    # Step 5: Show diff summary
    # Compare old stock with new stock if both exist and channels differ
    if old_channel != args.channel:
        old_stock_path = get_stock_ini(old_channel)
        if old_stock_path.exists():
            run_script("compare_ini.py", [str(old_stock_path), str(stock_ini_path)],
                        "Step 3: Compare Stock INI Changes")

    # Summary
    print(f"\n{'=' * 60}")
    print("  DONE! Summary")
    print(f"{'=' * 60}")
    print(f"  Stock INI:   {stock_ini_path}")
    print(f"  Remix INI:   {remix_path}")
    print(f"  user.cfg:    {get_channel_dir(args.channel) / 'user.cfg'}")
    print()
    print("Next steps:")
    print("  1. Review new components — search for entries without remix prefixes")
    print("  2. Run generate_manifest.py for a component overview")
    print("  3. Manually remix new components (M/I/C/R/S + size + grade)")
    print("  4. Verify with erkul.games or finder.cstone.space")
    print("  5. Commit to feature branch and push")
    print("  6. Create GitHub release via create-release.yml workflow")


if __name__ == "__main__":
    main()
