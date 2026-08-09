"""Read-only accept-watch poll: degree + invite badge for each pending invite.

[[13-accept-watch-runbook]] step 2 reads the accept signal with the LinkedIn MCP's
`get_person_profile`. That server is not always present (it had no tools at all on
2026-08-09), which blocks the whole watch on a *read*. This reads the same signal
straight off the profile page with the Playwright profile Phase 0 proved logged in.

Navigates and reads only: no clicks, no connects, no messages. Sending still goes
through the MCP, per the runbook.

    py -3 tools/poll_invites.py [--json]

The signal to act on is the degree flip (2nd/3rd -> 1st). The `Pending` badge is
reported alongside it because it separates two states the degree alone conflates:
"sent, not yet accepted" from "the invite never actually went out" (the D12
`custom_note_limit_reached` silent failure). A row sitting pending for days with no
Pending badge means stage 1 lied.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from apps.autopilot.fill import (  # noqa: E402
    DEFAULT_USER_DATA_DIR,
    check_logged_in,
    open_browser,
    sync_playwright,
)

STATE = REPO / "output" / "outreach" / "pending-invites.json"
TOP_CARD_CHARS = 1500


def degree_of(top: str) -> str:
    match = re.search(r"\b(1st|2nd|3rd)\b\s*degree\s*connection", top, re.I)
    if match:
        return match.group(1).lower()
    match = re.search(r"·\s*(1st|2nd|3rd)\b", top)
    return match.group(1).lower() if match else "unknown"


def poll(page, invite: dict) -> dict:
    user = invite["linkedin_username"]
    page.goto(f"https://www.linkedin.com/in/{user}/", wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3_500)
    top = page.locator("body").inner_text()[:TOP_CARD_CHARS]
    return {
        "slug": invite["slug"],
        "person": invite["person"],
        "linkedin_username": user,
        "degree": degree_of(top),
        "pending_badge": bool(re.search(r"\bPending\b", top)),
        "message_button": bool(re.search(r"\bMessage\b", top)),
        "landed_url": page.url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    pending = [i for i in state.get("invites", []) if i.get("status") == "pending"]
    if not pending:
        print("No pending invites to poll.")
        return 0

    results: list[dict] = []
    with sync_playwright() as pw:
        ctx = open_browser(pw, DEFAULT_USER_DATA_DIR, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            check_logged_in(page)
            if not args.json:
                print("login: OK\n")
            for invite in pending:
                results.append(poll(page, invite))
        finally:
            ctx.close()

    if args.json:
        print(json.dumps({"polled": results}, indent=2))
    else:
        for row in results:
            print(
                f"{row['slug']:16} {row['person']:20} degree={row['degree']:8} "
                f"pending_badge={row['pending_badge']} message_btn={row['message_button']}"
            )
        accepted = [r for r in results if r["degree"] == "1st"]
        print(f"\n{len(accepted)} of {len(results)} accepted (degree flipped to 1st).")
        for row in accepted:
            print(f"  -> py -3 tools/invite_tracker.py mark-accepted --username {row['linkedin_username']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
