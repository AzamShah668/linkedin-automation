# 36 — State archive (the old 07-current-state.md)

Everything that used to live in `07-current-state.md`, verbatim and unedited. It reached **2,566
lines / 228 KB**, of which **40 of its 58 sections were scheduled-agent run notes** appended one run
at a time. `CLAUDE.md` instructed every session to "read it 2nd", which was impossible at that size,
so the instruction was skipped entirely rather than partially - the same failure shape as the broken
`graphify query` command (see [[35-knowledge-system-audit]]).

Split on 2026-08-17. Nothing was deleted: `07-current-state.md` is now a real snapshot of what is
true today, and this file is the history behind it. Grep here for how something came to be.

⚠️ Sections here contradict each other, because they were written months apart as the project
changed. The oldest describe an MCP-first pipeline that no longer exists. **Treat this as a log, not
as a description of the system** - for that, read `07-current-state.md`.

---

# 07 — Current State (what ACTUALLY exists right now)

Back to [[00-INDEX]]. **Read this file second, every session, right after the INDEX.** It is the live
snapshot of what has really been built and where each job stands — the guard against "forgetting" work that
lives in a connected service (Notion / MCP) rather than in this repo. Update it after every working session.

> **Why this file exists:** on 2026-07-25 we nearly re-built the job-discovery store from scratch because the
> already-built Notion database + the MCP-driven discovery run were recorded *nowhere* in the brains. Lesson:
> work done through a connected service (Notion, LinkedIn/Gmail MCP) is invisible to future sessions unless
> it is written here. If it's not in a brain, it doesn't exist. See [[05-decisions]] D7.

## ✅ 2026-08-15 (evening) — THE LOOP IS CLOSED. One entry point, eight steps.

Read **[[32-the-complete-loop]]** and **D47** before answering "is the pipeline done?" or
"why did nothing happen?".

```
pipeline.cmd     ->  accepts → flush → replies → nudge → discovery → apply → outreach → packets
```

Scheduled: **"Job Hunt - Full Pipeline"**, daily 10:30 (battery-safe, catch-up on), plus
"Job Hunt - Catch Up" on resume. Per-step tasks still run for faster turnaround; the lock makes
collisions safe.

**What was missing until today:** the half that turns an application into a conversation.
`coverage.py` had counted the gap since D41 and could never close one — the next move existed only
as a runbook a human read. **`apps/autopilot/outreach.py`** now does it: read-only people search →
ranked candidates → `contact.md` → a Slack card with `ref:<slug>`. **It sends nothing**; the ✅ gate
(D12) is unchanged. **`apps/autopilot/nudge.py`** feeds the Day-3/Day-7 engine true counts (D44).

- **Verified live:** 2 companies researched, 2 named humans found and queued; coverage fell
  **19 → 17** reached-nobody in the same run. 7 overdue follow-ups posted to Slack.
- 🔴 **Three bugs shipped in its first three live runs, all silent**: a stranger, then an
  **ex-employee** (`Past:` on the card), then dropping the only genuine lead (headline named a
  different employer). `employment()` is now **CURRENT/PAST/UNKNOWN**, never a boolean, and the
  browser parses **nothing** — 24 tests pin `parse_card()` against real harvested cards.
- ⚠️ **One browser profile, three steps want it.** A clean run left **16** chrome processes; the
  next Playwright step dies **exit 21**. Guarded, and it will not kill an interactive MCP session.
- 🔢 **187 tests** (was 150).

**Still a human's job on purpose:** tick every ✅, send every nudge, answer every reply.

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

## Accept watch — 2026-08-10 21:02 (third run of the day; fifth consecutive identical result)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` Wall is still 08-20.
- **Step 2 (the poll):** all three `get_person_profile` calls returned — which doubles as the only
  trustworthy auth check, so the LinkedIn session is healthy at 21:02.

| Who | Company · role | Degree | Badge | Verdict |
|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | `3rd` | `Pending` | not accepted |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | `3rd` | `Pending` | not accepted |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | `3rd` | `Pending` | not accepted |

- **Step 3 `due`:** `[]`. **Verified as genuinely empty, not a business-hours hold** —
  `list --status accepted` returns `[]`, so there is no ripe row being held. This distinction matters at
  21:02: the 09:00–21:00 gate had just closed, and `cmd_due` returns `[]` for *both* reasons with the same
  output. A quiet `due` is only trustworthy once you have checked whether anything is `accepted` at all.

Fifth consecutive run reading identically; the invites are at **day 4** since 08-06, still normal latency
for a cold connect, and no pitch is late. The `Pending` badges keep ruling out the D12
`custom_note_limit_reached` hole — stage 1 genuinely delivered.

- ⚠️ **`last_checked` is still `null` on all three** — `invite_tracker.py` only stamps it inside
  `mark-accepted`, so this run polled three profiles and again left **no trace in the state file**. Fifth
  time recorded; these sections remain the only evidence any poll ever happened.
- 👀 **Recruiter-F's profile still advertises only the *Founder's Office Intern — Research & Strategic
  Growth*** req; the AI Engineering Intern posting she was pitched for stays closed. Unchanged since 08-09.
- 🪤 **PYMK trap, seventh confirmation.** The Indian-name sidebar `references` on all three profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

**Nothing here is actionable, and that is the point of the quiet exit** — but this runbook has now reported
"no change" five times running while the open levers sit elsewhere: Track A **A0** (Infosys Junior AI
Engineer 90, where Recruiter-A is already 1st-degree so no accept is needed at all) and **A2** (Energy
Exemplar's outreach, drafted 08-06 and still unsent).

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

## Closing the D32 gap — 2026-08-10 evening (first humans contacted for the batch submissions)

The batch had produced 8 Easy Apply submissions with **five of them reaching nobody**. This is the
first pass at fixing that, and it changed three of the five.

### ✅ Energy Exemplar — the email that had existed since 08-06 was finally SENT

Touch 1 went to the recruiter's **verified** address (he published it himself in a public LinkedIn
hiring post). Gmail thread `19fec506e940b383`, 2026-08-10 15:35 UTC.

- **MX checked first, per [[drive-sharing-mx-decides]]:** `energyexemplar.com` resolves to
  `au-smtp-inbound-*.mimecast.com`. Mimecast almost always fronts Microsoft 365, which matches an
  Azure-first engineering team, so a Drive link restricted to his address would have shown
  "You need access".
- **CV delivery changed at send time.** The tailored PDF could **not** be attached: Composio's Gmail
  attachment needs an `s3key` staged inside *its own* sandbox, and that sandbox cannot see a local
  file ([[cloud-tools-cannot-touch-local-files]], confirmed again). Sent the public general CV link
  instead — which is the standing rule anyway ("email links ONE general CV, never publish tailored
  variants") and is itself the DevOps CV, matching this DevOps role.
- The email names the **Azure gap** in the owner's own voice rather than hiding it. Deliberate.

### ✅ Celigo and Neurones IT Asia — recruiters found, bare invites sent

Both were previously "no packet, no contact, no outreach". Both now have `contact.md` and a drafted
touch-2, and a **bare connection request (no note, D12)** is pending on each. Registered in
`pending-invites.json`, so `watch-accepts` schedules the follow-up automatically.

| Company | Target | Why |
|---|---|---|
| Celigo | Lead, Recruiting (Hyderabad, 3rd) | seniority + explicit SaaS hiring; Celigo is iPaaS |
| Neurones IT Asia | TA Partner (Singapore, 3rd) | headline names **DevOps and Cloud explicitly**, in-house, end-to-end ownership |

⭐ **The Neurones partner's profile says she sources through "LinkedIn, GitHub, and niche tech
communities" with zero agency dependency.** That is the best hook available to this candidate, whose
whole differentiator is public GitHub work, and the touch-2 draft now leads with it.

### ❌ Crossing Hurdles — no contact exists, and that is the finding

`search_people("Crossing Hurdles recruiter talent")` returned **zero people employed there**. Combined
with the `ceipalmail.com` auto-ack that fires within 3 seconds and funnels to `jobs.micro1.ai` with a
referral code, the shape is a **staffing shell whose reqs are lead magnets for micro1's funnel**.
There is no hiring manager behind the posting to reach.

Recorded as a deliberate negative result in `output/outreach/crossing-hurdles/contact.md`, and no
unrelated recruiter was messaged just to have messaged somebody.

> **The wider point: two of eight application slots went to a company that cannot be followed up.**
> That is a *sourcing* defect, not an outreach one. Candidate scoring rule worth adding: **if no
> employee of the company is findable on LinkedIn, the row does not deserve an application slot.**

### Where the 8 stand now

| Company | Contact | Status |
|---|---|---|
| Energy Exemplar | ✅ verified email | **emailed 08-10** |
| Celigo | ✅ found | invite pending |
| Neurones IT Asia | ✅ found | invite pending |
| Crossing Hurdles ×2 | ❌ none exist | closed, unreachable by design |
| SkillsCapital ×3 | ⚠️ contact exists, packet is for a different role | 3 approaches already made, no answer |

## Reply check — 2026-08-11 (ninth run; the FIRST to find a real reply — and it is 16 days old)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82).
**Gmail: still zero.** **LinkedIn inbox: one reply, unanswered since 2026-07-26.** This is the first run in
the project's history to write a `Reply = ✓` or fire an `--event reply` alert.

### 🔴 Recruiter-A (Infosys, AI Application Engineer 90) replied two hours after the pitch

Pitch sent **07-26 16:43**; he answered **07-26 18:58** with his phone number and *"Send ur cv on this
number"*, plus the salaam returned. **Sixteen days unanswered.** Exactly the D35 case, and D35 was written
about *this same message* on 08-10 — so the finding is not new, but this is the first **scheduled reply
check** to surface it through the normal path (Notion + Slack) rather than as an incident write-up.

- **Classified `Other` / action-required, deliberately not `Interview`.** He is not scheduling anything; he
  is asking for the CV on a channel we do not automate. Calling it an interview would overstate it.
- **Notion updated** (`AI Application Engineer`, Infosys): `Reply = ✓`, note appended, **`Status` left at
  `Applied`** — the runbook only moves it for Interview or Rejection. Ticking `Reply` stops the Day-3/Day-7
  nudges, which is right: the ball has been in *our* court for 16 days, and another nudge would be absurd.
- **Slack alert posted** (`--event reply`), with the next step named as the owner's: message him on WhatsApp
  with the tailored Infosys CV. **Nothing was sent by this run** — read-only, per the guardrail.

### The other four rows, and why they are quiet

| Row | Gmail | LinkedIn inbox |
|---|---|---|
| Innova ESI (Recruiter-B) | nothing | `You:` — **we** spoke last (2b sent 08-01), no answer |
| GoodSpace (Recruiter-C) | nothing | `You:` — **we** spoke last (2b sent 08-01), no answer |
| CodeRound AI | nothing | no thread — email-only channel |
| Recro | nothing | no thread — Easy Apply only |

6 conversations scanned in total. The remaining two are personal (Jun 25, May 12) and one is a **sponsored
InMail ad** (Learnbay), which `replies.py` classifies as `ad` precisely so it cannot be misread as a lead.

### ⚠️ The D35 scanner could not be run from this session — the MCP inbox was used instead

`py -3 -m apps.autopilot.replies` was **refused by the permission prompt** in an interactive session, so the
inbox was read through the LinkedIn MCP `get_inbox` / `get_conversation` tools instead. Same conclusion, and
the MCP path needs no Playwright profile — but note the consequence: **the tested, unit-tested code path is
the one that did not run.** The scheduled `check-replies.ps1` STEP 0 runs under Task Scheduler and does not
consult that allowlist, so this is a session-only gap. It still means the `--notify` branch of `replies.py`
has never fired in anger; the Slack alert here was posted by hand via `slack_notify.py`.

### Verification done before any zero was believed (standing rule, ninth run)

- Bare `newer_than:14d in:inbox` → **201** threads; `(from:linkedin.com OR from:infosys.com)` → **29**. Both
  the connector and the `from:` OR-group syntax proven live before the empty 5-domain result was trusted.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN).
- **Campus sweep** (naukricampus, doselect, hackerrank, hackerearth, mettl, imocha, codility, hirevue, epam)
  → only the known **08-05 EPAM cancellation**. Ninth run done by hand; "next work" #6 still unbuilt.
- Control on today's inbox: 29 threads in 2 days, all newsletters, LinkedIn job alerts and the already
  classified auto-acks. **Nothing inbound is unaccounted for.**

### The number that has been driving decisions was wrong, and now it is fixed in the board too

"13 applications, 0 replies" reordered all of Track A on 08-10. The true figure is **13 applications, 1
reply — and the one reply came from the *first* warm-insider approach the project ever made**, on the
highest-fit company, within two hours. The outreach design is not what failed; the reading of the channel
was. Notion now carries that fact, so the next session cannot re-derive the wrong number from the board.

## Accept watch — 2026-08-11 13:02 (sixth consecutive quiet run; the queue is now FIVE, not three)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` Wall for the 08-06 trio is **08-20**;
  for the two added last night it is **08-24**.
- **Step 2 (the poll):** all five `get_person_profile` calls returned — which doubles as the only
  trustworthy auth check, so the LinkedIn session is healthy at 13:02.

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 5 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 5 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 5 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 0 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 0 | `3rd` | `Pending` |

- **Step 3 `due`:** `[]`, **and verified genuinely empty** — `list --status accepted` also returns `[]`, so
  no ripe row is being held. 13:02 is inside business hours anyway, so a hold would have been a real bug;
  checking the `accepted` bucket is what distinguishes the two, per the 08-10 21:02 note.

### ✅ The two D32 invites from last night were genuinely delivered

This is the first poll since Celigo and Neurones IT Asia were added at 21:10 on 08-10, and the finding is
positive: **both read `Pending`, which rules out the D12 `custom_note_limit_reached` hole** — the failure
mode where `connect_with_person` returns success and silently sends nothing. Stage 1 worked on both. They
are at **day 0**; there is nothing to conclude from silence yet.

The 08-06 trio is at **day 5**. Still normal latency for a cold connect; no pitch is late, nothing is
expired, and the correct action on all five is to wait.

- ⚠️ **`last_checked` is still `null` on all five** — `invite_tracker.py` only stamps it inside
  `mark-accepted`, so this run polled five profiles and again left **no trace in the state file**. **Sixth
  time recorded.** These sections remain the only evidence any poll has ever happened, which means the
  polling history lives in prose a script cannot read. Worth one line in `cmd_list` or a `mark-checked`.
- 👀 **Recruiter-F's profile still advertises only the *Founder's Office Intern — Research & Strategic
  Growth*** req; the AI Engineering Intern posting she was pitched for stays closed. Unchanged since 08-09 —
  do not silently re-aim the packet at a different job.
- ⭐ Recruiter-H's own profile confirms the hook already in her touch-2 draft: *"zero agency dependency —
  building strong pipelines through LinkedIn, GitHub, and niche tech communities"*, and her headline names
  **DevOps, Cloud and AI** explicitly. Best-matched cold approach on the board for a GitHub-first candidate.
