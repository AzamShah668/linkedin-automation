"""Read the Gmail inbox for recruiter replies, without Claude's connector.

WHY THIS EXISTS
---------------
`check-replies.ps1` reads Gmail by waking a headless Claude session that uses the Gmail MCP. There
is no MCP on this stack, so this talks to the Gmail API directly, **read-only**.

THE FAILURE DIRECTION IS INHERITED FROM replies.py, DELIBERATELY
-----------------------------------------------------------------
D35: a warm insider replied in two hours and waited fifteen days, because eight consecutive reply
checks reported "zero replies" while only ever looking at one channel. *"Looked everywhere and
found nothing" and "could not look" produce byte-identical output.*

So every failure here is **loud and distinguishable**:

    exit 0   the inbox was read; the count is real
    exit 2   the inbox was NOT read - and it says so in those words

It never returns an empty list to mean "could not check". A caller that treats exit 2 as "no
replies" reintroduces the exact bug this project spent fifteen days paying for.

SCOPE: `gmail.readonly` ONLY
-----------------------------
It cannot send, delete, or modify anything. A token that could send is a token that could send the
wrong thing unattended, and nothing in this project needs that: every outgoing email is still a
human action.

SETUP (once, needs a browser - the only step in the whole free stack that does)
--------------------------------------------------------------------------------
1. Google Cloud console -> new project -> enable the Gmail API.
2. Create an OAuth client ID of type **Desktop app**; download the JSON.
3. Save it as `~/.credentials/gmail-client.json` (gitignored, never in the repo).
4. `py -3 -m apps.autopilot.free.gmail --authorize` and approve in the browser.

Until that is done this module reports `needs-setup` and the pipeline carries on. Gmail is the
second channel; LinkedIn is where the only real reply has ever arrived, and `replies.py` reads
that in plain Python with no credentials at all.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from apps.autopilot.answers import REPO

# Windows consoles default to cp1252 and this module prints scraped text (job titles, company and
# recruiter names) full of en-dashes, arrows and accents. Without this, printing raises
# UnicodeEncodeError mid-run - which is how intake.py loaded zero of 36 discovered rows while
# reporting only a quiet exit 1. Enforced by tests/test_console_encoding.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CREDENTIALS_DIR = Path.home() / ".credentials"
CLIENT_SECRET = CREDENTIALS_DIR / "gmail-client.json"
TOKEN_PATH = CREDENTIALS_DIR / "gmail-token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Mail that is about an application but is not a human replying. Ticking a board row for one of
# these kills the Day-3 nudge for a conversation that never started.
AUTO_ACK = re.compile(
    r"do.?not.?reply|no.?reply@|noreply@|your application (was|has been) (sent|received)"
    r"|thank you for applying|we have received your application|automated (message|response)",
    re.I)

OK, NEEDS_SETUP, UNREADABLE = "ok", "needs-setup", "unreadable"


@dataclass
class Message:
    sender: str
    subject: str
    snippet: str
    received: str = ""

    @property
    def is_auto(self) -> bool:
        return bool(AUTO_ACK.search(f"{self.sender} {self.subject} {self.snippet}"))


@dataclass
class InboxReport:
    status: str = OK
    detail: str = ""
    messages: list[Message] = field(default_factory=list)

    @property
    def human_replies(self) -> list[Message]:
        return [m for m in self.messages if not m.is_auto]

    @property
    def readable(self) -> bool:
        return self.status == OK


def _load_service():
    """(service, InboxReport-or-None). Never raises for a missing dependency or credential."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        return None, InboxReport(
            NEEDS_SETUP,
            "google-api-python-client / google-auth-oauthlib are not installed. "
            "Run: py -3 -m pip install google-api-python-client google-auth-oauthlib")

    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as exc:                      # noqa: BLE001
            return None, InboxReport(NEEDS_SETUP, f"stored token is unusable ({exc})")

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        except Exception as exc:                      # noqa: BLE001
            return None, InboxReport(NEEDS_SETUP, f"could not refresh the token ({exc}); "
                                                  f"re-run with --authorize")
    if not creds or not creds.valid:
        if not CLIENT_SECRET.exists():
            return None, InboxReport(
                NEEDS_SETUP,
                f"no OAuth client at {CLIENT_SECRET}. See this module's docstring for the "
                f"one-time setup; it needs a browser and cannot be done unattended.")
        return None, InboxReport(NEEDS_SETUP, "not authorised yet; run with --authorize")

    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False), None
    except Exception as exc:                          # noqa: BLE001
        return None, InboxReport(UNREADABLE, f"could not open the Gmail API ({exc})")


