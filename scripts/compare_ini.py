import sys
import os
import io
import argparse

# Ensure UTF-8 output for console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

def load_ini(file_path):
    data = {}
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return None

    try:
        # Star Citizen INI files are typically UTF-8-SIG or UTF-8
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        if '=' in line:
            key, val = line.split('=', 1)
            data[key.strip()] = val.strip()
    return data

def compare_inis(ptu_path, live_path):
    ptu_data = load_ini(ptu_path)
    live_data = load_ini(live_path)

    if ptu_data is None or live_data is None:
        return

    new_keys = []
    changed_keys = []
    removed_keys = []

    for key in live_data:
        if key not in ptu_data:
            new_keys.append((key, live_data[key]))
        elif live_data[key] != ptu_data[key]:
            changed_keys.append((key, ptu_data[key], live_data[key]))

    for key in ptu_data:
        if key not in live_data:
            removed_keys.append(key)

    print(f"Comparison: File A vs File B")
    print(f"----------------------")
    print(f"New keys in B ({len(new_keys)}):")
    for k, v in new_keys:
        print(f"  + {k}={v}")

    print(f"\nChanged values ({len(changed_keys)}):")
    for k, old, new in changed_keys:
        print(f"  * {k}: '{old}' -> '{new}'")

    print(f"\nRemoved keys ({len(removed_keys)}):")
    for k in removed_keys:
        print(f"  - {k}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two Star Citizen INI files")
    parser.add_argument("file_a", help="First INI file (e.g., old stock)")
    parser.add_argument("file_b", help="Second INI file (e.g., new stock)")
    args = parser.parse_args()
    compare_inis(args.file_a, args.file_b)
