#!/usr/bin/env python3
"""Push Notion board rows into the local SQLite mirror.

    py -3 tools/sync_board.py                                  # from the seed file
    py -3 tools/sync_board.py path/to/rows.json                # from a file
    <notion query output> | py -3 tools/sync_board.py -        # from stdin

Accepts either shape:
  1. canonical  {"rows": [{id, job, company, fit, status, ...}], "captured": "..."}
  2. raw Notion MCP result  {"results": [{"Job": ..., "Company": ..., ...}]}

Shape 2 means a Claude session can paste the `notion-query-data-sources` result
through unchanged — no hand-translation, which is where transcription errors live.

Refresh loop (until a Notion API token exists): a Claude session runs the board
query over MCP, writes the result to a file, and calls this. The dashboard then
serves from SQLite with no Notion dependency at all.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from board_db import connect, log_sync, stats, upsert_rows  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "output" / "dashboard" / "board-seed.json"


def from_notion(results: list[dict]) -> list[dict]:
    """Translate the raw MCP row shape into the canonical one."""
    rows = []
    for r in results:
        rows.append({
            "id": r.get("id"),
            "job": r.get("Job") or "(untitled role)",
            "company": r.get("Company") or "—",
            "fit": r.get("Fit Score"),
            "status": r.get("Status") or "New",
            "work_type": r.get("Work Type"),
            "location": r.get("Location"),
            "warm": r.get("Warm Intro") == "__YES__",
            "url": r.get("userDefined:URL"),
            "found": r.get("date:Found:start"),
            "applied": r.get("date:Applied Date:start"),
            "next_action": r.get("date:Next Action:start"),
            "notes": r.get("Notes"),
        })
    return rows


def load(arg: str | None) -> tuple[list[dict], str, str | None]:
    if arg == "-":
        payload = json.load(sys.stdin)
        source = "stdin"
    else:
        path = Path(arg) if arg else SEED
        if not path.exists():
            sys.exit(f"no such file: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        source = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)

    if isinstance(payload, list):
        return payload, source, None
    if "rows" in payload:
        return payload["rows"], source, payload.get("captured")
    if "results" in payload:
        return from_notion(payload["results"]), source, payload.get("captured")
    sys.exit("unrecognised payload: expected 'rows' or 'results'")


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    rows, source, captured = load(arg)
    if not rows:
        sys.exit("no rows to sync")

    conn = connect()
    inserted, updated, protected = upsert_rows(conn, rows, captured=captured)
    log_sync(conn, source, len(rows), captured)
    s = stats(conn)

    print(f"synced {len(rows)} rows from {source}  (+{inserted} new, {updated} updated)")
    if protected:
        print(f"kept {protected} local status change(s) that Notion has not been told about yet")
    print(f"board now: {s['total']} roles · {s['companies']} companies · {s['warm']} warm")
    order = ["delivered", "inflight", "ready", "cold", "closed"]
    parts = [f"{k}={s['by_stage'][k]}" for k in order if k in s["by_stage"]]
    print("stages: " + " · ".join(parts))


if __name__ == "__main__":
    main()
