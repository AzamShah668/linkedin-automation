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
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot import answers, cv
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


@dataclass(frozen=True)
class Candidate:
    url: str
    company: str
    job: str
    fit: int
    row_id: str  # the board/Notion id, used to find an already-built packet


def board_candidates(limit: int = 40) -> list[Candidate]:
    """Best-fit-first board rows, already-done excluded."""
    if not BOARD_DB.exists():
        raise SystemExit(f"board mirror not found: {BOARD_DB}")

    conn = sqlite3.connect(BOARD_DB)
    rows = conn.execute(
        "SELECT url, company, job, fit, status, id FROM jobs "
        "WHERE url LIKE '%linkedin.com/jobs/view/%' ORDER BY fit DESC"
    ).fetchall()
    conn.close()

    out: list[Candidate] = []
    for url, company, job, fit, status, row_id in rows:
        if (status or "").strip().lower() in BLOCKED_STATUSES:
            continue
        if any(b in (company or "").lower() for b in BLOCKED_COMPANIES):
            continue
        out.append(Candidate(url, company or "?", job or "?", fit or 0, str(row_id)))
        if len(out) >= limit:
            break
    return out


def select_live_jobs(page, wanted: int) -> list[Candidate]:
    """Probe candidates until `wanted` postings actually show an Easy Apply button."""
    chosen: list[Candidate] = []
    print(f"\nSelecting {wanted} live Easy Apply jobs from the board mirror...")
    for cand in board_candidates():
        if len(chosen) >= wanted:
            break
        try:
            ok, why = has_easy_apply(page, cand.url)
        except Exception as exc:
            ok, why = False, f"probe-error {type(exc).__name__}"
        mark = "OK  " if ok else "skip"
        print(f"  {mark} [{cand.fit:>3}] {cand.company[:26]:<26} {why:<18} {cand.url}")
        if ok:
            chosen.append(cand)
    return chosen


def report(results: list[FillResult], launch_s: float, select_s: float) -> int:
    print("\n" + "=" * 78)
    print("PHASE 0 RESULT")
    print("=" * 78)

    for r in results:
        resume = r.resume_filename or "(none shown)"
        mark = {True: "OK", False: "MISMATCH", None: "unverified"}[r.resume_verified]
        print(
            f"  {r.seconds:>6.1f}s  {r.status:<22} steps={r.steps}  "
            f"filled={len(r.filled):<3} blank={len(r.unanswered):<3} "
            f"resume={resume} [{mark}]"
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
        elif args.job_id:
            by_id = {c.row_id: c for c in board_candidates(limit=10_000)}
            jobs = []
            for jid in args.job_id:
                if jid in by_id:
                    jobs.append(by_id[jid])
                else:
                    print(f"  row {jid} not on the board (or excluded as Applied/Skipped)")
        elif args.urls_file:
            jobs = [Candidate(u.strip(), "?", "?", 0, "")
                    for u in Path(args.urls_file).read_text().splitlines() if u.strip()]
        else:
            jobs = [Candidate(args.url, "?", "?", 0, "")]
        select_s = time.perf_counter() - t1

        if not jobs:
            print("no jobs to fill")
            context.close()
            return 1

        # Resolve the tailored CV per job. A job with no packet keeps LinkedIn's pre-filled
        # resume, which is the GENERIC cv - fine while nothing submits, fatal once it does.
        print(f"\nfilling {len(jobs)} job(s):")
        pdfs: dict[str, Path | None] = {}
        for cand in jobs:
            packet = cv.find_packet(cand.row_id) if cand.row_id else None
            pdf = packet.pdf if packet and packet.pdf.exists() else None
            pdfs[cand.url] = pdf
            tag = f"CV {pdf.name}" if pdf else "NO PACKET - generic CV stays attached"
            print(f"  {cand.company[:22]:<22} {tag}")
            print(f"    {cand.url}")
        print()

        results = []
        for i, cand in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {cand.url}")
            try:
                result = fill_job(page, cand.url, bank, cv_pdf=pdfs[cand.url])
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


def cmd_packet(args: argparse.Namespace) -> int:
    """Build tailored CV packets via Claude Code. Sends nothing."""
    job_ids = args.job_id
    print(f"building {len(job_ids)} packet(s) via Claude Code (this takes minutes each)\n")

    built, failed, limit = cv.build_many(job_ids, timeout=args.timeout)

    for packet in built:
        print(f"  OK    {packet.company} — {packet.role}")
        print(f"          {packet.path}")
        print(f"          PDF {packet.pdf.name} (ATS {packet.ats})")
    for job_id, error in failed:
        print(f"  FAIL  {job_id}\n          {error.splitlines()[0]}")

    if limit:
        # D25: the remaining jobs are NOT failures. Say so, loudly, and record nothing.
        remaining = len(job_ids) - len(built) - len(failed)
        print(f"\n  ** STOPPED: {limit}")
        print(f"  ** {remaining} job(s) untouched. They are NOT failures — retry after the reset.")
        return 3
    return 0 if not failed else 1


def cmd_fieldmap(_: argparse.Namespace) -> int:
    print(answers.dump_field_map())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="apps.autopilot.run")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fieldmap", help="print the FIELD_MAP and the value each entry resolves to")
    sub.add_parser("login", help="open the browser so YOU can sign into LinkedIn by hand")

    pk = sub.add_parser("packet", help="build tailored CV packet(s) via Claude Code; sends nothing")
    pk.add_argument("--job-id", action="append", required=True, help="board/Notion row id (repeatable)")
    pk.add_argument("--timeout", type=int, default=cv.DEFAULT_TIMEOUT)

    f = sub.add_parser("fill", help="fill Easy Apply forms, stopping before submit")
    src = f.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="one LinkedIn job URL")
    src.add_argument("--urls-file", help="file with one job URL per line")
    src.add_argument("--from-board", type=int, metavar="N", help="pick N live jobs from the mirror")
    src.add_argument("--job-id", action="append",
                     help="board row id (repeatable) - resolves the URL AND its tailored CV")
    f.add_argument("--headless", action="store_true", help="not recommended; LinkedIn flags it")

    args = parser.parse_args(argv)
    if args.cmd == "fieldmap":
        return cmd_fieldmap(args)
    if args.cmd == "login":
        return cmd_login(args)
    if args.cmd == "packet":
        return cmd_packet(args)
    return cmd_fill(args)


if __name__ == "__main__":
    sys.exit(main())
