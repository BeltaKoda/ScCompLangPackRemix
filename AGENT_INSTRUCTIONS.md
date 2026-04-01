# Agent Instructions: Star Citizen Language Pack Remix

**Objective**: Maintain and update the compact naming language pack for Star Citizen.

## The "Magic" Workflow (Each Patch)

When a new Star Citizen patch is released, follow these steps:

### 1. Ingest Stock Data

**Automated (recommended):**
```bash
python scripts/extract_stock_ini.py --channel [CHANNEL]
```
This extracts `global.ini` directly from the local `Data.p4k` file using the built-in P4K reader. Works on both Linux and Windows.

**Manual alternative:**
```bash
python scripts/extract_stock_ini.py --channel [CHANNEL] --local-file /path/to/stock-global.ini
```

The stock file is saved to `[CHANNEL]/stock-global.ini`.

### 2. Identify Changes
- Use `scripts/compare_ini.py` to compare the new stock INI with the previous version's stock INI:
  ```bash
  python scripts/compare_ini.py [OLD_STOCK_PATH] [NEW_STOCK_PATH]
  ```
- **Check for**:
    - New ship components/weapons (Look for `item_Name...` keys that aren't in your mapping).
    - Changes to the main menu version string (`Frontend_PU_Version`).

### 3. Apply the Remix
- **Do NOT** crawl Game.dcb unless absolutely necessary for a major mapping update.
- Use the consolidated workflow script:
  ```bash
  python scripts/new_patch.py --channel [CHANNEL]
  ```
- Or use `process-new-patch.py` directly:
    - **Update Version**: Set `Frontend_PU_Version` to the new patch title + `- ScCompLangPackRemix`.
    - **Apply Prefix**: For all ship component keys, prepend `[Type][Size][Quality]`.
- Ensure all other keys (MFDs, New missions, etc.) remain untouched from the original stock file.

### 4. Deploy & Release
- Install locally for testing:
  ```bash
  python scripts/install_to_ptu.py --channel [CHANNEL]
  ```
- Commit to a feature branch, merge to `main`.
- Push to GitHub and create a Release/Pre-release via `create-release.yml` workflow.

### 5. Cleanup (Crucial)
- **Nuke Temporary Data**: The `extracted_*` folders can reach 5GB+.
- **Command**: `rm -rf extracted_*`
- **Why?**: The manifest CSV/MD files are the permanent record; the raw XMLs are just for the run.

## Configuration

All scripts use `scripts/config.py` for centralized path detection:
- **SC install path** is auto-detected on both Linux (LUG Helper prefix) and Windows.
- Override in `config.ini` if non-standard location (copy from `config.ini.example`).

## Requirements
- Python 3.10+
- `zstandard` for P4K extraction: `pip install zstandard`
- `pycryptodome` only if extracting encrypted P4K entries (rare): `pip install pycryptodome`
- `wine` for DCB-to-XML conversion (runs `tools/unforge.exe` via Wine)
- Avoid using complex text editing tools on the 9MB `global.ini`; always use specific Python processing scripts to avoid truncation or encoding errors.
- Always use `utf-8-sig` when reading/writing Star Citizen INI files.

## Extraction Pipeline
The component data extraction uses a two-stage pipeline:
1. **P4K → DCB**: Built-in `scripts/p4k_reader.py` extracts Game2.dcb from Data.p4k (no external dependencies beyond zstandard)
2. **DCB → XML**: `tools/unforge.exe` via Wine converts the DataForge binary to component XMLs
3. **XML → Manifest CSV**: `scripts/dry_run_live.py` or `scripts/dry_run_ptu.py` parses the XMLs and generates the manifest

**Important**: Always extract fresh from the current game's Data.p4k before building a remix. CIG changes component types and metadata with each patch. Never rely on stale extracted data or static CSV files.
