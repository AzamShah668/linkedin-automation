"""Every pipeline script must at least PARSE.

WHY (2026-08-15)
----------------
`tools/sweep-packets.ps1` contained `"...not a problem with $company: $limit"`. A colon straight
after a variable name makes PowerShell read it as a drive-qualified reference (`$env:PATH`), and
that is a **parse** error: the whole file dies before its first line runs.

So the scheduled task "Job Hunt - Sweep Packets" had exit code 1 on every run, for weeks, and it
looked exactly like a build that kept failing. Nothing was failing. The script never executed.

The irony is the point: that line was written to explain a *different* silent failure — the Claude
usage-limit wall (D25) — and it was itself a silent failure the whole time.

A parse check is the cheapest possible guard, and it catches the entire class: an unterminated
string, an unbalanced brace, a here-string whose closing `'@` is indented, a `$var:` typo. None of
those produce a useful error at runtime, because there is no runtime.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Everything the scheduled pipeline can invoke. A parse error in any of these is a step that
# silently does nothing.
SCRIPTS = sorted((REPO / "tools").glob("*.ps1"))

POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")

pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="PowerShell not available")


def _parse_errors(path: Path) -> str:
    """Empty string when the file parses. Uses the PowerShell parser itself, not a heuristic."""
    script = (
        "$e = $null; "
        f"[void][System.Management.Automation.Language.Parser]::ParseFile('{path}', "
        "[ref]$null, [ref]$e); "
        "if ($e) { $e | ForEach-Object { $_.Message } }"
    )
    proc = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=120,
    )
    return (proc.stdout or "").strip()


def test_there_are_scripts_to_check():
    """A glob that quietly matches nothing would make every test below pass for the wrong reason."""
    assert SCRIPTS, "no .ps1 files found under tools/ - the glob is wrong, not the repo"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_parses(script: Path):
    errors = _parse_errors(script)
    assert not errors, f"{script.name} does not parse, so it can never run:\n{errors}"
