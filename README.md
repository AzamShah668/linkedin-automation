# Job Hunt Autopilot

An AI-driven job-application pipeline: discover roles → research the company → tailor a CV → draft
outreach → apply → track → follow up. Built and run in production by one person on a real job hunt,
with the reasoning at every step written down as it happened.

**The knowledge base is the point of this repo.** `docs/knowledge/` holds 22 documents and 28 logged
decisions covering six weeks of things that broke in production and why. The code is the smaller half.

---

## ⚠️ Read this first — the project is mid-rewrite

| | |
|---|---|
| **What works today** | The full pipeline. 94 jobs discovered, 7 application packets built, 5 applications submitted, 3 recruiter pitches delivered. |
| **What is being replaced** | The **runtime**. Not the logic, not the knowledge, not the skills. |
| **Decided** | 2026-08-06 |
| **Status** | Documented. `apps/autopilot/` is **not written yet.** Phase 0 is the next code task. |

### The problem

**We used Claude Code — an interactive IDE tool — as the production runtime.**

Every pipeline step spawns a whole Claude Code session, which reads a Markdown runbook and makes ~20
MCP calls to do work that is ~90% identical every time.

That one choice caused almost every bug in the decision log:

| What we logged | What it actually was |
|---|---|
| "One PowerShell layer too many kills headless Claude" (D24) | A **Claude session limit** (D25). A coding agent has quotas; a server does not. |
| Four LinkedIn MCP servers fighting over one browser profile (D13) | An interactive tool assumes **one user at one keyboard** |
| Five missed tasks all firing within three seconds on wake (D20) | Task Scheduler is **not a job queue** |
| One `hasTrustDialogAccepted` boolean silently voiding 55 permissions (D17) | A permission model built for **a human approver who is present** |
| 16 minutes to build one application packet | A full agent loop for work that is mostly **templating** |

### The solution

> **Anything that is the same every time → code.**
> **Anything that is different every time → AI.**

A LinkedIn Easy Apply form has 20 fields. Nineteen are a dictionary lookup — name, email, phone,
notice period, expected salary, résumé upload. **One** needs a model: *"Why do you want to join us?"*

Today an agent does all twenty, for sixteen minutes. The rewrite gives it field 20 and nothing else.

**The new shape** — same components, opposite direction:

```
BEFORE   Task Scheduler → PowerShell → Claude Code → does everything

AFTER    Python orchestrator → does everything
              ├── free model (OpenRouter) → fit scoring, the one odd form question
              ├── plain code              → discovery, form filling, tracking, submitting
              └── Claude Code (subprocess) → the tailored CV      ⭐ once per company
```

**Why the CV keeps a full agent:** it happens once per *company*, a *human recruiter* reads it, it is
not latency-sensitive, and it needs judgment — read the job description, check the profile for
evidence, refuse to fabricate. Low frequency + high stakes + not urgent is exactly where a slow,
careful tool belongs.

**Result:** 10 applications in ~7 minutes instead of ~2.5 hours, at **₹0/day** to run.

Full reasoning: **[`docs/knowledge/22-rewrite-architecture.md`](docs/knowledge/22-rewrite-architecture.md)**

---

## Orientation — read in this order

Whether you are a person or an AI picking this up cold, this is the whole tour in ~15 minutes.

| # | File | What you get |
|---|---|---|
| 1 | This README | What the project is and where it is going |
| 2 | [`CLAUDE.md`](CLAUDE.md) | Operating rules, conventions, dated project history |
| 3 | [`docs/knowledge/00-INDEX.md`](docs/knowledge/00-INDEX.md) | Map of the knowledge base |
| 4 | [`docs/knowledge/07-current-state.md`](docs/knowledge/07-current-state.md) | **What actually exists right now** — the honest snapshot |
| 5 | [`docs/knowledge/22-rewrite-architecture.md`](docs/knowledge/22-rewrite-architecture.md) | **Where it is going and why** |
| 6 | [`docs/knowledge/05-decisions.md`](docs/knowledge/05-decisions.md) | 28 decisions with the reasoning. The most valuable file here. |

**Do not skip #4.** This project has twice nearly rebuilt something that already existed, because the
work lived in a connected service (Notion, an MCP server) and was recorded nowhere. `07-current-state.md`
exists specifically to stop that. *If it is not written down, it does not exist.*

---

## Layout

```
docs/knowledge/     ⭐ 22 documents — the why. Decisions, runbooks, post-mortems.
.claude/skills/        cv-architect (CV/cover-letter engine) · recruiter-outreach (dual-touch drafts)
tools/                 17 Python + 9 PowerShell modules — the current pipeline
web/                   local dashboard (6 pages + JS)
graphify-out/          auto-generated code-structure graph (git hooks keep it fresh)
profile/               ⛔ gitignored — personal dossier + the answer bank (template included)
output/                ⛔ gitignored — generated CVs, recruiter contacts, application logs
apps/autopilot/        🔜 the rewrite. Not built yet.
```

