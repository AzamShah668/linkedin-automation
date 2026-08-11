"""Classify every live board row: Easy Apply, external ATS, or dead.

WHY
---
Roughly 60% of the board has no Easy Apply button, and until now nothing recorded WHICH rows. That
made two things impossible: telling the owner what he can actually action himself, and knowing how
much of the board the batch runner can even reach.

`fill.has_easy_apply()` already answers it per row and returns a reason. This just walks the board,
throttled, and writes the answer down so the dashboard and the planner can both read it without
re-opening ninety pages.

The result is a CACHE, not a source of truth. Postings close. Every record carries the date it was
checked so a stale answer is visibly stale rather than quietly wrong — the mistake D23/D29 cost a
week.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path

from apps.autopilot.answers import REPO
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    has_easy_apply,
    open_browser,
    sync_playwright,
)

TRIAGE_PATH = REPO / "output" / "apply-log" / "triage.json"
# Imported rather than re-declared: guessing this path wrote it as output/board/ and the scan died
# on "unable to open database file". One definition, in run.py.
from apps.autopilot.run import BOARD_DB  # noqa: E402

EASY = "easy-apply"
EXTERNAL = "external"
DEAD = "dead"


def load(path: Path = TRIAGE_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("rows", {})
    except (OSError, json.JSONDecodeError):
        print(f"  !! {path} unreadable; treating every row as unclassified")
        return {}


def save(rows: dict[str, dict], path: Path = TRIAGE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")


def live_rows(db: Path = BOARD_DB, statuses: tuple[str, ...] = ("New", "Invite sent")) -> list[dict]:
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    marks = ",".join("?" * len(statuses))
    out = [dict(r) for r in conn.execute(
        f"SELECT id, company, job, fit, status, url, work_type, location "
        f"FROM jobs WHERE status IN ({marks}) AND url IS NOT NULL AND url != '' "
        f"ORDER BY fit DESC", statuses)]
    conn.close()
    return out


def classify(limit: int | None = None, recheck: bool = False, headless: bool = True) -> dict[str, dict]:
    known = load()
    todo = [r for r in live_rows() if recheck or r["id"] not in known]
    if limit:
        todo = todo[:limit]
    if not todo:
        print("nothing to classify")
        return known

    print(f"classifying {len(todo)} row(s)\n")
    with sync_playwright() as pw:
        context = open_browser(pw, DEFAULT_USER_DATA_DIR, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)
            for i, row in enumerate(todo, 1):
                try:
                    ok, why = has_easy_apply(page, row["url"])
                except Exception as exc:  # a single bad page must not lose the whole scan
                    ok, why = False, f"error: {type(exc).__name__}"
                kind = EASY if ok else (DEAD if why in ("removed", "closed") else EXTERNAL)
                known[row["id"]] = {
                    "company": row["company"], "job": row["job"], "fit": row["fit"],
                    "url": row["url"], "work_type": row["work_type"], "location": row["location"],
                    "kind": kind, "why": why, "checked": date.today().isoformat(),
                }
                print(f"  [{i:>2}/{len(todo)}] {kind:<11} [{row['fit']:>3}] "
                      f"{row['company'][:22]:<22} {row['job'][:36]}")
                save(known)  # write as we go; a crash at row 40 must not lose 39 answers
                time.sleep(random.uniform(1.5, 3.5))
        except LinkedInLoggedOut as exc:
            print(f"!! {exc} — run: py -3 apps/autopilot/run.py login")
        finally:
            context.close()
    return known


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Classify board rows as Easy Apply / external / dead.")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--recheck", action="store_true", help="re-probe rows already classified")
    ap.add_argument("--show", action="store_true", help="print the current cache, probe nothing")
    args = ap.parse_args(argv)

    rows = load() if args.show else classify(limit=args.limit, recheck=args.recheck)
    counts: dict[str, int] = {}
    for r in rows.values():
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    print("\n" + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "  (empty)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
