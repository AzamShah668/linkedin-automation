#!/usr/bin/env python3
"""SQLite store for the job board — the local database behind the dashboard.

Notion stays the system of record (decision D7). This is a **local mirror** so the
dashboard has a real queryable backend that works offline and without a Notion
token: a Claude session (or the discovery task) re-queries Notion via MCP and
pushes rows in through `sync_board.py`.

    from board_db import connect, upsert_rows, all_rows, stats

Schema is deliberately flat — one row per Notion page, plus a sync log so you can
tell how stale the mirror is. Stdlib only.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "output" / "dashboard" / "board.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id           TEXT PRIMARY KEY,
    job          TEXT NOT NULL,
    company      TEXT NOT NULL,
    fit          INTEGER,
    status       TEXT,
    work_type    TEXT,
    location     TEXT,
    warm         INTEGER DEFAULT 0,
    url          TEXT,
    found        TEXT,
    applied      TEXT,
    next_action  TEXT,
    notes        TEXT,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_fit     ON jobs(fit DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status  ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);

CREATE TABLE IF NOT EXISTS sync_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    synced_at  TEXT NOT NULL,
    source     TEXT,
    row_count  INTEGER,
    captured   TEXT
);

-- Status changes made from the dashboard. Notion is still the system of record
-- (D7), so a local edit is recorded here as UNPUSHED until a Claude session
-- writes it back. Without this the mirror would silently diverge from Notion and
-- the next sync would quietly undo the owner's edit.
CREATE TABLE IF NOT EXISTS status_changes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        TEXT NOT NULL,
    from_status   TEXT,
    to_status     TEXT NOT NULL,
    note          TEXT,
    changed_at    TEXT NOT NULL,
    pushed_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_changes_unpushed ON status_changes(pushed_at);
"""

# Notion Status -> pipeline stage. Stage is derived, never stored, so a status
# rename in Notion needs one edit here and nothing else.
STAGE = {
    "Applied": "delivered",
    "Interview": "delivered",
    "Invite sent": "inflight",
    "To Apply": "ready",
    "New": "cold",
    "Rejected": "closed",
    "Skipped": "closed",
}

FIELDS = (
    "job", "company", "fit", "status", "work_type", "location",
    "warm", "url", "found", "applied", "next_action", "notes",
)


def _parse_ts(value: str | None) -> dt.datetime | None:
    """Parse an ISO timestamp, tolerating a trailing Z and dropping the timezone.

    Captures carry an offset (+05:30) while local change stamps are naive, and
    comparing the two raises. Normalising to naive local time keeps the comparison
    honest for a single-machine tool.
    """
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_rows(conn: sqlite3.Connection, rows: list[dict],
                captured: str | None = None) -> tuple[int, int, int]:
    """Insert or update by Notion page id. Returns (inserted, updated, protected).

    A local status change WINS over the incoming row unless the capture is provably
    newer than the change. Otherwise a refresh would silently revert the owner's
    edit to a stale Notion value — an edit that appears to work then undoes itself
    is worse than no edit button at all.

    `captured` is when the incoming rows were read out of Notion. Comparing it to
    each change's timestamp is what makes this self-correcting: once a capture is
    newer than the change, Notion demonstrably knows, and the guard lifts on its
    own. Without that comparison the guard depended on remembering to refresh the
    seed before clearing the queue, and getting that order wrong reverted the row.
    """
    now = dt.datetime.now().isoformat(timespec="seconds")
    existing = {r["id"] for r in conn.execute("SELECT id FROM jobs")}

    cap = _parse_ts(captured)
    unpushed = {}
    for c in conn.execute(
            "SELECT job_id, to_status, changed_at FROM status_changes "
            "WHERE pushed_at IS NULL ORDER BY id"):
        changed = _parse_ts(c["changed_at"])
        if cap and changed and cap > changed:
            continue          # this capture already reflects the change
        unpushed[c["job_id"]] = c["to_status"]
    # The local applied date is derived from the local status change, so it has to be
    # preserved alongside it — protecting `status` alone silently wiped the date.
    local_applied = {
        r["id"]: r["applied"]
        for r in conn.execute("SELECT id, applied FROM jobs WHERE applied IS NOT NULL")
    }
    inserted = updated = protected = 0

    for r in rows:
        rid = r.get("id")
        if not rid:
            continue
        if rid in unpushed:
            if r.get("status") != unpushed[rid]:
                protected += 1
            r = dict(r)
            r["status"] = unpushed[rid]
            if not r.get("applied") and local_applied.get(rid):
                r["applied"] = local_applied[rid]
        values = [r.get(f) for f in FIELDS]
        values[FIELDS.index("warm")] = 1 if r.get("warm") else 0
        if rid in existing:
            updated += 1
        else:
            inserted += 1
        conn.execute(
            f"""INSERT INTO jobs (id, {", ".join(FIELDS)}, updated_at)
                VALUES (?{", ?" * (len(FIELDS) + 1)})
                ON CONFLICT(id) DO UPDATE SET
                  {", ".join(f"{f}=excluded.{f}" for f in FIELDS)},
                  updated_at=excluded.updated_at""",
            [rid, *values, now],
        )
    conn.commit()
    return inserted, updated, protected


