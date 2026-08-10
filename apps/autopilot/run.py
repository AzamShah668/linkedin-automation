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
import re
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot import answers, cv, families, sourcing
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
        for blocker in r.blockers:
            print(f"          BLOCKED: {blocker}")
        if r.note:
            print(f"          note: {r.note}")

    # A job that reached neither Review nor Submit did NOT get filled. Counting it toward the
    # target is how the 2026-08-06 run printed PASS while 3 of 5 jobs did nothing at all
    # (filled=0, blank=0, steps=1, ~4s each). A metric that reports success for a no-op is
    # worse than no metric, because it stops you looking.
    # `submitted` is the MOST complete outcome there is. Omitting it here made the first real
    # application in this project's history print "INVALID - nothing was filled" (2026-08-09).
    DID_WORK = ("reached-review", "reached-submit", "submitted", "submitted-unconfirmed")
    real = [r for r in results if r.status in DID_WORK]
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
    # Submitting is irreversible. It stays one job at a time until the owner says otherwise,
    # and a batch flag must never be able to turn one real application into five.
    if args.submit:
        if args.from_board:
            print("REFUSING: --submit with --from-board. Submit one job at a time:")
            print("  py -3 -m apps.autopilot.run fill --job-id <id> --submit")
            return 2
        if args.urls_file or (args.job_id and len(args.job_id) > 1):
            print("REFUSING: --submit accepts exactly one job.")
            return 2

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
            # Same CV choice the batch makes: tailored packet first, family CV otherwise.
            # `fill` used to look only for a packet, so a dry run attached a different CV from
            # the one a real submission would - which makes the dry run worth less than nothing.
            choice = families.pick_cv(cand.row_id, cand.company, cand.job) if cand.row_id else None
            pdf = choice.pdf if choice else None
            pdfs[cand.url] = pdf
            tag = f"CV {choice.label}" if choice and pdf else "NO CV - generic stays attached"
            print(f"  {cand.company[:22]:<22} {tag}")
            print(f"    {cand.url}")
        print()

        results = []
        for i, cand in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {cand.url}")
            try:
                result = fill_job(
                    page, cand.url, bank,
                    cv_pdf=pdfs[cand.url],
                    submit=args.submit,
                    company=cand.company,
                    role=cand.job,
                )
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

    # Company name per job id, so a build that the runbook is guaranteed to refuse fails in
    # milliseconds instead of burning ~7 minutes of a session-limited resource.
    conn = sqlite3.connect(BOARD_DB)
    companies = {
        jid: (conn.execute("SELECT company FROM jobs WHERE id=?", (jid,)).fetchone() or [""])[0]
        for jid in job_ids
    }
    conn.close()

    built, failed, limit = cv.build_many(job_ids, timeout=args.timeout, companies=companies)

    for packet in built:
        print(f"  OK    {packet.company} — {packet.role}")
        print(f"          {packet.path}")
        print(f"          PDF {packet.pdf.name} (ATS {packet.ats})")
    for job_id, error in failed:
        # Print the WHOLE error. D17 says report both streams; showing only the first line
        # threw away the STDOUT that explains the failure (2026-08-09).
        print(f"  FAIL  {job_id}")
        for line in error.splitlines():
            print(f"          {line}")

    if limit:
        # D25: the remaining jobs are NOT failures. Say so, loudly, and record nothing.
        remaining = len(job_ids) - len(built) - len(failed)
        print(f"\n  ** STOPPED: {limit}")
        print(f"  ** {remaining} job(s) untouched. They are NOT failures — retry after the reset.")
        return 3
    return 0 if not failed else 1


JD_DIR = REPO / "output" / "jd"

# LinkedIn has renamed this container repeatedly; try them in order and fall back to <main>.
JD_SELECTORS = (
    "#job-details",
    ".jobs-description__content",
    ".jobs-box__html-content",
    ".jobs-description",
)

# Page chrome that appears in every LinkedIn page. If the "JD" contains these, it is the nav
# bar and footer, not a job description. A `main` fallback returned exactly this and sailed
# past a naive length check, making 14 of 15 captures look successful.
CHROME_MARKERS = ("Talent Solutions", "Community Guidelines", "Ad Choices", "Post a job")


