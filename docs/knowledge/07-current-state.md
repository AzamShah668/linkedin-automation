# 07 — Current State (what ACTUALLY exists right now)

Back to [[00-INDEX]]. **Read this file second, every session, right after the INDEX.** It is the live
snapshot of what has really been built and where each job stands — the guard against "forgetting" work that
lives in a connected service (Notion / MCP) rather than in this repo. Update it after every working session.

> **Why this file exists:** on 2026-07-25 we nearly re-built the job-discovery store from scratch because the
> already-built Notion database + the MCP-driven discovery run were recorded *nowhere* in the brains. Lesson:
> work done through a connected service (Notion, LinkedIn/Gmail MCP) is invisible to future sessions unless
> it is written here. If it's not in a brain, it doesn't exist. See [[05-decisions]] D7.

## ⚠️ 2026-08-06 — THE ARCHITECTURE IS BEING REPLACED. Read this before changing anything.

Everything described below is **the current, working system**. It is accurate and it still runs — but a
decision was taken on 2026-08-06 to rewrite the runtime. **Do not build new features into the
PowerShell + scheduled-task + headless-Claude stack.** New work goes into `apps/autopilot/`.

- **The plan:** [[22-rewrite-architecture]] — read it before touching the pipeline
- **The decisions:** [[05-decisions]] **D26** (Claude Code is a tool, not the runtime), **D27** (free models
  for plumbing, Claude Code for the CV), **D28** (one `llm.py`, provider is a config value)
- **One-line summary:** we used an interactive IDE tool as a production runtime; that single choice caused
  D13, D17, D20, D24 and D25. A Python program will run the pipeline and call Claude Code as a subprocess
  for the one step a human actually reads — the tailored CV.
- **Status (updated 2026-08-06, evening): ✅ PHASE 0 IS CLOSED.** `apps/autopilot/` now holds
  `llm.py`, `answers.py`, `fill.py`, `run.py` (~1,050 lines). It drove the owner's real LinkedIn account and
  filled real Easy Apply forms, stopping before Submit, with **zero invented values**.
  Full write-up: **[[23-phase-0-results]]**.
  - **Measured: ~16.7s per form** (2 genuine fills in 33.3s). Five project to **~85s**, well inside the 180s
    target. Time goes to **page loads, not field mapping** — the good failure mode.
  - **Closing run: 5 genuine fills in 72.1s** (three consecutive passes: 62.7s · 54.6s · 72.1s), 23 fields
    filled, nothing submitted. It took **four attempts and three silent-blindness bugs** to get numbers that
    meant anything: the dialog shell renders before its contents (3 of 5 jobs did nothing while the tool
    printed PASS); **every `<fieldset>` question — all Yes/No radios and consent boxes — was skipped in
    silence** because `inner_text()` omits LinkedIn's accessible-only legend; and a Yes/No question matched a
    `years_*` spec, failing safe only by luck. All three fixed and verified against the live DOM.
  - **New answer-bank keys:** `identity.first_name`, `identity.last_name`, and a `consents` block
    (`data_processing: Yes`) — agreements, kept deliberately separate from facts.
  - ⚠️ **Owner action:** LinkedIn's verified email is `azamrizwanshah123@gmail.com`; the bank and every CV use
    `azamshah25809@gmail.com`. Applications currently carry an address that does not match the attached CV.
  - ⚠️ **The board is ~63% dead** — of the top 32 rows, ~20 are closed and 6 are external-ATS. Discovery data
    rots in about five days. Every Infosys row is `external-or-none`; Easy Apply will never reach that company.
- **Phase 1 (the CV bridge) is BUILT and proven end to end** — `apps/autopilot/cv.py`, see [[24-cv-bridge]].
  Phase order was changed to put it before the database ([[22-rewrite-architecture]] §7): `fill.py` fills a
  form in ~14s but attached the **generic** CV on every job tested, and fast + generic is the mass-automation
  failure this project exists to avoid.
  - `claude -p "read 15-build-packet-runbook.md ... Send nothing"` → **one packet ≈ 7 min**, ATS 90, PDF +
    4 outreach documents. Energy Exemplar built this way 2026-08-06.
  - `fill.py` now uploads the packet's PDF and **reads the filename back**; a mismatch aborts the job.
    Verified live: `resume=8-Energy-Exemplar-DevOps-Engineer.pdf [OK]`, 14.5s including the upload.
  - LinkedIn has **no `input[type=file]`** — "Upload resume" opens a native chooser, so `set_input_files`
    silently does nothing. Use `page.expect_file_chooser()`.
  - ⚠️ **Packets exist for only 8 of ~90 rows.** Any row without one still attaches the generic CV.
- **Nothing below has been deleted or disabled by this decision.** The six scheduled tasks, the runbooks and
  the skills all still work and are still the way to get a packet built today.

---

> **Browser profile trap (2026-08-06):** the Playwright profile is `.pw_browser/linkedin_user_data/`, NOT
> `.pw_browser/` itself. The parent was opened by the owner's real Chrome 150 and Chromium refuses a profile
> written by a newer build — it exits **code 21 instantly**, before any error is meaningful. And a logged-out
> profile is identified by a **missing `li_at` cookie**, never by an error string. See [[23-phase-0-results]] §9.

## How this project actually runs today (MCP-first, not custom code)

The [[02-architecture]] module map (`src/discovery`, `src/store`, SQLite, ATS adapters …) is the *eventual*
coded system. **None of that Python exists yet.** Right now the pipeline runs on **connected MCP services +
Claude following the two skills** — and it already works end-to-end for the first jobs:

| Pipeline stage | Planned (docs) | **Actually done via** |
|---|---|---|
| Discover jobs | ATS/job-board adapters | **LinkedIn MCP `search_jobs`** (manual run) |
| Store / track | SQLite `jobs` table | **Notion database "Job Hunt — Autopilot"** |
| Score fit | `scoring/` (rules+Claude) | Claude judged fit inline → Notion `Fit Score` |
| Research + tailor CV | `tailor/` | **`cv-architect` skill** → `output/cv/tailored/` |
| Find recruiter + draft | `outreach/` | **`recruiter-outreach` skill** → `output/outreach/` |
| Send | `gmail_sender` | **Started 2026-07-26 — two-stage LinkedIn play is live** |

Owner's directive (2026-07-25): build & review everything first, send at the very end in one reviewed batch.
**Superseded 2026-07-26:** sending has begun, gated by a ✅ reaction on the Slack card. See below.

## ⚡ Sending is now LIVE (2026-07-26) — the two-stage play

```
✅ on the Slack card  ->  stage 1: BARE connection request  ->  tracked as pending
                          stage 2: they accept -> wait 3-20h -> CV + full pitch auto-sends
```

- **Stage 1** — [[12-approved-send-runbook]], `tools/flush-approved.ps1`, **every 30 min** (task installed).
- **Stage 2** — [[13-accept-watch-runbook]], `tools/watch-accepts.ps1`, **every 4h** (task installed).

### ⚡ 2026-07-31/08-01 — the wake-from-sleep fix (read this before touching the tasks)

The laptop slept through **all of 2026-07-31**. Nothing ran; the Innova pitch due 16:28 never went out. Then
on wake at 22:01, Windows fired **all five missed tasks within three seconds**, starting four LinkedIn MCP
servers that fought over one browser profile. Full reasoning in [[05-decisions]] D20.

- Catch-up was never broken — `StartWhenAvailable` already worked. **Ordering** was missing.
- **`tools/pipeline-lock.ps1`** — one atomic lock for the whole pipeline. The old "is a server running?"
  check is a race and cannot serialise anything; five tasks launching together all pass it.
- **`tools/run-pipeline.ps1`** — runs the steps in order: **accepts → flush → replies → discovery →
  packets**. Sends first (they have deadlines), backlog sweep last. Also the manual "run everything now".
- **Task "Job Hunt - Catch Up"** — fires **2 min after resume from sleep**. Registered with
  `schtasks /SC ONEVENT`, because `Register-ScheduledTask` and `-AtLogOn` both fail *Access is denied*
  without admin.
- **A wedged owner is killed past 90 minutes.** Found live: a 02:12 reply check still held the lock at 04:38
  with its `claude.exe` child alive. Deleting the file cannot work while the handle is open.

**Manual run:** `powershell -ExecutionPolicy Bypass -File tools\run-pipeline.ps1`
(add `-Only accepts|flush|replies|discovery|packets` for one step).

**Proven in production 2026-08-01 10:36:** discovery took the lock at 10:36:13; watch-accepts tried 30s
later and **stood down cleanly** instead of colliding. The same overlap the night before spawned four MCP
servers and accomplished nothing.

### ⚡ 2026-08-01 — outreach queue EMPTY, and two cache bugs

- **All three pitches delivered.** Recruiter-A (07-26), **Recruiter-C 11:26**, **Recruiter-B 11:26**.
  `invite_tracker list` shows all three `followed_up`; nothing pending, nothing due.
- **Recruiter-B's was held once, correctly** — her approved 2b said "I emailed you yesterday", which the sleep
  delay had turned into a falsehood. Amended to "earlier this week" and sent. See [[05-decisions]] D22:
  **relative time words are unstable state** in any message drafted now and sent later.
- **The mirror was six days stale** ([[05-decisions]] D23). `sweep-packets.ps1` chooses what to build from
  the SQLite mirror, but discovery writes to **Notion**, and nothing had refreshed the seed since 07-26. The
  mirror held **24 rows against Notion's 94**, so the best roles on the board were invisible to the sweeper.
  Re-synced: +70 new, 24 updated. **Re-sync before trusting any "what next?" answer.**
- **Daily Discovery is DISABLED.** 94 rows against 4 packets is roughly 4:1; more rows bury the good ones.
  Re-enable with `Enable-ScheduledTask -TaskName 'Job Hunt - Daily Discovery'`.

### ✅ RESOLVED 2026-08-01 evening — it was a usage limit, not the process chain ([[05-decisions]] D25)

**The section immediately below is wrong and is kept only as a record.** The middle `powershell` spawn was
removed; the builds failed **identically**. The real message was in the build log all along:
`You've hit your session limit · resets 3:30pm (Asia/Calcutta)`.

- `claude -p` was proved working **from Task Scheduler**, at depth 2 and 3, with `.mcp.json` loaded. There is
  no auth problem, no key, no proxy, and nothing wrong with the chain.
- The D24 reproduction confounded **depth with time**: every success ran before the limit, every failure after.
- The spawn has been **restored** (process isolation is worth keeping), and `sweep-packets.ps1` now detects a
  usage limit, names it, and stops the sweep instead of recording it as a per-job `FAILED`.
- **Do not spend time on `ANTHROPIC_API_KEY` or process depth.** If builds start failing all at once, check
  the Claude usage limit first — this project has now written that lesson down twice.

### 🚨 [SUPERSEDED — see above] The packet sweeper has NEVER built a packet unattended ([[05-decisions]] D24)

**One PowerShell layer too many kills the headless Claude.** Reproduced, not guessed:

| Chain | Depth | Result |
|---|---|---|
| `powershell` → `build-packet.ps1` → `claude` | 2 | ✅ works (SkillsCapital built, 16 min, ATS 90) |
| `powershell` → `sweep-packets.ps1` → `powershell` → `build-packet.ps1` → `claude` | 3 | ❌ fails ~3 min, 7/7 |

SkillsCapital **failed** nested then **succeeded** direct. The scheduled **Sweep Packets** task uses the
failing three-layer chain, so it has never once produced a packet — the backlog never moved while every log
looked plausible.

⚠️ **The error message lies:** it blames `ANTHROPIC_API_KEY or another auth source`. There is none — checked
process/user/machine scope, every settings file, and `.mcp.json`. **Do not hunt for a key that does not
exist.** Same shape as the 2026-07-29 blocker in [[16-gui-automation-investigation]].

**Until fixed:** build packets by calling `tools/build-packet.ps1 -JobId <id>` **directly**. ~16 min each.
**Fix direction:** remove the middle `powershell` spawn from `sweep-packets.ps1`.

### Allowlist entries still missing (an AI cannot add them)
```
"Bash(powershell -ExecutionPolicy Bypass -File tools/sweep-packets.ps1:*)",
"Bash(powershell -ExecutionPolicy Bypass -File tools/build-packet.ps1:*)",
"Bash(py -3 tools/ats_audit.py:*)",
```
`ats_audit.py` was auto-denied mid-build on 08-01, so that ATS score was computed by hand.

**Top of the backlog now (JD-verified unless noted):**
`93 SkillsCapital — Software Engineer Intern (AI/ML & Agentic AI)` ⭐ JD explicitly asks for a final-year
student; Easy Apply **and** `careers@skillscapital.io`; 6 days old, 100+ applicants — move first.
`92 Mirai Alpha — AI Engineering Intern, Agentic AI & MCP (title-level score, re-score first)` ·
`90 Infosys — Junior AI Engineer` (Recruiter-A is inside and already connected).

