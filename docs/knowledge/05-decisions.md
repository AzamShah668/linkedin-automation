# 05 — Decisions & Rationale

Back to [[00-INDEX]].

## D1 — Human-in-the-loop, not full auto-send

**Decision:** the AI does discovery, research, tailoring, and drafting; a human approves before anything sends.
**Why:**
- LinkedIn's User Agreement forbids bots/scraping/auto-DMs. Bulk automated messaging is the #1 cause
  of account restriction/permanent ban. A banned LinkedIn account sets the job hunt *back*, not forward.
- Recruiters recognize and ignore/flag generic mass messages. Approval keeps quality high.
- Reversible later: once response quality is proven and safeguards are trusted, we can auto-send the
  top-scoring, well-templated cases. Start safe, loosen deliberately.

## D2 — Legitimate data sources over scraping

**Decision:** pull jobs from ATS public APIs, job-board APIs, and parsed LinkedIn email alerts —
never headless LinkedIn scraping. See [[03-data-sources]].
**Why:** structured, richer data; no ToS violation; no IP bans; more reliable than brittle scrapers.

## D3 — Email as the primary outreach channel

**Decision:** deliver the CV + Highlight Reel primarily via **Gmail** (already connected), not LinkedIn DMs.
**Why:** email isn't rate-limited into a ban, handles attachments cleanly, and reaches recruiters directly.
LinkedIn stays a *research + manual, personalized-touch* channel.

## D4 — Python + Claude + SQLite

**Decision:** Python for the pipeline, Claude API for research/writing, SQLite for storage (Postgres later).
**Why:** fastest path to a working system; best ecosystem for AI + data + integrations; SQLite = zero-setup
for a single-user tool. Swap to Postgres only if multi-user/scale demands it (YAGNI until then).

## D5 — No fabrication in generated documents

**Decision:** tailoring emphasizes and re-frames the owner's *real* achievements to match each role;
it never invents experience, credentials, or metrics.
**Why:** integrity, and because fabrications collapse in interviews. The system's edge is *relevance and
speed*, not fiction.

## D6 — Highlight Reel as a first-class artifact

**Decision:** generate a separate, punchy, recruiter-facing achievement summary per role (owner's explicit ask).
**Why:** it's the hook that earns the read before the formal CV is opened; distinct tone and structure from
the résumé, so it gets its own generator in [[02-architecture]].

## D7 — MCP-first + Notion store now; custom Python code deferred

**Decision (2026-07-25):** run the pipeline today on **connected MCP services + the two skills**, not custom
code. Discovery = **LinkedIn MCP `search_jobs`**; the job store = a **Notion database ("Job Hunt — Autopilot")**;
CV/outreach = the `cv-architect` / `recruiter-outreach` skills. The coded `src/` system in [[02-architecture]]
(SQLite, ATS adapters, schedulers) is the *later* automation, not a prerequisite.
**Why:** it got a working end-to-end flow (10 jobs found, scored, stored; 3 fully processed) in one session
with zero code to maintain. Notion also gives the owner a browsable board for free. Build the code robot only
when the manual/MCP loop proves the value and daily volume justifies automation (YAGNI until then).
**Consequence (the risk to manage):** work now lives in external services, invisible to future sessions unless
recorded. Mitigation: **[[07-current-state]] is the mandatory live snapshot**, updated every session. This
decision is *why* that file exists — a near-miss on 2026-07-25 (almost rebuilt the existing Notion store).

## D8 — Warm-insider-first outreach (owner-praised, now mandatory)

**Decision (2026-07-25):** for **every** company, first search for a **warm insider who shares Azam's roots**
— mutual connection → same university → **same home region/community (Kashmir/Srinagar/J&K)** → former
employer — and lead the personal touch (Touch 2) with that *true* tie, before any cold recruiter.
**Why:** a warm referral beats a cold recruiter everywhere; a stranger is easy to ignore. This surfaced two
Kashmiri engineers inside Infosys (found via the *region* tie, not the school) — owner called it a "brilliant
move" and asked that it always happen. **Guardrail:** claim only the tie the data shows (region confirmed but
university not → "fellow Kashmiri", not "fellow CUK grad"; mark the stronger line `[VERIFY]`). A false claim
of connection is the fastest way to lose a recruiter's trust. Written into `recruiter-outreach/references/find-recruiter.md`.

## D9 — One canonical CV engine: `cv-architect` (cv-builder merged in & retired)

**Decision (2026-07-25):** consolidate the two divergent CV engines into a single canonical skill,
**`cv-architect`** (`.claude/skills/cv-architect/`).
**Why:** `cv-builder` (`.agents/skills/`) held the real content (Azam's `master_cv.md` + approved
OSS-framing/contact corrections) but was **not a registered/invokable skill** (wrong location).
`cv-architect` was invokable, in the standard `.claude/skills/` location, with richer references
(ats-optimization, humanization, visual-spec, achievement-mining) and three-brain grounding — but lacked the
master CV. Keeping both caused the exact doc-vs-reality mismatch the brains exist to prevent.
**What moved:** master CV → `cv-architect/references/master-cv.md`; proven Azam template →
`cv-architect/assets/cv-template-azam.html` (alongside the dependency-free default `cv-template.html`).
cv-builder is now a **tombstone** pointing here. All docs (CLAUDE.md, Brains 1/2, memory, positioning-selector)
now reference `cv-architect` only.

## D10 — Complete the pipeline via Path A (MCP-first + light glue), not a coded rebuild

**Decision (2026-07-25):** finish the pipeline by adding a thin automation layer on top of the working
Notion + MCP setup — a scheduler, event hooks, and a small Gmail sender — rather than building the planned
coded `src/` system (SQLite, ATS adapters, etc.).
**Why:** the MCP-first stack already delivers discovery + store + tailor + outreach end-to-end (decision D7);
Path B would re-implement what Notion/MCP give for free — weeks of work, more to maintain, no added value yet
(YAGNI). Build the robust coded system only if daily volume/scale later demands it.
**Plan:** [[08-completion-plan]] (sequenced gaps + definition of done).

## D13 — The fit score decides who gets a packet (no human decision)