def _job_description(page) -> str:
    """The JD text, or '' if no real description was found. Never returns chrome."""
    try:  # the description is usually collapsed behind a "see more" control
        more = page.get_by_role("button", name=re.compile(r"see more|show more", re.I)).first
        if more.count():
            more.click(timeout=3000)
    except Exception:
        pass

    for selector in JD_SELECTORS:
        target = page.locator(selector).first
        try:
            if not target.count():
                continue
            text = " ".join(target.inner_text(timeout=4000).split())
        except Exception:
            continue
        if len(text) > 400 and sum(m in text for m in CHROME_MARKERS) < 2:
            return text
    return ""


def cmd_prune(args: argparse.Namespace) -> int:
    """Probe every board row for liveness; mark dead ones and save survivors' job descriptions.

    ~63% of this board was found dead on 2026-08-06. Building packets at ~7 min each against
    closed postings is the most expensive possible mistake, so liveness is checked BEFORE any
    re-scoring effort is spent.
    """
    from apps.autopilot.fill import has_easy_apply

    conn = sqlite3.connect(BOARD_DB)
    rows = conn.execute(
        "SELECT id, url, company, job, fit, status FROM jobs "
        "WHERE url LIKE '%linkedin.com/jobs/view/%' ORDER BY fit DESC"
    ).fetchall()

    live: list[tuple] = []
    dead: list[tuple] = []
    jd_ok = jd_fail = 0
    JD_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        context = open_browser(pw, _user_data_dir(), headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            check_logged_in(page)
        except LinkedInLoggedOut as exc:
            print(f"ABORTING: {exc}")
            context.close()
            return 2

        print(f"probing {len(rows)} rows...\n")
        for row_id, url, company, job, fit, status in rows:
            if (status or "").lower() in BLOCKED_STATUSES:
                continue
            try:
                ok, why = has_easy_apply(page, url)
            except Exception as exc:
                ok, why = False, f"probe-error {type(exc).__name__}"

            # `external-or-none` is NOT dead — it just is not Easy Apply. Only a closed or
            # vanished posting is dead. Conflating the two would delete usable rows.
            if why in ("closed", "no-buttons", "removed"):
                dead.append((row_id, company, job, fit, why))
                print(f"  DEAD [{fit:>3}] {company[:24]:<24} {why}")
                continue

            live.append((row_id, company, job, fit, why, url))
            saved = ""
            if args.save_jd and len(live) <= args.save_jd_limit:
                text = _job_description(page)
                if text:
                    (JD_DIR / f"{row_id}.txt").write_text(text, encoding="utf-8")
                    saved = f"jd {len(text)}b"
                    jd_ok += 1
                else:
                    # Reported, never swallowed. A silent `except: pass` here saved 1 JD out of
                    # 52 on the first run and looked like a success.
                    saved = "JD CAPTURE FAILED"
                    jd_fail += 1
            print(f"  live [{fit:>3}] {company[:24]:<24} {why:<18} {saved}")

    if not args.dry_run:
        for row_id, company, job, fit, why in dead:
            conn.execute(
                "UPDATE jobs SET status='Skipped', "
                "notes=COALESCE(notes,'') || ?, updated_at=? WHERE id=?",
                (f"\n\nCLOSED {answers_today()}: posting no longer accepting applications "
                 f"(probe: {why}). Marked by `run prune`.", answers_today(), row_id),
            )
        conn.commit()
    conn.close()

    print("\n" + "=" * 70)
    print(f"  live    : {len(live)}")
    print(f"  dead    : {len(dead)}  {'(marked Skipped)' if not args.dry_run else '(dry run)'}")
    print(f"  survival: {len(live) / max(len(live) + len(dead), 1):.0%}")
    if args.save_jd:
        print(f"  JDs     : {jd_ok} saved, {jd_fail} FAILED to capture")
    print("\n  TOP 5 SURVIVING BY FIT")
    for row_id, company, job, fit, why, url in sorted(live, key=lambda r: -r[3])[:5]:
        print(f"    [{fit:>3}] {company[:22]:<22} {job[:40]:<40} {why}")
        print(f"          {url}")
    return 0


def answers_today() -> str:
    from apps.autopilot import ledger
    return ledger.today()


def cmd_applyall(args: argparse.Namespace) -> int:
    """Apply to every eligible live row using tailored packets first, family CVs otherwise.

    THROTTLED ON PURPOSE. LinkedIn watches application velocity, and fifty submissions inside a
    few minutes is the clearest bot signal there is - a restriction would cost the account where
    the warm insider and every recruiter connection lives. The runbook mandates randomised
    40-180s gaps for exactly this reason, so the batch takes about an hour rather than a minute.
    Same applications, no ban.
    """
    import random

    from apps.autopilot import families, ledger

    bank = answers.load_bank()
    candidates = board_candidates(limit=10_000)

    plan: list[tuple[Candidate, families.CvChoice]] = []
    skipped: list[tuple[str, str]] = []
    # Rows a heuristic finds suspicious. They are NOT dropped — they go to the back of the plan,
    # because a false positive here costs an opportunity while a false negative costs one slot.
    deferred: list[tuple[Candidate, families.CvChoice, str]] = []
    for cand in candidates:
        blocked = ledger.already_applied(cand.company, cand.job, cand.url)
        if blocked:
            skipped.append((f"{cand.company} - {cand.job}", f"ledger: {blocked}"))
            continue
        choice = families.pick_cv(cand.row_id, cand.company, cand.job)
        if choice.pdf is None:
            skipped.append((f"{cand.company} - {cand.job}", choice.label))
            continue

        # An application slot spent on a company with nobody behind it can never be followed up,
        # and D32 says an application that reaches no human is unfinished work. Crossing Hurdles
        # took two slots this way. Only recorded EVIDENCE blocks; a title heuristic merely sends
        # the row to the back of the queue (see sourcing.py on why the asymmetry runs this way).
        verdict = sourcing.screen(cand.company, cand.job)
        if verdict.blocks:
            skipped.append((f"{cand.company} - {cand.job}", f"sourcing: {verdict.reason}"))
            continue
        if verdict.action == sourcing.DEPRIORITIZE:
            deferred.append((cand, choice, verdict.reason))
            continue

        # ONE ROLE PER COMPANY. Three applications to the same staffing agency inside ten minutes
        # land on ONE recruiter's desk and read as scattershot rather than interested - the board
        # notes already say one contact covers all of an agency's rows (D8). The highest-fit role
        # goes first because the plan is sorted by fit.
        #
        # Counted across the LEDGER as well as this run: a per-run-only cap let Crossing Hurdles
        # receive two applications on consecutive runs (2026-08-09 and 08-10), which is the same
        # problem spread over time.
        #
        # But scoped to SAME CHANNEL and a RECENT WINDOW (D33). Counting every ledger row ever
        # made one linkedin-dm from 2026-07-26 permanently block all four Infosys rows including
        # Junior AI Engineer (fit 90) - the best row on the board, at the one company where a
        # 1st-degree connection is already inside.
        from apps.autopilot import ledger as _ledger
        prior = _ledger.recent_company_submissions(cand.company)
        pending = [c for c, _ in plan if c.company.lower() == cand.company.lower()]
        if len(prior) + len(pending) >= args.max_per_company:
            # The reason must state the ACTUAL condition. The old text said "this run", which was
            # false on both counts and sent two investigations down the wrong path (D33).
            if prior:
                when = ", ".join(sorted({r.get("submitted_at", "?") for r in prior}))
                why = (f"{len(prior)} Easy Apply to this company in the last "
                       f"{_ledger.COMPANY_CAP_WINDOW_DAYS}d ({when}); cap {args.max_per_company}")
            else:
                why = (f"already applying to {len(pending)} role(s) here THIS run; "
                       f"cap {args.max_per_company}")
            skipped.append((f"{cand.company} - {cand.job}", why))
            continue
        plan.append((cand, choice))

    # Suspicious rows go LAST, never away. The company cap is re-checked here so a deferred row
    # cannot sneak past a limit the main loop already enforced.
    for cand, choice, why in deferred:
        from apps.autopilot import ledger as _ledger2
        prior = len(_ledger2.recent_company_submissions(cand.company))
        pending = sum(1 for c, _ in plan if c.company.lower() == cand.company.lower())
        if prior + pending >= args.max_per_company:
            skipped.append((f"{cand.company} - {cand.job}", f"deprioritized, then capped: {why}"))
            continue
        plan.append((cand, choice))
        print(f"  .. deferred to the back of the queue: {cand.company} - {cand.job[:40]} ({why})")

    # --limit caps APPLICATIONS SENT, not rows examined. Capping the plan meant "--limit 5"
    # took the five highest-fit rows, which are all external-ATS companies with no Easy Apply
    # button, and submitted nothing at all (2026-08-09). The loop below walks the whole list
    # and stops once `limit` applications have actually gone out.
    print(f"\nPLAN: up to {args.limit} application(s) from {len(plan)} candidate row(s), "
          f"{len(skipped)} skipped")
    for cand, choice in plan:
        print(f"  [{cand.fit:>3}] {cand.company[:22]:<22} {cand.job[:34]:<34} {choice.label}")
    if skipped:
        print(f"\n  skipped ({len(skipped)}):")
        for what, why in skipped[:10]:
            print(f"    {what[:44]:<44} {why[:60]}")

    if args.dry_run:
        print("\nDRY RUN - nothing was opened or submitted.")
        return 0

    est = args.limit * ((args.min_gap + args.max_gap) / 2 + 45) / 60
    print(f"\nSUBMITTING FOR REAL. Up to {args.limit} applications, roughly {est:.0f} minutes "
          f"with {args.min_gap}-{args.max_gap}s gaps between them.\n")

    results: list[FillResult] = []
    with sync_playwright() as pw:
        context = open_browser(pw, _user_data_dir(), headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            check_logged_in(page)
        except LinkedInLoggedOut as exc:
            print(f"ABORTING: {exc}")
            context.close()
            return 2

        submitted_count = 0
        for i, (cand, choice) in enumerate(plan, 1):
            if submitted_count >= args.limit:
                print(f"\nReached the {args.limit}-application limit. "
                      f"{len(plan) - i + 1} row(s) left unexamined.")
                break
            print(f"[{i}/{len(plan)}] {cand.company} - {cand.job}")
            try:
                result = fill_job(page, cand.url, bank, cv_pdf=choice.pdf,
                                  submit=True, company=cand.company, role=cand.job)
            except LinkedInLoggedOut as exc:
                print(f"  ABORTING WHOLE RUN: {exc}")
                break
            results.append(result)
            print(f"  -> {result.status} ({choice.kind} CV) in {result.seconds:.0f}s")
            for blocker in result.blockers:
                print(f"     BLOCKED: {blocker}")

            if result.status in ("submitted", "submitted-unconfirmed"):
                _mark_applied(cand, result)
                submitted_count += 1

            # THROTTLE ONLY AFTER A REAL SUBMISSION. The gap exists because LinkedIn watches
            # APPLICATION velocity; a job with no Easy Apply button submitted nothing, so there
            # is nothing to throttle. Waiting 40-180s after a 1-second skip is what made the
            # first run look like it was crawling without applying - 5 of the first 6 rows are
            # external-ATS and each cost up to 3 minutes of dead waiting.
            if i < len(plan):
                if result.status in ("submitted", "submitted-unconfirmed"):
                    gap = random.randint(args.min_gap, args.max_gap)
                    print(f"  ... applied, pausing {gap}s before the next application")
                else:
                    gap = random.randint(3, 8)
                try:
                    page.wait_for_timeout(gap * 1000)
                except Exception as exc:
                    print(f"\nBROWSER CLOSED ({type(exc).__name__}). Stopping cleanly at {i}/{len(plan)}.")
                    break

        context.close()

    sent = [r for r in results if r.status == "submitted"]
    unconfirmed = [r for r in results if r.status == "submitted-unconfirmed"]
    print("\n" + "=" * 70)
    print(f"  SUBMITTED (confirmed) : {len(sent)}")
    print(f"  unconfirmed           : {len(unconfirmed)}  <- verify by hand, NEVER retry")
    print(f"  not submitted         : {len(results) - len(sent) - len(unconfirmed)}")

    from collections import Counter
    reasons = Counter(r.status for r in results if r not in sent and r not in unconfirmed)
    for status, count in reasons.most_common():
        print(f"    {count:>3}x {status}")

    # THE ACTIONABLE OUTPUT. A job that reaches Review but will not advance is almost always
    # held by a REQUIRED question the answer bank cannot answer - and we do not invent answers.
    # Each line here is one bank key that would unblock every job asking it.
    blocking: Counter[str] = Counter()
    for r in results:
        if r.status in ("submitted", "submitted-unconfirmed"):
            continue
        for label in r.unanswered:
            blocking[label] += 1
    if blocking:
        print("\n  QUESTIONS BLOCKING SUBMISSION - answer these once in the bank to unblock:")
        for label, count in blocking.most_common(20):
            print(f"    {count:>3}x  {label[:100]}")
    return 0


def _ledger_rows() -> list[dict]:
    from apps.autopilot import ledger
    return ledger.load()


def _mark_applied(cand: Candidate, result: FillResult) -> None:
    conn = sqlite3.connect(BOARD_DB)
    conn.execute(
        "UPDATE jobs SET status='Applied', applied=?, notes=COALESCE(notes,'')||?, updated_at=? WHERE id=?",
        (answers_today(),
         f"\n\n{answers_today()} APPLIED via apps/autopilot batch. status={result.status}. "
         f"CV: {result.resume_filename}. Receipt: {result.slug}-{answers_today()}-submitted.png",
         answers_today(), cand.row_id),
    )
    conn.commit()
    conn.close()


def cmd_ledger(args: argparse.Namespace) -> int:
    """Show or seed the never-resubmit ledger."""
    from apps.autopilot import ledger

    if args.seed:
        added, skipped = ledger.seed()
        print(f"seeded: {added} added, {skipped} already present\n")
    print(ledger.describe())
    print(f"\nfile: {ledger.LEDGER_PATH}")
    return 0


def cmd_fieldmap(_: argparse.Namespace) -> int:
    print(answers.dump_field_map())
    return 0


def main(argv: list[str] | None = None) -> int:
    # Line-buffer stdout. Piped/backgrounded runs block-buffer by default, so a long batch
    # writes a 0-BYTE log until it exits. On 2026-08-09 that hid a 15-minute hang completely:
    # no output, no error, no way to tell a stuck run from a slow one. Progress you cannot see
    # is the same as no progress (D30).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="apps.autopilot.run")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fieldmap", help="print the FIELD_MAP and the value each entry resolves to")
    sub.add_parser("login", help="open the browser so YOU can sign into LinkedIn by hand")

    pr = sub.add_parser("prune", help="probe every board row for liveness; mark the dead ones")
    pr.add_argument("--dry-run", action="store_true", help="report only, change nothing")
    pr.add_argument("--save-jd", action="store_true", help="save survivors' JD text for re-scoring")
    pr.add_argument("--save-jd-limit", type=int, default=15,
                    help="only fetch JDs for the top N survivors (default 15)")

    aa = sub.add_parser("apply-all", help="apply to every eligible live row, throttled")
    aa.add_argument("--dry-run", action="store_true", help="show the plan, open nothing")
    aa.add_argument("--limit", type=int, default=50, help="max applications this run")
    aa.add_argument("--min-gap", type=int, default=40, help="min seconds between applications")
    aa.add_argument("--max-gap", type=int, default=180, help="max seconds between applications")
    aa.add_argument("--max-per-company", type=int, default=1,
                    help="max roles per company per run (default 1; highest fit wins)")

    lg = sub.add_parser("ledger", help="show the never-resubmit ledger")
    lg.add_argument("--seed", action="store_true", help="add the pre-ledger applications")

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
    f.add_argument("--submit", action="store_true",
                   help="ACTUALLY SUBMIT. Off by default. One job at a time; not with --from-board.")

    args = parser.parse_args(argv)
    if args.cmd == "fieldmap":
        return cmd_fieldmap(args)
    if args.cmd == "login":
        return cmd_login(args)
    if args.cmd == "apply-all":
        return cmd_applyall(args)
    if args.cmd == "prune":
        return cmd_prune(args)
    if args.cmd == "ledger":
        return cmd_ledger(args)
    if args.cmd == "packet":
        return cmd_packet(args)
    return cmd_fill(args)


if __name__ == "__main__":
    sys.exit(main())
