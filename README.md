# ⚙️ Component Language Pack - Remix Edition

> **📢 IMPORTANT:** This language pack is built automatically from vanilla Star Citizen files using a compact naming transformation.
> **Credit:** Original concept inspired by [ExoAE's Component Language Pack](https://github.com/ExoAE/ScCompLangPack).
> This remix uses automated GitHub Actions to transform vanilla `global.ini` files into the compact format.

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

This makes it easier to quickly scan and sort components by their stats at a glance, which is my primary reason for this fork. I like to play 'self found', and I didn't want to waste time looting a ship that doesn't have components I want. This way, I can simply scan and move on.

## ⬇️ Download and install

**Download the latest version from the [Releases Page](https://github.com/joeydee1986/ScCompLangPackRemix/releases)**

**Want the original format instead?** Check out [ExoAE's original pack](https://github.com/ExoAE/ScCompLangPack)

🔧 How to Install:

1. Extract the ZIP file.
2. Copy the data folder and the user.cfg file into your game's LIVE folder root.
3. Launch the game.

**Note for manual downloads:** If you download files directly from the repository instead of using a release ZIP, **only copy the `data` folder and `user.cfg` file**. Do not include the `.claude` folder - it's only used for project maintenance and future updates.

## 🤖 How Releases Are Built

This language pack is built **automatically by GitHub Actions** from vanilla Star Citizen files:

1. Vanilla `global.ini` files are extracted using [SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor) and stored in `stock-global-ini/`
2. When a new version tag is pushed (e.g., `v6`), GitHub Actions automatically:
   - Finds the latest vanilla file
   - Runs `build-language-pack.py` to transform component names to compact format
   - Packages the result into a release ZIP
   - Creates a GitHub Release

**All builds are transparent and auditable** - you can view the [workflow runs](https://github.com/BeltaKoda/ScCompLangPackRemix/actions) to see exactly how each release was created.

## 🛠️ Create Your Own Language Pack

Want to create your own custom language pack? Use the **[SC Global.ini Extractor](https://github.com/BeltaKoda/SC-GlobalIni-Extractor)** to extract the vanilla `global.ini` file from Star Citizen, then modify it to your preferences!

This tool was created to make building this language pack easier, and it's now available for the community to create their own custom packs.

**Note:** The extraction tool is currently in beta. If you encounter any issues with it, please report them in the [tool's issue tracker](https://github.com/BeltaKoda/SC-GlobalIni-Extractor/issues).

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
