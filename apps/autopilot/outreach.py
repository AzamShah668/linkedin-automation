"""Find a named human for every application that reached nobody, and queue the invite.

WHY THIS EXISTS (D32, and it is the half of the pipeline that was missing)
--------------------------------------------------------------------------
`coverage.py` counts applications that reached no human. On 2026-08-15 it counted **19 of 21**.
It has always been able to count them and never able to *fix* them, because the next step -- find
one recruiter at that company -- existed only as a runbook an agent read by hand.

So the pipeline could apply twenty-one times in an evening and produce twenty-one queue entries.
That is the mass-automation failure this project was built to reject, reached from the other side:
not by spamming people, but by reaching nobody at all.

This module is the missing link between `coverage.py` (which knows the gap) and `flush-approved`
(which sends the invite once a human ticks it).

    apply-all  ->  coverage  ->  OUTREACH  ->  Slack tick  ->  flush-approved  ->  watch-accepts
                                 ^^^^^^^^
WHAT IT DOES AND DOES NOT DO -- read this before changing anything
------------------------------------------------------------------
It **searches** LinkedIn, read-only, through the same signed-in Playwright profile `replies.py`
already uses. It writes `contact.md` and posts a Slack card carrying `ref:<slug>`.

It **never sends a connection request and never messages anyone.** That is not an oversight and it
is not timidity: scripted people-search plus auto-connect is the single behaviour most reliably
punished with an account restriction, and this project's own north star names it as the red line.
The approved path already exists (D12) and this feeds it.

The split, unchanged from `coverage.py`'s docstring:

  * **code** finds candidates and ranks them -- deterministic, testable, zero send risk
  * **the human** taps the tick in Slack
  * **`flush-approved`** sends one bare invite

WARM FIRST (D8)
---------------
The only reply this project has ever received came from a warm insider: shared home region, found
by hand. Three cold invites were accepted and none replied. So a shared-roots signal outranks a
better job title, and the card says why, because "warm" is the field the owner actually acts on.

THE FAILURE DIRECTION (and it is NOT replies.py's)
--------------------------------------------------
Same asymmetry as `sourcing.py`, for the same reason: recording a real company as having nobody to
reach costs an opportunity permanently, while missing a shell company costs one Slack card.

So a search that **succeeds and finds zero people** is evidence and is recorded as unreachable. A
search that **errors, times out, or renders nothing** is *not evidence of anything* and is
escalated instead. Those two must never collapse into the same branch -- that collapse is D30, the
defect this codebase keeps re-finding, and it is why `_Outcome` carries `searched_ok` separately
from `len(people)`.
"""

from __future__ import annotations

import argparse
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from apps.autopilot import coverage, ledger, sourcing
from apps.autopilot.answers import REPO
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    open_browser,
    sync_playwright,
)

OUTREACH_DIR = REPO / "output" / "outreach"

# Windows consoles default to cp1252 and render every em-dash, star and tick as a replacement
# character -- and this module's whole output is warm-flags and approval prompts. Scheduled runs
# land in a log file the owner reads, so a mangled "WARM" marker defeats the point of the flag.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Deliberately slower than the apply throttle. Search is the endpoint LinkedIn rate-limits most
# aggressively, and unlike an application there is no deadline on finding a recruiter.
MIN_SECONDS_BETWEEN_SEARCHES = 25
MAX_SECONDS_BETWEEN_SEARCHES = 70

# How many profiles to consider per company. The ranking only has to surface one good name; reading
# more rows costs requests against the endpoint most likely to trip a limit.
MAX_CANDIDATES = 12

# ---------------------------------------------------------------------------------------------
# Who is worth contacting, best kind first. Order matters: the first pattern that matches wins.
# ---------------------------------------------------------------------------------------------
ROLE_KINDS: tuple[tuple[str, int, re.Pattern[str]], ...] = (
    ("recruiter", 40, re.compile(
        r"\brecruit(er|ing|ment)\b|\btalent acquisition\b|\bta\s+(lead|partner|specialist)\b"
        r"|\btechnical recruiter\b|\bsourcer\b|\bhiring\b", re.I)),
    ("people/HR", 30, re.compile(
        r"\bhuman resources\b|\bpeople (ops|operations|partner|team)\b|\bhr\b(?!\w)", re.I)),
    ("engineering leader", 24, re.compile(
        r"\bengineering manager\b|\bhead of engineering\b|\bvp,? engineering\b|\bcto\b"
        r"|\bdirector of engineering\b|\bplatform lead\b|\bdevops lead\b"
        # A team/tech lead at the target company is a real route in and was being dropped: the
        # live search returned "Current: Team Lead at Lotus Interworks" and nothing matched it.
        r"|\bteam lead\b|\btech(nical)? lead\b|\blead engineer\b", re.I)),
    ("engineer", 8, re.compile(
        r"\bdevops\b|\bsre\b|\bplatform engineer\b|\bml ?ops\b|\bai engineer\b"
        r"|\bsoftware engineer\b|\binfrastructure\b", re.I)),
)

