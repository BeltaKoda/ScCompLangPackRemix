---
name: new-remix
description: Generate a new ScCompLangPackRemix for a new Star Citizen patch. Use when a new SC patch drops and the language pack needs updating.
argument-hint: [version] [channel]
disable-model-invocation: true
---

# New Remix Patch Workflow

Generate a new ScCompLangPackRemix for Star Citizen patch **$ARGUMENTS[0]** on **$ARGUMENTS[1]**.

If no arguments were provided, ask the user for:
1. The patch version (e.g., `4.7.0`)
2. The channel (`LIVE` or `PTU`)

## Step 1: Confirm Patch Details

Ask the user to confirm:
- **Version**: The SC patch version number
- **Channel**: LIVE or PTU
- **Title bar name**: What should `Frontend_PU_Version` display in the main menu?
  - Default format: `[VERSION] [CHANNEL] - BeltaKoda's ScCompLangPackRemix`
  - Example: `4.7.0 LIVE - BeltaKoda's ScCompLangPackRemix`
  - The user may want custom text (e.g., including PTU wave info, patch subtitle, etc.)

**Wait for user confirmation before proceeding.**

## Step 2: Determine Previous Version

Find the most recent existing version directory in the repo to use as the remix base:
```bash
ls -d */LIVE */PTU 2>/dev/null | sort -V | tail -5
```

Or use `scripts/config.py`:
```python
python -c "import sys; sys.path.insert(0,'scripts'); from config import get_latest_version; print(get_latest_version())"
```

Confirm with the user which previous version/channel to base the new remix on.

## Step 3: Extract Stock global.ini

Run the extraction script to pull the fresh `global.ini` from the local Star Citizen installation:
```bash
python scripts/extract_stock_ini.py --version [VERSION] --channel [CHANNEL]
```

This uses the built-in P4K reader to extract from `Data.p4k` directly. The SC install is auto-detected. Requires `zstandard` (`pip install zstandard`).

If extraction fails (scdatatools not installed, Data.p4k not found, etc.), ask the user to provide a stock INI file manually:
```bash
python scripts/extract_stock_ini.py --version [VERSION] --channel [CHANNEL] --local-file /path/to/stock.ini
```

Verify the output: `[VERSION]/[CHANNEL]/stock-global.ini` should exist and contain key=value pairs.

## Step 4: Run the Merge

Execute the core merge script to combine the previous remix with the new stock data:
```bash
python scripts/process-new-patch.py \
  --old-remix [OLD_VERSION]/[OLD_CHANNEL]/data/Localization/english/global.ini \
  --new-stock [VERSION]/[CHANNEL]/stock-global.ini \
  --output [VERSION]/[CHANNEL]/data/Localization/english/global.ini
```

This preserves all existing remixed names by INI key matching and adds new entries in stock format.

## Step 5: Apply Custom Title Bar Branding

Update `Frontend_PU_Version` with the confirmed branding string.

**Note**: The INI key has a `,P` suffix: `Frontend_PU_Version,P=`. Use the update script with a substring match on `--old-string` and the full replacement line on `--new-string`:
```bash
python scripts/update_version_string.py \
  --file [VERSION]/[CHANNEL]/data/Localization/english/global.ini \
  --old-string "Frontend_PU_Version,P=" \
  --new-string "Frontend_PU_Version,P=[CONFIRMED_BRANDING]"
```

Or grep for the line and edit it directly in the output INI.

## Step 6: Show Changes Summary

Compare the old and new stock INIs to identify what changed:
```bash
python scripts/compare_ini.py \
  [OLD_VERSION]/[OLD_CHANNEL]/stock-global.ini \
  [VERSION]/[CHANNEL]/stock-global.ini
```

Report to the user:
- How many new keys were added
- How many keys were removed
- How many values changed
- Specifically highlight new `item_Name` keys (new components needing remix)

## Step 7: Copy user.cfg

Copy the `user.cfg` from the previous version if it doesn't already exist:
```bash
cp [OLD_VERSION]/[OLD_CHANNEL]/user.cfg [VERSION]/[CHANNEL]/user.cfg
```

## Step 8: Identify Components Needing Remix

