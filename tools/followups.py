#!/usr/bin/env python3
"""followups.py — the follow-up cadence engine (completion-plan step 3). No external deps.

Decides which applied jobs are due a Day-3 / Day-7 nudge, prints the templated nudge, and (with --notify)
fires a Slack `followup_due` event via tools/slack_notify.py. Follows the ban-safe rule: it only DRAFTS and
alerts — it never sends outreach. A human still approves + sends every nudge.

Why it takes JSON input instead of reading Notion: there is no Notion token in .env (Path A — the Notion
store is reached via MCP, not a standalone credential). The runner (Claude via MCP, or a future scheduler
with a token) queries Notion for Status="Applied" jobs and pipes them in.

Input (stdin or --file): JSON array of jobs, each:
  {"job","company","status","applied_date":"YYYY-MM-DD","reply":false,"followups_sent":0,"url":"..."}

Usage:
  py -3 tools/followups.py --file jobs.json                 # dry-run: list what's due
  echo '<json>' | py -3 tools/followups.py --today 2026-07-29 --notify
"""
import argparse, datetime as dt, json, os, subprocess, sys

# Windows consoles default to cp1252 and crash on em-dashes etc. Force UTF-8 so output never dies on a glyph.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Cadence: after N follow-ups already sent, the next one is due at this many days since Applied Date.
CADENCE = {0: 3, 1: 7}          # 0 sent -> Day 3 ; 1 sent -> Day 7
MAX_FOLLOWUPS = 2               # stop after Day 7
ACTIVE_STATUS = "Applied"      # only chase jobs whose Touch 1 was actually sent
DEAD_STATUSES = {"Interview", "Rejected", "Skipped", "Closed"}

TEMPLATES = {
    3: ("Day 3", "Circling back on my application — still very keen, and happy to send anything useful "
                 "(tailored CV, a quick call). Thanks for considering it."),
    7: ("Day 7", "Last note from me on this one — I'll assume the timing isn't right, but the door's open "
                 "if anything changes. Appreciate your time."),
}


def as_bool(v):
    return str(v).strip().lower() in ("1", "true", "yes", "__yes__", "y")


def due_for(job, today):
    if as_bool(job.get("reply")) or job.get("status") in DEAD_STATUSES:
        return None
    if job.get("status") != ACTIVE_STATUS:
        return None
    applied = job.get("applied_date")
    if not applied:
        return None
    try:
        applied_d = dt.date.fromisoformat(applied[:10])
    except ValueError:
        return None
    sent = int(job.get("followups_sent") or 0)
    if sent >= MAX_FOLLOWUPS or sent not in CADENCE:
        return None
    days = (today - applied_d).days
    threshold = CADENCE[sent]
    if days >= threshold:
        label, body = TEMPLATES[threshold]
        return {"label": label, "day": threshold, "days_since": days, "text": body}
    return None


def notify(job, due):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    title = f"{job.get('company','?')} · {job.get('job','?')} — {due['label']} nudge due"
    text = f"No reply after {due['days_since']}d. Draft nudge:\n> {due['text']}\n{job.get('url','')}".strip()
    subprocess.run([sys.executable, os.path.join(root, "tools", "slack_notify.py"),
                    "--event", "followup_due", "--title", title, "--text", text], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="JSON file of jobs (default: stdin)")
    ap.add_argument("--today", help="override today's date YYYY-MM-DD (for testing)")
    ap.add_argument("--notify", action="store_true", help="fire Slack followup_due for each due nudge")
    args = ap.parse_args()

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    try:
        jobs = json.loads(raw)
    except json.JSONDecodeError as e:
        print("ERROR: invalid JSON input:", e); sys.exit(1)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    due_count = 0
    for job in jobs:
        due = due_for(job, today)
        if not due:
            continue
        due_count += 1
        print(f"DUE  {due['label']:5} | {job.get('company','?')} · {job.get('job','?')} "
              f"| applied {job.get('applied_date')} ({due['days_since']}d ago)")
        print(f"      nudge: {due['text']}")
        if args.notify:
            notify(job, due)
    print(f"\n{due_count} follow-up(s) due{' — Slack notified' if (args.notify and due_count) else ''}. "
          f"(checked {len(jobs)} job(s) as of {today})")
    if not args.notify:
        print("Dry-run (no Slack). Add --notify to alert. Nudges are still human-approved before sending.")


if __name__ == "__main__":
    main()
