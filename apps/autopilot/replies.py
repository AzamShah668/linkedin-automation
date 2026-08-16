"""Read the LinkedIn inbox and report threads where THEY spoke last.

WHY THIS EXISTS (D35)
---------------------
On 2026-07-26 a warm insider at Infosys replied two hours after being pitched, gave his phone
number, and asked for the CV. Nobody answered for fifteen days.

Eight consecutive reply-check runs reported "zero replies" during that window. All eight were
telling the truth about the only place they looked: **Gmail**. LinkedIn's inbox was never opened by
anything in this project, so a reply arriving there was not missed — it was *unobservable*.

That is D30 in its purest form. A check that cannot see a channel reports the same "nothing found"
as a check that saw the channel and found nothing, and the two are indistinguishable from the log.

THE DETECTION RULE, AND WHICH WAY IT FAILS
------------------------------------------
LinkedIn's conversation list prefixes the preview with "You:" when the last message in the thread is
ours. No prefix means the other person spoke last.

We therefore treat **"no `You:` prefix" as "they replied"**, and — importantly — we also treat
*"could not tell"* as "they replied". The two failure directions are not symmetric:

  * a false positive costs a human ten seconds of reading a thread that needed no answer
  * a false negative costs what it already cost once: a warm referral going cold over fifteen days

So this module is deliberately noisy. It is a smoke alarm, not a classifier.

It does not classify, reply, or write to any board. It reports.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from apps.autopilot.answers import REPO
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    open_browser,
    sync_playwright,
)

# Windows consoles default to cp1252 and this module prints scraped text (job titles, company and
# recruiter names) full of en-dashes, arrows and accents. Without this, printing raises
# UnicodeEncodeError mid-run - which is how intake.py loaded zero of 36 discovered rows while
# reporting only a quiet exit 1. Enforced by tests/test_console_encoding.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

INBOX_URL = "https://www.linkedin.com/messaging/"

# LinkedIn writes the preview as "You: <text>" when we sent the last message. Some locales and some
# thread types (InMail, sponsored) render it differently, which is precisely why an unrecognised
# shape is escalated rather than ignored.
WE_SPOKE_LAST = re.compile(r"^\s*You:\s", re.IGNORECASE)

# Threads that are not a human replying to outreach. Sponsored InMail is an ad, and LinkedIn shows
# it in the same list as real conversations.
NOISE = re.compile(r"\bsponsored\b|\bpromoted\b", re.IGNORECASE)


@dataclass
class Thread:
    name: str
    preview: str
    they_spoke_last: bool
    sponsored: bool = False
    # Set when the preview could not be parsed at all. Escalated, never dropped — see module docstring.
    undetermined: bool = False

    @property
    def needs_attention(self) -> bool:
        return (self.they_spoke_last or self.undetermined) and not self.sponsored


@dataclass
class InboxReport:
    threads: list[Thread] = field(default_factory=list)
    error: str | None = None

    @property
    def waiting(self) -> list[Thread]:
        return [t for t in self.threads if t.needs_attention]


def classify(name: str, preview: str) -> Thread:
    """Decide who spoke last in one conversation row.

    Pure, so the rule is testable without a browser — the previous reply check was an agent reading
    a runbook, which meant its logic could never be unit-tested at all.
    """
    text = (preview or "").strip()
    sponsored = bool(NOISE.search(text) or NOISE.search(name or ""))
    if not text:
        # An empty preview tells us nothing. Nothing is not evidence of an answered thread.
        return Thread(name=name, preview="", they_spoke_last=False,
                      sponsored=sponsored, undetermined=True)
    if WE_SPOKE_LAST.search(text):
        return Thread(name=name, preview=text, they_spoke_last=False, sponsored=sponsored)
    return Thread(name=name, preview=text, they_spoke_last=True, sponsored=sponsored)


def _rows(page) -> list[tuple[str, str]]:
    """(name, preview) for each conversation in the list."""
    page.goto(INBOX_URL, wait_until="domcontentloaded", timeout=60_000)
    # The list streams in after the shell renders — the same trap that made three Easy Apply jobs
    # report "no next button" while the dialog was merely still loading (D30).
    page.wait_for_selector("li.msg-conversation-listitem, li.msg-conversations-container__convo-item",
                           timeout=25_000)
    page.wait_for_timeout(1_200)

    out: list[tuple[str, str]] = []
    items = page.locator("li.msg-conversation-listitem, li.msg-conversations-container__convo-item")
    for i in range(items.count()):
        row = items.nth(i)
        try:
            name = row.locator(".msg-conversation-listitem__participant-names").first.inner_text()
        except Exception:
            name = ""
        try:
            preview = row.locator(".msg-conversation-card__message-snippet").first.inner_text()
        except Exception:
            preview = ""
        if not (name or preview):
            continue
        out.append((name.strip(), preview.strip()))
    return out


def scan(user_data_dir: Path = DEFAULT_USER_DATA_DIR, headless: bool = False) -> InboxReport:
    report = InboxReport()
    with sync_playwright() as pw:
        context = open_browser(pw, user_data_dir, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)
            for name, preview in _rows(page):
                report.threads.append(classify(name, preview))
        except LinkedInLoggedOut as exc:
            report.error = str(exc)
        finally:
            context.close()
    return report


def notify(waiting: list[Thread]) -> None:
    """Push waiting threads to Slack.

    A scheduled task that only writes to a log file reproduces the very failure this module was
    built to fix: the information exists and nobody sees it. The log is the record; Slack is the
    part a human actually reads.
    """
    if not waiting:
        return
    lines = [f"- {t.name}: {t.preview[:110]}" for t in waiting[:10]]
    body = (
        f"{len(waiting)} LinkedIn thread(s) where they spoke last and we have not replied:\n"
        + "\n".join(lines)
        + "\n\nOpen: https://www.linkedin.com/messaging/"
    )
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", "reply", "--title", f"{len(waiting)} LinkedIn thread(s) waiting on you",
             "--text", body],
            cwd=REPO, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        # Never let a notification failure look like "nothing was waiting".
        print(f"  !! could not post to Slack ({exc}); the {len(waiting)} waiting thread(s) above still need a reply")
        return
    # Say so either way. A notification step that succeeds silently is indistinguishable in the log
    # from one that never ran, which is the exact defect this whole module exists to fix.
    if proc.returncode == 0:
        print(f"  slack: notified about {len(waiting)} waiting thread(s)")
    else:
        print(f"  !! slack REFUSED the alert (exit {proc.returncode}): "
              f"{(proc.stderr or proc.stdout or '').strip()[:200]}")
        print(f"     the {len(waiting)} waiting thread(s) above still need a reply")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report LinkedIn threads where they spoke last.")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--all", action="store_true", help="show every thread, not just the waiting ones")
    ap.add_argument("--notify", action="store_true", help="post waiting threads to Slack")
    args = ap.parse_args(argv)

    report = scan(headless=args.headless)

    if report.error:
        # Never let a failure read as an empty inbox. That equivalence is the whole bug (D35).
        print(f"!! COULD NOT READ THE INBOX: {report.error}")
        print("   This is NOT 'no replies'. Nothing was observed.")
        return 2

    print(f"scanned {len(report.threads)} conversation(s)\n")
    for t in (report.threads if args.all else report.waiting):
        # The mark must track needs_attention, not they_spoke_last. A sponsored InMail also has
        # "them" speaking last, and showing it with the same arrow as a real waiting thread invites
        # exactly the misreading this module exists to prevent.
        if t.sponsored:
            mark = "ad"
        elif t.undetermined:
            mark = "??"
        elif t.they_spoke_last:
            mark = "<<"
        else:
            mark = "  "
        print(f" {mark} {t.name[:28]:<28} {t.preview[:78]}")

    waiting = report.waiting
    print()
    if waiting:
        print(f"** {len(waiting)} thread(s) WAITING ON A REPLY FROM US")
        if args.notify:
            notify(waiting)
    else:
        print("no thread is waiting on us")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
