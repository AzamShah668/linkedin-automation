#!/usr/bin/env python3
"""slack_react.py — add (or remove) a reaction on a Slack job card. No external deps.

This is the send-twice guard. `check_approvals.py` treats a card carrying 📤 (outbox_tray) as already
actioned; without a way to stamp it, an approved job stays approved forever and the every-30-min flush would
send the same person a connection request again and again. Claude has no built-in Slack-reaction tool, so
the runbooks call this.

Needs bot scope: reactions:write.

Usage:
  py -3 tools/slack_react.py --slug infosys                      # stamp 📤 by looking the card up
  py -3 tools/slack_react.py --ts 1785044638.230639              # stamp 📤 by message timestamp
  py -3 tools/slack_react.py --slug infosys --emoji x --remove   # take a reaction off
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://slack.com/api/"


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def call(method, token, payload=None, query=None):
    url = API + method + ("?" + urllib.parse.urlencode(query) if query else "")
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Authorization": f"Bearer {token}"}
    if data:
        headers["Content-Type"] = "application/json; charset=utf-8"
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=20))
    except urllib.error.URLError as exc:
        print("ERROR reaching Slack:", exc)
        sys.exit(1)


def find_ts(token, channel, slug):
    """Locate the newest card carrying `ref:<slug>`."""
    resp = call("conversations.history", token, query={"channel": channel, "limit": 200})
    if not resp.get("ok"):
        print("Slack API error:", resp.get("error"))
        sys.exit(1)
    marker = re.compile(rf"ref:{re.escape(slug)}\b")
    for msg in resp.get("messages", []):
        if marker.search(msg.get("text", "")):
            return msg.get("ts")
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--slug", help="company slug from the card's ref: marker")
    target.add_argument("--ts", help="Slack message timestamp")
    parser.add_argument("--emoji", default="outbox_tray", help="reaction name, no colons (default outbox_tray)")
    parser.add_argument("--remove", action="store_true", help="remove instead of add")
    args = parser.parse_args()

    env = load_env(os.path.join(ROOT, ".env"))
    token, channel = env.get("SLACK_BOT_TOKEN"), env.get("SLACK_CHANNEL_ID")
    if not token or not channel:
        print("ERROR: SLACK_BOT_TOKEN / SLACK_CHANNEL_ID missing in .env")
        sys.exit(1)

    ts = args.ts or find_ts(token, channel, args.slug)
    if not ts:
        print(f"NOT FOUND: no card carrying ref:{args.slug} in the last 200 messages")
        sys.exit(1)

    method = "reactions.remove" if args.remove else "reactions.add"
    resp = call(method, token, payload={"channel": channel, "timestamp": ts, "name": args.emoji})

    if resp.get("ok"):
        print(f"OK: {'removed' if args.remove else 'added'} :{args.emoji}: on {args.slug or ts} (ts={ts})")
        return
    # Already stamped is the desired end state, not a failure — keeps re-runs idempotent.
    if resp.get("error") in ("already_reacted", "no_reaction"):
        print(f"NO CHANGE: :{args.emoji}: already in the desired state on {args.slug or ts}")
        return
    print("Slack API error:", resp.get("error"))
    sys.exit(1)


if __name__ == "__main__":
    main()