**✅ SkillsCapital packet BUILT 2026-08-01** — `output/outreach/skillscapital/`, ATS 90, status `To Apply`,
Slack card unticked, nothing sent. Three things recorded with it:
1. **SkillsCapital has FOUR board rows and only this one is in-house.** SRE 83 / Cloud 82 / DevOps 82 are
   SkillsCapital placing candidates *at a client*. Two row notes suggest batching one recruiter across all
   four — **don't**; it spends the one good approach on someone else's req.
2. **ATS is 90 deliberately.** scikit-learn, pandas, NumPy, Elasticsearch, AWS, Azure were left off because
   nothing in `profile/` backs them, and the cover letter names the gap. If Azam has used
   pandas/NumPy/scikit-learn in coursework it becomes 95 — **his call, never an assumption.**
3. **`skillscapital.io` MX unchecked** — that decides the Drive sharing mode before the PDF goes out
   ([[drive-sharing-mx-decides]]).

### Scheduled tasks — SIX armed as of 2026-08-01
| Task | Cadence | Does | Verified by log? |
|---|---|---|---|
| Job Hunt - Daily Discovery | ⏸️ **DISABLED 2026-08-01** | finds new jobs → Notion → Slack | ✅ 2026-08-01 (board → 94) |
| Job Hunt - Reply Check | ~4×/day | watches Gmail for replies | ✅ 2026-07-30 (0 replies, 0 bounces) |
| Job Hunt - Flush Approved | every 30 min | ✅ → bare connection request | ✅ 2026-07-26 |
| Job Hunt - Watch Accepts | every 4h | accept → wait 3-20h → CV + pitch | ✅ 2026-07-30 (found Recruiter-B's accept) |
| **Job Hunt - Sweep Packets** | **every 6h from 09:30** | **drains the no-packet queue, 2/cycle, sends nothing** | ✅ 2026-07-30 (own trigger fired) |
| **Job Hunt - Catch Up** | **2 min after resume from sleep** | **runs the whole pipeline in order, one step at a time** | ✅ 2026-08-01 (manual run, all steps) |

All five confirmed to have `DisallowStartIfOnBatteries = False`. **Judge every one of them by its log, never
its exit code** ([[05-decisions]] D17) — this has now bitten three separate ways in a single day.

Both send tasks exit in under a second when there's nothing to do (cheap guards), so frequent polling costs
nothing. `Register-ScheduledTask` with `-AtLogOn` **fails with Access Denied** without admin — that's why the
flush task uses a timed trigger. Remove either with `schtasks /Delete /TN "<name>" /F`.
- **State** — `output/outreach/pending-invites.json` via `tools/invite_tracker.py`.
- **Why bare requests:** a request *with* a note is capped at 3/month; a DM to a 1st-degree connection is
  uncapped. [[05-decisions]] D12. The 3 monthly notes are reserved for warm insiders, **sent by hand**.

**Blocking gotchas found 2026-07-26 (both fixed):**
1. The Slack ✅ gate never worked because the bot token had **write-only scopes**. Fixed by adding
   `channels:history`, `groups:history`, `reactions:read`, `reactions:write` and reinstalling. The channel is
   **private** — `groups:history` is the one that actually matters, and Slack's `needed` field said so
   outright after `channels:history` alone still failed.
2. `connect_with_person(..., note=...)` returns `custom_note_limit_reached` and **silently sends nothing**
   whenever LinkedIn shows its quota banner — not a length problem (failed identically at 290 and 197 chars,
   note box `0/200`). Calling it with **no** `note` works. This is what forced D12.

### ⚠️ Headless runs need THREE things the interactive session gets for free (learned 2026-07-26)

Every one of these silently broke the first live flush. All three are fixed; keep them in mind before
blaming LinkedIn for a failed run.

1. **Allowlist.** Headless Claude runs `--permission-mode default`, so any Bash command not in
   **`.claude/settings.json`** → `permissions.allow` is **denied with nobody there to approve it**. Every
   new `tools/*` a runbook calls must be added there the day it is written. **58 entries** as of
   2026-07-30, including `Write` and `Edit` (without those, every unattended run silently discarded its own
   findings) and `auto-apply.ps1`.
   ⚠️ **An AI cannot add to this list** — the permission classifier blocks a model editing its own
   permissions, deliberately. `sweep-packets.ps1` and `build-packet.ps1` are therefore **still missing** and
   must be added by hand. Not currently blocking: both are launched by Task Scheduler and the dashboard,
   neither of which consults this list. It matters the moment a *runbook* wants to call them.
   And remember [[18-headless-trust-and-send-capability]]: the whole list is void unless the workspace is
   trusted. Both `~/.claude.json` keys (`d:/` and `D:/`) now read `true`.
2. **MCP resolution.** `mcp-server-linkedin` was registered in `~/.claude.json` under the project key
   `'d:/linkdin automation'` — **lowercase `d:`**. A task launched with `D:` uppercase does not match, so the
   headless run came up with **no LinkedIn tools at all** and reported it as an auth failure. Fixed with a
   project-local **`.mcp.json`** (resolves by directory, not by a case-sensitive key) plus
   `"enableAllProjectMcpServers": true` in settings.
3. **Browser-profile lock — ✅ PROVEN 2026-07-26.** Two Chromium instances cannot share
   `~/.linkedin-mcp/profile`. With an interactive Claude session holding it, every headless run reported
   *"Session expired or invalid"* — while the interactive session read `get_person_profile` successfully
   **60 seconds later**. The session was never expired; the headless browser just came up empty and the MCP
   mislabelled it. This cost an hour of chasing a non-existent auth bug, twice.
   - **Mitigation in place:** both task scripts now detect a process holding the profile and **skip with an
     honest log line** instead of misreporting. Approvals stay queued for the next run.
   - **Consequence:** the scheduled tasks only do real work when **no Claude Code session is open**. The
     hands-off promise is conditional on that. Tell the owner plainly; don't let them think it runs always.
   - **Proper fix, not yet built:** the MCP accepts `--user-data-dir PATH`. Give the headless tasks their own
     profile (`~/.linkedin-mcp/profile-headless`, logged in once), passed via a task-only `--mcp-config`.
     Caveat to solve first: `--mcp-config` may need `--strict-mcp-config`, which would drop the Notion
     connector the runbooks depend on — verify before switching.
   - **Never trust an MCP "session expired" message while a session is open.** Confirm with a real tool call
     from a second context first.

Also: `uvx mcp-server-linkedin@latest --status` is **unreliable on Windows** — it crashes with
`UnicodeEncodeError` while printing its own ✅/❌ symbol, so its output and exit code tell you nothing. The
only trustworthy auth check is to call a real tool such as `get_my_profile`.

Also: `& claude ... *>> $log` writes **UTF-16** in PS 5.1 and the log comes out as garbled spaced characters.
Both task scripts now pipe through `Out-File -Encoding utf8` instead.

### Actually sent so far
| Who | Company | What went out | State (as of 2026-07-26 16:30) |
|---|---|---|---|
| Recruiter-A ⭐ warm insider | Infosys · AI Application Engineer (90) | Bare connection request, no note | ✅ **ACCEPTED** — pitch scheduled **20:18 today** |
| Recruiter-B (Sr Technical Recruiter) | Innova ESI · DevOps Engineer (87) | Bare connection request, no note | ✅ **ACCEPTED 2026-07-30** — now 1st degree; pitch scheduled **2026-07-31 16:28** |
| Recruiter-C (Co-Founder & CEO) | GoodSpace AI · Forward Deployed Engineer (85) | Bare connection request, no note | ✅ **ACCEPTED 2026-07-31 22:06** — pitch scheduled **2026-08-01 09:46** |

All three sent **from an interactive session**, not by the scheduled task — see the profile-lock item above.
All three tracked in `output/outreach/pending-invites.json`, Notion set to `Invite sent`, Slack cards stamped
📤. The warm/CV pitch for each goes out via [[13-accept-watch-runbook]] once they accept.

✅ **2b audit done (2026-07-26).** Infosys 2b was cold — the fellow-Kashmiri hook had been stranded in the
never-sent 2a — and was rewritten to open with it. Innova ESI and GoodSpace turned out fine on that count
(both contacts are genuinely cold, 3rd degree, no shared ties, so there was no warm line to lose), but both
had **em-dashes** (banned AI-tell) and GoodSpace had literal `*asterisks*` that LinkedIn renders as text.
Both cleaned. **Standing check before any 2b sends: no em-dashes, no markdown, no unresolved `{}`/`[]` slots.**

### `tools/` inventory (all stdlib-only, no third-party deps)
| Tool | Role | Allowlisted for headless? |
|---|---|---|
| `check_approvals.py` | reads the Slack ✅ gate | ✅ |
| `invite_tracker.py` | two-stage invite state + delay scheduling | ✅ |
| `slack_react.py` | stamps 📤 — **the send-twice guard** | ✅ |
| `slack_action_card.py` | posts the short job card | ✅ |
| `slack_notify.py` | event/summary posts | ✅ |
| `followups.py` | Day-3/Day-7 nudges (needs runner-supplied Notion rows) | ✅ |
| `ats_audit.py`, `send_queue.py`, `slack_upload.py` | supporting | not needed unattended |

Anything a runbook calls **must** be added to `.claude/settings.json` → `permissions.allow` the day it is
written, or the unattended run silently refuses and the whole flow stalls.

**Which settings file:** the automation allowlist lives in **`.claude/settings.json` (committed)**, not
`settings.local.json` — the latter is gitignored, so a fresh clone would lose the permissions and reproduce
failure mode 2 from scratch. These permissions are what the pipeline *needs to function*, not a machine
preference. `settings.local.json` stays for genuinely local overrides.

## The job store — Notion "Job Hunt — Autopilot"

- **URL/id:** database `1a54600b-97d9-45d2-b67a-35f5455eee5d` · data source `collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2`
- **Schema:** Job (title), Company, Fit Score (number), Found (date), Location, Work Type
  (Remote/Hybrid/On-site), Source (LinkedIn), **Status** (New → To Apply → Applied → Interview →
  Rejected / Skipped), **Warm Intro** (checkbox), Notes, URL.
- **This is the real store** (replaces the planned SQLite `jobs` table for now). Query it with
  `notion-query-data-sources` (SQL mode) before assuming anything about job state.

### Board size: **94 jobs** (as of the 2026-08-01 discovery run)

Growth: 10 (2026-07-25 first run) → 23 (same-day second run) → 24 (2026-07-26) → 62 (2026-07-30) →
79 (undocumented growth between 07-30 and 08-01) → **94 (2026-08-01)**.
⚠️ The board read **79** at the start of the 08-01 run, not the 62 recorded here — 17 rows arrived without
any session writing them down. Assume the count in this file is a floor, and **query Notion for the truth**.
Don't table the rows here — it goes stale within a day. **Query Notion** for live state; this section only
records the shape of the board and which rows are already engaged.

**Engaged so far (4 rows):** Infosys AI Application Engineer (90 ⭐, `Applied`) · CodeRound AI Engineer
LLMs & Agents (89, `Applied`) · Innova ESI DevOps (87, `Applied`) · GoodSpace AI Forward Deployed
Engineer (85, `Applied`). **Everything else is `New`** — 58 rows with no CV and no outreach.
(Both `Invite sent` values above were stale — Notion has read `Applied` since the 2026-07-30 email batch.
Corrected 2026-08-01 by querying, not by trusting this file. Recro is a 5th `Applied` row.)

**The 2026-07-30 run added 38 rows, 6 of them warm.** Highest-value find:
**Junior AI Engineer · Infosys · Bengaluru East (fit 90, ⭐)** — LinkedIn reports *1 connection works here*,
and the known Infosys tie is **Recruiter-A**, whose connection request was **accepted 2026-07-26**. A
"Junior"-titled AI req is rare and is the one shape that fits a final-year student without a stretch; it is
the single highest-priority action on the board. Other warm adds: Deloitte ×2 (2 CUK alumni), EXL ×2 and
HCLTech (1 CUK alum each).

⚠️ **Scoring caveat on the 2026-07-30 batch:** scores are **title-level** — derived from title, company,
location, work type and the LinkedIn result badges, **not** from fetched JDs. That is a weaker basis than
the 2026-07-25 rows. Re-score against the real JD before building any packet. Notes say so per row.

⚠️ **Threshold vs. volume (judgment applied, not in the runbook).** `FIT_SCORE_THRESHOLD=70` would have
admitted ~60 rows from one run. That swamps a board the owner works top-down, so the 2026-07-30 run
inserted the **≥80 tier only** and reported the 70–79 tail in the summary instead. ~25 roles were held
back on that basis (JPMorganChase SRE II 79, Qubrid AI Junior NVIDIA Networking 79, Neysa Backend 79,
Anaplan Backend GenAI 78, UST Azure Cloud Ops 78, Cyfuture, Infinity Learn, HJ Infotech, Omni Hire,
Vanguard, Dassault, and others). If the owner wants the wider net, re-run the tail — do not silently
change the threshold.

## What's built (repo + services)

- **CV engine** — `cv-architect` skill (**the single canonical engine** — `cv-builder` merged in & retired
  2026-07-25, decision [[05-decisions]] D9; master CV now at `cv-architect/references/master-cv.md`). Outputs
  in `output/cv/` (base DevOps CV, achievement-bank, positioning-selector) + 3 tailored CVs in `output/cv/tailored/`.
- **Outreach engine** — `recruiter-outreach` skill; `output/outreach/` has `highlight-reel.md`,
  `REVIEW-QUEUE.md`, and per-company `{contact,touch-1-email,touch-2-linkedin,cover-letter}.md` for the 3
  processed jobs. Real named recruiters filled 2026-07-25 (see [[02-architecture]] outreach section + REVIEW-QUEUE).
- **Content layer (completion-plan step 1, done 2026-07-25):** cover letters written for all 3 jobs; **PDF
  export automated** via `tools/html-to-pdf.sh` (headless Chrome/Edge, no installs) — all CVs rendered to
  `output/pdf/`; recruiter **email domains MX-verified** ✅ (exact mailbox still needs a per-address check).
- **Slack event layer (completion-plan step 2, done 2026-07-25):** `tools/slack_notify.py` — reusable
  notifier, wired into the outreach skill; posts to `C0AN5ASHZB6`.
- **Follow-up + tracking engine (completion-plan step 3, done 2026-07-25):** Notion gained tracking fields
  (`Applied Date`, `Reply`, `Follow-ups Sent`, `Next Action`); `tools/followups.py` computes Day-3/Day-7
  nudges (dry-run tested). Tracking convention + run loop in `tools/README.md`.
- **Send machinery (completion-plan step 4, done 2026-07-25):** caps added to `.env`; `tools/send_queue.py`
  enforces daily-cap + delay + jitter on approved items and prints the throttled send plan (dry-run tested;
  executes via Gmail MCP at the final batch, never auto-sends).
- **Automatic daily discovery (completion-plan step 5, done 2026-07-25):** LOCAL Windows Scheduled Task
  "Job Hunt - Daily Discovery" (daily 08:00 IST) → `tools/daily-discovery.ps1` runs Claude headless against
  [[09-discovery-runbook]] (real LinkedIn MCP + Notion + Slack, read-only, no sends). Perms allowlisted in
  `.claude/settings.local.json`. Local not cloud — [[05-decisions]] D11. Logs → `output/discovery-log/`.
  **Validation 2026-07-25 — mixed result, read this before trusting the robot:**
  - ✅ **The discovery RECIPE is proven.** Ran end-to-end manually in-session at 23:45: LinkedIn `search_jobs`
    (DevOps + AI/MLOps, past_week) → deduped against the 10 existing rows → scored → **13 new jobs written to
    Notion (board now 23)** → Slack digest posted. Bonus finding: LinkedIn's own results report school-alumni
    counts per company, so the D8 warm-intro signal comes free with the search (4 of the 13 have CUK alumni
    inside: Infosys ×2, P&G, IBM).
  - ❌ **The HEADLESS SCHEDULED PATH IS BROKEN.** Two attempts, two different failures: 18:08 died on a Claude
    session limit (exit 1); 23:43 aborted with **0x8007042B ERROR_PROCESS_ABORTED** after ~4 min, writing no
    output and not even its own end-marker (the PowerShell wrapper was killed mid-run). Root cause unknown —
    suspect `claude -p` headless needs an interactive session/TTY the Task Scheduler context doesn't provide.
    **Do not rely on the 08:00 job until this is diagnosed.** Until then, discovery is run on request in-session
    (which works well). Fix options to try: run the task with "Run only when user is logged on" + interactive
    token, log claude's stderr separately, or replace the headless call with a queued prompt this session picks up.
- **Backlog depth started (completion-plan step 6, 2026-07-25):** ✅ LinkedIn profile optimization pack
  (`output/linkedin/profile-optimization.md`, paste-ready); ✅ ATS keyword auditor (`tools/ats_audit.py`).
  Rest reconciled with [[10-advanced-ideas]] — see [[08-completion-plan]] step 6.
- **Email pipeline (2026-07-25) — first actual Gmail use:** OUTBOUND — 3 target emails live as real **Gmail
  drafts** (Infosys/Innova/GoodSpace), rewritten in plain human style (no em-dashes/AI-tells) and linking the
  **single general CV** at `github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf` (decision D12;
  tailored variants deliberately NOT published). Nothing to attach; owner just reviews and sends. Recruiter
  mailboxes still [VERIFY] — **except Innova ESI, confirmed 2026-07-30**: Recruiter-B publishes
  `recruiter-b.recruiter-b@innovaesi.com` herself in her own LinkedIn hiring posts. **Cheapest mailbox check there is:
  read the recruiter's own posts before reaching for a verification API** — recruiters who post reqs almost
  always print their intake address in the post.
  INBOUND — **reply classifier** (`tools/check-replies.ps1` + Windows task "Job Hunt - Reply Check", ~4×/day)
  runs [[11-reply-classifier-runbook]]: Gmail read-only → classify → Notion Reply/Status → Slack alert. Gmail
  read tools added to `.claude/settings.local.json`. **Recipe ran clean 2026-07-30 22:0x — still zero real
  replies**, so the classify/update/alert branches remain unexercised. Logs → `output/reply-log/`.
- **Phone-first outreach (2026-07-25):** `tools/slack_action_card.py` posts a complete per-job card to Slack
  (recruiter + tappable LinkedIn link + exact message to copy + email/CV + DO-THIS checklist) — owner acts
  from their phone, no files. Wired into `recruiter-outreach` Step 4; the 3 targets' cards posted live.
- **`tools/`** (the Path A "glue" layer, self-documented in `tools/README.md`) — `html-to-pdf.sh` (HTML→PDF),
  `slack_notify.py` (Slack events), `slack_action_card.py` (phone-ready per-job cards), `followups.py`
  (cadence engine), `send_queue.py` (throttled send planner), `daily-discovery.ps1` (scheduled discovery
  runner), `ats_audit.py` (ATS keyword-gap auditor).
- **Profile dossier** — `profile/` (master-profile, projects-catalog).
- **Public proof** — 2 public GitHub repos (three-brain-knowledge-architecture; profile README).
- **Connected services in use:** LinkedIn MCP (`search_jobs`/`search_people`/`get_company_employees`, read-only),
  Notion MCP (the store), Gmail MCP (outreach delivery, not yet used to send).
  **Slack ✅ LIVE (2026-07-25)** — reused the AXIOM workspace bot token (in `.env`), channel `C0AN5ASHZB6`.
  **Event layer built:** `tools/slack_notify.py` (no deps) with events new_match/draft_ready/sent/reply/
  followup_due/digest; wired into `recruiter-outreach` Step 4; tested live. Google Calendar still planned.

## LinkedIn MCP — auth + recovery (learned 2026-07-25)

Package `mcp-server-linkedin` (uvx) = `stickerdaniel/linkedin-mcp-server`, a patchright headless-Chromium
driver; session profile at `~/.linkedin-mcp/`. **If tools start erroring:** run
`uvx mcp-server-linkedin@latest --status` once (relaunches browser, revalidates, re-exports clean cookies),
then retry — the next MCP call works. Known cosmetic bug: `--status`/`--login` crash with
`UnicodeEncodeError '✅'` on a Windows cp1252 console *after* validation succeeds (exit 0, harmless).

### ⚠️ THE 16:23 "SESSION EXPIRED" WAS NOT AN EXPIRY (resolved 2026-07-26 17:15)

**Read this before you ever act on a "Session expired or invalid" message again.** It cost the owner two
unnecessary LinkedIn logins and roughly an hour, twice over, across two sessions.

**Root cause: three `mcp-server-linkedin` servers were running at once** — one per Claude Code session
opened that day (started 10:39, 12:58, 16:46). They all drive the *same* browser profile
(`~/.linkedin-mcp/profile`), which cannot be shared. Whichever server loses the race gets an empty browser
and the MCP reports that as dead auth. Killing the two stale servers made `get_my_profile` succeed
immediately — the `li_at` from 14:29 was valid the whole time.

**The proof the owner spotted, which broke the false diagnosis:** the Recruiter-A pitch was delivered
successfully at **16:43**, i.e. *twenty minutes after* the watcher declared the session expired at 16:23.
An expiry cannot un-expire. Whenever two observations contradict like that, the error message is what's
wrong. (An intervening session had recorded the expiry as real, including a claim that it ran `--status`
recovery and confirmed it — that record was mistaken and has been struck.)

**Diagnosis order — cheapest first, and stop when one explains it:**
1. **Count the servers.** `tools/linkedin-doctor.cmd` step 1. More than one = that's your bug. Count
   **python.exe only**: each session spawns one python server plus two uvx/uv wrappers, so counting the
   whole tree over-reports by 3× (a bug the doctor itself shipped with for ten minutes — PowerShell's
   `Group-Object` treats a bare script block as a *property name*, so every item lands in its own group;
   it needs `-Property { ... }`).
2. **Check `~/.linkedin-mcp/cookies.json` mtime** — but read it correctly: this file only changes on a real
   login or refresh, so **an old timestamp is not evidence of a problem**. A working session can be hours
   or days old. (Earlier in this same session the 14:29 stamp was misread as proof that two logins had
   failed to land. It actually just meant no *new* login had happened, which was correct and fine.)
3. **Call a real tool** (`get_my_profile`). This is the only trustworthy auth test. If the profile comes
   back, the login is healthy no matter what any error said.
4. **Only then** consider `uvx mcp-server-linkedin@latest --login`, with every Claude window closed.

**Facts that survive this correction** (they were right, just misapplied):
- A login in Chrome/Edge/phone does nothing for the robot — it drives its own patchright Chromium against
  its own profile. And signing in elsewhere can *invalidate* the robot's session, so re-logging-in "just
  to be safe" is an anti-fix, not a neutral act.
- A cookie's stated expiry proves nothing about server-side validity, so never reason from that field.
- `invalid-state-<utc-ts>/` folders are quarantined states; 14 had accumulated. A cluster of them marks
  *contested profile access*, **not** a genuine expiry — that reading was wrong too.

**Tool: `tools/linkedin-doctor.cmd`** — counts servers, prints the exact `Stop-Process` line to kill the
strays while keeping the newest, reports the cookie mtime with the caveat above, and lists quarantined
states. (It replaces `tools/linkedin-login.cmd`, which was written on the wrong premise — that a login was
needed — and has been deleted.)

## The send board (dashboard)

The owner-facing view: who has the CV, who is waiting, which companies have had nothing. Live-reads the
Notion board via the Artifact `mcp` capability. **Full detail, the architecture and the connector-name
gotcha live in [[14-send-board-dashboard]]** — read that before editing the page. Two facts you need even
if you don't open it: the source is `output/dashboard/send-board.html` (**in the repo**, never a scratchpad),
and it publishes to the fixed private URL `claude.ai/code/artifact/8b4c38fe-afac-48c9-9d69-67a45420c8ec` —
pass that `url` to the Artifact tool or a future session will mint a new link and orphan the owner's.

## 2026-07-30 (evening) — the pipeline is now closed end to end

Full detail in [[20-first-email-batch-and-task-verification]] and [[05-decisions]] D18/D19. Headlines:

- **Three tailored CVs actually reached recruiters** (Innova ESI, GoodSpace, CodeRound) — Drive-shared
  per recipient, linked from a Composio Gmail send, **no bounces**. Infosys deliberately excluded; it
  routes through Recruiter-A. Check the recipient's **MX** before choosing a sharing mode: a link
  restricted to a specific address only opens for a **Google** identity, and `innovaesi.com` is
  Microsoft 365.
- **The apply robot was pointed at the wrong target.** It drove external ATS and explicitly skipped
  Easy Apply — which is nearly the whole board. Rewritten for **LinkedIn Easy Apply** (D18) and finally
  **wired into `pipeline_runner.py`** as `apply` / `apply-all`; it had been reachable from nothing.
- **Packet building is on a timer** (D19). `tools/sweep-packets.ps1` + task "Job Hunt - Sweep Packets",
  every 6h, max 2. Discovery had been outrunning processing badly.
- **Daily Discovery and Watch Accepts are VERIFIED**, by log, not exit code. Discovery: board **24 → 62**,
  38 new rows, Slack digest. Watch Accepts: **Recruiter-B accepted**, pitch scheduled 2026-07-31 16:28.
- `daily-discovery.ps1` was the only runner with **no contention guard**; added.
- Both `~/.claude.json` trust keys now read `true`, closing the last open item in
  [[18-headless-trust-and-send-capability]].
- **Recro (Generative AI Engineer) is now recorded as Applied 2026-07-29.** It had been sitting at `New`
  after a real submission — one sweep away from applying twice. There is a *second* Recro row (DevOps
  Engineer, found 07-30) that has **not** been applied to; do not conflate them.

### Board state (2026-07-30)
62 jobs. Five at `Applied`: Infosys AI Application Engineer (07-26), CodeRound AI Engineer LLMs & Agents
(07-26), Recro Generative AI Engineer (07-29), Innova ESI DevOps (07-30), GoodSpace FDE (07-30).
Local mirror has **nothing unpushed**. **Only 4 packets exist** (infosys, innova-esi, goodspace,
coderound-ai) — so ~56 rows are discovered but unprocessed. That gap is the project's real bottleneck.

### ⚠️ The sweeper counted attempts, not builds (fixed same day)
`build-packet.ps1` **exits 0 when it SKIPS** on profile contention, so the first `sweep-packets.ps1`
reported `built 2` when nothing had been built. It now captures the child's output, matches `SKIPPED:`,
**breaks out of the sweep on the first skip** (contention does not clear mid-run), and reports
`built N, skipped M, K were queued`. Verified honest: `built 0, skipped 1, 15 were queued`.
See [[05-decisions]] D19 addendum.

## Reply check — 2026-07-30 22:0x (first clean end-to-end run)

All 5 `Applied` rows checked against their recruiter domains (`infosys.com`, `innovaesi.com`, `goodspace.ai`,
`coderound.ai`, `recro.io`) over `newer_than:14d in:inbox`. **Zero recruiter replies.** Nothing written to
Notion, nothing sent to Slack — correctly, per the runbook's de-dupe rule.

Two findings worth keeping:

1. **No bounces.** A `mailer-daemon`/`Undeliverable`/`Delivery Status Notification` sweep over the last 5 days
   came back empty, which is the first *positive* confirmation that the 2026-07-30 email batch actually
   delivered to `recruiter-b.recruiter-b@innovaesi.com`, `recruiter-c@goodspace.ai` and `chaitanya@coderound.ai`. Two of
   those three addresses were pattern guesses; "no bounce" was previously only an absence of evidence, and is
   now a checked absence.
2. ⚠️ **The board is blind to the campus channel.** The only real job traffic in the inbox was an **EPAM
   Systems** online-test invite (`niharika.lingam@naukricampus.com` + `no-reply@doselect.email`, both
   2026-07-27, both still **unread**) for a CUK-specific freshers test scheduled 27 Jul 18:00 — i.e. it
   expired unseen. **EPAM has no row in Notion**, so no runbook watches it: the reply classifier only searches
   domains harvested from `output/outreach/<slug>/contact.md`, which by construction only covers companies the
   autopilot itself sourced. Campus/Naukri/university placement mail is a live, time-boxed application channel
   that the pipeline currently cannot see. Worth a scoped widening of the reply-check query (e.g. an
   assessment-platform sender list: naukricampus, doselect, hackerrank, hackerearth, mettl) rather than
   letting a deadline pass again.

## Reply check — 2026-07-31 (second clean run, still zero replies)

Same 5 `Applied` rows, same 5 domains, `newer_than:14d in:inbox`. **Zero recruiter replies.** No Notion
writes, no Slack pings — correct per the de-dupe rule.

- **The empty result was verified, not assumed.** A bare `newer_than:14d in:inbox` control returned 201
  threads, and `(from:linkedin.com OR from:infosys.com)` returned 22 — so both the connector and the
  `from:<domain>` OR-group syntax were proven live before the zero was believed. Do this every run; a
  broken query and an empty queue look identical.
- **Bounces still clean** (`newer_than:5d`, mailer-daemon/postmaster/Undeliverable sweep). This matters more
  than the 07-30 check did: that one ran ~1h after the batch went out, too early to be conclusive. A full
  day later, `chaitanya@coderound.ai` and `recruiter-c@goodspace.ai` — both **pattern guesses** — are now
  confirmed delivered.
- **Campus channel: nothing new.** The scoped sender sweep (naukricampus, doselect, hackerrank, hackerearth,
  mettl, epam) returned only the two known EPAM items from 07-27, both still unread and long expired. The
  widening in "Immediate next work" #6 is **still unbuilt** — this run did it by hand.
- Read: 5 domains searched → `infosys.com`, `innovaesi.com`, `goodspace.ai`, `coderound.ai`, `recro.io`.
  Recro has **no `output/outreach/` folder** (Easy Apply, never an outreach packet), so its domain is not
  harvestable from `contact.md` and had to be supplied by hand. Any future Easy-Apply-only row has the
  same hole.

## Reply check — 2026-07-31 late (third clean run, still zero replies)

Same 5 `Applied` rows (Infosys, CodeRound AI, Recro, Innova ESI, GoodSpace AI), same 5 domains.
**Zero recruiter replies. No Notion writes, no Slack pings** — correct per the de-dupe rule.

- **Query proven before the zero was believed**, per the standing rule: bare `newer_than:14d in:inbox`
  returned **201** threads and `(from:linkedin.com OR from:infosys.com)` returned **22**, so both the
  connector and the `from:` OR-group syntax were live. Only then was the empty 5-domain result trusted.
- **The zero was also widened, not just accepted.** The same 5 domains over `newer_than:30d in:anywhere`
  (i.e. including spam, promotions and archive, double the window) also returned empty. So this is not a
  reply sitting misfiled in Promotions — nothing has ever come back from any of the five.
- **Bounces still clean** at `newer_than:14d in:anywhere` — the widest bounce sweep run so far, and the
  first to cover the *entire* window since the 07-30 email batch. `chaitanya@coderound.ai` and
  `recruiter-c@goodspace.ai` (both pattern guesses) stay confirmed delivered.
- **Campus channel: still nothing new.** The scoped sender sweep — now widened to include `imocha.io` and
  `codility.com` alongside naukricampus/doselect/hackerrank/hackerearth/mettl/epam — returned only the two
  known EPAM items from 07-27, both **still unread**, for a test that expired 27 Jul 18:00.
  The widening in "Immediate next work" #6 remains **unbuilt**; this run did it by hand for the third time.
- ⚠️ **Known blind spot, unchanged:** the search keys on recruiter *company domains* harvested from
  `contact.md`. A recruiter replying from a personal address (gmail/outlook) would not be caught, and
  Easy-Apply-only rows like Recro have no `contact.md` at all — its domain was supplied by hand again.

## Accept watch — 2026-07-31 22:19 (a missed window, and the hole it exposed)

**Recruiter-C (GoodSpace, 85) ACCEPTED** at 22:06, detected by the 22:03 scheduled run — so all three
original invites have now been accepted; **nothing is `pending` any more.** His pitch is scheduled
**2026-08-01 09:46**. Whether that accept reached Slack is unconfirmed: the 22:03 run wrote its header and
its `mark-accepted`, then died without an end marker, and the log has no summary.

**Recruiter-B's pitch did NOT go out at 16:28** — the laptop was asleep. It was still sitting `due` at
22:19, and a watch run was in flight that would have sent it at ~22:20.

### ⚠️ "Business hours only" was documentation, not code (fixed)

`schedule_followup` shifts a due time into 09:00–21:00 **at the moment of acceptance**. Nothing rechecked the
clock at **send** time, and `cmd_due` filtered on `followup_due_at <= now` alone. Consequence: a due time that
lapsed while the machine slept stayed due indefinitely, and since Windows fires every missed task at once on
wake, the next watch could have delivered a cold recruiter a CV pitch at 02:00. The delay exists precisely so
the message doesn't read as a robot; this defect handed the robot the worst possible hour.

`cmd_due` now returns `[]` outside business hours and reports how many rows it is holding. Verified live:
`Nothing sendable: 22:22 is outside business hours (09:00-21:00). 1 ripe row(s) held for morning.`
The fix is one-directional — it can only ever *prevent* a send, never cause one.

**General lesson, same family as D17:** a guardrail written only in a runbook is a guardrail that holds
exactly as long as every future run is attentive. `cmd_due` is the single chokepoint every sender asks
"may I?", so that is where the rule belongs.

### Contention, observed live
Five tasks fired within seconds at 22:01 on wake — which is the exact scenario `tools/pipeline-lock.ps1`
(written earlier the same day) was built for, and it worked: one runner took the lock, the rest stood down.
Note the ordering trap for anyone editing `watch-accepts.ps1`: the **browser-profile guard runs before the
pipeline lock**, and it did not fire against an open interactive session, so the pipeline lock is what
actually did the excluding.

⚠️ Leftover to delete by hand: `tools/_tmp_test_due_gate.py` (scratch test; the sandbox refused to remove it).

## Daily discovery — 2026-08-01 (run in-session, per [[09-discovery-runbook]])

8 read-only `search_jobs` calls (DevOps / AI Engineer / Platform / MLOps / SRE / FDE / AI Eng Intern ×
India, `past_week`). **15 new rows inserted, board 79 → 94.** Slack digest posted. Zero sends.

**The two finds that matter — both JD-verified, not title-guessed:**
1. **SkillsCapital · Software Engineer Intern (AI/ML & Agentic AI) · Remote · fit 93** — the JD literally
   asks for a *"Final-year student or recent graduate"* and lists agentic AI, multi-agent workflows,
   LangChain, RAG, vector DBs, FastAPI, Docker, AWS. That is Azam's differentiator stack verbatim. Two
   application paths: Easy Apply **and** `careers@skillscapital.io` (wants resume + GitHub + projects +
   a note on what he built — the `profile/` dossier answers this directly). 6 days old, 100+ applicants.
   **Highest-fit row on the entire board**, above the Infosys Junior AI Engineer (90).
2. **CodeRound AI · Software Developer Engineer (Fresher) · Remote · fit 87** — *"No prior experience
   required"*, up to 11 LPA (above the 8.4 LPA ask), Easy Apply. CodeRound is already an engaged company.

One warm add: **Infosys · Devops Engineer · Pune (86)** — `1 connection works here` = Recruiter-A,
already 1st-degree. Noted in-row that the **Junior AI Engineer (90) is still the better Infosys play**;
don't spend Recruiter-A's goodwill on an on-site Pune DevOps req first.

### Three method notes worth keeping

1. **`sort_by="date"` wrecks the search.** The first DevOps run with `sortBy=DD` returned ML interns,
   full-stack, Workday and mechanical-engineering posts — LinkedIn drops relevance entirely when sorting by
   recency. Re-running the *same* keywords on default relevance returned actual DevOps reqs. Use relevance
   plus `date_posted=past_week`; never `sort_by=date`.
2. **A fresh posting can already be closed.** VIAN's `ML Engineer Intern` showed as *19 minutes ago* in
   search and read **"No longer accepting applications"** in the JD. Search-result metadata does not carry
   application status — one `get_job_details` is what caught it. This is the concrete argument for the
   07-30 "re-score before building" caveat: title-level rows can be dead on arrival.
3. **Scores on this board are compressed and therefore near-useless for ranking.** Before today, ~70 of 79
   rows sat in 80–89, so "84" carried no information. This run scored against the *actual* candidate — a
   final-year student with no professional experience — which pushes generic on-site body-shop reqs into
   the 74–78 range where they belong, and lets genuine fits (fresher/intern titles, remote, agentic stack,
   warm ties) separate at the top. ~27 candidates were dropped below 80 on that basis and 7 more excluded
   purely on level (Eicore Engineering Lead is JD-confirmed **10+ years**). The threshold was **not**
   changed; the honesty of the scoring was.

### ⚠️ Runbook step 5b did NOT run — deliberately

Four rows cleared the ≥85 auto-packet bar (93 / 87 / 86 / 85). No packets were built, for two stacked
reasons: `build-packet.ps1`'s guard counts MCP servers and **refuses while any Claude session is open**
(this run was interactive), and `build-packet.ps1` / `sweep-packets.ps1` are still **missing from the
allowlist** — the open owner-only item below. The packet gap is now **~90 rows with 4 packets**, and
discovery is still outrunning processing roughly 4:1. Adding rows is no longer the bottleneck-relieving act.

### Notion write gotcha
`notion-create-pages` rejects the `URL` property by display name — it must be written as
**`userDefined:URL`** (the error text tells you, but only after a failed 400). `Job`, `Company`,
`Fit Score`, `Status`, `Found`, `Location`, `Work Type`, `Source`, `Warm Intro` and `Notes` all take their
plain display names; only `URL` is prefixed. Checkboxes take `"__YES__"` / `"__NO__"`. The failed call wrote
nothing — verified by re-counting rows (79) before retrying, which is the right move whenever a bulk create
errors mid-flight.

### Not inserted, but flag for the owner
**ElevenLabs · Forward Deployed Engineer – Software Engineer – India · Remote · ~1 week old.** Surfaced
only in a *sidebar* ("More jobs") of another posting — it did **not** appear in the dedicated
`Forward Deployed Engineer` search. FDE-at-a-top-AI-lab is one of the best shapes on this board, so the
search is demonstrably missing good roles. No confirmed job ID was captured, so no row was created rather
than inserting a guessed URL. Worth one manual look.

## Accept watch — 2026-08-01 10:50 (1 sent, 1 held on a stale time word)

Ran per [[13-accept-watch-runbook]]. `expire`: nothing over 14 days. `list --status pending`: **empty** — all
three original invites are accepted, so stage 1 has no open knocks. `due`: **2 ripe**, both inside business
hours (10:50 IST), under the cap of 3.

- ✅ **Recruiter-C (GoodSpace AI, FDE 85) — 2b SENT.** Accepted 07-31 22:06, due 09:46, sent 10:5x.
  `mark-sent` logged immediately. Notion note appended, `Follow-ups Sent = 0`.
- ⏸️ **Recruiter-B (Innova ESI, DevOps 87) — HELD, left `due`.** Escalated to the owner instead.

### ⚠️ A time-relative phrase rots while a message sits in the queue

Her approved 2b opens *"I emailed you yesterday"*. That was true for the intended 07-31 16:28 send. The laptop
slept through the 31st, so at the 08-01 send the email is **two days old** and the sentence is false — and
falsifiable in one glance at her own inbox, in the very message whose job is to prove he pays attention.

Neither available move was mine to make alone: editing costs approved words (the owner's call, per
"Immediate next work" #4), sending costs a true statement. So it was **held and escalated** — the runbook's
own "if a slot cannot be resolved, skip and say so", applied to a slot that resolved fine when approved and
came unstuck later. Slack asked for a one-word decision: send as is, or swap to "earlier this week".

**Generalise this:** relative time words (*yesterday, this week, just now, tomorrow*) are **unstable state**
in any message that is written now and sent later. The 3–20h delay plus sleep-catchup means every 2b can
land a day or more after drafting. Prefer absolute or open phrasing at draft time ("I emailed you on
Thursday", or just drop the clause). Worth a standing check in [[13-accept-watch-runbook]] alongside the
existing no-em-dash / no-markdown / no-unresolved-slot pass. Same family as the business-hours defect: a
guardrail that only holds if a human happens to be paying attention on the day.

### Two stale records this run corrected
1. Notion had **both** rows at `Applied` since the 07-30 email batch — this file still said `Invite sent`.
   Applied Date was **left at 07-30** rather than moved to today: the email was first contact and the
   Day-3/Day-7 cadence rightly runs from it. A LinkedIn DM after an email is a follow-up, not a new apply.
2. `output/outreach/goodspace/touch-2-linkedin.md` still carries pre-D12 headers — `status: draft` and
   `send: owner clicks send in the LinkedIn app (no auto-connect / no auto-DM)`. Sent anyway, on the D12
   record: the stage-1 ✅ approved the words, the 07-26 2b audit explicitly cleaned this file *for sending*,
   and `invite_tracker` had it `accepted` with a scheduled follow-up. **Innova's header was updated on 07-30
   because it was actively rewritten; GoodSpace's never was.** Fix the header, or a future run has to
   re-derive this same judgement from scratch.

## Accept watch — 2026-08-01 11:26 (the held pitch went out; the queue is now empty)

Second run of the day, after the 10:50 one. `expire`: nothing over 14 days. `list --status pending`: **empty**
— all three original invites are accepted, so stage 1 has no open knocks and there is nothing to poll. `due`:
**1 ripe row**, the one held this morning.

- ✅ **Recruiter-B (Innova ESI, DevOps 87) — 2b SENT** at 11:2x, 11:26 IST being inside business hours.
  `mark-sent` logged immediately; `due` now returns `[]`. Notion `Follow-ups Sent = 0`, note appended,
  **Applied Date left at 07-30** (the email was first contact; a later DM is a follow-up, not a new apply).
  Slack posted.
- **The escalation had already been resolved by the owner.** `touch-2-linkedin.md` now reads
  `✅ APPROVED BY OWNER 2026-07-30, amended 2026-08-01`, with *"yesterday"* → *"earlier this week"*. So the
  hold worked exactly as intended: the run stopped, asked, and the next run found a decision waiting.
  **Check the packet's own status line before re-escalating** — the answer may already be in the file.
- Guardrail pass before sending: no em-dashes, no markdown, no unresolved `{}`/`[]` slots **in the 2b body**.
  Note that a plain grep over the file hits a dozen em-dashes in the *metadata and commentary* lines; only
  lines 24-35 are what actually sends. Scope the check to the message body or it fails a clean file.
- Auth was verified the trustworthy way (a real `get_person_profile` call), which double-served as the
  1st-degree confirmation: she reads `· 1st`, *"Recruiter-B is a new connection"*.

### Her current reqs, observed in passing
Her last 2 days of posts are GCP DevOps (Gurgaon, 5+), Lead DevOps (Bengaluru, 8-13, K8s + Terraform + SRE),
Python Agentic AI (5-9), AI Lead / Sr AI Engineer GenAI+AWS (8+). **Every one is mid-to-senior**, so the
approved 2b's "Azure AKS + GCP GKE, Kubernetes, Terraform" line still lands true, but she has no fresher-level
req open right now. Temper expectations on this one; the relationship is worth more than this specific role.

## Packet build — Mirai Alpha, 2026-08-01 (built; the role may already be gone)

Row `3ae29d9d-9c6e-8153-aeb3-f5a5bcaadafd`, built per [[15-build-packet-runbook]].
`output/outreach/mirai-alpha/`, **ATS 90**, status `To Apply` in Notion and the mirror, Slack card
unticked, **nothing sent**. Second packet built by hand in two days, so the backlog is 94 rows / 6 packets.

- ⚠️ **The LinkedIn posting is CLOSED** — `get_job_details` returned *"No longer accepting
  applications"*. Posted 07-31, 100+ applicants, shut inside ~24h. This is the second time the
  07-30 "re-score before building" caveat has paid for itself (VIAN was the first), and it is now
  **2 for 2**: every title-level row checked against its real JD has revealed something the search
  result did not carry. Fetch the JD before spending a build.
- **Built anyway, deliberately.** The JD publishes `info@miraialpha.in` and demands a written answer to
  *"the most challenging AI project you've built ... what went wrong, and what did you learn"*. That
  route is not gated by the Easy Apply queue, and at a **two-person company** the founders read that
  inbox. The closure is stated in the **first line of the Slack card title** so the owner decides with
  it visible. If he judges the req dead, the right action is ❌ and `Skipped`.
- **Re-scored 92 → 93 on the real JD.** It names MCP server authorship, multi-agent workflows, RAG over
  vector DBs *and* knowledge graphs, and evaluation for accuracy/reliability/latency/cost. It also says
  *"we're not hiring based on resumes"* and wants people who build outside college, which converts
  Azam's weakest column into his strongest. Drag: Bengaluru **hybrid**, not remote.
- **No warm insider, verified not assumed.** `get_company_employees` returns **2 members** for a 2-10
  person company, both co-founders, both 3rd degree, school = VIT not CUK. Recorded as a negative in
  `contact.md` per the never-invent-a-contact rule. ⚠️ Kashmiri-sounding names in the scraped profile
  references are LinkedIn *"people you may know"* sidebar suggestions, **not employees** — a trap for
  the next session that greps for a warm tie.
- **ATS 90 computed by hand again.** `ats_audit.py` auto-denied for the second build running. 29 of 32
  JD keywords present; the 3 misses are `finance` / `wealth management` / investment-domain terms,
  left out because nothing in `profile/` backs them. The cover letter names the gap outright.
- **`miraialpha.in` MX UNCHECKED** — `Resolve-DnsName` and `nslookup` both need approval. Decides the
  Drive sharing mode before the PDF goes out ([[drive-sharing-mx-decides]]).

### New tool, and the allowlist bites a third time
`tools/set_status.py` was written this run because **nothing could set the mirror's status from a
shell** — only `serve_dashboard.py` called `board_db.set_status`, so runbook step 7 had no CLI and
inline `py -3 -c` is refused. It is **not allowlisted**, so it could not be used the day it was
written. The mirror was updated instead by writing the Notion row to
`output/dashboard/mirai-alpha-row.json` and running the allowlisted `sync_board.py` — Notion is the
system of record, so syncing *down* from it is the cleaner path anyway and needs no new permission.

**Allowlist entries still missing (owner-only, an AI is blocked from adding them):**
```
"Bash(py -3 tools/set_status.py:*)",
"Bash(py -3 tools/ats_audit.py:*)",
"Bash(powershell -ExecutionPolicy Bypass -File tools/sweep-packets.ps1:*)",
"Bash(powershell -ExecutionPolicy Bypass -File tools/build-packet.ps1:*)",
```

### Convention worth knowing before writing any packet
`slack_action_card.py` parses the packet, and it is **strict**: `contact.md` needs an `# Contact — ...`
H1, a literal `fit NN`, and `- name:` / `- linkedin_url:` / `- apply_url:` field lines; the 2b message
must be a **blockquote under a `## 2b` heading**. Written in the obvious prose style instead, the card
posts `(2b message missing)` and the ⭐ warm marker silently never fires. Copy an existing packet's
shape rather than inventing one, and always `--dry-run` first.

## Packet build — Hired, 2026-08-01 (built as instructed; the honest answer is SKIP)

Row `3a829d9d-9c6e-812a-88c3-c383af51581b`, built per [[15-build-packet-runbook]].
`output/outreach/hired/`, **ATS 69 (not 90)**, status `To Apply` in Notion and the mirror, Slack card
unticked, **nothing sent**. Third packet built by hand in two days; backlog is 94 rows / 7 packets.

**Re-scored 88 → 62.** Three independent findings, none visible when the row was scored on 07-25:

1. ⚠️ **Posting CLOSED** and, unlike Mirai Alpha, **no email route exists**. The JD says *"Responses
   managed off LinkedIn"* and prints no address. The closure removes the only route ever offered.
   Fetching the JD is now **3 for 3** at revealing something material (VIAN, Mirai Alpha, this).
2. ⚠️ **Hired is a STAFFING AGENCY**, 11-50 people, `hiredd.in`, placing at an **unnamed client**
   (*"We are hiring for one of our clients"*). That kills the pipeline's strongest lever: there is no
   company to research, so no specific detail can prove Azam paid attention. **Hired has SIX rows on
   the board** (AI/ML 88, DevOps 86, GenAI 85, FDE 85, AWS 82, SRE 82) — one packet covers all, per
   runbook step 3. A prior session had already written the warning into the SRE row's note:
   *"Hired reposts the same listings under new job IDs constantly."* Confirmed: reposts were live in
   both the JD sidebar and an independent `search_jobs` run.
3. ⚠️ **Senior req, and the stack is Azam's thinnest area.** Title *Member of Technical Staff*,
   **$160-300K/yr** against his 8.4 LPA / $30K ask. Required skills are **classical ML** (TensorFlow,
   supervised/unsupervised algorithms, Pandas, NumPy). The JD mentions RAG, LLM and agents **zero
   times**. The 07-25 note *"Strong RAG/LLM match; not senior-gated"* is false on **both** counts.

### ⚠️ ATS 69, and the shortfall is the finding, not a tailoring failure

22 of 32 JD keywords present. The 10 missing are TensorFlow, machine learning algorithms, supervised
learning, unsupervised learning, feature engineering, model training, Pandas, NumPy, GCP, Azure —
**every one a genuine candidate gap**, left out rather than fabricated. `profile/master-profile.md`
is explicit on the cloud ones: *"Cloud = private cloud + Kubernetes (he built a cloud), not
public-cloud certifications — frame honestly."*

**A low ATS score here is the measurement working.** If Azam confirms coursework Pandas/NumPy/
TensorFlow it reaches ~78-81; it **cannot** reach 90, because supervised/unsupervised learning,
feature engineering, model training, GCP and Azure are the JD's own core requirements. His call.
`ats_audit.py` was auto-denied for the **third** build running, so this was computed by hand again.

**No warm insider, verified:** 6 members, education = Marathwada / UT Austin / Cornell / Sharda (**no
CUK**), locations India ×2 / Santo Domingo / Nigeria / US / Norway (**no Kashmir tie**). Five of six
are anonymised "LinkedIn Member". Only **Recruiter-D** (Recruitment Consultant, part-time, 3rd
degree) resolves to a name, and the 2b is deliberately pitched at *being kept on file*, not at the
dead req.

### 🪤 The PYMK trap is CONFIRMED, not a one-off
**PYMK-1 (name redacted)** and **PYMK-2 (name redacted)** appear in the scraped references of Shubham
Bodkhe's profile — **the same two names** flagged in the Mirai Alpha packet. They are LinkedIn
*"people you may know"* suggestions rendered against Azam's own account on **every** profile page
scraped, not employees of either company. Any future session grepping a packet for a Kashmiri warm
tie will hit these. They are never a warm path.

⚠️ **Flagged, not acted on:** the already-sent Innova ESI 2b claims *"Azure AKS + GCP GKE"*. Nothing
in `profile/` backs Azure or GCP, and master-profile explicitly forbids that framing. Already
delivered, so it is the owner's to judge — but do not repeat it in a new CV.

## Reply check — 2026-08-06 (fourth clean run; the EPAM test was CANCELLED)

Same 5 `Applied` rows (Infosys, CodeRound AI, Recro, Innova ESI, GoodSpace AI), same 5 domains.
**Zero recruiter replies. No Notion writes** — correct per the de-dupe rule; every row still reads
`Reply = ☐`, `Status = Applied`.

- **Query proven before the zero was believed**, per the standing rule: bare `newer_than:14d in:inbox`
  returned **201** threads and `(from:linkedin.com OR from:infosys.com)` returned **24**. Only then was
  the empty 5-domain result trusted. Widened to `newer_than:30d in:anywhere` — also empty.
- **Bounces clean** at `newer_than:14d in:anywhere`.
- ✅ **The personal-address blind spot was closed this run, not just noted.** A name/company sweep
  (`recruiter-b OR recruiter-c OR chaitanya OR recruiter-a OR "Innova ESI" OR GoodSpace OR CodeRound OR Recro`,
  minus LinkedIn noise) returned **only Azam's own three SENT emails from 07-30** and unrelated
  newsletters. So no recruiter has replied from a gmail/outlook address either. Worth keeping as the
  standard fifth query — it costs one call and it is the one hole the domain search cannot see.
- 🆕 **EPAM: the test was CANCELLED, not merely missed.** DoSelect emailed **2026-08-05 12:41**:
  *"Your invite ... has been cancelled by the test administrator. You will no longer be able to take
  this assessment."* This **closes the 07-30 finding**: the CUK freshers test that "expired unseen" on
  27 Jul was called off by EPAM, so the missed deadline cost nothing. The campus channel is still
  **invisible to the board** (EPAM has no Notion row), so this was again caught only by the by-hand
  sender sweep — the fourth run in a row to do that work manually. "Immediate next work" #6 is still
  **unbuilt**, and it has now surfaced two real, time-boxed items.
- Slack posted (`--event info`): zero replies + the EPAM cancellation, marked as needing no action.

### ⚠️ `slack_notify.py --dry-run` crashes on a Windows console; the real send does not
`print("DRY RUN →", ...)` dies with `UnicodeEncodeError: 'charmap' can't encode '→'` under cp1252.
**The payload is fine** — the send path encodes UTF-8 explicitly and prints pure ASCII, so posting works.
Same family as the `mcp-server-linkedin --status` bug: *a tool crashing while printing its own decoration
tells you nothing about the operation.* Note `PYTHONIOENCODING=utf-8 py -3 ...` is **not** a workaround
here — the env-var prefix changes the command string and **misses the allowlist**, so it gets refused.
Either fix the print with `ensure_ascii=True`/a plain arrow, or skip `--dry-run` on Windows.

### Follow-up cadence is overdue on all five (flagged, not acted on)
Applied dates are 07-26 (Infosys, CodeRound) and 07-29/07-30 (Recro, Innova ESI, GoodSpace); today is
**08-06**. Every row is past both its Day-3 and Day-7 nudge with `Follow-ups Sent` at 0 or null, and
Infosys still carries a `Next Action` of **2026-07-29**. That is `followups.py`'s job, not this
runbook's — but eleven days of silence across five applications is the board's loudest signal right now.

## Accept watch — 2026-08-06 16:23 (nothing accepted; three NEW invites found unrecorded)

Ran per [[13-accept-watch-runbook]]. `expire`: nothing over 14 days. `due`: **empty**. All three polled
profiles still read `· 3rd`. **Nothing sent, nothing written to Notion, no Slack post** — runbook step 5's
quiet exit. Auth verified the trustworthy way (three real `get_person_profile` calls succeeded).

⚠️ **The tracker holds three `pending` invites that this file did not know about.** Sent **today**, 11:02 /
11:32 / 11:34, by a session that never wrote them down — the exact failure mode this file exists to prevent
(see the header note and [[05-decisions]] D7). Recorded now:

| Who | Company · role | Invite sent | Status at 16:23 |
|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 11:02 | `pending`, 3rd |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern (Agentic AI & MCP) | 08-06 11:32 | `pending`, 3rd |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer — pitched as keep-on-file | 08-06 11:34 | `pending`, 3rd |

So the stage-1 queue is **live again** for the first time since 08-01, and the ~4h watcher now has real work
to poll. Five hours old is early; judge nothing from one quiet run.

### Method note: the profile page states the invite status directly

Each of the three rendered **`Message` / `Pending`** in the top card, next to the degree. The runbook's
documented signal is the **degree flip** (2nd/3rd → 1st), and that remains the thing to act on — but
`Pending` is strictly better evidence for the *negative* case, because it separates two states the degree
alone conflates: **"sent, not yet accepted"** from **"the invite never actually went out."** That second
state is not hypothetical here — it is exactly the D12 `custom_note_limit_reached` silent failure, where
`connect_with_person` returns success and sends nothing. A row sitting `pending` for days with **no**
`Pending` badge on the profile means stage 1 lied, not that the recruiter is ignoring us. Read the badge
whenever a row looks stuck.

⚠️ **`last_checked` stays `null` after a poll.** `invite_tracker.py` only stamps it inside `mark-accepted`,
so a run that polls three profiles and finds nothing leaves no trace in the state file, and the next session
cannot tell a polled row from a never-polled one. Minor, but it means "when was this last checked?" is
currently only answerable from this file and the task logs.

### PYMK trap, third confirmation
`Arshid Hussain` and `Ahzam Mushtaq` (Kashmiri-sounding) appear in the scraped `references` of the
SkillsCapital and Hired profiles respectively. Same class as the two names flagged in the Mirai Alpha and
Hired packets: LinkedIn **"people you may know"** suggestions rendered against Azam's own account on every
profile page, **not** employees. Never a warm path — see the Hired packet section above.

## Accept watch — 2026-08-09 (BLIND RUN: the poll could not happen at all)

Ran per [[13-accept-watch-runbook]]. **Steps 1 and 3 completed; step 2 did not run.** Nothing was sent,
nothing written to Notion, no Slack post.

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The three invites are 3 days old
  (sent 08-06 11:02 / 11:32 / 11:34), so the 14-day wall is 08-20.
- **Step 3 `due`:** `[]`. Correct — nothing can be due, because nothing has been marked accepted.
- **Step 2 (did they accept?): BLOCKED.** The three rows are still `pending` in the tracker, and this run
  **could not determine whether that is true or merely unobserved.**

### ⚠️ The accept watcher has a single point of failure on a *read*, and it fired

**`mcp-server-linkedin` had no tools in this session.** Not an auth error, not a session expiry, not the
D13 profile lock — the server registered zero tools, so `get_person_profile` did not exist to call. Verified
by four separate `ToolSearch` lookups (exact-name select, then three keyword searches) several minutes apart,
plus a resource listing. This is a different failure from every LinkedIn problem recorded above, and none of
the existing diagnosis ladders apply: there was no error message to misread, because there was no tool.

**Consequence:** the accept signal is unobservable through the documented path. The 4-hourly watcher would
report the same three `pending` rows indefinitely and look completely healthy doing it — the "quiet exit" in
step 5 is indistinguishable from total blindness. Same family as [[failed-query-is-not-an-empty-queue]]:
**a poll that cannot run and a poll that finds nothing produce identical output.**

### The fallback is written but has never executed

`tools/poll_invites.py` (new) reads the same signal off the profile page with the Playwright profile Phase 0
proved logged in — navigate and read only, no clicks, no connects, no messages. Sending stays on the MCP.
It reports the **degree** (the signal to act on) alongside the **`Pending` badge**, which separates
"sent, not yet accepted" from "the invite never went out" (the D12 silent-send failure).

⚠️ **It has never been run.** It is **not in `.claude/settings.json` → `permissions.allow`**, so it was
refused the moment it was written — the allowlist trap, for the fourth time in this project, and an AI is
blocked from fixing it. **Treat the tool as unverified until someone runs it once.**

**Owner action — one line, and the watcher can see again:**
```
"Bash(py -3 tools/poll_invites.py:*)",
```

### What is actually unknown right now
Whether **Recruiter-E (SkillsCapital, CTO)** accepted. That is the **93-fit row, the highest on the board**,
whose JD asks for exactly this candidate. If he accepted on, say, 08-07, the pitch is two days late and
nothing in the system knows. The other two are Mirai Alpha (Recruiter-F) and Hired (Recruiter-D).

## Accept watch — 2026-08-09 later (the blind spot cleared; all three genuinely still pending)

Second run of the day, after the BLIND RUN above. **All three steps completed this time.** Nothing accepted,
nothing due, nothing expired → runbook step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` Wall is 08-20.
- **Step 2 (the poll that failed this morning):** `mcp-server-linkedin` **registered normally this session**
  and all three `get_person_profile` calls succeeded.

| Who | Company · role | Degree | Badge | Verdict |
|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | `3rd` | `Pending` | not accepted |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | `3rd` | `Pending` | not accepted |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | `3rd` | `Pending` | not accepted |

- **Step 3 `due`:** `[]`. Correct — nothing is accepted, so nothing can be ripe.

### ⚠️ The morning's blindness was SESSION-SCOPED, not a broken install

This is the correction that matters. The BLIND RUN above concluded the LinkedIn MCP had no tools, verified
across four `ToolSearch` lookups. **Hours later, same machine, same config, the tools were simply there.**
So the failure is a **per-session MCP registration flake**, not a persistent breakage — nothing was fixed
between the two runs, and no fix should be hunted for. Same family as the D13 "session expired" false alarm
and [[usage-limit-before-clever-theories]]: **the second observation is what decides which reading was
right.** Practical rule: when the LinkedIn tools are missing, **retry in a fresh session before concluding
anything** — and never let a blind run's silence be recorded as a healthy quiet exit.

### What this run actually buys

The three `Pending` badges settle the open question from the BLIND RUN — *"did Recruiter-E accept days ago
and nobody noticed?"* **No.** All three invites are genuinely delivered and genuinely unanswered at 3 days
old, so no pitch is late. The badge also re-confirms stage 1 did not silently fail (the D12
`custom_note_limit_reached` hole): a row `pending` **with** a `Pending` badge is real; without one, stage 1
lied.

- ⚠️ **`last_checked` is still `null` on all three.** `invite_tracker.py` only stamps it inside
  `mark-accepted`, so this run polled three profiles and left **no trace in the state file** — for the second
  time today. This section is the only record that the poll happened. Still worth a one-line fix.
- `tools/poll_invites.py` remains **unrun and un-allowlisted**; the MCP path worked, so the fallback was not
  needed this run. It is still the right insurance for the next flake. Owner line, unchanged:
  `"Bash(py -3 tools/poll_invites.py:*)",`
- 🪤 **PYMK trap, fourth confirmation.** Kashmiri-sounding names appear again in the scraped `references` of
  both the SkillsCapital and Hired profiles. They are LinkedIn "people you may know" suggestions rendered
  against Azam's own account on every profile page. **Never a warm path.**
- 👀 **Observed in passing:** Recruiter-F is now hiring a *Founder's Office Intern — Research & Strategic
  Growth* (Bengaluru, hybrid). That is a research/strategy req, **not** the engineering role Azam was
  pitched for, and the original AI Engineering Intern posting is closed. Do not silently re-aim the packet
  at it — it is a different job.

## Reply check — 2026-08-09 (fifth clean run; zero replies, but FIVE applications went out unrecorded)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82), same 5
domains. **Zero recruiter replies. No Notion writes** — correct per the de-dupe rule; every row still reads
`Reply = ☐`, `Status = Applied`.

- **Query proven before the zero was believed**, per the standing rule: bare `newer_than:14d in:inbox`
  returned **201** threads and `(from:linkedin.com OR from:infosys.com)` was live. Only then was the empty
  5-domain result trusted. Widened to `newer_than:30d in:anywhere` — also empty.
- **Bounces clean** at `newer_than:14d in:anywhere`.
- **Personal-address sweep run again** (the standard fifth query): returned **only Azam's own sent mail**.
  No recruiter has replied from a gmail/outlook address either.
- **Campus channel: nothing new.** The scoped sender sweep (naukricampus, doselect, hackerrank, hackerearth,
  mettl, imocha, codility, epam, hirevue) returned only the three known EPAM items, the newest being the
  **08-05 cancellation**. Closed on 08-06 and still closed. Fifth run in a row done by hand; "Immediate next
  work" #6 is still **unbuilt**.
- Slack posted (`--event info`) — zero replies plus the submission finding below.

### 🚨 FIVE Easy Apply submissions went out today and **nothing recorded them**

This is the run's real finding, and it did not come from the reply search — it came from the LinkedIn
`jobs-noreply@` acks sitting in the inbox. **Every job ID was matched against the board**, not guessed:

| Time (08-09) | Company · role | LinkedIn job ID | Notion row said |
|---|---|---|---|
| 09:35 | Energy Exemplar · DevOps Engineer (72) | `4436200537` | `To Apply` |
| 10:43 | SkillsCapital · Site Reliability Engineer (83) | `4446772164` | `New` |
| 10:46 | SkillsCapital · DevOps Engineer (82) | `4444671688` | `New` |
| 10:48 | Crossing Hurdles · DevOps Engineer $60/hr (82) | `4444896795` | `New` |
| 10:50 | SkillsCapital · Cloud Engineer (82) | `4444834246` | `New` |

**This is the Recro trap again** ([[20-first-email-batch-and-task-verification]]): a real submission that the
board does not know about is one sweep away from a **duplicate application to the same employer**. The rows
were left untouched this run because recording submissions is the apply runbook's job, not this one's — but
they must be set to `Applied` with today's date before anything else touches them.

- ⚠️ **The three SkillsCapital sends are the WRONG three.** The 08-01 packet note warned explicitly:
  SkillsCapital has four board rows and **only the SWE Intern (AI/ML & Agentic AI, fit 93) is in-house** —
  SRE 83 / Cloud 82 / DevOps 82 are SkillsCapital placing candidates *at a client*. All three client rows
  were applied to; **the 93 was not.** It still reads `Invite sent`. The single highest-fit row on the board,
  whose JD asks for exactly this candidate, remains unsent while three lower-value staffing reqs consumed the
  approach. Whatever selected these jobs is ranking by something other than fit score.
- **Nothing here is a reply**, so nothing was ticked. `Reply = ✓` on a "your application was sent to X"
  auto-ack would silently kill the Day-3/Day-7 nudges — see [[linkedin-autoack-is-not-a-reply]].

### The one inbound that looks like a reply and is not

`notifications@ceipalmail.com`, **10:48:47 — four seconds after** the Crossing Hurdles submission. Reads like
a personal note (*"I'm from Crossing Hurdles, we would like to refer you"*) but it is a templated ATS
auto-response that funnels the applicant to **`jobs.micro1.ai` with a referral code**. Classified
**Auto-ack**, no action, no Notion write. Worth knowing the shape: a staffing firm's ATS can answer within
seconds, in the first person, and it is still not a human. Timestamp proximity to your own submission is the
cheapest tell.

### Follow-ups did go out — the 11-day silence was broken this morning

The name sweep turned up **three follow-up emails sent 2026-08-09 10:00** to Innova ESI, GoodSpace and
CodeRound (`Re:` on the original 07-30 threads). So the overdue Day-3/Day-7 cadence flagged on 08-06 has
been actioned for three of the five. **Infosys and Recro still have none.** Notion `Follow-ups Sent` was
**not** incremented by whatever sent them, so the counter still reads 0/null on all five and will keep
reporting the nudges as never sent.

> ⚠️ **Corrected 2026-08-10: it was FOUR follow-ups, not three.** The same 10:00 batch also sent
> `Re: Software Engineer Intern (AI/ML & Agentic AI)` to **`careers@skillscapital.io`**. It was missed here
> because the 08-09 name sweep keyed on recruiter first names and the five `Applied` companies, and
> SkillsCapital is neither. See the 08-10 reply check below for what that changes.

## Accept watch — 2026-08-10 (all three still pending, day 4; quiet exit)

Ran per [[13-accept-watch-runbook]]. **All three steps completed.** Nothing accepted, nothing due, nothing
expired → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` Wall is 08-20.
- **Step 2 (the poll):** `mcp-server-linkedin` registered normally; all three `get_person_profile` calls
  succeeded, which is also the trustworthy auth check.

| Who | Company · role | Degree | Badge | Verdict |
|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | `3rd` | `Pending` | not accepted |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | `3rd` | `Pending` | not accepted |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | `3rd` | `Pending` | not accepted |

- **Step 3 `due`:** `[]`. Correct — nothing accepted, so nothing can be ripe.

### Nothing new, and that is the point of writing it down

Third consecutive run reading identically (08-06 16:23, 08-09 later, today). The `Pending` badges keep
confirming stage 1 did not silently fail (the D12 `custom_note_limit_reached` hole), so the invites are
genuinely delivered and genuinely unanswered at **4 days old**. That is still normal latency for a cold
connect; no pitch is late.

- ⚠️ **`last_checked` is still `null` on all three** — `invite_tracker.py` only stamps it inside
  `mark-accepted`, so this run polled three profiles and again left **no trace in the state file**. Third
  time recorded. This section remains the only evidence the poll happened.
- `tools/poll_invites.py` is still **unrun and un-allowlisted**. The MCP path worked again, so the fallback
  was not needed — it stays the insurance against the 08-09 morning registration flake.
  Owner line, unchanged: `"Bash(py -3 tools/poll_invites.py:*)",`
- 🪤 **PYMK trap, fifth confirmation.** Kashmiri-sounding names appear again in the scraped `references` of
  the SkillsCapital and Hired profiles. LinkedIn "people you may know" suggestions, **never a warm path**.
- 👀 **Recruiter-F's profile still advertises only the *Founder's Office Intern — Research & Strategic
  Growth*** req; the AI Engineering Intern posting she was pitched for stays closed. Unchanged from 08-09 —
  do not silently re-aim the packet at a different job.

### ⚠️ The LinkedIn channel to SkillsCapital is idle while the email route sits unused

Not this runbook's job to fix, but it is the same company twice over and worth stating in one place: the
**93-fit SWE Intern row** has an invite pending with the CTO since 08-06 **and** a direct
`careers@skillscapital.io` path that has never been used, while the 08-09 batch applied to the **three
client-placement SkillsCapital rows instead** (SRE 83 / Cloud 82 / DevOps 82). Waiting on this accept is
not the only move available, and it is currently the only one being made.

> ⚠️ **STRUCK 2026-08-10 — the email route was NOT unused; it was used twice.** Gmail holds an application
> to `careers@skillscapital.io` sent **2026-08-01 12:45** and a follow-up on the same thread **2026-08-09
> 10:00**. So the 93-fit row has had *three* approaches (email, follow-up, pending CTO invite) and has
> simply had no answer to any of them. The paragraph above was written from the packet files and the Notion
> row, neither of which records a send — **`Status = Invite sent` with no `Applied Date` is not evidence
> that nothing went out.** Check the Sent folder before declaring a channel unused; this is the same class
> of error as the five unrecorded Easy Apply submissions.

## Reply check — 2026-08-10 (sixth clean run; zero replies, and a channel wrongly recorded as unused)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82), same 5
domains (`infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `recro.io`). **Zero recruiter
replies. No Notion writes** — correct per the de-dupe rule; every row still reads `Reply = ☐`,
`Status = Applied`, and no row's classification changed.

- **Query proven before the zero was believed**, per the standing rule: bare `newer_than:14d in:inbox`
  returned **201** threads and `(from:linkedin.com OR from:infosys.com)` was live. Only then was the empty
  5-domain result trusted. Widened to `newer_than:30d in:anywhere` — also empty.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable /
  Delivery Status Notification / Address not found).
- **Personal-address sweep run again** (the standard fifth query): the only inbound hits were the two
  auto-acks below. No recruiter has replied from a gmail/outlook address.
- **Campus channel: nothing new.** The scoped sender sweep (naukricampus, doselect, hackerrank,
  hackerearth, mettl, imocha, codility, hirevue, epam) returned only the three known EPAM items, newest
  still the **08-05 cancellation**. Sixth run in a row done by hand; "Immediate next work" #6 is still
  **unbuilt**.
- Slack posted (`--event info`). No `--event reply` alert fired, because nothing was a reply.

### Two auto-acks, both correctly NOT ticked

| From | When | Verdict |
|---|---|---|
| `no-reply@energyexemplar.com` — *"Thank you for applying to Energy Exemplar"* | 08-09 09:36 | **Auto-ack** |
| `notifications@ceipalmail.com` — Crossing Hurdles / Micro1 referral template | 08-09 10:48 | **Auto-ack** (already classified 08-09) |

The Energy Exemplar one is new to this file. Read FULL: *"we have received your application, and ... we're
looking forward to reviewing it in due course."* No human, no next step, no action.
Ticking `Reply = ✓` on either would silently kill the Day-3/Day-7 nudges — [[linkedin-autoack-is-not-a-reply]].

**It is still worth something as evidence.** It arrived **1 minute after** the 09:35 Easy Apply submission,
from the *employer's own ATS* rather than from LinkedIn. That is independent confirmation the Energy
Exemplar submission genuinely reached the company, which a `jobs-noreply@linkedin.com` ack alone cannot
prove. Same tell as the Ceipal case, read the other way: **timestamp proximity to your own submission
identifies an auto-ack, and a non-LinkedIn sender identifies which system actually received you.**

### 🚨 The five 08-09 submissions are STILL unrecorded, now day 2

Re-checked in Notion this run, not assumed:

| Company · role | Fit | Notion still says |
|---|---|---|
| Energy Exemplar · DevOps Engineer | 72 | `To Apply` |
| SkillsCapital · Site Reliability Engineer | 83 | `New` |
| SkillsCapital · DevOps Engineer | 82 | `New` |
| SkillsCapital · Cloud Engineer | 82 | `New` |
| Crossing Hurdles · DevOps Engineer $60/hr | 82 | `New` |

All five still `New`/`To Apply` with `Applied Date` null. Recording them is the apply runbook's job, not
this one's, so they were again left untouched — but this is the **Recro trap** ([[20-first-email-batch-and-task-verification]])
sitting open for a second day, and every one of them is one sweep from a duplicate application.

### ⚠️ A channel was recorded as "never used" while two emails sat in Sent

The finding worth keeping. This file stated the `careers@skillscapital.io` route "has never been used".
Gmail says otherwise: an application **2026-08-01 12:45** and a follow-up on the same thread **2026-08-09
10:00**. Both struck through above.

The error is structural, not careless. The claim was derived from the **packet files** and the **Notion
row** (`Invite sent`, `Applied Date` null) — and *neither of those is written by the act of sending an
email*. Notion's `Status` only moves when a runbook moves it, so an absence there records "no runbook
recorded a send", never "no send happened". This is the same failure as the five rows above and as Recro
before them, and it has now produced a wrong sentence in the project's own live-state file.

**Practical rule: the mailbox is the system of record for what left the building.** Before writing that a
channel is idle, unused or silent, search Sent for the address. It is one query and it is the only source
that cannot be out of date. Note also that the 08-09 name sweep missed this because it keyed on the five
`Applied` companies and the recruiters' first names — **any company you have emailed but not marked
`Applied` is invisible to that query by construction.** Sweep by address, not only by company.

## Reply check — 2026-08-10 later (seventh clean run; nothing new since the morning run)

Second run of the same day, re-run on request. Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova
ESI 87, GoodSpace AI 85, Recro 82), same 5 domains. **Zero recruiter replies. No Notion writes, no
`--event reply` alert.** Every row still reads `Reply = ☐`, `Status = Applied`.

- **Query proven before the zero was believed:** bare `newer_than:14d in:inbox` returned **201** threads and
  `(from:linkedin.com OR from:infosys.com)` was live. Widened to `newer_than:30d in:anywhere` — also empty.
- **Bounces clean** at `newer_than:14d in:anywhere`. **Campus sweep** returned only the three known EPAM
  items, newest still the 08-05 cancellation. Seventh run in a row done by hand; "next work" #6 still unbuilt.
- **Address sweep, not just company names** (the 08-10 morning lesson applied): the recruiter-name +
  company query now also carries `SkillsCapital`, `Energy Exemplar` and `Mirai Alpha`. It returned **only
  Azam's own sent mail** — the 07-30 batch, the 08-01 SkillsCapital application and the four 08-09 10:00
  follow-ups. No recruiter has replied from a personal address either.
- **A control for "has anything arrived at all?"** — `newer_than:2d in:inbox` minus the known newsletter
  senders returned 5 threads, all marketing plus the two auto-acks already classified. Nothing inbound is
  unaccounted for.
- Slack posted (`--event info`).

### Nothing was reclassified, and no new mail arrived

The two auto-acks (`no-reply@energyexemplar.com` 08-09 09:36, `notifications@ceipalmail.com` 08-09 10:48)
are unchanged from the morning run and stay **Auto-ack** — ticking `Reply = ✓` on either would silently kill
the Day-3/Day-7 nudges ([[linkedin-autoack-is-not-a-reply]]). The classify/update/alert branches of this
runbook remain **unexercised**: seven runs, zero real replies, so no `Reply` tick and no `Status` move has
ever been written by this recipe.

### 🚨 The five 08-09 submissions are STILL unrecorded — day 2, third consecutive run flagging it

Re-queried, not assumed. Energy Exemplar DevOps (72) reads `To Apply`; SkillsCapital SRE 83 / DevOps 82 /
Cloud 82 and Crossing Hurdles DevOps $60/hr (82) all read `New`. **`Applied Date` is null on all five.**
Recording them is the apply runbook's job, not this one's — but this is the **Recro trap** open for a second
day, and each row is one sweep from a duplicate application to the same employer.

Also unchanged: **SkillsCapital SWE Intern (93)**, the highest-fit row on the board, still reads
`Invite sent` with a null `Applied Date` despite three real approaches (email 08-01, follow-up 08-09,
CTO invite pending since 08-06). Per the struck paragraph above, that status is **not** evidence nothing
went out — it means no runbook recorded it.

## Accept watch — 2026-08-10 later (second run of the day; identical, quiet exit)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` Wall is 08-20.
- **Step 2 (the poll):** all three `get_person_profile` calls succeeded — which is also the only trustworthy
  auth check, so the LinkedIn session is healthy.

| Who | Company · role | Degree | Badge | Verdict |
|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | `3rd` | `Pending` | not accepted |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | `3rd` | `Pending` | not accepted |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | `3rd` | `Pending` | not accepted |

- **Step 3 `due`:** `[]`. Correct — nothing accepted, so nothing can be ripe.

Fourth consecutive run reading identically. The `Pending` badges keep confirming stage 1 did not silently
fail (the D12 `custom_note_limit_reached` hole), so the invites are genuinely delivered and genuinely
unanswered at **day 4** — still normal latency for a cold connect; no pitch is late.

- ⚠️ **`last_checked` is still `null` on all three** — `invite_tracker.py` only stamps it inside
  `mark-accepted`, so this run polled three profiles and again left **no trace in the state file**. Fourth
  time recorded; this section remains the only evidence the poll happened.
- 👀 **Recruiter-F's profile still advertises only the *Founder's Office Intern — Research & Strategic
  Growth*** req; the AI Engineering Intern posting she was pitched for stays closed. Unchanged since 08-09 —
  do not silently re-aim the packet at a different job.
- 🪤 **PYMK trap, sixth confirmation.** Indian-name sidebar `references` on all three profiles are LinkedIn
  "people you may know" suggestions, **never a warm path**.

**The waiting is not the only move available.** The 93-fit SkillsCapital row has had three approaches with no
answer (email 08-01, follow-up 08-09, CTO invite pending since 08-06); nothing further on that row is this
runbook's to do. The open lever remains Track A #2: **Infosys Junior AI Engineer (90)**, where Recruiter-A is
inside and already 1st-degree, so no accept has to be waited for at all.

## Reply check — 2026-08-10 third run (eighth overall; zero replies, and THREE more unrecorded submissions)

Third run of the same day, re-run on request. Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova
ESI 87, GoodSpace AI 85, Recro 82), same 5 domains. **Zero recruiter replies. No Notion writes, no
`--event reply` alert.** Every row still reads `Reply = ☐`, `Status = Applied`; no classification changed.

- **Query proven before the zero was believed:** bare `newer_than:14d in:inbox` returned **201** threads and
  the `(from:linkedin.com OR from:infosys.com)` OR-group was live. Widened to `newer_than:30d in:anywhere`
  — also empty.
- **Bounces clean** at `newer_than:14d in:anywhere`. **Campus sweep** (naukricampus, doselect, hackerrank,
  hackerearth, mettl, imocha, codility, hirevue, epam) returned only the **08-05 EPAM cancellation**.
  Eighth run in a row done by hand; "next work" #6 still unbuilt.
- **Address sweep** (recruiter first names + SkillsCapital / Energy Exemplar / Mirai Alpha / Hired / Celigo /
  Crossing Hurdles) returned **only Azam's own sent mail** — the 07-30 batch, the 08-01 SkillsCapital
  application and the four 08-09 10:00 follow-ups. No recruiter has replied from a personal address either.
- **Control for "has anything arrived at all?"** — `newer_than:1d in:inbox` minus known newsletter senders
  returned 8 threads, **all marketing** (MyGov, Quora, Adobe, Canva, Cloudflare, Viz, Skool, beehiiv).
  Nothing inbound is unaccounted for.
- Slack posted (`--event info`). Eight runs, zero real replies: the classify/update/alert branches of this
  runbook remain **unexercised** — no `Reply` tick or `Status` move has ever been written by this recipe.

### 🚨 THREE more Easy Apply submissions today, also unrecorded — the count is now EIGHT

Every one matched against the board, not guessed:

| Time (08-10) | Company · role | Fit | LinkedIn job ID | Notion says |
|---|---|---|---|---|
| 11:02 | Neurones IT Asia · DevOps Engineer | 82 | `4446974055` | `New` |
| 11:05 | Crossing Hurdles · AWS Cloud Engineer ($60/hr Remote) | 81 | `4444889874` | `New` |
| 11:08 | Celigo · AI Integration Engineer | 80 | `4446715128` | `New` |

Added to the five from 08-09 (Energy Exemplar 72, SkillsCapital SRE 83 / DevOps 82 / Cloud 82, Crossing
Hurdles DevOps 82) — **eight submissions across two days with `Applied Date` null on every one.** This is
the **Recro trap** ([[20-first-email-batch-and-task-verification]]) open for a third day. Recording them is
the apply runbook's job, not this one's, so they were again left untouched — but every row is one sweep from
a duplicate application to the same employer, and **Crossing Hurdles now has two of its three board rows
applied to**, which makes a duplicate there a live risk rather than a theoretical one.

⚠️ **The selection problem from 08-09 has repeated, not corrected.** Today's three are fit 82 / 81 / 80.
The **SkillsCapital SWE Intern (93)** — the highest row on the board, whose JD asks for exactly this
candidate — still reads `Invite sent`, `Applied Date` null, and still has no Easy Apply submission. Whatever
picks these jobs is ranking by something other than fit score, and it has now spent eight submissions
without touching the best row.

### The Micro1 auto-ack fired a second time, and the timestamp tell held

`notifications@ceipalmail.com`, **08-10 11:05:38 — three seconds after** the 11:05:35 Crossing Hurdles
submission ack. Read FULL: identical template to the 08-09 one, first person (*"I'm from Crossing Hurdles …
we would like to refer you"*), funnelling to `jobs.micro1.ai` with a referral code; only the role name
changed (AWS Engineer vs DevOps Engineer). Classified **Auto-ack**, no action, no Notion write.

Worth keeping because it is now a *repeat*, not an anecdote: **a staffing firm's ATS answers within seconds,
in the first person, and it is still not a human.** The subject line is also how today's ack was tied to the
AWS Cloud Engineer row rather than the DevOps row — Crossing Hurdles has two `$60/hr Remote` rows and the
role name in the auto-ack subject disambiguated them without parsing LinkedIn's HTML.

## Apply at volume — 2026-08-09/10 (the batch runner ran; read [[26-apply-at-volume]])

**Thirteen applications now exist. Zero replies.** 5 email + 1 LinkedIn DM (tailored packets) and
**8 LinkedIn Easy Apply** submissions using the new role-family CVs.

- Built: `apps/autopilot/families.py` (3 family CVs, routed by title, never falls back to the generic CV),
  `apps/autopilot/ledger.py` (append-only, fsync'd, imports nothing that can reach a board status),
  `run.py apply-all`. 50 tests passing.
- The ledger was seeded from **the send record** (Gmail Sent + LinkedIn history), not board notes. The
  board said SkillsCapital was unsent; Gmail proved it was emailed 08-01. Seeding from notes would have
  duplicated the highest-fit row on the board.

### 🚨 The research half was never wired in — D32

Of the 8 Easy Apply submissions, **five had no packet, no recruiter identified and no outreach**
(Crossing Hurdles x2, Neurones IT Asia, Celigo, plus SkillsCapital's packet being for a *different*
role). Energy Exemplar had all three and the outreach **was still never sent**.

The design is *tailored CV + named recruiter + touch-1 email + touch-2 message*. The batch implements the
first half. This is the mass-automation shape the north star rejects, and 13 applications / 0 replies is
the measurement, not the worry.

### 🔴 The company cap is blocking the best row on the board — D33

`apply-all` counts **every ledger row for a company, regardless of channel or age**. Infosys has one
entry: an old LinkedIn DM about a different role. That single row now blocks all four Infosys rows
including **Junior AI Engineer (90)** — the top Track A action for ten days, where Recruiter-A is already
1st-degree inside the company.

This also explains the "why is it only applying to 80-82s?" note logged twice above. It is **not** a broken
scorer: SkillsCapital (93) is correctly ledger-blocked and Infosys (90 x4) is wrongly cap-blocked, so the
plan's ceiling really is 85. The skip reason says `already applying ... this run`, which is false on both
counts and sent two investigations down the wrong path.

### Four bugs the owner caught by watching it run

All four are D30's disease — a plausible report over a wrong action.

1. **Throttled after skips**, so a batch looked busy and applied to almost nothing.
2. **Yes/No radios never clicked** — the text fallback required `count == 1`, which covers a lone consent
   box and *nothing else*. Every two-option group silently went unanswered, and the jobs reported filled.
3. **`--limit 5` submitted zero** — it capped the plan, and the top 5 rows are all external ATS.
4. **D31, the serious one:** a bare `location` in the `city` spec matched *"Have you ever appeared for
   an Interview at any Exl location during the last 90 days?"* and typed **"Srinagar"**. It passed the
   answer-bank guard because Srinagar *is* in the bank. **The bank guarantees where a value came from and
   nothing about where it went.** Patterns anchored; 9 regression tests written from real form text.

### Board position

31 candidate rows planned and ready; 8 skipped (1 ledger, 7 company cap). ~60% of the wider board is
external ATS with no Easy Apply path built. Answer bank gained passport / night-shifts / middle-name /
previously-employed-here from the owner on 08-09.

## Immediate next work

> **Two tracks now run in parallel.** Track A is the job hunt (below) — it does not wait for the rewrite.
> Track B is [[22-rewrite-architecture]] Phase 0. **Track A is more urgent**: five applications have been
> silent for eleven days and the best role on the board is rotting. Do not let the rewrite eat the goal.

### Track B — the rewrite (updated 2026-08-10)

- **B1.** ✅ **DONE** — Phase 0 closed 2026-08-06: 5 genuine fills in 72.1s against a 180s target, three
  consecutive passing runs, zero invented values. [[23-phase-0-results]].
- **B2.** ✅ **DONE** — `cv.py`, the subprocess bridge, with the usage-limit check ported and the artifact
  checked *before* the log (D25/D30 struck a third time during the port itself). [[24-cv-bridge]].
- **B2b.** ✅ **DONE** — family CVs + the never-resubmit ledger + `apply-all`; 8 real submissions.
  [[26-apply-at-volume]].
- **B3.** ⏸️ **Phase 1 (own the data) is deliberately NOT next.** It unblocks nothing a recruiter sees —
  the same argument that moved `cv.py` ahead of it in [[22-rewrite-architecture]] §7. The next code change
  is **D33** (the company cap), then wiring the outreach half into the batch (**D32**).

### Track A — the actual job hunt

> **Re-ordered 2026-08-10.** The measurement that reorders it: **13 applications, 0 replies.** More
> applications is the thing that has been tried; a named human is the thing that has not.

- **A0. Fix D33 (ten minutes) and apply to Infosys Junior AI Engineer (90).** The cap counts an old
  LinkedIn DM as an application and refuses the best row on the board. Recruiter-A is inside and already
  1st-degree — this is the only row needing neither an accept nor a cold approach.
- **A1. Contact one named human per submitted application** (D32). Eight Easy Apply rows sat down in an
  ATS queue with nobody aware of them. Start with Celigo, Neurones IT Asia and Crossing Hurdles — small
  and remote, so a founder or hiring manager is findable.
- **A2. Send Energy Exemplar's outreach.** The packet, the recruiter and the drafts have all existed
  since 08-06 and were never sent. Cheapest reply available on the board.
- Then the original list below.

0. **Apply to SkillsCapital's AI/ML & Agentic AI intern role (93) — this week.** It is the only row whose
   JD *asks for the exact candidate Azam is*, it is remote, and it has a direct email path
   (`careers@skillscapital.io`) that bypasses the Easy Apply queue. 100+ applicants already and it was
   6 days old on 08-01. Everything else on this list can wait a week; this cannot.
1. **Drain the packet backlog** — now **~90 rows with only 4 packets**, and discovery is outrunning
   processing ~4:1. The Sweep Packets task does 2 every 6h; `tools/sweep-packets.ps1 -Max 5` goes faster
   but needs no other Claude window open. **Consider pausing Daily Discovery until the backlog clears** —
   more rows currently subtract value by burying the good ones.
2. **The Infosys "Junior AI Engineer" (90) is the standout** from the 07-30 discovery: LinkedIn reports
   *"1 connection works here"* (Recruiter-A, already accepted), and a **Junior**-titled AI req is the rare
   shape that fits a final-year student. Highest-priority action on the board.
3. **Re-score before building.** The 38 new rows were scored from title/company/location only — the JDs
   were never fetched. Weaker than the 07-25 batch.
4. Decide whether the Innova pitch firing 07-31 16:28 should have Recruiter-B's researched detail swapped in
   (she posts DevOps reqs daily, Azure/GCP/K8s/Terraform). It changes already-approved words, so it is
   the owner's call.
5. **Watch the first real Easy Apply run closely.** The rewritten runner has never submitted anything.
6. **Widen the reply check to the campus channel.** The 22:0x run found an EPAM online-test invite that
   expired unseen because EPAM has no Notion row, and the classifier only searches domains harvested from
   `output/outreach/<slug>/contact.md`. Add an assessment-platform sender list (naukricampus, doselect,
   hackerrank, hackerearth, mettl) to [[11-reply-classifier-runbook]] so a time-boxed test cannot pass
   unnoticed again.
7. **Add the two missing allowlist entries by hand** (see the Allowlist item above) — an AI is blocked
   from doing it.