- 🪤 **PYMK trap, eighth confirmation.** The Indian-name sidebar `references` on all five profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

**Sixth consecutive quiet run, and the open levers are still elsewhere** — the 08-11 top item (answer
Recruiter-A, waiting 16 days), Track A **A0** (Infosys Junior AI Engineer 90, where Recruiter-A is already
1st-degree so no accept is needed at all) and **A2**, now partly closed: Energy Exemplar's touch-1 was
finally sent 08-10. Nothing on this runbook's surface is actionable today.

## Engineering — 2026-08-11 (D34 resolved; the pipeline now watches its own blind spots)

Four modules now do in code what a runbook used to do by hand, and two of them proved themselves in
production the same day.

| Module | What it closes | State |
|---|---|---|
| `apps/autopilot/replies.py` | **D35** — the LinkedIn inbox nothing had ever opened | ✅ live in `check-replies.ps1` step 0 |
| `apps/autopilot/coverage.py` | **D41** — applications that reached no human | ✅ live, found Recro |
| `apps/autopilot/sourcing.py` | **D36** — slots spent on companies with nobody behind them | ✅ wired into `apply-all` |
| `apps/autopilot/cv.py` (rework) | **D34** — a company's second role was unbuildable | ✅ resolved |

**98 tests passing** (50 on 08-09). Graph at 780 nodes.

### The 08-11 12:49 scheduled run is the proof

The reply check ran unattended and did the whole thing through the normal path: LinkedIn inbox scanned
(exit 0), coverage counted, Gmail checked, **the 16-day-old reply found**, Notion ticked, Slack posted.
No human prompted it. That is the first time this project has caught an inbound signal by machine.

### D34 — resolved, and what it unblocks

Outreach stays per **company** (D8: never message the same recruiter twice). The **CV is per role**:

```
output/outreach/infosys/                      contact.md + messages
output/outreach/infosys--junior-ai-engineer/  this role's own tailored CV
```

The first role keeps the plain folder, so **nothing already on disk moved**. Verified live: *AI
Application Engineer* still resolves to `infosys/`, *Junior AI Engineer* to
`infosys--junior-ai-engineer/`, reusing the existing contact.

**Unblocks 9 rows** — Infosys ×5 (incl. **Junior AI Engineer, 90**) and SkillsCapital ×4.

⚠️ Trap worth remembering: **a folder slug is not a comparison key.** `slugify` gives `skillscapital`
and `skills-capital` for the same employer, and an unequal compare means a tailored CV is not found and
the **family CV silently goes out instead** — the "fast and generic" outcome [[24-cv-bridge]] exists to
prevent. Comparison uses an alphanumeric-only key, same as the ledger.

### Two guards, deliberately opposite failure directions

This is the reusable idea from the day:

| Guard | Fails toward | Because |
|---|---|---|
| `replies.py` | **shouting** | false alarm = 10 seconds; false silence = 15 lost days |
| `sourcing.py` | **applying** | false block = a lost job; false pass = ~15 wasted seconds |

> **Decide which direction a check should fail before writing it, and write down why.** "Be safe" is
> not a direction — safe for whom, against which cost? A guard whose failure direction was never chosen
> has one anyway, by accident.

### Housekeeping: the decision register had a collision

**D33-D36 were claimed twice** on 08-10 by two parallel sessions. The content engine's four are now
**D37-D40**, registered in [[05-decisions]] with pointers to [[27-linkedin-content-engine]]. The register
is append-only with no allocator, so concurrent writers cannot see each other's claim — **grep `^## D`
before numbering anything.**

### Coverage right now

`py -3 apps/autopilot/coverage.py` → **14 applications across 10 companies · 9 reached a human · 1
reached nobody** (Recro, applied 07-29). Five invites pending, three accepted and pitched.

## App structure — 2026-08-11 evening (frontend / backend / database, and the console page)

Full detail in [[28-app-structure]]. Headlines:

| Was | Now |
|---|---|
| `web/` | `frontend/` |
| `tools/serve_dashboard.py` | `backend/server.py` |
| `tools/pipeline_runner.py` | `backend/pipeline_runner.py` |
| `tools/board_db.py` | `database/board_db.py` |
| `output/dashboard/board.sqlite3` | `database/board.sqlite3` |

### 🔴 Two shims are load-bearing

`board_db` had **sixteen callers**, three of them PowerShell scripts launched by Task Scheduler.
`tools/board_db.py` now re-exports the real module and **must load it by file path** — both files
share a name, so a plain import re-imports the shim and dies on a circular import (hit on the
first attempt). `tools/serve_dashboard.py` redirects for the same reason: `dashboard.cmd`, the
repo README and four knowledge files all named that path.

### 🔴 The .sqlite3 leaving `output/` created a security problem, immediately handled

`output/` is gitignored; `database/` was not. The board's `notes` column holds **real recruiter
names on 17 rows**, and **this repo is public**. `.gitignore` now blocks `database/*.sqlite3`;
verified the file no longer shows as untracked. **Schema tracked, data not.**

Both `board_db.DB_PATH` and `run.BOARD_DB` fall back to the old path if the new one is missing, so
an un-migrated machine is never handed an *empty board* — which would read as "no jobs" rather
than as an error.

### The console page

`/console`, in the nav on every page, built on the existing `style.css` tokens and the
`JH.ready()` pattern rather than as a separate app. It shows 30-day progress, a **ranked action
queue** tagged *only you can do this* / *the system can do this*, the **Easy Apply vs external
split with links**, every application with a *reached a person?* column, skills to learn, and the
capability list.

`/api/console` reads board, triage, ledger and coverage **independently**; a source that fails
lands in `warnings` and the page says so. *A page rendering zeros looks identical to a page whose
data vanished* — designed out rather than waited for.

### `triage.py` — the number nobody had

Nothing had ever recorded **which** rows can be one-click applied to. `apps/autopilot/triage.py`
opens every live posting and caches the answer with a `checked` date.

> **First full run: 14 easy-apply · 22 external · 4 dead.** Three in five live rows have no Easy
> Apply button — the clearest measure yet of how much of the board the batch runner can reach.

Verified after the move: all 7 routes 200 · `/api/bootstrap` unchanged · the 4 PowerShell Python
callers still import · `apps.autopilot` finds the board (39 candidates) · 98 tests green.

## The dashboard cull — 2026-08-11 evening (7 pages → 4, 16 actions → 11)

Full detail in [[28-app-structure]] §8. Audited by **the age of the file each page reads**:

- **Deleted `slack.html`** — a mirror of a channel already on the phone, newest message **16 days**
  old. `check_approvals.py` queries Slack directly, so the ✅-to-send gate (D12) is untouched.
- **Deleted `research.html`** — `REVIEW-QUEUE.md` 5 days, `highlight-reel.md` 17 days, and it
  duplicated what the Jobs page shows per row.
- **Deleted the old Board index** — and this is the finding: **its data was never stale.** It only
  *looked* stale because it stamped `board synced 1d 23h ago`, which describes the last Notion
  capture and nothing else on the page. **The stamp was the bug.** Its filterable table moved onto
  the console with better filters and a count of hidden rows.

> A freshness indicator that describes one source while sitting above five is worse than none: it
> makes live data look dead, and would equally make dead data look live.

**Actions 16 → 11.** `notion-push` and `notion-queue` were removed because **`NOTION_TOKEN` is not
set** — buttons that were always going to fail. `invites`, `invites-due` and `expire` duplicated
the console or `watch-accepts`.

⚠️ **State this plainly: `database/board.sqlite3` is now the real store.** With no Notion token,
status changes made on the dashboard stay local and nothing pushes back. `apps/autopilot` plans
from the local DB. `sync-board` (import from a manual capture) is the only inbound path, and the
capture behind it is **10 days old**.

Two breakages caught by curling every route rather than assuming: the startup guard still checked
for the deleted `index.html`, and the Jobs page linked to `/research` (now 404) — repointed at the
packet zip, which carries the same research and is current on disk.

**Final shape:** Console (home, live, polls every 15s) · Jobs & CV · Downloads · Run it.

## Reply check — 2026-08-13 (tenth run; Gmail clean, LinkedIn UNREAD, and a 15th application nobody recorded)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82) against
`infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `recro.io`. **Zero new replies in Gmail.
No Notion writes, no `--event reply` alert** — correct per the de-dupe rule. Slack posted `--event info`.

- **Query proven before the zero was believed.** Bare `newer_than:14d in:inbox` → **201** threads;
  `(from:linkedin.com OR from:infosys.com)` → live. Widened to `newer_than:30d in:anywhere` — also empty.
- **Bounces clean** at `newer_than:14d in:anywhere`. **Campus sweep** (naukricampus, doselect, hackerrank,
  hackerearth, mettl, imocha, codility, hirevue, epam, micro1, ceipalmail) → only the known **08-05 EPAM
  cancellation**. Tenth consecutive run done by hand; "next work" #6 still unbuilt.
- **Infosys skipped correctly**: `Reply` was already ✓ from the 08-11 run and no newer message exists in
  Gmail. The two known auto-acks (Energy Exemplar 08-09, Crossing Hurdles/Micro1 08-09 + 08-10) produced
  nothing new and stay unticked.

### 🔴 The LinkedIn inbox was NOT read — and the Gmail proxy for it is worthless

Both paths were unavailable: `py -3 -m apps.autopilot.replies` was **refused by the permission prompt**
again (the same session-only gap recorded on 08-11), and the **LinkedIn MCP is not connected** this
session, so the 08-11 fallback was gone too. **Say this as "unchecked", never as "no replies"** — that
distinction is the whole of D35.

**The proxy was tested rather than assumed, and it failed.** LinkedIn does email a notification for some
inbound messages, so the inbox *looks* observable from Gmail. Calibrating against the one known true
positive kills it: Recruiter-A replied **2026-07-26 18:58**, and a sweep of every `linkedin.com` sender
across 07-25 → 07-28 returns **no message notification at all** — only job alerts, "application was sent"
receipts and marketing. A detector that misses the only true positive it has ever been given is not a
weak signal, it is **no signal**, and a clean sweep of `messages-noreply@` must not be reported as
evidence the LinkedIn channel is quiet.

### 🚨 A FIFTEENTH application exists, recorded nowhere — Tata Consultancy Services

`jobs-noreply@linkedin.com`, **2026-08-11 08:28**: *"your application was sent to Tata Consultancy
Services."* The ledger holds **14** entries and **no TCS row**; Notion's `Tata Consultancy Services ·
Gen AI Engineer (80)` still reads **`Status = New`, `Applied Date` null**.

This is the **Recro trap** for the fourth time, and it is worse than the 08-09/08-10 batch: those were at
least written down within two days. Left alone, `apply-all` will re-submit TCS, and both `coverage.py`
(D41) and the D33 company cap are computing off a send record that is one row short. Recording it belongs
to the apply runbook, not this one, so **nothing was written** — flagged instead, consistent with how the
previous five were handled.

**Note how it was found:** not from the board, not from the ledger, but from the employer-side receipt in
the mailbox. Same rule as the 08-10 SkillsCapital finding — **the mailbox is the system of record for what
left the building**, and it is the only source that cannot be silently out of date.

⚠️ Leftover to delete by hand: `output/reply-log/slack-2026-08-13.txt` (scratch; the sandbox refused to
remove it, exactly as it did with `tools/_tmp_test_due_gate.py` on 08-01).

## Accept watch — 2026-08-13 (seventh consecutive quiet run; all five still pending)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The 08-06 trio is at **day 7** (wall
  **08-20**); the 08-10 pair at **day 3** (wall **08-24**).
- **Step 2 (the poll):** all five `get_person_profile` calls returned, every one reading `· 3rd` with a
  `Pending` button. That doubles as the only trustworthy auth check ([[05-decisions]] D13), so **the
  LinkedIn MCP session is healthy today** — worth stating, because the 08-13 reply check ran a few hours
  earlier with the MCP *not* connected and had to record the inbox as unchecked.

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 7 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 7 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 7 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 3 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 3 | `3rd` | `Pending` |

- **Step 3 `due`:** `[]`, **and verified genuinely empty** — `list --status accepted` also returns `[]`, so
  no ripe row is being held behind the business-hours gate. Checking the `accepted` bucket is what
  distinguishes "nothing to send" from "something held", per the 08-10 21:02 note.

### Nothing here is late, and nothing here is the lever

Day 7 is still ordinary latency for a cold connect with no note, and day 3 is nothing at all. **The correct
action on all five is to wait** — there is no version of this runbook that makes a stranger accept faster.
The open levers remain exactly where the 08-11 run left them: answer **Recruiter-A** (now **18 days**),
Track A **A0** (Infosys Junior AI Engineer 90, where Recruiter-A is already 1st-degree so **no accept is
needed at all**), and the 15th application (TCS) that the 08-13 reply check found unrecorded.

### One research hook worth keeping, and one non-change

- ⭐ **Recruiter-G's feed is now the Celigo *Ora* + *Agent Builder* launch** — her CEO's post describes a
  *"multi-agent copilot"* and low-code agentic workflows, reposted by her. That is a genuine, current
  proof-of-effort detail for her touch-2 if she accepts, and it is much closer to Azam's agentic/MCP stack
  than her older Node/Java architect reqs. Harvest it from the live profile at send time, not now — a
  detail drafted today rots the same way a relative time word does ([[05-decisions]] D22).
- 👀 **Recruiter-F still advertises only the *Founder's Office Intern* req**; the AI Engineering Intern
  posting she was pitched for stays closed. Unchanged since 08-09 — **do not silently re-aim the packet at
  a different job.**
- 🪤 **PYMK trap, ninth confirmation.** The Indian-name sidebar `references` on all five profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

### ⚠️ `last_checked` is still `null` on all five — SEVENTH recording

`invite_tracker.py` stamps `last_checked` only inside `mark-accepted`, so this run polled five profiles and
again left **no trace in the state file**. These prose sections remain the only evidence any poll has ever
happened, which means the polling history lives somewhere no script can read — and a quiet run is exactly
the shape that [[05-decisions]] D30 warns about, since "polled five, none accepted" and "never polled" write
byte-identical state. It is a ~5-line fix (`cmd_list` stamping, or a `mark-checked` subcommand). Recording
it a seventh time instead of fixing it is the actual finding here.

## Reply check — 2026-08-13 later (eleventh run; the LinkedIn inbox this time was READ, not skipped)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82) against
`infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `recro.io`. **Zero new replies on either
channel. No Notion writes, no `--event reply` alert** — correct per the de-dupe rule. Slack got `--event info`.

**The point of this run is the channel the tenth one could not open.** At the morning run the LinkedIn MCP
was disconnected, so the inbox was correctly recorded as **unchecked**. It is connected now, so the same
question was actually asked, and the answer is *quiet* rather than *unknown*. That is the whole of D35:
those two words are not synonyms, and only one of them is evidence.

