"""Role families — one reusable CV per family, instead of one per company.

WHY THIS EXISTS (owner's call, 2026-08-09). A company-tailored CV takes ~7 minutes to build and
Claude session limits cap that at roughly 5/day, so per-company tailoring capped the whole
pipeline at ~5 applications/day. A family CV is built once and attached to every job in that
family, which takes the ceiling off entirely.

THE TRADE, STATED HONESTLY: a family CV is genuinely weaker than one written for a named
company. It is also far stronger than the single generic CV LinkedIn pre-fills, which is what
these jobs would otherwise receive. For a board of ~50 roles across three families, 47 good
applications beats 5 perfect ones and 42 unsent.

Per-company packets still win where they exist: `pick_cv` prefers a real packet every time and
only falls back to the family CV. Nothing here replaces the tailored path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from apps.autopilot.answers import REPO

PDF_DIR = REPO / "output" / "pdf"

DEVOPS = "DevOps/Platform"
AI_ML = "AI/ML"
GENERAL = "General"

FAMILY_CV = {
    DEVOPS: "FAMILY-DevOps-Platform-SRE",
    AI_ML: "FAMILY-AI-ML-Engineer",
    GENERAL: "FAMILY-Software-Engineer",
}

# Order matters. A title like "AI DevOps Engineer" or "Applied AI SRE" is genuinely both; the
# DevOps CV leads with infrastructure evidence, which is the stronger and better-evidenced half
# of the portfolio, so it wins those. "MLOps" is deliberately AI/ML, not DevOps: those postings
# ask for model lifecycle work, not cluster work.
_AI_FIRST = re.compile(r"mlops|machine learning ops|genai|gen ai|\bllm|prompt engineer|data scien", re.I)
_DEVOPS = re.compile(
    r"devops|\bsre\b|site reliab|platform engineer|infrastructure|cloud engineer|observab"
    r"|release engineer|build (and|&) release|devsecops|kubernetes|multi-cloud|iam",
    re.I,
)
_AI = re.compile(r"\bai\b|\bml\b|machine learning|artificial intelligence|agent|codex|deployment engineer", re.I)


def family_for(job_title: str) -> str:
    """Which family CV this role should receive."""
    title = job_title or ""
    if _AI_FIRST.search(title):
        return AI_ML
    if _DEVOPS.search(title):
        return DEVOPS
    if _AI.search(title):
        return AI_ML
    return GENERAL


def family_pdf(family: str) -> Path:
    return PDF_DIR / f"{FAMILY_CV[family]}.pdf"


@dataclass(frozen=True)
class CvChoice:
    pdf: Path | None
    kind: str      # "tailored" | "family" | "none"
    label: str


def pick_cv(row_id: str, company: str, job_title: str) -> CvChoice:
    """A company-tailored CV if one exists, otherwise the family CV. Never the generic one."""
    from apps.autopilot import cv as cv_module

    packet = cv_module.find_packet(row_id)

    # D34: a company's second role now lives in `<company>--<role>/`, and its packet.json may
    # carry a different job_id than the board row (the runbook writes the id it was given). Match
    # on company+role as well, or a genuinely tailored CV silently loses to the family one — the
    # exact "fast and generic" outcome the CV bridge was built to prevent.
    if not (packet and packet.complete()) and company and job_title:
        by_role = cv_module.find_role_packet(company, job_title)
        if by_role and by_role.complete():
            packet = by_role

    if packet and packet.complete():
        return CvChoice(packet.pdf, "tailored", f"{packet.pdf.name} (tailored, ATS {packet.ats})")

    family = family_for(job_title)
    pdf = family_pdf(family)
    if pdf.exists():
        return CvChoice(pdf, "family", f"{pdf.name} ({family})")
    return CvChoice(None, "none", f"NO CV for {family} - build it before applying")
