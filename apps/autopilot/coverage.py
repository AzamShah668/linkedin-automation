"""Which applications have reached a human, and which are sitting in a queue alone.

WHY THIS EXISTS (D32)
---------------------
Eight Easy Apply submissions went out on 2026-08-09/10. Five of them reached **nobody**: no packet,
no recruiter identified, no outreach. That was discovered by auditing by hand, on the day someone
happened to ask. Nothing in the pipeline was tracking it.

An application that no human knows about is not a sent application, it is a queue entry. This module
makes the difference countable, so "we applied to 30 things" can never again stand in for "30 people
know who you are".

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not search LinkedIn for recruiters and it does not send connection requests.

Driving LinkedIn people-search from a script and firing invites is the automated-connection-request
pattern that gets accounts restricted, and it is the red line in this project's own north star. The
approved path already exists (D12): a Slack card, a human taps the tick, `flush-approved` sends a
bare invite. This module feeds that path; it does not replace it.

So the split is:
  * **code** decides WHICH applications lack a human — deterministic, testable, zero risk
  * **an agent** finds the recruiter, through the read-only MCP search already used for this
  * **the human** approves the invite

Ranking exists because attention is the scarce resource: the highest-fit application with no human
attached is the one worth researching first, not whichever is newest.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot.answers import REPO
from apps.autopilot import ledger, sourcing

# Windows consoles default to cp1252 and this module prints company and role names full of
# en-dashes and accents. Without this, printing raises UnicodeEncodeError mid-run - which is how
# intake.py loaded zero of 36 discovered rows while reporting only a quiet exit 1.
# Enforced by tests/test_console_encoding.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

OUTREACH_DIR = REPO / "output" / "outreach"
INVITES_PATH = OUTREACH_DIR / "pending-invites.json"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


@dataclass(frozen=True)
class Gap:
    company: str
    role: str
    submitted_at: str
    channel: str
    reason: str


def companies_with_a_named_human(
    outreach_dir: Path | None = None, invites_path: Path | None = None
) -> dict[str, str]:
    """Normalised company -> how we reached them.

    Three independent signals, because each one alone has been wrong before:
      * a `contact.md` in the company's outreach folder (someone was researched)
      * an entry in `pending-invites.json` (an invite exists, at any stage)
      * an outreach folder holding a sent/drafted message

    A company counts as covered if ANY of them fires. Over-counting coverage would hide a real gap,
    so each signal is checked against the *file system*, never against a board status — the board has
    been both stale and wrong (D23, D29).
    """
    # Resolved HERE, not in the signature. A default argument is evaluated once at import, which
    # freezes the module constant — so reassigning OUTREACH_DIR (a test, or any future caller
    # pointing this at another tree) had no effect and the function silently read the real folder.
    # Found 2026-08-10 by a test that passed for the wrong reason until one case disagreed.
    outreach_dir = outreach_dir if outreach_dir is not None else OUTREACH_DIR
    invites_path = invites_path if invites_path is not None else INVITES_PATH

    covered: dict[str, str] = {}

    if outreach_dir.exists():
        for folder in sorted(outreach_dir.iterdir()):
            if not folder.is_dir():
                continue
            contact = folder / "contact.md"
            if not contact.exists():
                continue
            # A contact.md that records "nobody exists" is NOT coverage. Crossing Hurdles has one.
            try:
                body = contact.read_text(encoding="utf-8", errors="replace")
            except OSError:
                body = ""
            if re.search(r"NO CONTACT FINDABLE|no findable human|zero employees", body, re.I):
                continue
            covered[_norm(folder.name)] = f"researched in output/outreach/{folder.name}/"

    if invites_path.exists():
        try:
            data = json.loads(invites_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        for invite in data.get("invites", []):
            slug = _norm(invite.get("slug", ""))
            if slug:
                covered.setdefault(slug, f"invite {invite.get('status', '?')}")

    return covered


def _company_matches(company: str, covered: dict[str, str]) -> str | None:
    """Coverage is keyed by folder slug, which is not always the company name verbatim."""
    key = _norm(company)
    if key in covered:
        return covered[key]
    for slug, how in covered.items():
        # "goodspace" covers "GoodSpace AI"; "skillscapital" covers "SkillsCapital".
        if slug and (slug in key or key in slug):
            return how
    return None


def gaps(rows: list[dict] | None = None) -> list[Gap]:
    """Applications with no human attached, worst first."""
    covered = companies_with_a_named_human()
    unreachable = sourcing.load_unreachable()
    out: list[Gap] = []
    seen: set[str] = set()

    for row in (rows if rows is not None else ledger.load()):
        company = row.get("company", "")
        key = _norm(company)
        if not company or key in seen:
            continue
        seen.add(key)

        if key in unreachable:
            continue  # recorded as having nobody to reach; not a gap, a dead end (D36)
        if _company_matches(company, covered):
            continue

        out.append(Gap(
            company=company,
            role=row.get("role", ""),
            submitted_at=row.get("submitted_at", ""),
            channel=row.get("channel", ""),
            reason="applied, but no recruiter has been identified",
        ))

    # Oldest first: an application that has been silent longest is the one whose window is closing.
    out.sort(key=lambda g: g.submitted_at or "9999")
    return out


def notify(items: list[Gap]) -> None:
    if not items:
        return
    lines = [f"- {g.company} ({g.role[:44]}) applied {g.submitted_at}" for g in items[:10]]
    body = (
        f"{len(items)} application(s) have reached NO human:\n" + "\n".join(lines)
        + "\n\nNext: find one recruiter per company, then approve the invite as usual."
    )
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", "info", "--title", f"{len(items)} application(s) with nobody attached",
             "--text", body],
            cwd=REPO, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  !! could not post to Slack ({exc}); the gaps above still stand")
        return
    print("  slack: notified" if proc.returncode == 0
          else f"  !! slack REFUSED (exit {proc.returncode}); the gaps above still stand")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Applications that have reached no human.")
    ap.add_argument("--notify", action="store_true")
    args = ap.parse_args(argv)

    applied = ledger.load()
    items = gaps()
    reached = len({_norm(r.get("company", "")) for r in applied}) - len(items)

    print(f"{len(applied)} application(s) across {len({_norm(r.get('company','')) for r in applied})} "
          f"company(ies)")
    print(f"  reached a human: {reached}")
    print(f"  reached NOBODY:  {len(items)}\n")
    for g in items:
        print(f"  {g.submitted_at}  {g.company[:26]:<26} {g.role[:40]:<40} via {g.channel}")
    if items and args.notify:
        notify(items)
    if not items:
        print("  every application has a human attached")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