# Shared roots. From profile/application-answers.json: Srinagar, Jammu & Kashmir, Central
# University of Kashmir. This is the single signal that has ever produced a reply, so it outweighs
# every job title -- see the score arithmetic in `rank`.
WARM_SIGNALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Central University of Kashmir", re.compile(r"central university of kashmir", re.I)),
    ("Kashmir", re.compile(r"\bkashmir\b|\bsrinagar\b", re.I)),
)

# Someone who left is not a route in. LinkedIn headlines say so explicitly and often.
EX_EMPLOYEE = re.compile(r"\bex[- ]|\bformer(ly)?\b|\bprevious(ly)?\b", re.I)

# An "Open to work" jobseeker at the target company is a peer, not a way in.
JOBSEEKER = re.compile(r"open to work|seeking (new )?opportunit|looking for (a )?(new )?role", re.I)

# LinkedIn appends the connection degree to the rendered name ("Faiqa B • 2nd"). It is part of the
# card chrome, not the person, and it would be sent to Slack as if it were their surname.
DEGREE_BADGE = re.compile(r"\s*[•·]\s*(1st|2nd|3rd\+?)\s*$", re.I)

# Words that identify no company. "Lotus Interworks" must match on lotus+interworks; requiring
# "technologies" too would fail every card that abbreviates it.
GENERIC_COMPANY_WORDS = frozenset({
    "inc", "ltd", "llc", "llp", "plc", "pvt", "private", "limited", "corp", "corporation",
    "co", "company", "group", "holdings", "technologies", "technology", "tech", "solutions",
    "systems", "services", "consulting", "software", "labs", "lab", "global", "international",
    "india", "the", "and",
})


def company_tokens(company: str) -> list[str]:
    """The words that actually identify this employer."""
    base = re.sub(r"\(.*?\)", " ", company or "")          # "IndiGo (InterGlobe Aviation Ltd)"
    words = [w for w in re.split(r"[^A-Za-z0-9]+", base.lower()) if w]
    distinctive = [w for w in words if len(w) >= 3 and w not in GENERIC_COMPANY_WORDS]
    # A company called only generic words ("The Tech Company") still needs something to match on.
    return distinctive or [w for w in words if len(w) >= 3] or words


def mentions_company(text: str, company: str) -> bool:
    """Does this text name the target employer?"""
    tokens = company_tokens(company)
    if not tokens:
        return False
    lowered = (text or "").lower()
    if all(token in lowered for token in tokens):
        return True
    # "SkillsCapital" on the card vs "Skills Capital" in the board, and vice versa: a slug is not a
    # comparison key, so compare with every separator removed as well.
    return "".join(tokens) in re.sub(r"[^a-z0-9]+", "", lowered)


CURRENT, PAST, UNKNOWN = "current", "past", "unknown"


def employment(card: Card, company: str) -> str:
    """CURRENT / PAST / UNKNOWN for this person at this company.

    ⚠️ THIS IS THE DIFFERENCE BETWEEN A LEAD AND A STRANGER, AND BETWEEN A LEAD AND SOMEONE WHO
    LEFT. LinkedIn's people search matches anywhere in a profile, so '"Lotus Interworks" recruiter'
    returns people who merely share a skill word, and others whose only link is a job they left.

    Both mistakes were made live on 2026-08-15, in two consecutive runs of this module:
      * run 1 recommended someone with no visible connection to the company at all
      * run 2 recommended her again -- the card did say "Lotus Interworks", on a line beginning
        **"Past:"**, and a substring test cannot tell an employee from an alumnus

    Neither run errored. Both wrote a confident contact.md and posted a Slack card asking the owner
    to connect. That is the house style of bug in this repo: plausible, well-formed, wrong, silent.

    Three states, not a boolean, because the three deserve different treatment: contact the current
    employee, never recommend the past one, and escalate the unknown for human eyes.
    """
    if card.current_company and mentions_company(card.current_company, company):
        return CURRENT
    # An employer named in the headline ("Recruiter @ Acme") is a present-tense claim.
    if card.headline:
        for match in _HEADLINE_AT.finditer(card.headline):
            if mentions_company(match.group("company"), company):
                return CURRENT
    if card.past_company and mentions_company(card.past_company, company):
        return PAST
    # A current role somewhere ELSE, with our company mentioned nowhere structured, is not evidence
    # of anything: fall through to UNKNOWN rather than guessing from loose card text.
    return UNKNOWN


