# ⚙️ Component Language Pack - Remix Edition

> **📢 IMPORTANT:** This is a modified fork of the original [Component Language Pack by ExoAE](https://github.com/ExoAE/ScCompLangPack).
> **All credit for the original language pack goes to [ExoAE](https://github.com/ExoAE).**
> This remix was created using [Claude Code](https://claude.com/claude-code) to provide an alternative compact naming format.

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

## ⬇️ Download and install

**Download the latest version from the [Releases Page](https://github.com/joeydee1986/ScCompLangPackRemix/releases)**

**Want the original format instead?** Check out [ExoAE's original pack](https://github.com/ExoAE/ScCompLangPack)

🔧 How to Install:

1. Extract the ZIP file.
2. Copy the data folder and the user.cfg file into your game's LIVE folder root.
3. Launch the game.

**Note for manual downloads:** If you download files directly from the repository instead of using a release ZIP, **only copy the `data` folder and `user.cfg` file**. Do not include the `.claude` folder - it's only used for project maintenance and future updates.

## 🛠️ Create Your Own Language Pack

Want to create your own custom language pack? Use the **[SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor)** to extract the vanilla `global.ini` file from Star Citizen, then modify it to your preferences!

This tool was created to make building this language pack easier, and it's now available for the community to create their own custom packs.

**Note:** The extraction tool is currently in beta. If you encounter any issues with it, please report them in the [tool's issue tracker](https://github.com/BeltaKoda/SC-GlobalIni-Extractor/issues).

## 🤖 Automation

This repository includes a suite of automation tools to streamline the update process for new Star Citizen patches.

**Key Features:**
*   **Automated Extraction:** Extracts component data directly from `Data.p4k`.
*   **Intelligent Auditing:** Scans the game data to identify component types (Military, Civilian, etc.) even when not explicitly labeled.
*   **Auto-Fixing:** Automatically applies the naming convention (e.g., `M2A`) to the `global.ini`.

**How to Run:**
See [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md) for detailed usage instructions.

## 📦 Stock Global.ini Files

For reference and transparency, **stock (unmodified) `global.ini` files are included in this repository** for each patch version. You can find them at:

```
/[VERSION]/[ENVIRONMENT]/stock-global.ini
```

**Examples:**
- `/4.3.2/LIVE/stock-global.ini` (if available)
- `/4.4.0/PTU/stock-global.ini`

These stock files were extracted using the **[SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor)** tool. The extractor is compiled via GitHub Actions and includes everything it needs without requiring additional installation.

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
