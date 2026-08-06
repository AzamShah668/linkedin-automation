#!/usr/bin/env python3
"""send_queue.py — the throttled send planner (completion-plan step 4). No external deps.

Takes APPROVED outreach items and produces a safe, capped, randomized-jitter send PLAN. It does NOT send:
there is no Gmail token here (Path A — Gmail is reached via MCP), and sending is human-gated + deferred to
the final batch. The runner (Claude via Gmail MCP, or a future scheduler) executes the plan in the printed
order, honoring the offsets. This tool's whole job is to enforce the ban-safe throttle so the final "post
everything" can't accidentally blast.

Caps read from .env: DAILY_OUTREACH_CAP, MIN_SECONDS_BETWEEN_SENDS, OUTREACH_JITTER_SECONDS,
LINKEDIN_CONNECTS_DAILY_CAP.

Input (stdin or --file): JSON array of items:
  {"company","role","channel":"email"|"linkedin","to","subject","status":"approved","fit":90}

Usage:
  py -3 tools/send_queue.py --file queue.json           # dry-run plan (default)
  py -3 tools/send_queue.py --file queue.json --seed 1  # reproducible jitter (testing)
"""
import argparse, json, os, random, sys

# Windows consoles default to cp1252 and crash on ·/≥/– etc. Force UTF-8 so output never dies on a glyph.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULTS = {
    "DAILY_OUTREACH_CAP": 15,
    "MIN_SECONDS_BETWEEN_SENDS": 45,
    "OUTREACH_JITTER_SECONDS": 120,
    "LINKEDIN_CONNECTS_DAILY_CAP": 5,
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


def cap(env, key):
    try:
        return int(env.get(key, DEFAULTS[key]))
    except (ValueError, TypeError):
        return DEFAULTS[key]


def fmt(sec):
    m, s = divmod(int(sec), 60)
    return f"{m:d}m{s:02d}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="JSON file of approved items (default: stdin)")
    ap.add_argument("--seed", type=int, help="seed the jitter RNG (reproducible testing)")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = load_env(os.path.join(root, ".env"))
    daily_cap = cap(env, "DAILY_OUTREACH_CAP")
    min_gap = cap(env, "MIN_SECONDS_BETWEEN_SENDS")
    jitter = cap(env, "OUTREACH_JITTER_SECONDS")
    li_cap = cap(env, "LINKEDIN_CONNECTS_DAILY_CAP")
    if args.seed is not None:
        random.seed(args.seed)

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        print("ERROR: invalid JSON input:", e); sys.exit(1)

    approved = [i for i in items if str(i.get("status", "")).lower() == "approved"]
    skipped = len(items) - len(approved)
    emails = [i for i in approved if i.get("channel") == "email"]
    linkedin = [i for i in approved if i.get("channel") == "linkedin"]

    print(f"Caps: {daily_cap} emails/day · ≥{min_gap}s between sends + 0–{jitter}s jitter · "
          f"{li_cap} LinkedIn connects/day")
    print(f"Approved: {len(approved)} ({len(emails)} email, {len(linkedin)} linkedin) · "
          f"skipped (not approved): {skipped}\n")

    # --- Email plan: capped + throttled schedule ---
    email_today, email_defer = emails[:daily_cap], emails[daily_cap:]
    print(f"EMAIL — Touch 1 (send today, throttled): {len(email_today)}")
    clock = 0
    for n, it in enumerate(email_today, 1):
        if n > 1:
            clock += min_gap + random.randint(0, jitter)
        print(f"  {n:2}. [t+{fmt(clock):>7}] {it.get('company','?')} · {it.get('role','?')} "
              f"→ {it.get('to','?')}  «{it.get('subject','(no subject)')}»")
    if email_defer:
        print(f"  ↳ deferred to tomorrow (over daily cap): {len(email_defer)}")

    # --- LinkedIn plan: capped, manual send in-app ---
    li_today, li_defer = linkedin[:li_cap], linkedin[li_cap:]
    print(f"\nLINKEDIN — Touch 2 (you send manually in-app): {len(li_today)}"
          + (f"  ↳ deferred (over connect cap): {len(li_defer)}" if li_defer else ""))
    for n, it in enumerate(li_today, 1):
        print(f"  {n:2}. {it.get('company','?')} · {it.get('role','?')} → {it.get('to','?')}")

    total_time = clock
    print(f"\nPlan: {len(email_today)} emails over ~{fmt(total_time)}, {len(li_today)} LinkedIn connects. "
          f"DRY-RUN — nothing sent (execute via Gmail MCP in this order; sending stays human-gated).")


if __name__ == "__main__":
    main()