def _slug(company: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (company or "").lower()).strip("-")


@dataclass(frozen=True)
class Candidate:
    name: str
    headline: str
    username: str          # the /in/<username> handle -- what connect_with_person needs
    kind: str = ""
    warm: str = ""
    score: int = 0

    @property
    def profile_url(self) -> str:
        return f"https://www.linkedin.com/in/{self.username}/"


@dataclass
class _Outcome:
    company: str
    role: str
    # searched_ok is NOT `bool(people)`. Keeping them separate is the entire point of this class:
    # "the search ran and the company has nobody" and "the search never ran" are different facts
    # with opposite correct responses, and every version of this bug in this repo started by
    # letting one stand in for the other.
    searched_ok: bool = False
    people: list[Candidate] = field(default_factory=list)
    # Right sort of person, but the card never showed them working at this company. Held back from
    # `people` (we will not ask the owner to connect with a stranger) and held back from the
    # unreachable evidence too (they might well work there; we just cannot prove it from a card).
    unconfirmed: list[Candidate] = field(default_factory=list)
    rows_seen: int = 0
    error: str = ""

    @property
    def best(self) -> Candidate | None:
        return self.people[0] if self.people else None

    @property
    def proven_empty(self) -> bool:
        """Evidence of no findable human -- the only state allowed to block a company (D36).

        Requires the search to have RUN and returned no profiles whatsoever. A page full of people
        none of whom could be confirmed at this company is not evidence about the company; it is a
        limitation of what the card renders, and blocking on it would burn a real employer forever.
        """
        return self.searched_ok and self.rows_seen == 0


def classify(name: str, headline: str, warm_text: str = "") -> Candidate | None:
    """Score one search result. Returns None for someone not worth contacting.

    Judges the PERSON only -- whether they work at the target company is a separate question, asked
    by `affiliated()` against the whole card. Keeping the two apart is what lets an unaffiliated
    result be escalated for review instead of being scored, ranked and posted as a lead.

    Pure: no browser, so the ranking rules are unit-testable. The previous version of this step was
    an agent reading a runbook, which meant its judgement could not be tested at all.
    """
    name = DEGREE_BADGE.sub("", (name or "").strip()).strip()
    text = (headline or "").strip()
    if not name or name.lower() in {"linkedin member", "linkedin user"}:
        # An out-of-network profile renders as "LinkedIn Member" with no handle. Not contactable.
        return None
    if EX_EMPLOYEE.search(text) or JOBSEEKER.search(text):
        return None

    kind, score = "", 0
    for label, weight, pattern in ROLE_KINDS:
        if pattern.search(text):
            kind, score = label, weight
            break
    if not kind:
        return None

    # Shared roots show up on the card's LOCATION line ("Srinagar, Jammu & Kashmir, India"), not in
    # the headline, so warmth is judged against the whole card. Searching only the headline found
    # zero warm contacts on a live search whose top result was in Srinagar.
    warm = ""
    for label, pattern in WARM_SIGNALS:
        if pattern.search(f"{text}\n{warm_text}"):
            # Warm beats every title gap on purpose: the spread across ROLE_KINDS is 32 points
            # (40 down to 8), so +60 guarantees a warm engineer outranks a cold recruiter. That is
            # D8 expressed as arithmetic rather than as a comment nobody reads.
            warm, score = label, score + 60
            break

    return Candidate(name=name, headline=text, username="", kind=kind, warm=warm, score=score)


def rank(candidates: list[Candidate]) -> list[Candidate]:
    """Best route in first. Warm always wins; then seniority of the hiring role; then name order."""
    return sorted(candidates, key=lambda c: (-c.score, c.name.lower()))


# ---------------------------------------------------------------------------------------------
# The browser half
# ---------------------------------------------------------------------------------------------
def search_url(company: str) -> str:
    from urllib.parse import quote

    # Quoting the company name keeps "Energy Exemplar" from matching every profile containing
    # "energy". The role words widen it back out to the people actually worth finding.
    query = f'"{company}" (recruiter OR "talent acquisition" OR hiring OR engineering)'
    return ("https://www.linkedin.com/search/results/people/?keywords="
            + quote(query) + "&origin=GLOBAL_SEARCH_HEADER")


