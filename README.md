# ⚙️ Component Language Pack - Remix Edition

![GitHub release (latest by date)](https://img.shields.io/github/v/release/BeltaKoda/ScCompLangPackRemix)
![GitHub pre-release (latest by date)](https://img.shields.io/github/v/release/BeltaKoda/ScCompLangPackRemix?include_prereleases&label=pre-release&color=orange)
![GitHub all releases](https://img.shields.io/github/downloads/BeltaKoda/ScCompLangPackRemix/total)

> **📢 IMPORTANT:** This is a modified fork of the original [Component Language Pack by ExoAE](https://github.com/ExoAE/ScCompLangPack).
> **All credit for the original language pack goes to [ExoAE](https://github.com/ExoAE).**
> This remix was created using [Claude Code](https://claude.com/claude-code) to provide an alternative compact naming format.

> [!IMPORTANT]
> **Major Update (v4.5.0+):**
> I have completely changed how I gather data for this remix by extracting it **directly from the Star Citizen game files**. Since I no longer have to struggle parsing data from multiple sources, it's much harder to accidentally "cross the streams", so i've added missiles and torpedos in scope of this remix. I've left ship weapons out for now still, but let me know if you have ideas around them.

## 💡 Why Did I Make This?

> [!NOTE]
> **Quick-scan ship components without the guesswork!**
>
> When you scan a ship, you want to know **immediately** if it has components worth looting - without having to:
> - Enter the ship and visually identify the component type
> - Look up component names online
>
> This remix puts the critical stats **first**, so you can make instant decisions while scanning. See `M2A` at the start? You know it's Military, Size 2, A-grade. Decision made. Move on or loot up!

## 🎯 What's Different in This Remix?

This version uses a **compact naming format** that puts the important stats first:

**Original format:**
`XL-1` → `XL-1 S2 Military A`

**Remix format:**
`XL-1` → `M2A XL-1`

The format is: **[Type][Size][Quality] [Component Name]**

**Type abbreviations:**
- **M** = Military
- **I** = Industrial
- **C** = Civilian
- **R** = Racing (Competition renamed to avoid conflict with Civilian)
- **S** = Stealth

**More examples:**
- `QuadraCell MT` → `M2A QuadraCell MT` (Military, Size 2, Quality A)
- `Eco-Flow` → `I1B Eco-Flow` (Industrial, Size 1, Quality B)
- `Cryo-Star` → `C1B Cryo-Star` (Civilian, Size 1, Quality B)
- `AbsoluteZero` → `R2B AbsoluteZero` (Racing, Size 2, Quality B)
- `NightFall` → `S2A NightFall` (Stealth, Size 2, Quality A)

## 🚀 Expanded Scope: Ordnance (v4.5.0+)

Starting with patch 4.5.0, we have expanded the scope to include missiles, torpedoes, and bombs with highly informative functional tags.

### Functional Ordnance Tags:
- **IR** = Infrared Tracking
- **EM** = Electromagnetic Tracking
- **CS** = Cross-Section Tracking
- **B** = Bomb

### Examples:
- `Marksman I Missile` → **`IR Marksman I Missile`**
- `Seeker IX Torpedo` → **`EM Seeker IX Torpedo`**
- `Colossus Bomb` → **`B10 Colossus Bomb`**

> [!TIP]
> **MFD Ready!** These tags are also applied to the "short" names used on your ship's MFD screens (e.g., `CS StrkFrc II`), giving you critical combat info at a glance.

## 📡 Expanded Scope: Radars (v4.7.0+)

Starting with patch 4.7.0, radars are now included in the remix using the same **[Type][Size][Grade]** prefix format as coolers, power plants, shields, and quantum drives.

### Radar Manufacturers & Classes:
| Prefix | Manufacturer | Class |
|--------|-------------|-------|
| **M** | Groupe Nouveau Paradigme (GNP) | Military |
| **I** | Chimera Communications | Industrial |
| **C** | WillsOp | Civilian |
| **R** | Nav-E7 Gadgets | Competition |
| **S** | Blue Triangle Inc. | Stealth |

### Examples:
- `Epier` → **`M2C Epier`** (Military, Size 2, Grade C)
- `FullSpec` → **`I2A FullSpec`** (Industrial, Size 2, Grade A)
- `Backlund` → **`C1B Backlund`** (Civilian, Size 1, Grade B)
- `SNS-R6` → **`R1C SNS-R6`** (Competition, Size 1, Grade C)
- `Hunter` → **`S1B Hunter`** (Stealth, Size 1, Grade B)

> [!NOTE]
> As of 4.7.0 PTU, radars are not yet lootable or player-swappable in-game, but CIG has added full component data for them — suggesting they may become swappable soon.

## ⬇️ Download and install

**Download the latest version from the [Releases Page](https://github.com/joeydee1986/ScCompLangPackRemix/releases)**

**Want the original format instead?** Check out [ExoAE's original pack](https://github.com/ExoAE/ScCompLangPack)

🔧 How to Install:

1. Extract the ZIP file.
2. Copy the data folder and the user.cfg file into your game's LIVE folder root.
3. Launch the game.

**Note for manual downloads:** If you download files directly from the repository instead of using a release ZIP, **only copy the `data` folder and `user.cfg` file**. Do not include the `.claude` folder - it's only used for project maintenance and future updates.

## 🛠️ Create Your Own Language Pack

Want to create your own custom language pack? Use the **[SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor)** (Windows GUI) or the built-in extraction script (cross-platform) to extract the vanilla `global.ini` file from Star Citizen, then modify it to your preferences!

**Cross-platform extraction (Linux & Windows):**
```bash
python scripts/extract_stock_ini.py --channel LIVE
```

The script uses a built-in P4K reader (pure Python) to extract directly from `Data.p4k`. On Linux (via [LUG Helper](https://github.com/starcitizen-lug/lug-helper)), the SC installation is auto-detected in the Wine/Proton prefix. Only dependency: `pip install zstandard`.

## 🤖 Automation

This repository includes a suite of automation tools to streamline the update process for new Star Citizen patches.

**Key Features:**
*   **Automated Extraction:** Extracts component data directly from `Data.p4k` using custom P4K and DCB parsing tools.
*   **XML Data Mining:** Drills into individual item XMLs to verify tracking types (IR/EM/CS) and authentic manufacturer data.
*   **Intelligent Auditing:** Scans the game data to identify component types (Military, Civilian, etc.) even when not explicitly labeled.
*   **Auto-Fixing:** Automatically applies the naming convention to both the full and "short" (MFD) localization strings.

**How to Run:**
See [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md) for detailed usage instructions.

## 📦 Stock Global.ini Files

For reference and transparency, **stock (unmodified) `global.ini` files are included in this repository** for each channel. You can find them at:

```
/[CHANNEL]/stock-global.ini
```

**Examples:**
- `/LIVE/stock-global.ini`
- `/PTU/stock-global.ini`

Previous versions are preserved in the `archives/` folder and in git history.

These stock files were extracted using the **[SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor)** tool. The extractor is compiled via GitHub Actions and includes everything it needs without requiring additional installation.

## 🔄 Auto-Update URL

The remixed `global.ini` is always available at a stable URL that doesn't change between patches:

```
https://raw.githubusercontent.com/BeltaKoda/ScCompLangPackRemix/refs/heads/main/LIVE/data/Localization/english/global.ini
```

This enables tools and scripts to automatically fetch the latest version without needing to know the current patch number.

## 🚧 Found an Error or Issue?

If you notice any incorrectly formatted component names, missing conversions, or other issues, please let us know!

**How to report:**
- Open an issue on [GitHub Issues](https://github.com/joeydee1986/ScCompLangPackRemix/issues)
- Include the component name and what's wrong
- Screenshots are super helpful!

We appreciate your help in making this pack better for everyone. Feel free to submit pull requests with fixes too!

## Notes

- This project is not affiliated with Cloud Imperium Games.
- Using language packs is currently intended by Cloud Imperium Games. 
https://robertsspaceindustries.com/spectrum/community/SC/forum/1/thread/star-citizen-community-localization-update

## ☕ Support the Original Creator

If you'd like to support the original creator ExoAE, you can use their Star Citizen referral code when buying the game:

**STAR-4JD7-RZT4**

Thank you to ExoAE for creating the original pack!
