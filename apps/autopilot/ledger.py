"""The never-resubmit ledger — the guard that must exist before submitting can.

"One attempt per company per role, ever" ([[17-auto-apply-runbook]]) has until now been a
sentence in a markdown file. A sentence cannot stop a robot.

WHY THIS DOES NOT READ THE MIRROR OR NOTION
-------------------------------------------
D29: the SQLite mirror held `Applied` for SkillsCapital while Notion said `Invite sent` and
nothing had ever been sent. A status field that has already lied is not a guard. This ledger is
therefore:

  * its own append-only file, written only AFTER a confirmed submission, and fsync'd
  * never derived from, reconciled with, or corrected by any board status
  * consulted BEFORE every apply, with a hit aborting that job loudly

TWO INDEPENDENT MECHANISMS (D30)
--------------------------------
This file is the first. The second is LinkedIn's own "Applied" indicator on the job page, checked
separately in fill.py. Neither is authoritative over the other: **either one saying "already
applied" blocks the job**, and a disagreement between them is reported rather than resolved
silently. One mechanism going wrong should be visible, not silent.

Duplicate applications are irreversible and read as spam to a recruiter. When in doubt, block.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from apps.autopilot.answers import REPO

# AUTOPILOT_LEDGER exists so the guard can be exercised against a scratch file without touching
# the real one. It is NOT a way to bypass the guard: an unset/missing file means an EMPTY ledger,
# which blocks nothing and is therefore never a silent weakening — it just fails to protect, and
# `run ledger` says "ledger is EMPTY" in as many words.
LEDGER_PATH = Path(os.environ["AUTOPILOT_LEDGER"]) if os.environ.get("AUTOPILOT_LEDGER") else (
    REPO / "output" / "apply-log" / "submitted.jsonl"
)

# A LinkedIn job id is exact. A company+role key is fuzzier but catches the SAME role reposted
# under a NEW job id — which some aggregators on this board do constantly. Both are checked.
JOB_ID_RE = re.compile(r"/jobs/view/(\d+)")


def _norm(text: str) -> str:
    """Fold to a comparable key: lowercase, alphanumeric only."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def company_role_key(company: str, role: str) -> str:
    return f"{_norm(company)}|{_norm(role)}"


def linkedin_job_id(url: str) -> str | None:
    match = JOB_ID_RE.search(url or "")
    return match.group(1) if match else None


@dataclass(frozen=True)
class Entry:
    company: str
    role: str
    submitted_at: str
    channel: str
    job_id: str | None = None
    linkedin_id: str | None = None
    url: str | None = None
    screenshot: str | None = None
    note: str = ""

    def to_json(self) -> str:
        return json.dumps(
            {
                "company_role_key": company_role_key(self.company, self.role),
                "company": self.company,
                "role": self.role,
                "submitted_at": self.submitted_at,
                "channel": self.channel,
                "job_id": self.job_id,
                "linkedin_id": self.linkedin_id,
                "url": self.url,
                "screenshot": self.screenshot,
                "note": self.note,
            },
            ensure_ascii=False,
        )


def load(path: Path = LEDGER_PATH) -> list[dict]:
    """Every recorded submission. A malformed line is skipped but never silently dropped."""
    if not path.exists():
        return []
    out: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            # Loud, not silent: a corrupt ledger line means the guard may be weaker than it looks.
            print(f"  !! ledger line {number} is not valid JSON and is being IGNORED: {line[:80]}")
    return out


# ---------------------------------------------------------------------------------------------
# The company cap window (D33).
#
# A "one role per company" cap is right — three applications to one staffing agency inside ten
# minutes land on ONE recruiter's desk and read as scattershot. But the first implementation
# counted EVERY ledger row for a company regardless of channel or age, and that is a LIFETIME
# LOCKOUT triggered by any prior contact of any kind.
#
# What it cost: Infosys has exactly one ledger row — a linkedin-dm from 2026-07-26 about a
# different role. That single line blocked all four Infosys rows including Junior AI Engineer
# (fit 90), the highest-value row on the board, for as long as the ledger exists. It also made
# the plan's ceiling look like 85 and sent two investigations chasing a "broken scorer".
#
# A cap exists to stop a recruiter seeing the same name three times in one morning. It does not
# exist to stop applying to a company you once messaged. So: same channel, recent window.
COMPANY_CAP_WINDOW_DAYS = 14
COMPANY_CAP_CHANNELS = ("linkedin-easy-apply",)


def recent_company_submissions(
    company: str,
    within_days: int = COMPANY_CAP_WINDOW_DAYS,
    channels: tuple[str, ...] = COMPANY_CAP_CHANNELS,
    path: Path = LEDGER_PATH,
    today: date | None = None,
) -> list[dict]:
    """Rows for `company` on `channels` submitted within the last `within_days` days.

    A row whose date is missing or unparseable is COUNTED. This guard's failure directions are
    not symmetric: counting one row too many costs a skipped application, while missing one costs
    a duplicate to a real recruiter, which cannot be taken back.
    """
    want = _norm(company)
    now = today or date.today()
    hits: list[dict] = []
    for row in load(path):
        if _norm(row.get("company", "")) != want:
            continue
        if row.get("channel") not in channels:
            continue
        try:
            when = date.fromisoformat(row.get("submitted_at", ""))
        except (TypeError, ValueError):
            hits.append(row)  # undateable → assume recent, see docstring
            continue
        if (now - when).days < within_days:
            hits.append(row)
    return hits