# Harvest by STRUCTURE, never by class name. LinkedIn ships obfuscated rotating classes
# (`LwOMWkdcwjxyNbocfBZZNRTrZvgogtY`), and runbook 31 already paid for that lesson once during
# discovery: a class-name selector returned 7 cards out of 121 and looked like a complete result.
# Anchors to /in/ are part of the URL contract and do not rotate.
#
# It returns RAW LINES and parses nothing. Every judgement lives in `parse_card` below, in Python,
# where it is unit-testable -- the first version parsed inside the browser and shipped an
# ex-employee as the recommended contact because the rule was unreachable from a test.
_HARVEST_JS = """
() => {
  const seen = new Map();
  for (const a of document.querySelectorAll('a[href*="/in/"]')) {
    const m = a.getAttribute('href').match(/\\/in\\/([^/?#]+)/);
    if (!m) continue;
    const username = m[1];
    if (seen.has(username)) continue;
    // Climb to the result card: the nearest list item, else a few levels of parent.
    let card = a.closest('li') || a.parentElement;
    for (let i = 0; i < 3 && card && card.innerText && card.innerText.length < 20; i++) {
      card = card.parentElement;
    }
    const lines = ((card && card.innerText) || '')
      .split('\\n').map(s => s.trim()).filter(Boolean);
    if (!lines.length) continue;
    seen.set(username, { username, lines });
  }
  return [...seen.values()];
}
"""

# Lines that are card chrome rather than anything about the person.
_CHROME = re.compile(
    r"^(?:[•·]\s*)?(?:1st|2nd|3rd\+?)$"                    # connection degree
    r"|^(?:Connect|Follow|Message|Save|View .*profile.*)$"  # buttons
    r"|^·?\s*[\d,.]+[KM]?\s*followers?$"                    # follower count
    r"|mutual connection", re.I)

# LinkedIn's own summary of where someone works, rendered on the result card.
_CURRENT_AT = re.compile(r"^Current:\s*(?P<role>.*?)\s+at\s+(?P<company>.+)$", re.I)
_PAST_AT = re.compile(r"^Past:\s*(?P<role>.*?)\s+at\s+(?P<company>.+)$", re.I)
# "Social Media Manager @ Lotus Interworks" / "Recruiter at Acme" inside the headline itself.
_HEADLINE_AT = re.compile(r"(?:@|\bat\b)\s*(?P<company>[^|·•]+)", re.I)

# A facepile link ("Parvaiz Ahmad - Srinagar, SAYAR UL HASSAN & 4 other mutual connections") is a
# link to a profile, so it survives the /in/ harvest, but it is not a search result and its "name"
# is a sentence about several people.
_FACEPILE = re.compile(r"mutual connection|&\s*\d+\s*other", re.I)


@dataclass(frozen=True)
class Card:
    username: str
    name: str
    headline: str
    current_company: str = ""
    current_role: str = ""
    past_company: str = ""
    junk: bool = False

    @property
    def role_text(self) -> str:
        """What to judge seniority on.

        The headline often describes a DIFFERENT employer than the one we searched for -- LinkedIn
        shows "Team Lead Simplia" as the headline and "Current: Team Lead at Lotus Interworks"
        underneath. Judging the headline alone dropped a genuine current Team Lead at the target
        company while promoting an ex-employee, on the first live run.
        """
        return " | ".join(part for part in (self.current_role, self.headline) if part)


def parse_card(username: str, lines: list[str]) -> Card:
    """Turn one raw result card into structured facts. Pure, so every rule below is testable."""
    clean = [ln.strip() for ln in lines if ln and ln.strip()]
    if not clean:
        return Card(username=username, name="", headline="", junk=True)

    name = DEGREE_BADGE.sub("", clean[0]).strip()
    if _FACEPILE.search(name):
        return Card(username=username, name=name, headline="", junk=True)

    current = current_role = past = ""
    headline = ""
    for line in clean[1:]:
        got_current = _CURRENT_AT.match(line)
        if got_current:
            if not current:
                current = got_current.group("company").strip()
                current_role = got_current.group("role").strip()
            continue
        got_past = _PAST_AT.match(line)
        if got_past:
            past = past or got_past.group("company").strip()
            continue
        if not headline and not _CHROME.search(line):
            headline = line

    return Card(username=username, name=name, headline=headline,
                current_company=current, current_role=current_role, past_company=past)


