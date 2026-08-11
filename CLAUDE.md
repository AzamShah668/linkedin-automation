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
  `graphify . --update`. Query with `graphify query "<question>" --budget 2000` instead of reading `tools/`.
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

**Built 2026-08-10.** A full content calendar system for daily LinkedIn posting.

### Architecture
- **Content Hub DB**: `tools/content_hub_db.py` — SQLite store at `output/content_hub/content_hub.sqlite3`
- **Experience Logger**: `tools/log_experience.py` — logs pair-programming discoveries as post ideas
- **Trend Finder**: `tools/trend_finder.py` — fetches trending topics from Hacker News (free, no key)
- **Dispatch Engine**: `tools/post_creator/dispatch_engine.py` — unified orchestrator that generates images + posts
- **Image Prompt Templates**: `tools/post_creator/prompt_templates.json` — per-post-type visual styles
- **Fallback Cache**: `tools/post_creator/generate_fallback_cache.py` — pre-generated images for FLUX.1 downtime

### 7-Day Posting Calendar
| Day | Type | Visual |
|-----|------|--------|
| Mon | Daily Build Story | 1× FLUX.1 Hero Image |
| **Tue** | **Project Showcase** | **6-Page PDF Carousel** |
| Wed | Trending Tech Take | 1× FLUX.1 Infographic |
| **Thu** | **Project Showcase** | **6-Page PDF Carousel** |
| Fri | Engineering Lesson | 1× FLUX.1 Hero Image |
| Sat | Behind The Scenes | 1× FLUX.1 Scene |
| Sun | Tech Reflection | 1× FLUX.1 Concept Art |

### Workflow
1. **Log ideas**: `py -3 tools/log_experience.py --title "..." --insight "..." --type daily-build`
2. **Fetch trends**: `py -3 tools/trend_finder.py --count 3`
3. **Draft copy**: Agent rewrites idea into humanized copy (via `linkedin-post-copywriter` skill)
4. **Approve**: Human marks post as "approved" in the database
5. **Dispatch**: `py -3 tools/post_creator/dispatch_engine.py` (or scheduled task at 9 AM)
6. **Verify**: Post appears on LinkedIn with image

### Key Commands
```bash
py -3 tools/content_hub_db.py --stats          # hub statistics
py -3 tools/content_hub_db.py --list           # list all posts
py -3 tools/log_experience.py --list           # same as above
py -3 tools/trend_finder.py --dry-run          # preview trends
py -3 tools/scan_sessions.py                   # mine ALL brains for post ideas (Brain 1-3 + transcripts)
py -3 tools/scan_sessions.py --add             # mine + add top 10 to Content Hub
py -3 tools/scan_sessions.py --source claude   # mine only Claude session transcripts
py -3 tools/post_creator/dispatch_engine.py --dry-run --post-id N  # preview dispatch
```


## Current status

- **2026-07-24** — Project kicked off. Plan + Brain 2 knowledge base + this file created. Git initialized.
- **2026-07-24 (later)** — Built the **`cv-architect` skill** (`.claude/skills/cv-architect/`) — the `tailor/`
  engine. Rules: ATS ≥90, humanization (no AI-tells), zero fabrication, dual output (visual + ATS-plain).
  Produced Azam's DevOps CV from GitHub + the brains: `output/cv/azam-shah-devops-cv.{md,html}` +
  `achievement-bank.md`. Visual CV published as a private Artifact for preview/print.
- **2026-07-24 (later 2)** — Deep-researched the full portfolio → `profile/` dossier (20 projects, 4
  signature differentiators). Pushed two PUBLIC GitHub repos to make the CV verifiable:
  **github.com/AzamShah668/three-brain-knowledge-architecture** (the signature architecture, genericized)
  and **github.com/AzamShah668** (profile README landing page). No secrets/private repos were exposed.
