#!/usr/bin/env python3
"""check_approvals.py — read Slack for job cards the owner approved with a ✅ reaction. No external deps.

The phone-side approval gate: the owner taps ✅ on a job's action card in Slack (laptop can be off), and
this reports which jobs are approved so the flush run can send them. Read-only — it never sends anything
itself; sending is done by Claude via the LinkedIn MCP (see docs/knowledge/12-approved-send-runbook.md).

Approval marks recognised: white_check_mark, heavy_check_mark, +1, rocket
Skip marks (explicitly rejected): x, no_entry, no_entry_sign
Already handled: outbox_tray (the flush adds this after sending, so nothing is ever sent twice)

Needs bot scopes: channels:history (or groups:history for a private channel), reactions:read.

Usage:
  py -3 tools/check_approvals.py            # human-readable list
  py -3 tools/check_approvals.py --json     # machine-readable, for the flush run
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request, urllib.error

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPROVE = {"white_check_mark", "heavy_check_mark", "+1", "rocket"}
REJECT = {"x", "no_entry", "no_entry_sign"}
DONE = {"outbox_tray"}


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=100, help="how many recent messages to scan")
    args = ap.parse_args()

    env = load_env(os.path.join(ROOT, ".env"))
    token, channel = env.get("SLACK_BOT_TOKEN"), env.get("SLACK_CHANNEL_ID")
    if not token or not channel:
        print("ERROR: SLACK_BOT_TOKEN / SLACK_CHANNEL_ID missing in .env"); sys.exit(1)

    url = "https://slack.com/api/conversations.history?" + urllib.parse.urlencode(
        {"channel": channel, "limit": args.limit})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=20))
    except urllib.error.URLError as e:
        print("ERROR reaching Slack:", e); sys.exit(1)

    if not resp.get("ok"):
        err = resp.get("error")
        print("Slack API error:", err)
        if err == "missing_scope":
            print("  -> the bot token needs 'channels:history' (or 'groups:history') and 'reactions:read'.")
            print("     Add them at api.slack.com/apps > your app > OAuth & Permissions, then Reinstall.")
        sys.exit(1)

    approved, rejected = [], []
    for msg in resp.get("messages", []):
        text = msg.get("text", "")
        m = re.search(r"ref:([a-z0-9\-]+)", text)
        if not m:
            continue                      # not a job card
        slug = m.group(1)
        names = {r.get("name") for r in msg.get("reactions", [])}
        if names & DONE:
            continue                      # already sent
        if names & REJECT:
            rejected.append(slug); continue
        if names & APPROVE:
            # first line of the card is the job header, useful for the summary
            header = text.split("\n", 1)[0].strip("* ").replace("🎯", "").strip()
            approved.append({"slug": slug, "ts": msg.get("ts"), "job": header})

    if args.json:
        print(json.dumps({"approved": approved, "rejected": rejected}, ensure_ascii=False, indent=2))
        return

    if not approved and not rejected:
        print("Nothing approved. React to a job card with :white_check_mark: to queue it for sending.")
        return
    for a in approved:
        print(f"APPROVED  {a['slug']:<16} {a['job']}   (ts={a['ts']})")
    for r in rejected:
        print(f"SKIPPED   {r}")
    print(f"\n{len(approved)} approved, {len(rejected)} skipped.")


if __name__ == "__main__":
    main()