### The LinkedIn inbox, read in full

6 conversations. Nothing inbound is unaccounted for:

| Thread | Last message | Reading |
|---|---|---|
| **Recruiter-A** (Infosys) | **07-26 18:58, his** | known reply, already ticked 08-11 — **no newer message** |
| Recruiter-B (Innova ESI) | 08-01, `You:` | we spoke last, no answer |
| Recruiter-C (GoodSpace) | 08-01, `You:` | we spoke last, no answer |
| Learnbay (sponsored InMail) | 08-11 | **ad**, not a lead — see the trap below |
| Two personal threads | Jun 25 · May 12 | not job traffic |

- **Infosys skipped correctly per de-dupe rule 6**: `Reply` was already ✓ and no newer message exists. That
  was **verified by opening the thread**, not inferred from the inbox list's date stamp — the list shows a
  preview, and trusting a preview to prove absence is the same shape of mistake as the Gmail proxy below.
  His last message is still *"9419280094 / Send ur cv on this number"*. **Eighteen days unanswered.**
- CodeRound AI and Recro have **no LinkedIn thread at all** — email-only and Easy-Apply-only respectively.

### 🪤 New trap: an ad thread can show `You:` as the last speaker

The Learnbay sponsored InMail now contains **outbound messages from the owner** — he tapped *"Check My
Eligibility"* and *"Learn More"* on 08-11 12:44, and LinkedIn records those button taps as messages he sent.
Any future scan that reasons *"`You:` means this is our own outreach awaiting a reply"* will mis-shelve a
sponsored ad as an outreach thread. `replies.py` classifies it as `ad`, which is why that classifier exists —
but the heuristic is now demonstrably load-bearing rather than theoretical.

### Verification done before any zero was believed (standing rule, eleventh run)

- Bare `newer_than:14d in:inbox` → **201** threads; `(from:linkedin.com OR from:infosys.com)` → live results.
  Connector and `from:` OR-group syntax both proven before the empty 5-domain result was trusted.
- Widened to **`newer_than:30d in:anywhere`** on the same 5 domains → also empty. Not misfiled in spam.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN).
- **Campus sweep** (naukricampus, doselect, hackerrank, hackerearth, mettl, imocha, codility, hirevue, epam,
  micro1, ceipalmail) → only the **three known items**: the 08-05 EPAM cancellation and the two Crossing
  Hurdles/micro1 `ceipalmail.com` funnel mails (08-09, 08-10). Nothing new. Eleventh run done by hand;
  "next work" #6 still unbuilt.
- **The Gmail proxy stays worthless, re-confirmed.** Every `messages-noreply@linkedin.com` item in the window
  is job-alert marketing (*"HuntingCube and Accenture in India are hiring"*), not a message notification.
  A clean sweep of that sender still says nothing about the LinkedIn channel — read the inbox or say unchecked.

### ⚠️ `apps.autopilot.replies` was refused by the permission prompt — THIRD consecutive session

`py -3 -m apps.autopilot.replies` was blocked again, so the inbox was read through the LinkedIn MCP
`get_inbox` / `get_conversation` instead. Same conclusion, but the same standing consequence: **the
unit-tested code path is the one that keeps not running interactively, and its `--notify` branch has still
never fired in anger.** This is session-only — the scheduled `check-replies.ps1` STEP 0 runs under Task
Scheduler and does not consult that allowlist (the 08-11 12:49 run is the proof it works there). Recorded a
third time rather than worked around.

## Accept watch — 2026-08-13 21:03 (second run of the day; eighth consecutive quiet run)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.** Identical to the earlier
08-13 run in every field; recorded only so the polling history stays continuous.

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` 08-06 trio at **day 7** (wall **08-20**),
  08-10 pair at **day 3** (wall **08-24**).
- **Step 2 (the poll):** all five `get_person_profile` calls returned, every one `· 3rd` with a `Pending`
  button. Doubles as the trustworthy auth check ([[05-decisions]] D13) — **the MCP session is healthy at
  21:00**, which is worth stating because it was *not* connected at the start of this session and only came
  up mid-run.
- **Step 3 `due`:** `[]`. Run at **21:03**, i.e. three minutes past the 09:00–21:00 business-hours gate — so
  the empty result had to be disambiguated: `list --status accepted` is **also `[]`**, so nothing is being
  held for morning. This is exactly the case the 08-10 21:02 note exists for; without that second check a
  gate-suppressed row and an empty queue are indistinguishable.

**Nothing here is late and nothing here is the lever.** Day 7 on a cold no-note connect is ordinary; day 3
is nothing. The open levers are unchanged: answer **Recruiter-A** (now **18 days**), Track A **A0** (Infosys
Junior AI Engineer 90 — Recruiter-A is already 1st-degree, **no accept needed**), and the unrecorded 15th
(TCS) application.

### ⚠️ `last_checked` is still `null` on all five — EIGHTH recording

Two accept watches ran on 2026-08-13, ten profile polls between them, and `output/outreach/pending-invites.json`
is **byte-identical to its 08-06 state**. `invite_tracker.py` stamps `last_checked` only inside
`mark-accepted`, so "polled ten times, none accepted" and "never polled once" write the same file. These
prose sections are still the only evidence any poll has happened. It is a ~5-line fix (`cmd_list` stamping,
or a `mark-checked` subcommand) and it has now been *written down* eight times and *fixed* zero — which
makes the tally itself the finding, not the bug. Escalated to the owner in chat rather than logged a ninth time.

## Immediate next work

> ⚡ **NEW TOP ITEM 2026-08-11: answer Recruiter-A.** He asked for the CV on 07-26 and has been waiting 16
> days (**18 as of 2026-08-13**). It costs one WhatsApp message, it is the warmest lead in the project, and it sits inside the
> company holding the board's best unworked row (Junior AI Engineer, 90). Nothing else on this list is
> cheaper or warmer. **Only the owner can send it** — the number is a personal channel this project does
> not automate.

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

## OmniRoute gateway live — 2026-08-13 (the autopilot finally has a free model)

**State:** OmniRoute v3.8.49 running on `localhost:20128`. `apps/autopilot/llm.py` is wired to it and
answering. Config in `.env`: `LLM_BASE_URL=http://localhost:20128/v1` (**with** `/v1`),
`LLM_MODEL=gemini/gemini-3.5-flash-lite`, `LLM_API_KEY` = the gateway key, `GEMINI_API_KEY` = the
Google key. Measured: a real question answered in **7.3s**. **104 tests pass** (was 98).

**Providers connected (9):** `gemini` (the working one), `groq` (key created 08-13, valid at 325ms
but its streaming through the gateway returns only keepalives - use `LLM_STREAM=false` if pinned), plus `pollinations`, `hackclub`,
`g4f-gemini`, `g4f-groq`, `g4f-nvidia`, `g4f-ollama`, `g4f-pollinations`. Catalog 115 → **665 models**.

**Canary-verified working — one primary, two fallbacks:**
`gemini/gemini-3.5-flash-lite` · `gemini/gemini-3.6-flash` · `felo/felo-chat`

**Everything else in that 665 does not answer:** `pollinations/*` 401 (its "optional" auth still needs
an upstream key), `tllm/*` and `oc/*` 403, `ddgw/*` 429, `pepper/*` 502, `mimocode/*` 400. Model count
is not capability — only an exact echo test is.

### What still needs the owner

- **Groq** (30 req/min) and **Cerebras** (1M tokens/day) — both gate signup behind a CAPTCHA, so an
  agent cannot and should not complete them. ~5 min each; they are the independent fallbacks that
  would make this survive a Google outage.
- **Kiro** — OAuth from the OmniRoute dashboard, free-forever Claude models, no CAPTCHA.
- **The gateway does not survive a reboot.** It runs in a terminal; nothing starts it automatically.
  Until a startup task exists, "runs all the time" is not true and `ask()` will fail closed.

### The four things that cost time, all silent

1. **Non-streamed answers lose their first token** (`HELLO WORLD`→`WORLD`), both wire formats,
   HTTP 200. `llm.py` streams and joins now; a test fails if that is undone.
2. **`gemini-2.5-flash` is retired for new users**, yet OmniRoute's imported list still advertises it.
   The provider's own catalog is the only honest source.
3. **Thinking tokens share `max_tokens`** — at 64, a reasoning model returns `''` or `'123'` for
   `"12345"`. Default raised to **1024**; canary probes at 512.
4. **One 404 trips a 65s cooldown**, after which every 429 is the gateway's own circuit breaker
   rather than the provider — debugging that is debugging the wrong system.

⚠️ **`api key` at the repo root.** The Google key first landed in an extensionless file that `*.key`
does **not** match — untracked but not ignored, in a public repo. Moved to `.env`, never committed,
`.gitignore` hardened. Related: [[29-omniroute-gateway]], [[05-decisions]] D42.

## Reply check — 2026-08-13 third run (twelfth overall; Gmail clean, LinkedIn UNCHECKED again)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82) against
`infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `recro.io`. **Zero new replies in Gmail.
No Notion writes, no `--event reply` alert** — correct per de-dupe rule 6. Slack got `--event info`.

- **Query proven before the zero was believed** (standing rule, twelfth run). Bare `newer_than:14d
  in:inbox` → **201** threads; `(from:linkedin.com OR from:infosys.com)` → live results. Only then was
  the empty 5-domain result trusted.
- **Widened** to `newer_than:30d in:anywhere` on the same 5 domains → also empty. Not misfiled in spam.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN).
- **Campus sweep** (naukricampus, doselect, hackerrank, hackerearth, mettl, imocha, codility, hirevue,
  epam, micro1, ceipalmail) → only the **three known items**: the 08-05 EPAM cancellation and the two
  Crossing Hurdles/micro1 `ceipalmail.com` funnel mails (08-09, 08-10). Twelfth run done by hand;
  "next work" #6 still unbuilt.
- **A keyword sweep was added this run** as a second angle on the same question: `newer_than:30d
  in:anywhere` on the five company *names* rather than their domains (21 threads). Every hit is either
  a LinkedIn notification/job alert or **our own `SENT` mail** — including the three 08-09 follow-ups to
  `saksham@goodspace.ai`, `swaleha.pathan@innovaesi.com` and `chaitanya@coderound.ai`, all of which
  remain unanswered four days on. A domain-only search would miss a recruiter replying from a personal
  address; the name sweep is cheap and closes part of that known blind spot.
- **Infosys skipped correctly**: `Reply` was already ✓ from the 08-11 run and Gmail holds no newer
  message. Status stays `Applied` (only Interview/Rejection move it).

### 🔴 The LinkedIn inbox was NOT read — SECOND time in three runs, and BOTH paths failed

`py -3 -m apps.autopilot.replies` was **refused by the permission prompt for the fourth consecutive
session**, on the PowerShell tool *and* on the Bash tool, and the **LinkedIn MCP is not connected**
this session (`ToolSearch` for it returns nothing, twice). So the 08-13-later fallback was gone too.

**Say this as "unchecked", never as "no replies"** — that distinction is the whole of D35, and the
LinkedIn inbox is the only channel that has ever produced a real reply in this project. The Gmail
proxy for it stays worthless and was not used: every `messages-noreply@linkedin.com` item in the
window is job-alert marketing (*"HuntingCube and Accenture in India are hiring"*), and that sender
demonstrably missed the one true positive it has ever been given ([[calibrate-a-proxy-on-a-known-positive]]).

**This is now the pattern, not the incident.** Of the last three reply checks, **two could not open the
LinkedIn channel at all**. The unit-tested code path is the one that keeps not running interactively and
its `--notify` branch has still never fired in anger. It works fine under Task Scheduler (the 08-11 12:49
run is the proof), so the gap is session-only — but a channel readable only by a scheduled task is a
channel this session cannot verify, and the honest word for that is *unchecked*.

### Nothing here moved, and the lever is unchanged

Twelve reply checks have now found exactly **one** reply, and it was found by opening LinkedIn, not
Gmail. **Recruiter-A has been waiting 18 days** for the CV on a personal WhatsApp number. That is still
the warmest lead in the project and **only the owner can send it**.

## Accept watch — 2026-08-14 01:02 (ninth consecutive quiet run; all five still pending)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The 08-06 trio is at **day 8** (wall
  **08-20**); the 08-10 pair at **day 4** (wall **08-24**).
- **Step 2 (the poll):** all five `get_person_profile` calls returned, every one reading `· 3rd` with a
  `Pending` button. That doubles as the only trustworthy auth check ([[05-decisions]] D13), so **the
  LinkedIn MCP session is healthy** — worth stating, because the 08-13 *third* reply check had to record
  the inbox as unchecked with the MCP disconnected. It is connected now.

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 8 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 8 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 8 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 4 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 4 | `3rd` | `Pending` |

- **Step 3 `due`:** `[]` — **and this run needed the disambiguation more than any before it.** It ran at
  **01:02**, four hours past the 09:00–21:00 gate, which is precisely when `cmd_due` returns `[]`
  unconditionally. `list --status accepted` is **also `[]`**, so nothing ripe is being held for morning.
  Without that second check, a gate-suppressed row and an empty queue are byte-identical (the 08-10 21:02
  note exists for exactly this, and at 01:02 the ambiguity is total rather than marginal).

### Nothing here is late, and nothing here is the lever

Day 8 on a cold connect with no note is still ordinary latency; day 4 is nothing. **The correct action on
all five is to wait** — no version of this runbook makes a stranger accept faster. The open levers are
unchanged from the 08-13 runs: answer **Recruiter-A** (now **19 days**), Track A **A0** (Infosys Junior AI
Engineer 90, where Recruiter-A is already 1st-degree so **no accept is needed at all**), and the 15th
application (TCS) that the 08-13 reply check found recorded nowhere.

### Observations carried forward unchanged

- ⭐ **Recruiter-G's Celigo *Ora* / *Agent Builder* hook still stands** as her touch-2 proof-of-effort
  detail — but harvest it from the live profile **at send time**, not now ([[05-decisions]] D22). Her
  profile this run surfaced no new activity to re-date it against.
- 👀 **Recruiter-F still advertises only the *Founder's Office Intern* req.** The AI Engineering Intern
  posting she was pitched for remains closed, unchanged since 08-09. **Do not silently re-aim the packet
  at a different job.**
- 🪤 **PYMK trap, tenth confirmation.** The Indian-name sidebar `references` on all five profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

### ⚠️ `last_checked` is still `null` on all five — NINTH recording

Fifteen profile polls across three accept watches (08-13 ×2, 08-14) and
`output/outreach/pending-invites.json` remains **byte-identical to its 08-06 state**. `invite_tracker.py`
stamps `last_checked` only inside `mark-accepted`, so "polled fifteen times, none accepted" and "never
polled once" write the same file. The polling history exists **only in these prose sections**, where no
script can read it — the exact shape [[05-decisions]] D30 warns about.

The 08-13 entry escalated this to the owner rather than log it a ninth time. It is logged a ninth time
anyway, because the run happened and the record has to stay continuous. **The tally is the finding.** It
is a ~5-line fix (`cmd_list` stamping, or a `mark-checked` subcommand) waiting on one word from the
owner, not on any technical unknown.

## Accept watch — 2026-08-14 09:06 (tenth consecutive quiet run; all five still pending)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The 08-06 trio is at **day 8** (wall
  **08-20**); the 08-10 pair at **day 4** (wall **08-24**).
- **Step 2 (the poll):** all five `get_person_profile` calls returned, every one reading `· 3rd` with a
  `Pending` button. That doubles as the only trustworthy auth check ([[05-decisions]] D13), so **the
  LinkedIn MCP session is healthy at 09:06** — it was disconnected as recently as the 08-13 third reply
  check, so this is worth stating rather than assuming.

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 8 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 8 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 8 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 4 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 4 | `3rd` | `Pending` |

- **Step 3 `due`:** `[]`, **and genuinely empty rather than gate-suppressed.** 09:06 is six minutes inside
  the 09:00–21:00 window, so `cmd_due` was not returning `[]` unconditionally the way it was at 01:02 last
  night; `list --status accepted` is **also `[]`**, so no ripe row is being held for later either. Both
  checks are needed — the two states print identically (08-10 21:02 note).

### Nothing here is late, and nothing here is the lever

Day 8 on a cold connect with no note is ordinary latency; day 4 is nothing. **The correct action on all
five is to wait** — no version of this runbook makes a stranger accept faster. The open levers are
unchanged: answer **Recruiter-A** (now **19 days**), Track A **A0** (Infosys Junior AI Engineer 90, where
Recruiter-A is already 1st-degree so **no accept is needed at all**), and the 15th application (TCS) the
08-13 reply check found recorded nowhere.

### Observations carried forward

- ⭐ **Recruiter-G's Celigo *Ora* / *Agent Builder* hook still stands** as her touch-2 proof-of-effort
  detail. Her profile this run showed no new activity to re-date it against — the CEO repost she shares it
  from is now **4 months** old, so harvest the phrasing at send time, not from this entry ([[05-decisions]] D22).
- ⭐ **Recruiter-H's profile re-confirms her touch-2 hook**: *"zero agency dependency — building strong
  pipelines through LinkedIn, GitHub, and niche tech communities"*, headline naming DevOps/Cloud/AI. But
  note what her last 6 months of posts actually are: Senior Software Architect (10+ yrs), Senior Data
  Leader, Senior Functional PM, AAA/Temenos, infra PM — **all mid-to-senior, none fresher-level**, same
  shape as Recruiter-B (08-01). The relationship is worth more than the specific req.
- 👀 **Recruiter-F still advertises only the *Founder's Office Intern* req.** The AI Engineering Intern
  posting she was pitched for remains closed, unchanged since 08-09. **Do not silently re-aim the packet
  at a different job.**
- 🪤 **PYMK trap, eleventh confirmation.** The Indian-name sidebar `references` on all five profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

### ⚠️ `last_checked` is still `null` on all five — TENTH recording

Twenty profile polls across four accept watches (08-13 ×2, 08-14 ×2) and
`output/outreach/pending-invites.json` is **still byte-identical to its 08-06 state**. Re-stating the
finding rather than the tally: this run cannot prove, from any file on disk, that the previous nine ever
happened. **A poll that leaves no trace is indistinguishable from a poll that never ran** — the same
shape as D35, where eight honest "zero replies" reports were all reading a channel that could not contain
the reply. Still a ~5-line fix (`cmd_list` stamping, or a `mark-checked` subcommand) waiting on one word
from the owner.

## Reply check — 2026-08-15 (thirteenth run; BOTH channels read, both quiet)

Same 5 `Applied` rows (Infosys 90, CodeRound AI 89, Innova ESI 87, GoodSpace AI 85, Recro 82) against
`infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `recro.io`. **Zero new replies on either
channel. No Notion writes, no `--event reply` alert** — correct per de-dupe rule 6. Slack got `--event info`.