- **2026-07-25** — Built the **`recruiter-outreach` skill** (`.claude/skills/recruiter-outreach/`) — the
  dual-touch engine: find recruiter (ban-safe ladder) → Touch 1 formal email + Touch 2 personal LinkedIn
  message (leads with Highlight Reel + one researched detail). Human-approval-gated review queue; LinkedIn
  MCP used to find+draft only, never to auto-send. Generated the base Highlight Reel
  (`output/outreach/highlight-reel.md`) + full drafts for the 3 tailored targets (Infosys 90, Innova ESI 87,
  GoodSpace 85) in `output/outreach/<slug>/` + `REVIEW-QUEUE.md`.
- **2026-07-25 (later)** — **LinkedIn MCP auth fixed** (recovery: `uvx mcp-server-linkedin@latest --status`
  once, then retry — see `docs/knowledge/07-current-state.md`). Ran `find-recruiter` live → **real named
  recruiters filled** for all 3: Infosys ⭐ Recruiter-A (warm, inside) + Recruiter-A2 (AI TA lead);
  Innova ESI Recruiter-B; GoodSpace founder Recruiter-C. Added the **warm-insider-first rule** (D8) to
  the outreach skill after Azam praised the "fellow Kashmiri inside Infosys" move.
- **2026-07-25 (docs sync)** — Reconciled ALL brains to reality: the pipeline runs **MCP-first**, the job
  store is a **Notion database ("Job Hunt — Autopilot") holding 10 scored jobs** (found via LinkedIn MCP) —
  NOT the planned SQLite. New Brain-2 file `docs/knowledge/07-current-state.md` is the mandatory live
  snapshot (read 2nd each session). Decisions D7 (MCP-first) + D8 (warm-insider-first) added. Near-miss
  logged: almost rebuilt the existing Notion store because it was recorded nowhere.
