import sys
import os
import argparse

parser = argparse.ArgumentParser(description="Find and replace a version string in a Star Citizen INI file")
parser.add_argument("--file", required=True, help="Path to the INI file")
parser.add_argument("--old-string", required=True, help="The target substring to find")
parser.add_argument("--new-string", required=True, help="The replacement string")
args = parser.parse_args()

file_path = args.file
target_substring = args.old_string
replacement_string = args.new_string

print(f"Processing {file_path}...")

if not os.path.exists(file_path):
    print(f"Error: File not found at {file_path}")
    sys.exit(1)

# Read content
try:
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    print("UTF-8-SIG decode failed, trying UTF-8...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print("UTF-8 decode failed, trying Latin-1...")
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()

found = False
new_lines = []
for line in lines:
    if target_substring in line:
        print(f"Found target line: {line.strip()}")
        new_lines.append(replacement_string + "\n")
        found = True
    else:
        new_lines.append(line)

if found:
    # Write back
    with open(file_path, 'w', encoding='utf-8-sig') as f:
        f.writelines(new_lines)
    print("Successfully updated version string.")
else:
    print(f"Error: Target string '{target_substring}' not found in file.")
    sys.exit(1)
