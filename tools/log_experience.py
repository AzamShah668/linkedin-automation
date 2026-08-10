#!/usr/bin/env python3
"""Log a pair-programming experience or discovery as a LinkedIn post idea.

    py -3 tools/log_experience.py --title "How we fixed lock contention" --insight "The bug was a missing mutex on the shared counter" --type daily-build
    py -3 tools/log_experience.py --title "Local LLMs vs Cloud APIs" --type trend --insight "Latency wins for <500 token tasks"
    py -3 tools/log_experience.py --list
    py -3 tools/log_experience.py --dry-run --title "Test" --insight "Test"

Both Claude and Antigravity can call this. The Notion Content Hub is the
local SQLite database (tools/content_hub_db.py). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from content_hub_db import connect, add_idea, all_posts, stats  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log an experience / discovery as a LinkedIn post idea"
    )
    parser.add_argument("--title", "-t", help="Short title for the post idea")
    parser.add_argument(
        "--insight", "-i",
        help="The key insight, problem, or discovery (1-3 sentences)"
    )
    parser.add_argument(
        "--type", dest="post_type", default="daily-build",
        choices=["project", "daily-build", "trend", "lesson", "reflection"],
        help="Content type (default: daily-build)"
    )
    parser.add_argument("--day", help="Scheduled day (mon-sun)")
    parser.add_argument("--date", help="Scheduled date (YYYY-MM-DD)")
    parser.add_argument(
        "--hashtags", help="Comma-separated hashtags (e.g. #DevOps,#Python)"
    )
    parser.add_argument(
        "--source", default="agent-session",
        help="Who created this (default: agent-session)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be logged")
    parser.add_argument("--list", action="store_true", help="List all ideas")
    parser.add_argument("--stats", action="store_true", help="Show hub stats")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if args.list:
        conn = connect()
        posts = all_posts(conn)
        if args.json:
            print(json.dumps(posts, indent=2, default=str))
        else:
            for p in posts:
                print(f"  [{p['status']:>8}] #{p['id']} {p['post_type']:>12} | {p['title']}")
            print(f"\n  Total: {len(posts)} post(s)")
        return

    if args.stats:
        conn = connect()
        s = stats(conn)
        print(json.dumps(s, indent=2))
        return

    if not args.title:
        parser.error("--title is required when logging an experience")

    if args.dry_run:
        print(f"[DRY RUN] Would log:")
        print(f"  Title:   {args.title}")
        print(f"  Type:    {args.post_type}")
        print(f"  Insight: {args.insight or '(none)'}")
        print(f"  Day:     {args.day or '(auto)'}")
        print(f"  Date:    {args.date or '(auto)'}")
        print(f"  Source:  {args.source}")
        return

    conn = connect()
    row_id = add_idea(
        conn,
        title=args.title,
        post_type=args.post_type,
        insight=args.insight,
        scheduled_day=args.day,
        scheduled_date=args.date,
        source=args.source,
        hashtags=args.hashtags,
    )

    result = {
        "status": "logged",
        "id": row_id,
        "title": args.title,
        "post_type": args.post_type,
        "message": f"Logged idea #{row_id}: '{args.title}' as {args.post_type}",
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Logged idea #{row_id}: '{args.title}' ({args.post_type})")
        if args.insight:
            print(f"  Insight: {args.insight}")
        print(f"  Source:  {args.source}")
        s = stats(conn)
        print(f"  Hub now has {s['total']} post(s)")


if __name__ == "__main__":
    main()