**The LinkedIn MCP was connected this session, so the inbox was READ, not skipped.** That makes this the
second run in thirteen where the answer on that channel is *quiet* rather than *unknown* (the first was
08-13-later). Of the last four reply checks, two could open the channel and two could not — the session-only
permission gap on `py -3 -m apps.autopilot.replies` is still the reason, and it is still unfixed.

### The LinkedIn inbox, read in full — unchanged since 08-13

6 conversations, identical in shape to the 08-13-later reading. Nothing inbound is unaccounted for:

| Thread | Last message | Reading |
|---|---|---|
| **Recruiter-A** (Infosys) | **07-26 18:58, his** | known reply, ticked 08-11 — **no newer message** |
| Recruiter-B (Innova ESI) | 08-01, `You:` | we spoke last, still no answer (14 days) |
| Recruiter-C (GoodSpace) | 08-01, `You:` | we spoke last, still no answer (14 days) |
| Learnbay (sponsored InMail) | 08-11 | **ad**, not a lead — the `You:` trap from 08-13 |
| Two personal threads | Jun 25 · May 12 | not job traffic |

- **Infosys skipped correctly per de-dupe rule 6**, and — per the 08-13 lesson — that was **verified by
  opening the thread**, not inferred from the inbox list preview. His last message is still
  *"9419280094 / Send ur cv on this number / Wa Alaikum As Salam"*. **Twenty days unanswered.**
- CodeRound AI and Recro still have **no LinkedIn thread at all** (email-only, Easy-Apply-only).
- The five pending 08-06/08-10 invites have produced **no message threads**, consistent with all five still
  reading `Pending` at the 08-14 09:06 accept watch.

### Verification done before any zero was believed (standing rule, thirteenth run)

- Bare `newer_than:14d in:inbox` → **201** threads; `(from:linkedin.com OR from:infosys.com)` → 5 live
  results. Connector and `from:` OR-group syntax both proven before the empty 5-domain result was trusted.
- **Widened** to `newer_than:30d in:anywhere` on the same 5 domains → also empty. Not misfiled in spam.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN).
- **Campus sweep** (naukricampus, doselect, hackerrank, hackerearth, mettl, imocha, codility, hirevue, epam,
  micro1, ceipalmail) → the **same three known items** and nothing new: the 08-05 EPAM cancellation and the
  two Crossing Hurdles/micro1 `ceipalmail.com` funnel mails (08-09, 08-10), all still unread. Thirteenth run
  done by hand; "next work" #6 still unbuilt.
- **Recro's domain was supplied by hand again.** Its `output/outreach/recro/contact.md` exists now (written
  08-14) but deliberately carries **no email address** — there is no verified one and D36 says do not guess.
  So the harvest step still cannot produce `recro.io`, and any future Easy-Apply-only row has the same hole.

### Nothing moved, and the lever is unchanged

Thirteen reply checks have now found exactly **one** reply, and it was found by opening LinkedIn, not Gmail.
**Recruiter-A has been waiting 20 days** for the CV on a personal WhatsApp number. That is still the warmest
lead in the project, it sits inside the company holding the board's best unworked row (Junior AI Engineer 90),
and **only the owner can send it**.

Also still true and still unrecorded anywhere a script can read: the **15th application (TCS)**, found by the
08-13 reply check in an employer-side receipt and never written to the ledger or the board.

## Accept watch — 2026-08-15 13:01 (eleventh consecutive quiet run; all five still pending)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The 08-06 trio is at **day 9** (wall
  **08-20**); the 08-10 pair at **day 5** (wall **08-24**).
- **Step 2 (the poll):** all five `get_person_profile` calls returned, every one reading `· 3rd` with a
  `Pending` button. That doubles as the only trustworthy auth check ([[05-decisions]] D13), so **the
  LinkedIn MCP session is healthy at 13:01**.

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 9 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 9 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 9 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 5 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 5 | `3rd` | `Pending` |

- **Step 3 `due`:** `[]`, **and genuinely empty rather than gate-suppressed.** 13:01 sits squarely inside
  the 09:00–21:00 window, so `cmd_due` was not returning `[]` unconditionally; `list --status accepted` is
  **also `[]`**, so no ripe row is being held for later. Both checks are needed — the two states print
  identically (08-10 21:02 note).

### ⚠️ One profile timed out, and a timeout is not a "still pending"

**Recruiter-H's first `get_person_profile` call failed** — `Page.goto: Timeout 30000ms exceeded`, empty
`sections`, a populated `section_errors` block with a trace path. **A retry seconds later returned the full
profile**, `· 3rd` / `Pending`, so the finding stands on a real read.

Worth recording because of what the failure *shaped like*: the response was still HTTP-successful JSON with
the right `url` and `profile_urn`, and only the absence of `sections` distinguishes it from a good read. A
run that skimmed for "no accept signal" would have found none and recorded the row as unchanged —
truthfully-worded and evidence-free, the exact D30/D35 shape. **The other four calls succeeded either side
of it, so this was a page-load flake, not auth.** Rule: on a `section_errors` response, retry; if the retry
also fails, record the row as **unknown**, never as pending.

### Nothing here is late, and nothing here is the lever

Day 9 on a cold connect with no note is still ordinary latency; day 5 is nothing. **The correct action on
all five is to wait.** The open levers are unchanged: answer **Recruiter-A** (now **20 days**, confirmed
again by the 08-15 reply check earlier today), Track A **A0** (Infosys Junior AI Engineer 90, where
Recruiter-A is already 1st-degree so **no accept is needed at all**), and the 15th application (TCS) still
recorded nowhere a script can read.

### Observations carried forward

- ⭐ **Recruiter-G's Celigo *Ora* / *Agent Builder* hook still stands** as her touch-2 proof-of-effort
  detail. Her profile shows **no new activity** — the CEO repost she shares it from is now ~4 months old and
  her own last post is a year old, so harvest the phrasing at send time ([[05-decisions]] D22).
- ⭐ **Recruiter-H's touch-2 hook re-confirmed verbatim**: *"zero agency dependency — building strong
  pipelines through LinkedIn, GitHub, and niche tech communities"*, headline naming DevOps/Cloud/AI. Her
  last 6 months of posts remain **all mid-to-senior** (Senior Software Architect 10+, Senior Data Leader,
  Senior Functional PM, AAA/Temenos, infra PM) — the relationship is worth more than any specific req.
- 👀 **Recruiter-F still advertises only the *Founder's Office Intern* req.** The AI Engineering Intern
  posting she was pitched for remains closed, unchanged since 08-09. **Do not silently re-aim the packet
  at a different job.**
- 👀 **Recruiter-E has no recent posts at all** — nothing to re-date a proof-of-effort detail against; his
  SkillsCapital "Agentic AI Talent Intelligence Engine" position text is still the only harvestable hook.
- 🪤 **PYMK trap, twelfth confirmation.** The Indian-name sidebar `references` on all five profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

### ⚠️ `last_checked` is still `null` on all five — ELEVENTH recording

Twenty-five profile polls across five accept watches (08-13 ×2, 08-14 ×2, 08-15) and
`output/outreach/pending-invites.json` is **still byte-identical to its 08-06 state**. The escalation to the
owner is now ten runs old and unanswered, so the honest framing is no longer "waiting on a word" but **the
project has chosen, by default, to keep a poll history that only exists in prose**. Still a ~5-line fix
(`cmd_list` stamping, or a `mark-checked` subcommand); still purely additive, touching no board status and
nothing `ledger.py` can reach.

---

## 2026-08-15 — the day applications actually went out (20 confirmed)

**Headline: 0 submissions in the morning, 20 confirmed by evening.** Full procedure in
[[31-apply-batch-runbook]]; reasoning in [[05-decisions]] D45 and D46.

### Board

| | |
|---|---|
| Purged | 43 `New` rows, all 14-21 days old (backup taken) |
| Discovered | 115 unique Easy Apply roles, past week, via `f_AL=true` |
| Loaded | 45 rows scored ≥70, `found=2026-08-15` |
| Applied | **20 confirmed, 0 unconfirmed** |
| Board now | `Applied` 33 · `Skipped` 37 · **`New` 25** · `Invite sent` 1 (counted, not estimated) |

The 20: Lotus Interworks · ThreatXIntel · MyRemoteTeam · Talentgigs · Hyper Lychee Labs ·
slice · Reflections Info Systems · IndiGo · CloudLeap · TCS · BayOne · ShimentoX · Berribot ·
Discovr AI · ANSR · Armakuni · Valiance Solutions · Infosys Finacle · Opttab · Synthires.

### Why it was 0 before

1. **The board was an archive.** `apply-all` over 32 stale rows submitted **0**: 9 closed,
   13 not Easy Apply, the rest stalled. Discovery rots in ~5 days.
2. **`f_EA=true` is not the Easy Apply filter** and LinkedIn ignores it silently. `f_AL=true`
   is. Same query: 1/18 → 17/17. This is also what the LinkedIn MCP's
   `search_jobs(easy_apply=True)` emits, so that flag does nothing.
3. **The bank could not answer the forms.** 44 forms carry 104 distinct questions; it answered
   65. The fix was `survey.py` (read every form, submit nothing), then one editing pass to
   **102 of 104**.

### What is in the bank now that was not

`capabilities` (9 owner-confirmed Yes/No), `logistics` (7, incl. walk-in drives = **No** —
Srinagar to Chennai is ~3000km), `narrative` (reason for change, certifications, primary
technologies, small/large scale), `identity.postal_code` 190020, `education.completed_*`, and
**`experience.technology_years` — 97 technologies** grounded in his CV with a truthful 0 default.

### Still open

- **6 `stalled-validation`, 5 `reached-review`** on the last run. Several are genuine
  mismatches (roles wanting 10+ years); the rest need the §5 hand-diagnosis loop.
- ⚠️ **`NEEDS_AZAM.offer_in_hand` = "Yes / 80000" is UNRECONCILED.** He stated it, so it is
  recorded, but 80,000/month is 9.6 LPA — **above** the 8.4 LPA he asks for. A recruiter
  seeing both will ask. Either raise the expectation or drop the claim.
- Certifications answer truthfully "no formal certifications, but…" so the field never blocks.
  If he ever earns one, it goes in `narrative.certifications`.
- The 13 overdue follow-up nudges from D44 are still unsent (his tick).
- **Recro / Arya Priyadarshini** bare-connect still awaits approval ([[30-warm-insider-runbook]]).

## Accept watch — 2026-08-15 19:25 (twelfth consecutive quiet run; second run of the day)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The 08-06 trio is at **day 9** (wall
  **08-20**); the 08-10 pair at **day 5** (wall **08-24**). Unchanged from the 13:01 run — same calendar day.
- **Step 2 (the poll):** all five `get_person_profile` calls returned populated `sections`, every one
  reading `· 3rd` with a `Pending` button. That doubles as the only trustworthy auth check
  ([[05-decisions]] D13), so **the LinkedIn MCP session is healthy at 19:25**.

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 9 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 9 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 9 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 5 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 5 | `3rd` | `Pending` |

