# Agent Instructions: Star Citizen Language Pack Remix

**Objective**: Maintain and update the compact naming language pack for Star Citizen.

## The "Magic" Workflow (Each Patch)

When a new Star Citizen patch is released, the entire extraction, dry-run parsing, remixing, branding, comparison, and installation process is consolidated into a single unified script: `scripts/new_patch.py`.

### The Recommended Path (One-Command)

Run the consolidated script with the appropriate channel (e.g. `LIVE` or `PTU`). If it's a major new patch, always use `--force-convert` to perform a fresh DCB-to-XML extraction:

```bash
python scripts/new_patch.py --channel LIVE --old-channel PTU --force-convert --branding "4.8.0 LIVE - BeltaKoda's ScCompLangPackRemix" --install
```

#### Key Flags:
*   `--channel [CHANNEL]`: The target channel (`LIVE`, `PTU`, or `HOTFIX`).
*   `--old-channel [OLD_CHANNEL]`: The previous channel (e.g. comparing `LIVE` against the recent `PTU` stock file to see stock differences).
*   `--force-convert`: Deletes any old cache of extracted component XMLs and performs a fresh unforge/wine extraction. Crucial for major new patches!
*   `--branding "[STRING]"`: Custom `Frontend_PU_Version` main menu branding override.
*   `--install`: Automatically runs `scripts/install_to_ptu.py` to copy the compiled localization and configuration straight into your game installation directory.
*   `--stock-file [/path/to/stock.ini]`: Allows using a pre-downloaded stock INI instead of reading it from `Data.p4k` (optional).

---

### Alternative: Step-by-Step Manual Sub-workflow

If you need to run specific parts of the pipeline manually, the individual scripts are fully available:

#### 1. Ingest Stock Data
```bash
python scripts/extract_stock_ini.py --channel [CHANNEL]
```
This extracts `global.ini` from `Data.p4k` to `[CHANNEL]/stock-global.ini`.

#### 2. Generate Component Manifest
```bash
python scripts/dry_run_channel.py --channel [CHANNEL] --force-convert
```
This extracts `Game2.dcb` / `Game.dcb`, converts it to XML via `unforge.exe`, parses component metadata, and writes `dry_run_manifest_[channel].csv`.

#### 3. Apply the Remix
```bash
python scripts/apply_manifest.py --channel [CHANNEL] --manifest-csv dry_run_manifest_[channel].csv --branding "[BRANDING]"
```
Merges stock data with the parsed manifest and outputs `[CHANNEL]/data/Localization/english/global.ini`.

#### 4. Install Manually
```bash
python scripts/install_to_ptu.py --channel [CHANNEL]
```
Copies the generated files into the Star Citizen installation folder.

### 3.5 Naming Conventions

The remix uses the compact format: **[Type][Size][Grade] ComponentName**

#### Component Prefixes
| Prefix | Category | Sizes | Grades |
|--------|----------|-------|--------|
| M | Military | 1-4 | A(1) B(2) C(3) D(4) |
| I | Industrial | 1-2 | A(1) B(2) |
| C | Civilian | 1-2 | A(1) B(2) |
| R | Racing/Competition | 1-2 | A(1) B(2) |
| S | Stealth | 1-2 | A(1) B(2) |

#### Ordnance Prefixes
| Prefix | Meaning |
|--------|---------|
| IR | Infrared Tracking |
| EM | Electromagnetic Tracking |
| CS | Cross-Section Tracking |
| B[size] | Bomb (e.g., B10 for size 10) |
| G-[tracking] | Ground Missile |

#### Key Rules
- **Weapons (WeaponGun, Turret, TurretBase)** are excluded from remixing — they keep their stock names
- **Ordnance short keys** (MFD display names ending in `_short`) get the same prefix as their full names
- **Ground Missiles** are handled via regex on `item_NameGMISL_*` keys — tracking inferred from key names (`_IR_`, `_EM_`, `_CS_`), size from `_S<N>_` pattern
- **Mission items** (`mission_item_*`) get lowercased automatically by `apply_manifest.py`
- **Custom fixes** exist for known CIG naming mismatches (e.g., `BroadspecLite` uses INI key size S01 but XML says S02)
- If a key in the remix INI has no prefix, it wasn't in the manifest — check against the game to see if it needs manual treatment

#### Branding Format
The `Frontend_PU_Version` gets the stock version appended with ` - ScCompLangPackRemix`. Examples:
- LIVE: `4.7.0 - Welcome to the Rock - ScCompLangPackRemix`
- PTU: `4.8 - Tactical Strike - ScCompLangPackRemix`

