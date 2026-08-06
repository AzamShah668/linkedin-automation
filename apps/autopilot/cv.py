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
from dataclasses import dataclass
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

    @property
    def pdf(self) -> Path:
        return PDF_DIR / f"{self.cv_stem}.pdf"


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


def build_packet(job_id: str, timeout: int = DEFAULT_TIMEOUT, force: bool = False) -> Packet:
    """Run Claude Code against the packet runbook for one job. Sends nothing.

    Raises UsageLimitHit (stop the batch, blame nobody) or PacketBuildFailed (this job).
    """
    existing = find_packet(job_id)
    if existing and not force:
        return existing  # runbook §2: rebuilding silently overwrites approved drafts

    prompt = (
        f"Read {RUNBOOK} and follow it for job id {job_id}. Send nothing."
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

    # D25 BEFORE the returncode check: a usage limit can surface with either exit code, and
    # misfiling it as a per-job failure is the expensive mistake.
    if USAGE_LIMIT_RE.search(blob):
        line = LIMIT_LINE_RE.search(blob)
        raise UsageLimitHit(
            f"Claude usage limit — NOT a problem with job {job_id}: "
            f"{line.group(0).strip() if line else 'limit message in output'}"
        )

    if result.returncode != 0:
        raise PacketBuildFailed(
            f"claude exited {result.returncode} for job {job_id}\n"
            f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"
        )

    # D17: exit 0 proves nothing. The artifact is the verdict.
    packet = find_packet(job_id)
    if packet is None:
        raise PacketBuildFailed(
            f"claude exited 0 but wrote no packet.json for job {job_id}\n"
            f"--- STDOUT ---\n{result.stdout[-2000:]}"
        )
    if not packet.pdf.exists():
        raise PacketBuildFailed(
            f"packet {packet.slug} exists but its PDF is missing: {packet.pdf}\n"
            f"A packet without a PDF is half-built (runbook §4) and cannot be attached."
        )
    return packet


def build_many(job_ids: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[list[Packet], list[tuple[str, str]], str | None]:
    """Build several packets. Returns (built, [(job_id, error)], usage_limit_message).

    On a usage limit the batch STOPS and the remaining jobs are left untouched — they are not
    failures and must not be recorded as any.
    """
    built: list[Packet] = []
    failed: list[tuple[str, str]] = []
    for job_id in job_ids:
        try:
            built.append(build_packet(job_id, timeout=timeout))
        except UsageLimitHit as exc:
            return built, failed, str(exc)
        except PacketBuildFailed as exc:
            failed.append((job_id, str(exc)))
    return built, failed, None
