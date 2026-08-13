#!/usr/bin/env python3
"""Feed the local board into followups.py, which has never had an input wired to it.

WHY THIS EXISTS (found 2026-08-14)
----------------------------------
`tools/followups.py` computes the Day-3 / Day-7 nudge cadence and has worked since the
completion plan. It reads JSON on stdin because, in its own words, "there is no Notion token
in .env ... the runner queries Notion and pipes them in." That runner was Claude-via-MCP.

NOTION_TOKEN is still unset and the real store moved to `database/board.sqlite3`, so nothing
has ever piped anything in. The engine was complete and **fed by nothing** - which is why two
recruiters pitched on 2026-08-01 sat 13 days with no nudge, and why the LinkedIn inbox shows
Azam's own message as the last one in both threads.

    py -3 tools/followups_from_board.py                 # dry-run, prints what is due
    py -3 tools/followups_from_board.py --emit-json     # just the JSON, to pipe yourself
    py -3 tools/followups_from_board.py --notify        # Slack a card per due nudge

⚠️ TWO FIELDS THE SCHEMA CANNOT ANSWER
--------------------------------------
`jobs` has no `reply` column and no `followups_sent` column. followups.py needs both. This
script therefore emits `reply=false, followups_sent=0` for every row and says so loudly.

That direction is deliberate (D-"choose the failure direction first"). Over-reporting costs
one Slack card that Azam ignores; under-reporting costs a lead going cold and is invisible.
And **nothing here sends** - followups.py only drafts, and every nudge is still his click. The
one real hazard is sending a *duplicate* Day-3 to someone who already got one, so the output
says, every run, that `followups_sent` is a guess.

The proper fix is two columns on `jobs`. Until then this is honest rather than silent.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(REPO, "database", "board.sqlite3")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def board_rows() -> list[dict]:
    """Applied rows with a real applied date, shaped for followups.py."""
    if not os.path.exists(DB):
        raise SystemExit(f"no board at {DB} - run sync-board first")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT job, company, status, applied, url
        FROM jobs
        WHERE status = 'Applied' AND applied IS NOT NULL AND applied != ''
        ORDER BY applied
        """
    ).fetchall()
    conn.close()
    return [
        {
            "job": r["job"],
            "company": r["company"],
            "status": r["status"],
            "applied_date": r["applied"],
            "url": r["url"] or "",
            # NOT IN THE SCHEMA. See the module docstring - these are assumptions, not data.
            "reply": False,
            "followups_sent": 0,
        }
        for r in rows
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit-json", action="store_true", help="print the JSON and stop")
    ap.add_argument("--notify", action="store_true", help="pass --notify through to followups.py")
    ap.add_argument("--today", help="override today's date YYYY-MM-DD (for testing)")
    args = ap.parse_args()

    jobs = board_rows()
    payload = json.dumps(jobs, ensure_ascii=True)

    if args.emit_json:
        print(payload)
        return 0

    print(f"Feeding {len(jobs)} Applied row(s) from database/board.sqlite3 into followups.py.")
    print("WARNING: `reply` and `followups_sent` are NOT columns on `jobs`. Every row is sent")
    print("         through as reply=false, followups_sent=0. Anything already nudged, or")
    print("         already answered, will still be listed. Check before you send.\n")
    # Flush before handing the console to the child. Without this the caveat lands AFTER
    # ~40 lines of nudges, and a warning printed below the thing it warns about is not a
    # warning. Cost one confusing run on 2026-08-14.
    sys.stdout.flush()

    cmd = [sys.executable, os.path.join(REPO, "tools", "followups.py")]
    if args.notify:
        cmd.append("--notify")
    if args.today:
        cmd += ["--today", args.today]
    return subprocess.run(cmd, input=payload, text=True, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
