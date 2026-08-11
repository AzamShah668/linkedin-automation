"""Compatibility shim — the real module now lives in `database/board_db.py`.

WHY THIS FILE STILL EXISTS
--------------------------
Sixteen callers import `board_db` by adding `tools/` to `sys.path` — including three PowerShell
scripts that run from Task Scheduler (`auto-apply.ps1`, `build-packet.ps1`, `sweep-packets.ps1`)
and seven post_creator scripts. Moving the module without this shim would have broken all of them
silently, at 3am, in a log nobody reads.

⚠️ It must load the real module **by file path**, not by name. Both files are called `board_db`, so
a plain `from board_db import *` here re-imports *this* file and fails with a confusing circular
import. `importlib` with an explicit location is the only thing that disambiguates them.

Delete this file only after `grep -rn "board_db" --include=*.py --include=*.ps1` comes back clean.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REAL = Path(__file__).resolve().parent.parent / "database" / "board_db.py"

_spec = importlib.util.spec_from_file_location("_board_db_real", _REAL)
_real = importlib.util.module_from_spec(_spec)
sys.modules["_board_db_real"] = _real
_spec.loader.exec_module(_real)

# Re-export everything public. `import *` semantics without the name clash.
for _name in dir(_real):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_real, _name)

__all__ = [n for n in dir(_real) if not n.startswith("_")]
