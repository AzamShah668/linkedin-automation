"""CLI entry point for the autopilot.

    py -3 -m apps.autopilot.run fieldmap
    py -3 -m apps.autopilot.run fill --url <job-url>
    py -3 -m apps.autopilot.run fill --urls-file <file>
    py -3 -m apps.autopilot.run fill --from-board 5

Phase 0 measures ONE thing: fill time for 5 jobs, target under 3 minutes. Browser launch and
job selection are reported separately and DO NOT count toward the verdict — launch is a
one-time cost that amortises across a whole batch.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

from apps.autopilot import answers
from apps.autopilot.fill import (
    DEFAULT_USER_DATA_DIR,
    FillResult,
    LinkedInLoggedOut,
    check_logged_in,
    fill_job,
    has_easy_apply,
    open_browser,
    sync_playwright,
)

REPO = answers.REPO
BOARD_DB = REPO / "output" / "dashboard" / "board.sqlite3"
TARGET_SECONDS = 180.0

# Never reopened, regardless of what any board says (runbook: "Never resubmit").
BLOCKED_COMPANIES = ("recro",)
BLOCKED_STATUSES = ("applied", "skipped")


def _user_data_dir() -> Path:
    override = os.getenv("PW_USER_DATA_DIR")
    return Path(override) if override else DEFAULT_USER_DATA_DIR


def board_candidates(limit: int = 40) -> list[tuple[str, str, str, int]]:
    """(url, company, job, fit) from the local mirror, best fit first, already-done excluded."""
    if not BOARD_DB.exists():
        raise SystemExit(f"board mirror not found: {BOARD_DB}")

    conn = sqlite3.connect(BOARD_DB)
    rows = conn.execute(
        "SELECT url, company, job, fit, status FROM jobs "
        "WHERE url LIKE '%linkedin.com/jobs/view/%' ORDER BY fit DESC"
    ).fetchall()
    conn.close()

    out = []
    for url, company, job, fit, status in rows:
        if (status or "").strip().lower() in BLOCKED_STATUSES:
            continue
        if any(b in (company or "").lower() for b in BLOCKED_COMPANIES):
            continue
        out.append((url, company or "?", job or "?", fit or 0))
        if len(out) >= limit:
            break
    return out


def select_live_jobs(page, wanted: int) -> list[tuple[str, str, str, int]]:
    """Probe candidates until `wanted` postings actually show an Easy Apply button."""
    chosen: list[tuple[str, str, str, int]] = []
    print(f"\nSelecting {wanted} live Easy Apply jobs from the board mirror...")
    for url, company, job, fit in board_candidates():
        if len(chosen) >= wanted:
            break
        try:
            ok, why = has_easy_apply(page, url)
        except Exception as exc:
            ok, why = False, f"probe-error {type(exc).__name__}"
        mark = "OK  " if ok else "skip"
        print(f"  {mark} [{fit:>3}] {company[:26]:<26} {why:<18} {url}")
        if ok:
            chosen.append((url, company, job, fit))
    return chosen


def report(results: list[FillResult], launch_s: float, select_s: float) -> int:
    print("\n" + "=" * 78)
    print("PHASE 0 RESULT")
    print("=" * 78)

    for r in results:
        resume = r.resume_filename or "(none shown)"
        print(
            f"  {r.seconds:>6.1f}s  {r.status:<22} steps={r.steps}  "
            f"filled={len(r.filled):<3} blank={len(r.unanswered):<3} resume={resume}"
        )
        print(f"          {r.url}")
        if r.note:
            print(f"          note: {r.note}")

    # A job that reached neither Review nor Submit did NOT get filled. Counting it toward the
    # target is how the 2026-08-06 run printed PASS while 3 of 5 jobs did nothing at all
    # (filled=0, blank=0, steps=1, ~4s each). A metric that reports success for a no-op is
    # worse than no metric, because it stops you looking.
    real = [r for r in results if r.status in ("reached-review", "reached-submit")]
    noop = [r for r in results if r not in real]
    real_total = sum(r.seconds for r in real)
    wall_total = sum(r.seconds for r in results)

    print("-" * 78)
    print(f"  browser launch (not counted)  : {launch_s:6.1f}s")
    print(f"  job selection  (not counted)  : {select_s:6.1f}s")
    print(f"  wall time, all {len(results)} attempts  : {wall_total:6.1f}s")
    print(f"  FILL TIME, {len(real)} REAL fills{'':<7}: {real_total:6.1f}s   target {TARGET_SECONDS:.0f}s")
    if noop:
        print(f"  !! {len(noop)} job(s) DID NO WORK, excluded from the verdict:")
        for r in noop:
            print(f"       {r.status:<22} {r.url}")

    if not real:
        verdict = "INVALID - nothing was filled"
    elif len(real) < len(results):
        pace = real_total / len(real)
        verdict = (f"{'PASS' if real_total <= TARGET_SECONDS else 'FAIL'} on {len(real)} jobs "
                   f"- INCOMPLETE SAMPLE ({pace:.1f}s/job, 5 would be ~{pace * 5:.0f}s)")
    else:
        verdict = "PASS" if real_total <= TARGET_SECONDS else "FAIL"
    print(f"  VERDICT                       : {verdict}")

    every_value = {f.value for r in results for f in r.filled}
    print(f"\n  values typed, all distinct    : {len(every_value)} (every one from the answer bank)")

    pre = [p for r in results for p in r.prefilled]
    if pre:
        print("\n  LINKEDIN'S OWN VALUE KEPT (bank differs) - check these:")
        for p in sorted(set(pre)):
            print(f"    {p}")

    drafts = [r for r in results if r.draft_offered]
    if drafts:
        print(f"  ** LinkedIn offered to SAVE a draft on {len(drafts)} job(s) — runbook finding **")

    print("\n" + "-" * 78)
    print("FIELDS I COULD NOT ANSWER (across all jobs) — candidates for the answer bank")
    print("-" * 78)
    tally: dict[str, int] = {}
    for r in results:
        for label in r.unanswered:
            tally[label] = tally.get(label, 0) + 1
    if not tally:
        print("  (none)")
    for label, count in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {count}x  {label}")

    return 0 if verdict == "PASS" else 1


def cmd_fill(args: argparse.Namespace) -> int:
    bank = answers.load_bank()
    user_dir = _user_data_dir()
    print(f"browser profile: {user_dir}")
    print(f"answer bank    : {answers.BANK_PATH}")

    with sync_playwright() as pw:
        t0 = time.perf_counter()
        context = open_browser(pw, user_dir, headless=args.headless)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            check_logged_in(page)
        except LinkedInLoggedOut as exc:
            print(f"\nABORTING WHOLE RUN: {exc}")
            print("Sign in manually in that profile, or point PW_USER_DATA_DIR at the one that is.")
            context.close()
            return 2
        launch_s = time.perf_counter() - t0
        print(f"logged in OK ({launch_s:.1f}s)")

        t1 = time.perf_counter()
        if args.from_board:
            jobs = select_live_jobs(page, args.from_board)
            urls = [j[0] for j in jobs]
        elif args.urls_file:
            urls = [u.strip() for u in Path(args.urls_file).read_text().splitlines() if u.strip()]
        else:
            urls = [args.url]
        select_s = time.perf_counter() - t1

        if not urls:
            print("no jobs to fill")
            context.close()
            return 1

        print(f"\nfilling {len(urls)} job(s):")
        for u in urls:
            print(f"  {u}")
        print()

        results = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            try:
                result = fill_job(page, url, bank)
            except LinkedInLoggedOut as exc:
                print(f"  ABORTING WHOLE RUN: {exc}")
                break
            print(f"  -> {result.status} in {result.seconds:.1f}s")
            results.append(result)

        context.close()
    return report(results, launch_s, select_s)


def cmd_login(_: argparse.Namespace) -> int:
    """Open the profile and wait for the OWNER to sign in by hand.

    This is not an automated login. The runbook forbids a headless/unattended login attempt
    because that is what gets accounts restricted; a human typing their own password into a
    real browser window is the sanctioned path, and it is what the existing working poster
    script does. Nothing is typed for you here.
    """
    user_dir = _user_data_dir()
    print(f"browser profile: {user_dir}")
    with sync_playwright() as pw:
        context = open_browser(pw, user_dir, headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=60_000)
        print("\nA browser window is open. Sign in there yourself — I will not type anything.")
        print("Waiting up to 5 minutes for the feed to load...")
        try:
            page.wait_for_url("**/feed/**", timeout=300_000)
        except Exception:
            print("Did not reach the feed in time. Nothing was changed; rerun when ready.")
            context.close()
            return 1
        print("Signed in. The session is saved in this profile — rerun the fill command.")
        context.close()
    return 0


def cmd_fieldmap(_: argparse.Namespace) -> int:
    print(answers.dump_field_map())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="apps.autopilot.run")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fieldmap", help="print the FIELD_MAP and the value each entry resolves to")
    sub.add_parser("login", help="open the browser so YOU can sign into LinkedIn by hand")

    f = sub.add_parser("fill", help="fill Easy Apply forms, stopping before submit")
    src = f.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="one LinkedIn job URL")
    src.add_argument("--urls-file", help="file with one job URL per line")
    src.add_argument("--from-board", type=int, metavar="N", help="pick N live jobs from the mirror")
    f.add_argument("--headless", action="store_true", help="not recommended; LinkedIn flags it")

    args = parser.parse_args(argv)
    if args.cmd == "fieldmap":
        return cmd_fieldmap(args)
    if args.cmd == "login":
        return cmd_login(args)
    return cmd_fill(args)


if __name__ == "__main__":
    sys.exit(main())
