#!/usr/bin/env python3
"""slack_notify.py — post Job Hunt Autopilot events to Slack. No external deps (urllib only).

The event layer for Path A (completion-plan step 2): every pipeline action calls this to notify the owner,
so nothing slips even though there's no always-on daemon yet. Reads SLACK_BOT_TOKEN + SLACK_CHANNEL_ID
from .env (never hardcode the token).

Usage:
  py -3 tools/slack_notify.py --event draft_ready --title "Infosys · AI App Engineer" --text "Packet ready to review."
  py -3 tools/slack_notify.py --event digest --title "3 drafts ready" --text "<multi-line body>"
  py -3 tools/slack_notify.py --event new_match --text "..." --dry-run

Events: new_match 🎯 · draft_ready 📝 · sent 📤 · reply 💬 · followup_due ⏰ · digest 📋 · info ℹ️
"""
import argparse, json, os, sys, urllib.request, urllib.error

EVENTS = {
    "new_match":    "🎯 New job match",
    "draft_ready":  "📝 Draft ready to review",
    "sent":         "📤 Outreach sent",
    "reply":        "💬 Reply received",
    "followup_due": "⏰ Follow-up due",
    "digest":       "📋 Digest",
    "info":         "ℹ️ Update",
}


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default="info", choices=list(EVENTS))
    ap.add_argument("--text", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--dry-run", action="store_true", help="print the payload, don't post")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = load_env(os.path.join(root, ".env"))
    token = env.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN")
    channel = env.get("SLACK_CHANNEL_ID") or os.environ.get("SLACK_CHANNEL_ID")
    if not token or not channel:
        print("ERROR: SLACK_BOT_TOKEN / SLACK_CHANNEL_ID missing in .env")
        sys.exit(1)

    header = EVENTS[args.event]
    title = f"*{header}*" + (f" — {args.title}" if args.title else "")
    payload = {"channel": channel, "text": f"{title}\n{args.text}", "mrkdwn": True}

    if args.dry_run:
        print("DRY RUN →", json.dumps(payload, ensure_ascii=False))
        return

    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=utf-8"},
    )
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.URLError as e:
        print("ERROR posting to Slack:", e)
        sys.exit(1)
    if resp.get("ok"):
        print(f"OK: posted '{args.event}' to {channel} (ts={resp.get('ts')})")
    else:
        print("Slack API error:", resp.get("error"))
        sys.exit(1)


if __name__ == "__main__":
    main()
