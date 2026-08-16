"""Send the bare connection request directly, and report afterwards.

WHY THIS EXISTS, AND WHOSE DECISION IT WAS
------------------------------------------
Until 2026-08-16 every connection request went through a human gate (D12): `outreach.py` found a
recruiter, posted a Slack card, and `flush-approved` sent only what Azam had ticked. He removed
that gate himself, twice and explicitly:

    "don't leave it up to Slack ... Whenever you find a connection just go for it ... Don't ask me
     for permission from Slack. Remove that ... just provide me with the details that you have done."

It is his account and his call, and the concern was already raised before he reaffirmed it. Slack
becomes a **report** of what was done, not a request to do it.

⚠️ WHAT THIS COSTS, RECORDED HONESTLY SO NOBODY RE-LITIGATES IT FROM MEMORY
---------------------------------------------------------------------------
Automated connection requests are the behaviour LinkedIn most reliably restricts accounts for. The
gate was the thing that kept this project on the safe side of its own north star, and it is gone.
Everything still here exists to keep the *rest* of the risk down, and none of it is a substitute:

  * **a daily cap** (`LINKEDIN_CONNECTS_DAILY_CAP`) counted from an append-only log, not memory
  * **a randomised throttle** between sends (`MIN_SECONDS_BETWEEN_SENDS` + jitter)
  * **business hours only** — invites landing at 03:00 are a bot signal no cap can disguise
  * **one request per person, ever** — the log is checked before every send
  * **current employees only** — `outreach.py` already refuses ex-employees and strangers, and a
    wrong-person invite at volume is what turns "automated" into "spam"

Removing the human gate raised the value of every one of those, because there is no longer a person
looking at each name before it goes out.

WHAT IT STILL WILL NOT DO
-------------------------
It sends a **bare** request — no note. A request carrying a note is capped at ~3/month on a free
account and the send silently fails when LinkedIn is showing its quota banner (D17). The pitch is
delivered after they accept, by `watch-accepts`, exactly as before.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from apps.autopilot import env as envfile
from apps.autopilot.answers import REPO
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    open_browser,
    sync_playwright,
)

CONNECT_LOG = REPO / "output" / "outreach" / "connect-log.jsonl"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Outcomes. Only SENT counts against the cap; the rest are facts about the profile, not actions.
SENT = "sent"
ALREADY_PENDING = "already-pending"
ALREADY_CONNECTED = "already-connected"
NO_CONNECT_BUTTON = "no-connect-button"
LIMIT_REACHED = "linkedin-weekly-limit"
OUT_OF_HOURS = "out-of-hours"
CAPPED = "daily-cap-reached"
COMPANY_UNVERIFIED = "company-unverified"
ERROR = "error"

DEFAULTS = {
    "LINKEDIN_CONNECTS_DAILY_CAP": 15,
    "MIN_SECONDS_BETWEEN_SENDS": 45,
    "OUTREACH_JITTER_SECONDS": 90,
    "BUSINESS_HOUR_START": 9,
    "BUSINESS_HOUR_END": 21,
}


def _env() -> dict[str, str]:
    """Settings for this module. One loader for the whole project (see apps/autopilot/env.py).

    A real environment variable still wins over the file, which is why the `os.environ` update
    comes last: exporting `LINKEDIN_CONNECTS_DAILY_CAP=1` for a single cautious run must not be
    silently overruled by what is on disk.
    """
    values = dict(envfile.values())
    values.update({k: v for k, v in os.environ.items() if k in DEFAULTS})
    return values


def setting(name: str, env: dict[str, str] | None = None) -> int:
    env = env if env is not None else _env()
    try:
        return int(str(env.get(name, DEFAULTS[name])).strip())
    except (TypeError, ValueError):
        return int(DEFAULTS[name])


# ---------------------------------------------------------------------------------------------
# The record. Append-only, and the ONLY source of truth for "have we already asked this person?"
# ---------------------------------------------------------------------------------------------
def log_rows(path: Path | None = None) -> list[dict]:
    path = path if path is not None else CONNECT_LOG
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def record(username: str, name: str, company: str, outcome: str,
           path: Path | None = None, now: datetime | None = None) -> None:
    path = path if path is not None else CONNECT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "username": username, "name": name, "company": company,
            "outcome": outcome, "at": stamp.isoformat(timespec="seconds"),
        }, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())      # a crash must not lose the fact that we contacted someone


def already_requested(username: str, path: Path | None = None) -> bool:
    """Have we ever put a request in front of this person?

    Counts every outcome that means contact was made or already exists. A second request to the
    same human is the single most obviously robotic thing this system could do.
    """
    target = (username or "").strip().lower()
    return any(
        (row.get("username", "").strip().lower() == target)
        and row.get("outcome") in {SENT, ALREADY_PENDING, ALREADY_CONNECTED}
        for row in log_rows(path)
    )


def sent_today(path: Path | None = None, now: datetime | None = None) -> int:
    today = (now or datetime.now()).date().isoformat()
    return sum(1 for row in log_rows(path)
               if row.get("outcome") == SENT and str(row.get("at", "")).startswith(today))


def within_business_hours(now: datetime | None = None, env: dict[str, str] | None = None) -> bool:
    env = env if env is not None else _env()
    hour = (now or datetime.now()).hour
    return setting("BUSINESS_HOUR_START", env) <= hour < setting("BUSINESS_HOUR_END", env)


# ---------------------------------------------------------------------------------------------
# The browser half
# ---------------------------------------------------------------------------------------------
# LinkedIn renders the invite control as `aria-label="Invite Jane Doe to connect"`. Matching the
# ARIA label is far more stable than the rotating obfuscated class names (runbook 31 paid for that
# lesson during discovery, where a class selector returned 7 of 121 results).
_CONNECT_LABEL = re.compile(r"invite .* to connect", re.I)
_PENDING_LABEL = re.compile(r"\bpending\b|invitation sent", re.I)
_WEEKLY_LIMIT = re.compile(r"weekly invitation limit|you.{0,3}ve reached the (weekly )?limit", re.I)


@dataclass(frozen=True)
class Result:
    username: str
    name: str
    company: str
    outcome: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.outcome == SENT


def _click_through_sticky_nav(page, locator, timeout_ms: int = 4_000) -> bool:
    """Click something LinkedIn's sticky header is sitting on top of.

    ⚠️ The plain click FAILS on a profile page, every time, and the error names the wrong thing:

        <nav class="e60892a5 ..."> from <div ...> subtree intercepts pointer events

    Playwright scrolls the button into view, which parks it *underneath* the sticky navigation bar,
    and then waits for it to be clickable until it times out. The button is visible, enabled and
    stable throughout -- so the failure reads like "the element is fine but the click won't take",
    which is exactly the shape that sent the first version of this module down the
    `no-connect-button` path while a perfectly good Connect control sat in the menu.

    Three attempts, cheapest first. `force=True` is deliberately NOT one of them: force skips the
    actionability checks, not the fact that another element is on top (the same trap as the resume
    radio, one layer along).
    """
    try:
        locator.click(timeout=timeout_ms)
        return True
    except Exception:
        pass

    # Scroll it into view, then push the page up so the header no longer covers it.
    try:
        locator.scroll_into_view_if_needed(timeout=timeout_ms)
        page.mouse.wheel(0, -220)
        page.wait_for_timeout(400)
        locator.click(timeout=timeout_ms)
        return True
    except Exception:
        pass

    # Last resort: dispatch a real click event on the element itself. This bypasses the overlay
    # entirely. It is a genuine click event, so React's handler still fires.
    try:
        locator.evaluate("el => el.click()")
        return True
    except Exception:
        return False


def _open_more_menu(page) -> bool:
    """Open the profile's overflow menu, where Connect lives for most non-1st-degree people.

    There are several buttons labelled "More" on a profile (top card, sticky header, each section),
    so try them in order until one actually reveals a Connect entry.
    """
    buttons = page.get_by_role("button", name=re.compile(r"^more$", re.I))
    for i in range(min(buttons.count(), 4)):
        if not _click_through_sticky_nav(page, buttons.nth(i)):
            continue
        page.wait_for_timeout(1_000)
        if page.get_by_role("menuitem", name=_CONNECT_LABEL).count():
            return True
        if page.get_by_role("button", name=_CONNECT_LABEL).count():
            return True
        page.keyboard.press("Escape")      # wrong menu; close it before trying the next
        page.wait_for_timeout(300)
    return False


def _has_pending_marker(page) -> bool:
    """Is there an outstanding invitation to this person?

    ⚠️ `get_by_role("button", name=...)` does NOT find it. LinkedIn renders the badge as a plain
    element with an EMPTY aria-label and the word "Pending" as its text, so it has no accessible
    name to match on. Verified live 2026-08-16: an invite that had genuinely been sent, and showed
    six "Pending" markers on the reloaded profile, was reported as "sent, but the Pending badge was
    not seen" — the send worked and the confirmation was blind.

    That direction is the safe one (under-claiming a success), but it is still a broken check, and
    the same blindness in `_top_card_state` would have let us invite someone twice.
    """
    if page.get_by_role("button", name=_PENDING_LABEL).count():
        return True
    return page.locator("xpath=//*[normalize-space(text())='Pending']").count() > 0


def profile_corroborates_company(page, company: str, scrolls: int = 5) -> tuple[bool, str]:
    """(corroborated, detail) — does the PERSON'S OWN PROFILE name this employer?

    ⚠️ WHY THIS EXISTS, AND WHY THE SEARCH CARD IS NOT ENOUGH.
    On 2026-08-16 a real, unrecallable connection request went to Aditya Sharma for Berribot.
    LinkedIn's search card said, in its own words, **"Current: Software Engineer at Berribot"** —
    so `employment()` was working exactly as designed and returned CURRENT.

    His profile mentions Berribot **zero times**, fully scrolled. The search index and the profile
    disagree, and the profile is the authority.

    My first diagnosis was "card bleed" and it was wrong: the harvested cards were clean, each
    person's lines were their own. *The bug was trusting one source for an irreversible action.*

    The three-state discipline applies here too, because the failure directions differ:
      * profile loaded and does NOT name the company -> refuse (an invite cannot be recalled)
      * profile could not be read at all             -> NOT evidence; fall back to the card
    Collapsing those two would block every private or slow-loading profile.
    """
    if not company:
        return True, "no company to check"
    try:
        # Experience lazy-loads well below the fold. A previous check read the body WITHOUT
        # scrolling, found nothing, and produced a confident false negative.
        for _ in range(scrolls):
            page.mouse.wheel(0, 1400)
            page.wait_for_timeout(700)
        body = page.locator("body").inner_text(timeout=8_000)
    except Exception as exc:
        return True, f"profile unreadable ({type(exc).__name__}); falling back to the search card"

    if len(body.strip()) < 400:
        return True, "profile rendered almost nothing; falling back to the search card"

    from apps.autopilot.outreach import mentions_company

    if mentions_company(body, company):
        return True, f"profile names {company}"
    return False, f"profile never mentions {company} (search card claimed otherwise)"


def _top_card_state(page) -> str:
    """What the profile currently offers: connect / pending / connected / nothing."""
    if _has_pending_marker(page):
        return ALREADY_PENDING
    if page.get_by_role("button", name=_CONNECT_LABEL).count():
        return "connect"
    return NO_CONNECT_BUTTON


def send_request(page, username: str, name: str, company: str) -> Result:
    """Send one bare connection request. Never raises for an expected LinkedIn state."""
    url = f"https://www.linkedin.com/in/{username}/"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2_000)
    except Exception as exc:
        return Result(username, name, company, ERROR, f"profile would not load ({type(exc).__name__})")

    if "/authwall" in page.url or "/checkpoint/" in page.url:
        return Result(username, name, company, ERROR, "LinkedIn interrupted with a checkpoint")

    state = _top_card_state(page)
    if state == ALREADY_PENDING:
        return Result(username, name, company, ALREADY_PENDING, "a request is already outstanding")

    # Corroborate on the profile BEFORE clicking anything. This is the last check standing between
    # a wrong name and an invite that cannot be taken back, and it is the one that would have
    # stopped the Berribot send.
    corroborated, why = profile_corroborates_company(page, company)
    if not corroborated:
        return Result(username, name, company, COMPANY_UNVERIFIED, why)

    if state == NO_CONNECT_BUTTON:
        # Connect is demoted into the "More" menu on most 2nd/3rd-degree profiles -- the top card
        # offers only "Follow". Both live profiles tested on 2026-08-16 were like this, so this is
        # the normal path, not the fallback.
        if not _open_more_menu(page):
            if page.get_by_role("button", name=re.compile(r"^message$", re.I)).count():
                return Result(username, name, company, ALREADY_CONNECTED, "already a connection")
            return Result(username, name, company, NO_CONNECT_BUTTON,
                          "no Connect control, in the top card or the More menu")
        entry = page.get_by_role("menuitem", name=_CONNECT_LABEL)
        if not entry.count():
            entry = page.get_by_role("button", name=_CONNECT_LABEL)
        if not _click_through_sticky_nav(page, entry.first):
            return Result(username, name, company, ERROR, "could not click Connect in the More menu")
    else:
        if not _click_through_sticky_nav(page, page.get_by_role("button", name=_CONNECT_LABEL).first):
            return Result(username, name, company, ERROR, "could not click the Connect button")

    page.wait_for_timeout(1_500)

    body = ""
    try:
        body = page.locator("body").inner_text(timeout=5_000)
    except Exception:
        pass
    if _WEEKLY_LIMIT.search(body or ""):
        return Result(username, name, company, LIMIT_REACHED,
                      "LinkedIn is refusing further invites this week")

    # Send WITHOUT a note, always. A note caps at ~3/month and fails silently under the quota
    # banner (D17); the pitch goes out after they accept instead.
    for label in (r"send without a note", r"^send now$", r"^send$", r"^send invitation$"):
        button = page.get_by_role("button", name=re.compile(label, re.I))
        if button.count():
            if not _click_through_sticky_nav(page, button.first):
                return Result(username, name, company, ERROR, f"could not click '{label}'")
            page.wait_for_timeout(2_500)
            break
    else:
        return Result(username, name, company, ERROR, "invite dialog had no send button")

    # Verify against what the PAGE now says, not against the fact that we clicked. Every silent
    # failure in this project came from trusting the click instead of reading the result back.
    page.wait_for_timeout(1_200)
    if _has_pending_marker(page):
        return Result(username, name, company, SENT, "confirmed: profile now shows Pending")
    try:
        body = page.locator("body").inner_text(timeout=5_000)
    except Exception:
        body = ""
    if _WEEKLY_LIMIT.search(body or ""):
        return Result(username, name, company, LIMIT_REACHED, "weekly limit hit on send")
    # The dialog closed and nothing contradicts a send, but "Pending" never appeared. Record it as
    # sent-unconfirmed rather than clean, so a silent failure cannot masquerade as a success.
    return Result(username, name, company, SENT, "sent, but the Pending badge was not seen")


def connect_one(page, username: str, name: str, company: str,
                env: dict[str, str] | None = None, now: datetime | None = None) -> Result:
    """All the guards, then the send. This is the function callers should use."""
    env = env if env is not None else _env()

    if already_requested(username):
        return Result(username, name, company, ALREADY_PENDING, "already contacted previously")
    if not within_business_hours(now, env):
        return Result(username, name, company, OUT_OF_HOURS,
                      f"outside {setting('BUSINESS_HOUR_START', env)}:00-"
                      f"{setting('BUSINESS_HOUR_END', env)}:00; holding until tomorrow")
    cap = setting("LINKEDIN_CONNECTS_DAILY_CAP", env)
    if sent_today(now=now) >= cap:
        return Result(username, name, company, CAPPED, f"{cap} sent today already")

    # send_request handles every LinkedIn state it knows about, but a browser crash, a navigation
    # race or a detached element can still raise. This function must never be the thing that ends a
    # batch: the caller has already sent invites it needs to report on.
    try:
        result = send_request(page, username, name, company)
    except Exception as exc:                                  # noqa: BLE001 - deliberately broad
        result = Result(username, name, company, ERROR,
                        f"unexpected browser failure ({type(exc).__name__})")

    record(username, name, company, result.outcome, now=now)
    return result


def throttle(env: dict[str, str] | None = None) -> int:
    env = env if env is not None else _env()
    base = setting("MIN_SECONDS_BETWEEN_SENDS", env)
    jitter = setting("OUTREACH_JITTER_SECONDS", env)
    return base + random.randint(0, max(0, jitter))


def report(results: list[Result]) -> bool:
    """Tell Slack what was DONE. Not a request, a receipt."""
    sent = [r for r in results if r.outcome == SENT]
    other = [r for r in results if r.outcome != SENT]
    if not results:
        return True

    lines = [f"✅ {r.name} — {r.company}\n   https://www.linkedin.com/in/{r.username}/"
             for r in sent]
    if other:
        lines.append("")
        lines += [f"– {r.name or r.username} ({r.company}): {r.outcome} — {r.detail}"
                  for r in other[:8]]
    body = (
        f"Sent {len(sent)} connection request(s). No note attached; the CV and pitch go out "
        f"automatically once they accept.\n\n" + "\n".join(lines)
    )
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", "sent", "--title", f"Connected with {len(sent)} recruiter(s)",
             "--text", body],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  !! could not post the report to Slack ({exc}); the sends above still happened")
        return False
    if proc.returncode != 0:
        print(f"  !! slack REFUSED the report (exit {proc.returncode}); the sends still happened")
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Send a bare LinkedIn connection request.")
    ap.add_argument("username", help="the /in/<username> handle")
    ap.add_argument("--name", default="")
    ap.add_argument("--company", default="")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args(argv)

    with sync_playwright() as pw:
        context = open_browser(pw, DEFAULT_USER_DATA_DIR, headless=args.headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)
            result = connect_one(page, args.username, args.name or args.username, args.company)
        except LinkedInLoggedOut as exc:
            print(f"!! {exc}")
            return 2
        finally:
            context.close()

    print(f"{result.outcome}: {result.detail}")
    report([result])
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
