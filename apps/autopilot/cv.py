"""The bridge to Claude Code — the one step that keeps a full agent session.

Everything else in this app is a dictionary lookup. CV tailoring is not: it happens once per
COMPANY, a human recruiter reads the result, it is not latency-sensitive, and it needs judgment
(read the JD, find evidence in profile/, refuse to fabricate). Low frequency + high stakes +
not urgent is exactly where a slow, careful, expensive tool belongs.
See docs/knowledge/22-rewrite-architecture.md §5.

This module is deliberately thin. The intelligence lives in
docs/knowledge/15-build-packet-runbook.md and the cv-architect / recruiter-outreach skills,
all reused unchanged. The runbook IS the spec; this just invokes it.

TWO RULES ARE LOAD-BEARING HERE:

1. Judge by the artifact, never the exit code (D17). `claude` exiting 0 having written nothing
   is a failure, and it is the common one.
2. A usage limit is not a job failure (D25). On "You've hit your session limit" the whole batch
   stops and names the cause. Filing it per-job marks good rows FAILED and they never get
   retried — the project lost a day to that already.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

from apps.autopilot.answers import REPO

OUTREACH_DIR = REPO / "output" / "outreach"
PDF_DIR = REPO / "output" / "pdf"
DEFAULT_TIMEOUT = 1800  # a real packet build is minutes, not seconds

RUNBOOK = "docs/knowledge/15-build-packet-runbook.md"

# D25. Claude Code reports these on STDOUT, mixed into ordinary output.
USAGE_LIMIT_RE = re.compile(
    r"hit your (session|usage) limit|monthly spend limit|rate.?limit", re.IGNORECASE
)
LIMIT_LINE_RE = re.compile(r".*hit your.*limit[^\r\n]*", re.IGNORECASE)


class UsageLimitHit(RuntimeError):
    """Claude Code refused because of a quota. NOT this job's fault — stop the whole batch.

    Callers must not record the job as failed. It will build fine after the limit resets.
    """


class PacketBuildFailed(RuntimeError):
    """This job genuinely failed. Safe to record against the job."""


@dataclass(frozen=True)
class Packet:
    slug: str
    company: str
    role: str
    cv_stem: str
    ats: int | None
    job_id: str
    path: Path
    # Set when the build SUCCEEDED but a usage-limit message also appeared — i.e. the limit was
    # reached at the end. This job is fine; the next one will not be. Stops the batch without
    # discarding work that actually completed.
    limit_notice: str | None = None

    @property
    def pdf(self) -> Path:
        return PDF_DIR / f"{self.cv_stem}.pdf"

    def complete(self) -> bool:
        """A packet without its PDF is half-built (runbook §4) and cannot be attached."""
        return self.pdf.exists()


def slugify(text: str) -> str:
    """Folder-name form: hyphenated, readable on disk."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def _key(text: str) -> str:
    """Comparison form: alphanumerics only.

    NOT slugify(). "SkillsCapital" and "Skills Capital" are the same employer but slugify makes
    them `skillscapital` and `skills-capital`, which compare unequal — and an unequal compare here
    means a tailored CV is not found and the family CV goes out instead. Same normalisation the
    ledger uses for exactly the same reason.
    """
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def company_slug(company: str) -> str:
    """The folder that owns a company's OUTREACH — contact.md and the messages."""
    return slugify(company)


def packet_dir_for(company: str, role: str, outreach_dir: Path | None = None) -> Path:
    """Where THIS ROLE's packet lives (D34).

    The two units were conflated. Outreach is per **company** — D8 says messaging the same
    recruiter twice is the fastest way to look automated, so `contact.md` and the touch messages
    stay in one folder per company. But a **CV is per role**: a CV tailored to an AI Application
    Engineer req must never be attached to a Junior AI Engineer one.

    So the first role a company gets keeps the plain company folder (nothing moves, no existing
    packet is disturbed), and every subsequent role gets `<company>--<role>`, which reuses the
    company's `contact.md` rather than re-researching the recruiter.
    """
    root = outreach_dir if outreach_dir is not None else OUTREACH_DIR
    base = root / company_slug(company)
    existing = base / "packet.json"
    if not existing.exists():
        return base

    # If the company folder already holds THIS role, that IS this role's home. Returning a new
    # `<company>--<role>` path would split one role across two folders and quietly orphan the
    # first. build_packet short-circuits before reaching here, but this function is public and
    # must be correct on its own.
    try:
        data = json.loads(existing.read_text(encoding="utf-8"))
        if _key(data.get("role", "")) == _key(role) and _key(data.get("company", "")) == _key(company):
            return base
    except (OSError, json.JSONDecodeError):
        pass  # unreadable: treat as occupied, and give this role its own folder

    return root / f"{company_slug(company)}--{slugify(role)}"