### Key modules today

| File | Job |
|---|---|
| `tools/board_db.py` | Local SQLite mirror of the job board |
| `tools/invite_tracker.py` | Two-stage LinkedIn outreach state |
| `tools/notion_push.py` | Push local status → Notion |
| `tools/serve_dashboard.py` | Local dashboard server with runner actions |
| `tools/pipeline-lock.ps1` | Atomic cross-process lock (debugged in production — see D20) |
| `tools/sweep-packets.ps1` | Batch packet builder, with usage-limit detection (D25) |

---

## Setup

```bash
git clone https://github.com/AzamShah668/linkedin-automation.git
cd linkedin-automation

cp .env.example .env          # then fill in your own keys
cp profile/application-answers.example.json profile/application-answers.json

py -3 scripts/setup-hooks.py  # required on a fresh clone — see below
```

### Why `setup-hooks.py` is a required step

`.git/hooks/` is not version-controlled, so the knowledge graph's auto-rebuild hooks do not
survive a clone. The default installer also picks its interpreter with `command -v python3`,
which on Windows finds the **Windows Store App Execution Alias stub** — a real executable with no
site-packages. Every commit then fails with `No module named 'graphify'` while
`graphify hook status` reports the hooks installed. Both statements are true; they describe
different shells. That went unnoticed for eleven days.

```bash
py -3 scripts/setup-hooks.py           # install / repair
py -3 scripts/setup-hooks.py --check   # verify, non-zero exit if broken
```

Verify by committing and checking `graphify-out/graph.json`'s mtime. **Judge it by the artifact,
never by a status line** — that is decision D17, and it applies to the tooling too.

You will also need to create `profile/master-profile.md` and `profile/projects-catalog.md` — see
[`profile/README.md`](profile/README.md) for what goes in them.

**Requirements:** Python 3 (`py -3` on Windows), Claude Code CLI, and the connectors you want
(Notion, Slack, Gmail). Everything is optional — the pipeline degrades to local files without them.

---

## What is **not** in this repo, and why

This repository is public. Two directories are deliberately gitignored:

- **`output/`** — generated CVs, cover letters, recruiter contact cards, application logs, screenshots
- **`profile/`** — the owner's personal dossier and the filled-in answer bank (DOB, phone, salary)

**Real recruiters appear nowhere in this repo.** People who received an application or a message are
referred to as `Recruiter-A`, `Recruiter-B`, `Recruiter-C` throughout the knowledge base. They are
private individuals who never agreed to appear in a public repository, and the stories in the decision
log work perfectly well without their names.

> **If you contribute or extend this: never commit a real third party's name, email, or LinkedIn URL.**

---

## The rules this project runs on

Learned the hard way. Each maps to a decision in `05-decisions.md`.

1. **Quality + human-approved outreach beats mass automation.** LinkedIn's User Agreement forbids bots
   and automated messaging; violating it gets accounts permanently restricted. Jobs come from
   legitimate sources; every message is tailored; throttled, capped, randomized. *(D1, D2)*
2. **Never invent a value on a real employer's form.** The answer bank is the only legal source. A
   `null` means *leave the field blank and report it*. **Blank beats wrong. Skip beats invent.** *(D15)*
3. **No fabrication in a generated CV.** Every claim traces to a recorded fact. Reframe honestly;
   never invent. *(D5)*
4. **Judge every automated run by its log, never its exit code.** A task exiting 0 proves nothing —
   this bit three separate ways in a single day. *(D17)*
5. **Cheap, boring explanations before clever structural ones.** When several unrelated things fail at
   once, check the shared resource — a usage limit, a lock, a battery setting — before theorising.
   We spent a day on process trees for what a log line called a session limit. *(D24 → D25)*
6. **If it is not in a brain, it does not exist.** Work done through a connected service is invisible
   to the next session unless it is written into `docs/knowledge/`. *(D7)*

---

## Status

| | |
|---|---|
| Jobs discovered | 94 |
| Application packets built | 7 |
| Applications submitted | 5 |
| Recruiter pitches delivered | 3 |
| Interviews | 0 — replies still outstanding |
| Cost to run | ₹0/day |

Honest read: **the pipeline works and the outcome has not landed yet.** The rewrite is about making
each application cost minutes instead of hours, so the volume can go up without the quality going down.

---

## License & intent

Built as a personal job-hunt tool and a working study in agent architecture — specifically, in learning
the difference between *using an agent* and *building on one*. If the decision log saves you a day of
debugging, it has done its job.
