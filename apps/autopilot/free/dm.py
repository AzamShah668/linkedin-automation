"""Deliver the 2b pitch to someone who accepted, without an agent.

WHY THIS EXISTS
---------------
`watch-accepts.ps1` does this today by waking a headless Claude session that reads
13-accept-watch-runbook.md and drives the LinkedIn MCP. That is the step most exposed to D24
(three process layers) and D25 (the usage wall), and it is the last thing in the chain — so when
it fails, everything upstream was wasted.

`accepts.py` already detects acceptances in plain Python. This sends the message.

THE TEXT IS NEVER GENERATED HERE
---------------------------------
It comes verbatim from the `## 2b` block of `output/outreach/<slug>/touch-2-linkedin.md`, written
by `pitch.py` or by hand. The runbook's rule is "never invent the pitch", and it holds harder here
than under Claude: this module has a live LLM one import away and must not reach for it.

⚠️ A missing file is a **refusal**, never an improvisation. An invite with no pitch is D49 — the
person accepted and would hear silence — and the answer to that is to write the pitch beforehand,
not to make one up at send time.

⚠️ And a WITHHELD pitch must stay withheld. The Berribot file was deliberately renamed to
`touch-2-linkedin.WITHHELD.md` so no sender could find it (D50). Anything that starts globbing for
`touch-2*` re-arms a message that a human decided not to send.
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

from apps.autopilot import connect
from apps.autopilot.answers import REPO
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    open_browser,
    sync_playwright,
)

OUTREACH_DIR = REPO / "output" / "outreach"
INVITES_PATH = OUTREACH_DIR / "pending-invites.json"

SENT = "sent"
NO_PITCH = "no-pitch-file"
NOT_CONNECTED = "not-connected"
ERROR = "error"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass(frozen=True)
class Delivery:
    slug: str
    person: str
    username: str
    outcome: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.outcome == SENT


def extract_2b(markdown: str) -> str:
    """The 2b block, unquoted. Empty string when there isn't one.

    The file is a document for humans as well as a source for this sender, so the message lives in
    a blockquote under a `## 2b` heading. Everything else in the file - the status header, the
    research note, the checks - must never reach the recipient.
    """
    if not markdown:
        return ""
    match = re.search(r"^##\s*2b\b.*?$", markdown, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    rest = markdown[match.end():]
    # Stop at the next heading or a horizontal rule; the trailing notes are not part of the pitch.
    rest = re.split(r"^(?:##\s|---\s*$)", rest, maxsplit=1, flags=re.MULTILINE)[0]
    lines = []
    for raw in rest.splitlines():
        stripped = raw.strip()
        if stripped.startswith(">"):
            lines.append(stripped[1:].lstrip() if stripped != ">" else "")
        elif lines and not stripped:
            lines.append("")
    return "\n".join(lines).strip()


def pitch_for(slug: str, outreach_dir: Path | None = None) -> tuple[str, str]:
    """(text, why-empty). Only ever reads the exact filename; never globs."""
    outreach_dir = outreach_dir if outreach_dir is not None else OUTREACH_DIR
    path = outreach_dir / slug / "touch-2-linkedin.md"
    if not path.exists():
        # Deliberately does NOT look for touch-2-*.md. A withheld pitch was renamed precisely so
        # that no sender would find it (D50); a glob here would undo a human's decision.
        return "", f"no {path.name} for {slug} (a withheld pitch stays withheld)"
    try:
        body = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return "", f"could not read {path.name}: {exc}"
    text = extract_2b(body)
    if not text:
        return "", f"{path.name} has no '## 2b' block to send"
    return text, ""


def due_invites() -> list[dict]:
    """Accepted invites whose randomised delay has elapsed, per invite_tracker."""
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "invite_tracker.py"), "due", "--json"],
            cwd=REPO, capture_output=True, text=True, timeout=60)
        payload = json.loads(proc.stdout or "[]")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"!! could not read the invite tracker ({exc}); assuming nothing is due")
        return []
    if isinstance(payload, dict):
        payload = payload.get("due") or payload.get("invites") or []
    return [i for i in payload if isinstance(i, dict)]


def mark_sent(username: str) -> bool:
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "invite_tracker.py"),
             "mark-sent", "--username", username],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"     !! could not mark sent ({exc}) - it WILL be re-sent next run")
        return False
    return proc.returncode == 0


def send_dm(page, username: str, text: str) -> Delivery:
    """Open the profile, click Message, type the pitch, send, then read it back."""
    try:
        page.goto(f"https://www.linkedin.com/in/{username}/",
                  wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2_500)
    except Exception as exc:
        return Delivery("", "", username, ERROR, f"profile would not load ({type(exc).__name__})")

    button = page.get_by_role("button", name=re.compile(r"^message", re.I))
    if not button.count():
        # No Message control means not a 1st-degree connection. Sending is impossible, and this is
        # information, not a failure: the accept detection was wrong or they disconnected.
        return Delivery("", "", username, NOT_CONNECTED, "no Message button; not connected")
    if not connect._click_through_sticky_nav(page, button.first):
        return Delivery("", "", username, ERROR, "could not open the message composer")
    page.wait_for_timeout(1_800)

    box = page.get_by_role("textbox").filter(visible=True)
    if not box.count():
        return Delivery("", "", username, ERROR, "composer opened but no message box appeared")
    try:
        box.first.click()
        # type(), not fill(): the composer is a contenteditable that listens for real key events,
        # and fill() leaves the Send button disabled with the text visibly present. Same family as
        # the location typeahead (D46) - displayed is not accepted.
        box.first.type(text, delay=8)
        page.wait_for_timeout(900)
    except Exception as exc:
        return Delivery("", "", username, ERROR, f"could not type the pitch ({type(exc).__name__})")

    send = page.get_by_role("button", name=re.compile(r"^send$", re.I))
    if not send.count():
        return Delivery("", "", username, ERROR, "no Send button (is the composer empty?)")
    if not connect._click_through_sticky_nav(page, send.first):
        return Delivery("", "", username, ERROR, "could not click Send")
    page.wait_for_timeout(2_500)

    # Read it back. A click that did not raise is not a message that arrived - the whole history of
    # this project says to check the artifact, not the action.
    probe = text.strip().split("\n")[0][:40]
    try:
        body = page.locator("body").inner_text(timeout=8_000)
    except Exception:
        body = ""
    if probe and probe in body:
        return Delivery("", "", username, SENT, "confirmed: the message is in the thread")
    return Delivery("", "", username, SENT, "sent, but could not read it back in the thread")


def run(limit: int = 3, headless: bool = False, dry_run: bool = False,
        user_data_dir: Path = DEFAULT_USER_DATA_DIR) -> int:
    invites = due_invites()
    if not invites:
        print("no accepted invite is due a pitch")
        return 0

    todo = invites[:limit]
    print(f"{len(invites)} pitch(es) due; sending {len(todo)}\n")

    # Resolve every pitch BEFORE opening a browser. A missing file should cost nothing.
    prepared: list[tuple[dict, str]] = []
    for invite in todo:
        slug = invite.get("slug", "")
        text, why = pitch_for(slug)
        if not text:
            print(f"  SKIP {slug}: {why}")
            continue
        prepared.append((invite, text))

    if not prepared:
        print("\nnothing sendable. Write the pitch first: py -3 -m apps.autopilot.pitch --backfill")
        return 0
    if dry_run:
        for invite, text in prepared:
            print(f"\n--- would send to {invite.get('person')} ({invite.get('slug')}) ---")
            print("\n".join(f"    {line}" for line in text.splitlines()[:8]))
        print("\nDRY RUN. No browser opened, nothing sent.")
        return 0

    sent = 0
    with sync_playwright() as pw:
        context = open_browser(pw, user_data_dir, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)
            for i, (invite, text) in enumerate(prepared):
                if i:
                    time.sleep(random.randint(40, 110))
                person = invite.get("person", "?")
                username = invite.get("linkedin_username", "")
                print(f"[{i + 1}/{len(prepared)}] {person} ({invite.get('slug')})")
                result = send_dm(page, username, text)
                print(f"     {result.outcome}: {result.detail}")
                if result.ok:
                    sent += 1
                    if mark_sent(username):
                        print("     tracker updated; it will not be sent twice")
        except LinkedInLoggedOut as exc:
            print(f"!! COULD NOT SEND: {exc}")
            print("   This is NOT 'nothing was due'. Nothing was attempted.")
            return 2
        finally:
            context.close()

    print(f"\n{sent} pitch(es) delivered")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deliver the 2b pitch to accepted invites.")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="show what would be sent, send nothing")
    args = ap.parse_args(argv)
    return run(limit=args.limit, headless=args.headless, dry_run=args.dry_run)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
