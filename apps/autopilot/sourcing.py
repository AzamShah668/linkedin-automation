"""Screen a board row before it consumes an application slot.

WHY THIS EXISTS
---------------
Two of the eight Easy Apply submissions on 2026-08-09/10 went to **Crossing Hurdles**, a company with
**zero employees findable on LinkedIn**. Both produced an auto-acknowledgement from
`notifications@ceipalmail.com` within three seconds, first person, funnelling to `jobs.micro1.ai`
with a referral code.

There is no hiring manager behind a req like that. It is a lead magnet. So those two applications
could never be followed up (D32 needs a *named human*), and the slots were spent before anyone
noticed.

THE FAILURE ASYMMETRY — NOTE THAT IT IS THE OPPOSITE OF replies.py
------------------------------------------------------------------
`replies.py` escalates anything it cannot classify, because a false alarm costs ten seconds and a
false silence cost fifteen days.

**This module leans the other way.** Here:

  * a false positive (blocking a real company) costs a **job opportunity**, which is unrecoverable
  * a false negative (letting a shell through) costs **one application slot**, roughly fifteen seconds

A missed opportunity is strictly worse than a wasted slot. So:

  **Heuristics may only DEPRIORITIZE. Only recorded evidence may BLOCK.**

A pattern in a job title is a suspicion. "We searched LinkedIn and this company has no employees" is
evidence. The two must never be given the same power, and the tempting shortcut — blocking on the
`$60/hr` tell alone — would have skipped legitimate contract roles.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from apps.autopilot.answers import REPO

UNREACHABLE_PATH = Path(os.environ["AUTOPILOT_UNREACHABLE"]) if os.environ.get(
    "AUTOPILOT_UNREACHABLE"
) else (REPO / "output" / "apply-log" / "unreachable.json")

APPLY = "apply"
DEPRIORITIZE = "deprioritize"
BLOCK = "block"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


# ---------------------------------------------------------------------------------------------
# Suspicions. These DEPRIORITIZE only. Each one is a real observation from this board, not a guess.
# ---------------------------------------------------------------------------------------------
AGENCY_TELLS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # A pay rate in the TITLE is a staffing-marketplace convention. Employers put the rate in the
    # body; agencies put it in the title because the rate is the advertisement.
    ("pay rate advertised in the job title", re.compile(r"\$\s?\d+\s*/\s*hr|\bper hour\b|\d+\s*/hr", re.I)),
    # "Fully Remote" in the title, in caps-y marketing form, alongside superlatives.
    ("marketing superlative in the job title", re.compile(r"top\s+us\b|\burgent(ly)?\s+hiring\b|\bimmediate\s+joiner", re.I)),
)


@dataclass(frozen=True)
class Verdict:
    action: str
    reason: str

    @property
    def blocks(self) -> bool:
        return self.action == BLOCK


def load_unreachable(path: Path = UNREACHABLE_PATH) -> dict[str, dict]:
    """Companies PROVEN to have nobody to follow up with. Keyed by normalised company name."""
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # Loud. An unreadable evidence file must not silently become "nothing is blocked" — but it
        # also must not block everything, so we return empty AND say so.
        print(f"  !! unreachable list at {path} is unreadable ({exc}); NOTHING is being blocked")
        return {}
    return {_norm(k): v for k, v in raw.get("companies", {}).items()}


def record_unreachable(
    company: str, evidence: str, path: Path = UNREACHABLE_PATH, today: date | None = None
) -> None:
    """Mark a company as having no findable human. Requires evidence, in words, on purpose."""
    if not (evidence or "").strip():
        raise ValueError("recording a company as unreachable requires evidence, not a bare assertion")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"companies": {}}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    data.setdefault("companies", {})[company] = {
        "evidence": evidence.strip(),
        "recorded": (today or date.today()).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def screen(company: str, role: str, path: Path = UNREACHABLE_PATH) -> Verdict:
    """Decide whether this row deserves an application slot.

    Pure enough to test: the only I/O is the evidence file, which is injectable.
    """
    proven = load_unreachable(path).get(_norm(company))
    if proven:
        # Plain hyphen, not an em-dash: this string reaches a Windows console whose codepage
        # renders an em-dash as a replacement character, which makes the reason look corrupted.
        return Verdict(BLOCK, f"no findable human at this company - {proven.get('evidence', 'recorded')}")

    for label, pattern in AGENCY_TELLS:
        if pattern.search(role or ""):
            # Suspicion only. It still gets applied to, just last.
            return Verdict(DEPRIORITIZE, f"{label}; applying last, verify a human exists before follow-up")

    return Verdict(APPLY, "")


__all__ = [
    "APPLY", "BLOCK", "DEPRIORITIZE", "UNREACHABLE_PATH", "Verdict",
    "load_unreachable", "record_unreachable", "screen",
]
