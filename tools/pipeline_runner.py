#!/usr/bin/env python3
"""Run pipeline steps on demand and stream their output back to the dashboard.

Every button on the Controls page maps to one ACTION here. Actions are grouped by
how much damage a mis-click can do, and the tier is enforced server-side, not just
in the UI:

    safe   read-only or local-only. Runs on one click.
    arm    authorises a send that a robot will later perform on its own. Nothing
           leaves the machine now, but the 30-minute flush task will act on it.
           Needs confirm=True.
    heavy  drives a headless Claude session; slow, costs tokens, writes to
           Notion/Slack. Needs confirm=True.
    send   PUTS A MESSAGE IN FRONT OF A REAL PERSON. Irreversible.
           Needs confirm=True and is labelled as such everywhere.

One run at a time for anything that touches LinkedIn, because the browser profile
cannot be shared (see 05-decisions D13) — a second concurrent run would fail and
misreport it as expired auth.
"""
from __future__ import annotations

import datetime as dt
import itertools
import re
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable or "py"
PS = "powershell"

MAX_LINES = 600          # per run, keeps memory bounded
KEEP_RUNS = 40

_counter = itertools.count(1)
_lock = threading.Lock()
RUNS: dict[str, dict] = {}


class Action:
    def __init__(self, key, label, tier, cmd, blurb, touches_linkedin=False, cwd=None,
                 param=None, hidden=False):
        self.key = key
        self.label = label
        self.tier = tier              # safe | heavy | send
        self.cmd = cmd                # list[str]; a "{param}" element is substituted
        self.blurb = blurb            # what it actually does, in plain words
        self.touches_linkedin = touches_linkedin
        self.cwd = cwd or ROOT
        self.param = param            # name of the required argument, or None
        self.hidden = hidden          # not listed on the Controls page (fired per row)

    def as_json(self) -> dict:
        return {
            "key": self.key, "label": self.label, "tier": self.tier,
            "blurb": self.blurb, "linkedin": self.touches_linkedin,
            "param": self.param, "hidden": self.hidden,
            "cmd": " ".join(self.cmd),
        }

    def resolve(self, param: str | None) -> list[str]:
        if not self.param:
            return list(self.cmd)
        return [param if part == "{param}" else part for part in self.cmd]


# A parameter reaches a subprocess argv, so it is validated against a strict pattern
# rather than trusted. Notion page ids are hex with dashes; nothing else is accepted.
PARAM_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


ACTIONS: dict[str, Action] = {}


def register(*actions: Action) -> None:
    for a in actions:
        ACTIONS[a.key] = a