def find_role_packet(company: str, role: str, outreach_dir: Path | None = None) -> Packet | None:
    """A packet already built for this exact company AND role, wherever it lives."""
    root = outreach_dir if outreach_dir is not None else OUTREACH_DIR
    want = (_key(company), _key(role))
    for candidate in sorted(root.glob("*/packet.json")):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (_key(data.get("company", "")), _key(data.get("role", ""))) == want:
            try:
                return _to_packet(data, candidate)
            except PacketBuildFailed:
                return None
    return None


def find_company_packet(company: str, outreach_dir: Path | None = None) -> Packet | None:
    """Any packet already built for this COMPANY, whatever role it was for.

    Kept because it is still the thing that tells a caller "this company already has outreach,
    reuse its contact.md instead of re-researching the recruiter". It is no longer a blocker:
    before D34 a hit here meant the build could never succeed, because the runbook refused to
    overwrite `output/outreach/<slug>/` while `find_packet` looked up by job id and saw nothing.
    That deadlock cost Infosys AI/ML Engineer (08-09) and Junior AI Engineer, fit 90 (08-10).
    """
    slug = company_slug(company)
    if not slug:
        return None
    candidate = OUTREACH_DIR.joinpath(slug, "packet.json") if outreach_dir is None else \
        outreach_dir.joinpath(slug, "packet.json")
    if not candidate.exists():
        return None
    try:
        return _to_packet(json.loads(candidate.read_text(encoding="utf-8")), candidate)
    except (OSError, json.JSONDecodeError, PacketBuildFailed):
        return None


def find_packet(job_id: str) -> Packet | None:
    """Locate an already-built packet by job id. Packets are discovered, never hardcoded.

    Hardcoding the list is how a new packet stayed invisible until someone edited the server
    (2026-07-26). Scan the directory instead.
    """
    for candidate in sorted(OUTREACH_DIR.glob("*/packet.json")):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("job_id", "")).strip() == str(job_id).strip():
            return _to_packet(data, candidate)
    return None


def _to_packet(data: dict, path: Path) -> Packet:
    missing = [k for k in ("slug", "cv_stem") if not data.get(k)]
    if missing:
        raise PacketBuildFailed(f"{path} is missing required field(s): {', '.join(missing)}")
    return Packet(
        slug=data["slug"],
        company=data.get("company", "?"),
        role=data.get("role", "?"),
        cv_stem=data["cv_stem"],
        ats=data.get("ats"),
        job_id=str(data.get("job_id", "")),
        path=path,
    )


