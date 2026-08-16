"""Ask LinkedIn who has accepted, instead of asking our own notes.

WHY THIS EXISTS
---------------
`invite_tracker.py` records what we last *observed*. `watch-accepts.ps1` is what does the
observing, and it is a headless Claude session — so it is subject to D24 (process depth), D25 (the
usage-limit wall) and lock contention. On 2026-08-16 its 18:26 run stood down because check-replies
held the pipeline lock, leaving the tracker's answer eighteen hours old.

Asked "has anyone accepted?", the tracker answers **"0 accepted"** either way. That is D35 exactly:
*"we looked and nobody has"* and *"we have not looked since last night"* produce identical output,
and the difference is a warm lead going cold.

So this module reads the **profiles themselves**, in plain Python over the existing Playwright
profile — no agent, no quota, nothing that can silently decline to run.

WHAT IT DOES NOT DO
-------------------
It does not send the pitch. It marks accepted invites in the tracker, which schedules the follow-up
for a randomised, human-looking moment inside business hours; `watch-accepts` still delivers it.
Detecting an accept and immediately firing a message is the robotic pattern the two-stage design
(D12/D17) exists to avoid — the delay is the point, not an accident.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot.answers import REPO
from apps.autopilot.connect import _has_pending_marker
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    open_browser,
    sync_playwright,
)

INVITES_PATH = REPO / "output" / "outreach" / "pending-invites.json"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ACCEPTED = "accepted"
STILL_PENDING = "still-pending"
UNKNOWN = "unknown"

# A 1st-degree connection gets a real Message button in the top card. Non-connections get
# "Message" only in some sidebar contexts, so this is checked ONLY after Pending is ruled out.
_MESSAGE = re.compile(r"^message$", re.I)
_DEGREE_FIRST = re.compile(r"\b1st\b")


@dataclass(frozen=True)
class Check:
    slug: str
    person: str
    username: str
    state: str
    detail: str = ""


def pending_invites(path: Path | None = None) -> list[dict]:
    path = path if path is not None else INVITES_PATH
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"!! could not read {path.name} ({exc})")
        return []
    return [i for i in data.get("invites", []) if i.get("status") == "pending"]


def classify_profile(page) -> tuple[str, str]:
    """(state, detail) for a profile we have an outstanding invite to."""
    # Pending first: it is the unambiguous "not yet accepted" signal, and it has no accessible
    # name, so it must be read as text (see connect.py).
    if _has_pending_marker(page):
        return STILL_PENDING, "invitation still outstanding"

    if page.get_by_role("button", name=_MESSAGE).count():
        return ACCEPTED, "no Pending badge and a Message button is present"

    try:
        body = page.locator("body").inner_text(timeout=5_000)
    except Exception:
        body = ""
    if _DEGREE_FIRST.search(body or ""):
        return ACCEPTED, "profile shows a 1st-degree connection"

    # Withdrawn, declined, or the page did not render the top card. Never guess an accept.
    return UNKNOWN, "no Pending badge and no sign of a connection"


def mark_accepted(username: str) -> bool:
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "invite_tracker.py"),
             "mark-accepted", "--username", username],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"     !! could not mark accepted ({exc})")
        return False
    if proc.returncode != 0:
        print(f"     !! invite_tracker refused (exit {proc.returncode}): "
              f"{(proc.stderr or proc.stdout or '').strip()[:150]}")
        return False
    return True


def notify(accepted: list[Check]) -> None:
    if not accepted:
        return
    lines = [f"• {c.person} — {c.slug}\n  https://www.linkedin.com/in/{c.username}/"
             for c in accepted]
    body = (f"{len(accepted)} person(s) accepted your connection request:\n"
            + "\n".join(lines)
            + "\n\nThe CV and pitch are scheduled automatically, at a randomised time "
              "inside business hours.")
    try:
        subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", "reply", "--title", f"{len(accepted)} invite(s) accepted",
             "--text", body],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  !! Slack notify failed ({exc}); the accepts above still stand")


def run(headless: bool = False, mark: bool = True,
        user_data_dir: Path = DEFAULT_USER_DATA_DIR) -> int:
    invites = pending_invites()
    if not invites:
        print("no pending invites to check")
        return 0

    print(f"checking {len(invites)} pending invite(s) against LinkedIn\n")
    results: list[Check] = []

    with sync_playwright() as pw:
        context = open_browser(pw, user_data_dir, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)

            for i, invite in enumerate(invites):
                username = invite.get("linkedin_username") or invite.get("username") or ""
                person = invite.get("person", "?")
                slug = invite.get("slug", "?")
                if not username:
                    results.append(Check(slug, person, "", UNKNOWN, "no username recorded"))
                    continue

                if i:
                    time.sleep(random.randint(4, 11))

                try:
                    page.goto(f"https://www.linkedin.com/in/{username}/",
                              wait_until="domcontentloaded", timeout=45_000)
                    page.wait_for_timeout(2_500)
                    state, detail = classify_profile(page)
                except Exception as exc:
                    state, detail = UNKNOWN, f"profile would not load ({type(exc).__name__})"

                mark_str = {ACCEPTED: "ACCEPTED", STILL_PENDING: "  pending",
                            UNKNOWN: "  ??     "}[state]
                print(f" {mark_str}  {person[:26]:<26} {slug[:24]:<24} {detail}")
                results.append(Check(slug, person, username, state, detail))

                if state == ACCEPTED and mark:
                    if mark_accepted(username):
                        print("            -> pitch scheduled; watch-accepts will deliver it")
        except LinkedInLoggedOut as exc:
            print(f"!! COULD NOT CHECK: {exc}")
            print("   This is NOT 'nobody accepted'. Nothing was observed.")
            return 2
        finally:
            context.close()

    accepted = [c for c in results if c.state == ACCEPTED]
    unknown = [c for c in results if c.state == UNKNOWN]
    print(f"\n{len(accepted)} accepted · "
          f"{len([c for c in results if c.state == STILL_PENDING])} still pending · "
          f"{len(unknown)} could not be read")
    if unknown:
        print("  ?? these told us NOTHING - not the same as 'still pending':")
        for c in unknown:
            print(f"     {c.person[:28]:<28} {c.detail}")
    if accepted and mark:
        notify(accepted)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ask LinkedIn who accepted. Sends no messages.")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--no-mark", action="store_true",
                    help="report only; do not schedule any pitch")
    args = ap.parse_args(argv)
    return run(headless=args.headless, mark=not args.no_mark)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
