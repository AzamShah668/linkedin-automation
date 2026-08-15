"""Decide which applications are due a follow-up, from records that are actually true.

WHY THIS EXISTS
---------------
`tools/followups.py` has computed the Day-3 / Day-7 cadence correctly since the completion plan and
has **never had a truthful input**. It reads JSON on stdin, expecting a runner to supply
`applied_date`, `reply` and `followups_sent`. The runner was Claude-via-MCP against Notion, and
`NOTION_TOKEN` was never set, so nothing was ever piped in: two recruiters pitched on 2026-08-01 sat
thirteen days with no nudge.

`tools/followups_from_board.py` then wired the board in, and had to emit `reply=false,
followups_sent=0` for **every** row, because `jobs` has neither column. It says so loudly, which is
honest, but it means the one genuinely dangerous mistake -- sending a second Day-3 to someone who
already got one -- was left to whoever read the output.

Both numbers are already recorded somewhere truthful. This module reads them from there:

  * **applied_date** <- `output/apply-log/submitted.jsonl`, the append-only ledger. It is the send
    record, seeded from Gmail Sent and LinkedIn history, and is the only artefact in this project
    that has never been wrong about whether something went out.
  * **followups_sent** <- `output/apply-log/followups-sent.jsonl`, written when a nudge is actually
    sent. A real count, not a zero standing in for one.
  * **reply / dead** <- the board's status column, for the states that mean stop.

WHAT IT DOES NOT DO
-------------------
It does not send. `followups.py` drafts, this feeds it, and a human still sends every nudge.

⚠️ AND IT MUST NEVER PUT `ref:<slug>` IN A SLACK CARD. `tools/check_approvals.py` greps for exactly
that string to find *connection-request* approvals, and `flush-approved` acts on what it finds. A
nudge card carrying a ref would turn "yes, send this follow-up message" into "send a connection
request to this company", silently, through a completely different runner.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot import ledger, sourcing
from apps.autopilot.answers import REPO

BOARD_DB = REPO / "database" / "board.sqlite3"
SENT_LOG = REPO / "output" / "apply-log" / "followups-sent.jsonl"
NOTIFIED_LOG = REPO / "output" / "apply-log" / "nudges-notified.jsonl"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Statuses that mean "stop chasing". A reply is good news and a rejection is bad news, and both end
# the cadence; leaving either out produces a nudge that reads as though nobody was paying attention.
STOP_STATUSES = {"interview", "rejected", "offer", "closed", "skipped", "replied", "hired"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _engine():
    """Load tools/followups.py by PATH and reuse its cadence and templates.

    Imported rather than reimplemented so there is exactly one definition of the schedule and one
    set of message templates. `tools/` is not a package, so this is the same load-by-file-path
    pattern `tools/board_db.py` already uses.
    """
    spec = importlib.util.spec_from_file_location(
        "_followups_engine", REPO / "tools" / "followups.py")
    if spec is None or spec.loader is None:      # pragma: no cover
        raise RuntimeError("could not load tools/followups.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sent_counts(path: Path | None = None) -> dict[str, int]:
    """Normalised company -> how many nudges have ACTUALLY been sent.

    ⚠️ The path is resolved HERE, not in the signature. A default argument is evaluated once at
    import, which freezes the module constant, so reassigning SENT_LOG had no effect and this read
    the real send record anyway. `coverage.py` carries the same warning for the same reason -- and
    this module still reintroduced it, which is why every path below is resolved at call time.
    """
    path = path if path is not None else SENT_LOG
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = _norm(row.get("company", ""))
        if key:
            counts[key] = counts.get(key, 0) + 1
    return counts


def board_status(db: Path | None = None) -> dict[str, str]:
    """Normalised company -> its furthest-along status. Path resolved at CALL time (see sent_counts)."""
    db = db if db is not None else BOARD_DB
    if not db.exists():
        return {}
    out: dict[str, str] = {}
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error:
        return {}
    try:
        for company, status in conn.execute("SELECT company, status FROM jobs"):
            key = _norm(company or "")
            if not key:
                continue
            # A stop beats anything else recorded for the same company.
            if (status or "").strip().lower() in STOP_STATUSES:
                out[key] = (status or "").strip()
            else:
                out.setdefault(key, (status or "").strip())
    except sqlite3.Error:
        return out
    finally:
        conn.close()
    return out


def notified(path: Path | None = None) -> set[tuple[str, int]]:
    """(company, day) pairs already pushed to Slack, so a due nudge is announced once, not daily."""
    path = path if path is not None else NOTIFIED_LOG
    out: set[tuple[str, int]] = set()
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        company, day = _norm(row.get("company", "")), row.get("day")
        if company and isinstance(day, int):
            out.add((company, day))
    return out


def record_notified(company: str, day: int, path: Path | None = None) -> None:
    path = path if path is not None else NOTIFIED_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "company": company, "day": day,
            "notified_at": dt.date.today().isoformat(),
        }, ensure_ascii=False) + "\n")


@dataclass(frozen=True)
class Due:
    company: str
    role: str
    applied: str
    day: int
    days_since: int
    text: str
    channel: str


def plan(today: dt.date | None = None, rows: list[dict] | None = None) -> list[Due]:
    """Every application whose next nudge is due, oldest first."""
    engine = _engine()
    today = today or dt.date.today()
    counts = sent_counts()
    statuses = board_status()
    # A company proven to have nobody findable cannot receive a follow-up either: the application
    # went into an auto-acknowledging void (D36). Chasing it wastes the owner's attention on the
    # one queue that is supposed to be all real leads.
    unreachable = sourcing.load_unreachable()

    # One entry per company, keyed on its MOST RECENT application: two roles at one employer is one
    # conversation, and nudging twice about the same company in a week reads as automation.
    latest: dict[str, dict] = {}
    for row in (rows if rows is not None else ledger.load()):
        key = _norm(row.get("company", ""))
        if not key:
            continue
        if key not in latest or (row.get("submitted_at", "") > latest[key].get("submitted_at", "")):
            latest[key] = row

    out: list[Due] = []
    for key, row in latest.items():
        status = statuses.get(key, "")
        if status.strip().lower() in STOP_STATUSES:
            continue
        if key in unreachable:
            continue
        job = {
            "company": row.get("company", ""),
            "job": row.get("role", ""),
            # followups.py gates on status == "Applied"; every ledger row IS an application that
            # went out, which is a stronger fact than any board column.
            "status": "Applied",
            "applied_date": (row.get("submitted_at") or "")[:10],
            "reply": False,
            "followups_sent": counts.get(key, 0),
            "url": row.get("url", ""),
        }
        due = engine.due_for(job, today)
        if not due:
            continue
        out.append(Due(
            company=row.get("company", ""), role=row.get("role", ""),
            applied=job["applied_date"], day=due["day"], days_since=due["days_since"],
            text=due["text"], channel=row.get("channel", ""),
        ))

    out.sort(key=lambda d: d.applied)
    return out


def notify(item: Due) -> bool:
    title = f"{item.company} · {item.role[:44]} — Day {item.day} nudge due"
    # No `ref:` token. See the module docstring: that string is the connection-request approval
    # gate, and putting it here would make a nudge approval fire a connection request instead.
    text = (
        f"No reply {item.days_since} day(s) after applying ({item.applied}, via {item.channel}).\n"
        f"Draft:\n> {item.text}\n"
        f"Send it yourself, then log it:\n"
        f"`py -3 -m apps.autopilot.nudge --mark \"{item.company}\"`"
    )
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", "followup_due", "--title", title, "--text", text],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  !! slack failed ({exc}); the nudge above is still due")
        return False
    if proc.returncode != 0:
        print(f"  !! slack REFUSED (exit {proc.returncode}); the nudge above is still due")
        return False
    return True


def mark_sent(company: str, path: Path | None = None) -> None:
    path = path if path is not None else SENT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "company": company, "sent_at": dt.date.today().isoformat(),
            "kind": "day-3/day-7 nudge", "channel": "manual",
        }, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Follow-ups that are due. Sends nothing.")
    ap.add_argument("--notify", action="store_true", help="post each newly-due nudge to Slack once")
    ap.add_argument("--today", help="override today's date, YYYY-MM-DD")
    ap.add_argument("--mark", metavar="COMPANY",
                    help="record that you sent a nudge to COMPANY (keeps the count honest)")
    args = ap.parse_args(argv)

    if args.mark:
        mark_sent(args.mark)
        print(f"recorded a nudge to {args.mark}; its next one is now scheduled from this count")
        return 0

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    items = plan(today)
    already = notified()

    print(f"{len(items)} follow-up(s) due as of {today}\n")
    posted = 0
    for item in items:
        seen = (_norm(item.company), item.day) in already
        mark = "   " if seen else ">> "
        print(f" {mark}Day {item.day}  {item.company[:26]:<26} {item.role[:34]:<34} "
              f"applied {item.applied} ({item.days_since}d)")
        if args.notify and not seen:
            if notify(item):
                record_notified(item.company, item.day)
                posted += 1

    if not items:
        print("  nothing is due")
    elif args.notify:
        print(f"\n{posted} card(s) posted to Slack; {len(items) - posted} already announced earlier")
    else:
        print("\nDry run. Add --notify to post. Every nudge is still sent by hand.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