def log_sync(conn: sqlite3.Connection, source: str, count: int, captured: str | None) -> None:
    conn.execute(
        "INSERT INTO sync_log (synced_at, source, row_count, captured) VALUES (?,?,?,?)",
        (dt.datetime.now().isoformat(timespec="seconds"), source, count, captured),
    )
    conn.commit()


ALLOWED_STATUS = ("New", "To Apply", "Invite sent", "Applied", "Interview", "Rejected", "Skipped")

# Statuses that mean the CV has actually reached someone, so an Applied Date is set.
DELIVERED_STATUS = ("Applied", "Interview")


def set_status(conn: sqlite3.Connection, job_id: str, status: str,
               note: str | None = None) -> dict | None:
    """Change a job's status from the dashboard. Returns the updated row.

    Records the change as unpushed so Notion can be reconciled later — and stamps
    `applied` when the status means the CV went out, because the owner applying by
    hand is exactly the case this exists for.
    """
    if status not in ALLOWED_STATUS:
        raise ValueError(f"status must be one of {', '.join(ALLOWED_STATUS)}")

    cur = conn.execute("SELECT status, applied FROM jobs WHERE id = ?", (job_id,))
    row = cur.fetchone()
    if row is None:
        return None
    previous = row["status"]
    now = dt.datetime.now()

    applied = row["applied"]
    if status in DELIVERED_STATUS and not applied:
        applied = now.date().isoformat()

    conn.execute(
        "UPDATE jobs SET status = ?, applied = ?, updated_at = ? WHERE id = ?",
        (status, applied, now.isoformat(timespec="seconds"), job_id),
    )
    conn.execute(
        """INSERT INTO status_changes (job_id, from_status, to_status, note, changed_at)
           VALUES (?,?,?,?,?)""",
        (job_id, previous, status, note, now.isoformat(timespec="seconds")),
    )
    conn.commit()

    updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    d = dict(updated)
    d["warm"] = bool(d["warm"])
    d["stage"] = STAGE.get(d.get("status") or "", "cold")
    d["warm_hinted"] = _warm_hinted(d)
    return d


def pending_notion(conn: sqlite3.Connection) -> list[dict]:
    """Dashboard edits Notion has not been told about — one row per job, latest state.

    Collapsed per job on purpose: Notion only needs the value to end up at, not a
    replay of every click. Re-marking a role three times is one update, not three.
    """
    sql = """SELECT c.id, c.job_id, c.from_status, c.to_status, c.note, c.changed_at,
                    j.job, j.company
             FROM status_changes c LEFT JOIN jobs j ON j.id = c.job_id
             WHERE c.pushed_at IS NULL ORDER BY c.id"""
    latest: dict[str, dict] = {}
    for row in conn.execute(sql):
        d = dict(row)
        prior = latest.get(d["job_id"])
        if prior:
            d["from_status"] = prior["from_status"]   # keep where it actually started
        latest[d["job_id"]] = d
    return list(latest.values())


def mark_pushed(conn: sqlite3.Connection, change_ids: list[int] | None = None) -> int:
    now = dt.datetime.now().isoformat(timespec="seconds")
    if change_ids:
        marks = ",".join("?" * len(change_ids))
        cur = conn.execute(
            f"UPDATE status_changes SET pushed_at = ? WHERE pushed_at IS NULL AND id IN ({marks})",
            [now, *change_ids])
    else:
        cur = conn.execute(
            "UPDATE status_changes SET pushed_at = ? WHERE pushed_at IS NULL", (now,))
    conn.commit()
    return cur.rowcount


def all_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = []
    for r in conn.execute("SELECT * FROM jobs ORDER BY fit DESC, company"):
        d = dict(r)
        d["warm"] = bool(d["warm"])
        d["stage"] = STAGE.get(d.get("status") or "", "cold")
        rows.append(d)
    return rows


def last_sync(conn: sqlite3.Connection) -> dict | None:
    cur = conn.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    return dict(row) if row else None


def stats(conn: sqlite3.Connection) -> dict:
    rows = all_rows(conn)
    by_stage: dict[str, int] = {}
    for r in rows:
        by_stage[r["stage"]] = by_stage.get(r["stage"], 0) + 1
    return {
        "total": len(rows),
        "companies": len({r["company"] for r in rows}),
        "warm": sum(1 for r in rows if r["warm"] or _warm_hinted(r)),
        "by_stage": by_stage,
        "last_sync": last_sync(conn),
        "pending_notion": len(pending_notion(conn)),
    }


def _warm_hinted(row: dict) -> bool:
    """Notes say warm/alumni but the checkbox is unticked — a real data gap that
    silently drops rows out of warm filters (Oracle SRE is the live example)."""
    notes = (row.get("notes") or "").lower()
    return not row.get("warm") and ("warm" in notes or "alumn" in notes)


def warm_hinted(row: dict) -> bool:
    return _warm_hinted(row)
