"""Every CLI module must survive a Windows console.

2026-08-17: `intake.py` had no UTF-8 guard. A job title containing an en-dash raised
UnicodeEncodeError while PRINTING THE PLAN, which is before the insert runs - so discovery found
36 rows and none of them reached the board. The traceback scrolled past inside a runner that had
the step marked "informational", and the only visible symptom was a quiet `exit 1`.

Windows consoles default to cp1252. Job titles, company names and recruiter names are full of
en-dashes, arrows, accents and emoji. Any module that prints scraped text needs the guard, and
"remembered to add it" is not a mechanism.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Modules with a __main__ block print scraped text to a console. Pure library modules do not.
CLI_MODULES = sorted(
    p for p in list((REPO / "apps" / "autopilot").glob("*.py"))
    + list((REPO / "apps" / "autopilot" / "free").glob("*.py"))
    if '__main__' in p.read_text(encoding="utf-8", errors="replace")
)

GUARD = re.compile(r"reconfigure\(encoding=[\"']utf-8[\"']", re.I)


def test_there_are_cli_modules_to_check():
    """A glob that matches nothing would make the test below pass for the wrong reason."""
    assert CLI_MODULES, "no CLI modules found - the glob is wrong, not the repo"


@pytest.mark.parametrize("path", CLI_MODULES, ids=lambda p: p.name)
def test_a_cli_module_reconfigures_stdout(path: Path):
    source = path.read_text(encoding="utf-8", errors="replace")
    assert GUARD.search(source), (
        f"{path.name} prints to a console without forcing UTF-8. On cp1252 an en-dash in a job "
        f"title raises UnicodeEncodeError mid-run, which is how intake.py silently loaded zero of "
        f"36 discovered rows."
    )
