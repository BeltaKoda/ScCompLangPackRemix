#!/usr/bin/env python3
"""Compatibility wrapper for generating the LIVE manifest."""
import subprocess
import sys
from pathlib import Path

script = Path(__file__).resolve().parent / "dry_run_channel.py"
raise SystemExit(subprocess.call([sys.executable, str(script), "--channel", "LIVE", *sys.argv[1:]]))
