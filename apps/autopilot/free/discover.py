"""Find fresh Easy Apply jobs, in Python, with the filter that actually works.

WHY THIS EXISTS
---------------
`daily-discovery.ps1` wakes a headless Claude session to drive the LinkedIn MCP. It has been
DISABLED as a scheduled task since 2026-08-01 (D23: it outran packet-building 94 rows to 4), and
the MCP's `search_jobs(easy_apply=True)` emits the wrong URL parameter anyway.

`intake.py` already scores and loads scraped JSON into the board. The scrape itself was the only
part still done by hand, walked through in [[31-apply-batch-runbook]] §1. This is that walk, as a
program.

⚠️ `f_AL=true`, NEVER `f_EA=true`
---------------------------------
LinkedIn **silently ignores** `f_EA` and returns the unfiltered set. Same query, same minute
(D45):

    f_EA=true    1 of 18 were Easy Apply
    f_AL=true   17 of 17

That one wrong parameter explains every `external-or-none` this project ever logged, and the
LinkedIn MCP still emits the broken one. There is a test asserting the URL this module builds
contains `f_AL` and not `f_EA`.

⚠️ NEVER SELECT THE RESULTS PANE BY CLASS NAME
-----------------------------------------------
LinkedIn ships obfuscated rotating classes (`LwOMWkdcwjxyNbocfBZZNRTrZvgogtY`). The list
virtualises, so a class-name selector once returned **7 cards out of 121** and looked like a
complete result set. Everything here selects structurally, by the `/jobs/view/` link contract.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote

from apps.autopilot.answers import REPO
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    LinkedInLoggedOut,
    check_logged_in,
    open_browser,
    sync_playwright,
)

DEFAULT_KEYWORDS = ("DevOps Engineer", "AI Engineer")
PAGES_PER_KEYWORD = 3

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def search_url(keyword: str, location: str = "India", days: int = 7) -> str:
    """The one URL that matters. `f_AL=true` is the real Easy Apply filter (D45)."""
    return (
        "https://www.linkedin.com/jobs/search/?"
        f"keywords={quote(keyword)}"
        f"&location={quote(location)}"
        f"&f_TPR=r{days * 86400}"          # posted within N days
        "&f_AL=true"                        # ⚠️ NOT f_EA, which LinkedIn ignores
        "&sortBy=DD"                        # newest first
    )


# Harvest by the URL contract, never by class name. Returns raw rows; all judgement is in Python.
# ⚠️ The results list lives in its own scrollable pane, NOT the window. Scrolling the window moves
# nothing and the virtualised list never loads more rows: measured 2026-08-16, window scrolling
# yielded 7 cards while scrolling the pane took it to 14 and climbing.
#
# The pane's class is `LwOMWkdcwjxyNbocfBZZNRTrZvgo` today and will be something else tomorrow, so
# it is found STRUCTURALLY: the scrollable element that actually contains job links.
_SCROLL_PANE_JS = """
() => {
  let moved = 0;
  for (const el of document.querySelectorAll('div, ul, main, section')) {
    if (el.scrollHeight > el.clientHeight + 200 &&
        el.querySelectorAll('a[href*="/jobs/view/"]').length > 2) {
      el.scrollTop = el.scrollTop + 1400;
      moved++;
    }
  }
  window.scrollBy(0, 800);
  return { moved, links: document.querySelectorAll('a[href*="/jobs/view/"]').length };
}
"""

_HARVEST_JS = """
() => {
  const out = new Map();
  for (const a of document.querySelectorAll('a[href*="/jobs/view/"]')) {
    const m = (a.getAttribute('href') || '').match(/\\/jobs\\/view\\/(\\d+)/);
    if (!m) continue;
    const id = m[1];
    if (out.has(id)) continue;
    let card = a.closest('li') || a.parentElement;
    for (let i = 0; i < 3 && card && (card.innerText || '').length < 25; i++) {
      card = card.parentElement;
    }
    const lines = ((card && card.innerText) || '')
      .split('\\n').map(s => s.trim()).filter(Boolean);
    if (!lines.length) continue;
    out.set(id, { id, lines });
  }
  return [...out.values()];
}
"""

# LinkedIn repeats the job title as the link's accessible text, so line 0 is often duplicated.
_EASY_APPLY = re.compile(r"easy apply", re.I)
_PROMOTED = re.compile(r"^(promoted|viewed|actively reviewing|be an early applicant)$", re.I)


def parse_card(job_id: str, lines: list[str]) -> dict | None:
    """One search-result card -> a row `intake.py` understands. Pure, so it is testable."""
    clean = [ln for ln in lines if ln and not _PROMOTED.match(ln)]
    # Collapse the duplicated title LinkedIn emits as the anchor's own text.
    # LinkedIn repeats the title as the anchor's own text, and the two copies are NOT always
    # identical: "Lead Java Developer" is followed by "Lead Java Developer with verification".
    # Exact-match dedup left the second copy in place and it became the company name.
    deduped: list[str] = []
    for line in clean:
        if deduped:
            previous = deduped[-1].lower()
            current = line.lower()
            if current == previous or current.startswith(previous) or previous.startswith(current):
                # Keep the SHORTER form: the longer one carries badge text like "with verification".
                if len(line) < len(deduped[-1]):
                    deduped[-1] = line
                continue
        deduped.append(line)
    if len(deduped) < 2:
        return None
    title, company = deduped[0], deduped[1]
    location = deduped[2] if len(deduped) > 2 else ""
    blob = " | ".join(deduped)
    return {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location,
        # The card says "Easy Apply" explicitly. With f_AL=true every result should be, but the
        # flag is recorded from the page rather than assumed from the query - intake.py drops rows
        # that are not marked, and a silently-ignored filter is exactly the D45 failure.
        "easyApply": bool(_EASY_APPLY.search(blob)),
        "posted": "",
        "alumni": "",
    }


def _scroll_and_harvest(page, pages: int) -> list[dict]:
    rows: dict[str, dict] = {}
    for page_number in range(1, pages + 1):
        # Scroll the PANE until the link count stops growing. A fixed number of scrolls is a
        # guess; "until it stops producing new rows" is the actual finishing condition, and the
        # virtualised list only materialises what has been scrolled past.
        seen_links, stalls = 0, 0
        for _ in range(30):
            state = page.evaluate(_SCROLL_PANE_JS)
            page.wait_for_timeout(650)
            if state["links"] <= seen_links:
                stalls += 1
                if stalls >= 3:          # three quiet passes: the list really has ended
                    break
            else:
                stalls = 0
            seen_links = max(seen_links, state["links"])
        page.wait_for_timeout(1_000)
        for raw in page.evaluate(_HARVEST_JS):
            parsed = parse_card(raw["id"], raw.get("lines", []))
            if parsed:
                rows.setdefault(parsed["id"], parsed)
        print(f"    page {page_number}: {len(rows)} unique so far")

        if page_number >= pages:
            break
        # It is an SPA: the next page swaps in without a reload.
        nxt = page.get_by_role("button", name=re.compile(rf"^page {page_number + 1}$", re.I))
        if not nxt.count():
            print("    no further pages")
            break
        try:
            nxt.first.click()
            page.wait_for_timeout(2_500)
        except Exception:
            print("    could not advance a page")
            break
    return list(rows.values())


def scrape(keywords: tuple[str, ...] = DEFAULT_KEYWORDS, pages: int = PAGES_PER_KEYWORD,
           headless: bool = False, user_data_dir: Path = DEFAULT_USER_DATA_DIR) -> list[dict]:
    found: dict[str, dict] = {}
    with sync_playwright() as pw:
        context = open_browser(pw, user_data_dir, headless=headless)
        try:
            page = context.pages[0] if context.pages else context.new_page()
            check_logged_in(page)
            for i, keyword in enumerate(keywords):
                if i:
                    time.sleep(random.randint(20, 50))
                print(f"  searching: {keyword}")
                try:
                    page.goto(search_url(keyword), wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_selector('a[href*="/jobs/view/"]', timeout=25_000)
                except Exception as exc:
                    # Learned nothing about this keyword. Say so; do not let it read as "no jobs".
                    print(f"    ?? search did not render ({type(exc).__name__}); NOT 'no results'")
                    continue
                for row in _scroll_and_harvest(page, pages):
                    found.setdefault(row["id"], row)
        except LinkedInLoggedOut as exc:
            print(f"!! COULD NOT SEARCH: {exc}")
            print("   This is NOT 'no jobs found'. Nothing was observed.")
            raise
        finally:
            context.close()
    return list(found.values())


def write_scrape(rows: list[dict], path: Path | None = None) -> Path:
    """Write the file `intake.py` reads. Same shape the by-hand scrape produced."""
    path = path or (REPO / f"jobs-{date.today().isoformat()}.json")
    path.write_text(json.dumps({"jobs": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scrape fresh Easy Apply jobs (f_AL=true).")
    ap.add_argument("--keyword", action="append", dest="keywords",
                    help="repeatable; defaults to DevOps Engineer + AI Engineer")
    ap.add_argument("--pages", type=int, default=PAGES_PER_KEYWORD)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="scrape and report, write nothing")
    args = ap.parse_args(argv)

    keywords = tuple(args.keywords or DEFAULT_KEYWORDS)
    print(f"discovering with f_AL=true across {len(keywords)} keyword(s)")
    try:
        rows = scrape(keywords, pages=args.pages, headless=args.headless)
    except LinkedInLoggedOut:
        return 2

    easy = [r for r in rows if r["easyApply"]]
    print(f"\n{len(rows)} unique posting(s); {len(easy)} marked Easy Apply")
    if not rows:
        # Loud, because "the scrape ran and found nothing" and "the scrape did not work" look
        # identical in a log, and one of them is the D45 filter bug coming back.
        print("ZERO POSTINGS SEEN: treat this as a broken scrape, not an empty market.")
        return 1
    for row in easy[:12]:
        print(f"  {row['company'][:26]:<26} {row['title'][:46]}")
    if args.dry_run:
        print("\nDRY RUN. Nothing written.")
        return 0

    path = write_scrape(rows)
    print(f"\nwritten: {path.name}")
    print("next: py -3 -m apps.autopilot.intake --write")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
