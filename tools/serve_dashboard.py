"""Moved. The server now lives at `backend/server.py`.

Kept as a redirect because `dashboard.cmd`, the README and four knowledge-base files all named
this path, and a stale shortcut that fails with ModuleNotFoundError teaches nothing.
"""
import subprocess
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "backend" / "server.py"
print(f"note: the server moved to backend/server.py — launching it for you\n", file=sys.stderr)
sys.exit(subprocess.call([sys.executable, str(TARGET), *sys.argv[1:]]))