**Decision (2026-07-26):** the fit score alone determines whether a job gets worked up. No ad-hoc choosing.
- **85 or above → automatically build the FULL packet**: tailored CV (+PDF, ATS-checked), recruiter found
  with the D8 warm-insider check, Touch 1 email draft, Touch 2 LinkedIn note, Slack action card + CV upload.
- **0–84 → store and alert only.** It sits in Notion, appears in the digest, and is built only on request.

**Why:** owner asked *"how do we decide to make the CV of a particular job?"* — and the honest answer was
that no rule existed, so it felt arbitrary. The scoring step already exists and already encodes fit, so the
score should be the decision. This removes the human bottleneck for the jobs that matter and stops Claude
usage being spent tailoring CVs for weak matches.
**Efficiency note:** batch by company before building. Multiple roles at one employer (Infosys ×3, Hired ×3
on the board today) share one recruiter search and often one CV variant.
**Dependency:** this rule only fires by itself once the unattended runner is fixed — see [[07-current-state]];
the headless scheduled task is currently broken, so today the rule is applied when a session runs.

## D12 — ONE general CV hosted publicly for email; tailored variants stay private

**Decision (2026-07-25):** emails link a **single general CV**, hosted at
`github.com/AzamShah668/AzamShah668/blob/main/Azam-Shah-CV.pdf` (the profile repo, no new public repo
needed). The **tailored variants are never published** — they stay local in `output/pdf/` for LinkedIn
applications and direct uploads, where you pick one per role.
**Why:** the original plan (publish all three tailored CVs to a public repo) had a flaw the owner caught: a
recruiter who clicks the link can browse the repo root and see *AI Engineer*, *DevOps*, and *FDE* CVs side by
side. That signals "he rewrites himself for whoever's asking" and undermines the exact positioning the email
just established — the opposite of this project's tailoring thesis. Renaming files doesn't help (the root is
always browsable) and separate repos are worse (all listed on the public profile). One general CV has no
variants to expose. Secondary benefit: less public exposure of the phone number on the CV.
**Consequence:** email CV delivery is now a stable link (fully automatable, no attachment step — the Gmail
API cannot attach files anyway); tailoring lives in the *message*, not the linked CV. Which general CV: the
cv-architect canonical `azam-shah-devops-cv` (tied top ATS at 89%). Refresh it by pushing over the same path
so every previously-sent link stays current.

## D11 — Discovery robot runs LOCAL (scheduled task), not a cloud routine