register(
    # ---------------- safe ----------------
    Action("doctor", "LinkedIn health check", "safe",
           ["cmd", "/c", str(ROOT / "tools" / "linkedin-doctor.cmd")],
           "Counts how many LinkedIn servers are running, reads the session file and lists quarantined "
           "states. Run this FIRST whenever anything LinkedIn-shaped looks broken. Changes nothing.",
           touches_linkedin=False),
    Action("sync-board", "Refresh the board from the last Notion capture", "safe",
           [PY, "tools/sync_board.py"],
           "Re-reads output/dashboard/board-seed.json into the local database. Use after a Claude session "
           "writes a fresh Notion capture. Does not talk to Notion itself."),
    Action("slack-refresh", "Refresh the Slack mirror", "safe",
           [PY, "tools/slack_export.py"],
           "Pulls the latest messages and reactions from the Slack channel so the Slack page is current."),
    Action("invites", "Show the invite pipeline", "safe",
           [PY, "tools/invite_tracker.py", "list"],
           "Lists every connection request and its state: pending, accepted, pitched, expired."),
    Action("invites-due", "Which pitches are due now", "safe",
           [PY, "tools/invite_tracker.py", "due"],
           "Shows accepted invites whose randomised 3-20 hour delay has elapsed, so a pitch is due."),
    Action("expire", "Expire stale invites", "safe",
           [PY, "tools/invite_tracker.py", "expire"],
           "Marks connection requests older than the expiry window as expired so they stop being tracked."),
    Action("notion-queue", "What has not reached Notion yet", "safe",
           [PY, "tools/notion_queue.py"],
           "Lists status changes you made on the dashboard that Notion has not been told about, with the "
           "page ids to update. Local edits win over syncs until pushed, so nothing gets reverted."),
    Action("notion-push", "Push my changes to Notion", "safe",
           [PY, "tools/notion_push.py"],
           "Writes every status you changed here into the Notion pages, refreshes the local capture so "
           "nothing can revert, and clears the queue. Needs NOTION_TOKEN in .env; without it, it still "
           "keeps the local side consistent and tells you what is left."),
    Action("approvals", "Read the Slack approval gate", "safe",
           [PY, "tools/check_approvals.py"],
           "Scans the channel for the cards you ticked with a check mark, and which are already stamped as sent."),

    # ---------------- heavy (headless Claude) ----------------
    Action("discovery", "Find new jobs now", "heavy",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/daily-discovery.ps1"],
           "Runs the discovery robot: searches LinkedIn for fresh DevOps/AI roles, dedupes against the "
           "board, scores fit, writes new rows to Notion and posts a Slack digest. Read-only on LinkedIn "
           "and sends nothing to anyone. Takes several minutes.",
           touches_linkedin=True),
    Action("reply-check", "Check for recruiter replies", "heavy",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/check-replies.ps1"],
           "Reads Gmail (read-only), classifies any recruiter replies, updates Notion and alerts Slack. "
           "Never writes a reply."),

    # ---------------- heavy, per-role (fired from a job row) ----------------
    Action("build-packet", "Build the CV + outreach packet", "heavy",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/build-packet.ps1",
            "-JobId", "{param}"],
           "Researches this company, tailors a CV to the job description, checks it against the job's "
           "keywords, finds the right person to contact, writes both messages, and posts a Slack card for "
           "you to approve. Sends nothing. Takes a few minutes.",
           touches_linkedin=True, param="job_id", hidden=True),

    # ---------------- arm (authorise, do not send) ----------------
    Action("approve", "Approve this one for sending", "arm",
           [PY, "tools/slack_react.py", "--slug", "{param}", "--emoji", "white_check_mark"],
           "Ticks the check mark on this company's Slack card — the same gate as tapping it on your phone. "
           "Nothing goes out this second, but the flush step (and the every-30-minute task) will send the "
           "bare connection request once it sees this.",
           param="slug", hidden=True),
    Action("unapprove", "Take the approval back", "safe",
           [PY, "tools/slack_react.py", "--slug", "{param}", "--emoji", "white_check_mark", "--remove"],
           "Removes the check mark, so the flush step stops treating this as approved. Only works if it has "
           "not already been sent.",
           param="slug", hidden=True),
    Action("skip", "Mark this one as not for me", "safe",
           [PY, "tools/slack_react.py", "--slug", "{param}", "--emoji", "x"],
           "Puts the reject mark on the Slack card so the flush step skips it for good.",
           param="slug", hidden=True),

    # ---------------- send (real outreach) ----------------
    Action("flush-approved", "Send the approved connection requests", "send",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/flush-approved.ps1"],
           "STAGE 1. For every Slack card you ticked, sends a bare LinkedIn connection request (no note) "
           "and records it. Real requests to real people. Cannot be recalled once sent.",
           touches_linkedin=True),
    Action("watch-accepts", "Deliver pitches to anyone who accepted", "send",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/watch-accepts.ps1"],
           "STAGE 2. Checks who accepted, and for those whose delay has elapsed sends the full pitch plus "
           "your CV as a LinkedIn message. This is the step that puts your CV in a stranger's inbox.",
           touches_linkedin=True),

    # The only action that files a real application. Two shapes: one role from its own
    # row, or a capped sweep from the Controls page. Both are 'send' — an application
    # cannot be withdrawn and a company only reads the first one.
    Action("apply", "Apply to this job now", "send",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/auto-apply.ps1",
            "-JobId", "{param}"],
           "Fills and SUBMITS the LinkedIn Easy Apply form for this role, attaching the CV tailored to "
           "this company. Real application, cannot be withdrawn. Needs a built packet first; it refuses "
           "rather than fall back to the generic CV.",
           touches_linkedin=True, param="job_id", hidden=True),
    Action("apply-all", "Apply to everything that is ready", "send",
           [PS, "-ExecutionPolicy", "Bypass", "-File", "tools/auto-apply.ps1", "-All"],
           "Sweeps every row at 'To Apply' that has a built packet and SUBMITS the LinkedIn Easy Apply "
           "form for each, highest fit first, tailored CV per company, with a randomised gap between "
           "them. Capped at 5 per run. Real applications, none of them reversible.",
           touches_linkedin=True),
)


