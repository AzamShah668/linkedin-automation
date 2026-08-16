"""Write a tailored CV with a free model, and refuse to ship it unless it passes.

WHY THIS EXISTS
---------------
`apps/autopilot/cv.py` builds the packet by shelling out to `claude -p` against the
`cv-architect` skill. It works, it stays, and it is untouched. This is the OmniRoute equivalent,
for the stack that must run with no Claude anywhere.

The CV is the hardest thing to move, because it is the only artifact a recruiter actually reads
and a free model's default register is exactly what this project bans. Measured 2026-08-16, asked
for a CV summary with no other instruction:

    "Results-driven DevOps Engineer with extensive expertise in architecting resilient
     infrastructure..."

Two banned phrases in eleven words. So generation here is a **loop, not a call**: generate,
validate, feed the violations back, regenerate. `cv_validate.py` decides; this module only asks.

WHAT IT WILL NOT DO
-------------------
* It will not ship an unvalidated CV. Every exit path either returns a passing document or fails
  loudly with the violations attached.
* It will not invent. The prompt carries the achievement bank and orders the model to use only
  what is in it, and `check_fabrication` then verifies every number against that same corpus —
  the instruction is not trusted on its own.
* It will not overwrite a Claude-built packet. Output goes to `<company>--<role>/cv-free.md`, so
  the two engines can be compared side by side (which is the whole point of keeping both).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot import llm
from apps.autopilot.answers import REPO
from apps.autopilot.free import cv_validate

OUTREACH_DIR = REPO / "output" / "outreach"

# Each attempt costs one model round trip and nothing else, so the ceiling is about avoiding an
# infinite loop rather than about cost. If four attempts cannot clear the blocklist, the model is
# not going to; failing loudly is more useful than a fifth try.
MAX_ATTEMPTS = 4

# The CV is long. The thinking pass shares this budget (MIN_SAFE_MAX_TOKENS documents the trap one
# layer down), and a truncated CV is a "fragment" violation rather than a crash, so be generous.
CV_MAX_TOKENS = 8192

# How much of the dossier goes into the prompt. Measured 2026-08-16: at 24,000 chars the request
# was 14,463 tokens and Groq's free tier refused it outright (413, TPM limit 12,000). The fallback
# exists precisely for when the gateway is dead, so a prompt only the gateway can accept is a
# fallback that does not work. 12,000 chars keeps the whole request inside the smaller ceiling.
DOSSIER_CHARS = 12_000

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


@dataclass
class BuildResult:
    company: str
    role: str
    path: Path | None
    attempts: int
    report: cv_validate.Report
    text: str = ""

    @property
    def ok(self) -> bool:
        """Did we produce a CV that passes? NOT "did we write a file".

        The first version required a path, so every --dry-run reported FAILED while printing
        "attempt 1: PASS" two lines above. Conflating "succeeded" with "persisted" makes the
        one mode you use for testing lie about the thing you are testing.
        """
        return bool(self.text.strip()) and self.report.ok


def build_prompt(company: str, role: str, jd: str, corpus: str,
                 feedback: str = "") -> str:
    """The cv-architect rules, stated explicitly because a plain model reads no skill file.

    An agent could be told "follow the cv-architect skill" and go and read it. A single-shot model
    cannot, so every rule it must obey is inlined here. The blocklist below is deliberately the
    same one `cv_validate` enforces: telling the model one set of rules and grading it against
    another is how a retry loop never converges.
    """
    banned = ", ".join(f'"{p}"' for p in cv_validate.BANNED_PHRASES)
    sections = " / ".join(cv_validate.REQUIRED_ONE_OF)
    parts = [
        "You are writing a tailored CV for a real job application. It will be read by a human "
        "recruiter, so it must read like a person wrote it.",
        "",
        f"TARGET COMPANY: {company}",
        f"TARGET ROLE: {role}",
        "",
        "THE ONLY FACTS YOU MAY USE. Everything below is verified. You may select from it, "
        "reorder it and rephrase it. You may NOT add achievements, numbers, employers, dates or "
        "technologies that do not appear here. If something is not below, it did not happen.",
        "--- BEGIN SOURCE DOSSIER ---",
        corpus.strip()[:DOSSIER_CHARS],
        "--- END SOURCE DOSSIER ---",
    ]
    if jd.strip():
        parts += ["", "THE JOB DESCRIPTION (use it to choose emphasis, never as a source of "
                      "facts about the candidate):", jd.strip()[:6_000]]
    parts += [
        "",
        "HARD RULES:",
        f"1. NEVER use any of these phrases: {banned}.",
        "2. No em-dashes as a habit. A couple as title separators is fine; peppering them through "
        "sentences is the most recognisable machine tell there is.",
        "3. Every number must come from the dossier. Do not round, inflate or invent one.",
        "4. Plain verbs: built, wrote, shipped, deployed, cut, automated, migrated, hardened. "
        "Specific beats grand: 'cut cold start from 60s to 8s', never 'improved performance'.",
        "5. Vary the rhythm. Not every bullet the same length or the same opening verb.",
        "6. No vague scale words with no number behind them ('various', 'numerous', 'several key').",
        "7. No pronouns in bullets. The summary may read naturally.",
        f"8. Include a Skills section and one of: {sections}. Name the target company somewhere.",
        "9. Say nothing admiring about the company. You have not researched it and an invented "
        "compliment is the most obvious tell in the document.",
        "",
        "Output MARKDOWN only: the CV itself, starting with the candidate's name as an H1. "
        "No preamble, no commentary, no code fences.",
    ]
    if feedback:
        parts += ["", "=== YOUR PREVIOUS ATTEMPT WAS REJECTED ===", feedback,
                  "Rewrite the whole CV, fixing every point above. Change nothing else."]
    return "\n".join(parts)


def _strip_fences(text: str) -> str:
    """Models wrap markdown in ``` despite being told not to. Cheaper to strip than to re-ask."""
    body = (text or "").strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-zA-Z]*\n", "", body)
        body = re.sub(r"\n```\s*$", "", body)
    return body.strip()