def build_packet(
    job_id: str, timeout: int = DEFAULT_TIMEOUT, force: bool = False,
    company: str = "", role: str = "",
) -> Packet:
    """Run Claude Code against the packet runbook for one job. Sends nothing.

    Raises UsageLimitHit (stop the batch, blame nobody) or PacketBuildFailed (this job).
    """
    existing = find_packet(job_id)
    if existing and not force:
        return existing  # runbook §2: rebuilding silently overwrites approved drafts

    # D34. A company's SECOND role used to be unbuildable forever: the runbook refuses to
    # overwrite output/outreach/<company>/, and find_packet looks up by job id, so the two could
    # never agree. Now the role gets its own folder and REUSES the company's existing contact.md,
    # which keeps D8 intact (one recruiter per company) while letting the CV be per role.
    prompt = f"Read {RUNBOOK} and follow it for job id {job_id}. Send nothing."

    if company and role:
        existing = find_role_packet(company, role)
        if existing and not force:
            return existing  # this exact role is already done

        target = packet_dir_for(company, role)
        sibling = find_company_packet(company)
        if sibling and target.name != company_slug(company):
            prompt = (
                f"Read {RUNBOOK} and follow it for job id {job_id}. Send nothing.\n\n"
                f"IMPORTANT - this is {company}'s SECOND role, so the usual one-packet-per-company "
                f"rule needs adjusting for this build:\n"
                f"- Write this packet to `output/outreach/{target.name}/`, NOT to "
                f"`output/outreach/{company_slug(company)}/`. Do not overwrite or modify the "
                f"existing packet there.\n"
                f"- REUSE the recruiter already researched in "
                f"`output/outreach/{company_slug(company)}/contact.md`. Do NOT research a new "
                f"contact and do NOT message a second person at this company (D8).\n"
                f"- The CV must be tailored to THIS role ({role!r}) and needs its own distinct "
                f"cv_stem. The existing stem {sibling.cv_stem!r} belongs to {sibling.role!r} and "
                f"must not be reused.\n"
                f"- packet.json must record company={company!r} and role={role!r} exactly."
            )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise PacketBuildFailed(
            "the `claude` CLI is not on PATH. cv.py drives Claude Code as a subprocess; "
            "install/expose the CLI or run the build from the dashboard."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise PacketBuildFailed(f"packet build for {job_id} exceeded {timeout}s") from exc

    # Claude Code prints its errors to STDOUT, not stderr. Read both, always.
    blob = f"{result.stdout or ''}\n{result.stderr or ''}"
    limit_match = LIMIT_LINE_RE.search(blob) if USAGE_LIMIT_RE.search(blob) else None
    limit_text = limit_match.group(0).strip() if limit_match else "usage limit reported"

    # THE ARTIFACT IS CHECKED FIRST, BEFORE ANY MESSAGE IN THE LOG.
    #
    # Learned the hard way 2026-08-06, on this very function's first real run. The Energy
    # Exemplar packet built completely — packet.json, a 105KB tailored PDF, four outreach
    # documents — and Claude Code hit its session limit immediately AFTER finishing. Because
    # the limit check ran first, cv.py threw UsageLimitHit and reported the job as untouched
    # while the finished work sat on disk.
    #
    # That is precisely the mistake D30 names: a string in a log outranked an artifact on
    # disk. D25 is still right that a limit must never be filed as a per-job FAILURE — but a
    # limit is also not a reason to disown work that demonstrably completed.
    packet = find_packet(job_id)
    if packet is not None and packet.complete():
        return replace(packet, limit_notice=limit_text) if limit_match else packet

    # No usable artifact. NOW the log gets to explain why.
    if limit_match:
        raise UsageLimitHit(
            f"Claude usage limit — NOT a problem with job {job_id}: {limit_text}"
        )

    if result.returncode != 0:
        raise PacketBuildFailed(
            f"claude exited {result.returncode} for job {job_id}\n"
            f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"
        )
    if packet is None:
        raise PacketBuildFailed(
            f"claude exited 0 but wrote no packet.json for job {job_id}\n"
            f"--- STDOUT ---\n{result.stdout[-2000:]}"
        )
    raise PacketBuildFailed(
        f"packet {packet.slug} exists but its PDF is missing: {packet.pdf}\n"
        f"A packet without a PDF is half-built (runbook §4) and cannot be attached."
    )


def build_many(
    job_ids: list[str],
    timeout: int = DEFAULT_TIMEOUT,
    companies: dict[str, str] | None = None,
    roles: dict[str, str] | None = None,
) -> tuple[list[Packet], list[tuple[str, str]], str | None]:
    """Build several packets. Returns (built, [(job_id, error)], usage_limit_message).

    On a usage limit the batch STOPS and the remaining jobs are left untouched — they are not
    failures and must not be recorded as any.
    """
    built: list[Packet] = []
    failed: list[tuple[str, str]] = []
    for job_id in job_ids:
        try:
            packet = build_packet(
                job_id, timeout=timeout,
                company=(companies or {}).get(job_id, ""),
                role=(roles or {}).get(job_id, ""),
            )
        except UsageLimitHit as exc:
            return built, failed, str(exc)
        except PacketBuildFailed as exc:
            failed.append((job_id, str(exc)))
            continue

        built.append(packet)
        if packet.limit_notice:
            # This one finished; the limit landed at the end. Keep the success, stop the batch.
            return built, failed, (
                f"Claude usage limit reached AFTER {packet.slug} completed "
                f"(that packet is good): {packet.limit_notice}"
            )
    return built, failed, None