- **2026-07-26** — **Sending went live**, as a **two-stage play** (owner's design, decision D12). Stage 1: ✅ on a
  Slack card → a **bare** connection request (no note) → tracked in `output/outreach/pending-invites.json`.
  Stage 2: `tools/watch-accepts.ps1` polls every 4h, and once someone accepts it waits a random 3–20h
  (business hours) then **auto-sends the CV + full pitch**. New: `tools/invite_tracker.py`,
  `docs/knowledge/13-accept-watch-runbook.md`, `tools/install-watch-task.cmd`.
  Two blockers found and fixed: the Slack ✅ gate was dead (bot token had **write-only** scopes; the channel is
  **private**, so `groups:history` was the missing one), and `connect_with_person` **silently sends nothing**
  when a `note` is supplied while LinkedIn shows its quota banner — regardless of length. First real send:
  bare connect to **Recruiter-A** (Infosys warm insider), awaiting accept.
  ⚠️ Stage 2 is the **one** place a message goes out without a fresh human tick — the owner approves the
  *words* at stage 1, the robot only picks the *moment*. Capped at 3 follow-ups/run.
- **2026-07-26 (armed)** — owner said turn it on, so **all four scheduled tasks are now installed and running**:
  Daily Discovery, Reply Check, Flush Approved (every 30 min), Watch Accepts (every 4h). Both send tasks have
  cheap early-exit guards so idle cycles never wake a headless Claude. The flush uses a **timed** trigger, not
  `-AtLogOn` — the latter needs admin and fails with Access Denied.
- **2026-07-26 (first real sends + end-to-end audit)** — board is now **24 jobs**. Three bare connection
  requests sent: **Recruiter-A** (Infosys 90 ⭐warm) → **ACCEPTED**, pitch auto-scheduled 20:18;
  **Recruiter-B** (Innova ESI 87) and **Recruiter-C** (GoodSpace 85) still pending. Notion gained an
  `Invite sent` status between `To Apply` and `Applied`. Slack cards cut to ~5 lines + the exact 2b message in
  a code box. New tool `tools/slack_react.py`. Full audit found **six defects, five fixed** — see
  [[07-current-state]] and [[05-decisions]] D13. **Read those before touching the scheduler.** Headlines:
  every task was silently dead on **battery power**; the 📤 send-twice guard had **no tool behind it**; and
  MCP "session expired" errors were actually a **browser-profile lock**, not auth.
- **2026-07-26 (evening) — the Send Board + a three-hour false alarm.** Replaced the static control panel with a
  **live** dashboard: `output/dashboard/send-board.html` → private Artifact
  `claude.ai/code/artifact/8b4c38fe-afac-48c9-9d69-67a45420c8ec` (pass that `url` to republish, or the owner's
  link is orphaned). It reads Notion **at view time** through the Artifact `mcp` capability — no server, no
  stored token — and shows the four buckets the owner asked for: what needs his hands · invited-no-answer ·
  accepted-and-CV-sent (real timestamps) · **no CV out yet, grouped by company**. Phone layout included; a page
  declaring `mcp` **cannot be shared publicly**, but the owner can open it himself. Details:
  `docs/knowledge/14-send-board-dashboard.md` + D14. Trap that cost a publish cycle: a connector has **two
  names** — manifest takes `claude_ai_Notion`, the in-page call takes the display name `Notion`. Discover it
  with `listTools()`; never hardcode.
  Then: the 16:23 **"LinkedIn session expired" never happened.** Three `mcp-server-linkedin` servers were
  running (one per session opened that day), contending for one browser profile; the loser's empty browser was
  reported as dead auth. The owner disproved it: the CV was delivered at **16:43**, after the 16:23 "expiry".
  Cost: two pointless real logins by him, ~3 h across two sessions, and a wrong entry in this file. Now
  enforced by `tools/linkedin-doctor.cmd`. Read **D13 addendum** before touching LinkedIn auth.
- **2026-07-26 (night) — the dashboard can now CREATE, not just read.** Packets are **discovered** from
  `output/outreach/*/packet.json` instead of a hardcoded list in the server (a new packet used to be invisible
  until someone edited `serve_dashboard.py`). A role with no packet gets a **Build the CV + outreach packet**
  button → `tools/build-packet.ps1 -JobId <id>` → headless Claude against the new
  `docs/knowledge/15-build-packet-runbook.md` → CV + PDF + 4 documents + `packet.json` + Slack card, **sends
  nothing**. Runner actions can now take a validated parameter (`PARAM_PATTERN`; injection attempts refused
  server-side). Also on `/jobs`: mark-as-applied + **Push to Notion now** (`tools/notion_push.py`, needs
  `NOTION_TOKEN` in `.env` — otherwise it keeps the local side consistent and says Notion is waiting).
  **A build only runs with no other Claude window open** — its guard counts MCP servers, which is stricter
  than `watch-accepts.ps1` (that one only looked for an open Chromium and missed the common case).
- **⚠️ Operating constraint:** the tasks only do real work when **exactly one** MCP server exists — i.e. no
  other Claude Code session is open, *and* no stale server is left over from a closed one. Servers accumulate
  silently. Run `tools/linkedin-doctor.cmd` first; count `python.exe` only (one session = 1 server + 2 uvx
  wrappers, so counting the tree over-reports 3×). Say this plainly to the owner rather than implying it always
  runs. Fix pending: `--user-data-dir`. **Never diagnose auth from an MCP error message** — look for a
  successful action after the claimed failure time, then test with a real `get_my_profile` call.
- **2026-07-29 — full-autonomy attempt (GUI form filling).** Owner asked for the screen-control agent at
  `d:\New folder (2)\desktop-agent` to fill/submit application forms and drive LinkedIn itself.
  **Read [[16-gui-automation-investigation]] + D15 before touching any of this.** Headlines: free OpenRouter
  vision models score an effective **0/8** on the easiest GUI task; the cause is **raw pixel-coordinate
  guessing, not the model** (Claude missed the Start button by 328px too); **`USE_GROUNDING=true` fixes it**
  (numbered UIA elements → `click_element 7`, correct first try). Built `brains/claude_code_brain.py` (uses
  the CLI, no API key), `apply_to_job.py` (**fills, never submits**), `diagnose_brain.py`, and
  `profile/application-answers.json` — the **answer bank**, where 12 fields are deliberately null so the
  agent leaves them blank instead of inventing answers on a real employer's form. Salary stored as two
  figures: **8.4 LPA** (India) / **$30,000/yr** (international).
  ⚠️ **Blocked, environmentally not in code:** the standalone `claude` CLI returns `ConnectionRefused` and
  an interactive `claude` fails identically; proxy/DNS/TCP/hosts/sandbox all verified clean. It only
  connects when spawned inside a Claude Code session. Unblock = ~$10 OpenRouter credit +
  `AGENT_BACKEND=openrouter`. Also fixed 3 agent bugs (console crash inside the error handler, screenshot
  path, stdout-hidden failures). **Never diagnose from one shell** — the same call passed in 18.9s nested
  and timed out at 180s standalone.
- **2026-07-30 (evening) — the pipeline closed end to end.** Read [[20-first-email-batch-and-task-verification]]
  + D18/D19 before touching apply or the tasks. Headlines: **three tailored CVs actually reached recruiters**
  (Innova ESI, GoodSpace, CodeRound; Drive-shared per recipient, linked from a Composio Gmail send, **no
  bounces**) — Infosys deliberately excluded, it routes through Recruiter-A. **Check the recipient's MX before
  picking a Drive sharing mode:** a link restricted to one address only opens for a *Google* identity, and
  `innovaesi.com` is Microsoft 365, so that one needed link-only. Drive also defaults to **Editor** and
  **Notify people on** — both wrong here; the Send→Share button change is how you confirm notify is off.
  The **apply robot was aimed at the wrong target**: it drove external ATS and explicitly *skipped* Easy
  Apply, which is nearly the whole board, and it was **wired to nothing** (17 actions, no apply). Now
  rewritten for **LinkedIn Easy Apply** and registered as `apply` / `apply-all`, refusing to run without the
  tailored `cv_stem` PDF. **Packet building is on a 6-hourly timer** (`sweep-packets.ps1`) because discovery
  was outrunning processing badly. **Daily Discovery and Watch Accepts are now VERIFIED by log** (board
  24 → 62; Recruiter-B accepted, pitch scheduled 07-31 16:28). `daily-discovery.ps1` had **no contention
  guard at all** — added. **Recro is recorded as Applied 2026-07-29**; it had sat at `New` after a real
  submission, one sweep from a duplicate. Both `.claude.json` trust keys now `true`.
- ⚠️ **Two pending items for the owner (an AI cannot do either):** `.claude/settings.json` could not gain the
  `sweep-packets.ps1` / `build-packet.ps1` allowlist entries — the classifier blocks an AI editing its own
  permissions, deliberately. Not currently blocking: those run from Task Scheduler and the dashboard, which
  do not consult that list. And a Watch Accepts run at 21:00 died on **"You've hit your monthly spend
  limit"** — if every task starts failing at once with nothing in common, check the Claude usage limit first.
- **2026-07-31 / 08-01 — the sleep day, and why the sweeper never worked.** Read [[05-decisions]] D20-D24 +
  [[07-current-state]]. The laptop slept through all of 07-31 so nothing ran; then on wake Windows fired **all
  five missed tasks within 3 seconds**, spawning four LinkedIn MCP servers that fought over one profile.
  Catch-up was never broken — **ordering** was. New `tools/pipeline-lock.ps1` (atomic; the old "is a server
  running?" check is a race five simultaneous launches all pass), `tools/run-pipeline.ps1` (accepts → flush →
  replies → discovery → packets, sends first), and task **"Job Hunt - Catch Up"** firing 2 min after resume
  (`schtasks /SC ONEVENT`; `Register-ScheduledTask` and `-AtLogOn` both fail Access Denied without admin).
  **Proven in production 10:36** — discovery took the lock, watch-accepts stood down cleanly.
  **All three pitches now delivered** (Recruiter-A, Recruiter-C, Recruiter-B); invite queue empty. Recruiter-B's was correctly
  **held once**: her approved 2b said "I emailed you yesterday", which the sleep delay had turned into a
  falsehood (D22 — **relative time words are unstable state** in anything drafted now and sent later; and only
  the 2b block actually sends, so scope cleanliness greps to the message body). The accept watcher also fixed
  D21: business hours were enforced when *scheduling* an accept but never at *send* time, so the wake flood
  could have DMed a cold recruiter at 2am.
  **D23:** `sweep-packets` picks work from the **SQLite mirror** while discovery writes to **Notion**, and
  nothing refreshed it — mirror held **24 rows against Notion's 94**, hiding the three best roles. Re-synced
  (+70). **Daily Discovery is now DISABLED** (94 rows vs 4 packets buried the good ones).
  **D24, the big one:** headless `claude.exe` works 2 process layers deep and **fails at 3**. The scheduled
  **Sweep Packets** task uses the failing chain, so it had **never built a packet unattended** — the backlog
  sat still while every log looked plausible. Its error blames `ANTHROPIC_API_KEY`; **no such key exists**,
  don't hunt for it. Build packets with `tools/build-packet.ps1 -JobId <id>` **directly** until the middle
  `powershell` spawn is removed from the sweeper. First packet in days built this way: **SkillsCapital 93**.
- **2026-08-06 — the rewrite was decided, and the repo went public.** Full reasoning in
  `docs/knowledge/22-rewrite-architecture.md` + D26/D27/D28. Headline: **an IDE is not a server.** Claude Code
  becomes a subprocess called ~3×/day for the tailored CV; a Python orchestrator does everything else, with a
  free model for the handful of genuinely variable decisions. Target: 10 applications in **~7 minutes** instead
  of ~2.5 hours, at **₹0/day**. Nothing was deleted — the runbooks *become* the code, and `cv-architect`,
  `recruiter-outreach`, the answer bank and `board_db.py` are all reused unchanged.
  ⚠️ **The repo is now PUBLIC** (`github.com/AzamShah668/linkedin-automation`). `output/` and `profile/` are
  gitignored because they hold real recruiter names and personal contact details; recruiters are referred to
  as `Recruiter-A/B/C` in all committed docs. **Never commit a real third party's name, email, or LinkedIn URL.**

- **2026-08-06 (evening) — Phase 0 is written and has run against real forms.** Read
  [[23-phase-0-results]] + D29 before touching `apps/autopilot/`. `llm.py` · `answers.py` · `fill.py` ·
  `run.py`. Playwright **library** + a 37-entry `FIELD_MAP` filled real Easy Apply forms at **~16.7s each**
  with **zero LLM calls and zero invented values** — five project to ~85s against a 180s target, and the time
  goes to **page loads, not field mapping**. Nothing was submitted.
  **Four attempts and three silent-blindness bugs** were needed before the numbers meant anything, and that
  is the lesson worth keeping: the Easy Apply **dialog becomes visible before its contents render**, so 3 of 5
  jobs did nothing and **the tool printed PASS anyway** (*a metric that reports success for a no-op is worse
  than no metric*); **every `<fieldset>` question — all Yes/No radios and every consent box — was skipped in
  total silence**, because `inner_text()` omits LinkedIn's accessible-only `<legend>` and an unlabelled
  control was `continue`d (so `blank=0` meant "nothing was *seen*", not "nothing was missed"); and a Yes/No
  question containing "Docker" matched a `years_*` spec and tried to answer "2" — it failed safe **only
  because no radio option reads "2"**, which is luck, not design. Also confirmed: **LinkedIn offers to save a
  draft on 100% of jobs tested**, so a crash mid-wizard leaves a half-filled application behind. Also: `.pw_browser/` is version-locked by the owner's real Chrome 150 (exits **code 21**) — the
  live profile is `.pw_browser/linkedin_user_data/`, and a logged-out one is proven by a **missing `li_at`
  cookie**, never by an error string. **Phase 0 is NOT closed** — it needs one clean 5-fill run.
  ⚠️ **Owner action:** LinkedIn's verified email is not the canonical one on the CV; every application
  currently carries a mismatched address. And **~63% of the board is dead** — discovery rots in ~5 days.

- **2026-08-06 (later) — the CV bridge is built; phase order changed.** `apps/autopilot/cv.py` +
  [[24-cv-bridge]]. **The CV step was moved ahead of the database** ([[22-rewrite-architecture]] §7) because
  Phase 0 succeeded in a way that created a new problem: `fill.py` fills a form in ~14s and attached the
  **generic** CV on every job tested. Fast + generic is precisely the mass-automation failure this project
  exists to avoid, so speed made the CV bridge *more* urgent, not less. The database unblocks nothing a
  recruiter sees.
  `cv.py` is ~20 lines — `claude -p "read 15-build-packet-runbook.md ... Send nothing"` — reusing the
  runbook and skills unchanged. **One packet ≈ 7 minutes** (Energy Exemplar, ATS 90, PDF + 4 documents).
  `fill.py` uploads that PDF and **reads the filename back**; a mismatch aborts the job, because a wrong
  filename means a company receives another company's CV and nothing downstream would notice.
  Two traps paid for: LinkedIn has **no `input[type=file]`** — "Upload resume" opens a native chooser, so
  `set_input_files` silently does nothing (use `page.expect_file_chooser()`); and **D30 struck a third time
  in the D25 port itself** — the packet built completely, Claude hit its session limit a second later, and
  `cv.py` reported the job untouched while the 105KB PDF sat on disk. **Check the artifact first; only when
  there is no artifact does the log get to explain why.**
  ⚠️ Packets exist for **8 of ~90 rows** — every other row still attaches the generic CV. Nothing submits.

- **2026-08-09/10 — it applies now.** ~~Thirteen applications, zero replies.~~ ⚠️ **That number was
  FALSE and it reordered the whole plan — see the 08-11 entry below and D35.** Read [[26-apply-at-volume]]
  + **D31 / D32 / D33** before running `apply-all`. Built `families.py` (three **role-family CVs** —
  DevOps/Platform/SRE, AI/ML, Software Engineer — routed by title, and a missing family CV **skips the row**
  rather than falling back to the generic CV), `ledger.py` (append-only, fsync'd, and it imports nothing
  that can reach a board status — asserted by an AST test, because the mirror has been both stale *and*
  wrong), and `run.py apply-all`. **Eight real Easy Apply submissions.** 50 tests passing.
  The ledger was seeded from **the send record** (Gmail Sent + LinkedIn history), never from board notes —
  the board claimed SkillsCapital was unsent and Gmail proved it went out 08-01.
  🔴 **D32 — the research half was never wired in.** Five of the eight submissions have **no packet, no
  recruiter identified, no outreach**. The design is *tailored CV + named recruiter + touch 1 + touch 2*;
  the batch does the first quarter. Making a step cheap removed the cost that used to force the question
  "is this worth sending?" — which is the mass-automation shape this project exists to reject.
  🔴 **D33 — the company cap blocks the best row on the board.** It counts **every ledger row for a
  company regardless of channel or age**, so one old LinkedIn DM permanently locks out all four Infosys
  rows including **Junior AI Engineer (90)**. It also explains the twice-logged "why only fit 80-82?"
  puzzle: the scorer is fine, the plan's ceiling is just 85 once 93 and 90 are (rightly and wrongly) hidden.
  ⚠️ **D31, the most dangerous bug this project has produced.** A bare `\blocation\b` in the `city` spec
  matched *"Have you ever appeared for an Interview at any Exl location during the last 90 days?"* and typed
  **"Srinagar"** onto a real employer's form. It passed the answer-bank guard **because Srinagar is in the
  bank**. *The bank guarantees where a value came from and nothing about where it went* — two different
  safety properties, only one implemented. Patterns anchored, 9 regression tests written from real form text.
  Three more owner-caught bugs, all D30's disease: throttling after **skips** (so a batch looked busy and
  applied to nothing), Yes/No radios **never clicked** (the fallback required `count == 1`, which covers a
  lone consent box and nothing else), and `--limit 5` submitting **zero** (it capped the plan, and the top
  five rows are all external ATS).

