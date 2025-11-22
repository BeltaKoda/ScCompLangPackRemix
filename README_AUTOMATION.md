# Automated Language Pack Patcher

This guide explains how to use the automated tooling to update the Star Citizen Language Pack Remix for new game patches.

## Prerequisites

1. **Python 3.9+**: Ensure Python is installed and added to your PATH.
2. **Star Citizen Installed**: The script looks for the game in `C:\Program Files\Roberts Space Industries\StarCitizen\LIVE`.
3. **Dependencies**: Install required packages (if any).
   ```bash
   pip install -r requirements.txt
   ```

## Workflow for New Patches

When a new Star Citizen patch drops (e.g., 4.5.0), follow these steps:

### 1. Prepare the Repository
1. Create a new folder structure for the patch if needed (e.g., `4.5.0/PTU/data/Localization/english`).
2. Place the **stock** `global.ini` from the new patch into this folder (you can extract it manually or let the script try to find it if you update the paths in `audit_sc_native.py`).
   * *Note: Currently, the script defaults to `4.4.0/PTU`. You may need to update the path in `audit_sc_native.py` and `apply_fixes.py` for a new version.*

### 2. Run the Automation Script
Open a terminal in the repository root and run:

```bash
# Default (4.4.0 PTU)
python automate_patch.py

# For a new patch (e.g., 4.5.0 LIVE)
python automate_patch.py --version 4.5.0 --channel LIVE
```

This will automatically:
1. **Extract Data**: Use `unp4k` and `unforge` to extract the latest component data from `Data.p4k`.
2. **Audit**: Scan the current `global.ini` against the extracted game data.
3. **Fix**: Apply naming conventions (e.g., `C1A PowerBolt`) to the `global.ini`.
4. **Verify**: Run a final audit to ensure zero mismatches.

### 3. Deploy (Optional)
To automatically copy the fixed file to your game directory, run:

```bash
python automate_patch.py --version 4.5.0 --channel LIVE --deploy
```

## Troubleshooting

*   **Extraction Failed**: Ensure `unp4k.exe` and `unforge.exe` are in the `tools/` directory.
*   **Missing Components**: If the audit reports 0 components, check if the `Data.p4k` path is correct in `audit_sc_native.py`.
*   **Path Issues**: The script now accepts `--version` and `--channel` arguments to dynamically construct paths. Ensure your folder structure matches (e.g., `4.5.0/LIVE/data/...`).

## Script Overview

*   `automate_patch.py`: Master orchestrator script.
*   `audit_sc_native.py`: Handles P4K extraction, XML parsing, and auditing.
*   `apply_fixes.py`: Applies the naming fixes to `global.ini` based on audit data.
