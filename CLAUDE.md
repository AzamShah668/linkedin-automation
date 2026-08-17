# CLAUDE.md — Job Hunt Autopilot (LinkedIn Automation)

> Local project instructions. This is a **living document** — update it as the project grows.
> Global rules in `~/.claude/CLAUDE.md` (Three Brains, coding style, security) still apply on top of this.

## What this project is

An AI-driven job-application pipeline for the owner (Azam). Goal: get **interviews in days, not weeks**
by automating discovery → research → tailoring → outreach → tracking, while a human stays the final "send" button.

Owner's 6-step vision:
1. Find companies that are actively hiring
2. Store them
3. Process one-by-one
4. Focus on the ones genuinely recruiting
5. Research each company deeply
6. Tailor the CV per company so they're likely to invite an interview

Plus: **Slack notifications** for every event, and a **separate recruiter-facing "highlight reel"**
message that leads with quantified achievements (distinct from the formal CV).

## ⚠️ ARCHITECTURE DECISION 2026-08-06 — read `docs/knowledge/22-rewrite-architecture.md` first

The pipeline described in this file **works and still runs**, but the runtime is being replaced.

**The problem:** we used Claude Code — an interactive IDE tool — as the production runtime. Every step
spawns a full agent session to read a Markdown runbook and make ~20 MCP calls, for work that is ~90%
identical every time. That single choice caused D13, D17, D20, D24 and D25.

**The fix:** a Python program (`apps/autopilot/`) runs the pipeline. It calls a **free model** for the
few genuinely variable bits, and **Claude Code** as a subprocess for the one artifact a human reads —
the tailored CV. Cost to run: ₹0/day.

**The rule:** *anything that is the same every time → code; anything different every time → AI.*
A LinkedIn Easy Apply form is 19 dictionary lookups and one real question. Today an agent does all 20.

- Plan: `docs/knowledge/22-rewrite-architecture.md`
- Decisions: `docs/knowledge/05-decisions.md` **D26, D27, D28**
- Status: Phase 0 **written and run** (2026-08-06) — see `docs/knowledge/23-phase-0-results.md`. Not yet closed: needs one clean 5-fill run.
- **Do not add features to the PowerShell + scheduled-task stack.** Fix bugs there; build new work in `apps/`.

## The one rule that shapes everything (READ THIS FIRST)

**Quality + human-approved outreach beats mass automation — and won't get the LinkedIn account banned.**

- LinkedIn's User Agreement forbids bots, scraping, and automated DMs. Headless scraping and bulk
  auto-messaging get accounts *restricted or permanently banned*, and recruiters ignore/flag generic spam.
- So we automate ~90% (find, research, write) and keep a **human-in-the-loop review queue** for sending.
- We pull jobs from **legitimate sources** (ATS public job APIs, job-board APIs, parsed LinkedIn email
  alerts via the connected Gmail) — never headless LinkedIn scraping.
- We prefer **email outreach** (Gmail API, already connected) over LinkedIn DMs for delivering the CV.
- Throttle everything, randomized delays, daily caps, personalize every message.

This is not just compliance — tailored + timely + personal is the approach that *actually* gets interviews.

## Stack

**How it runs TODAY (MCP-first, no custom code yet — decision D7):**
- **Discovery:** LinkedIn MCP (`search_jobs` / `search_people` / `get_company_employees`, read-only)
- **Job store:** **Notion** database "Job Hunt — Autopilot" (not SQLite) — the real store, query via Notion MCP
- **Outreach delivery:** Gmail MCP · **Notifications:** Slack ✅ connected (channel `C0AN5ASHZB6`, bot token in `.env`)
- **CV + outreach:** two Claude skills — see "The CV engine" + `recruiter-outreach` — output to `output/`
- Full live snapshot: `docs/knowledge/07-current-state.md` (read it 2nd each session)

**Planned CODED system (later automation, not built yet):**
- Python 3 (`py -3`); Claude API (`claude-fable-5` / `claude-sonnet-5`); SQLite → Postgres
- Source adapters: Greenhouse / Lever / Ashby / Workable / SmartRecruiters; Adzuna / Reed / Remotive /
  Arbeitnow; Gmail LinkedIn-alert parser; careers RSS · CLI → FastAPI review dashboard