- **Step 3 `due`:** `[]`, **and genuinely empty rather than gate-suppressed.** 19:25 is inside the
  09:00–21:00 window, so `cmd_due` was not returning `[]` unconditionally; `list --status accepted` is
  **also `[]`**, so no ripe row is being held for later. Both checks are needed — the two states print
  identically (08-10 21:02 note).

### ✅ Recruiter-H's profile loaded first-try — the 13:01 timeout was a flake, not a pattern

The 13:01 run needed a retry on this one profile (`Page.goto: Timeout 30000ms exceeded`, empty `sections`).
This run it returned complete on the first call, which **retires the open question** that entry left: it was
page-load latency, not a profile-specific or auth-specific problem. The 13:01 rule still stands and is worth
keeping — **on a `section_errors` response, retry; if the retry also fails, record the row `unknown`, never
`pending`** — but no follow-up work is owed on it.

### ⚠️ Scope note: "no new activity" is only as good as what the main page rendered

Recorded because prior entries have asserted it more strongly than the evidence supports. This run used the
**default scrape (main profile page only)** on all five — no `sections=posts` request. For Recruiter-F and
Recruiter-G the main page happened to carry an activity feed, so their observations below are real reads.
For Recruiter-E the page said outright *"has no recent posts"*. **For Recruiter-D and Recruiter-H no post
list was returned at all**, so this run has *nothing to say* about their recent activity — which is not the
same as "unchanged", and earlier entries claiming a 6-month post history for Recruiter-H were reading a
richer scrape than this one. Same family as D35: an unread channel is not a quiet channel.

### Observations carried forward

- ⭐ **Recruiter-G's Celigo *Ora* / *Agent Builder* hook still stands** as her touch-2 proof-of-effort
  detail; the CEO repost she shares it from is now ~4 months old and her own last post ~1 year. Harvest the
  phrasing at send time, never from this entry ([[05-decisions]] D22).
- ⭐ **Recruiter-H's touch-2 hook re-confirmed verbatim** from her About section: *"zero agency dependency —
  building strong pipelines through LinkedIn, GitHub, and niche tech communities"*, headline naming
  DevOps/Cloud/AI. Her post history was not visible this run (see scope note).
- 👀 **Recruiter-F still advertises only the *Founder's Office Intern* req**, unchanged since 08-09. The AI
  Engineering Intern posting she was pitched for remains closed. **Do not silently re-aim the packet.**
- 🪤 **PYMK trap, thirteenth confirmation.** The Indian-name sidebar `references` on all five profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**.

### Nothing here is late, and nothing here is the lever

Day 9 on a cold connect with no note is ordinary latency; day 5 is nothing. **The correct action on all five
is to wait.** The open levers are unchanged: answer **Recruiter-A** (now **20 days**), Track A **A0**
(Infosys Junior AI Engineer 90, where Recruiter-A is already 1st-degree so **no accept is needed at all**),
and the 15th application (TCS) still recorded nowhere a script can read.

### ⚠️ `last_checked` is still `null` on all five — TWELFTH recording

Thirty profile polls across six accept watches and `output/outreach/pending-invites.json` is **still
byte-identical to its 08-06 state**. Framing unchanged from the 13:01 entry and deliberately not re-argued:
the escalation is now eleven runs old, so the project has chosen by default to keep a poll history that
exists only in prose. Still a ~5-line fix (`cmd_list` stamping, or a `mark-checked` subcommand); still purely
additive, touching no board status and nothing `ledger.py` can reach. **Not implemented this run** because
the instruction was to follow the runbook exactly, and the runbook does not cover it — it needs one word.

## Reply check — 2026-08-15 later (fourteenth run; the FIRST assessment request, found 10 minutes after applying)

Ran per [[11-reply-classifier-runbook]]. **One new reply, classified ASSESSMENT.** Notion row created and
ticked, Slack `--event reply` posted. Gmail read-only throughout; nothing replied to, nothing sent.

### 🔴 Step 1 does not see 30 of the 35 applications

The runbook's input is "Notion rows with `Status = Applied`". Notion returns **5**. The real record —
`output/apply-log/submitted.jsonl` — holds **35**, of which **21 were submitted today**. The 08-15 batch was
written to the local SQLite board and the ledger and **never to Notion**, because `NOTION_TOKEN` is not set
and nothing pushes back (CLAUDE.md records this; the consequence for *this* runbook had not been drawn).

So the runbook, followed exactly, would have checked 5 applications and reported a clean zero — while
**86% of the applications awaiting a reply were outside the query**. That is the D35 shape again in a new
place: not a missed reply, an **unobservable** one. This run went to the ledger instead, and the one real
reply of the day was in the 30 the runbook could not see.

⚠️ **Fix direction:** step 1 should read `submitted.jsonl` (the append-only send record), not the board.
The ledger is the only store that has never been stale or wrong; the board has been both.

### The reply: ANSR / Talent500 / Under Armour India — ASSESSMENT