**Always check the stock INI to find the exact version string format** — PTU may not include the patch number (it may just say `4.8 - Tactical Strike`). `apply_manifest.py` handles appending the suffix automatically.

### 4. Deploy, Vet, Branch, and Release
- Run `python scripts/install_to_ptu.py --channel [CHANNEL]` to copy the remixed global.ini into your game install at `[SC_BASE]/[CHANNEL]/data/Localization/english/` and copy `user.cfg` into the game channel root.
- **Vetting**: Launch the game and verify:
  1. Main menu version string shows `[PATCH] - [TITLE] - ScCompLangPackRemix` (confirm branding is applied)
  2. Scan a ship and verify component names show compact prefixes (e.g., `M2A QuadraCell MT`)
  3. Check MFD ordnance tags display correctly (e.g., `IR Marksman I Missile`)
  4. Spot-check ground missiles and bombs in inventory/MFD
- If anything looks wrong, compare the remix INI against the stock INI using `scripts/compare_ini.py` to identify what changed.

#### Feature Branch
- After in-game vetting succeeds, create a feature branch before committing:
  ```bash
  git checkout -b [channel]-[patch]-remix
  ```
- Commit only relevant files:
  - `[CHANNEL]/stock-global.ini`
  - `[CHANNEL]/data/Localization/english/global.ini`
  - `[CHANNEL]/user.cfg`
  - `dry_run_manifest_[channel].csv` if changed
  - workflow/tooling updates (`scripts/*`, `tools/unforge.exe`, `AGENT_INSTRUCTIONS.md`) if needed
- Do **not** commit temporary extraction folders (`extracted_*`), backup binaries, or ad-hoc ZIPs unless explicitly requested.
- Push the feature branch:
  ```bash
  git push -u origin [branch-name]
  ```

#### Release Type Rules
- **PTU and HOTFIX builds are GitHub pre-releases.** Always use `--prerelease` for PTU/HOTFIX.
- Tag/title format:
  - PTU: `4.8.0-PTU`
  - HOTFIX: `4.7.0-LIVE-HOTFIX`
  - LIVE: `4.7.1-LIVE`

#### Packaging and Release (Strictly Automated via GitHub Actions)

> [!WARNING]
> **Manual Release Creation and Local ZIP Packaging are STRICTLY FORBIDDEN.**
> Always use the automated `.github/workflows/create-release.yml` GitHub Actions workflow. Manual compilation runs the risk of introducing path structure mismatches and tagging/prerelease inconsistencies.

To publish a release:
1. Ensure your feature branch (e.g. `remix/4.8-live`) is fully committed and pushed to GitHub.
2. Trigger the GitHub Actions release workflow (`Create Release`) using one of the following methods:

**Method A: Via the GitHub CLI (Recommended)**
Run this terminal command:
```bash
gh workflow run create-release.yml --ref [branch-name] -f version=[version] -f environment=[ENVIRONMENT]
```
*Example for LIVE*:
```bash
gh workflow run create-release.yml --ref remix/4.8-live -f version=4.8.0 -f environment=LIVE
```
*Example for PTU*:
```bash
gh workflow run create-release.yml --ref remix/4.8-live -f version=4.8.0 -f environment=PTU
```

**Method B: Via the GitHub Web UI**
1. Navigate to the repository page on GitHub.
2. Click the **Actions** tab.
3. Select the **Create Release** workflow from the left sidebar.
4. Click **Run workflow**, choose your branch (e.g. `remix/4.8-live`), fill in the version (e.g. `4.8.0`) and environment (e.g., `LIVE`), and click **Run workflow**.

#### Verification
Once the GitHub Action runs, monitor its progress:
```bash
gh run list --workflow=create-release.yml
```
Verify the completed release and download asset:
```bash
gh release view [TAG] --json url,name,tagName,isPrerelease,assets
```

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
- `wine` for DCB-to-XML conversion (runs `tools/unforge.exe` via Wine). First Wine invocation on Linux may prompt for setup (~10-30s). Subsequent runs are faster.
- The P4K reader is pure Python (just `zstandard`), so no Wine needed for stock INI extraction.
- On Linux, SC install is auto-detected via LUG Helper Wine prefix at `~/Games/star-citizen/drive_c/Program Files/Roberts Space Industries/StarCitizen/`. Override in `config.ini` if needed.
- Avoid using complex text editing tools on the 9MB `global.ini`; always use specific Python processing scripts to avoid truncation or encoding errors.
- Always use `utf-8-sig` when reading/writing Star Citizen INI files.

## Task Tracking

Always use `todowrite` for multi-step workflows. When running in Claude Code CLI, use the native equivalent: `TaskCreate`, `TaskUpdate`, `TaskList`, and `TaskGet` (accessible via `/tasks` slash command).

