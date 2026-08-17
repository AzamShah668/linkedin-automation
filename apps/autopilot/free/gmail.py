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
    py -3 -m apps.autopilot.free.gmail --authorize

It looks for a **Desktop app** OAuth client already on this machine (`~/.credentials`, then
`~/Downloads`) and lists what it found; pick one with `--client <path>`. Only if there is none do
you need the Google Cloud console: new project -> enable the Gmail API -> OAuth client ID of type
Desktop app -> download the JSON.

⚠️ **A stored token is not proof of a readable inbox.** An OAuth client borrowed from another
project authorises fine and then 403s every call, because the Gmail API is enabled *per Google
Cloud project*. So `--authorize` finishes with a real `getProfile` call, and if that fails it
**deletes the token** and prints the exact enable URL. A credential that looks installed and reads
nothing is this project's oldest failure shape (D35) wearing a new hat.

Until setup is done this module reports `needs-setup` and the pipeline carries on. Gmail is the
second channel; LinkedIn is where the only real reply has ever arrived, and `replies.py` reads
that in plain Python with no credentials at all.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
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

# Where a downloaded OAuth client tends to sit. Ordered: an already-installed one wins over a
# stray download, so re-running --authorize does not silently switch Google Cloud projects.
CLIENT_SEARCH_DIRS = (CREDENTIALS_DIR, Path.home() / "Downloads")
CLIENT_GLOBS = ("gmail-client*.json", "client_secret*.json")

# Mail that is about an application but is not a human replying. Ticking a board row for one of
# these kills the Day-3 nudge for a conversation that never started.
AUTO_ACK = re.compile(
    r"do.?not.?reply|no.?reply@|noreply@|your application (was|has been) (sent|received)"
    r"|thank you for applying|we have received your application|automated (message|response)",
    re.I)

# Senders whose mail is a notification ABOUT something this pipeline already watches elsewhere.
# LinkedIn's own mail is the clearest case: `replies.py` reads that inbox directly and `accepts.py`
# polls the invites, so alerting on the email copy is double-counting a signal we already have.
NOTIFIER = re.compile(
    r"(invitations|notifications-noreply|messaging-digest-noreply|jobs-listings|jobalerts-noreply|"
    r"job-alerts-noreply|inmail-hit-reply)@linkedin\.com"
    r"|noreply-accounts@google\.com|no-reply@accounts\.google\.com",
    re.I)

OK, NEEDS_SETUP, UNREADABLE = "ok", "needs-setup", "unreadable"


@dataclass
class Message:
    sender: str
    subject: str
    snippet: str
    received: str = ""
    list_unsubscribe: str = ""

    @property
    def is_auto(self) -> bool:
        return bool(AUTO_ACK.search(f"{self.sender} {self.subject} {self.snippet}"))

    @property
    def is_bulk(self) -> bool:
        """Newsletter, marketing blast, or a notification we already read at the source.

        `List-Unsubscribe` is the honest signal here, not a keyword list: it is the header bulk
        senders are required to set and that a person typing a reply never has. Keyword matching on
        subjects would eventually swallow a recruiter who happens to write "unsubscribe" or shout.
        """
        return bool(self.list_unsubscribe.strip()) or bool(NOTIFIER.search(self.sender))


@dataclass
class InboxReport:
    status: str = OK
    detail: str = ""
    messages: list[Message] = field(default_factory=list)

    @property
    def human_replies(self) -> list[Message]:
        """Mail that could plausibly be a person writing to Azam.

        ⚠️ Narrowing this is the dangerous direction. [[D35]] cost fifteen days because a real
        reply was in a channel nobody read, and a filter that hides one is the same outcome by
        another route. So `bulk` is never discarded - it is counted and printed, just not alerted
        on. Nothing becomes invisible; some things become quiet.
        """
        return [m for m in self.messages if not m.is_auto and not m.is_bulk]

    @property
    def bulk(self) -> list[Message]:
        return [m for m in self.messages if not m.is_auto and m.is_bulk]

    @property
    def readable(self) -> bool:
        return self.status == OK


