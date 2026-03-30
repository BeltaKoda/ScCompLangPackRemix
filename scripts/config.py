"""
Centralized configuration for ScCompLangPackRemix.
Auto-detects repo root, platform, and Star Citizen installation path.
All scripts should import from this module instead of hardcoding paths.
"""

import os
import platform
import configparser
from pathlib import Path

# Auto-detect repo root from this file's location (scripts/ -> repo root)
REPO_ROOT = Path(__file__).resolve().parent.parent

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Load optional config.ini overrides
_config_file = REPO_ROOT / "config.ini"
_config = configparser.ConfigParser()
if _config_file.exists():
    _config.read(_config_file)

# Default SC install base paths per platform
_DEFAULT_SC_BASES_WINDOWS = [
    Path(r"C:\Program Files\Roberts Space Industries\StarCitizen"),
    Path(r"D:\Program Files\Roberts Space Industries\StarCitizen"),
    Path(r"E:\Program Files\Roberts Space Industries\StarCitizen"),
]

_DEFAULT_SC_BASES_LINUX = [
    Path.home() / "Games" / "star-citizen" / "drive_c" / "Program Files" / "Roberts Space Industries" / "StarCitizen",
]


def get_repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


def _find_sc_base() -> Path | None:
    """Find the Star Citizen base installation directory (contains LIVE/, PTU/, etc.)."""
    # Check config.ini override first
    override = _config.get("paths", "sc_base", fallback=None)
    if override:
        p = Path(override)
        if p.exists():
            return p

    bases = _DEFAULT_SC_BASES_WINDOWS if IS_WINDOWS else _DEFAULT_SC_BASES_LINUX
    for base in bases:
        if base.exists():
            return base

    return None


def get_sc_install_path(channel: str = "LIVE") -> Path | None:
    """Find SC installation for a given channel (LIVE, PTU, etc.). Returns None if not found."""
    base = _find_sc_base()
    if base is None:
        return None

    candidate = base / channel
    if candidate.exists():
        return candidate

    return None


def get_data_p4k(channel: str = "LIVE") -> Path | None:
    """Return path to Data.p4k for a given channel, or None if not found."""
    sc_path = get_sc_install_path(channel)
    if sc_path is None:
        return None

    p4k = sc_path / "Data.p4k"
    return p4k if p4k.exists() else None


def get_channel_dir(channel: str) -> Path:
    """Return the channel directory path (e.g., LIVE/, PTU/, HOTFIX/)."""
    return REPO_ROOT / channel


def get_stock_ini(channel: str) -> Path:
    """Return the expected stock-global.ini path for a channel."""
    return get_channel_dir(channel) / "stock-global.ini"


def get_remix_ini(channel: str) -> Path:
    """Return the remixed global.ini path for a channel."""
    return get_channel_dir(channel) / "data" / "Localization" / "english" / "global.ini"


if __name__ == "__main__":
    # Quick diagnostic when run directly
    print(f"REPO_ROOT:    {REPO_ROOT}")
    print(f"IS_WINDOWS:   {IS_WINDOWS}")
    print(f"IS_LINUX:     {IS_LINUX}")
    print(f"SC Base:      {_find_sc_base()}")
    print(f"SC LIVE:      {get_sc_install_path('LIVE')}")
    print(f"SC PTU:       {get_sc_install_path('PTU')}")
    print(f"Data.p4k:     {get_data_p4k('LIVE')}")