**Rules:**
- Mark **exactly one** task as `in_progress` at any time
- Mark `completed` immediately after finishing (do not batch completions)
- Mark `in_progress` **before** starting a task, not after
- Add new follow-up tasks as discovered during execution
- Remove irrelevant tasks entirely (do not leave stale pending items)
- Tasks persist across context compactions and sessions (stored in `~/.claude/tasks/` for Claude Code)

**Status lifecycle:** `pending` → `in_progress` → `completed`

**When to use:**
- Complex multi-step pipelines (3+ steps) — always use for this workflow
- User explicitly requests todo list
- After receiving new instructions (capture requirements)
- When starting work (plan first, track as you go)

**When NOT to use:**
- Single straightforward task
- Trivial tasks providing no organizational benefit
- Tasks completable in <3 trivial steps
- Purely conversational/informational requests

## Extraction Pipeline

Full pipeline flow for each patch:

```
extract_stock_ini.py → dry_run_ptu.py → apply_manifest.py → remix INI
     ↓                      ↓                      ↓
  stock-global.ini    dry_run_manifest*.csv    [CHANNEL]/data/Localization/english/global.ini
```

### Step-by-step:

1. **`scripts/extract_stock_ini.py --channel [CHANNEL]`**
   - Reads `Data.p4k` via built-in `p4k_reader.py` (pure Python, just needs `zstandard`)
   - Extracts `global.ini` from the P4K archive
   - Saves to `[CHANNEL]/stock-global.ini`

2. **`scripts/dry_run_channel.py --channel [CHANNEL] --force-convert`**
   - **Extracts DCB**: Uses `p4k_reader.py` to pull `Game2.dcb` from `Data.p4k` → `extracted_[channel]/dcb/Data/`
   - **Converts DCB→XML**: Runs `tools/unforge.exe` via Wine → outputs to `extracted_[channel]/dcb/Data/libs/foundry/records/`
   - **Progress output**: Reports XML count every 30 seconds during long DCB conversion
   - **Parses XMLs**: Reads all component XMLs, extracts `key/size/grade/type/tracking/path`
   - **Generates manifest**: Writes `dry_run_manifest_[channel].csv`
   - **Caching safety**: Existing XMLs are counted before reuse. If count is below the safety threshold (default 10,000), the script fails and tells you to rerun with `--force-convert`.

3. **`scripts/apply_manifest.py --channel [CHANNEL] --manifest-csv dry_run_manifest_[channel].csv`**
   - Loads stock INI → merges with manifest CSV → produces remixed INI
   - Applies all naming prefixes from the Naming Conventions section above
   - Handles ground missiles, mission items, custom fixes, and branding
   - Output: `[CHANNEL]/data/Localization/english/global.ini`

### Important Notes:
- **Always regenerate the manifest** fresh from the current `Data.p4k`. CIG changes component metadata with each patch. Never reuse an old manifest CSV.
- **PTU INI delimiter quirk**: PTU stock files use comma delimiters (`Key,Value`) while LIVE uses equals (`Key=Value`). The parsing in `apply_manifest.py` handles both via `line.split('=', 1)` — but if you manually edit stock files, be aware of the difference.
- The `extracted_*` folders contain raw XMLs and can grow to 5GB+. Clean them up after the run (see Cleanup step).
- If `unforge.exe` fails, check that Wine is installed and configured. On Linux, `wine --version` should return a version string.


## 4.8+ DataForge/DCB v8 Lessons

- Use `tools/unforge.exe` **v4.0.83 or newer**. Older v4.0.81 builds fail on DCB/DataForge v8.
- Full 4.8 PTU DCB conversion via Wine took about **7 minutes** and produced **59,697 XML files**.
- A partial conversion is dangerous: if only some XMLs exist, old scripts may skip conversion and generate a tiny manifest.
- Symptom of partial extraction: manifest has ~27 rows instead of hundreds.
- Healthy 4.8 PTU manifest from full extraction: **963 parsed rows** (964 CSV lines with header).
- Always run new patch manifest generation with `--force-convert` unless you intentionally trust the existing extracted XML cache.
- `unp4k_rs` was tested diagnostically against 4.8 PTU: it detected DataForge v8 and 114,467 records, but crashed during XML export. Do not use it as the primary path yet.
- `dry_run_ptu.py` and `dry_run_live.py` are compatibility wrappers; prefer `dry_run_channel.py` for all channels.
- Branding must be stock version + ` - ScCompLangPackRemix` only. Do not include `PTU`, `LIVE`, or old `BeltaKoda` branding unless explicitly requested.