- **2026-08-11 — the number that drove yesterday was wrong, and the pipeline now proves itself.**
  Read **D34 (resolved) / D35 / D36 / D41** and [[26-apply-at-volume]].
  🚨 **"13 applications, 0 replies" was false.** On **2026-07-26 at 18:58**, two hours after being pitched,
  Recruiter-A replied with **his personal phone number** and *"Send ur cv on this number"*. He asked for the
  CV. **Nobody answered for 16 days.** Eight consecutive reply checks reported "zero replies" and all eight
  were honest about the only place they looked — **Gmail**. Nothing in this project had ever opened LinkedIn
  messaging, so the reply was not missed, it was **unobservable**. *"Looked everywhere, found nothing" and
  "looked in one place, found nothing there" produce byte-identical output.* The real tally is **1 reply from
  1 warm-insider approach**, and it arrived on the first try at the highest-fit company — the outreach design
  never failed, the channel reading did. **D35.**
  Fixed in code: **`apps/autopilot/replies.py`** reads the LinkedIn inbox through the existing Playwright
  profile, escalates anything it cannot parse instead of going quiet, and an unreadable inbox prints *"this
  is NOT no replies"* and exits 2. Wired into `tools/check-replies.ps1` as **step 0**, deliberately in plain
  Python and deliberately *before* the agent step so a quota wall (D25) cannot blind it. **Proven in
  production 08-11 12:49**: the scheduled run surfaced the reply through the normal path, ticked Notion and
  posted Slack.
  **`apps/autopilot/coverage.py` (D41)** counts, every run, how many applications reached a **named human**.
  First run found **Recro — applied 07-29, nobody ever contacted**, which every prior audit had missed.
  Deliberately *not* automated end to end: code finds the gap, an agent finds the recruiter, **the human
  approves the invite** (D12). Automating a LinkedIn people-search plus auto-connect is the pattern that gets
  accounts restricted, and it is this project's own red line.
  **`apps/autopilot/sourcing.py` (D36)** screens a row *before* it spends an application slot. Two of eight
  submissions went to **Crossing Hurdles — zero employees findable on LinkedIn**, auto-ack funnelling to
  micro1 in 3 seconds; neither could ever be followed up. The screen immediately found a **third** such row
  queued. ⚠️ Its failure direction is the **opposite** of `replies.py` on purpose: blocking a real company
  costs an unrecoverable opportunity, letting a shell through costs ~15 seconds — so **heuristics may only
  deprioritize; only recorded evidence may block**.
  **D34 resolved.** A company's second role was unbuildable forever: the runbook refused to overwrite
  `output/outreach/<company>/` while `cv.py` looked packets up by **job id**. Now outreach stays per company
  (D8) and the **CV is per role** — `<company>--<role>/`, reusing the company's `contact.md`. **Unblocks 9
  rows** (Infosys ×5 incl. Junior AI Engineer 90, SkillsCapital ×4). Trap: a folder slug is **not** a
  comparison key (`skillscapital` vs `skills-capital`), and an unequal compare silently attaches the family
  CV instead of the tailored one.
  🔢 **98 tests** (was 50 on 08-09). Also fixed: **D33-D36 were claimed twice** by two parallel sessions —
  the content engine's four are now **D37-D40**. [[05-decisions]] is the single numbering authority; grep
  `^## D` before numbering anything.

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
