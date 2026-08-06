#!/usr/bin/env python3
"""Show (or clear) dashboard status changes that Notion has not been told about.

    py -3 tools/notion_queue.py              # list what is waiting, with the update to make
    py -3 tools/notion_queue.py --json       # same, machine-readable
    py -3 tools/notion_queue.py --mark-done  # after a Claude session has pushed them

Notion is the system of record (D7), but the dashboard can change a status locally —
the "I applied by hand and the board still said packet ready" case. Those edits live
in the local mirror and win over incoming syncs until they are pushed. This is the
handoff: a Claude session reads this, updates the Notion pages, then marks them done.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_db import connect, mark_pushed, pending_notion  # noqa: E402


def main() -> None:
    conn = connect()
    changes = pending_notion(conn)

    if "--mark-done" in sys.argv:
        if not changes:
            print("nothing was waiting.")
            return
        n = mark_pushed(conn)
        print(f"marked {n} change(s) as pushed to Notion.")
        return

    if "--json" in sys.argv:
        print(json.dumps(changes, indent=1))
        return

    if not changes:
        print("Notion is up to date — no local status changes waiting.")
        return

    print(f"{len(changes)} status change(s) made on the dashboard, not yet in Notion:\n")
    for c in changes:
        arrow = f'{c["from_status"] or "?"} -> {c["to_status"]}'
        print(f'  {c["company"]} · {c["job"]}')
        print(f'    {arrow}   (changed {c["changed_at"]})')
        if c["note"]:
            print(f'    note: {c["note"]}')
        print(f'    Notion page id: {c["job_id"]}')
        print()
    print("To reconcile: set Status on each Notion page above, then run this with --mark-done.")


if __name__ == "__main__":
    main()
