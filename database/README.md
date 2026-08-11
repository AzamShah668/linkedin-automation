# database/ — the board store

The one store the whole pipeline plans from, and the schema that defines it.

| File | What it is |
|---|---|
| `board_db.py` | schema + access layer (`connect`, `all_rows`, `set_status`, `stats`, …) |
| `board.sqlite3` | **the data — gitignored, never committed** |

## Why it moved here

It used to live in `output/dashboard/`, beside generated HTML and disposable exports. That made
the one irreplaceable file in the project look like build output. `output/` is routinely cleaned;
this must not be.

## ⚠️ The data file is deliberately NOT in git

This repository is **public**. The `notes` column holds **real recruiter names on 17 rows** —
who was contacted, when, and through which warm connection. `.gitignore` blocks
`database/*.sqlite3`. The **schema and access layer are tracked**; the data is not.

Never commit a `.sqlite3` from this folder, and never paste `notes` content into a document that
lands in the repo. Recruiters appear as `Recruiter-A/B/C` in everything committed.

## Who reads it

- `backend/server.py` — the dashboard API
- `apps/autopilot/run.py` — picks which jobs to apply to (`BOARD_DB`)
- `tools/*.ps1` and `tools/*.py` — via the compatibility shim at `tools/board_db.py`

## The one rule that has already cost a week

**A mirror can be stale *and* it can be wrong.** On 2026-08-01 this file held 24 rows while Notion
held 94, and the packet sweeper quietly planned from the smaller set. On 2026-08-06 it reported a
company as `Applied` that had never been contacted.

So: **nothing that decides whether to send something may trust this store alone.** The
never-resubmit guard (`apps/autopilot/ledger.py`) is a separate append-only file that imports
nothing capable of reading a board status — enforced by a test that walks its AST. See
`docs/knowledge/05-decisions.md` D23 and D29.
