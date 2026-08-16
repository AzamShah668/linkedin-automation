"""Refuse to ship a CV a free model got wrong.

WHY THIS EXISTS
---------------
On the Claude stack the CV is written by an agent following `cv-architect`, and the quality is the
model's. Azam chose to move it to a free OmniRoute model anyway (2026-08-16), knowing the tradeoff.
Measured the same day, asked for a CV summary unprompted, the free model produced:

    "Results-driven DevOps Engineer with extensive expertise in architecting resilient
     infrastructure..."

**Two banned phrases in the first eleven words**, from a blocklist this project has had since the
`cv-architect` skill was written. So the validator is not belt-and-braces: it is the thing standing
between a free model and a document a recruiter reads.

WHAT IT CHECKS, AND WHY EACH ONE
--------------------------------
1. **AI tells** — the exact blocklist in `.claude/skills/cv-architect/references/humanization.md`.
   Not duplicated here by choice: `test_cv_validate.py` asserts every phrase below still appears in
   that file, so the two cannot drift apart silently.
2. **Fabrication** — every number in the CV must appear somewhere in the source dossier. This is
   the oldest rule in the project ("zero fabrication") and a free model is likelier to round 18 up
   to 20, or invent a percentage that reads well.
3. **Structure** — the sections a CV needs, and a length that is a CV rather than a paragraph.
4. **Grounding** — the target company and role appear, and no invented claim about the company
   (the same rule `pitch.py` enforces on outreach).

THE FAILURE DIRECTION
---------------------
A validator that passes a bad CV is worse than no validator, because it converts "nobody checked"
into "something checked and approved it". So every check fails **closed**: unreadable source
dossier, unparseable CV, or an unexpected error all produce violations, never a silent pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from apps.autopilot.answers import REPO

HUMANIZATION = REPO / ".claude" / "skills" / "cv-architect" / "references" / "humanization.md"

# Sources of truth for anything factual. A number not present in one of these is unsupported.
EVIDENCE_FILES = (
    REPO / "output" / "cv" / "achievement-bank.md",
    REPO / "profile" / "master-profile.md",
    REPO / ".claude" / "skills" / "cv-architect" / "references" / "master-cv.md",
)

# From humanization.md's "AI-tell blocklist". Kept as data so it is testable; the test asserts each
# one still appears in that file, so the skill remains the single source of truth.
BANNED_PHRASES: tuple[str, ...] = (
    "leverage", "leveraged", "spearhead", "spearheaded", "utilize", "utilized",
    "delve", "foster", "empower", "passionate about", "results-driven", "detail-oriented",
    "team player", "proven track record", "dynamic professional", "cutting-edge",
    "state-of-the-art", "seamless", "seamlessly", "robust solutions",
    "in today's fast-paced world", "wear many hats", "think outside the box", "synergy",
    "holistic",
)

# Vague scale words with no number: also a structural tell in humanization.md.
VAGUE_SCALE = ("various", "numerous", "several key", "a wide range of", "multiple key")

EM_DASH = "—"

# A CV that is too short is a fragment (the silent-truncation failure mode, one layer up); one that
# is far too long has usually padded itself with exactly the prose we are trying to avoid.
MIN_CHARS = 900
MAX_CHARS = 12_000

# ⚠️ Calibrated against the REAL CV (output/cv/azam-shah-devops-cv.md), which the first version of
# this validator rejected. He is a final-year student: his CV has **Projects**, not "Experience",
# and demanding the latter would have failed every genuine document he owns. A validator tuned only
# on bad input rejects the good input too, and nobody finds out until it blocks real work.
REQUIRED_SECTIONS = ("skills",)
REQUIRED_ONE_OF = ("experience", "projects", "work history", "employment")

# humanization.md bans em-dash **overuse**, not em-dashes. The real CV uses 10 in 6,009 characters,
# mostly as title separators ("PrivateCloud — Self-Hosted VM Management Platform"), and that reads
# perfectly human. A density ceiling catches a model that sprinkles them into every clause while
# leaving normal typography alone. (pitch.py and followups.py stay at ZERO — a LinkedIn message is
# a different medium, and there an em-dash is the tell.)
EM_DASH_CHARS_EACH = 400

# Numbers that carry no factual claim and should never be treated as fabrication.
_HARMLESS_NUMBER = re.compile(r"^(19|20)\d{2}$")     # years


@dataclass
class Report:
    violations: list[str] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def fail(self, message: str) -> None:
        self.violations.append(message)

    def summary(self) -> str:
        if self.ok:
            return f"PASS ({len(self.checked)} checks)"
        lines = [f"FAIL ({len(self.violations)} violation(s)):"]
        lines += [f"  - {v}" for v in self.violations]
        return "\n".join(lines)

    def feedback(self) -> str:
        """What to hand back to the model on a retry. Specific, so the retry can actually fix it."""
        return "Your previous draft was rejected for these reasons. Fix every one:\n" + "\n".join(
            f"- {v}" for v in self.violations)


def _numbers(text: str) -> set[str]:
    """Numeric claims: 18, 98, 7, 60, 95. Percentages and suffixes normalised to the digits.

    ⚠️ Thousands separators are consumed, not split on. The first version matched `\\d+` alone, so
    "10,000" became {"10", "000"} and a real generated CV was rejected for the invented number
    "000". A fabrication check that cries wolf on ordinary formatting gets switched off, which
    costs far more than the check was ever worth.
    """
    found = set()
    for match in re.finditer(r"\d[\d,]*(?:\.\d+)?", text or ""):
        token = match.group(0).replace(",", "").rstrip(".")
        if token:
            found.add(token.lstrip("0") or "0")     # 007 and 7 are the same claim
    return found


def evidence_corpus(paths: tuple[Path, ...] | None = None) -> tuple[str, list[str]]:
    """(all source text, which files were readable). Missing sources are reported, never ignored.

    ⚠️ Resolved at CALL time. A default argument is evaluated once at import, freezing the module
    constant, so reassigning EVIDENCE_FILES had no effect and this read the real dossier anyway.
    That is the THIRD time this exact bug has appeared here - coverage.py documents it, nudge.py
    reintroduced it, and so did this file. Never bind a module constant in a signature.
    """
    paths = paths if paths is not None else EVIDENCE_FILES
    chunks, missing = [], []
    for path in paths:
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            # relative_to() RAISES for a path outside the repo, turning "this file is missing"
            # into a crash inside the very check meant to fail safe. Report the name we were
            # given instead of insisting it live somewhere in particular.
            try:
                missing.append(str(path.relative_to(REPO)))
            except ValueError:
                missing.append(str(path))
    return "\n".join(chunks), missing


def check_tells(text: str, report: Report) -> None:
    lowered = (text or "").lower()
    report.checked.append("ai-tells")
    for phrase in BANNED_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            report.fail(f'banned phrase "{phrase}" (humanization.md blocklist)')
    for phrase in VAGUE_SCALE:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            report.fail(f'vague scale word "{phrase}" with no number behind it')
    # Overuse, not presence. See EM_DASH_CHARS_EACH: the real CV uses 10 legitimately.
    dashes = (text or "").count(EM_DASH)
    allowed = max(2, len(text or "") // EM_DASH_CHARS_EACH)
    if dashes > allowed:
        report.fail(f"em-dash overuse: {dashes} in {len(text)} chars (at most {allowed} here); "
                    f"humanization.md lists this as a structural tell")


def check_fabrication(text: str, report: Report,
                      corpus: str | None = None) -> None:
    report.checked.append("fabrication")
    if corpus is None:
        corpus, missing = evidence_corpus()
        if missing:
            # Fail closed. Without the dossier we cannot tell an achievement from an invention, and
            # "we could not check" must never read the same as "we checked and it was fine".
            report.fail(f"cannot verify claims: source dossier unreadable ({', '.join(missing)})")
            return
    if not corpus.strip():
        report.fail("cannot verify claims: source dossier is empty")
        return

    supported = _numbers(corpus)
    for number in sorted(_numbers(text)):
        if _HARMLESS_NUMBER.match(number) or number in supported:
            continue
        report.fail(f'number "{number}" does not appear anywhere in the source dossier')


def check_structure(text: str, report: Report) -> None:
    report.checked.append("structure")
    body = text or ""
    if len(body) < MIN_CHARS:
        report.fail(f"only {len(body)} chars; a CV under {MIN_CHARS} is a fragment, "
                    f"not a document (check for a truncated generation)")
    if len(body) > MAX_CHARS:
        report.fail(f"{len(body)} chars exceeds {MAX_CHARS}; almost always padding")
    lowered = body.lower()
    for section in REQUIRED_SECTIONS:
        if section not in lowered:
            report.fail(f'no "{section}" section found')
    if not any(name in lowered for name in REQUIRED_ONE_OF):
        report.fail(f"none of {list(REQUIRED_ONE_OF)} found; a CV needs somewhere the work lives")


def check_grounding(text: str, company: str, role: str, report: Report) -> None:
    report.checked.append("grounding")
    lowered = (text or "").lower()
    if company and company.split()[0].lower() not in lowered:
        report.fail(f'the target company "{company}" is never mentioned; this is not a tailored CV')
    if role:
        # Match on the role's distinctive words rather than the whole string: "Software Engineer
        # [Data Engineer - Python, SQL...]" will never appear verbatim.
        words = [w for w in re.split(r"[^a-z0-9]+", role.lower()) if len(w) > 3]
        if words and not any(w in lowered for w in words[:4]):
            report.fail(f'nothing in the CV echoes the role "{role[:50]}"')
    # The same rule pitch.py enforces: admiration we never researched is the most obvious tell.
    for tell in ("i love what you", "excited about your mission", "big fan of", "i admire"):
        if tell in lowered:
            report.fail(f'invented sentiment about the company: "{tell}"')


def validate(text: str, company: str = "", role: str = "",
             corpus: str | None = None) -> Report:
    """Every check, always all of them, so one retry can fix everything at once."""
    report = Report()
    if not (text or "").strip():
        report.fail("the generated CV is empty")
        return report
    check_tells(text, report)
    check_fabrication(text, report, corpus=corpus)
    check_structure(text, report)
    check_grounding(text, company, role, report)
    return report


__all__ = [
    "BANNED_PHRASES", "EM_DASH", "EVIDENCE_FILES", "HUMANIZATION", "MAX_CHARS", "MIN_CHARS",
    "REQUIRED_ONE_OF", "REQUIRED_SECTIONS", "Report", "VAGUE_SCALE", "check_fabrication", "check_grounding",
    "check_structure", "check_tells", "evidence_corpus", "validate",
]
