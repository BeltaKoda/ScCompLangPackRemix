import sys

file_path = "LIVE/data/Localization/english/global.ini"

try:
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

start = 9810
end = 9815

for i in range(start, end):
    if i < len(lines):
        print(f"{i+1}: {repr(lines[i])}")