| | |
|---|---|
| Applied | 2026-08-15 09:30, LinkedIn Easy Apply, `4454549031` |
| Replied | 2026-08-15 09:40 — **ten minutes later** |
| From | `aditi@talent500.co` (Talent500 = ANSR's brand; client is Under Armour India, Bengaluru) |
| Asks | a ~2 min screening questionnaire behind a "Complete Your Application" link |

**Classified `Assessment`, not `Auto-ack`, and the distinction is the whole point.** It shares an auto-ack's
shape — instant, templated, no named human relationship — but it says *"After reviewing your profile, we
believe you could be an excellent fit"* and **the application does not proceed until the questionnaire is
answered**. An auto-ack requires nothing; this one is a gate. Per step 4, Assessment **keeps `Applied`**,
ticks `Reply`, and gets a note. **Still unread in the inbox.**

⚠️ **ANSR had no Notion row, so there was nothing to update.** A row was **created** — beyond the runbook's
"update the matching job", and deliberate: the alternative was a real, action-gated employer request recorded
nowhere, which is exactly how the 15th application (TCS) was lost. The note says on its face that the reply
check created it. Ticking `Reply` also arms de-dupe rule 6, so the next run will skip it.

### Verification done before any zero was believed (standing rule, fourteenth run)

- Bare `newer_than:14d in:inbox` → **201** threads; `(from:linkedin.com OR from:infosys.com)` → live results.
  Connector and `from:` OR-group syntax both proven before any empty result was trusted.
- The 5 Notion domains (`infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `recro.io`) → **empty**.
- **The 21 new companies have no `contact.md`, so no domain to harvest.** Covered instead by a broad
  `newer_than:3d in:anywhere -from:linkedin.com` sweep — 24 threads, read by sender, and **only the
  Talent500 message was job traffic**. This is the honest substitute for a `from:` list that cannot be built.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN) → empty.
- **Campus + ATS sweep** widened to include `talent500.co`, `greenhouse.io`, `lever.co`, `ashbyhq.com`,
  `workable.com`, `smartrecruiters.com` → the Talent500 message plus the **same three known items** (08-05
  EPAM cancellation, two Crossing Hurdles/micro1 `ceipalmail.com` mails), all still unread. Fourteenth run
  done by hand; "next work" #6 still unbuilt.
- 21 LinkedIn `jobs-noreply@linkedin.com` "your application was sent to X" receipts confirm today's batch
  delivered. **These are receipts, not replies** ([[linkedin-autoack-is-not-a-reply]]) — none ticked.

### The LinkedIn inbox, read in full — unchanged since 08-13

6 conversations, byte-identical in shape to the 08-15 morning reading. **Recruiter-A's thread still ends at
his 07-26 18:58 message** — verified by opening it, not inferred from the list preview. **Twenty days
unanswered.** Recruiter-B and Recruiter-C still show `You:` last (14 days). The Learnbay thread is a
**sponsored ad**, and now shows Azam's own "Check My Eligibility" / "Learn More" clicks as replies — an ad
funnel, not a lead. The five pending invites still have no message threads.

### Nothing else moved, and the lever is unchanged

Fourteen reply checks, **two** replies total: Recruiter-A (LinkedIn, 20 days unanswered) and ANSR (today,
unread). Both need Azam, neither needs code. The 15th application (TCS) is **now in the ledger** (line 24,
submitted 08-15) but still has no board row — as do the other 20 from today.

## Reply check — 2026-08-16 00:42 (fifteenth run; both channels read, both quiet)

Ran per [[11-reply-classifier-runbook]]. **Zero new replies on either channel. No Notion writes, no
`--event reply` alert** — correct per de-dupe rule 6. Slack got `--event info`. Gmail read-only throughout.

⚠️ **Short window by design, not by accident.** This run is ~5 hours after the 08-15-later check (which
created the ANSR row at 14:00Z); the clock had just rolled past midnight IST. Both known replies were
already ticked, so the only thing this run could add was *newer* traffic, and there is none.

### The two known replies, re-verified rather than assumed

| Company | Reply | De-dupe | State |
|---|---|---|---|
| **Infosys** (Recruiter-A) | LinkedIn, 07-26 18:58 | `Reply` already ✓ | **21 days unanswered** |
| **ANSR / Talent500** | Gmail, 08-15 09:40 | `Reply` already ✓ | questionnaire **still unread** |

- **Recruiter-A's thread was OPENED, not skimmed** (the 08-13 lesson). It still ends at his
  *"9419280094 / Send ur cv on this number / Wa Alaikum As Salam"*. **No newer message**, so rule 6 skips it.
- **The Talent500 thread still holds exactly one message.** Rule 6 needs "already ✓ **and** no newer
  message" — the second half is a real check, and it was made, not inferred from the tick.

### Verification done before any zero was believed (standing rule, fifteenth run)

- Bare `newer_than:14d in:inbox` → **201** threads; the 7-domain `from:` OR-group returned a live hit (the
  known Talent500 message). Connector **and** OR-group syntax proven before the empty results were trusted.
- Notion `Status = Applied` → **6 rows** (the 5 originals + ANSR, created by the 08-15 run). Domains
  harvested: `infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `skillscapital.io`,
  `talent500.co`; **Recro supplied by hand again** (its `contact.md` deliberately carries no address, D36).
- **The 30 ledger rows with no `contact.md` were covered by a broad `newer_than:2d in:anywhere
  -from:linkedin.com` sweep** — 21 threads, read by sender: newsletters, a Namecheap status mail, Handshake,
  VizMedia, Skool digests. **No job traffic at all.** This is the honest substitute for a `from:` list that
  cannot be built, and it fully spans the gap since the previous check.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN) → empty.
- **Campus + ATS sweep** (18 senders incl. talent500, greenhouse, lever, ashby, workable, smartrecruiters,
  myworkday) → the **same four known items**, nothing new: Talent500 08-15, the two Crossing Hurdles/micro1
  `ceipalmail.com` mails (08-09, 08-10), and the 08-05 EPAM cancellation. All still unread. Fifteenth run
  done by hand; "next work" #6 still unbuilt.
- **LinkedIn inbox read in full** — 6 conversations, unchanged. Recruiter-B and Recruiter-C still show
  `You:` last (15 days). Learnbay is still the **sponsored-ad funnel**, not a lead. The five pending
  08-06/08-10 invites still have **no message threads**.

### ⚠️ A near-miss worth recording: the harvest looked broken and was not

A first pass grepped `contact.md` for an email pattern and returned **"No matches found" across all 18
files** — which reads exactly like "the runbook's step-1 harvest is dead". It was **the glob**: with
`path=output/outreach`, a `*/contact.md` pattern does not match `output/outreach/<slug>/contact.md`.
Verified against a real file before writing anything down — `innova-esi/contact.md` plainly contains
`swaleha.pathan@innovaesi.com`. The harvest is **healthy**: 13 of 18 files carry an address, and 4 of the
5 original Applied companies are harvestable.

Same family as [[the-instrument-can-be-the-bug]] — a canary that failed a working provider. Had this gone
unchecked it would have argued, with a clean-looking six-file result, for "fixing" a mechanism that works.
**A zero from a search you just wrote is a claim about your query first, and about the world second.**

### The lever has not moved in twenty-one days

Fifteen reply checks, **two** replies total, and **both are still sitting on Azam**. Nothing in this run
is a code problem:

1. 🔴 **Recruiter-A — 21 days.** A warm insider gave a personal number and asked for the CV. It is the
   only reply the outreach design has ever produced, at the company also holding the board's best
   unworked row (Junior AI Engineer 90, where he is already 1st-degree — **no accept needed**).
2. 🟡 **ANSR questionnaire — unread.** ~2 minutes of work, and the application **does not proceed**
   without it. It will quietly expire the way the EPAM test did.

Also unchanged: the 20 applications from 08-15 have **no board rows** (no `NOTION_TOKEN`), so step 1 still
cannot see 30 of 35 submissions. The 08-15 fix direction stands — **step 1 should read
`output/apply-log/submitted.jsonl`, not the board.** Not implemented here: the instruction was to follow
the runbook exactly, and this run covered the gap by sweep instead.

## Accept watch — 2026-08-16 01:02 (thirteenth consecutive quiet run; the queue is NINE, and four have no pitch)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing accepted, nothing due, nothing
expired** → step 5's quiet exit: **no Slack post, no Notion writes, nothing sent.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.`
- **Step 2 (the poll):** **nine** `get_person_profile` calls, all returning populated `sections`, every one
  reading `· 3rd` with a `Pending` button. That doubles as the only trustworthy auth check
  ([[05-decisions]] D13), so **the LinkedIn MCP session is healthy at 01:02**. No retries needed.
- **Step 3 `due`:** `[]` — and 01:02 **is** outside the 09:00–21:00 window, so the gate could have been
  suppressing rows. It was not: `list --status accepted` is **also `[]`**, so nothing ripe is being held.
  Both checks are needed; the two states print identically (08-10 21:02 note).

| Who | Company · role | Sent | Day | Degree | Badge |
|---|---|---|---|---|---|
| **Recruiter-E** (CTO) | SkillsCapital · SWE Intern (AI/ML & Agentic AI) **93** | 08-06 | 10 | `3rd` | `Pending` |
| **Recruiter-F** (Co-Founder) | Mirai Alpha · AI Engineering Intern | 08-06 | 10 | `3rd` | `Pending` |
| **Recruiter-D** (Recruitment Consultant) | Hired · AI/ML Engineer (keep-on-file) | 08-06 | 10 | `3rd` | `Pending` |
| **Recruiter-G** (Lead Recruiter, Hyderabad) | Celigo · AI Integration Engineer 80 | 08-10 | 5 | `3rd` | `Pending` |
| **Recruiter-H** (Talent Partner, Singapore) | Neurones IT Asia · DevOps Engineer 82 | 08-10 | 5 | `3rd` | `Pending` |
| 🆕 **Recruiter-I** (TA lead, 15+ yrs) | IndiGo (InterGlobe Aviation) · Python Developer (RAVE) | 08-15 | 0 | `3rd` | `Pending` |
| 🆕 **Recruiter-J** (Associate Recruiter) | Hyper Lychee Labs · LLMOps Engineer | 08-15 | 0 | `3rd` | `Pending` |
| 🆕 **Recruiter-K** (Chairman HRATN) | TalentGigs · AI/ML Developer | 08-15 | 0 | `3rd` | `Pending` |
| 🆕 **Recruiter-L** (Team Lead) | Lotus Interworks · AI Systems Lab Developer | 08-15 | 0 | `3rd` | `Pending` |

Expiry walls: the 08-06 trio **08-20**, the 08-10 pair **08-24**, the 08-15 quartet **08-29**.

### 🔴 Four of the nine knocks have no pitch behind them

**Four new invites went out 2026-08-15 23:04–23:06** — `indigo-interglobe-aviation-ltd`,
`hyper-lychee-labs`, `talentgigs`, `lotus-interworks` — and **no state entry records them**. Same shape as
the 08-06 "three NEW invites found unrecorded" entry: the queue grew between sessions and this file found
out by querying, not by being told. (The 08-15 evening entries cover the 20 applications and the reply
checks; the invites are not in them.)

More important than the bookkeeping: **all four have `contact.md` and nothing else.** No
`touch-2-linkedin.md` exists for any of them.

```
9 pending invites -> 5 have output/outreach/<slug>/touch-2-linkedin.md
                 -> 4 have contact.md ONLY
```

That is the stage-1/stage-2 halves coming apart. `outreach.py` finds and ranks the human and posts the
`ref:<slug>` card; the ✅ sends the bare request. But the **pitch the knock exists to deliver** comes from
the packet build, which has not run for these four. **If any of them accepts, step 3 of this runbook has
nothing to send** — the guardrail is explicit ("never invent the pitch… if a slot cannot be resolved, skip,
mark failed, and say so"), so an unattended run would correctly skip and the accept would sit there.

The window is real but not tight: an accept schedules the follow-up **3–20h out**, so there is most of a
day to write the pitch after the flip. Still, this is the D47 loop half-wired — a knock with no answer
ready is the one shape the two-stage design cannot absorb. **Nothing was built this run**: the instruction
was to follow the runbook exactly, and the runbook does not cover packet building.

### Observations carried forward, and three new ones

- 👀 **Recruiter-F still advertises only the *Founder's Office Intern* req**, unchanged since 08-09. The AI
  Engineering Intern posting she was pitched for remains closed. **Do not silently re-aim the packet.**
- ⭐ **Recruiter-G's Celigo *Ora* / *Agent Builder* hook still stands** (the CEO repost, ~4 months old; her
  own last post ~1 year). Harvest the phrasing at send time, never from this entry ([[05-decisions]] D22).
- ⭐ **Recruiter-H's About re-confirmed verbatim**: *"zero agency dependency — building strong pipelines
  through LinkedIn, GitHub, and niche tech communities"*, ~80 hires/yr, DevOps/Cloud/AI.
- 🆕 ⭐ **Recruiter-K (TalentGigs) is the strongest touch-2 hook in the new quartet.** He chairs HRATN
  (18,000+ members) and his own About names *"empowering students with free employability skills training"*
  and campus/academia bridging. A final-year student is his stated constituency, which is unusual and
  genuine — but harvest the phrasing at send time, not from here.
- 🆕 ⚠️ **Recruiter-L (Lotus Interworks) is a thin target**: **77 connections, 80 followers**, titled *Team
  Lead Simplia*, not a recruiter, no hiring activity. The invite is cheap and already spent, so leave it —
  but do not expect this one to convert, and do not build a packet for it ahead of the other three.
- 🆕 ❓ **Recruiter-I (IndiGo) — a possible shared-roots signal, NOT yet evidence.** The surname *Ganju* is
  commonly Kashmiri. Her profile says **Greater Delhi Area** and shows **no** stated Kashmir tie, so this is
  a lead to verify by hand, not a warm hook to write into a message. D8 warm-first only pays when the tie is
  real; asserting one that is not is worse than a cold approach.
- 🪤 **PYMK trap, fourteenth confirmation.** The Indian-name sidebar `references` on all nine profiles are
  LinkedIn "people you may know" suggestions, **never a warm path**. (`Sunil Reddy` appears on five of the
  nine — that is the recommender, not a connection.)
- ⚠️ **Scope note, unchanged from 08-15:** this run used the **default scrape (main page only)**. Activity
  feeds rendered for Recruiter-D/F/G/K/L; Recruiter-E's page said *"has no recent posts"*; **Recruiter-H,
  Recruiter-I and Recruiter-J returned no post list at all**, so this run has *nothing to say* about their
  recent activity — which is not the same as "unchanged" (D35).

### Nothing here is late, and nothing here is the lever

Day 10 on a cold connect with no note is ordinary latency; day 5 is nothing; day 0 is noise. **The correct
action on all nine is to wait.** The open levers are unchanged and all three still need Azam, not code:
answer **Recruiter-A** (now **21 days**), the **ANSR questionnaire** (unread, gates the application), and
Track A **A0** (Infosys Junior AI Engineer 90, where Recruiter-A is already 1st-degree so **no accept is
needed at all**).

### ⚠️ `last_checked` is still `null` — THIRTEENTH recording

Thirty-nine profile polls across seven accept watches and `output/outreach/pending-invites.json` still
records no poll history; the four new rows were written 08-15 with `last_checked: null` and stayed that way.
Framing unchanged and deliberately not re-argued: the escalation is twelve runs old, so the project has
chosen by default to keep a poll history that exists only in prose. Still a ~5-line fix (`cmd_list` stamping,
or a `mark-checked` subcommand); still purely additive, touching no board status and nothing `ledger.py` can
reach. **Not implemented this run** — the instruction was to follow the runbook exactly, and it needs one
word from Azam.

## Reply check — 2026-08-16 18:27 (sixteenth run; a DEADLINE arrived, and the board was hiding an application)

Ran per [[11-reply-classifier-runbook]]. **One re-alert (ANSR, now hard-deadlined) and one board correction
(Energy Exemplar).** Both channels read. Gmail read-only throughout; nothing replied to, nothing sent.

### 🔴 The ANSR assessment now expires — re-alerted under de-dupe rule 6's *second* limb

A **second** mail from `aditi@talent500.co` landed **2026-08-15 22:11Z (08-16 03:41 IST)**, i.e. ~3 hours
after the 00:42 check: *"the application link expires in 48 hours. Kindly complete your application."*

Classification is **unchanged (Assessment)** — the same ~2-minute screening questionnaire that gates the
Under Armour India application. What changed is that it now has a clock. **Both mails are still unread.**

This is the case rule 6 exists to catch and the one every prior run got to skip. `Reply` was **already ✓**,
so the first limb says skip; but the rule is "already ✓ **and no newer message**", and a newer message is
exactly what arrived. Skipping on the tick alone would have swallowed a deadline. **Slack `--event reply`
posted; `Status` stays `Applied` per step 4; `Reply` stays ✓.**

⚠️ **The 48 hours is ambiguous, so the earlier reading governs.** Counted from the reminder it expires
**08-18 ~03:41 IST**; counted from the original 08-15 09:40Z mail, **08-17 ~15:10 IST**. Nothing in either
mail disambiguates it, so the row records **08-17 15:10 IST** as the deadline. A guess that runs long costs
the application; a guess that runs short costs nothing.

### 🔴 Energy Exemplar was applied to on 08-09 and the board still said `To Apply`

Not a reply, and found only because the harvest included the packet's `contact.md` domain.
`no-reply@energyexemplar.com`, **2026-08-09 09:36Z**: *"we have received your application."*

Classified **Auto-ack**, so per the runbook it warrants no Slack ping and **no `Reply` tick** — ticking an
application-received receipt would silently kill the Day-3/Day-7 cadence
([[linkedin-autoack-is-not-a-reply]]). But the *receipt* is evidence of something else entirely:

```
ledger   submitted.jsonl line 7   -> submitted 2026-08-09, linkedin_id 4436200537, screenshot on disk
employer no-reply@energyexemplar  -> "we have received your application", 2026-08-09 09:36Z
Notion   Status                   -> "To Apply"
```

Two independent records against one stale board field. The row had sat at `To Apply` for **seven days —
one `apply-all` sweep from a duplicate submission**, the exact trap Recro hit on 07-30. **Corrected to
`Applied`, Applied Date 2026-08-09**, with the evidence written into the note.

**The generalisable bit:** an auto-ack is worthless as a *reply* and is first-class evidence of *state*.
The runbook classifies it into the bin marked "no human action" and stops, which is right about the human
and wrong about the board. Same family as [[sent-folder-is-the-record]] and [[ledger-is-the-send-record]] —
a third party's receipt is a record this project does not control and therefore cannot have made stale.

⚠️ It was delivered to **`azamrizwanshah123@gmail.com`** (LinkedIn's verified address), not the canonical
`azamshah25809@gmail.com` on the CV. That is the known email-mismatch item, confirmed live — and it is also
*why* a `from:`-domain sweep built from `contact.md` had never surfaced this one.

### Verification done before any zero was believed (standing rule, sixteenth run)

- Bare `newer_than:14d in:inbox` → **201** threads; the 9-domain `from:` OR-group returned **3 live hits**.
  Connector and OR-group syntax both proven before any empty result was trusted.
- Domains searched: `infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `talent500.co`,
  `skillscapital.io`, `miraialpha.in`, `energyexemplar.com`, **`recro.io` supplied by hand again** (its
  `contact.md` deliberately carries no address, D36).
- **The ~29 ledger rows with no `contact.md` were covered by a broad `newer_than:1d in:anywhere
  -from:linkedin.com` sweep** — 9 threads, read by sender: Ollama, two Skool digests, three beehiiv blasts.
  **Only the Talent500 reminder was job traffic.** This fully spans the gap since the 00:42 check.
- **LinkedIn inbox read in full** — 6 conversations, unchanged. **Recruiter-A's thread was OPENED, not
  skimmed** (the 08-13 lesson): it still ends at his 07-26 18:58 *"9419280094 / Send ur cv on this number"*.
  **No newer message**, so rule 6 correctly skips it. Recruiter-B and Recruiter-C still show `You:` last
  (15 days). Learnbay remains the sponsored-ad funnel. The nine pending invites still have no threads.

### The tally, and the levers

Sixteen reply checks, **three** inbound items of substance: Recruiter-A (LinkedIn, **21 days unanswered**),
ANSR (now deadlined), and — newly counted, though not a reply — one employer receipt that corrected the
board. All three open levers still need Azam, not code:

1. 🔴 **ANSR questionnaire — ~2 minutes, expires 2026-08-17 15:10 IST.** It will otherwise die exactly the
   way the EPAM test did.
2. 🔴 **Recruiter-A — 21 days.** The only reply the outreach design has ever produced, at the company also
   holding the board's best unworked row (Junior AI Engineer 90, already 1st-degree, **no accept needed**).
3. 🟡 **Four of nine pending invites still have no touch-2** (08-16 01:02 accept watch).

Unchanged and still the structural gap: **step 1 reads Notion (6 rows) while the ledger holds 35.** The
08-15 fix direction stands — step 1 should read `output/apply-log/submitted.jsonl`. Not implemented here;
the instruction was to follow the runbook exactly, and this run covered the gap by sweep instead.

## Accept watch — 2026-08-16 21:0x-22:0x (the FIRST accept in six weeks, and a wrongly-targeted invite)

Ran per [[13-accept-watch-runbook]]. **All three steps completed. Nothing sent.** Step 5's quiet exit
applies (nothing accepted *during* this run, nothing due, nothing expired) → **no Slack post, no Notion
writes.**

- **Step 1 `expire`:** `Nothing older than 14 days still pending.` The 08-06 trio is at day 10; its wall
  is 08-20.
- **Step 2 (the poll):** **thirteen** `get_person_profile` calls, every one returning populated
  `sections`, every one reading `· 3rd` with a `Pending` button. Doubles as the auth check
  ([[05-decisions]] D13): **the LinkedIn MCP session is healthy.**
- **Step 3 `due`:** `[]`. Correct on both limbs — the one `accepted` row is due **2026-08-17 09:12**, and
  21:46 is outside the 09:00-21:00 window anyway.

### ✅ Lotus Interworks — SHALE FRANCIS ACCEPTED 2026-08-16 19:49

First accept since the original three (07-26 / 07-30 / 07-31). Detected and recorded by an earlier run
this evening, **not** by this one, so step 2 found it already `accepted` and step 5 correctly stayed
quiet. Pitch auto-sends **2026-08-17 ~09:12 IST**.

Pre-send check applied to `output/outreach/lotus-interworks/touch-2-linkedin.md` (the standing
no-em-dash / no-markdown / no-unresolved-slot / no-relative-time pass): **clean on all four.** It is
addressed to Shale by name, carries no invented company hook, and every number traces to
`highlight-reel.md`. It is safe to fire unattended.

⚠️ Worth remembering against the 08-16 01:02 entry, which called Recruiter-L **"a thin target — 77
connections, Team Lead, not a recruiter… do not expect this one to convert."** That read was reasonable
and **the thin target is the one who accepted.** Accept rate has never been the bottleneck (4 of 4 now);
conversion is.

### ✅ The "four knocks with no pitch" gap from 01:02 is CLOSED

All **fourteen** slugs now hold `touch-2-linkedin.md`. `indigo-interglobe-aviation-ltd`,
`hyper-lychee-labs`, `talentgigs` and `lotus-interworks` gained theirs during the 08-16 evening session.
Step 3 can now answer any accept in the queue.

### 🔴 Berribot — the invite was spent on someone who does not work there, and is himself job-hunting

`Aditya Sharma` (`adityasharmalin`), invited 08-16 19:05 for **M365 Infrastructure SME / L3 Engineer**:

```
contact.md   "Why them: engineer"        <- no employment evidence recorded at all
live profile company slot                 -> "Indian Institute of Technology, Delhi" (no Berribot)
live profile banner                       -> "Open to work · Gurugram +4 more"
live profile headline                     -> "AI / Full-Stack Engineer | IIT Delhi'25 | GATE CS AIR 156"
```

He is a **peer job-seeker**, not a hiring contact, and an M365 infrastructure req is nothing to do with
him. This is **D47's third failure mode returning through a different door**: `employment()` now returns
CURRENT/PAST/UNKNOWN, but `contact.md` for this row records **no employment field whatsoever** — only the
string `engineer`. The check either did not run or its verdict was never persisted, and nothing
downstream could notice, because the file it would have been written to is the same file a human reads.

**Action:** the invite is already spent and cannot be recalled. **If he accepts, do NOT send the 2b** —
mark it failed and say so, per the runbook's "never invent the pitch / stop on anything strange". The
generalisable bit is [[a-keyword-hit-is-not-a-relationship]] again: *the ranking accepted a keyword and
the record kept no evidence, so the error was unreviewable by design.*

### 🟡 Three more targeting notes from the poll (none blocking, all cheap to know)

- **TCS · Himaja Madala** carries a featured **`#OpenToWork`** post: *"I am looking for a new role."* A TA
  recruiter who is herself leaving. The invite is spent; expect little.
- **BayOne · Abhishek Negi** — genuine BayOne recruiter (current, since Jan 2024), but his About lists his
  live reqs as *UI/UX Designers, UX Researchers, UX Writers, Graphic Designers, Content Writers*. He was
  approached for **Agentic AI Engineer**. Headline says "& Engineering Roles", so not wrong, just thin.
- **Discovr AI · Aastha Choudhary** — genuine and current (`Building Team @ Discovr AI`), but **every req
  she or her team advertises is influencer-marketing / brand-partnerships / sales**. The approach was for
  **AI Product Engineer**; no engineering hiring is visible on that company's feed.
- **ANSR · Abarna Devi** is the strongest of the new five: **Associate Director, Talent Acquisition**,
  current, promoted 3 months ago, and ANSR is the company whose **Talent500 assessment expires
  2026-08-17 ~15:10 IST**. That deadline, not this invite, is the live lever.

### ⚠️ Do not poll profiles in parallel — it wedges the browser for 43 minutes

Two `get_person_profile` calls issued in one block: one returned, the other **hung for 2618s** and was
killed by the idle timeout. The LinkedIn MCP drives **one** browser profile
([[one-browser-profile-many-steps]]), so concurrent calls contend rather than pipeline. The remaining
eleven ran **strictly sequentially** with no failures. Cost this run: ~45 minutes of wall clock, which
pushed it past 21:00 and out of business hours. **Poll one at a time.**

### ⚠️ `last_checked` is still `null` — FOURTEENTH recording

Fifty-two profile polls across eight accept watches. Only `lotus-interworks` carries a timestamp, and only
because `mark-accepted` wrote one. Framing unchanged, deliberately not re-argued: still a ~5-line fix
(`cmd_list` stamping, or a `mark-checked` subcommand), still purely additive, still touching nothing
`ledger.py` can reach. **Not implemented** — the instruction was to follow the runbook exactly.

## Reply check — 2026-08-17 10:13 (seventeenth run; the ANSR clock is down to 24h, and the ledger grew by 6)

Ran per [[11-reply-classifier-runbook]]. **One re-alert (ANSR, third mail, 24-hour clock).** Both channels
read. Gmail read-only throughout; nothing replied to, nothing sent.

### 🔴 A THIRD Talent500 mail — de-dupe rule 6's second limb fires for the second consecutive run

`aditi@talent500.co`, **2026-08-16 22:12:48Z** (08-17 03:42 IST), subject *"Pending: Azam, 2-minutes to
complete your job application with Under Armour India"*: **"Your application link expires in 24 hours."**

Classification **unchanged (Assessment)** — same ~2-minute screening questionnaire, same *Complete Your
Application* link, same gate on the same application. **All three mails are still unread.** `Reply` was
already ✓, so limb one says skip; a newer message is exactly what arrived, so limb two says alert.
**Slack `--event reply` posted; `Status` stays `Applied` per step 4; `Reply` stays ✓.**

### The deadline ambiguity NARROWED — and the safe reading is kept anyway

The 08-16 run recorded two irreconcilable readings and adopted the earlier one. The third mail is a
tiebreaker, and it breaks *against* that choice:

```
mail 1  08-15 09:40Z  "48 hours"  ->  08-17 09:40Z  = 08-17 15:10 IST   <- the 08-16 safe reading
mail 2  08-15 22:11Z  "48 hours"  ->  08-17 22:11Z  = 08-18 03:41 IST
mail 3  08-16 22:12Z  "24 hours"  ->  08-17 22:12Z  = 08-18 03:42 IST
```

**Two independent countdowns now converge on 08-17 ~22:1xZ**; mail 1 is the outlier. **The actionable
deadline is still recorded as 2026-08-17 15:10 IST** — a guess that runs short costs nothing, a guess that
runs long costs the application — but the row now carries the evidence that the true expiry is ~08-18 03:41
IST. Worth keeping as a shape: *new evidence that moves a deadline later does not license moving the
action later.*

### 🔴 The ledger grew to 41 while Notion sees 7 — six new submissions today

`output/apply-log/submitted.jsonl` now holds **41** rows. **Six were submitted 2026-08-17** and exist in no
Notion row: Zetheta Algorithms, Data Eminence, QuietSpark, HCLTech, ColigoMed, GC Technologies. Notion's
`Status = Applied` returns **7** (the 5 originals + ANSR + Energy Exemplar, the latter corrected on 08-16).

So step 1, followed exactly, sees **7 of 41** — the gap is now **34**, up from 29 yesterday and 30 on 08-15.
It widens every time the apply step runs, because `NOTION_TOKEN` is not set and nothing pushes back. The
**08-15 fix direction stands and is now three runs old: step 1 should read `submitted.jsonl`, not the
board.** Not implemented here — the instruction was to follow the runbook exactly, and this run covered the
gap by sweep instead.

### Verification done before any zero was believed (standing rule, seventeenth run)

- Bare `newer_than:14d in:inbox` → **201** threads; the 9-domain `from:` OR-group returned **4 live hits**
  (three Talent500, one Energy Exemplar). Connector and OR-group syntax both proven before any empty result.
- Domains searched: `infosys.com`, `coderound.ai`, `innovaesi.com`, `goodspace.ai`, `energyexemplar.com`,
  `talent500.co`, `skillscapital.io`, `miraialpha.in`, **`recro.io` supplied by hand again** (its
  `contact.md` deliberately carries no address, D36).
- **The 34 ledger rows with no `contact.md` were covered by a broad `newer_than:2d in:anywhere
  -from:linkedin.com` sweep** — 16 threads, read by sender: Emergent ×2, Ollama ×2, Skool ×3, beehiiv ×4,
  VizMedia, and the three Talent500 mails. **Only Talent500 was job traffic.** This fully spans the gap
  since the 08-16 18:27 check.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN) →
  **empty result set**.
- **Campus + ATS sweep** (18 senders incl. talent500, greenhouse, lever, ashby, workable, smartrecruiters,
  myworkday, naukricampus, doselect, hackerrank, mettl, imocha, codility, hirevue, epam, micro1, ceipalmail)
  → **only the three Talent500 mails**, nothing new. Seventeenth run done by hand; "next work" #6 unbuilt.
- **LinkedIn inbox read in full** — 6 conversations, unchanged. **Recruiter-A's thread was OPENED, not
  skimmed** (the 08-13 lesson): it still ends at his 07-26 18:58 *"9419280094 / Send ur cv on this number /
  Wa Alaikum As Salam"*. **No newer message**, so rule 6 correctly skips it. Recruiter-B and Recruiter-C
  still show `You:` last (16 days). Learnbay remains the sponsored-ad funnel.

### 👀 Out of scope, but observed: the Lotus Interworks pitch does not appear to have fired

The 08-16 accept watch scheduled Shale Francis's touch-2 for **2026-08-17 ~09:12 IST**. This run read the
LinkedIn inbox at **10:13 IST** and there is **no thread with Shale Francis at all** — a delivered DM would
sit at the top of the list. That is the accept watcher's job and **nothing was done about it here**, but it
is the first accept in six weeks and the one thing on the board with a live, already-won opening.
**Flagging, not acting** — and per [[silent-failure-is-the-house-style]], check the artifact (the thread)
rather than the watcher's log.

### The tally, and the levers

Seventeen reply checks, **two** genuine replies in the project's history. Neither needs code:

1. 🔴 **ANSR questionnaire — ~2 minutes, and the clock is now explicit.** Third mail, still unread. It dies
   exactly the way the EPAM test died if today passes.
2. 🔴 **Recruiter-A — 22 days.** The only reply the outreach design has ever produced, at the company also
   holding the board's best unworked row (Junior AI Engineer 90, already 1st-degree, **no accept needed**).

## Reply check — 2026-08-17 later (eighteenth run; a channel that had been unread for eight days)

Ran per [[11-reply-classifier-runbook]]. **One new classification, two Notion rows corrected.** Gmail
read-only throughout; nothing replied to, nothing sent. ANSR and Recruiter-A both correctly skipped by
de-dupe rule 6 — no newer message on either since the 10:13 run.

### 🔴 The domain list was hand-maintained, and it was missing one — 16 runs of blindness

`notifications@ceipalmail.com` (Crossing Hurdles' Ceipal ATS) is published in
`output/outreach/crossing-hurdles/contact.md` and has been **harvestable since the folder existed**. Every
prior run built its `from:` group from a **hand-copied 9-domain list** rather than from the contact files
the runbook actually specifies, so this sender was never queried. Two mails sat unread for eight days:

```
08-09 10:48Z  "DevOps Engineer | $60/hr Remote | Micro1 x AI Labs"
08-10 11:05Z  "AWS Cloud Engineer | $60/hr Remote | Micro1 x AI Labs"
```

This run harvested the domains **from the 28 `contact.md` files** instead of retyping the list, which is
what surfaced them. Same shape as D35: *the reply was not missed, it was unobservable* — and again the
cause was the input set, not the classifier.

### Classified OTHER, deliberately not Auto-ack

Neither mail acknowledges the application. Both are templated **referrals redirecting to a different
company's job board**: *"Organization: Micro1"*, an `Apply Here` link to `jobs.micro1.ai` carrying a
referral code, and an application process stated as *"resume evaluation & interview stage"* — i.e. it
starts from zero over there. Identical bodies, only the role name swapped.

**So both applications reach nobody.** Crossing Hurdles is a lead-gen funnel into Micro1's board, which is
exactly what the **D36 sourcing screen predicted** for this company (zero employees findable on LinkedIn,
auto-ack funnelling to micro1 in 3 seconds). That prediction is now **evidence rather than heuristic** —
and it is the first time the screen's judgment has been confirmed by the employer's own mail.

`Reply` ticked on both (Other → tick, per the Infosys/Recruiter-A precedent; the Energy Exemplar
*Auto-ack* exception does not apply). There is no human at this company to nudge, so the cadence is
cancelling nothing real. Slack alerted **once**.

### 🔴 Both rows were sitting at `New` after a real submission — the Recro trap, third occurrence

Step 1 queries `Status = 'Applied'`. **Both Crossing Hurdles rows read `New`**, so the runbook's own step 1
could never have reached them; they were found only because the domain sweep ran wider than the row set.
The ledger proves both submissions outright — `submitted.jsonl` lines 10 and 13, with screenshots on disk.

| Row | Sat at `New` | Corrected to |
|---|---|---|
| DevOps Engineer ($60/hr Remote), `4444896795` | 8 days | Applied, 2026-08-09 |
| AWS Cloud Engineer ($60/hr Remote), `4444889874` | 7 days | Applied, 2026-08-10 |

Both were **one `apply-all` sweep from a duplicate submission** — the trap Recro hit on 07-30 and Energy
Exemplar on 08-16. Three occurrences now; the common cause is unchanged and structural: `NOTION_TOKEN` is
not set, so nothing writes submissions back to the board.

⚠️ A **third** Crossing Hurdles row (`Platform Engineer`) is still at `New` and has **not** been applied to.
On this evidence it should not be.

### Verification done before any zero was believed (standing rule, eighteenth run)

- Bare `newer_than:14d in:inbox` → **201** threads. Domain OR-group → **6** hits (3 Talent500, 2 Crossing
  Hurdles, 1 Energy Exemplar). Connector and `from:` OR-group syntax proven before any empty result.
- **10 domains, harvested from `contact.md` not retyped**: `infosys.com`, `coderound.ai`, `innovaesi.com`,
  `goodspace.ai`, `energyexemplar.com`, `skillscapital.io`, `miraialpha.in`, **`ceipalmail.com` (new)**,
  `talent500.co`, and `recro.io` supplied by hand again (its `contact.md` carries no address, D36).
- The 34 ledger rows with no `contact.md` covered by `newer_than:2d in:anywhere -from:linkedin.com` → 17
  threads, read by sender: Ideogram, Google, Emergent, VizMedia, Ollama ×2, Skool ×3, beehiiv ×4, and the
  three Talent500 mails. **Only Talent500 was job traffic.** Spans the gap since the 10:13 check.
- **Bounces clean** at `newer_than:14d in:anywhere` → empty result set.
- **Campus + ATS sweep** (20 senders, now including `micro1.ai` and `ceipalmail.com`) → only the three
  Talent500 mails. Eighteenth run done by hand; "next work" #6 still unbuilt.
- **LinkedIn inbox read in full** — 6 conversations, unchanged. Recruiter-A's thread **opened, not skimmed**
  (the 08-13 lesson): still ends at his 07-26 18:58 *"9419280094 / Send ur cv on this number"*. No newer
  message, so rule 6 correctly skips it.

### 🔢 The six 08-17 submissions have produced no mail at all

Zetheta, Data Eminence, QuietSpark, HCLTech, ColigoMed, GC Technologies — submitted today, **zero inbound**,
not even an auto-ack. Ledger unchanged at **41** rows since the 10:13 run. Notion `Applied` now reads **9**
(7 + the two Crossing Hurdles corrections), against 41 in the ledger — gap **32**, down from 34 only because
this run corrected two rows by hand. **The 08-15 fix direction stands and is now four runs old: step 1
should read `submitted.jsonl`, not the board.**

### 👀 Out of scope, unchanged: the Lotus Interworks pitch still has not fired

The 08-16 accept watch scheduled Shale Francis's touch-2 for **2026-08-17 ~09:12 IST**. The 10:13 run found
no thread; this run, hours later, finds **no thread with Shale Francis at all**. The first accept in six
weeks, and the pitch is still not out. Flagging for the second consecutive run, **not acting** — it is the
accept watcher's job. Check the thread, not the watcher's log ([[silent-failure-is-the-house-style]]).

### The tally

Eighteen reply checks. **Three** inbound classifications in the project's history: Recruiter-A (Other,
22 days unanswered), ANSR (Assessment, deadline today), Crossing Hurdles (Other, dead end). Only the first
two are worth Azam's time, and neither needs code.

## State at 2026-08-17 11:00 — both inboxes readable, the pitch delivered

### What changed today

| | Before | Now |
|---|---|---|
| Tests | 349 | **405** |
| Gmail | never authorised, `needs-setup` | **live, read-only, verified by a real read** |
| `free/dm.py` | 9/9 green but never exercised | **one confirmed delivery**, two bugs out |
| Claude stack | unchanged | **still unchanged** (`git diff rewrite/phase-0` empty) |

### The delivery, and why it took three attempts

`SHALE FRANCIS` (Lotus Interworks, AI Systems Lab Developer) accepted 2026-08-16 19:49; the pitch
was due 09:12. The 08-17 00:08 pipeline run reported nine steps green — but `free/dm.py` had
**nothing due at the time**, so it had never opened a composer. The previous session's own log line
had already flagged the gap: *"the Lotus Interworks pitch scheduled 08-17 09:12 has not fired —
there is no Shale Francis thread in the inbox at all."*

1. **10:21** — `not-connected: no Message button`. False. See **D52**: the control is an `<a>`.
2. **10:32** — `sent, but could not read it back`, tracker marked. **Also false.** Inbox at 10:40:
   six conversations, newest a week old, no thread with him. The tracker mark was undone from a
   backup, one record by username.
3. **10:38** (after the real fix) — `confirmed: the message is in the thread`, then **verified
   independently** through the inbox: seven conversations where there had been six.

The lesson is in **D52**, and it is uncomfortable: attempt 2 shipped *with a written justification
for the behaviour that caused it*. A failure direction chosen to avoid one bad outcome buys that
safety with the other one, and it is only worth choosing once the evidence is reliable.

### Inbox, as of the first real Gmail read

```
read 40 message(s) from the last 14 days: 3 worth a look, 12 bulk, 25 auto-ack
```

All three are **Talent500** (`aditi@talent500.co`) about the same *Software Engineer — Data and AI
Platform* application. The newest says the link **expires in 24 hours**. The Claude stack's reply
check had flagged the same thread independently at 10:13. It is a ~2-minute screening
questionnaire and it is the only thing in the inbox on a clock.

⚠️ **Owner action, unchanged from this morning:** answering Recruiter-A on his personal number is
still the warmest lead in the project and still cannot be automated.

### Coverage, from the 10:24 scheduled reply check

| | |
|---|---|
| applications | **41** across 37 companies |
| reached a named human | **28** |
| reached **nobody** | **9** |

Six of the nine are the 08-17 00:08 free-stack submissions and are simply waiting their turn —
`outreach.py` runs after `apply` and works a limited batch per cycle. **Worth watching, not yet
worth fixing:** if that column grows faster than outreach clears it, the apply step is outrunning
the half of the pipeline that turns an application into a conversation, which is [[05-decisions]]
D32 returning.

### Deliberately not done

- **`connect.py` has the same "unconfirmed counts as sent" shape** as the dm bug. Left alone: it
  has a page-level pre-check, it has confirmed five real invites by the Pending badge, and a
  duplicate connection request is an account-restriction signal rather than an embarrassment.
  Editing an account-risk-sensitive sender immediately after getting the same judgement call wrong
  was the worse risk.
- **Nothing on the free stack is scheduled.** Still the owner's call.

## Reply check — 2026-08-17 (nineteenth run; two new mails, no new reply, and no Slack ping)

Ran per [[11-reply-classifier-runbook]]. **Zero new replies. Nothing written to Notion except one
evidence note; deliberately NO Slack alert.** Gmail read-only throughout; nothing replied to, nothing
sent. Both channels read.

### 🔴 Talent500 sent two more mails and neither is a reply — the domain has no bulk filter

`aditi@talent500.co` has now sent **five** mails. Three are the ANSR application chase. The two that
arrived since the 18th run are not:

```
08-17 06:19Z  "Profile Shortlisted: Unlock Interviews With Guidance From Ex-Amazon Leader"  BULK
08-17 09:45Z  "Talent500 - Email Verification Code"  (OTP 599650)                           TRANSACTIONAL
```

The first is a **webinar advert**, and the tells are all in the body, not the subject: addressed
*"Hi there"* rather than "Hi Azam", selling a 17-Aug 6PM LIVE session run by **Interview Kickstart**,
*"🔥 Only 15 seats remaining"*, a **List-Unsubscribe** footer, and an audience of *"experienced tech
professionals"* / *"mid-level engineers"* — which Azam is not. The second is an account-verification
OTP. Neither acknowledges or advances the application.

⚠️ **The word "Shortlisted" is in the subject line.** A classifier keying on keywords calls that
**Interview** and pings Slack loudly. This is the [[alert-noise-is-a-correctness-bug]] shape arriving
through a channel we opened ourselves: **Talent500 is both the ATS brand and a content marketer**, so
`from:talent500.co` pulls marketing straight into the reply channel. The free stack's `free/gmail.py`
already filters on `List-Unsubscribe` (D53); **the Claude-stack reply check does not.** That is the
concrete fix direction, and it is cheap — the header is already in the message.

### Why no Slack alert, when de-dupe rule 6 literally says to send one

Rule 6's second limb is *"or a newer message arrived since last check"*, and two did. It was **read
against its stated purpose** (*"Never double-ping the same reply"*) rather than literally: step 5 alerts
**per NEW reply**, and neither mail is a reply. Three consecutive runs have already escalated this same
~2 minutes of work; a fourth ping carrying a webinar advert and a dead OTP would spend the owner's
attention on noise and make the next real ping cheaper to ignore. **Recorded as a judgement, not a rule
change** — the escalation is in this file and in the row instead.

### 📌 Consistent with, but NOT proof of, the owner acting on the deadline

The OTP sits inside a cluster of **account-signup mail from the same morning**, all plainly Azam's own:
Obsidian account activation **09:51Z**, Obsidian Sync signup **09:52Z**, and a Microsoft *"new app(s)
connected"* notice at **10:28Z** for the `remotely-save` plugin. Three signup flows in eleven minutes
makes *"Azam clicked Talent500's Complete Your Application link himself"* the likeliest reading — which
would be the outcome three runs have been asking for.

**It is not evidence the questionnaire was completed.** The reply check cannot see the questionnaire's
state, and **all five Talent500 mails are still UNREAD**. The deadline is unchanged: the 24h countdown
from 08-16 22:12Z expires **08-17 22:12Z = 2026-08-18 03:42 IST**.

### 🔴 `talent500.co` is not harvestable either — the second D36 hole

The 18th run fixed the input set by harvesting domains from the **28 `contact.md` files** instead of
retyping a list. That fix does not reach this sender: `output/outreach/ansr/contact.md` carries
**LinkedIn profile URLs only, no email address** — same shape as `recro.io` (D36). So the harvest gives
8 domains and **two must still be supplied by hand**. A harvest that silently covers 8 of 10 is the
[[derive-the-input-set-never-retype-it]] lesson only two-thirds learned: the *method* is right, the
**source files are incomplete**. Worth making `outreach.py` write the reply-to address it actually saw.

### Verification done before any zero was believed (standing rule, nineteenth run)

- Bare `newer_than:14d in:inbox` → **201** threads; the 10-domain `from:` OR-group returned **8** hits
  (5 Talent500, 2 Crossing Hurdles, 1 Energy Exemplar) — all previously classified. Connector and
  OR-group syntax proven before any empty result was believed.
- **10 domains: 8 harvested from `contact.md`** (`infosys.com`, `coderound.ai`, `innovaesi.com`,
  `goodspace.ai`, `energyexemplar.com`, `skillscapital.io`, `miraialpha.in`, `ceipalmail.com`) **plus
  `recro.io` and `talent500.co` by hand** (neither has an address in its contact file).
- **The 32 ledger rows with no `contact.md` covered** by `newer_than:2d in:anywhere` minus the known
  bulk senders → 12 threads, read by sender: n8n, Microsoft security, Obsidian ×2, NVIDIA, Twilio,
  Ideogram, Emergent, VizMedia, Ollama. **Zero job traffic.** Spans the gap since the 18th run.
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN)
  → **empty result set**.
