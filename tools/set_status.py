#!/usr/bin/env python3
"""set_status.py — set one job's status in the local mirror from the command line.

The dashboard could already do this (`serve_dashboard.py` calls `board_db.set_status`),
but nothing could from a shell, so the build-packet runbook's step 7 had no way to set
the mirror side without an inline `py -3 -c` — which the headless allowlist refuses.

Notion stays the system of record (D7). This records the change as UNPUSHED, so a later
`py -3 tools/notion_push.py` reconciles it.

Usage:
  py -3 tools/set_status.py <notion-page-id> "To Apply"
  py -3 tools/set_status.py <notion-page-id> "To Apply" --note "packet built"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from board_db import ALLOWED_STATUS, connect, set_status  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Set a job's status in the local mirror.")
    ap.add_argument("job_id", help="Notion page id of the board row")
    ap.add_argument("status", help=f"one of: {', '.join(ALLOWED_STATUS)}")
    ap.add_argument("--note", default=None, help="why the status changed")
    args = ap.parse_args()

    try:
        row = set_status(connect(), args.job_id, args.status, args.note)
    except ValueError as exc:
        sys.exit(f"ERROR: {exc}")

    if row is None:
        sys.exit(f"ERROR: no row in the mirror with id {args.job_id}. "
                 "Re-sync the mirror from Notion first (D23).")

    print(f"OK  {row['company']} / {row['job']}  ->  {row['status']}")
    print("Recorded as unpushed. Reconcile with: py -3 tools/notion_push.py")


if __name__ == "__main__":
    main()
