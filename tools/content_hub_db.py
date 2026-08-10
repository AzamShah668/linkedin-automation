#!/usr/bin/env python3
"""SQLite store for the LinkedIn Content Hub — the content calendar database.

Works offline, no Notion token required. A Claude or Antigravity session can
sync rows to/from Notion via MCP when available.

    from content_hub_db import connect, add_idea, get_todays_post, mark_posted

Schema mirrors the Notion "Content Hub" database we'll create later.
Stdlib only.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "output" / "content_hub" / "content_hub.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    post_type       TEXT NOT NULL DEFAULT 'daily-build',
    scheduled_day   TEXT,
    scheduled_date  TEXT,
    status          TEXT NOT NULL DEFAULT 'idea',
    copy            TEXT,
    image_prompt    TEXT,
    image_path      TEXT,
    media_type      TEXT DEFAULT 'image',
    media_path      TEXT,
    hashtags        TEXT,
    source          TEXT,
    insight         TEXT,
    notion_page_id  TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    posted_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type);
CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(scheduled_date);

CREATE TABLE IF NOT EXISTS content_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at   TEXT NOT NULL,
    action      TEXT NOT NULL,
    post_id     INTEGER,
    detail      TEXT
);
"""

# Valid values for enums
VALID_TYPES = ("project", "daily-build", "trend", "lesson", "reflection")
VALID_STATUSES = ("idea", "drafted", "approved", "posted", "skipped")
VALID_DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def add_idea(
    conn: sqlite3.Connection,
    title: str,
    post_type: str = "daily-build",
    insight: str | None = None,
    scheduled_day: str | None = None,
    scheduled_date: str | None = None,
    source: str = "manual",
    hashtags: str | None = None,
) -> int:
    """Add a new content idea to the hub. Returns the row id."""
    if post_type not in VALID_TYPES:
        raise ValueError(f"post_type must be one of {VALID_TYPES}")
    if scheduled_day and scheduled_day.lower() not in VALID_DAYS:
        raise ValueError(f"scheduled_day must be one of {VALID_DAYS}")

    now = _now()
    cur = conn.execute(
        """INSERT INTO posts
           (title, post_type, scheduled_day, scheduled_date, status,
            insight, source, hashtags, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (title, post_type, (scheduled_day or "").lower() or None,
         scheduled_date, "idea", insight, source, hashtags, now, now),
    )
    conn.commit()
    _log(conn, "add_idea", cur.lastrowid, f"type={post_type} src={source}")
    return cur.lastrowid


def update_draft(
    conn: sqlite3.Connection,
    post_id: int,
    copy: str,
    image_prompt: str | None = None,
    hashtags: str | None = None,
    media_type: str = "image",
) -> dict | None:
    """Move a post from 'idea' to 'drafted' with copy and image prompt."""
    now = _now()
    conn.execute(
        """UPDATE posts SET status='drafted', copy=?, image_prompt=?,
           hashtags=COALESCE(?, hashtags), media_type=?, updated_at=?
           WHERE id=?""",
        (copy, image_prompt, hashtags, media_type, now, post_id),
    )
    conn.commit()
    _log(conn, "update_draft", post_id, "status -> drafted")
    return _get_post(conn, post_id)


def approve_post(conn: sqlite3.Connection, post_id: int) -> dict | None:
    """Mark a post as approved for publishing."""
    now = _now()
    conn.execute(
        "UPDATE posts SET status='approved', updated_at=? WHERE id=?",
        (now, post_id),
    )
    conn.commit()
    _log(conn, "approve", post_id, "status -> approved")
    return _get_post(conn, post_id)


def mark_posted(
    conn: sqlite3.Connection,
    post_id: int,
    image_path: str | None = None,
    media_path: str | None = None,
) -> dict | None:
    """Mark a post as published on LinkedIn."""
    now = _now()
    conn.execute(
        """UPDATE posts SET status='posted', posted_at=?,
           image_path=COALESCE(?, image_path),
           media_path=COALESCE(?, media_path),
           updated_at=? WHERE id=?""",
        (now, image_path, media_path, now, post_id),
    )
    conn.commit()
    _log(conn, "posted", post_id, "status -> posted")
    return _get_post(conn, post_id)


def get_todays_post(conn: sqlite3.Connection) -> dict | None:
    """Get the next approved post for today (by scheduled_date or day-of-week)."""
    today = dt.date.today().isoformat()
    day_name = dt.date.today().strftime("%a").lower()

    # First try exact date match
    row = conn.execute(
        """SELECT * FROM posts WHERE status='approved'
           AND scheduled_date=? ORDER BY id LIMIT 1""",
        (today,),
    ).fetchone()
    if row:
        return dict(row)

    # Then try day-of-week match
    row = conn.execute(
        """SELECT * FROM posts WHERE status='approved'
           AND scheduled_day=? ORDER BY id LIMIT 1""",
        (day_name,),
    ).fetchone()
    if row:
        return dict(row)

    # Finally any approved post
    row = conn.execute(
        "SELECT * FROM posts WHERE status='approved' ORDER BY id LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def get_next_drafts(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    """Get the next N drafted posts awaiting approval."""
    rows = conn.execute(
        "SELECT * FROM posts WHERE status='drafted' ORDER BY scheduled_date, id LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_posts_by_status(conn: sqlite3.Connection, status: str) -> list[dict]:
    """Get all posts with a given status."""
    rows = conn.execute(
        "SELECT * FROM posts WHERE status=? ORDER BY scheduled_date, id", (status,)
    ).fetchall()
    return [dict(r) for r in rows]


def all_posts(conn: sqlite3.Connection) -> list[dict]:
    """Get all posts ordered by date."""
    rows = conn.execute(
        "SELECT * FROM posts ORDER BY scheduled_date, id"
    ).fetchall()
    return [dict(r) for r in rows]


def stats(conn: sqlite3.Connection) -> dict:
    """Summary statistics for the content hub."""
    rows = all_posts(conn)
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_type[r["post_type"]] = by_type.get(r["post_type"], 0) + 1
    return {
        "total": len(rows),
        "by_status": by_status,
        "by_type": by_type,
    }


def _get_post(conn: sqlite3.Connection, post_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    return dict(row) if row else None


def _log(conn: sqlite3.Connection, action: str, post_id: int | None, detail: str):
    conn.execute(
        "INSERT INTO content_log (logged_at, action, post_id, detail) VALUES (?,?,?,?)",
        (_now(), action, post_id, detail),
    )
    conn.commit()


# --- CLI ---
if __name__ == "__main__":
    import sys

    conn = connect()

    if "--stats" in sys.argv:
        s = stats(conn)
        print(json.dumps(s, indent=2))
    elif "--list" in sys.argv:
        status_filter = None
        for i, arg in enumerate(sys.argv):
            if arg == "--status" and i + 1 < len(sys.argv):
                status_filter = sys.argv[i + 1]
        posts = get_posts_by_status(conn, status_filter) if status_filter else all_posts(conn)
        for p in posts:
            print(f"  [{p['status']:>8}] #{p['id']} {p['post_type']:>12} | {p['title']}")
        print(f"\n  Total: {len(posts)} post(s)")
    elif "--today" in sys.argv:
        post = get_todays_post(conn)
        if post:
            print(f"Today's post: #{post['id']} — {post['title']}")
            print(f"  Type: {post['post_type']}  Status: {post['status']}")
            if post.get("copy"):
                print(f"  Copy: {post['copy'][:200]}...")
        else:
            print("No approved post for today.")
    else:
        s = stats(conn)
        print(f"Content Hub: {s['total']} posts")
        for status, count in s["by_status"].items():
            print(f"  {status}: {count}")