def linkedin_servers() -> list[dict]:
    """Count real MCP servers (python only — each session also spawns 2 uvx wrappers)."""
    ps = (
        "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
        "Where-Object { $_.CommandLine -like '*mcp-server-linkedin*' } | "
        "ForEach-Object { \"$($_.ProcessId)|$($_.CreationDate.ToString('HH:mm:ss'))\" }"
    )
    try:
        out = subprocess.run([PS, "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=25)
    except (OSError, subprocess.SubprocessError):
        return []
    servers = []
    for line in (out.stdout or "").splitlines():
        line = line.strip()
        if "|" in line:
            pid, _, started = line.partition("|")
            servers.append({"pid": pid, "started": started})
    return servers


def preflight() -> dict:
    """What the owner needs to know before firing a LinkedIn action."""
    servers = linkedin_servers()
    cookie = ROOT.parent / ".linkedin-mcp" / "cookies.json"
    home_cookie = Path.home() / ".linkedin-mcp" / "cookies.json"
    path = home_cookie if home_cookie.exists() else cookie
    session_saved = None
    if path.exists():
        session_saved = dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="minutes")

    if len(servers) > 1:
        verdict, detail = "contended", (
            f"{len(servers)} LinkedIn servers are running. They cannot share one browser profile, so a run "
            "now would fail and blame your login. Close the other Claude Code windows, then re-check."
        )
    elif len(servers) == 1:
        verdict, detail = "ok", (
            "One LinkedIn server, no conflict. A run started now gets the browser to itself."
        )
    else:
        verdict, detail = "idle", (
            "No LinkedIn server running. One starts on demand, so this is fine — the first call is just slower."
        )
    return {
        "verdict": verdict, "detail": detail,
        "servers": servers, "session_saved": session_saved,
        "note": "An old session timestamp is normal: that file only changes when you actually log in.",
    }


def _pump(run: dict, proc: subprocess.Popen) -> None:
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip("\n")
        with _lock:
            run["lines"].append(line)
    proc.wait()
    with _lock:
        run["exit"] = proc.returncode
        run["status"] = "done" if proc.returncode == 0 else "failed"
        run["finished"] = dt.datetime.now().isoformat(timespec="seconds")


def busy_linkedin_run() -> str | None:
    with _lock:
        for rid, r in RUNS.items():
            if r["status"] == "running" and r.get("linkedin"):
                return rid
    return None


def start(key: str, confirm: bool = False,
          param: str | None = None) -> tuple[dict | None, str | None]:
    action = ACTIONS.get(key)
    if not action:
        return None, "unknown action"
    if action.tier in ("heavy", "send", "arm") and not confirm:
        return None, f"'{action.label}' needs an explicit confirmation"
    if action.param:
        if not param:
            return None, f"'{action.label}' needs a {action.param}"
        if not PARAM_PATTERN.match(param):
            return None, f"that {action.param} does not look valid"
    elif param:
        return None, f"'{action.label}' takes no argument"
    if action.touches_linkedin:
        busy = busy_linkedin_run()
        if busy:
            return None, "another LinkedIn step is already running — wait for it to finish"

    try:
        proc = subprocess.Popen(
            action.resolve(param), cwd=str(action.cwd),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"could not start: {exc}"

    rid = f"r{next(_counter)}"
    run = {
        "id": rid, "key": key,
        "label": action.label + (f" ({param})" if param else ""),
        "tier": action.tier,
        "linkedin": action.touches_linkedin, "status": "running",
        "started": dt.datetime.now().isoformat(timespec="seconds"),
        "finished": None, "exit": None,
        "lines": deque(maxlen=MAX_LINES), "proc": proc,
    }
    with _lock:
        RUNS[rid] = run
        for old in list(RUNS)[:-KEEP_RUNS]:
            if RUNS[old]["status"] != "running":
                RUNS.pop(old, None)
    threading.Thread(target=_pump, args=(run, proc), daemon=True).start()
    return snapshot(run), None


def stop(rid: str) -> bool:
    with _lock:
        run = RUNS.get(rid)
    if not run or run["status"] != "running":
        return False
    proc: subprocess.Popen = run["proc"]
    proc.terminate()
    with _lock:
        run["status"] = "stopped"
        run["finished"] = dt.datetime.now().isoformat(timespec="seconds")
        run["lines"].append("-- stopped from the dashboard --")
    return True


def snapshot(run: dict) -> dict:
    return {
        "id": run["id"], "key": run["key"], "label": run["label"], "tier": run["tier"],
        "linkedin": run["linkedin"], "status": run["status"],
        "started": run["started"], "finished": run["finished"], "exit": run["exit"],
        "lines": list(run["lines"]),
    }


def get(rid: str) -> dict | None:
    with _lock:
        run = RUNS.get(rid)
        return snapshot(run) if run else None


def recent(limit: int = 12) -> list[dict]:
    with _lock:
        runs = [snapshot(r) for r in RUNS.values()]
    runs.sort(key=lambda r: r["started"], reverse=True)
    for r in runs:
        r["lines"] = r["lines"][-3:]          # just a tail for the list view
    return runs[:limit]


def catalogue() -> list[dict]:
    order = {"safe": 0, "heavy": 1, "arm": 2, "send": 3}
    return sorted((a.as_json() for a in ACTIONS.values() if not a.hidden),
                  key=lambda a: (order.get(a["tier"], 9), a["label"]))
