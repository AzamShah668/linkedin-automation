"""Turn scraped LinkedIn job JSON into scored board rows.

⚠️ THIS EXISTED ONLY AS A SCRATCHPAD SCRIPT UNTIL 2026-08-15. The whole 20-application run
depended on it, [[31-apply-batch-runbook]] §1 describes it, and it was sitting in a
session-scoped temp directory that gets deleted when the session ends. A runbook that
references a program nobody can run is a runbook that fails on its first reuse.

Input: the `jobs-*.json` files written by the Playwright scrape (see the runbook for the
`f_AL=true` search URL and the scroll/paginate evaluate). Each holds
`{"jobs": [{id, title, company, location, easyApply, alumni, posted}, ...]}`.

    py -3 -m apps.autopilot.intake                 # dry run, prints what would be inserted
    py -3 -m apps.autopilot.intake --write
    py -3 -m apps.autopilot.intake --write --min-fit 75

Scores from the TITLE only. That is a triage ORDERING signal, not a judgement: no JD is
fetched here, and the board has always worked this way. Re-score before building a packet.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BOARD_DB = REPO / "database" / "board.sqlite3"
DEFAULT_MIN_FIT = 70

# --- his target families ----------------------------------------------------------------
DEVOPS = re.compile(
    r"devops|sre|site reliability|platform engineer|infrastructure|cloud engineer"
    r"|kubernetes|observability|cloud ops|cloudops|systems engineer", re.I)
AIML = re.compile(
    r"\bai\b|\bml\b|machine learning|mlops|genai|gen ai|generative|\bllm|deep learning"
    r"|data scien|prompt|agentic|nlp", re.I)
SWE = re.compile(r"software engineer|backend|python developer|full ?stack", re.I)

# --- what makes a row worse -------------------------------------------------------------
SENIOR = re.compile(
    r"\bsenior\b|\bsr\.?\b|\blead\b|principal|\bstaff\b|architect|manager|head of"
    r"|director|\bvp\b|vice president", re.I)
YEARS = re.compile(r"(\d+)\s*\+?\s*(?:to\s*\d+\s*)?year", re.I)
OFF_TARGET = re.compile(
    r"\bmern\b|\breact\b|next\.?js|angular|\bnode\.?js\b|\bjava\b(?!script)|\.net"
    r"|\bc#\b|salesforce|servicenow|sap\b|\bqa\b|tester|testing|ui/ux|designer"
    r"|android|\bios\b|flutter|wordpress|php|drupal|sales|marketing|recruiter"
    r"|business analyst|scrum|product manager|golang|ruby|dotnet|mainframe"
    r"|network engineer|desktop|support engineer|technical writer"
    # His whole stack is Linux/Proxmox/K8s. "Windows Systems Engineer II" scored 82 on the
    # bare "systems engineer" and burned an attempt on 2026-08-15.
    r"|windows|active directory|\bm365\b|microsoft 365|sharepoint|citrix|vmware", re.I)
INTERN = re.compile(r"intern\b|internship|trainee|fresher", re.I)


def score(title: str, location: str, alumni: str) -> tuple[int, str | None]:
    """(fit, family). fit 0 with family None means "not one of his families at all"."""
    text = title or ""
    family = ("DevOps/Platform" if DEVOPS.search(text)
              else "AI/ML" if AIML.search(text)
              else "General" if SWE.search(text)
              else None)
    if family is None:
        return 0, None

    fit = {"DevOps/Platform": 82, "AI/ML": 82, "General": 72}[family]
    if DEVOPS.search(text) and AIML.search(text):
        fit += 6                       # the exact intersection he sells
    if OFF_TARGET.search(text):
        fit -= 30
    if SENIOR.search(text):
        fit -= 14                      # ~2 years of experience
    match = YEARS.search(text)
    if match:
        years = int(match.group(1))
        # A title advertising 8+ years is not a near miss, it is a different candidate.
        # Measured 2026-08-15: these reach the form and then ask "10+ years?" as a REQUIRED
        # question he must truthfully answer No to, wasting the whole attempt.
        fit -= 25 if years >= 8 else 15 if years >= 5 else 0
    if INTERN.search(text):
        fit -= 4
    if re.search(r"remote", location or "", re.I):
        fit += 3
    if alumni:
        fit += 5                       # Central University of Kashmir alumni inside (D8)
    return max(0, min(99, fit)), family


def _work_type(location: str) -> str:
    if re.search(r"remote", location or "", re.I):
        return "Remote"
    if re.search(r"hybrid", location or "", re.I):
        return "Hybrid"
    return "On-site"


def collect(pattern: str = "jobs-*.json") -> dict[str, dict]:
    """Merge every scrape file, keeping ONLY Easy Apply rows, deduped by LinkedIn job id."""
    merged: dict[str, dict] = {}
    for path in sorted(glob.glob(str(REPO / pattern))):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for job in data.get("jobs", []):
            if job.get("easyApply") and job.get("id"):
                merged[job["id"]] = job
    return merged


def plan(min_fit: int) -> tuple[list[dict], int, int]:
    """(rows_to_insert, already_known, below_threshold)."""
    merged = collect()
    conn = sqlite3.connect(BOARD_DB)
    conn.row_factory = sqlite3.Row
    known_urls = {r["url"] for r in conn.execute("SELECT url FROM jobs WHERE url IS NOT NULL")}
    known_pairs = {
        (str(r["company"]).strip().lower(), str(r["job"]).strip().lower())
        for r in conn.execute("SELECT company, job FROM jobs")
    }
    conn.close()

    today = dt.date.today().isoformat()
    rows, dupes, low = [], 0, 0
    for job_id, job in merged.items():
        url = f"https://www.linkedin.com/jobs/view/{job_id}/"
        pair = (job["company"].strip().lower(), job["title"].strip().lower())
        # Dedupe on BOTH url and company+title: the same role is often reposted under a new id.
        if url in known_urls or pair in known_pairs:
            dupes += 1
            continue
        fit, _family = score(job["title"], job.get("location", ""), job.get("alumni", ""))
        if fit < min_fit:
            low += 1
            continue
        rows.append({
            "id": f"li-{job_id}",
            "job": job["title"],
            "company": job["company"],
            "fit": fit,
            "status": "New",
            "work_type": _work_type(job.get("location", "")),
            "location": re.sub(r"\s*\((Remote|Hybrid|On-site)\)\s*$", "", job.get("location", "")),
            "warm": 1 if job.get("alumni") else 0,
            "url": url,
            "found": today,
            "notes": f"alumni: {job['alumni']}" if job.get("alumni") else None,
        })
    rows.sort(key=lambda r: -r["fit"])
    return rows, dupes, low


def write(rows: list[dict]) -> int:
    conn = sqlite3.connect(BOARD_DB)
    now = dt.datetime.now().isoformat(timespec="seconds")
    for r in rows:
        conn.execute(
            """INSERT OR IGNORE INTO jobs
               (id, job, company, fit, status, work_type, location, warm, url, found,
                applied, next_action, notes, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL,?,?)""",
            (r["id"], r["job"], r["company"], r["fit"], r["status"], r["work_type"],
             r["location"], r["warm"], r["url"], r["found"], r["notes"], now),
        )
    conn.commit()
    n = conn.total_changes
    conn.close()
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="actually insert (default: dry run)")
    ap.add_argument("--min-fit", type=int, default=DEFAULT_MIN_FIT)
    args = ap.parse_args(argv)

    if not glob.glob(str(REPO / "jobs-*.json")):
        print("no jobs-*.json scrape files at the repo root.")
        print("Run the Playwright scrape first - see docs/knowledge/31-apply-batch-runbook.md §1.")
        return 1

    rows, dupes, low = plan(args.min_fit)
    print(f"{len(rows)} new row(s) | {dupes} already on the board | {low} below fit {args.min_fit}\n")
    for r in rows[:40]:
        warm = " *ALUMNI*" if r["warm"] else ""
        print(f"  [{r['fit']:>3}] {r['company'][:26]:28} {r['job'][:46]:48} {r['work_type']}{warm}")
    if not args.write:
        print("\nDRY RUN. Pass --write to insert.")
        return 0
    print(f"\ninserted {write(rows)} row(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
