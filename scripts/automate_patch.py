"""
Star Citizen Language Pack Automation Tool

This script orchestrates the entire process of updating the language pack for a new patch.
It runs the following steps:
1. Extraction: Extracts game data (Game.dcb, global.ini) using scdatatools.
2. Audit: Scans for component naming discrepancies.
3. Fix: Applies automated naming fixes to the global.ini.
4. Deploy: Optionally deploys the fixed file to the game directory.
5. Cleanup: Removes the temporary extraction directory.

Usage:
    python automate_patch.py [--channel PTU] [--deploy] [--auto-cleanup]
"""

import os
import sys
import subprocess
import shutil
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_sc_install_path

# Configuration
REPO_ROOT = get_repo_root()

def run_step(script_name: str, description: str, args: list) -> bool:
    """Run a python script as a subprocess with arguments."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")

    script_path = REPO_ROOT / "scripts" / script_name
    if not script_path.exists():
        print(f"Error: Script {script_name} not found at {script_path}!")
        return False

    cmd = [sys.executable, str(script_path)] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            check=False
        )

        if result.returncode != 0:
            print(f"Error: {script_name} failed with exit code {result.returncode}")
            return False

        return True

    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def deploy_file(channel: str):
    """Deploy the fixed global.ini to the game directory."""
    print(f"\n{'='*60}")
    print("STEP: Deploying to Game Directory")
    print(f"{'='*60}")

    source_path = REPO_ROOT / channel / "data" / "Localization" / "english" / "global.ini"

    sc_install = get_sc_install_path(channel)
    if sc_install is None:
        print(f"Error: Star Citizen {channel} installation not found")
        print("Set sc_base in config.ini if installed in a non-standard location.")
        return

    dest_dir = sc_install / "data" / "Localization" / "english"
    dest_path = dest_dir / "global.ini"

    if not source_path.exists():
        print(f"Error: Source file not found at {source_path}")
        return

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        print(f"Success! Deployed to: {dest_path}")
    except Exception as e:
        print(f"Error deploying file: {e}")

def cleanup_temp(temp_dir: Path, auto_cleanup: bool):
    """Clean up the temporary directory."""
    print(f"\n{'='*60}")
    print("STEP: Cleanup")
    print(f"{'='*60}")

    if not temp_dir.exists():
        return

    if auto_cleanup:
        should_delete = True
    else:
        print(f"Temporary data is stored in: {temp_dir}")
        print(f"Size: {get_dir_size_mb(temp_dir):.2f} MB")
        response = input("Do you want to delete this temporary data? (y/n): ").lower()
        should_delete = response == 'y'

    if should_delete:
        print(f"Deleting {temp_dir}...")
        try:
            shutil.rmtree(temp_dir)
            print("Cleanup complete.")
        except Exception as e:
            print(f"Error deleting temp dir: {e}")
    else:
        print(f"Skipping cleanup. Data remains in {temp_dir}")

def get_dir_size_mb(path: Path) -> float:
    """Calculate directory size in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)

def main():
    parser = argparse.ArgumentParser(description='Star Citizen Language Pack Automation')
    parser.add_argument('--channel', default='LIVE', help='Game channel (e.g., LIVE, PTU, HOTFIX)')
    parser.add_argument('--deploy', action='store_true', help='Deploy to game directory')
    parser.add_argument('--auto-cleanup', action='store_true', help='Automatically delete temp files without prompting')
    args = parser.parse_args()

    print("Star Citizen Language Pack Automation")
    print("-------------------------------------")
    print(f"Target Channel: {args.channel}")

    # Create Temp Directory
    temp_dir = Path(tempfile.mkdtemp(prefix="ScCompLangPackRemix_"))
    print(f"Created temporary working directory: {temp_dir}")

    try:
        # Construct args to pass to subprocesses
        sub_args = ['--channel', args.channel, '--extract-dir', str(temp_dir)]

        # Step 1: Audit & Extraction (This script handles extraction if needed)
        if not run_step("audit_sc_native.py", "Extracting Data & Initial Audit", sub_args):
            print("Aborting due to failure in Step 1.")
            return

        # Step 2: Apply Fixes
        if not run_step("apply_fixes.py", "Applying Naming Fixes", sub_args):
            print("Aborting due to failure in Step 2.")
            return

        # Step 3: Final Verification
        if not run_step("audit_sc_native.py", "Verifying Fixes", sub_args):
            print("Warning: Final verification reported issues (check report).")

        # Step 4: Deploy (Optional)
        if args.deploy:
            deploy_file(args.channel)
        else:
            print("\nSkipping deployment. Use --deploy to auto-install.")
            print(f"You can manually copy the file from: {args.channel}/data/Localization/english/global.ini")

    finally:
        # Step 5: Cleanup
        cleanup_temp(temp_dir, args.auto_cleanup)

if __name__ == "__main__":
    main()