def _load_service():
    """(service, InboxReport-or-None). Never raises for a missing dependency or credential."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
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
            spare = len(discover_clients())
            hint = (f"{spare} Desktop client(s) are already on this machine - run with "
                    f"--list-clients") if spare else "run with --authorize for the one-time setup"
            return None, InboxReport(
                NEEDS_SETUP,
                f"no OAuth client at {CLIENT_SECRET}; {hint}. Needs a browser once, so it "
                f"cannot be done unattended.")
        return None, InboxReport(NEEDS_SETUP, "not authorised yet; run with --authorize")

    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False), None
    except Exception as exc:                          # noqa: BLE001
        return None, InboxReport(UNREADABLE, f"could not open the Gmail API ({exc})")


# =================================================================================================
# Finding an OAuth client that already exists, and proving it actually reads mail
# =================================================================================================

def is_desktop_client(path: Path) -> bool:
    """A Desktop-app client, the only kind `run_local_server` can complete.

    A web-app client has a `web` key instead of `installed`; it authorises against registered
    redirect URIs and fails on a random loopback port with an error that blames the port.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(payload, dict) and "installed" in payload


def discover_clients(dirs: tuple[Path, ...] | None = None) -> list[Path]:
    """Desktop OAuth clients already on this machine, best candidate first.

    Deliberately does not pick one. These belong to different Google Cloud projects and only the
    owner knows which has the Gmail API enabled and is tied to the right account; choosing for him
    would authorise the wrong mailbox and look like success.
    """
    found: list[Path] = []
    for folder in dirs if dirs is not None else CLIENT_SEARCH_DIRS:
        if not folder.is_dir():
            continue
        matches: list[Path] = []
        for pattern in CLIENT_GLOBS:
            matches.extend(folder.glob(pattern))
        for path in sorted(set(matches), key=lambda p: p.stat().st_mtime, reverse=True):
            if is_desktop_client(path) and path not in found:
                found.append(path)
    return found


def project_number(path: Path) -> str:
    """The Google Cloud project number, taken from the client id's prefix.

    Needed only to build the 'enable the Gmail API' URL, which is useless without it.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    client_id = str(payload.get("installed", {}).get("client_id", ""))
    prefix = client_id.split("-", 1)[0]
    return prefix if prefix.isdigit() else ""


def enable_url(project: str) -> str:
    base = "https://console.developers.google.com/apis/api/gmail.googleapis.com/overview"
    return f"{base}?project={project}" if project else base


_API_DISABLED = re.compile(
    r"SERVICE_DISABLED|accessNotConfigured|has not been used in project|is disabled", re.I)


def is_api_disabled(error: str) -> bool:
    """True when the failure is 'Gmail API off in this project', not 'wrong credential'.

    Worth telling apart: one is a two-click fix on a page whose URL we can print, the other means
    starting over. Both arrive as a generic 403.
    """
    return bool(_API_DISABLED.search(error))


def install_client(source: Path) -> Path:
    """Copy a chosen client into place. Copied, not referenced: a file in Downloads is one tidy-up
    away from breaking every unattended run."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, CLIENT_SECRET)
    return CLIENT_SECRET


def verify_access(creds) -> tuple[bool, str]:
    """One real API call. Returns (readable, detail).

    The whole point: OAuth consent proves the human said yes, and nothing about whether the Gmail
    API is switched on in the project behind the client. Skipping this is how a channel ends up
    'configured' and permanently silent.
    """
    try:
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        profile = service.users().getProfile(userId="me").execute()
    except Exception as exc:                              # noqa: BLE001
        return False, str(exc)
    return True, str(profile.get("emailAddress", "unknown address"))


