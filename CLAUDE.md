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
- Status: decided and documented. `apps/autopilot/` **not written yet** — Phase 0 is the next code task.
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

- **NEXT — two tracks, in this order:**
  1. 🔴 **The job hunt does not wait for the rewrite.** Five applications have been silent for 11 days with
     zero follow-ups sent, and the best row on the board (**SkillsCapital 93**, packet built 08-01) has never
     been sent. Run `followups.py`; email SkillsCapital; ping Recruiter-A about the Infosys "Junior AI
     Engineer" (90) — he is inside and already connected, and a *Junior* AI req is the rare shape that fits a
     final-year student.
  2. 🔵 **Rewrite Phase 0** — `apps/autopilot/` with `llm.py` + `fill.py` (Playwright *library*, answer bank,
     stop before submit). **Success test: 5 forms in under 3 minutes.** If it misses that, re-diagnose before
     building Phase 1. Then `cv.py`, the ~20-line bridge to Claude Code.

  Also still true: **re-score before building** any packet — the 38 newest rows were scored from title only,
  no JD fetched — and **watch the first real Easy Apply submission closely**; the rewritten runner has never
  submitted anything.

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
