import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_repo_root, get_sc_install_path

try:
    import scdatatools
    from scdatatools.sc import StarCitizen
except ImportError as e:
    print(f"scdatatools import failed: {e}")
    print("Install with: pip install scdatatools")
    sys.exit(1)

REPO_ROOT = get_repo_root()

def find_sc_install(channel: str = "LIVE") -> str | None:
    """Finds the Star Citizen installation path."""
    print("Searching for Star Citizen installation...")
    sc_path = get_sc_install_path(channel)
    if sc_path is not None:
        return str(sc_path)
    return None

def parse_ini(file_path):
    """Parses the global.ini file into a dictionary."""
    print(f"Parsing {file_path}...")
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()
    except UnicodeDecodeError:
        print("UTF-8-SIG failed, trying utf-16")
        with open(file_path, 'r', encoding='utf-16') as f:
            for line in f:
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()
    print(f"Loaded {len(data)} entries from INI.")
    return data

def generate_expected_name(name, size, grade, type_str):
    """
    Generates the expected name based on the remix format: [Type][Size][Grade] [Name]
    """
    type_map = {
        "Military": "M",
        "Industrial": "I",
        "Civilian": "C",
        "Competition": "R",
        "Stealth": "S"
    }

    type_code = type_map.get(type_str, "?")
    return f"{type_code}{size}{grade} {name}"

def main():
    # 1. Find SC Install
    sc_path = find_sc_install()
    if not sc_path:
        print("Could not find Star Citizen installation.")
        print("Set sc_base in config.ini if installed in a non-standard location.")
        return

    print(f"Found Star Citizen at: {sc_path}")

    # 2. Initialize scdatatools
    try:
        sc = StarCitizen(sc_path)
        print("Initialized StarCitizen API.")
    except Exception as e:
        print(f"Failed to initialize scdatatools: {e}")
        return

    # 3. Explore available managers
    print("Exploring scdatatools managers...")
    print(f"Available attributes: {[attr for attr in dir(sc) if not attr.startswith('_')]}")

    # Try localization
    if hasattr(sc, 'localization'):
        print("\nExploring localization data...")
        loc = sc.localization
        print(f"Localization type: {type(loc)}")
        print(dir(loc))

        # Try to find component names
        if hasattr(loc, 'data') or hasattr(loc, 'strings'):
            data = loc.data if hasattr(loc, 'data') else loc.strings
            print(f"\nLocalization has {len(data)} entries.")

            # Search for shield component names
            print("\nSearching for shield component names...")
            shield_keys = [k for k in list(data.keys())[:1000] if 'shield' in k.lower() and 'item_name' in k.lower()]
            print(f"Found {len(shield_keys)} shield name keys (sample of first 1000).")

            for key in shield_keys[:5]:
                print(f"  {key}: {data[key]}")

    print("\n\nAlternative approach needed:")
    print("scdatatools may require using the CLI tool 'scdt' to export component data.")
    print("Or, we could parse the extracted localization .ini files directly.")

if __name__ == "__main__":
    main()
