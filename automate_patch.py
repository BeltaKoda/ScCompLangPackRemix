"""
Star Citizen Language Pack Automation Tool

This script orchestrates the entire process of updating the language pack for a new patch.
It runs the following steps:
1. Extraction: Extracts game data (Game.dcb, global.ini) using unp4k/unforge.
2. Audit: Scans for component naming discrepancies.
3. Fix: Applies automated naming fixes to the global.ini.
4. Deploy: Optionally deploys the fixed file to the game directory.

Usage:
    python automate_patch.py [--version 4.5.0] [--channel PTU] [--deploy]
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# Configuration
SC_INSTALL_PATH = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"
REPO_ROOT = Path(__file__).parent

def run_step(script_name: str, description: str, args: list) -> bool:
    """Run a python script as a subprocess with arguments."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    
    script_path = REPO_ROOT / script_name
    if not script_path.exists():
        print(f"Error: Script {script_name} not found!")
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

def deploy_file(version: str, channel: str):
    """Deploy the fixed global.ini to the game directory."""
    print(f"\n{'='*60}")
    print("STEP: Deploying to Game Directory")
    print(f"{'='*60}")
    
    source_path = REPO_ROOT / version / channel / "data" / "Localization" / "english" / "global.ini"
    
    dest_dir = Path(SC_INSTALL_PATH) / "data" / "Localization" / "english"
    dest_path = dest_dir / "global.ini"
    
    if not source_path.exists():
        print(f"Error: Source file not found at {source_path}")
        return
        
    if not Path(SC_INSTALL_PATH).exists():
        print(f"Error: Star Citizen installation not found at {SC_INSTALL_PATH}")
        return
        
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        print(f"Success! Deployed to: {dest_path}")
    except Exception as e:
        print(f"Error deploying file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Star Citizen Language Pack Automation')
    parser.add_argument('--version', default='4.4.0', help='Game version (e.g., 4.4.0)')
    parser.add_argument('--channel', default='PTU', help='Game channel (e.g., PTU, LIVE)')
    parser.add_argument('--deploy', action='store_true', help='Deploy to game directory')
    args = parser.parse_args()

    print("Star Citizen Language Pack Automation")
    print("-------------------------------------")
    print(f"Target Version: {args.version}")
    print(f"Target Channel: {args.channel}")
    
    # Construct args to pass to subprocesses
    sub_args = ['--version', args.version, '--channel', args.channel]
    
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
        deploy_file(args.version, args.channel)
    else:
        print("\nSkipping deployment. Use --deploy to auto-install.")
        print(f"You can manually copy the file from: {args.version}/{args.channel}/data/Localization/english/global.ini")

if __name__ == "__main__":
    main()