def authorize() -> int:
    """One-time browser consent. The only step in the free stack that needs a human."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("!! install first: py -3 -m pip install google-api-python-client google-auth-oauthlib")
        return 1
    if not CLIENT_SECRET.exists():
        print(f"!! no OAuth client JSON at {CLIENT_SECRET}")
        print("   Google Cloud console -> enable Gmail API -> OAuth client ID (Desktop app)")
        print("   -> download the JSON and save it at that path.")
        return 1
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"authorised; token stored at {TOKEN_PATH}")
    print("scope is gmail.readonly: this cannot send or delete anything.")
    return 0


def _header(payload: dict, name: str) -> str:
    for header in payload.get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def scan(days: int = 14, limit: int = 40) -> InboxReport:
    """Recent inbox mail. Read-only, and it never conflates 'nothing' with 'could not look'."""
    service, failure = _load_service()
    if failure is not None:
        return failure

    after = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"in:inbox after:{after}"
    try:
        listing = service.users().messages().list(
            userId="me", q=query, maxResults=limit).execute()
        ids = [m["id"] for m in listing.get("messages", [])]
    except Exception as exc:                          # noqa: BLE001
        return InboxReport(UNREADABLE, f"could not list messages ({exc})")

    report = InboxReport(OK, f"read {len(ids)} message(s) from the last {days} days")
    for message_id in ids:
        try:
            raw = service.users().messages().get(
                userId="me", id=message_id, format="metadata",
                metadataHeaders=["From", "Subject", "Date"]).execute()
        except Exception:
            continue                                  # one unreadable message is not an outage
        payload = raw.get("payload", {})
        report.messages.append(Message(
            sender=_header(payload, "From"),
            subject=_header(payload, "Subject"),
            snippet=raw.get("snippet", ""),
            received=_header(payload, "Date"),
        ))
    return report


def notify(messages: list[Message]) -> None:
    if not messages:
        return
    lines = [f"- {m.sender[:44]}: {m.subject[:70]}" for m in messages[:10]]
    body = (f"{len(messages)} non-automated email(s) in the last two weeks:\n"
            + "\n".join(lines))
    try:
        subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", "reply", "--title", f"{len(messages)} email(s) worth a look",
             "--text", body],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  !! Slack notify failed ({exc}); the messages above still stand")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read Gmail for replies. Read-only; sends nothing.")
    ap.add_argument("--authorize", action="store_true", help="one-time browser consent")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--notify", action="store_true")
    args = ap.parse_args(argv)

    if args.authorize:
        return authorize()

    report = scan(days=args.days)

    if report.status == NEEDS_SETUP:
        # NOT an error, and NOT "no replies". Gmail is the second channel; the pipeline continues.
        print(f"gmail: not set up ({report.detail})")
        print("       This is NOT a report of zero replies - Gmail was not checked at all.")
        print("       LinkedIn is still read by apps/autopilot/replies.py, which needs no setup.")
        return 0
    if report.status == UNREADABLE:
        print(f"!! COULD NOT READ GMAIL: {report.detail}")
        print("   This is NOT 'no replies'. Nothing was observed.")
        return 2

    human = report.human_replies
    print(f"{report.detail}; {len(human)} look like a person rather than an auto-ack\n")
    for message in human[:15]:
        print(f"  {message.sender[:40]:<40} {message.subject[:60]}")
    if not human:
        print("  nothing that needs a reply")
    elif args.notify:
        notify(human)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
