import os
import sys
import shutil
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_sc_install_path, get_remix_ini

parser = argparse.ArgumentParser(description="Install remixed global.ini to Star Citizen game directory")
parser.add_argument("--version", default="4.6.0", help="Game version (e.g., 4.6.0)")
parser.add_argument("--channel", default="PTU", help="Channel to install to (LIVE, PTU)")
args = parser.parse_args()

SOURCE_FILE = get_remix_ini(args.version, args.channel)

def install():
    print(f"Installing global.ini to {args.channel}...")

    if not SOURCE_FILE.exists():
        print(f"Error: Source file not found at {SOURCE_FILE}")
        return

    sc_path = get_sc_install_path(args.channel)
    if sc_path is None:
        print(f"Error: Star Citizen {args.channel} installation not found")
        print("Set sc_base in config.ini if installed in a non-standard location.")
        return

    dest_dir = sc_path / "data" / "Localization" / "english"
    dest_path = dest_dir / "global.ini"

    try:
        if not dest_dir.exists():
            print(f"Creating directory: {dest_dir}")
            dest_dir.mkdir(parents=True, exist_ok=True)

        print(f"Copying {SOURCE_FILE} to {dest_path}...")
        shutil.copy2(SOURCE_FILE, dest_path)
        print("Installation successful!")

    except Exception as e:
        print(f"Error installing file: {e}")

if __name__ == "__main__":
    install()