def authorize(client: Path | None = None) -> int:
    """One-time browser consent. The only step in the free stack that needs a human."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("!! install first: py -3 -m pip install google-api-python-client google-auth-oauthlib")
        return 1

    if client is not None:
        if not client.is_file():
            print(f"!! no such file: {client}")
            return 1
        if not is_desktop_client(client):
            print(f"!! {client.name} is not a Desktop-app OAuth client (no 'installed' key).")
            print("   A web-app client cannot complete a loopback consent flow.")
            return 1
        install_client(client)
        print(f"using {client.name}")

    if not CLIENT_SECRET.exists():
        candidates = [p for p in discover_clients() if p != CLIENT_SECRET]
        print(f"!! no OAuth client JSON at {CLIENT_SECRET}")
        if candidates:
            print(f"\n   {len(candidates)} Desktop client(s) already on this machine:")
            for path in candidates[:8]:
                print(f"     {path}")
            print("\n   Pick the one whose Google Cloud project has the Gmail API enabled:")
            print(f'     py -3 -m apps.autopilot.free.gmail --authorize --client "{candidates[0]}"')
        else:
            print("   Google Cloud console -> enable Gmail API -> OAuth client ID (Desktop app)")
            print("   -> download the JSON and save it at that path.")
        return 1

    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0)

    readable, detail = verify_access(creds)
    if not readable:
        # Do NOT keep the token. A stored-but-dead credential turns every later run into a 403
        # that reads like an outage, and the fix is on a page nobody would think to visit.
        TOKEN_PATH.unlink(missing_ok=True)
        print("\n!! consent succeeded but the inbox could NOT be read; token discarded.")
        if is_api_disabled(detail):
            project = project_number(CLIENT_SECRET)
            print("   The Gmail API is not enabled in this client's Google Cloud project.")
            print(f"   Enable it here, wait a minute, then re-run --authorize:\n     {enable_url(project)}")
        else:
            print(f"   {detail[:400]}")
        return 1

    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nauthorised and VERIFIED by a real read: {detail}")
    print(f"token stored at {TOKEN_PATH}")
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
                metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe"]).execute()
        except Exception:
            continue                                  # one unreadable message is not an outage
        payload = raw.get("payload", {})
        report.messages.append(Message(
            sender=_header(payload, "From"),
            subject=_header(payload, "Subject"),
            snippet=raw.get("snippet", ""),
            received=_header(payload, "Date"),
            list_unsubscribe=_header(payload, "List-Unsubscribe"),
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
    ap.add_argument("--client", type=Path, default=None,
                    help="path to a Desktop-app OAuth client JSON to install and use")
    ap.add_argument("--list-clients", action="store_true",
                    help="show Desktop OAuth clients already on this machine")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--notify", action="store_true")
    args = ap.parse_args(argv)

    if args.list_clients:
        found = discover_clients()
        if not found:
            print("no Desktop-app OAuth client JSON found in ~/.credentials or ~/Downloads")
            return 1
        print(f"{len(found)} Desktop OAuth client(s):")
        for path in found:
            print(f"  {path}   (project {project_number(path) or 'unknown'})")
        return 0

    if args.authorize:
        return authorize(args.client)

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

    human, bulk = report.human_replies, report.bulk
    autos = len(report.messages) - len(human) - len(bulk)
    print(f"{report.detail}: {len(human)} worth a look, {len(bulk)} bulk, {autos} auto-ack\n")
    for message in human[:15]:
        print(f"  {message.sender[:40]:<40} {message.subject[:60]}")
    if not human:
        print("  nothing that needs a reply")
    elif args.notify:
        notify(human)

    # Printed, never hidden. A filter that silently swallowed a recruiter would recreate D35 from
    # the other end, so the quiet pile stays visible to anyone reading the log.
    if bulk:
        print(f"\n  ...and {len(bulk)} newsletter/notification(s), not alerted on:")
        for message in bulk[:8]:
            print(f"    {message.sender[:38]:<38} {message.subject[:52]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
