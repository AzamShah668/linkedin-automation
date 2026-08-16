"""Load `.env` into the process, once, for both stacks.

WHY THIS EXISTS
---------------
`llm.py` reads its configuration with `os.getenv`, and **nothing in this project ever loaded
`.env`**. `python-dotenv` is not installed either. It has only ever worked in a shell where the
variables happened to be exported by hand.

That means `freetext.py` — the one place an LLM already writes to a **real employer's form** — was
**dead in every unattended run**, raising `LLM_BASE_URL is not set` under Task Scheduler. Nothing
errored visibly, because the code path is only reached when a form asks a motivation question.
Found 2026-08-16 while checking whether the free models could carry the OmniRoute stack: the very
first `llm.ask()` from a clean `py -3 -m` invocation failed.

This is the **only shared file the OmniRoute work touches**. It cannot change how the Claude stack
behaves: it only ever *adds* variables that were missing.

THE RULE: A REAL ENVIRONMENT VARIABLE ALWAYS WINS
--------------------------------------------------
`setdefault`, never assignment. If a caller exported `LLM_MODEL` to try a different model for one
run, a file on disk must not silently overrule them — that is the same class of surprise as a
config that ignores its own flags.

Values are read literally. `KEY=value`, `#` comments and blank lines only; surrounding single or
double quotes are stripped. No interpolation, no `export` prefix handling, no multi-line values —
if `.env` ever needs those, use a real parser rather than growing this one quietly.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENV_PATH = REPO / ".env"

_loaded = False


def parse(text: str) -> dict[str, str]:
    """`.env` text -> mapping. Pure, so the parsing rules are testable without a file."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        # Strip ONE matching pair of surrounding quotes; an apostrophe inside a value survives.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def values(path: Path | None = None) -> dict[str, str]:
    """What `.env` contains, without touching the process environment."""
    path = path if path is not None else ENV_PATH
    if not path.exists():
        return {}
    try:
        return parse(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}


def load(path: Path | None = None, force: bool = False) -> int:
    """Put missing `.env` values into `os.environ`. Returns how many were added.

    Idempotent: repeated imports do no extra work. `force` re-reads, for tests.
    """
    global _loaded
    if _loaded and not force:
        return 0
    added = 0
    for key, value in values(path).items():
        if key not in os.environ:          # setdefault semantics: a real env var always wins
            os.environ[key] = value
            added += 1
    _loaded = True
    return added


def get(name: str, default: str = "") -> str:
    load()
    return os.environ.get(name, default)


def require(name: str) -> str:
    """Fail with a message that says what to do, not just what is missing."""
    load()
    value = os.environ.get(name)
    if not value:
        raise KeyError(
            f"{name} is not set. Add it to {ENV_PATH} (never hardcode it, never commit it)."
        )
    return value


# Import for effect. Every entry point that reads configuration imports this module, so a scheduled
# task gets the same environment an interactive shell does.
load()
