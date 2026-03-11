import argparse

parser = argparse.ArgumentParser(description="Search a Star Citizen INI file for specific terms")
parser.add_argument("file", help="Path to the INI file to search")
parser.add_argument("--terms", nargs="+", default=["Arctic", "XL-1", "QuadraCell", "item_Name"],
                    help="Search terms (default: Arctic XL-1 QuadraCell item_Name)")
args = parser.parse_args()

file_path = args.file

print(f"Reading {file_path}...")

try:
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    print("UTF-8-SIG failed, trying utf-16")
    with open(file_path, 'r', encoding='utf-16') as f:
        lines = f.readlines()
except Exception as e:
    print(f"Error reading file: {e}")
    exit(1)

print(f"Read {len(lines)} lines.")

for term in args.terms:
    print(f"Searching for '{term}'...")
    count = 0
    for i, line in enumerate(lines):
        if term.lower() in line.lower():
            print(f"Found at line {i+1}: {line.strip()}")
            count += 1
            if count >= 5:
                print("... (stopping after 5 matches)")
                break
    if count == 0:
        print(f"'{term}' NOT FOUND.")