- **Campus + ATS sweep**, 20 senders → only the five Talent500 mails, the two Crossing Hurdles mails,
  and the already-recorded 08-05 DoSelect cancellation. Nineteenth run done by hand; "next work" #6
  still unbuilt.
- **LinkedIn inbox read in full — 7 conversations, up from 6.** The new one is **Azam's own outbound**
  pitch to SHALE FRANCIS at 10:38, i.e. the D52 delivery confirmed from a second angle. **No inbound
  reply from him yet.** Showkat Gaffar's thread was **opened, not skimmed** (the 08-13 lesson): still
  ends at his 07-26 18:58 message. No newer message, so rule 6 correctly skips it.

### The tally

Nineteen reply checks, **three** genuine inbound classifications in the project's history, unchanged
this run. The board's two live items both need a human and neither needs code:

1. 🔴 **ANSR questionnaire — expires tonight**, 2026-08-18 03:42 IST on the convergent reading.
2. 🔴 **Showkat Gaffar — 22 days**, on a personal number, at the company holding the board's best
   unworked row (Junior AI Engineer 90, already 1st-degree, no accept needed).

## Reply check — 2026-08-17 ~21:30 IST (twentieth run; genuinely quiet, and the ANSR clock is ~6h out)

Ran per [[11-reply-classifier-runbook]]. **Zero new replies. Nothing written to Notion, no Slack alert** —
both correct per step 4 (updates fire *per reply*) and step 5 (*per NEW reply*). Gmail read-only
throughout; nothing replied to, nothing sent. Both channels read. This is the first run in four where
there was nothing new to classify *at all* — no new mail from any harvested sender, no new LinkedIn inbound.

