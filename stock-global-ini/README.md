# Stock Global.ini Files

This folder contains vanilla `global.ini` files extracted from Star Citizen using the [SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor).

## How to Add a New Vanilla File

When a new Star Citizen patch is released:

1. **Extract the vanilla global.ini** using [SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor)
2. **Save the file here** with the format: `StockGlobal-{VERSION}-{BRANCH}.ini`
   - Example: `StockGlobal-4-4-0-PTU.ini`
3. **Commit the file** to git
4. **Create a release tag** (e.g., `v6`)
5. **Push the tag** - GitHub Actions will automatically build the language pack

## Naming Convention

Follow the naming format output by the SC Global.ini Extractor:

```
StockGlobal-{VERSION}-{BRANCH}.ini
```

**Examples:**
- `StockGlobal-4-4-0-PTU.ini`
- `StockGlobal-4-3-2-LIVE.ini`
- `StockGlobal-4-4-1-EPTU.ini`

## How the Build Works

The GitHub Actions workflow:
1. Finds the **latest** vanilla file (by filename sorting)
2. Runs the transformation script to create compact component names
3. Packages the result with `user.cfg` into a release ZIP

## Why Keep Multiple Versions?

- Track changes across Star Citizen patches
- Rebuild old versions if needed
- Transparency - users can see exactly what vanilla file was used