## Repo layout (restructured 2026-08-11 — see [[28-app-structure]])

```
frontend/   the dashboard pages + static/ (plain HTML/CSS/vanilla JS, no build step)
backend/    server.py (the local HTTP API) + pipeline_runner.py
database/   board_db.py (schema + access) + board.sqlite3 (GITIGNORED — real recruiter names)
apps/       the autopilot: answers, fill, cv, families, ledger, sourcing, coverage, replies, triage
tools/      PowerShell runners, Slack, Notion, post creator — everything else
```

⚠️ **`tools/board_db.py` and `tools/serve_dashboard.py` are SHIMS, not dead files.** Sixteen
callers import `board_db` by name — three of them PowerShell scripts run by Task Scheduler. The
shim must load the real module **by file path**; both files share a name, so a plain import
re-imports the shim and dies on a circular import. Delete only when grep comes back clean.

⚠️ **`database/*.sqlite3` is gitignored on purpose.** The `notes` column holds real recruiter names
on 17 rows and this repo is public. Schema tracked, data not.

Start the dashboard with `dashboard.cmd`. **The console IS the home page** and it is **live** —
it polls every 15s, pauses in a hidden tab, and shows a **per-source** freshness strip (board /
triage / ledger / invites) because those four update on completely different clocks. A stale source
turns amber and offers the button that fixes it.

**Four pages, down from seven** (2026-08-11): Console, Jobs & CV, Downloads, Run it. Deleted the old
Board index (its live table moved onto the console; it only *looked* stale because it stamped
"board synced Xd ago", which describes the last Notion capture and nothing else), Research (files
5-17 days stale) and Slack (a 16-day-old mirror of an app already on the phone). **Actions cut
16 → 11** — `notion-push`/`notion-queue` could never work because **`NOTION_TOKEN` is not set**.

⚠️ **`database/board.sqlite3` is the real store.** With no Notion token nothing pushes back;
`apps/autopilot` plans from the local DB. `sync-board` is the only inbound path.

## Three Brains integration (per global CLAUDE.md)

- **Brain 2** (the *why*): `docs/knowledge/` — read `00-INDEX.md` first every session.
- **Brain 3** (the *how*): `graphify-out/` — ✅ **initialized 2026-07-26** (75 nodes, 125 edges, 14 communities
  from the 13 code files). Git hooks installed, so it refreshes itself on commit/checkout — never run
  `graphify . --update`. Query with **`py -3 -m graphify query "<question>" --budget 2000`** instead of
  reading `tools/` — ⚠️ a bare `graphify` is not on PATH and raises `CommandNotFoundException`.
  Built **AST-only on purpose**: the graph maps code structure; the markdown lives in Brain 2 and graphing it
  would duplicate. Append a line to `graphify-out/log.md` at the end of each session.
- **Brain 1** (global): Obsidian `Projects/LinkedIn-Automation.md`.

Retrieval order each session: **Brain 2 → Brain 3 → raw files.**

## Conventions

- Secrets in `.env` only — never hardcode (Claude / Gmail / Slack / job-board keys). See `.env.example`.
- Small files (<400 lines). One adapter per data source. Immutable data patterns.
- Every outreach message is tailored + logged; **nothing sends without approval**.
- Respect each API's ToS, robots.txt, and rate limits; randomized throttling + daily caps.
- Validate all external data (API responses, parsed emails) at the boundary.

## LinkedIn Content Hub (7-Day Content Engine)

**Built 2026-08-10.** A daily-posting content calendar: SQLite hub, experience logger, Hacker News
trend finder, and a dispatch engine that generates the image and the post together.

Full architecture, the 7-day calendar, the workflow and every command are in
**[[27-linkedin-content-engine]]** (`docs/knowledge/27-linkedin-content-engine.md`). Start there:

```bash
py -3 tools/content_hub_db.py --stats     # what is queued
py -3 tools/scan_sessions.py              # mine all brains for post ideas
py -3 tools/post_creator/dispatch_engine.py --dry-run --post-id N
```