def build(company: str, role: str, jd: str = "",
          max_attempts: int = MAX_ATTEMPTS, model: str | None = None,
          write: bool = True) -> BuildResult:
    """Generate, validate, retry with the violations, and only then write."""
    corpus, missing = cv_validate.evidence_corpus()
    if missing or not corpus.strip():
        report = cv_validate.Report()
        report.fail(f"source dossier unreadable: {', '.join(missing) or 'empty'}")
        # No dossier means no facts, and a CV written without facts is the one thing this project
        # has never permitted. Refuse before spending a single call.
        return BuildResult(company, role, None, 0, report)

    model = model or llm.heavy_model()
    feedback = ""
    report = cv_validate.Report()
    text = ""
    used = 0

    for attempt in range(1, max_attempts + 1):
        prompt = build_prompt(company, role, jd, corpus, feedback)
        try:
            text = _strip_fences(llm.ask(prompt, max_tokens=CV_MAX_TOKENS, model=model))
        except Exception as exc:                      # noqa: BLE001 - any provider failure
            # Consume an attempt and keep going. The gateway intermittently streams nothing at
            # all (it certified clean minutes before this was written), and treating a transient
            # transport failure as a permanent one throws away every remaining retry.
            used = attempt
            report = cv_validate.Report()
            report.fail(f"model call failed on attempt {attempt}: {type(exc).__name__}: "
                        f"{str(exc)[:200]}")
            print(f"  attempt {attempt}: call failed ({type(exc).__name__}); retrying")
            time.sleep(min(5 * attempt, 20))
            continue

        report = cv_validate.validate(text, company=company, role=role, corpus=corpus)
        used = attempt
        print(f"  attempt {attempt}: {len(text)} chars -> {report.summary().splitlines()[0]}")
        if report.ok:
            break
        for violation in report.violations[:6]:
            print(f"      {violation}")
        feedback = report.feedback()

    if not report.ok:
        # Loud, and the text is kept on the result so a human can read what it kept getting wrong.
        return BuildResult(company, role, None, used, report, text=text)

    path = None
    if write:
        folder = OUTREACH_DIR / f"{_slug(company)}--{_slug(role)[:40]}"
        folder.mkdir(parents=True, exist_ok=True)
        # cv-free.md, never cv.md: the Claude packet builder owns its own filenames and the two
        # engines must be comparable side by side, not overwriting each other.
        path = folder / "cv-free.md"
        path.write_text(text, encoding="utf-8")
    return BuildResult(company, role, path, used, report, text=text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build a tailored CV with a free model. Sends nothing.")
    ap.add_argument("--company", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--jd", default="", help="path to a job description file")
    ap.add_argument("--attempts", type=int, default=MAX_ATTEMPTS)
    ap.add_argument("--dry-run", action="store_true", help="generate and validate, write nothing")
    args = ap.parse_args(argv)

    jd = ""
    if args.jd:
        try:
            jd = Path(args.jd).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"!! could not read the JD ({exc}); continuing without it")

    print(f"building a CV for {args.company} / {args.role}")
    result = build(args.company, args.role, jd,
                   max_attempts=args.attempts, write=not args.dry_run)

    if result.ok:
        print(f"\nPASS after {result.attempts} attempt(s)")
        if result.path:
            print(f"written: {result.path.relative_to(REPO)}")
        else:
            print("(dry run: nothing written)")
        return 0

    print(f"\nFAILED after {result.attempts} attempt(s). NOTHING was written.")
    print(result.report.summary())
    print("\nThis is not a silent failure: no CV means no CV, never a bad one.")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
