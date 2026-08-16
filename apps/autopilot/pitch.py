"""Write the message that gets sent when someone accepts.

WHY THIS EXISTS
---------------
`watch-accepts.ps1` delivers the pitch by sending the **exact `2b` text** from
`output/outreach/<slug>/touch-2-linkedin.md`, and it is forbidden from inventing one ("never invent
the pitch" — 13-accept-watch-runbook).

`outreach.py` wrote only `contact.md`. So when D48 made connecting automatic, every new invite was
heading for a dead end: **8 of 14 pending invites had no `touch-2-linkedin.md`**, and the first
person to accept — Shale Francis at Lotus Interworks, 2026-08-16 — would have been met with silence.

That is the exact failure this project has already paid for once (D35: a warm insider answered in
two hours and waited fifteen days). Getting an accept and having nothing to say is worse than not
having asked, because the other person has now done something and been ignored.

WHAT IT WILL NOT DO
-------------------
**It never invents a company detail.** A pitch is built from the role family, the verified
highlight reel, and the person's name — all of which we actually know. Nothing here claims to admire
a product, a funding round or a mission, because none of that has been researched. An invented
"I love what you're building" is the most obvious tell in a cold message, and the rule is that a
detail is either researched or absent.

So these are **honest but generic** pitches. A researched hook is strictly better, and
[[30-warm-insider-runbook]] plus the `recruiter-outreach` skill remain the way to produce one for a
company worth the effort. This guarantees a floor, not a ceiling.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from apps.autopilot import families
from apps.autopilot.answers import REPO

OUTREACH_DIR = REPO / "output" / "outreach"
INVITES_PATH = OUTREACH_DIR / "pending-invites.json"

CV_URL = "https://github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf"
GITHUB_URL = "github.com/AzamShah668"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# One opening per role family, lifted verbatim in substance from output/outreach/highlight-reel.md
# ("Win by role"). Every number is his own and backed by a public repo.
#
# ⚠️ NO EM-DASHES anywhere in these strings. An em-dash is the most recognisable AI tell in a
# message a recruiter reads, and two templates in this repo carried one undetected for weeks
# because no nudge had ever actually been rendered from real data.
OPENERS: dict[str, str] = {
    families.DEVOPS: (
        "production infrastructure I built and operate myself: a 7-service private cloud that goes "
        "from bare metal to running in one Ansible command with 98 passing tests, and a 2-node GPU "
        "Kubernetes cluster with a Jenkins quality gate that blocks bad deploys"
    ),
    families.AI_ML: (
        "production RAG with hybrid retrieval and an LLM-as-a-Judge CI gate, my own Claude agents "
        "and MCP servers, and I contribute to Everything Claude Code, a 140K-star open-source AI "
        "tooling project"
    ),
    families.GENERAL: (
        "18+ shipped projects where I own the whole stack, from the model and the pipeline through "
        "containers and CI/CD to the production box it lands on, plus 108 production Python tools "
        "across my own automation systems"
    ),
}

SECOND_LINE: dict[str, str] = {
    families.DEVOPS: (
        "Alongside that I build the AI systems that run on it, including production RAG and my own "
        "Claude agents, so I am comfortable on both sides of the handover."
    ),
    families.AI_ML: (
        "Most of it runs on infrastructure I built and operate myself, including a 2-node GPU "
        "Kubernetes cluster with a Jenkins quality gate, and 18+ shipped projects where I own the "
        "stack from the model through to the box it lands on."
    ),
    families.GENERAL: (
        "That includes a private cloud on Proxmox with 98 passing tests and production RAG running "
        "on GPU-scheduled Kubernetes, so the deployment side is not an afterthought for me."
    ),
}

_RELATIVE_TIME = re.compile(
    r"\b(yesterday|today|tomorrow|this morning|earlier|just now|last week|recently)\b", re.I)


def first_name(full_name: str) -> str:
    """"SHALE FRANCIS" -> "Shale". A shouted full name in a greeting reads as a mail merge."""
    cleaned = re.sub(r"\s*\(.*?\)\s*", " ", (full_name or "").strip())
    parts = [p for p in re.split(r"\s+", cleaned) if p]
    if not parts:
        return "there"
    first = parts[0]
    # ALL-CAPS or all-lower names are how LinkedIn stores plenty of profiles; title-case them
    # rather than greeting someone as "SHALE".
    return first if any(c.islower() for c in first) and first[0].isupper() else first.capitalize()


def message(person: str, company: str, role: str) -> str:
    """The exact 2b text. Deterministic: same inputs, same message, and it is testable."""
    family = families.family_for(role)
    opener = OPENERS.get(family, OPENERS[families.GENERAL])
    second = SECOND_LINE.get(family, SECOND_LINE[families.GENERAL])
    return "\n".join([
        f"Hi {first_name(person)}, thanks for connecting!",
        "",
        f"I applied for the {role} role at {company}, and it lines up closely with what I "
        f"actually build: {opener}.",
        "",
        second,
        "",
        "Happy to send a CV tailored to the role, or grab 15 minutes whenever suits you.",
        "",
        f"CV: {CV_URL}",
        f"GitHub: {GITHUB_URL}",
        "",
        "Cheers, Azam",
    ])


def document(person: str, company: str, role: str) -> str:
    body = message(person, company, role)
    quoted = "\n".join(f"> {line}" if line else ">" for line in body.split("\n"))
    family = families.family_for(role)
    return "\n".join([
        f"# Touch 2 — LinkedIn · {company} · {role}",
        "",
        f"- status:   READY TO SEND — generated by apps/autopilot/pitch.py",
        "- channel:  linkedin",
        "- send:     AUTO via the accept watcher (stage 2), on the randomised business-hours delay",
        f"- lead:     the {family} line from output/outreach/highlight-reel.md",
        "- research: ⚠️ NO verified company-specific hook. Nothing below claims anything about this",
        "            company's product, funding or mission, because none of it was researched. A",
        "            detail is either researched or absent; an invented one is the most obvious tell",
        "            in a cold pitch. A researched hook is strictly better — see",
        "            [[30-warm-insider-runbook]] for a company worth the effort.",
        "",
        "---",
        "",
        "## 2b — Direct message (1st degree / after they accept)",
        "",
        quoted,
        "",
        "---",
        "**Generated, not hand-written.** No em-dashes, no relative time words (D22: written now,",
        "sent hours later), OSS framed at project level per the highlight-reel guardrail, and every",
        "number already present in `highlight-reel.md` and backed by a public repo.",
        "",
    ])


def write(slug: str, person: str, company: str, role: str,
          outreach_dir: Path | None = None, overwrite: bool = False) -> tuple[Path, bool]:
    """(path, written). Never clobbers a hand-written or researched pitch unless told to."""
    outreach_dir = outreach_dir if outreach_dir is not None else OUTREACH_DIR
    path = outreach_dir / slug / "touch-2-linkedin.md"
    if path.exists() and not overwrite:
        return path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document(person, company, role), encoding="utf-8")
    return path, True


def _company_from_slug(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.split("-"))


def backfill(overwrite: bool = False) -> int:
    """Give every outstanding invite something to send."""
    if not INVITES_PATH.exists():
        print("no pending-invites.json")
        return 1
    data = json.loads(INVITES_PATH.read_text(encoding="utf-8"))
    made = 0
    for invite in data.get("invites", []):
        if invite.get("status") not in ("pending", "accepted"):
            continue
        slug = invite.get("slug", "")
        role = invite.get("role") or "the role"
        person = invite.get("person", "there")
        company = _company_from_slug(slug)
        path, written = write(slug, person, company, role, overwrite=overwrite)
        print(f"  {'WROTE ' if written else 'kept  '} {slug:<32} {role[:40]}")
        made += int(written)
    print(f"\n{made} pitch(es) written")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write the 2b pitch. Sends nothing.")
    ap.add_argument("--backfill", action="store_true",
                    help="write a pitch for every outstanding invite that lacks one")
    ap.add_argument("--overwrite", action="store_true", help="replace existing pitches")
    ap.add_argument("--show", nargs=3, metavar=("PERSON", "COMPANY", "ROLE"),
                    help="print the message that would be written")
    args = ap.parse_args(argv)

    if args.show:
        print(message(*args.show))
        return 0
    if args.backfill:
        return backfill(overwrite=args.overwrite)
    ap.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
