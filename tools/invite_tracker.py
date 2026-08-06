#!/usr/bin/env python3
"""invite_tracker.py — the memory behind the two-stage LinkedIn play. No external deps.

Stage 1 sends a bare connection request (unlimited-ish) and records it here as `pending`.
Stage 2 (tools/watch-accepts.ps1 -> docs/knowledge/13-accept-watch-runbook.md) polls LinkedIn, and when a
person has accepted, this schedules the real pitch for a randomised, human-looking moment hours later.

Why bare requests: a request WITH a note is capped at 3/month on a free account, but a message to an
existing 1st-degree connection has no cap at all. So the note is skipped and the full pitch is delivered
after the accept instead. Warm insiders are the exception — the owner sends those 3 notes by hand.

This file only ever tracks state. It never talks to LinkedIn and never sends anything; sending is Claude
via the LinkedIn MCP, following the runbook.

Usage:
  py -3 tools/invite_tracker.py add --slug infosys --person "Recruiter-A" \
      --username recruiter-a-recruiter-a-42670216a --role "AI Application Engineer"
  py -3 tools/invite_tracker.py list [--status pending] [--json]
  py -3 tools/invite_tracker.py mark-accepted --username <u>   # schedules the follow-up
  py -3 tools/invite_tracker.py due [--json]                   # follow-ups ripe to send NOW
  py -3 tools/invite_tracker.py mark-sent --username <u>
  py -3 tools/invite_tracker.py mark-failed --username <u> --reason "..."
  py -3 tools/invite_tracker.py expire                         # age out silent invites
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(ROOT, "output", "outreach", "pending-invites.json")

PENDING = "pending"
ACCEPTED = "accepted"
FOLLOWED_UP = "followed_up"
EXPIRED = "expired"
FAILED = "failed"

DEFAULTS = {
    "ACCEPT_FOLLOWUP_MIN_HOURS": 3,
    "ACCEPT_FOLLOWUP_MAX_HOURS": 20,
    "BUSINESS_HOUR_START": 9,
    "BUSINESS_HOUR_END": 21,
    "INVITE_EXPIRY_DAYS": 14,
}


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def setting(env: dict[str, str], name: str) -> int:
    """Read an int knob from .env, falling back to the documented default."""
    raw = env.get(name, "")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return DEFAULTS[name]


def now() -> datetime:
    return datetime.now().astimezone()


def parse(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


def read_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"invites": []}
    try:
        with open(STATE_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {STATE_PATH} is unreadable ({exc}). Refusing to overwrite it.")
        sys.exit(1)
    if not isinstance(data.get("invites"), list):
        print(f"ERROR: {STATE_PATH} has no 'invites' list. Refusing to overwrite it.")
        sys.exit(1)
    return data


def write_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def find(state: dict, username: str) -> dict | None:
    for invite in state["invites"]:
        if invite.get("linkedin_username") == username:
            return invite
    return None


def replace(state: dict, username: str, updated: dict) -> dict:
    """Return a new state with one invite swapped out — no in-place mutation."""
    return {
        **state,
        "invites": [
            updated if inv.get("linkedin_username") == username else inv
            for inv in state["invites"]
        ],
    }


def shift_into_business_hours(when: datetime, start_hour: int, end_hour: int) -> datetime:
    """Nudge a timestamp into waking hours. Nobody sends a CV pitch at 4am except a robot."""
    if when.hour < start_hour:
        return when.replace(hour=start_hour, minute=random.randint(0, 59), second=0, microsecond=0)
    if when.hour >= end_hour:
        tomorrow = when + timedelta(days=1)
        return tomorrow.replace(hour=start_hour, minute=random.randint(0, 59), second=0, microsecond=0)
    return when.replace(second=0, microsecond=0)


def schedule_followup(env: dict[str, str], accepted_at: datetime) -> datetime:
    """Random 3-20h after the accept, then pulled into business hours."""
    low = setting(env, "ACCEPT_FOLLOWUP_MIN_HOURS")
    high = max(setting(env, "ACCEPT_FOLLOWUP_MAX_HOURS"), low)
    delay_minutes = random.randint(low * 60, high * 60)
    due = accepted_at + timedelta(minutes=delay_minutes)
    return shift_into_business_hours(
        due, setting(env, "BUSINESS_HOUR_START"), setting(env, "BUSINESS_HOUR_END")
    )


def cmd_add(args, env) -> None:
    state = read_state()
    if find(state, args.username):
        print(f"ALREADY TRACKED  {args.username} — not adding twice.")
        return
    invite = {
        "slug": args.slug,
        "person": args.person,
        "linkedin_username": args.username,
        "role": args.role,
        "note_sent": bool(args.note_sent),
        "status": PENDING,
        "requested_at": now().isoformat(),
        "accepted_at": None,
        "followup_due_at": None,
        "followed_up_at": None,
        "last_checked": None,
        "failure_reason": None,
    }
    write_state({**state, "invites": [*state["invites"], invite]})
    print(f"TRACKED  {args.person} ({args.username}) for {args.slug} — status pending.")


def cmd_mark_accepted(args, env) -> None:
    state = read_state()
    invite = find(state, args.username)
    if not invite:
        print(f"NOT TRACKED  {args.username}"); sys.exit(1)
    if invite["status"] in (FOLLOWED_UP, ACCEPTED):
        print(f"NO CHANGE  {args.username} is already {invite['status']}.")
        return
    accepted_at = now()
    due = schedule_followup(env, accepted_at)
    updated = {
        **invite,
        "status": ACCEPTED,
        "accepted_at": accepted_at.isoformat(),
        "followup_due_at": due.isoformat(),
        "last_checked": accepted_at.isoformat(),
    }
    write_state(replace(state, args.username, updated))
    print(f"ACCEPTED  {invite['person']} — follow-up scheduled for {due:%Y-%m-%d %H:%M}.")


def in_business_hours(moment: datetime, start_hour: int, end_hour: int) -> bool:
    return start_hour <= moment.hour < end_hour


def cmd_due(args, env) -> None:
    """Rows ripe to send RIGHT NOW — which means the delay has elapsed AND it is a
    civilised hour.

    The second half used to be missing, and it is not academic. `schedule_followup`
    only shifts a due time into business hours at the moment of ACCEPTANCE; nothing
    re-checked the clock at send time. So a due time that came and went while the
    laptop slept stayed "due" forever, and the next 4-hourly watch — which may well
    fire at 02:00 when Windows floods the missed tasks on wake — would send a cold
    recruiter a CV pitch in the middle of the night. Caught 2026-07-31 22:19 with
    Recruiter-B's 16:28 pitch sitting due and a watch run in flight.

    The runbook states "business hours only" as a hard guardrail; this is where that
    sentence finally becomes code rather than an intention.
    """
    state = read_state()
    moment = now()
    start = setting(env, "BUSINESS_HOUR_START")
    end = setting(env, "BUSINESS_HOUR_END")
    if not in_business_hours(moment, start, end):
        held = [inv for inv in state["invites"] if inv["status"] == ACCEPTED
                and (parse(inv.get("followup_due_at")) or moment) <= moment]
        if args.json:
            print(json.dumps({"due": []}, ensure_ascii=False, indent=2))
        else:
            print(f"Nothing sendable: {moment:%H:%M} is outside business hours "
                  f"({start:02d}:00-{end:02d}:00). {len(held)} ripe row(s) held for morning.")
        return
    ripe = [
        inv for inv in state["invites"]
        if inv["status"] == ACCEPTED
        and (parse(inv.get("followup_due_at")) or moment) <= moment
    ]
    if args.json:
        print(json.dumps({"due": ripe}, ensure_ascii=False, indent=2))
        return
    if not ripe:
        upcoming = [inv for inv in state["invites"] if inv["status"] == ACCEPTED]
        print(f"Nothing due. {len(upcoming)} accepted invite(s) waiting on their delay.")
        return
    for inv in ripe:
        print(f"DUE  {inv['slug']:<14} {inv['person']} ({inv['linkedin_username']})")


def cmd_mark_sent(args, env) -> None:
    state = read_state()
    invite = find(state, args.username)
    if not invite:
        print(f"NOT TRACKED  {args.username}"); sys.exit(1)
    updated = {**invite, "status": FOLLOWED_UP, "followed_up_at": now().isoformat()}
    write_state(replace(state, args.username, updated))
    print(f"SENT  follow-up logged for {invite['person']} ({invite['slug']}).")


def cmd_mark_failed(args, env) -> None:
    state = read_state()
    invite = find(state, args.username)
    if not invite:
        print(f"NOT TRACKED  {args.username}"); sys.exit(1)
    updated = {**invite, "status": FAILED, "failure_reason": args.reason,
               "last_checked": now().isoformat()}
    write_state(replace(state, args.username, updated))
    print(f"FAILED  {invite['person']} — {args.reason}")


def cmd_expire(args, env) -> None:
    state = read_state()
    limit = setting(env, "INVITE_EXPIRY_DAYS")
    cutoff = now() - timedelta(days=limit)
    aged, invites = [], []
    for inv in state["invites"]:
        requested = parse(inv.get("requested_at"))
        if inv["status"] == PENDING and requested and requested < cutoff:
            aged.append(inv)
            invites.append({**inv, "status": EXPIRED, "last_checked": now().isoformat()})
        else:
            invites.append(inv)
    write_state({**state, "invites": invites})
    if not aged:
        print(f"Nothing older than {limit} days still pending.")
        return
    for inv in aged:
        print(f"EXPIRED  {inv['slug']:<14} {inv['person']} — no accept in {limit} days, try email.")


def cmd_list(args, env) -> None:
    state = read_state()
    rows = [i for i in state["invites"] if not args.status or i["status"] == args.status]
    if args.json:
        print(json.dumps({"invites": rows}, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("No invites tracked yet.")
        return
    for inv in rows:
        when = inv.get("followup_due_at") or inv.get("requested_at") or ""
        print(f"{inv['status']:<12} {inv['slug']:<14} {inv['person']:<22} {when[:16]}")
    print(f"\n{len(rows)} invite(s).")


COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "mark-accepted": cmd_mark_accepted,
    "due": cmd_due,
    "mark-sent": cmd_mark_sent,
    "mark-failed": cmd_mark_failed,
    "expire": cmd_expire,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    subs = parser.add_subparsers(dest="command", required=True)

    add = subs.add_parser("add", help="record a connection request that just went out")
    add.add_argument("--slug", required=True)
    add.add_argument("--person", required=True)
    add.add_argument("--username", required=True)
    add.add_argument("--role", default="")
    add.add_argument("--note-sent", action="store_true", help="a personalised note rode along")

    listing = subs.add_parser("list", help="show tracked invites")
    listing.add_argument("--status", choices=[PENDING, ACCEPTED, FOLLOWED_UP, EXPIRED, FAILED])
    listing.add_argument("--json", action="store_true")

    accepted = subs.add_parser("mark-accepted", help="they accepted; schedule the pitch")
    accepted.add_argument("--username", required=True)

    due = subs.add_parser("due", help="follow-ups whose delay has elapsed")
    due.add_argument("--json", action="store_true")

    sent = subs.add_parser("mark-sent", help="the follow-up pitch went out")
    sent.add_argument("--username", required=True)

    failed = subs.add_parser("mark-failed", help="something went wrong; stop retrying")
    failed.add_argument("--username", required=True)
    failed.add_argument("--reason", required=True)

    subs.add_parser("expire", help="age out invites nobody accepted")

    args = parser.parse_args()
    env = load_env(os.path.join(ROOT, ".env"))
    COMMANDS[args.command](args, env)


if __name__ == "__main__":
    main()