### The one live item, and it expires tonight

The ANSR / Talent500 / Under Armour India screening questionnaire. **No sixth Talent500 mail arrived**, so
nothing about the classification, the deadline or the evidence changed since the nineteenth run. On the
convergent reading the 24h countdown from 08-16 22:12Z expires **08-17 22:12Z = 2026-08-18 03:42 IST**,
i.e. roughly six hours after this check. **All five Talent500 mails are still UNREAD**, and the reply check
still cannot see the questionnaire's state — only the mail about it.

⚠️ **The nineteenth run's "consistent with Azam having clicked the link" inference is now WEAKER, not
stronger.** That reading rested on the 09:45Z Talent500 OTP sitting beside two Obsidian signups. This run's
wider sweep shows the whole morning was sync-tooling setup: Ideogram 04:42Z, Google/Autosync 08:50Z,
Obsidian ×2 09:51–09:52Z, **Dropbox account + `remotely-save` app + two browser sign-ins 10:42–10:53Z**, and
a Microsoft app-consent notice 10:28Z. An account-verification OTP is much less distinctive inside *that*
cluster than beside two mails. It remains **consistent with, and still not evidence of, completion** — the
honest position is unchanged, but the supporting argument should not be leaned on.

### No Slack ping, and this time the reason is different from run 19

Run 19 withheld because the two new mails were not replies. Here there is **no new mail at all**, so step 5
does not fire on any reading, literal or purposive. Separately: a fourth card on the same ~2 minutes of work
would be [[alert-noise-is-a-correctness-bug]], and it was **unnecessary** — the owner was present in the
session when this ran, so the deadline was put in front of him directly, which is a higher-bandwidth channel
than a Slack card and costs no alert fatigue. Slack is for when he is away.

### Verification done before any zero was believed (standing rule, twentieth run)

- Bare `newer_than:14d in:inbox` → **201** threads; the 10-domain `from:` OR-group → **8** hits (5 Talent500,
  2 Crossing Hurdles, 1 Energy Exemplar), **every one already classified**. Connector and OR-group syntax
  proven live before any empty result was believed.
- **10 domains: 8 harvested from the 28 `contact.md` files** (`energyexemplar.com`, `coderound.ai`,
  `skillscapital.io`, `miraialpha.in`, `ceipalmail.com`, `infosys.com`, `goodspace.ai`, `innovaesi.com`)
  **plus `recro.io` and `talent500.co` by hand** — neither has an address in its contact file (D36; the
  second hole is still open).
- 🔴 **The harvest itself nearly returned a false zero.** A `--glob '*/contact.md'` ripgrep filter matched
  **nothing**; `**/contact.md` matched all 28. The empty result was a calm, confident "No matches found" and
  is byte-identical to "this project has no contact files" — [[wrong-probe-gives-a-confident-negative]],
  caught only because 19 prior runs had recorded a non-zero domain count to disagree with it. **A harvest is
  only safer than a retyped list if the harvest is verified against a known positive.**
- **The 32 ledger rows with no `contact.md` covered** by `newer_than:1d in:anywhere -from:linkedin.com` → 23
  threads, read by sender: Dropbox ×4, Google accounts ×5, Obsidian ×2, Microsoft, ninjaaitools, n8n,
  beehiiv, NVIDIA, Skool ×2, Twilio, Ideogram, Emergent + the 3 known Talent500. **Zero job traffic.** Spans
  the gap since the nineteenth run (whose newest mail was 09:45Z; this run read to 15:58Z).
- **Bounces clean** at `newer_than:14d in:anywhere` (mailer-daemon / postmaster / Undeliverable / DSN) →
  **empty result set**.
- **Campus + ATS sweep**, 20 senders → the 5 Talent500, the 2 Crossing Hurdles, and the already-recorded
  08-05 DoSelect EPAM cancellation. Nothing new. Twentieth run done by hand; "next work" #6 still unbuilt.
- **LinkedIn inbox read in full — 7 conversations.** Composition changed but not the substance: a
  **Snowflake sponsored ad** (18:18 today) replaced Learnbay at the top; both are ad funnels, not traffic.
  **Two threads were OPENED via `thread_id`, not skimmed** (the 08-13 lesson): **Showkat Gaffar** still ends
  at his 07-26 18:58 *"9419280094 / Send ur cv on this number / Wa Alaikum As Salam"*, and **SHALE FRANCIS**
  shows only Azam's 10:38 outbound with **no inbound reply**. Rule 6 correctly skips both.

### 📌 The row/ledger gap, measured precisely — and it is NOT the Recro trap this time

Ledger **41** (unchanged since the nineteenth run — no new submissions today). Notion `Status = 'Applied'`
returns **9**. Gap **32**, so step 1 followed exactly sees **22%** of the real set. **The 08-15 fix direction
is now five runs old: step 1 should read `submitted.jsonl`, not the board.**

A check of 12 recently-submitted companies shows the gap has a *different shape* than the three prior
duplicate-submission scares, and it is worth not conflating them:

| What was found | Rows | Duplicate-submission risk? |
|---|---|---|
| Applied role has a correct `Applied` row | 1 (ANSR) | none |
| Company has a row at `New` for a **different req** than the one submitted | 3 (Data Eminence *AI DevOps*, HCLTech *GenAI*, TCS *Gen AI*) | **no** — one-per-company-per-role is intact |
| Applied role has **no Notion row at all** | 8 (Zetheta, QuietSpark, ColigoMed, GC Technologies, Lotus Interworks, BayOne, Berribot, Discovr AI) | none *today*, but invisible to every board-driven step |

So the Recro/Energy-Exemplar/Crossing-Hurdles trap — *a row sitting at `New` after that exact role was
submitted* — **did not recur here**. The live defect is plain absence: eight submissions the board cannot
see. **No 32-row status write was made**, deliberately: that is the missing `NOTION_TOKEN` push-back's job,
not the reply check's, and doing it unasked would bury a real correction under bulk edits.

### The tally

Twenty reply checks, **three** genuine inbound classifications in the project's history, unchanged this run.
Both live items need a human and neither needs code:

1. 🔴 **ANSR questionnaire — ~2 minutes, expires 2026-08-18 03:42 IST.** It dies exactly the way the EPAM
   test died if tonight passes.
2. 🔴 **Showkat Gaffar — 22 days**, on a personal number, at the company holding the board's best unworked
   row (Junior AI Engineer 90, already 1st-degree, no accept needed).