Search the new remix INI for component entries that still have stock (un-remixed) names.
A remixed entry has a prefix like `M2A`, `I1B`, `C3D`, `R2B`, `S1A`, `IR`, `EM`, `CS`, `B10`, `G-IR`, etc.
A stock entry is just the plain component name without any prefix.

Look for `item_Name` keys where the value does NOT match these patterns:
- `^[MICRS]\d[A-D]\s` — standard component prefix
- `^(IR|EM|CS)\s` — missile/torpedo tracking prefix
- `^B\d+\s` — bomb prefix
- `^G-(IR|EM|CS)\s` — ground missile prefix

List these for the user and explain the naming convention:

### Naming Convention Reference
- **Type**: M=Military, I=Industrial, C=Civilian, R=Racing(Competition), S=Stealth
- **Size**: 0-4
- **Grade**: A=Best, B=Good, C=Average, D=Basic
- **Ordnance**: IR=Infrared, EM=Electromagnetic, CS=CrossSection, B=Bomb

### Auto-Classifying New Components

The `item_Desc` fields in the stock INI contain structured metadata that can be parsed to determine Size, Grade, Class, and Manufacturer without needing external sources:
```
item_Desc_RADR_BLTR_S01_Hunter=Item Type: Radar\nManufacturer: Blue Triangle Inc.\nSize: 1\nGrade: B\nClass: Stealth\n\n...
```

Use these fields to auto-generate prefix suggestions for new components.

### Watch for New Component Categories

Not all component types have been remixed yet. If new `item_Name` keys appear for a category that has **never** been remixed (e.g., radars, missile racks, thrusters), flag them separately and ask the user whether to start remixing that category.

### Verification Sources (in order of preference)
1. **erkul.games** — most up-to-date component database
2. **finder.cstone.space** — reliable alternative
3. **starcitizen.tools** — community wiki (may lag behind)

## Step 9: Install to Local Game Directory

Deploy the remix to the local SC installation for in-game testing:
```bash
python scripts/install_to_ptu.py --version [VERSION] --channel [CHANNEL]
```

This copies the merged `global.ini` into the SC game directory so the user can launch and verify in-game.

## Step 10: Generate Manifest (Optional)

If the user wants a component manifest document:
```bash
python scripts/generate_manifest.py --version [VERSION] --channel [CHANNEL]
```

This creates `component_manifest_[VERSION]_[channel].md` with a table of all components and their remix status.

## Step 11: Create GitHub Deploy Workflow (LIVE releases only)

**Skip this step for PTU test builds.** Only needed when preparing a LIVE release.

Copy and adapt an existing deploy workflow for the new version:
```bash
cp .github/workflows/deploy-[OLD_VERSION]-[channel].yml .github/workflows/deploy-[VERSION]-[channel].yml
```

Then update the version references, tag name, and paths inside the new YAML file.

## Step 12: Commit and Push

If not already on a feature branch, create one:
```bash
git checkout -b feature/[VERSION]-[channel]
```

Commit all changes:
```bash
git add [VERSION]/ .github/workflows/deploy-[VERSION]-*.yml
git commit -m "feat([VERSION]-[channel]): add remix for patch [VERSION]"
```

For **PTU test builds**: commit but do NOT push — wait for the user to verify in-game first.

For **LIVE releases**: push immediately per repo rules:
```bash
git push origin feature/[VERSION]-[channel]
```

## Step 13: Create Release (LIVE releases only)

**Skip this step for PTU test builds.**

Ask the user if they want to trigger the release now. If yes:
```bash
gh workflow run create-release.yml -f version=[VERSION] -f environment=[CHANNEL]
```

Or guide them to trigger it manually from the GitHub Actions tab.

## Important Notes

- Always use `utf-8-sig` encoding when reading/writing SC INI files
- The 9MB `global.ini` is too large for text editors — always use the Python scripts
- Match components by INI **key** (e.g., `item_NameCOOL_AEGS_S01_Bracer`), not by name
- Stock `global.ini` has plain names (`Bracer`); remix adds prefixes (`M1C Bracer`)
- The `Frontend_PU_Version` string is what appears in the SC main menu title bar
