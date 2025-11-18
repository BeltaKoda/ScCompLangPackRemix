# ScCompLangPackRemix - Claude Code Project Guidelines

## Repository Structure

This repository uses a patch version-based structure:
```
/[VERSION]/[ENVIRONMENT]/
  ├── data/
  │   └── Localization/
  │       └── english/
  │           └── global.ini (remixed)
  ├── user.cfg
  └── stock-global.ini (original from CIG)
```

**Examples:**
- `/4.3.2/LIVE/` - Current live version (patch 4.3.2)
- `/4.4.0/PTU/` - PTU test version (patch 4.4.0)

## Patch Update Workflow

When a new Star Citizen patch is deployed, a new `global.ini` file is released by CIG containing all in-game items from that patch (new items, updated items, balance changes, etc.).

**Process for updating to a new patch:**

1. **Obtain new stock global.ini**: Extract the stock `global.ini` from the new patch's Data.p4k file
2. **Save stock ini to repo**: Copy to `/[VERSION]/[ENVIRONMENT]/stock-global.ini` for reference
3. **Run processing script**: Use `process-new-patch.py` to:
   - Preserve all existing remixed component names from the current version
   - Add new components in stock format (to be remixed manually or in future updates)
   - Remove components that no longer exist in the game
4. **Create version directory**: Place the processed files in `/[VERSION]/[ENVIRONMENT]/`
5. **Manual remixing**: Review new components and apply remix format where metadata is available

**Important Notes:**
- When comparing components, match by ini KEY (e.g., `item_NameCOOL_AEGS_S01_Bracer`), not by component name
- The stock global.ini has simple component names (e.g., "Bracer"), while the remix adds type/size/quality prefix (e.g., "M1C Bracer")
- New components that don't have remixed versions yet will remain in stock format until manually updated
- Use Git tags to mark versions: version tags (4.3.2, 4.4.0) and environment tags (LIVE, PTU, HOTFIX)

## Git Workflow

### Commit and Push Policy

**IMPORTANT:** All commits must be pushed to GitHub immediately after committing.

**Standard workflow for feature branches:**
1. Make changes
2. Create commit with `git commit`
3. **Immediately push to GitHub** with `git push origin [branch-name]`

**Exception - Main branch:**
- **ALWAYS** ask for user confirmation before committing to `main`
- **ALWAYS** ask for user confirmation before pushing to `main`
- This prevents accidental changes to the production branch

**Example:**
```bash
# Feature branch - automatic push
git commit -m "Add new feature"
git push origin feature/my-feature  # ✅ Push immediately

# Main branch - requires confirmation
# ❌ Do NOT commit or push to main without explicit user approval
```

## Release Process

### ZIP File Naming Convention
When creating new releases, **always** use this exact naming format:
```
ScCompLangPackRemix-v[VERSION].zip
```

**Examples:**
- `ScCompLangPackRemix-v4.zip`
- `ScCompLangPackRemix-v5.zip`
- `ScCompLangPackRemix-v10.zip`

### Release ZIP Contents
The release ZIP file should contain **ONLY**:
- `data/` folder (with all localization files)
- `user.cfg` file

### What NOT to Include in Release ZIP
**DO NOT** include the following in release ZIP files:
- `.claude/` directory or `claude.md` file
- `.git/` directory
- `.gitignore` file
- `README.md`
- Any existing ZIP files
- Any development/project files

### Creating Release ZIP

**Note:** Release creation should be handled by GitHub Actions, not manually by Claude Code.

For manual testing, use this command from within the version directory:
```bash
cd [VERSION]/[ENVIRONMENT]
powershell.exe -Command "Compress-Archive -Path data,user.cfg -DestinationPath ../../ScCompLangPackRemix-[VERSION]-[ENVIRONMENT].zip -Force"
```

**Example:**
```bash
cd 4.4.0/PTU
powershell.exe -Command "Compress-Archive -Path data,user.cfg -DestinationPath ../../ScCompLangPackRemix-4.4.0-PTU.zip -Force"
```

## Component Naming Convention

This project uses a compact naming format for Star Citizen ship components:

**Format:** `[Type][Size][Quality] ComponentName`

### Type Abbreviations
- **M** = Military
- **I** = Industrial
- **C** = Civilian
- **R** = Racing (NOTE: The in-game type is "Competition", but we use "R" for Racing to avoid conflict with Civilian's "C")
- **S** = Stealth

### Size
- **0-4** = Component size

### Quality Grades
- **A** = Best
- **B** = Good
- **C** = Average
- **D** = Basic

### Example Transformations
- `QuadraCell MT S2 Military A` → `M2A QuadraCell MT`
- `Eco-Flow S1 Industrial B` → `I1B Eco-Flow`
- `Cryo-Star S1 Civilian B` → `C1B Cryo-Star`
- `AbsoluteZero S2 Competition B` → `R2B AbsoluteZero`
- `NightFall S2 Stealth A` → `S2A NightFall`

## Component Verification

When verifying components, use these authoritative sources in order of preference:
1. **erkul.games** (most up-to-date, but requires JavaScript)
2. **finder.cstone.space** (reliable alternative)
3. **starcitizen.tools** (wiki, may have outdated data)

Always verify: Size, Grade, Type, and Component Name spelling.

## File Locations

- Component definitions: `data/Localization/english/global.ini`
- Game configuration: `user.cfg`
