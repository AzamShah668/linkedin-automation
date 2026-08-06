#!/usr/bin/env python3
"""Export the Job Hunt Slack channel to JSON for the Send Board dashboard.

Reads SLACK_BOT_TOKEN + SLACK_CHANNEL_ID from .env. Stdlib only (urllib).
Needs the history scope for the channel type: the Job Hunt channel is PRIVATE,
so `groups:history` is the one that matters (`channels:history` alone fails).

Writes output/dashboard/slack-export.json — never prints the token.

Usage:  py -3 tools/slack_export.py [--limit 300]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "dashboard" / "slack-export.json"
API = "https://slack.com/api/"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        sys.exit("no .env found")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def call(method: str, token: str, **params) -> dict:
    url = API + method + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if not data.get("ok"):
        err = data.get("error", "unknown")
        needed = data.get("needed")
        hint = f" (needs scope: {needed})" if needed else ""
        sys.exit(f"slack {method} failed: {err}{hint}")
    return data


def resolve_users(token: str, ids: set[str]) -> dict[str, str]:
    """Map user/bot ids to display names so the export is readable."""
    names: dict[str, str] = {}
    for uid in sorted(i for i in ids if i):
        try:
            info = call("users.info", token, user=uid)
            u = info.get("user", {})
            names[uid] = u.get("profile", {}).get("display_name") or u.get("real_name") or uid
        except SystemExit:
            names[uid] = uid  # bot ids and lapsed scopes are not fatal
    return names


def main() -> None:
    limit = 300
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    env = load_env()
    token = env.get("SLACK_BOT_TOKEN", "")
    channel = env.get("SLACK_CHANNEL_ID", "")
    if not token or not channel:
        sys.exit("SLACK_BOT_TOKEN / SLACK_CHANNEL_ID missing from .env")

    messages: list[dict] = []
    cursor = None
    while len(messages) < limit:
        params = {"channel": channel, "limit": min(200, limit - len(messages))}
        if cursor:
            params["cursor"] = cursor
        page = call("conversations.history", token, **params)
        messages.extend(page.get("messages", []))
        cursor = (page.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break

    ids = {m.get("user", "") for m in messages}
    names = resolve_users(token, ids)

    clean = []
    for m in messages:
        # Reactions are the approval gate, so carry them through with their users.
        reactions = [
            {"name": r.get("name"), "count": r.get("count", 0)}
            for r in (m.get("reactions") or [])
        ]
        blocks_text = []
        for b in (m.get("blocks") or []):
            t = (b.get("text") or {}).get("text")
            if t:
                blocks_text.append(t)
            for f in (b.get("fields") or []):
                if f.get("text"):
                    blocks_text.append(f["text"])
        clean.append({
            "ts": m.get("ts"),
            "author": names.get(m.get("user", ""), m.get("username") or "bot"),
            "text": m.get("text", ""),
            "blocks_text": blocks_text,
            "reactions": reactions,
            "files": [f.get("name") for f in (m.get("files") or []) if f.get("name")],
            "thread_replies": m.get("reply_count", 0),
        })

    clean.sort(key=lambda m: float(m["ts"] or 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"channel": channel, "messages": clean}, indent=1), encoding="utf-8")
    print(f"exported {len(clean)} messages -> {OUT.relative_to(ROOT)}")
    stamps = [m["ts"] for m in clean if m["ts"]]
    if stamps:
        import datetime as dt
        first = dt.datetime.fromtimestamp(float(stamps[0]))
        last = dt.datetime.fromtimestamp(float(stamps[-1]))
        print(f"range: {first:%Y-%m-%d %H:%M} -> {last:%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    main()