def already_applied(
    company: str, role: str, url: str = "", path: Path = LEDGER_PATH
) -> str | None:
    """Reason string if this company+role (or this exact posting) was already submitted."""
    want_key = company_role_key(company, role)
    want_linkedin = linkedin_job_id(url)

    for row in load(path):
        if want_linkedin and row.get("linkedin_id") and row["linkedin_id"] == want_linkedin:
            return (
                f"this exact posting was already submitted on {row.get('submitted_at')} "
                f"via {row.get('channel')}"
            )
        if row.get("company_role_key") == want_key:
            return (
                f"{row.get('company')} — {row.get('role')} was already submitted on "
                f"{row.get('submitted_at')} via {row.get('channel')}"
            )
    return None


def record(entry: Entry, path: Path = LEDGER_PATH) -> None:
    """Append one confirmed submission, durably.

    Called ONLY after a submission is confirmed. fsync because the alternative — a crash losing
    the record of a real submission — reopens the job for a duplicate, which is the exact harm
    this file exists to prevent. Slow and durable beats fast and forgetful.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(entry.to_json() + "\n")
        handle.flush()
        os.fsync(handle.fileno())


# ---------------------------------------------------------------------------------------
# Seed — applications that happened before the ledger existed.
#
# SOURCE OF TRUTH: Gmail "Sent" and the LinkedIn message history. NOT the board notes.
#
# ⚠️ Corrected 2026-08-09, and the correction is the point. The first version of this seed was
# built from the board notes, which said the SkillsCapital email route was "still unsent". Gmail
# proves it was sent on 2026-08-01 12:45 to careers@skillscapital.io. The guard therefore
# shipped with a hole in exactly the row it mattered most for — the highest-fit role on the
# board (93) — and it was the OLD reply-check that caught it, not this file.
#
# The lesson is D29 one level up: it is not enough to avoid reading a record that has lied. The
# SEED itself must come from the system that actually performed the action. An application is
# evidenced by a sent email or a sent message, never by a status field or a human-written note.
#
# "Applied" here means a real application reached the company for that role by ANY channel. An
# email carrying the tailored CV is an application; Easy Apply on top of it is a duplicate
# contact with the same company for the same role, which is what the rule forbids.
# ---------------------------------------------------------------------------------------
SEED = [
    Entry("SkillsCapital", "Software Engineer Intern (AI/ML & Agentic AI)", "2026-08-01", "email",
          linkedin_id="4444658927",
          url="https://www.linkedin.com/jobs/view/4444658927/",
          note="Gmail-verified: careers@skillscapital.io, 2026-08-01 12:45. The board notes said "
               "'still unsent' and were WRONG. Highest-fit row on the board."),
    Entry("Recro", "Generative AI Engineer", "2026-07-29", "linkedin-easy-apply",
          linkedin_id="4444013362",
          url="https://www.linkedin.com/jobs/view/4444013362/",
          note="The one confirmed Easy Apply submission. Runbook: NEVER RESUBMIT."),
    Entry("Infosys", "AI Application Engineer", "2026-07-26", "linkedin-dm",
          linkedin_id="4445304160",
          url="https://www.linkedin.com/jobs/view/4445304160/",
          note="Warm-insider route: full pitch + CV link delivered by LinkedIn DM."),
    Entry("CodeRound AI", "AI Engineer (LLMs & Agents)", "2026-07-30", "email",
          linkedin_id="4444922204",
          url="https://www.linkedin.com/jobs/view/4444922204/",
          note="Tailored CV delivered by email. Easy Apply was never submitted for this role."),
    Entry("Innova ESI", "DevOps Engineer", "2026-07-30", "email",
          linkedin_id="4445305388",
          url="https://www.linkedin.com/jobs/view/4445305388/",
          note="Tailored CV by email 07-30, LinkedIn DM follow-up 08-01."),
    Entry("GoodSpace AI", "Forward Deployed Engineer", "2026-07-30", "email",
          linkedin_id="4439299952",
          url="https://www.linkedin.com/jobs/view/4439299952/",
          note="Tailored CV by email 07-30, LinkedIn DM auto-sent 08-01."),
]


def seed(path: Path = LEDGER_PATH) -> tuple[int, int]:
    """Add any missing seed rows. Idempotent. Returns (added, already_present)."""
    added = skipped = 0
    for entry in SEED:
        if already_applied(entry.company, entry.role, entry.url or "", path):
            skipped += 1
            continue
        record(entry, path)
        added += 1
    return added, skipped


def describe(path: Path = LEDGER_PATH) -> str:
    rows = load(path)
    if not rows:
        return "ledger is EMPTY — nothing is protected from a duplicate submission"
    lines = [f"{len(rows)} submission(s) on record — these can never be applied to again:"]
    for row in rows:
        lines.append(
            f"  {row.get('submitted_at', '?'):<12} {row.get('channel', '?'):<20} "
            f"{row.get('company', '?')} — {row.get('role', '?')}"
        )
    return "\n".join(lines)


def today() -> str:
    return date.today().isoformat()
