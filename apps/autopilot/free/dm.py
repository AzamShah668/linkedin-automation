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

# Marker inside a Delivery.detail meaning the message was read back out of the thread, not merely
# clicked at. "20 confirmed, 0 unconfirmed" is the only shape of report this project trusts.
CONFIRMED = "confirmed"

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
    """Record the delivery so the next run does not repeat it.

    ⚠️ This failing is worse than the send failing. The message has already reached a real person;
    an unrecorded delivery means they get the identical pitch again on the next run, which is the
    single most embarrassing thing this pipeline could do to a warm lead. So every path out of here
    is loud - the quiet one used to be a non-zero exit code, which is also the likeliest.
    """
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "invite_tracker.py"),
             "mark-sent", "--username", username],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"     !! could not mark sent ({exc}) - it WILL be re-sent next run")
        return False
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "no output").strip().splitlines()
        print(f"     !! tracker refused to mark {username} sent (exit {proc.returncode})")
        print(f"        {detail[-1][:200] if detail else ''}")
        print("        THE PITCH WAS DELIVERED. Mark it by hand or it will be sent twice:")
        print(f'        py -3 tools/invite_tracker.py mark-sent --username "{username}"')
        return False
    return True


_MESSAGE_EXACT = re.compile(r"^\s*message\s*$", re.I)
_RECIPIENT = re.compile(r"recipient=([^&]+)")


def message_control(page):
    """(locator, recipient_urn, reason). The profile owner's own Message control.

    ⚠️ Two traps, both already paid for elsewhere in this repo.

    1. **It is an `<a>`, not a `<button>`.** `get_by_role("button", name=/message/)` matches nothing
       and returns a confident "not connected" for someone who accepted yesterday - the same shape
       as the Pending badge with no accessible name. A negative from the wrong selector is
       indistinguishable from a true negative.
    2. **The sidebar has one `Message <Name>` link per suggested profile.** Loosening the match to
       find trap 1 walks straight into addressing a composer to a stranger, which is D50 with a
       different door. So: the name must be exactly "Message" (the owner's control carries no name;
       everyone else's does), and every such control must agree on the `recipient` URN. They
       disagree - we refuse rather than guess.
    """
    controls = [c for c in (page.get_by_role("link", name=_MESSAGE_EXACT),
                            page.get_by_role("button", name=_MESSAGE_EXACT))
                if c.count()]
    if not controls:
        return None, "", "no Message control on the profile"

    first = controls[0].first
    urns = set()
    for group in controls:
        for i in range(min(group.count(), 6)):
            href = group.nth(i).get_attribute("href") or ""
            match = _RECIPIENT.search(href)
            if match:
                urns.add(match.group(1))
    if len(urns) > 1:
        return None, "", (f"{len(urns)} different recipients behind controls named 'Message'; "
                          f"refusing to guess which one is this profile")
    return first, (urns.pop() if urns else ""), ""


def send_dm(page, username: str, text: str, expected_person: str = "") -> Delivery:
    """Open the profile, click Message, type the pitch, send, then read it back."""
    try:
        page.goto(f"https://www.linkedin.com/in/{username}/",
                  wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector("main", timeout=20_000)
        page.wait_for_timeout(3_000)          # the top card lazy-loads after main appears
    except Exception as exc:
        return Delivery("", "", username, ERROR, f"profile would not load ({type(exc).__name__})")

    button, urn, why = message_control(page)
    if button is None:
        # Sending is impossible. Whether that is "they disconnected" or "we looked wrong" is the
        # distinction that cost this project fifteen days, so the reason travels with the outcome.
        return Delivery("", "", username, NOT_CONNECTED, f"{why}; not connected")
    if not connect._click_through_sticky_nav(page, button):
        return Delivery("", "", username, ERROR, "could not open the message composer")
    page.wait_for_timeout(2_200)

    # Post-condition on WHO, before a single character is typed - but only where it adds evidence.
    # When the control carried an href, `urn` already binds the recipient to this profile and every
    # control named "Message" agreed on it; that is stronger than reading a heading. The fallback
    # is for a bare <button> with no href, where nothing else identifies the recipient.
    #
    # Deliberately NOT matching a bare `aside`: the right-hand rail is an <aside> too, and reading
    # "People also viewed" instead of the composer would refuse every legitimate send while looking
    # like a safety feature.
    if expected_person and not urn:
        wanted = expected_person.strip().split()[0].lower()
        shown = ""
        for selector in (".msg-overlay-conversation-bubble", ".msg-form", "[role=dialog]"):
            region = page.locator(selector)
            try:
                if region.count():
                    shown = region.first.inner_text(timeout=6_000).lower()
                    break
            except Exception:
                continue
        if shown and wanted not in shown:
            return Delivery("", "", username, ERROR,
                            f"composer does not name {expected_person!r}; refusing to type")

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
        return Delivery("", "", username, SENT, f"{CONFIRMED}: the message is in the thread")
    # Still SENT, deliberately. The Send click completed, so the message almost certainly went; if
    # this were treated as a failure the invite would stay due and the next run would send it
    # AGAIN. Between an unconfirmed delivery and a duplicate one, the duplicate is worse and it is
    # the one a recruiter would notice. The count is reported separately so it is never silent.
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

    sent = unconfirmed = unrecorded = 0
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
                result = send_dm(page, username, text, expected_person=person)
                print(f"     {result.outcome}: {result.detail}")
                if result.ok:
                    sent += 1
                    if CONFIRMED not in result.detail:
                        unconfirmed += 1
                    if mark_sent(username):
                        print("     tracker updated; it will not be sent twice")
                    else:
                        unrecorded += 1
        except LinkedInLoggedOut as exc:
            print(f"!! COULD NOT SEND: {exc}")
            print("   This is NOT 'nothing was due'. Nothing was attempted.")
            return 2
        finally:
            context.close()

    print(f"\n{sent} pitch(es) delivered ({sent - unconfirmed} confirmed in-thread, "
          f"{unconfirmed} unconfirmed)")
    if unrecorded:
        print(f"!! {unrecorded} delivered but NOT recorded in the tracker. Mark them by hand "
              f"before the next run or the same person is pitched twice.")
        return 2
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