def _harvest(page, company: str) -> _Outcome:
    out = _Outcome(company=company, role="")
    page.goto(search_url(company), wait_until="domcontentloaded", timeout=60_000)

    # Wait for EITHER real results or LinkedIn's explicit empty state. Reaching a timeout means we
    # learned nothing, which is a different outcome from an empty result set -- see the class
    # docstring. Getting this wrong would let a slow page permanently blacklist a real employer.
    try:
        page.wait_for_selector(
            'a[href*="/in/"], .search-reusables__no-results, [class*="no-results"]',
            timeout=25_000)
        page.wait_for_timeout(1_500)
    except Exception as exc:
        out.error = f"search page never rendered ({type(exc).__name__})"
        return out

    # An auth wall renders instantly and contains no results; treat it as "learned nothing".
    if "/authwall" in page.url or "/checkpoint/" in page.url:
        out.error = f"LinkedIn interrupted the search ({page.url.split('?')[0]})"
        return out

    try:
        rows = page.evaluate(_HARVEST_JS)
    except Exception as exc:
        out.error = f"could not read the results ({type(exc).__name__})"
        return out

    # The search RAN. From here, zero profiles on the page is a real finding about the company.
    out.searched_ok = True
    out.rows_seen = len(rows)

    confirmed: list[Candidate] = []
    unconfirmed: list[Candidate] = []
    for row in rows[:60]:
        if not row.get("username"):
            continue
        card = parse_card(row["username"], row.get("lines", []))
        if card.junk:
            continue

        status = employment(card, company)
        if status == PAST:
            # Someone who left is not a route in, and recommending them looks careless to the owner.
            continue

        scored = classify(card.name, card.role_text, warm_text=" ".join(row.get("lines", [])))
        if scored is None:
            continue
        person = Candidate(
            name=scored.name, headline=card.headline or card.current_role,
            username=card.username, kind=scored.kind, warm=scored.warm, score=scored.score)
        (confirmed if status == CURRENT else unconfirmed).append(person)

    out.people = rank(confirmed)[:MAX_CANDIDATES]
    out.unconfirmed = rank(unconfirmed)[:MAX_CANDIDATES]
    return out


# ---------------------------------------------------------------------------------------------
# What gets written and posted
# ---------------------------------------------------------------------------------------------
def contact_md(company: str, role: str, people: list[Candidate]) -> str:
    best = people[0]
    lines = [
        f"# Contact — {company}",
        "",
        f"Applied for: **{role}**",
        f"Found by: `apps/autopilot/outreach.py` (read-only LinkedIn people search)",
        "",
        "## Approach first",
        "",
        f"- **Name:** {best.name}",
        f"- **Headline:** {best.headline}",
        f"- **Profile:** {best.profile_url}",
        f"- **Why them:** {best.kind}"
        + (f" — **WARM: shared {best.warm}** (D8: lead with this)" if best.warm else ""),
        "",
    ]
    if len(people) > 1:
        lines += ["## Backups", ""]
        lines += [
            f"- {p.name} — {p.kind}{' — WARM: ' + p.warm if p.warm else ''} — {p.profile_url}"
            for p in people[1:6]
        ]
        lines.append("")
    lines += [
        "## Next",
        "",
        "1. Owner taps ✅ on the Slack card.",
        "2. `flush-approved` sends a **bare** connection request (no note — D12/D17).",
        "3. `watch-accepts` delivers the CV and the pitch once they accept.",
        "",
        "_Nothing here has been sent. This file records who to approach, not an approach._",
    ]
    return "\n".join(lines) + "\n"


def write_contact(company: str, role: str, people: list[Candidate]) -> Path:
    folder = OUTREACH_DIR / _slug(company)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "contact.md"
    path.write_text(contact_md(company, role, people), encoding="utf-8")
    return path


def _slack(event: str, title: str, text: str) -> bool:
    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "slack_notify.py"),
             "--event", event, "--title", title, "--text", text],
            cwd=REPO, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"  !! slack failed ({exc})")
        return False
    if proc.returncode != 0:
        print(f"  !! slack REFUSED (exit {proc.returncode}): "
              f"{(proc.stderr or proc.stdout or '').strip()[:160]}")
        return False
    return True