**Decision (2026-07-25):** the automatic daily discovery runs as a **local Windows Scheduled Task** invoking
Claude headless (`tools/daily-discovery.ps1` → [[09-discovery-runbook]]), not an Anthropic cloud routine.
**Why:** the rich LinkedIn job/people/company search comes from the **local** `mcp-server-linkedin` (a
browser-automation MCP on Azam's authenticated session). A cloud agent can't reach it — it's not a cloud
connector, and Slack + `.env` + tools are local too. **Composio was evaluated** (owner asked): its LinkedIn
toolkit only offers the official API (no job/people search) or paid CrustData (posts, not jobs) or Exa
web-search workarounds — none replicate the local search, and running LinkedIn automation from a cloud/
datacenter IP raises ban risk (violates D1). Composio *can* do Slack, but that doesn't unlock cloud
discovery. **Trade-off accepted:** the task only runs when the PC is on/awake. If true PC-off autonomy is
ever needed, the fallback is a *different, thinner* cloud discovery (Gmail LinkedIn-alert parsing + Exa web
search + Slack-via-Composio) — explicitly lower quality than the local LinkedIn-MCP search.

## D12 — Two-stage LinkedIn outreach: bare request first, pitch after they accept

**Decision (2026-07-26, owner's design):** stop attaching a note to connection requests. Stage 1 sends a
**bare** request and tracks it (`tools/invite_tracker.py`, [[12-approved-send-runbook]]). Stage 2 polls every
4h for the accept and, a randomised 3–20h later (business hours only), auto-sends the CV + full pitch
([[13-accept-watch-runbook]]).
**Why:** the caps are wildly asymmetric on a free account — a request **with** a note is limited to **3 per
month**, a bare request to ~100/week, and a DM to an existing 1st-degree connection is **uncapped**. The old
one-shot design put the entire pitch inside the scarcest channel available. Splitting it moves the payload to
the free channel and removes the bottleneck: 7 queued jobs were unreachable under the old model.
Forced by evidence the same day: the LinkedIn MCP's `connect_with_person` returns `custom_note_limit_reached`
and silently sends **nothing** whenever a `note` is supplied and LinkedIn is showing its quota banner — it
failed identically at 290 and 197 chars with the note box reading `0/200`, so length was never the cause.
Called with no `note`, it sends fine (verified on Recruiter-A, 2026-07-26).
**Consequence:** the 3 monthly personalised notes become a scarce reserve **spent only on warm insiders, by
hand** (D8 still rules — that's where shared-roots framing earns the accept). Notion gains a `Status =
"Invite sent"` step between `To Apply` and `Applied`; a request is not an application. Accept rates on bare
requests are lower than on noted ones — accepted deliberately, because an uncapped pitch to someone who
already said yes beats a capped pitch to someone who hasn't.
**The one gate this removes:** stage 2 messages without a fresh human tick. Mitigation — the owner still
approves the *words* at stage 1 (the ✅); the robot only chooses the *moment*; `FOLLOWUPS_DAILY_CAP=3` keeps
volume invisible; any captcha or odd MCP status halts the run instead of retrying.

## D13 — Scheduled tasks are the runtime; they are fragile in three specific ways

**Decision (2026-07-26):** the pipeline runs as four **local Windows Scheduled Tasks** driving headless Claude
(Daily Discovery, Flush Approved every 30 min, Watch Accepts every 4 h, Reply Check). This extends D11 (local,
not cloud) from discovery to the whole pipeline including sending.
**Why:** LinkedIn is only reachable through the local browser-automation MCP, so every stage that touches it
must run on Azam's machine. Slack reactions are polled rather than pushed because push needs Socket Mode plus
an always-on listener ([[12-approved-send-runbook]]).
**Consequence — three failure modes that all present as "nothing happened", found the hard way on day one:**
1. **Battery.** `New-ScheduledTaskSettingsSet` defaults `DisallowStartIfOnBatteries = $true`. On a laptop that
   silently kills every task — Task Scheduler reports success and leaves the task in *Queued*. All four tasks
   had been dead since creation. Always pass `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries`.
2. **Permissions.** Headless runs `--permission-mode default` with no human to approve, so any Bash command or
   MCP tool missing from `.claude/settings.local.json` is refused mid-run. Add every new tool the same day.
3. **Browser-profile lock.** Two Chromium instances cannot share `~/.linkedin-mcp/profile`, and the MCP
   mislabels the conflict as *"Session expired or invalid"*. **The tasks therefore only do real work when no
   Claude Code session is open.** Both scripts now detect the holder and skip with an honest log line rather
   than misreporting. Proper fix (not yet built): a second profile via `--user-data-dir`, passed through a
   task-only `--mcp-config` — verify first that this doesn't drop the Notion connector.
**Also:** registering an `-AtLogOn` trigger needs admin (Access Denied without it), so the flush uses a timed
trigger instead — which is more responsive anyway. Both send tasks carry a cheap early-exit guard so idle
cycles never wake a headless Claude.
**Standing rule:** never conclude "LinkedIn auth is broken" from an MCP error message alone. Confirm with a
real tool call from a second context first. Two separate hours were lost to that false signal in one day.

### D13 addendum (2026-07-26 17:15) — the lock is worse than described, and the standing rule got ignored anyway

Failure mode 3 above understates the mechanism. It is not only "two Chromium instances": **every Claude Code
session starts its own `mcp-server-linkedin`, and they are never cleaned up.** Three servers were found
running from three sessions opened across one day (10:39, 12:58, 16:46), all contending for the single
profile. Killing the two stale ones made auth work instantly *with the cookie that had just been declared
dead*. So the trigger is not "a session is open" but "**more than one server exists**" — which accumulates
silently as the owner opens and closes windows.

**Count `python.exe` only.** Each session spawns one python server plus two uvx/uv wrapper processes, so
counting the whole tree over-reports 3× and invents a lock fight where there is none.

**The uncomfortable part:** the standing rule above was already written down, and was still ignored twice —
once by the session that recorded the 16:23 expiry as real (claiming a `--status` recovery had confirmed it),
and once by the session that then "diagnosed" it. A rule in a doc is not a control. What actually ends it is
**`tools/linkedin-doctor.cmd`**: it counts servers, prints the exact `Stop-Process` line to kill strays while
keeping the newest, and states the cookie-mtime caveat inline. Cost of the rule not being enforceable: two
unnecessary real logins by the owner, and roughly three hours across two sessions.

**The disproof that should have been reached in one minute:** a LinkedIn DM was delivered successfully at
**16:43**, twenty minutes *after* the 16:23 "expiry". An expiry cannot un-expire. When a timeline contradicts
an error message, the error message is what's wrong — look for a successful action after the claimed failure
before diagnosing anything. The owner spotted this, not the agent.

**Also corrected:** an old cookie-file mtime is **not** evidence of broken auth (that file only changes on a
real login, so an old stamp is normal and healthy), and a cluster of `invalid-state-*` folders marks
*contested access*, not a genuine expiry. Both were misread as confirming the false diagnosis.

## D14 — The owner-facing dashboard is a live-reading Artifact, not a web app

**Decision (2026-07-26):** the dashboard ([[14-send-board-dashboard]]) is a single self-contained HTML page
published as a private Artifact that **queries Notion at view time** through the runtime `mcp` capability,
rather than (a) a static page regenerated by a script or (b) a real web app with a server.
**Why:**
- **Not static:** the previous control panel hardcoded "10 jobs / 0 sent" and was wrong within a day. A
  dashboard whose numbers are written at build time is a liability — it is most confidently wrong exactly
  when the pipeline is moving fastest.
- **Not a web app:** a server means hosting, auth, and a Notion token to store. The Artifact runtime already
  brokers the viewer's own connector credentials, so the page holds **no secrets at all** and there is
  nothing to deploy or keep running.
- **Notion stays the store.** The board reads it; it never writes. Notion's own views remain the place to
  edit, which keeps D7 (Notion is the store) intact.

**Consequences accepted:**
1. A page declaring `mcp` **cannot be shared publicly** — so this is a private instrument, not a portfolio
   piece. A shareable variant would need the capability dropped and the recruiter names removed.
2. The live half is only as available as the connector; every error code therefore needs its own branch and
   its own fix copy, and the page must degrade to the snapshot half rather than looking broken.
3. Anything not in Notion (the invite tracker, the robots' health) stays a **timestamped snapshot**, labelled
   as such in the footer. Mixing live and snapshot data without saying which is which would be worse than
   either alone.

## D15 — GUI form-filling: grounding is mandatory, and the agent may never invent an answer

**Decision (2026-07-29):** the screen-control agent (`d:\New folder (2)\desktop-agent`) becomes the pipeline's
hands for job-application forms, under two non-negotiable rules — always run with `USE_GROUNDING=true`, and
never type a value that is not in `profile/application-answers.json`. Full evidence: [[16-gui-automation-investigation]].

**Why grounding is mandatory:** without it the model must guess pixel coordinates, and **every** brain tested
failed at that — 4 free OpenRouter models scored an effective **0/8** on the easiest possible GUI task, and
Claude itself missed the Start button by 328px while reasoning from convention rather than from the image.
With grounding on, the model picks a numbered UIA element and the agent clicks its real rectangle: asked to
click the File menu it returned `click_element 7`, correct first try. **Grounding beat a better model** — no
upgrade would have closed a 328px gap.

**Why the answer bank exists:** application forms ask things no CV contains (notice period, expected salary,
years per technology, visa status). A vision model that has to guess will guess, and those guesses become
false statements sent to real employers under Azam's name. So twelve fields are deliberately `null`; the
agent leaves them blank and reports them. Salary is stored as **two** figures on purpose — `8.4 LPA` for
Indian employers, `$30,000/year` for remote/international — after the owner's first answer ("70K/month
rupees, 30K$/month") turned out to differ by ~40x. That was caught before it reached a form.

**Also decided:** the agent fills but **never submits**. Submitting is irreversible and outward-facing; the
human presses the button. This matches the desktop-agent's own safety model ("unattended = do reversible,
queue risky").

**Blocked on:** the standalone `claude` CLI cannot reach the API on this machine (`ConnectionRefused`;
interactive fails identically; network, proxy, DNS and TCP all verified clean). The `claude_code` brain
therefore only works when spawned from inside a Claude Code session — useless for unattended runs. Practical
unblock: ~$10 of OpenRouter credit and `AGENT_BACKEND=openrouter`. The architecture is proven; only the model
connection is missing.

**Standing rule learned here:** never conclude "the code is broken" from a failure in one shell. The
identical call succeeded in 18.9s from a Claude-Code-spawned process and timed out at 180s from PowerShell.
Reproduce in both contexts before diagnosing — and always print **both** stdout and stderr on failure, since
Claude Code writes its errors to stdout and hiding it cost two entire runs.

---

## D16 — Applications submit with no per-send human tick (2026-07-29)

**Decision (owner's, explicit and repeated):** the form-filling step **submits**. No Slack card, no ✅,
no waiting. Owner's reasoning, in his words: a queue that waits on his laptop is not automation.

He was right. The earlier fills-never-submits design meant ten forms could sit unsent while he was away,
which defeats the point of the pipeline.

**What replaces the human tick as the safety rail:** the answer bank
(`profile/application-answers.json`) is the **only** legal source of field values. Blank beats wrong,
skip beats invent. A required field with no bank value aborts that job and moves to the next — it never
stops and waits. See [[17-auto-apply-runbook]].

## D17 — Trust, allowlists, and where local files can and cannot go (2026-07-30)

Three rules learned the expensive way in one session. See [[18-headless-trust-and-send-capability]].

**1. A scheduled task exiting 0 proves nothing.** Flush Approved looked like the one healthy runner. It
was idle — it early-exits on `nothing approved, skipping` before ever reaching `claude.exe`. Judge a
task by what its log says it *did*, never by its exit code.

**2. The allowlist is worthless until the workspace is trusted, and the project path exists twice.**
`hasTrustDialogAccepted: false` makes Claude discard **all 55** permission entries, so headless runs get
no tools and die. `~/.claude.json` holds `d:/linkdin automation` and `D:/linkdin automation` as separate
entries with independent values — headless resolves the upper-case one. Check both by exact key. An AI
cannot set this flag; the classifier blocks it on purpose, because trusting a workspace is a human act.

**3. Cloud tools cannot touch local disk; Playwright is the bridge.** Composio runs in a cloud sandbox,
so a local path passed as an attachment `s3key` returns HTTP 404, and the claude.ai Gmail connector
states plainly that draft attachments are unsupported. The working pattern is
**Playwright uploads the file locally → share it per-recipient → put that link in the email.**
General form: cloud tools for APIs, Playwright for anything involving a file on this machine.

**Corollary that keeps biting:** a note claiming something was fixed is not proof. `07-current-state.md`
said both task scripts had been moved off the UTF-16 `*>>` redirect; two of four never were. Grep for
the defect, do not trust the changelog.

## D18 — Auto-apply targets LinkedIn Easy Apply, not external ATS (2026-07-30)

**Decision (owner's):** the apply robot drives **LinkedIn Easy Apply**. External ATS becomes the
fallback, not the target.

**Why the old design was backwards.** [[17-auto-apply-runbook]] and `tools/auto-apply.ps1` were written
for Greenhouse/Lever/Ashby/Workday and contained an explicit rule: *"If a role's only route is LinkedIn
Easy Apply, skip it and log `easy-apply-only`."* But the board is populated **from LinkedIn search**, so
the overwhelming majority of rows *are* Easy Apply. The runner was built to skip precisely the thing it
existed to do. It had never submitted anything.

**And it was wired to nothing.** `pipeline_runner.py` had 17 registered actions and not one of them was
apply, so no button, task or dashboard row could reach the script. Built, documented, unreachable.
Now registered as `apply` (per-row, hidden) and `apply-all` (capped sweep), both tier `send`.

### The two facts that make Easy Apply work

Learned by hand 2026-07-29, now baked into the runbook, the prompt, and the answer bank so no future
session rediscovers them:

1. **Numeric fields reject words.** Notice period `Immediate` fails validation; type `0`. Expected CTC
   `8.4` fails; type `840000` (India) or `30000` (international). The answer bank now carries both the
   word form and the numeric form (`notice_period_days`, `expected_ctc_india_annual_inr`) because the
   one hard rule says only bank values may be typed — telling the robot to type `840000` required
   `840000` to legally exist in the bank.
2. **Fixing those reveals hidden questions.** Once the failing field validates, LinkedIn shows extra
   Yes/No questions that were not in the first snapshot. Always re-snapshot after any correction, and
   never treat the first snapshot as the whole form.

Also: Easy Apply is a **multi-step wizard**, so the loop is snapshot → fill → Next → snapshot → *verify
the step actually advanced*. Never two Nexts without a snapshot between them.

### The tailored CV is the point

LinkedIn pre-fills the résumé slot with the **last** résumé used, which is almost always the wrong
company's. The runner refuses to start without `packet.json` and its `output/pdf/<cv_stem>.pdf`, and the
runbook requires verifying the filename in a snapshot before submit. Falling back to the generic CV
would defeat the entire pipeline, so it aborts instead.

## D19 — Discovery outruns processing, so packet-building gets its own timer (2026-07-30)

`build-packet.ps1` requires a `-JobId`, so every discovered role waited for a human to click Build on its
row. Discovery ran daily; nothing consumed its output. The 2026-07-30 discovery run took the board from
24 to 62 jobs and reported it itself: **58 of 62 rows were still `New`**.

New `tools/sweep-packets.ps1` + task **"Job Hunt - Sweep Packets"** (every 6h, max 2 per cycle) drains
that queue: highest fit first, skipping anything that already has a packet. It sends nothing.

**A bug worth keeping:** the first version used a PowerShell expandable here-string, which ate the quotes
in the Python f-string. The query died with a `SyntaxError`, printed it to stdout, matched zero rows, and
the script cheerfully announced *"nothing to build"* and exited 0 — the exact failure shape D17 warns
about, reproduced within an hour of writing D17. It now prints an `OK-SWEEP-QUERY` sentinel and aborts
when it is missing. **A query that fails must never be indistinguishable from an empty queue.**
(Inside `@"..."@`, escape inner double quotes as `\"` so the C runtime hands Python a real quote.)

Related: `daily-discovery.ps1` was the only runner with **no profile-contention guard at all** — an open
Claude window did not stop it, it just made LinkedIn report "session expired" and the day's discovery came
back empty, looking exactly like "no new jobs today". Guard added.

**D19 addendum — the sweeper lied about its own output (found within the hour).** The first version
counted *attempts*, not builds. `build-packet.ps1` **exits 0 when it SKIPS** on profile contention, so
the exit code cannot distinguish a real build from a refusal, and the summary line read `built 2` when
nothing had been built. Third instance of the same failure shape in one day (D17's "exit 0 proves
nothing", D19's "SyntaxError looks like an empty queue", and now this).

Fixed: capture the child's output, match `SKIPPED:`, count separately, and report
`built N, skipped M, K were queued`. It also **breaks out of the sweep** on the first skip — contention
does not clear mid-run, so continuing just burns launches.

**The general rule, now stated three ways because it keeps costing hours:** *never infer success from a
process exiting 0.* Read what it said it did.

Incidental proof from the same run: the task's **own 21:30 trigger fired unprompted**, which is the
first independent confirmation that a newly registered trigger in this project actually works.

## D20 — The wake-from-sleep stampede, and one lock for the whole pipeline (2026-07-31)

**Symptom (owner's words):** *"the pipeline doesn't get run... the laptop is off... immediately when I open
the laptop it should run."* On 2026-07-31 the laptop slept through the entire day. Nothing ran. The Innova
pitch scheduled for 16:28 never went out.

**The catch-up was never broken.** Four of five tasks already had `StartWhenAvailable = $true`, so Windows
*did* re-run every missed task on wake — all of them, **within three seconds of each other**, at 22:01. Four
LinkedIn MCP servers came up at once and fought over one browser profile. Nothing useful happened.

So the missing piece was never "run on wake". It was **ordering**.

### Why the existing guard could not help

Every runner already checked *"is a LinkedIn MCP server running?"* and skipped if so. That check is a **race**:
at the instant five tasks launch together, no server exists yet, so all five pass, then all five start one.
A "is anyone else there?" test can never serialise anything. A lock can, because acquisition is atomic.

### `tools/pipeline-lock.ps1`

One lock for the whole pipeline. `[System.IO.File]::Open(..., CreateNew, ...)` throws if the file exists, so
exactly one runner wins and the rest stand down and wait for their next cycle. Stale locks are recoverable:
the owning PID is checked first, with age as the backstop.

### `tools/run-pipeline.ps1` + task "Job Hunt - Catch Up"

Rather than five tasks racing for one lock, a single task fires **2 minutes after the machine resumes from
sleep** (Power-Troubleshooter event 1) and runs the steps in deliberate order:
**accepts → flush → replies → discovery → packets.** Sends first, because those have deadlines; the backlog
sweep last, because it keeps. Also the manual "run everything now" entry point.

⚠️ `Register-ScheduledTask` and `-AtLogOn` both fail **Access is denied** without admin.
`schtasks /SC ONEVENT` works as a normal user. Do not "improve" it back.

### Four bugs found by testing the lock instead of assuming it

1. **`Write-Output` in a function that returns a boolean.** `Write-LockLine` wrote to the output stream, so
   the caller got `@(logline, $false)` — a two-element array, which PowerShell evaluates as **TRUE**. The lock
   answered "no" and every caller read "yes". It excluded nobody. Fixed with `Write-Host`.
2. **`catch [System.IO.IOException]` does not catch it.** PowerShell wraps a .NET method failure in a
   `MethodInvocationException`, so the typed catch was bypassed. Untyped catch now.
3. **Unreadable ≠ abandoned.** The first stale-check deleted any lock it could not parse — but a lock is
   unparseable *precisely because a live owner holds it open*. That deleted healthy locks. Now it refuses by
   default and only clears past the age threshold.
4. **Share modes must permit each other in BOTH directions.** Writer opened `FileShare::Read`, so a reader's
   `ReadAllText` (which requests `FileShare::Read`, forbidding the holder's *write* handle) threw. Result: a
   held lock was undiagnosable — no pid, no age, no owner. Fixing only the writer was not enough; the reader
   also needs `FileShare::ReadWrite`.

**The wedged-owner case, found live.** At 04:38 a reply check that started 02:12 had held the lock for 2.5
hours with its `claude.exe` child still alive. Deleting the file fails while the handle is open, so the lock
now **kills the owner's process subtree** past the age threshold. Only past 90 minutes, always logged loudly:
real runners finish in 2-10 minutes, so that long is wedged, not busy.

## D21 — Business hours are enforced at SEND time, not only at scheduling (2026-07-31)

Found by the accept-watch run itself while catching up the missed day.

`schedule_followup` picked a civilised hour **when the accept was detected**. Nothing re-checked the clock
**when sending**. So a due time that lapsed while the laptop slept stayed due forever — and since Windows
floods every missed task on wake, the next watch could fire at 02:00 and send a cold recruiter a CV pitch in
the middle of the night. Recruiter-B's 16:28 pitch was sitting due at 22:19 with a watch run in flight.

`invite_tracker.py cmd_due` now returns nothing outside 09:00-21:00 and says what it is holding:

```
Nothing sendable: 22:22 is outside business hours (09:00-21:00). 1 ripe row(s) held for morning.
```

The gate can only ever **prevent** a send, never cause one. *A guardrail written in a runbook but not in code
is an intention, not a guardrail* — the third time this project has learned that.

## D22 — Relative time words are unstable state in delayed messages (2026-08-01)

The Innova 2b opened *"I emailed you **yesterday**"*. True for the intended 2026-07-31 16:28 send. The laptop
slept through that window, so at actual send time the email was two days old — a **checkable falsehood inside
the one message whose entire job is to prove he pays attention.**

The accept-watch run caught it and refused to send, which was correct.

**Rule:** any message drafted now and sent later must use **absolute or open phrasing**. With a 3-20h
randomised delay *plus* sleep catch-up, a 2b can land a day or more after it was written. "yesterday",
"today", "this morning", "just now" are all state that silently rots.

Added to the standing pre-send check, beside no-em-dash / no-markdown / no-unresolved-slot.
Fix applied: `yesterday` → `earlier this week`.

**Scoping trap noticed while checking it:** grepping the whole packet file for em-dashes returns a dozen
hits, all in metadata and commentary. **Only the 2b block actually sends.** Scope the cleanliness check to
the message body or it fails a perfectly clean file.

## D23 — The local mirror is not the board (2026-08-01)

`sweep-packets.ps1` picks what to build from the **SQLite mirror**, but discovery writes to **Notion**. The
mirror is only refreshed when something runs `sync_board.py` against a fresh capture — and the seed file was
**six days stale** (2026-07-26).

Consequence: the mirror held **24 rows while Notion held 94**. The sweeper could not see the best work on the
board — SkillsCapital 93, Mirai Alpha 92, Infosys Junior AI Engineer 90 were all invisible to it. It was
diligently building packets for the best of a stale, tiny subset.

Refreshed by pasting the raw `notion-query-data-sources` result straight into `sync_board.py` (it accepts the
raw MCP shape on purpose, so there is no hand-translation step to get wrong): **+70 new, 24 updated**.

**The standing lesson, again:** a component that reads from a cache is only as good as whatever refreshes the
cache — and nothing was refreshing this one. Re-sync before trusting any "what should I work on next?" answer.

**Also decided:** Daily Discovery is now **DISABLED** (`Disable-ScheduledTask`). Discovery was outrunning
packet-building roughly 4:1 (94 rows, 4 packets), so more rows actively bury the good ones. Re-enable with
`Enable-ScheduledTask -TaskName 'Job Hunt - Daily Discovery'` once the backlog is under control.

## D24 — One PowerShell layer too many kills the headless Claude (2026-08-01)

**Reproduced, not guessed.** Same job, same script, same minute-ish:

| Chain | Depth | Result |
|---|---|---|
| shell → `powershell` → `build-packet.ps1` → `claude` | 2 | ✅ **SkillsCapital packet built** (16 min, ATS 90) |
| shell → `powershell` → `sweep-packets.ps1` → `powershell` → `build-packet.ps1` → `claude` | 3 | ❌ fails at ~3 min, 7/7 attempts |

SkillsCapital **failed** through the sweep and then **succeeded** run directly. Mirai Alpha failed nested
twice. So it is the extra process layer, not the job, not the data, and not transient flakiness.

**The error message lies.** It reads:

```
⚠ claude.ai connectors are disabled because ANTHROPIC_API_KEY or another auth source is set
API Error: Unable to connect to API (ConnectionRefused)
```

There is **no** `ANTHROPIC_API_KEY` (checked process, user and machine scope), no `apiKeyHelper` in any
settings file, and no env block in `.mcp.json`. Do not go hunting for a key that does not exist — this is the
same shape as the 2026-07-29 "the standalone CLI cannot reach the API" blocker in
[[16-gui-automation-investigation]], and the same standing rule applies: **never diagnose from one shell.**

### The consequence nobody had noticed

The scheduled **"Job Hunt - Sweep Packets"** task runs `Task Scheduler → powershell(sweep) → powershell(build)
→ claude` — the **same three-layer chain that fails**. So the packet sweeper has **never once built a packet
unattended**, which is exactly why the backlog never moved while every log looked plausible: the sweep found
rows, launched builds, and reported honest failures nobody read.

**Fix direction:** remove the middle layer — the sweeper must invoke `build-packet.ps1` without spawning a
second `powershell`. Until then, build packets by calling `build-packet.ps1 -JobId <id>` **directly**, which
is proven to work.

> ## ❌ D24 IS WRONG — SUPERSEDED BY D25 (2026-08-01, same day)
> The process-layer theory above is **disproven**. The middle `powershell` was removed and the builds failed
> **exactly as before**. Do not act on anything in D24. Read D25 instead. It is kept, struck, as the record
> of how a confident reproduction can still be measuring the wrong variable.

## D25 — It was a usage limit the whole time; D24 measured a clock, not a chain (2026-08-01)

**What the log actually said,** two lines into the failing build, in plain text:

```
=== build-packet 3ae29d9d-9c6e-8153-aeb3-f5a5bcaadafd  2026-08-01T12:40:24 ===
target: Mirai Alpha | AI Engineering Intern - Agentic AI & MCP Systems | fit 92
You've hit your session limit · resets 3:30pm (Asia/Calcutta)
=== end (exit 1) 2026-08-01T12:45:07 ===
```

Not auth. Not `ANTHROPIC_API_KEY`. Not process depth. A **Claude session limit**.

### Why D24's reproduction was so convincing and still wrong

The evidence was real: direct builds worked, nested builds failed, 7/7. But every direct success ran
**before** the limit was reached and every nested failure ran **after** it. Depth and time were perfectly
confounded, and depth was the variable being watched. *A reproduction only isolates the variable you
actually varied* — the SkillsCapital build "failed nested then succeeded direct" also succeeded **earlier**,
and nobody varied the clock.

### How it was settled

Ruled out by direct measurement instead of inference, testing **both** shells (the standing rule):

| Probe | From a Claude Code session | From Task Scheduler |
|---|---|---|
| `ANTHROPIC_*` / proxy env, user + machine scope | none | none |
| `claude -p` smoke, cwd = system32 | SMOKE-OK | **SMOKE-OK** |
| `claude -p` smoke, cwd = project (`.mcp.json` loads) | SMOKE-OK | **SMOKE-OK** |

Task Scheduler runs `claude` perfectly well at depth 2 **and** depth 3. There was never anything to fix
about the chain. The 17:44 sweep, run after the 15:30 reset with the spawn **restored**, built normally.

### What changed in code

`sweep-packets.ps1` now **detects the limit and names it**, instead of filing it as a per-job failure:

```
STOPPING - CLAUDE USAGE LIMIT, not a problem with <company>: You've hit your session limit ...
Nothing was built and nothing is wrong with the queue. It keeps for the next run, after the reset.
```

It also stops the sweep immediately. A quota wall will not clear mid-run, so attempting the next row only
burns a launch and libels a second good role as "FAILED" — which is how one 12:4x cycle produced *two*
bogus failures from one cause.

### The lesson, which the project had already written down and did not use

[[20-first-email-batch-and-task-verification]] says it outright: *"If every task starts failing at once with
nothing in common, check the Claude usage limit before debugging anything."* That note existed, described
this exact failure, and a day was still spent on process trees. **Cheap, boring, global explanations come
before clever structural ones** — and the log line was never scrolled to, because the summary said `failed 2`
and the summary was believed. Same family as D17: judge by the log, and then actually *read* the log.

---

## D26 — Claude Code is a tool the code calls, not the runtime (2026-08-06)

**Decision:** stop using Claude Code as the process that *runs* the pipeline. A Python program runs the
pipeline and calls Claude Code as a subprocess for the one step that needs it. Full plan: [[22-rewrite-architecture]].

**Why.** Claude Code is an interactive IDE tool. Every pipeline step currently spawns a whole session to
read a Markdown runbook and make ~20 MCP calls, most of them doing work that never varies. That one choice
produced almost every entry in this file:

| Logged as | Actually |
|---|---|
| D24 → D25 "layer too many" → "usage limit" | a coding agent has session limits; a server does not |
| D13 four MCP servers over one browser profile | an interactive tool assumes one user at one keyboard |
| D20 five tasks firing in three seconds | Task Scheduler is not a job queue |
| D17 one boolean voiding 55 permissions | a permission model built for a human approver who is present |
| 16 minutes per packet | a full agent loop for work that is mostly templating |

**The rule that replaces it:** *same every time → code; different every time → AI.* On a LinkedIn Easy Apply
form that is 19 fields of dictionary lookup and **one** question that needs a model. Today an agent does all
twenty.

**Reliability is the point, not tokens.** [[17-auto-apply-runbook]] contains *"Never invent a value. Blank
beats wrong."* That rule exists **because a model might improvise on a real employer's form.** A dict lookup
cannot improvise, so the failure mode disappears rather than being policed. Cost is the fourth-ranked benefit,
behind reliability, speed, and being able to run for someone other than the owner.

**Rejected alternative — move Claude Code to the cloud.** Fixes exactly two of the seven problems (sleeping
laptop, profile contention) and makes local files *worse*: a cloud agent cannot attach `output/pdf/<cv>.pdf`,
already learned via Composio ([[cloud-tools-cannot-touch-local-files]]). Cloud is a patch for one symptom;
the API is the fix for the class.

---

## D27 — Free models for plumbing, Claude Code for the CV (2026-08-06)

**Decision (owner's design):** route by task difficulty, not by habit.

| Task | Engine |
|---|---|
| Discovery, filling, tracking, submitting | **plain code — no AI at all** |
| Fit scoring, one odd screening question | **free model** (OpenRouter / OmniRouter) |
| Tailored CV, cover letter, ATS score | **Claude Code** ⭐ |

**Why the CV keeps a full agent.** Once per *company*, read by a *human*, not latency-sensitive, and it needs
judgment — read the JD, check `profile/` for evidence, refuse to fabricate. Low frequency + high stakes +
not urgent is exactly where a slow, careful, expensive tool belongs. Claude Code is already covered by the
owner's subscription, so **the whole design costs ₹0/day** — not "free except CVs".

⚠️ **A free model must not write the CV.** It is the single artifact a recruiter judges. The 0/8 free-model
result in [[16-gui-automation-investigation]] was about *pixel-coordinate regression*, so it does **not**
disqualify free models from screening questions — that is a much easier task and they handle it. It does
argue against trusting them where quality is visible to a human.

**Latency, measured honestly** (our own numbers: 65s/11s/9s/14s, avg ≈25s), 10 applications: today ≈2.5 h;
free ≈7 min; paid Haiku ≈3.5 min. Free vs paid is minutes. **Both are ~30× better than today — so start free.**
The win is the architecture, not the model tier.

**On OmniRouter** (rotate many free keys, fail over on rate limit): it genuinely solves free-tier **rate
limits**, which was the main objection. It does **not** solve latency, quality, or silent `no choices`
dropouts — more calls is not faster calls. ⚠️ Rotating multiple free accounts to bypass limits violates most
providers' terms: acceptable for one person's job hunt, **disqualifying as the engine of a paid product** —
the same reasoning as D2 on LinkedIn scraping.

---

## D28 — One `llm.py`, so the provider is a config value (2026-08-06)

**Decision:** every model call in the codebase goes through a single `ask()` function. The provider, base
URL, and model name live in `.env`.

**Why.** Free-vs-paid then stops being an architecture decision and becomes one line, so it can be deferred
and revisited without touching `discover.py`, `fill.py`, or anything else. It also gives exactly one place to
put the guards we already paid for:

- `if not r.choices: raise` — free providers returned empty responses on 2026-07-29 and the crash printed nothing
- usage-limit detection on the Claude Code path — stop the batch and name the cause, never file it as a
  per-job `FAILED` (D25)
- one retry/backoff policy, one timeout, one log line per call

**Consequence for the product plan:** the same code runs on free keys for the owner today and on paid keys
for users later. Nothing in the pipeline knows or cares which is in use.

---

## D29 — A mirror can be WRONG, not merely stale, and wrong is undetectable without comparison (2026-08-06)

**What happened.** Before the first Phase 0 run, the SQLite mirror was re-synced against Notion. Three rows
disagreed. One mattered enormously:

| Row | Mirror said | Notion said |
|---|---|---|
| **SkillsCapital — Software Engineer Intern, fit 93** | `Applied` | `Invite sent` |
| Mirai Alpha, fit 92 | `Skipped` | `Invite sent` |
| Hired, fit 62 | `Skipped` | `Invite sent` |

**The single best row on the board had been carrying a false `Applied` flag since 2026-08-01.** It was never
applied to. Every status filter — `sweep-packets`, the dashboard, and the brand-new `board_candidates()`
written that same morning — correctly excluded it, for a reason that was false. The row Azam's own `CLAUDE.md`
flags as *"apply this week, cannot wait"* was invisible to the entire pipeline, and the pipeline was working
exactly as designed.

**Why this is not D23.** D23 said the mirror goes **stale**: it held 24 rows against Notion's 94, and the
missing rows were simply absent. That is detectable from one side — compare `sync_log.synced_at` to now, or
count rows, and staleness announces itself.

**Wrong announces nothing.** The row was present, recently touched, well-formed, and plausible. Nothing about
the mirror in isolation could reveal it. A timestamp check passes. A row count passes. Only a
**field-by-field comparison against the source of truth** finds it — which nothing was doing.

> **Stale is detectable from one side. Wrong is only detectable by comparison.**

**Probable origin:** a status write that landed locally and was never pushed, or was pushed and rejected, with
no reconciliation afterwards. Two writers, one truth, no arbiter — the structural flaw, not the specific bad
value.

**What catches it next time**

1. **Phase 1 removes the class.** Own the data: one database is authoritative and Notion becomes a *view*.
   Two writers with no arbiter is the actual bug; re-syncing is a treatment, not a cure.
2. **Until then, reconcile before trusting a status filter.** Any run that *excludes* rows on status must
   first diff against Notion and print what changed. Cheap, and it was how this was found at all.
3. **Log every correction loudly.** The re-sync printed `status 'Applied' -> 'Invite sent'` per row. That one
   line is what turned a silent 5-day hole into a finding.
4. **Treat a terminal status as the highest-risk value in the store.** `Applied` and `Skipped` are the only
   values that cause a row to be *ignored forever*. A false `New` costs one wasted look; a false `Applied`
   costs the job. Verify terminal statuses against the source, not the mirror.

**The wider lesson, consistent with D17 and D25:** the failure was silent and every log looked plausible. Ask
not "did anything error?" but "**what would this look like if it were quietly wrong?**" — and then go and
compare. Here, the answer had been sitting in Notion for five days.

Related: [[23-phase-0-results]] · D23 (the stale mirror) · D17 (judge by the log, not the exit code)

---

## D30 — A metric that cannot tell "nothing wrong" from "nothing observed" is not a metric (2026-08-06)

**Two instances in one day, on the same code, hours apart. Both read as clean. Both were blind.**

| # | What it printed | What was true |
|---|---|---|
| 1 | `VERDICT: PASS` for 5 jobs | 3 of them did nothing at all — `filled=0`, `steps=1`, out in ~4s |
| 2 | `blank=0` on Energy Exemplar | **every** `<fieldset>` question was invisible to the scanner |

The second is the more instructive. `filled=6, blank=0` reads as a clean sweep: six answered,
nothing missed. In fact all six were plain `<input>` elements, and every grouped question — the
Yes/No radios and the required consent checkbox — had been skipped by `if not label: continue`
because `inner_text()` does not return LinkedIn's accessible-only `<legend>`. Nothing was filled.
Nothing was reported. **`blank=0` did not mean "nothing was missed"; it meant "nothing was seen".**

A blank in a report is a *claim about an observation*. If the observation never happened, the
report is not merely incomplete — it is confidently wrong, and it points away from the bug. Both
times, the number that should have raised the alarm was the number that suppressed it.

### The rule

> **Every count needs a denominator it did not choose for itself.**

`filled=7` says nothing. `filled=7 of 9 controls seen, 9 of 9 present` says three separate things,
and any of them going wrong is now visible. A zero is only trustworthy when the thing producing it
can demonstrate it was able to count — so report the population alongside the tally, and take the
population from a *different* mechanism than the one being measured. Here: the raw
`modal.locator("fieldset").count()` is independent of whether labelling worked, and one line of it
in the debug dump is what finally exposed the bug after two wrong theories.

Three concrete forms this takes in the code now:

1. **Verdicts exclude no-ops and name them.** `report()` counts only jobs that reached
   Review/Submit, prints the ones that did nothing, and labels a partial run `INCOMPLETE SAMPLE`
   with a projection rather than a pass.
2. **Nothing is skipped silently.** An unlabelled control is reported as
   `(unlabelled <tag>, required=<bool>)`. Noisy beats invisible — a noisy report gets read, a
   silent one gets trusted.
3. **Actions are verified, not assumed.** `_fill_group` returns `is_checked()`, not "I clicked".
   Reporting a tick that did not land is the same lie in miniature.

**Relationship to D17.** D17 says judge by the log, not the exit code. D30 is the next layer: the
log can lie too, when its counters cannot distinguish absence from success. Ask of every green
number: *what would this read if the check never ran?* If the answer is "the same", it is not
evidence.

### Corollary — a fail-safe that works by accident is not a fail-safe

Found the same day. The question *"Do you have hands-on experience with MLOps and cloud platforms
(Azure ML, AWS SageMaker, GCP), including ... **Docker/Kubernetes** ...?"* matched the
`years_with_docker` spec on the bare word "docker", and tried to answer **"2"**.

It came out blank, which looks like the "blank beats wrong" rule working. It was not. It was blank
**only because no radio option happens to read "2"**. Presented as a text input — which the same
question is, on other forms — it would have typed `2` into a yes/no question on a real employer's
form, and the mapping would have looked correct in every log.

Fixed with `Spec.requires`: a `years_*` spec must also match a quantity cue
(`how many|how much|how long|years|months|duration`). A skill name in a label does not make the
question a quantity question.

> **When something dangerous does not happen, establish whether that was the design or the
> circumstances.** "It failed safe" is a claim requiring the same evidence as "it worked".

Related: [[23-phase-0-results]] §1, §3b, §3c · D17 (judge by the log) · D25 (read the child's log) ·
D29 (stale vs wrong)