## Current status

> **📜 History lives in [[34-changelog]]** (`docs/knowledge/34-changelog.md`) — every dated
> entry from 2026-07-24 on. Only the three most recent are kept here, because this file is
> loaded at the start of *every* session and the older history is not needed to do today's
> work. Grep it when you need to know why something is the way it is.

- **2026-08-16 — ⚠️ THE APPROVAL GATE IS GONE. Read D48 before touching outreach or connect.**
  D12 ("nothing sends without a tick") governed this project from 2026-07-26. **Azam removed it
  himself**, explicitly: *"don't leave it up to Slack ... Whenever you find a connection just go for
  it ... just provide me with the details that you have done."* The risk was already on record from
  D47 and he reaffirmed it. It is his account. **Slack is now a receipt, not a request.**
  **`apps/autopilot/connect.py`** sends the bare request through the Playwright profile;
  `outreach.py` calls it, hands the invite to `watch-accepts`, and reports once per run.
  `--no-send` restores the old card-and-tick behaviour.
  ⚠️ **What still stands between this and an account restriction** — none of it a substitute for a
  human reading each name, and all of it now load-bearing: a **daily cap** from an append-only log
  (`LINKEDIN_CONNECTS_DAILY_CAP`, currently **5** — raise to ~10), a 45s+jitter throttle,
  **business hours only** (03:00 invites are a bot signal no cap disguises), **one request per
  person ever**, and **current-employees-only**, which is now the last check on who gets contacted.
  Guards fire *before* the browser opens, and a refusal is deliberately **not** logged — logging it
  would poison `already_requested()` and permanently skip someone never asked.
  🔴 **Three bugs, one good failure direction.** Connect is **not on the top card** (both live
  profiles offered only *Follow*; it lives in **More**). LinkedIn's **sticky nav eats the click** —
  Playwright scrolls the button under the fixed header and reports it *visible, enabled and stable*
  while `<nav> ... intercepts pointer events`; **`force=True` does not help**, force skips
  actionability, not an element on top. And the confirmation was **blind**:
  `get_by_role("button", name=/pending/)` never matches because LinkedIn renders the badge with an
  **empty aria-label** and "Pending" as text — a real send was reported as unconfirmed. That one
  failed *safe*; the same blindness in `_top_card_state` would have invited someone **twice**.
  🔴 **A transient `ERR_CONNECTION_CLOSED` aborted a whole batch** — `page.goto` sat outside the
  try, so every later company went unprocessed and the run died before its Slack report, leaving
  two real invites reported nowhere. Guarded per company; `connect_one` can no longer raise.
  ✅ **Five sent the first evening**, all confirmed by the Pending badge, all tracked for stage 2:
  TCS, BayOne Solutions, Berribot, Discovr AI, ANSR. **220 tests** (was 198).
  Still human: the nudges, and replying to people. **Do not reply to Showkat** (owner's instruction).

- **2026-08-17 — TWO STACKS NOW. Read [[33-omniroute-stack]] + D51 before touching `apps/autopilot/free/`.**
  Azam asked for the pipeline to run on OmniRoute free keys, then set the constraint: *"I don't want
  you to replace all this ... the previous one with the cloud agents should be there. It should not
  get deleted."* So it is **additive**:
  `pipeline.cmd` → Claude stack, **unchanged, still scheduled 10:30** ·
  `pipeline-free.cmd` → OmniRoute stack, **opt-in, unscheduled**.
  Proven untouched: `git diff rewrite/phase-0` for `run-pipeline.ps1`, `cv.py` and all six agent
  runners is **empty**; no `free/` module mentions `claude.exe`. Thirteen Claude-free modules are
  **shared**, not forked. Branches: Claude on `rewrite/phase-0`, free on `rewrite/omniroute-native`.
  **Built + verified live:** `env.py` · `free/discover.py` (**64 postings, 63 Easy Apply → 36 board
  rows**) · `free/cv.py` + `cv_validate.py` (**PASS in 2 attempts**; attempt 1 rejected for a
  fabricated 140,000) · `free/dm.py` · `free/gmail.py` · `run-pipeline-free.ps1`. **349 tests.**
  Certified tiers: `LLM_MODEL=gemini/gemini-3.5-flash-lite`, **`LLM_CV_MODEL=gemini/gemini-3.6-flash`**,
  fallback Groq direct — all three pass an exact echo in both transports.
  🔴 **`.env` was never loaded by anything.** `llm.py` read `os.getenv`; no loader existed and
  `python-dotenv` is not installed. `freetext.py` — which writes into **real employer forms** — was
  dead in every unattended run. `apps/autopilot/env.py` fixes it for **both** stacks.
  🔴 **Silent truncation:** `max_tokens=128` gave **0/4** exact echoes (`ALPHA 12345 OMEGA` →
  `ALPHA 12`), 512 gave 4/4 — the thinking pass shares the budget, HTTP 200 throughout. `ask()` now
  **raises** anything below `MIN_SAFE_MAX_TOKENS`.
  🔴 **A missing UTF-8 guard loaded zero of 36 rows.** `intake.py` crashed printing a job title,
  *before* the insert; the only symptom was a quiet `exit 1` inside a step marked "informational".
  The regression test then found **six more**, including `run.py`. **"Informational" must mean "this
  failing is fine", not "this fails a lot".**
  ⚠️ Also: a prompt only the primary can accept makes the fallback useless (Groq 413 at 14,463
  tokens vs 12,000); scroll the results **pane**, not the window (7 postings vs 40), and stop when
  the count stops growing rather than after N scrolls.
  ✅ **Gmail consent done 2026-08-17 10:48** (see the next entry). **Nothing on the free stack is
  scheduled**, by design.

- **2026-08-17 (later) — the pitch that never sent, and both inboxes now readable. Read D52 / D53
  + [[33-omniroute-stack]] §12.** The first full free run went 9/9 green, but `free/dm.py` had
  **nothing due**, so it had never once opened a message composer. *A step with no work is not a
  tested step* — the moment a real accept landed, two defects surfaced inside twenty minutes.
  🔴 **`Message` is an `<a>`, not a `<button>`.** `get_by_role("button", name=/^message/)` matched
  nothing on any profile ever, so **every** accept read `not-connected` — including SHALE FRANCIS,
  who had accepted 15 hours earlier. A negative from the wrong selector is byte-identical to a true
  one; the tracker disagreed, so the page was dumped instead of believed. ⚠️ **Fix it by getting
  MORE specific**: the right rail carries one `Message <Name>` link per suggested profile, so a
  widened regex opens a composer addressed to a **stranger** (D50's door again). Anchor on the name
  being exactly `Message`, then require every match to agree on the `recipient=` URN and refuse if
  they disagree. `Message with Premium` is InMail and spends a paid credit.
  🔴 **Then the first fix reported a send it had not made.** It printed *"sent, but could not read
  it back"*, counted it SENT and marked the tracker — reasoning that *between an unconfirmed
  delivery and a duplicate, the duplicate is worse*. True, and it assumed the click had worked. The
  inbox eight minutes later: **six conversations, newest a week old, no thread with him at all.**
  He was recorded as pitched and would never have been pitched again. Three causes: the read-back
  searched the **profile page body** instead of the thread; the composer was addressed **page-wide**
  (`get_by_role("textbox")` finds LinkedIn's global nav search field — everything is now scoped
  inside `.msg-form`); and the probe string was *"Hi Shale, thanks for connecting!"*, which is
  **LinkedIn's own canned suggestion**. The answer was never a better coin-flip — `send_dm` now
  checks the thread **before typing as well as after**, which is what makes it safe to call an
  unconfirmed send `UNVERIFIED`, leave it due and exit 2. ✅ Delivered 10:38 and verified from
  outside the tool: **7 conversations where there were 6**, sent exactly once.
  Also: `mark_sent()` was silent on a non-zero exit — the path where the message **already reached
  a real person** and was not recorded, so the next run sends it again. Loud now, with the by-hand
  remedy; the batch exits 2 if anything went unrecorded.
  ✅ **Gmail is live** (D53). `--authorize` used to dead-end at *"no OAuth client JSON"* while
  **five Desktop clients** sat in `~/Downloads`. ⚠️ **The Gmail API is enabled per Google Cloud
  project**, so a borrowed client consents perfectly and then 403s forever — a token on disk proves
  a click and nothing about a readable inbox, which is D35 in new paperwork. Setup now ends with a
  real `getProfile` and **deletes the token** if that fails. Project **569148103391** was chosen
  because `Desktop\my assistant` holds a live `gmail.modify` token on it; ours asks
  `gmail.readonly` only. ⚠️ Its first read called **15 of 40 messages "a person"** (Twilio, Ollama,
  a beehiiv blast, LinkedIn invite mail) — *a card with 15 items is a card you stop opening, which
  is how the 16-day reply happened.* Filter is **`List-Unsubscribe`**, not keywords, plus LinkedIn's
  notifier addresses (already read at source). Bulk is **counted and printed, never discarded**.
  Live: **15 → 3 worth a look, 12 bulk, 25 auto-ack**; the 3 are Talent500 assessment mails with a
  24-hour clock. 🔢 **405 tests** (was 349). Claude-stack diff vs `rewrite/phase-0`: still empty.

- **NEXT — in this order. The reordering fact is now: 14 applications, 1 reply, and the reply came from
  the only warm-insider approach the project has made.**
  1. 🔴 **Answer Recruiter-A** — 16 days late, on a personal phone number. **Only the owner can do this**;
     the project deliberately does not automate WhatsApp. It is the warmest lead in the project, inside the
     company that also holds the board's best unworked row.
  2. 🔴 **Build the warm-insider finder.** Accepts are not the bottleneck — 3 of 3 older invites were
     accepted, including two cold ones. **Conversion is**: accept→reply is 1 of 3, and the 1 was the warm
     one (shared region + mutual connections). D8 says warm-first but it has only ever been done by hand.
     ⏳ Blocked while the LinkedIn MCP is disconnected; it needs read-only people search.
  3. 🟡 **Recro** — the one application that reached nobody, 13 days silent. Also needs people search.
  4. 🟡 **Infosys Junior AI Engineer (90)** — now buildable (D34). Note it is **not Easy Apply**
     ("Responses managed off LinkedIn"), so the packet's value is a CV the insider can pass on, not an
     auto-submission.
  5. ⏸️ **Phase 1 (own the data) and multi-platform (Naukri) are both still NOT next.** Naukri is worth
     doing later as a **profile/inbound** play — recruiters search that resume database — not as bulk
     applying, which is a known account-restriction vector.

  Also still true: **re-score before building** any packet — the 38 newest rows were scored from title only,
  no JD fetched. And the **re-scan-after-numeric-validation** branch has still never executed, so the first
  `stalled-validation` report should be distrusted and its screenshot read.

## The CV engine (cv-architect)

The reusable résumé builder. Positioning for Azam: **DevOps Engineer · Platform & MLOps**. It mines the
verified `achievement-bank.md`, tailors per job, and emits three grounded artifacts (tailored CV, cover
letter, recruiter Highlight Reel). Reframes off-target work honestly (e.g. the YouTube/football pipelines
→ "fault-tolerant, self-healing automation with CI/CD quality gates and GPU orchestration").

## Inputs from the owner — ✅ ALL PROVIDED (2026-07-25)

1. ✅ Master CV → `.claude/skills/cv-architect/references/master-cv.md` + profile `linkedin.com/in/azam-shah-4ba6752ba`
2. ✅ Target roles → DevOps / Platform / MLOps / AI Engineer; India + Remote (see the 10 jobs in Notion)
3. ✅ Preferences → captured in `profile/master-profile.md`
4. ✅ Slack → bot token (reused from AXIOM) + channel `C0AN5ASHZB6`, in `.env`; live digest tested
5. ✅ Outreach email → `azamshah25809@gmail.com` (connected via Gmail MCP)
6. ✅ Priorities → highest-fit first; warm-intro companies first (Infosys, Oracle)

(Kept for the record; nothing outstanding. Current state + next steps live in `docs/knowledge/07-current-state.md`.)