def approval_card(company: str, role: str, best: Candidate) -> tuple[str, str]:
    """(title, text). The text MUST carry `ref:<slug>` -- that is how check_approvals.py finds it."""
    warm = f"  ⭐ WARM: shared {best.warm}" if best.warm else ""
    title = f"Connect with {best.name}? — {company}"
    text = (
        f"*{company}* · {role[:60]}{warm}\n"
        f"{best.name} — {best.headline[:90]}\n"
        f"{best.profile_url}\n"
        f"✅ = send a bare connection request. CV + pitch follow once they accept.\n"
        f"ref:{_slug(company)}"
    )
    return title, text


# ---------------------------------------------------------------------------------------------
def run(limit: int = 5, dry_run: bool = False, headless: bool = False,
        user_data_dir: Path = DEFAULT_USER_DATA_DIR) -> int:
    gaps = coverage.gaps()
    if not gaps:
        print("every application already has a human attached; nothing to do")
        return 0

    todo = gaps[:limit]
    print(f"{len(gaps)} application(s) with nobody attached; working the oldest {len(todo)}\n")
    for g in todo:
        print(f"  {g.submitted_at}  {g.company[:30]:<30} {g.role[:40]}")
    print()

    if dry_run:
        print("DRY RUN — no browser opened, nothing written, nothing posted.")
        return 0

    queued, blocked, escalate = 0, 0, []
    with sync_playwright() as pw:
        context = open_browser(pw, user_data_dir, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)

            for i, gap in enumerate(todo):
                if i:
                    pause = random.randint(MIN_SECONDS_BETWEEN_SEARCHES,
                                           MAX_SECONDS_BETWEEN_SEARCHES)
                    print(f"  ...{pause}s")
                    time.sleep(pause)

                print(f"[{i + 1}/{len(todo)}] {gap.company}")
                outcome = _harvest(page, gap.company)
                outcome.role = gap.role

                if outcome.error:
                    # Learned nothing. Say so in the words that stop it being read as a clean sweep.
                    print(f"  ?? {outcome.error}")
                    print("     This is NOT 'nobody works there'. Nothing was observed.")
                    escalate.append(f"{gap.company}: {outcome.error}")
                    continue

                if outcome.proven_empty:
                    print("  -- search ran, returned nobody at all")
                    sourcing.record_unreachable(
                        gap.company,
                        f"LinkedIn people search returned no profiles at all "
                        f"({ledger.today()})")
                    blocked += 1
                    continue

                if not outcome.people:
                    # People exist; none could be shown to work here. Do NOT record unreachable --
                    # blocking a real employer is the expensive mistake (sourcing.py's asymmetry),
                    # and "the card did not name the company" says nothing about the company.
                    names = ", ".join(p.name for p in outcome.unconfirmed[:3]) or "none scored"
                    print(f"  ?? {outcome.rows_seen} profile(s), none confirmed at {gap.company}")
                    print(f"     closest: {names}")
                    escalate.append(
                        f"{gap.company}: {outcome.rows_seen} profile(s) found, none confirmed "
                        f"as working there (closest: {names})")
                    continue

                best = outcome.best
                assert best is not None
                path = write_contact(gap.company, gap.role, outcome.people)
                flag = f"  ⭐WARM {best.warm}" if best.warm else ""
                print(f"  -> {best.name} ({best.kind}){flag}")
                print(f"     {path.relative_to(REPO)}")

                title, text = approval_card(gap.company, gap.role, best)
                # "draft_ready" is the only EVENTS key that means "a human must look at this".
                # slack_notify.py validates with argparse choices, so a wrong name exits non-zero
                # and the card silently never appears -- which is the whole gap this module closes.
                print("     slack: card posted, waiting on ✅" if _slack("draft_ready", title, text)
                      else "     !! card NOT posted; contact.md is still on disk")
                queued += 1
        except LinkedInLoggedOut as exc:
            print(f"!! COULD NOT SEARCH: {exc}")
            print("   This is NOT 'no recruiters found'. Nothing was observed.")
            return 2
        finally:
            context.close()

    print(f"\n{queued} card(s) awaiting your ✅ · {blocked} company(ies) recorded unreachable")
    if escalate:
        print(f"{len(escalate)} search(es) told us NOTHING (retry these):")
        for line in escalate:
            print(f"  ?? {line}")
    if queued:
        print("Nothing has been sent. `flush-approved` picks these up once you tick them.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Find a named human for applications that reached nobody. Sends nothing.")
    ap.add_argument("--limit", type=int, default=5, help="how many companies to research this run")
    ap.add_argument("--dry-run", action="store_true", help="show the queue, open no browser")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args(argv)
    return run(limit=args.limit, dry_run=args.dry_run, headless=args.headless)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
