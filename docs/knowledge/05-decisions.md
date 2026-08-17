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

### Third instance, hours later, in the code written to honour D25

`cv.py`'s first real run built the Energy Exemplar packet **completely** — `packet.json`, a 105 KB
tailored PDF, four outreach documents — and Claude Code hit its session limit *immediately after
finishing*. `cv.py` checked the limit string **before** looking for the artifact, so it raised
`UsageLimitHit` and reported the job as untouched while the finished work sat on disk.

The bug was in the D25 port itself. D25 says *a usage limit is not a job failure*; the
over-correction was to let a **message in a log** outrank a **file on disk**. Both rules are
needed, and their order matters:

> **Check the artifact first. Only when there is no artifact does the log get to explain why.**

`build_packet` now returns the completed packet carrying a `limit_notice`, so the batch still stops
(the next job *would* fail) without disowning work that demonstrably succeeded.

Note how it was caught: the run printed `** STOPPED: Claude usage limit ... 1 job(s) untouched`
while `ls` showed the PDF. **The report and the filesystem disagreed, and the filesystem was
right.** That is the whole of D30 in one line.

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

---

## D31 — An over-broad pattern is as dangerous as an invented value, and much harder to catch (2026-08-10)

**Decision:** every answer-bank pattern is anchored to the shape of the question it answers, and every
pattern that has ever mis-fired keeps a regression test written from the **real form text** that broke it.

**What happened.** The `city` spec contained a bare `\blocation\b`. On a real EXL form it matched:

> *"Have you ever appeared for an Interview at any Exl **location** during the last 90 days?
> If 'Yes' then please mention the date"*

and typed **"Srinagar"**.

**Why this is the worst bug the project has produced.** The one hard rule is *only values from the answer
bank go into a real employer's form* — the rule that exists to prevent exactly this harm. Srinagar **is**
in the answer bank. The guard passed it. Every log line was green. A false statement went out under Azam's
real name with the entire safety system reporting success.

An invented value is caught by a provenance check. **A correct value in the wrong field is caught by
nothing** — provenance is intact, the answer is truthful in isolation, and only reading the question tells
you it is wrong. The failure is in the *mapping*, and nothing in the pipeline was validating the mapping.

**The rule that follows:**

> The answer bank guarantees **where a value came from**. It guarantees nothing about **where it went**.
> Those are two different safety properties and only the first one was ever implemented.

**What changed:**
- All `city` patterns anchored: `^city\b`, `^location\b`, `your (current )?location`, `city of residence`,
  `where are you (currently )?(located|based)`.
- Nine regression tests in `tests/test_families.py`, each one a verbatim question from a real form,
  asserting it does **not** match `city`.
- `Spec.requires` (see D30's corollary) so a skill name cannot make a question a quantity question.

**How to obey it:** when adding a pattern, do not ask *"does this match the question I have in mind?"*
Ask *"what else in a job form contains this word?"* `location` appears in interview-location, client-site,
shift-preference and office-preference questions. So does `experience`, `available`, `notice`, `current`.
A bare noun is almost never a safe pattern.

Related: D30 (a metric that cannot see) · [[26-apply-at-volume]] §3.4 · [[17-auto-apply-runbook]]

---

## D32 — Volume without the research half is the exact failure this project was built to avoid (2026-08-10)

**Decision:** an application is not "sent" until a **named human** knows it exists. The batch runner's
output is a *queue entry*, not an application, and it will not be counted as one.

**What happened.** Eight LinkedIn Easy Apply submissions went out across 08-09 and 08-10 using role-family
CVs. Asked directly whether the people behind those forms had been researched and contacted:

- **Energy Exemplar** — packet, recruiter identified, outreach drafted, **never sent**
- **SkillsCapital ×3** — packet exists but for a *different role* (the Intern req)
- **Crossing Hurdles ×2, Neurones IT Asia, Celigo** — no packet, no contact, no outreach, nothing

Five of eight reached an ATS queue with no human aware of them. Thirteen applications total across both
channels; **zero replies.**

**Why it happened, and why it is not a bug.** Every component did what it was written to do. The failure is
that the *fast* half of the pipeline was built and run without the *slow* half. `families.py` and
`apply-all` made applying nearly free, and free made volume feel like progress. The runbooks
([[15-build-packet-runbook]], `recruiter-outreach`) already define the other half; nothing wired them into
the batch, and nothing noticed, because the batch's success metric is *forms submitted*.

**The rule that follows:**

> **Cheap × many is the mass-automation shape this project's north star explicitly rejects.**
> Making a step cheap does not make it correct — it removes the cost that used to force the
> question *"is this worth sending?"*

Note the symmetry with D26. That decision made the machine fast. This one records what fast is worth on its
own: thirteen applications, zero replies, and the one channel that has never been tried at volume is the
one the project was designed around.

**What changes:** the batch runner keeps running, but a submitted row is now *unfinished work* — it enters
a follow-up queue for recruiter identification and a short note. The metric moves from **forms submitted**
to **humans contacted**.

Related: D8 (warm insider first) · D12 (two-stage outreach) · [[26-apply-at-volume]] §4 ·
[[01-vision-and-goals]]

---

## D33 — A lifetime, channel-blind company cap locks out the best row on the board (2026-08-10)

**Decision (pending implementation):** the one-role-per-company cap must be scoped to **channel and
recency**, not to the whole history of contact with that employer.

**What happened.** After three SkillsCapital applications went out inside ten minutes, `apply-all` gained
`--max-per-company` (default 1), counted across the ledger as well as the current run. Correct fix, too
blunt an implementation: it counts **every ledger row for that company regardless of channel or age**.

Infosys has exactly one ledger entry — a **LinkedIn DM** about *AI Application Engineer*. That single old
message now permanently blocks all four Infosys rows, including:

> **Infosys · Junior AI Engineer — fit 90.** The highest-value row in the project. Recruiter-A is inside
> the company and already a 1st-degree connection, so no accept has to be waited for. A *Junior*-titled AI
> req is the rare shape that fits a final-year student.

It has been named the top Track A action in [[07-current-state]] for ten days, and the tool built to apply
to it silently refuses to — reporting `already applying to 1 role(s) at this company this run`, which is
false on both counts: not this run, and not an application.

**The second-order effect** is the "why is it only applying to fit 80-82 rows?" puzzle logged on 08-09 and
08-10. It is not a broken scorer. SkillsCapital (93) is correctly ledger-blocked; Infosys (90, ×4) is
wrongly cap-blocked; so the plan's real ceiling is **85** and everything above it is invisible. A
diagnosis was written twice against a symptom whose cause was one `sum()` in the planner.

**The rule that follows:**

> A safety cap is a filter on the *best* candidates as much as the worst. When a guard starts refusing
> work, read what it refused before trusting that it was right — and make its skip reason state the
> **actual** condition, because `this run` sent the last two investigations down the wrong path.

**The fix:** count only submissions on the same channel within a recency window (e.g. no second Easy Apply
to one company within 14 days). A DM sent weeks ago about a different role is not a reason to skip a
better-fitting job today.

Related: D23/D29 (the store that lied) · D30 (a plausible message over a real fact) ·
[[26-apply-at-volume]] §5

---

## D34 — Outreach is per company; a CV is per role. The packet layout conflates them (2026-08-10)

**Decision (pending implementation):** split the packet. `output/outreach/<company>/` keeps the
recruiter contact and the messages, which genuinely are per company (D8: messaging the same recruiter
twice is the fastest way to look automated). The **CV** must be addressable per role, because a CV
tailored to one req must never be attached to another.

**What happened.** `build_packet` refused twice, and the refusal is correct both times:

- 2026-08-09, Infosys **AI/ML Engineer** — reported FAIL forever
- 2026-08-10, Infosys **Junior AI Engineer** (fit 90) — the best row on the board

The runbook builds one packet per **company** and will not overwrite. `find_packet` looks up by **job
id**. For a company's second role those two can never agree: Claude refuses to build, `cv.py` sees no
packet for that job id, and the job is unbuildable in perpetuity. Infosys has **five** rows on the
board; SkillsCapital has four and hit the same wall from the other direction — its packet is for the
Intern req while three *different* SkillsCapital roles were submitted with a family CV.

**Why the guard is still right.** `find_company_packet()` at least makes the collision *visible*: it
fails in 0.345s with an explanation instead of burning ~7 minutes of a session-limited resource on a
build guaranteed to be refused. That is D30 applied — a fast honest refusal beats a slow plausible one.
But a clear error is not a fix, and this one has been logged twice without the underlying shape changing.

**The rule that follows:**

> **Check that your storage key matches your unit of work.** Packets are keyed by company because
> *outreach* is per company. But the artifact inside them, the CV, is per **role**. One directory
> holding two different units of work means the second one is unreachable, and the failure looks like a
> tool bug rather than a schema mistake.

**RESOLVED 2026-08-11.** Implemented as designed, not as the interim workaround:

- `cv.packet_dir_for(company, role)` — the **first** role keeps the plain company folder, so nothing
  already on disk moves; every later role gets `<company>--<role>`.
- `cv.find_role_packet(company, role)` — lookup by **company + role**, not job id, so the board row id
  and the packet's recorded id no longer have to agree.
- `build_packet` passes the target folder to Claude and instructs it to **reuse the company's existing
  `contact.md`** — D8 stays intact (one recruiter per company) while the CV becomes per role.
- `families.pick_cv` also checks by company+role. Without that a genuinely tailored CV would silently
  lose to the family CV, which is the "fast and generic" outcome [[24-cv-bridge]] exists to prevent.
- [[15-build-packet-runbook]] §2 and §3 updated to match; the agent side and the code side now agree.

Two traps found while building it, both worth keeping:

1. **Folder slug is not a comparison key.** `slugify` gives `skillscapital` and `skills-capital` for the
   same employer. Matching on that would miss a tailored CV and quietly attach the family one, so
   comparison uses an alphanumeric-only `_key()` — the same normalisation the ledger uses, for the same
   reason.
2. **A corrupt `packet.json` must route the new role to its OWN folder**, never to the occupied one.
   Guessing "probably the same role" on unreadable JSON would overwrite approved drafts.

Unblocks 9 board rows: Infosys ×5 (including Junior AI Engineer, 90) and SkillsCapital ×4. 98 tests.

Related: D8 (one contact per company) · D30 (fail fast and explain) · [[15-build-packet-runbook]] ·
[[24-cv-bridge]] · [[26-apply-at-volume]] §5

---

## D35 — Eight reply checks reported "zero replies" about a channel none of them could see (2026-08-10)

**Decision:** the reply check reads the **LinkedIn inbox** as well as Gmail, in code
(`apps/autopilot/replies.py`), and an inbox it could not read is reported as *unread*, never as empty.

**What happened.** On **2026-07-26 at 18:58**, two hours after being pitched, the warm Infosys
insider replied:

> *"[phone number] / Send ur cv on this number / Wa Alaikum As Salam"*

He gave his phone number and asked for the CV. **Nobody answered for fifteen days.**

Across that window, **eight consecutive reply-check runs reported "zero recruiter replies"**. Every
one of them was honest about the only place it looked: Gmail. The runbook
([[11-reply-classifier-runbook]]) searches mail domains harvested from `contact.md`. **Nothing in
this project had ever opened LinkedIn messaging.**

So the reply was not *missed*. It was **unobservable** — and the output of "looked everywhere, found
nothing" is byte-identical to "looked in one place, found nothing there".

**Why this one is worse than the earlier instances of D30.** The previous cases cost time. This one
cost the single warmest lead in the project: a 1st-degree insider at the highest-fit company, who
volunteered a phone number. He was not slow to respond. **He responded in two hours and we did not.**

It also silently corrupted every downstream decision. "13 applications, 0 replies" was the number
that drove the whole 2026-08-10 session — the reordering of Track A, D32, the argument against
adding more platforms. That number was **wrong**, and it was wrong in the direction that made the
outreach channel look useless when it had in fact worked on the first try.

**The rule that follows:**

> **A channel you do not read is not a quiet channel.** Before believing any "no results", enumerate
> the places the check actually looked and compare that list to the places a result could arrive.
> Coverage is a property of the *checker*, and it is invisible in the checker's own output.

**What changed:**
- `apps/autopilot/replies.py` reads the LinkedIn conversation list directly through the existing
  Playwright profile. Detection: LinkedIn prefixes the preview with `You:` when we spoke last.
- **It fails loud in both unclear directions.** An empty preview, an unfamiliar shape, or a locale
  we have not seen is escalated to the WAITING pile rather than dropped. False positive costs ten
  seconds of reading; a false negative already cost fifteen days.
- A read error prints `COULD NOT READ THE INBOX ... This is NOT 'no replies'` and exits 2, so a
  failure can never render as an empty inbox.
- The classifier is a pure function, so it is unit-tested — the previous check was an agent reading
  markdown, whose logic could not be tested at all. That is a second argument for D26 nobody had
  made: **a runbook cannot have a regression test.**

**Verified against the live inbox on 2026-08-10:** 6 conversations scanned, the missed reply
flagged, and the two threads where we genuinely spoke last correctly left alone.

Related: D30 (nothing wrong vs nothing observed) · D26 (runbook to code) ·
[[11-reply-classifier-runbook]] · [[campus-channel-is-invisible]] (the same defect, different channel)

---

## D36 — Screen the row before it spends an application slot; only evidence may block (2026-08-10)

**Decision:** `apps/autopilot/sourcing.py` screens every candidate before it enters the plan.
**Heuristics may only DEPRIORITIZE. Only recorded evidence may BLOCK.**

**What happened.** Two of the eight Easy Apply submissions went to **Crossing Hurdles**, a company
with **zero employees findable on LinkedIn**. Both produced a `notifications@ceipalmail.com` auto-ack
within three seconds, first person, funnelling to `jobs.micro1.ai` with a referral code. It is a
lead-magnet req with no hiring manager behind it, so neither application could ever be followed up —
and D32 says an application that reaches no human is unfinished work.

Running the new screen over all 94 board rows immediately found a **third** Crossing Hurdles row —
*Platform Engineer, fit 83, status `New`* — queued and unapplied. That was the next slot about to go
the same way.

**The asymmetry, and why it is the OPPOSITE of D35's.**

`replies.py` escalates anything it cannot classify, because a false alarm costs ten seconds and a
false silence cost fifteen days. This module leans the other way:

| | cost |
|---|---|
| false positive — blocking a real company | **a job opportunity. Unrecoverable.** |
| false negative — letting a shell through | one application slot, about fifteen seconds |

A missed opportunity is strictly worse than a wasted slot, so the screen is **conservative about
blocking**. A `$60/hr` in the title is a staffing-marketplace convention and a genuine tell — but a
real employer can post an hourly contract rate, so that tell sends the row to the **back of the
queue**, never out of it. A deprioritized row is still applied to.

**The rule that follows:**

> **Decide which direction a check should fail BEFORE writing it, and write the reason down.**
> Two guards in the same codebase can need opposite defaults, and "be safe" is not a direction —
> safe for whom, against which cost? A guard whose failure direction was never chosen has one
> anyway, by accident.

**What changed:**
- `screen(company, role)` returns `apply` / `deprioritize` / `block` with a reason.
- `record_unreachable()` **refuses an empty evidence string** — a company cannot be blocked by
  assertion, only by something someone can read and check.
- A corrupt or missing evidence file blocks **nobody**, loudly (`NOTHING is being blocked`) — failing
  toward applying, per the asymmetry above.
- Deprioritized rows are appended to the end of the plan and re-checked against the company cap, so
  they cannot sneak past a limit the main loop already enforced.

Related: D32 (an application that reaches no human is unfinished) · D35 (the opposite asymmetry) ·
[[26-apply-at-volume]] §6

---

## D37-D40 — the LinkedIn Content Engine's design decisions (2026-08-10)

Recorded in full in [[27-linkedin-content-engine]]. Registered here because **this file is the single
numbering authority**, and these four were originally written as D33-D36 — numbers already taken by
four unrelated decisions on the same day, from a parallel session. A duplicate decision number makes
every future `D33` reference ambiguous forever, which is why they were renumbered rather than left.

- **D37 — SQLite over Notion as the content store.** Notion is only reachable through MCP during an
  active agent session; the content hub must work offline from a scheduled task. Same reasoning that
  produced `board_db.py`, and the same reasoning as D23/D29 about not depending on a remote store.
- **D38 — agent-agnostic pipeline.** Claude and Antigravity share `.mcp.json`, the Playwright profile,
  `output/` and `tools/*.py`; the database is the shared state, so either can log, draft, approve
  and dispatch.
- **D39 — human approval before posting.** The dispatcher only posts `status='approved'`, and does
  nothing when nothing is approved. Same gate as outreach.
- **D40 — every post gets a visual**, with a 3-engine fallback chain and a cached safety net.

> **Process note:** two sessions on one day both reached for "the next decision number" and collided.
> The register is append-only and has no allocator, so concurrent writers cannot see each other's
> claim. Cheap mitigation: **grep `^## D` here before numbering anything.**

---

## D41 — Count the applications that reached nobody, on every run (2026-08-10)

**Decision:** `apps/autopilot/coverage.py` reports, every reply-check run, how many applications have
reached a **named human** and how many are sitting in a queue alone. It **does not** search LinkedIn
and **does not** send invites.

**Why the report and not the automation.** The obvious build was "for each application, find a
recruiter and send a connection request". That is the automated-connection-request pattern LinkedIn
restricts accounts for, and it is the red line in this project's own north star. The approved path
already exists (D12): a Slack card, a human taps the tick, `flush-approved` sends a *bare* invite.

So the split is deliberate:

| step | who | why |
|---|---|---|
| decide which applications lack a human | **code** | deterministic, testable, zero account risk |
| find the recruiter | an agent, read-only MCP search | judgement, and it is a read |
| approve the invite | **the human** | D12; this is the ban-sensitive action |

Automating the last step would trade the account for a few minutes. The measurement was the missing
piece, not the sending.

**What it found on its first run:** **Recro**, applied 2026-07-29 — **twelve days silent, no human
ever identified.** It was the very first Easy Apply and was missed by every audit since, including
this morning's, which only examined the eight recent submissions.

**Two design details that matter:**

- **Over-reporting coverage hides a gap**, so coverage requires a *positive* signal and anything
  ambiguous counts as uncovered. A `contact.md` whose content says *"NO CONTACT FINDABLE"* is
  explicitly **not** coverage — treating file existence as the signal would have marked Crossing
  Hurdles, the company that proved the whole problem, as solved.
- **A recorded dead end is not an outstanding task.** Companies in `sourcing.py`'s unreachable list
  are excluded, because a report that lists the same impossible item forever trains its reader to
  skim it, and that is how the next real gap gets missed.

**A bug worth keeping, found by a test that had been passing for the wrong reason.** Three tests
passed because `companies_with_a_named_human(outreach_dir=OUTREACH_DIR)` evaluates its default
**once, at import**, freezing the module constant — so monkeypatching the module attribute did
nothing and the function kept reading the real folder. Only the fourth case disagreed loudly enough
to expose it.

> **A green test proves the assertion held, not that the code under test was the code you meant.**
> When several tests pass and one fails, suspect the passing ones first: they may share the failing
> one's cause and be hiding it.

Related: D32 (an application that reaches no human is unfinished) · D12 (the approved send path) ·
D36 (dead ends) · D30 (nothing wrong vs nothing observed)

---

## D42 — Free models are a launcher, not an environment variable (2026-08-13)

**Decision:** OmniRoute fronts the **high-frequency, machine-read** work (`apps/autopilot/llm.py`
fit scoring, the one odd screening question). Claude Code keeps the **subscription by default**,
and the free path is entered by an explicit command — `claude-free.cmd`, wrapping
`omniroute launch` — never by a global `ANTHROPIC_BASE_URL`.

**Why not just set the env var.** Because it is not scoped to the session the owner is thinking
about. `ANTHROPIC_BASE_URL` reroutes *every* Claude Code invocation, and one of those is
`cv.py`'s headless packet build — the tailored CV, the single artifact in this project a human
reads, kept on a full agent deliberately (D26/D27). The saving is a few free tokens; the cost is
a recruiter receiving a CV written by whichever free model happened to win the fallback chain,
with nothing in any log marking the difference.

> **A global switch cannot express a per-purpose decision.** D26 split the work by stakes —
> plumbing to free models, the human-read artifact to Claude Code. An env var applies to all of
> it at once, silently undoing the split the architecture is built on.

So the launcher does three things a bare env var cannot: it refuses to start against a dead
gateway, it **warns if the default was already rerouted** (`~/.claude/settings.json` or a
persisted User/Machine var — meaning the CV engine is silently no longer Opus 5), and it prints
a banner naming the engine. The third guards the likeliest failure: the owner forgetting which
window he is in.

**What this does not change.** D26's terms finding stands unaltered — pooling free keys to clear
rate limits violates most providers' terms, which is fine for one person's job hunt and
disqualifying for a paid product (same shape as D2). OmniRoute turning out to be well built is
not an argument that the pooling became legitimate.

**The corollary, found the same day.** Capsule Hub was requested in the same breath and **cannot**
be integrated: it is a browser extension plus a **web** SDK whose entire API is DOM
(`initDropZone('#chat-input')`, `bin: none`, no MCP, no API). Its long supported-platforms list —
including Antigravity and VS Code — is real *because those are Electron apps rendering HTML*. A
terminal has no DOM to inject into.

> **A supported-platforms list names surfaces the vendor can reach, not capabilities you can
> call.** Look for a CLI entry point, an API, or a file format before reading a name on that list
> as an integration.

**Measured the same day, and it changes how the gateway may be used.** OmniRoute silently
**drops the first token of every non-streamed answer** — `HELLO WORLD` comes back `WORLD`,
on both wire formats, reproduced across three providers. HTTP 200, well-formed JSON, no
symptom. `llm.py` now always streams and joins; `tests/test_llm_streaming.py` fails if
anyone restores the non-streaming call. And `auto/*` routes to a different provider each
call with different correctness, so the autopilot must **pin** a model that passes
`tools/omniroute_canary.py`.

> **A round trip that returns *something* is not a round trip that returns *your answer*.**
> Echo a known multi-token string and compare exactly. A smoke test asserting 200-and-not-empty
> passes this bug, and a single-token reply (`4`) survives it — which is how it hides.

⚠️ Still unproven: `claude-free.cmd`'s final exec into an interactive session. Claude Code
streams by default so it should be on the correct path, but that is inference, not a
measurement (D30).

Full mechanics, including the `/v1`-suffix trap that differs between the two callers:
[[29-omniroute-gateway]]

Related: D26/D27 (free for plumbing, Claude Code for the CV) · D2 (the terms line) ·
D30 (nothing wrong vs nothing observed) · [[24-cv-bridge]]

---

## D43 — The fallback must be a different road, not a wider lane on the same one (2026-08-14)

**Context.** D42 pinned `gemini/gemini-3.5-flash-lite` through OmniRoute and listed
`gemini/gemini-3.6-flash` and `felo/felo-chat` as fallbacks. Asked to "connect all the
free providers", this session connected three more (`opencode`, `mimocode`, `auggie`),
taking the catalog **665 → 1019 models**, then echo-tested 23 models spanning every free
family.

**Three answered.** Two Gemini and `felo/felo-chat`. Everything else returned 401
(`pollinations`, 250 models), 402/429 (`g4f-*`), 403 (`oc/*` 92 models incl. an advertised
`claude-opus-5`, `tllm/*` 26), 502 (`aug/*` 28), 418/429 (`ddgw/*`), or an empty stream.

> **1019 models. Three that work.** Every one of the three is backed by a real API key on
> a real account. The free-and-anonymous tier is uniformly rate-limited, paywalled or
> blocked — connecting 200 more of them buys catalog entries, not capacity.

**The decision.** The autopilot's fallback is now **Groq reached directly**
(`api.groq.com`, no gateway), configured as `LLM_FALLBACK_*` in `.env`. Not another
OmniRoute model.

**Why the old fallback list was not a fallback.** OmniRoute is a *local npm process on
:20128*. When the laptop sleeps (which it did for an entire day — D20), the process dies,
or the gateway wedges, **every model behind it dies together** — the Gemini primary and
both its listed fallbacks. Three names on one process is one point of failure with three
labels on it. `llm.py` now tries the primary, then a genuinely separate road, and raises
loudly naming both if neither answers. 8 new tests; 112 total.

### ⚠️ The gateway is what breaks Groq — the key was always fine

Groq's connection reported `testStatus: "active"` and 403'd every completion. The chain of
wrong conclusions this invites is the point:

| Step | What it looked like | What it was |
|---|---|---|
| OmniRoute 403 | bad Groq key | key is valid |
| `lastError` cites **Cloudflare** | Groq blocking us | Cloudflare blocking a *client fingerprint* |
| Python `urllib` 403, `curl` 200 | TLS fingerprinting | the **`User-Agent` string**: `Python-urllib` is banned, any normal UA passes |
| custom-UA provider node: `/models` **works** | fixed | `POST /chat/completions` still 403 — the fix reached one path, not the other |
| `openai` client **direct** | should need the UA too | exact answer in **both** transports, default UA, no gateway |

So the same key is simultaneously dead through the gateway and perfect without it. Chasing
the UA was reasonable and wrong; the variable that mattered was **whether OmniRoute was in
the path at all**. *When a credential fails in one client and works in another, the
credential is not the variable — stop tuning it and change the client.*

### ⚠️ `testStatus: "active"` is a green light for the wrong question

`groq` and `opencode` both report **active** while 403'ing every single inference call. The
dashboard tests that a *connection* can be established, never that a *completion* comes
back. This is D30's disease in the vendor's own UI: a metric that reports success for
something nobody asked about. **Only `tools/omniroute_canary.py` — an exact multi-token
echo — is evidence.** Read the artifact, never the status field.

### Not done, on purpose

- **Multi-key Gemini rotation.** His account holds 7 keys, but they span only **5 projects**
  and Google meters the free tier **per project, not per key** — so it was 5×, not 7×. And
  the autopilot makes tens of calls a day against ~1000/project/day: **quota was never the
  binding constraint.** A multiplier on a resource that is not scarce is not a win.
  (Cost of learning this: a `navigator.clipboard.readText()` call hung the Playwright MCP
  for 74 minutes. **Do not read the clipboard through that server.**)
- **The 31 `web-cookie` providers** (ChatGPT, Perplexity, Copilot, Qwen, Kimi…) run off
  session cookies harvested from a logged-in browser. Approved by the owner but **not done
  unattended**: using a web session as an API breaks those services' terms and risks the
  accounts, `claude-web` most of all — losing that account kills the CV engine (D26/D27),
  which is the one thing this project cannot replace. Real frontier models, but the
  autopilot only needs fit-scoring and the odd screening question, which Gemini already
  does in ~5 s. **Low marginal value against an unrecoverable downside.** Left for a
  supervised session.

### 🔴 The canary failed the working fallback — the instrument had the bug

The most valuable ten minutes here. With Groq direct **proven working from `llm.py`**,
`tools/omniroute_canary.py` was pointed at the same endpoint with the same key and
returned **FAIL, 403, all three models, both transports.**

The canary speaks `urllib`. `llm.py` speaks the `openai` client. urllib's default
`User-Agent` is `Python-urllib/3.x` — **the one string Groq's Cloudflare bans.** Every
other UA tested passes, including `curl/8.5.0` and a made-up `omniroute-canary/1.0`. The
provider was perfect; the measuring instrument was banned.

> **A canary that fails a working provider is exactly as dangerous as one that passes a
> broken one.** This one would have argued for deleting a fallback that works — and the
> argument would have looked rigorous, with three models and six probes of evidence.

This file already warned that *"a canary that tests a different path than production
certifies the wrong thing"* — written about streaming vs non-streaming. The path is wider
than the transport: **the HTTP client's own default headers are part of it.** `USER_AGENT`
is now set unconditionally in the canary, with the reason attached so nobody tidies it away.

Second-order point: this session's *screening* script also used urllib, but only ever
talked to `localhost:20128`, so it was never exposed. The bug needed a **direct** provider
call to appear — which only existed because the fallback stopped going through the gateway.
*Removing a layer can expose a defect the layer was hiding.*

Related: D42 (the gateway, the streaming bug) · D26/D27 (free for plumbing, Claude Code for
the CV) · D30 (nothing observed is not nothing wrong) · [[29-omniroute-gateway]]

---

## D44 — The follow-up engine was finished, correct, and fed by nothing (2026-08-14)

**Found by reading the LinkedIn inbox** (see D43's session): Swaleha Pathan and Saksham
Sandhu were both pitched on **2026-08-01**, and in both threads the last message is **Azam's
own**. Thirteen days, no nudge. The design promises Day-3 and Day-7 follow-ups.

`tools/followups.py` is not broken. It computes the cadence correctly and has since the
completion plan. Its docstring says exactly why it reads JSON on stdin:

> *"there is no Notion token in .env ... The runner (Claude via MCP, or a future scheduler
> with a token) queries Notion for Status='Applied' jobs and pipes them in."*

**That runner no longer exists.** `NOTION_TOKEN` was never set, and the store moved to
`database/board.sqlite3`. So the engine has **never once been fed**, by anything, ever.

> **A component with no caller does not fail. It is simply absent.** Nothing errored, no log
> line was missing, no task reported a problem — because no task ran it. This is D30's family
> again, but a rung further out: not "silent failure" but *silent non-existence*. A grep for
> "is it built?" answers yes; only "what calls it?" finds this.

Now wired: **`tools/followups_from_board.py`** reads the Applied rows out of the real store
and pipes them in. First run: **13 of 13 applications are past their Day-3 nudge**, the oldest
by **19 days**.

### ⚠️ Two fields the board cannot answer

`jobs` has no `reply` column and no `followups_sent` column — two of the four inputs the
cadence needs. The feeder emits `reply=false, followups_sent=0` and says so, loudly, **before**
the list rather than after it.

That direction is chosen, not defaulted (the "choose the failure direction first" rule):
over-reporting costs one Slack card he ignores; under-reporting lets a lead go cold and is
invisible. And **nothing sends** — followups.py only drafts, every nudge is still his click.
The one genuine hazard is a *duplicate* Day-3 to someone already nudged, which is precisely
what the warning names. The real fix is two columns on `jobs`.

### 🔴 Both nudge templates contained an em-dash

*"Circling back on my application — still very keen…"* and the Day-7 twin. An em-dash is the
single most recognisable AI tell in this project's own writing rules, and these are drafts
that go to a **real recruiter**. They sat there since the templates were written.

They were never caught because **no nudge had ever been rendered from real data.** Reading the
template in the source, nobody sees it; watching thirteen of them print with real company
names, it is the first thing you see.

> **A template that has never been rendered with real data has never actually been reviewed.**

Same run, same shape: the feeder's caveat printed *after* forty lines of nudges, because the
child process wrote straight to the console while the parent's `print` sat in a buffer. **A
warning printed below the thing it warns about is not a warning.** One `sys.stdout.flush()`.

Related: D30 (nothing observed is not nothing wrong) · D23 (the mirror is not the board) ·
D35 (a channel nobody reads) · D41 (count who reached nobody) · [[30-warm-insider-runbook]]

---

## D45 — One wrong URL parameter explains years of "external-or-none" (2026-08-15)

**Trigger.** Azam asked for 20 fresh applications. The board held 43 `New` rows, so the
obvious move was to apply to those. He pushed back — *"are you just repeating the previous
25 or 30 posts you already scraped? Screw them and delete all those posts"* — and he was
right, in a way the numbers stated bluntly.

### The board was 100% spent

An `apply-all` run walked all 32 eligible rows (`--limit` caps *submissions*, not rows
examined — the documented behaviour):

```
SUBMITTED (confirmed) : 0
not submitted         : 32
   13x external-or-none      9x closed      3x resume-mismatch
    3x stalled-validation    2x reached-review   2x error
```

**Zero.** Every row was 14-21 days old, against a measured rot horizon of ~5 days. Nine
postings were closed outright. The board was not a backlog, it was an archive.

### 🔴 The root cause of `external-or-none`: `f_EA` is not the Easy Apply filter

Thirteen of thirty-two rows were **not Easy Apply at all**, and the apply robot only does
Easy Apply (D18). That was blamed on discovery being indiscriminate. It was not. It was one
wrong query parameter:

| Parameter | Same query, same day | Easy Apply hits |
|---|---|---|
| `f_EA=true` | DevOps Engineer / India / past week | **1 of 18** |
| `f_AL=true` | identical | **17 of 17** |

LinkedIn **silently ignores `f_EA`** and returns the unfiltered set. It is also what the
LinkedIn MCP's `search_jobs(easy_apply=True)` puts in the URL, so that flag does nothing
either. Nothing errors; the results just quietly are not filtered — a wrong answer with a
200 next to it, which is this project's recurring shape (D30, D42, D43).

> **A filter that is ignored looks exactly like a filter that found everything.** Verify a
> filter by checking the property it claims to filter on, not by whether results came back.

With the right parameter, 4 pages × 2 keyword searches produced **115 unique Easy Apply
roles posted within the past week**, of which 45 scored ≥70 and were loaded.

### Two scraping details worth keeping

- **Never select LinkedIn's results pane by class name.** It ships obfuscated, rotating
  classes (`LwOMWkdcwjxyNbocfBZZNRTrZvgogtY`). The list virtualises, so without scrolling
  the right container you get **7 cards out of 121** and think that is the result set.
  Select it structurally: *the scrollable element that contains job cards*.
- **Paginate by clicking the numbered buttons inside one page context.** It is an SPA, so
  `button[aria-label="Page N"]` advances without a reload: 17 → 32 → 48 → 64 in one call.

### What was done

Deleted all 43 `New` rows (backup taken first). **`Applied`, `Invite sent` and `Skipped`
were kept** — the first two are the record, and `Skipped` is the dedupe memory that stops
junk being re-added tomorrow. Loaded 45 fresh rows scored from title only, which is a
triage ordering signal and explicitly **not** a judgement (no JD is fetched).

Also: **Crossing Hurdles' evidence entry was refreshed** with the D36 detail. It was already
recorded, and the screen correctly blocked both of its new postings this run — the first
time that guard has been observed doing its job on live data.

Related: D18 (Easy Apply is the target) · D36 (screen before spending a slot) · D30 (nothing
observed is not nothing wrong) · D23 (the mirror is not the board) · [[26-apply-at-volume]]

---

## D46 — Read every form before answering any of them (2026-08-15)

**The instruction that produced this.** Three consecutive `apply-all` runs ended
`stalled-validation`, `error`, `reached-review` with zero submissions. Azam stopped it:

> *"Read all these 30 forms continuously and see what questions are popping up. I give you
> the answer. From next time if you see that type of question, you will be able to answer
> that."*

That is the right order and the tool did not support it. `apply-all` reports only the
questions the bank FAILED on, and only for steps it managed to reach, so a run that stalls
on page 3 hides everything behind page 3. **Each failed application taught exactly one thing
and cost a real application slot to learn it.**

### `apps/autopilot/survey.py` — read the forms, submit nothing

Walks the same wizard with the same scanner and records EVERY control on EVERY step, with
options, then discards the draft. There is no code path in the file that can submit.

Result over 44 live forms: **104 distinct questions, 65 already answerable, 39 not.** One
pass, no slots spent. Of the 39, most were not missing information at all — they were
phrasings `FIELD_MAP` did not recognise for data the bank already held ("expected **total
annual** compensation" vs `expected (ctc|salary|compensation)`).

⚠️ **The first survey run reported `no-next-button, 0 questions` on three jobs that all have
real forms.** It detected the Easy Apply button and never clicked it — `has_easy_apply()`
only *detects*; `fill_job` clicks and waits. A clean zero produced by opening nothing looks
exactly like a clean zero produced by an easy form, so the survey now prints
**`ZERO QUESTIONS SEEN: treat as blind, not as easy`** rather than a tidy `0`.

### What actually blocked submission

| Blocker | Fix |
|---|---|
| "how many years with **&lt;any tech&gt;**" — bank knew 8 technologies | `experience.technology_years`, 97 entries from his own CV, with a **0** default. One unmapped technology stalls the whole wizard, because these fields are required. |
| "Have you completed **Bachelor's Degree**?" | `education_*` specs. ⚠️ Must precede `degree`, whose bare `\bdegree\b` matched it and would have answered **"B.Tech"** to a Yes/No — and given the Bachelor's answer to a **Master's** question. |
| "Are you **currently** serving notice period?" | one adverb between "you" and "serving" broke the pattern. Another form spelled it **"servibg"**. Employers typo their own questions. |
| "Why do you want to join **our company**?" | genuinely per-company, so `freetext.py` asks the free model — the only LLM write onto an employer's form, whitelisted to motivation prose. |

### 🔴 Three failures that were the SAME bug wearing different clothes

Each looked like a different subsystem. All three were *"the value never actually landed"*:

1. **`resume-mismatch`, 15 of 33.** `_capture_resume` took the FIRST filename in the modal
   text. The résumé step is a **radio list** — five CVs — and the first was
   `FAMILY-Software-Engineer.pdf`. Every DevOps and AI/ML job was compared against it and
   aborted, **while the correct CV sat three rows below, already uploaded.** Now reads the
   *checked* radio and SELECTS a match before considering an upload.
2. **The select then failed silently.** `radio.check(force=True)` →
   *"Element is outside of the viewport"*. The list scrolls; `force` skips actionability
   checks but **not** the viewport requirement. Clicking the **label** carrying the filename
   works first try.
3. **`stalled-validation`.** NielsenIQ's "Location (city)*" showed *"This field is required"*
   in red **while visibly containing "Srinagar"**. It is a typeahead bound to a location
   entity: `fill()` sets the visible string and never fires the selection, so the form still
   considers it blank. Now types per-keystroke and picks a suggestion.

> **A field that displays your value has not necessarily accepted it.** Read the state the
> form itself keeps — the checked radio, the validation message — not the pixels.

### Measured

0 of 32 submitted before. **8 confirmed submissions** on the first run with the filled bank,
more on the runs after the résumé and typeahead fixes. **142 tests** (was 112).

Related: D45 (the board was stale and `f_EA` is the wrong filter) · D31 (a pattern that can
match another question is as dangerous as inventing a value) · D30 · D42 (the token budget)

### Addendum to D46 — free-text fields have a character cap, and the browser enforces it silently

Caught by Azam 2026-08-15, after the 21 submissions: *"there is a limit on the number of words
you can write and you cannot exceed that."* He was right, and the failure mode is the worst
kind.

LinkedIn caps free-text answers — the live counter reads **`0/20`** on the years fields and
`0/300` on prose. **Playwright's `fill()` does not error on an over-long string; the BROWSER
truncates it.** So a 235-character banked paragraph arrived on a real employer's form ending
mid-word, with nothing raised anywhere. `Control` did not even capture `maxlength`, so nothing
had ever looked.

Fixed in three places:

1. **`Control.maxlength`** is captured in `_scan`.
2. **`_fit_to_limit()`** trims at a sentence end, else a clause break, else **refuses**. It
   carries two independent floors, because they catch different mistakes: the result must fill
   a fair share of the **field** (or it reads as a stub), *and* keep a fair share of the
   **answer** — retaining 8% of a 235-char reply is not a trim, it is a 300-char paragraph
   aimed at a 20-char box, and the honest move there is blank-and-report.
3. **The LLM is told the cap in characters** and writes inside it. Verified live: 259 chars at
   a 300 cap, 188 at 200, both ending on a full stop. ⚠️ The budget line says **characters,
   never words** — a word count is what made the model number its own words earlier.

The four banked prose answers were rewritten to **under 300 characters each, ending on a full
stop**, so a common 300-cap field receives finished prose rather than something the trimmer had
to rescue. `tests/test_field_limits.py` asserts that and fails if anyone lengthens them.

> **A silent truncation is a wrong answer with no error attached.** Anywhere a system accepts
> your value without complaint, check what it stored, not what you sent — the same lesson as
> the résumé radio and the location typeahead, one layer lower.

**150 tests** (was 142).

---

## D47 — Finding the human is code; contacting them is not (2026-08-15)

**Context.** The day before, 21 applications went out and **19 reached no human**. `coverage.py`
had counted that correctly since D41 and could never fix a single one: the next move — find a
recruiter at that company — existed only as [[30-warm-insider-runbook]], a procedure a person read
by hand. So the pipeline could apply twenty-one times in an evening and produce twenty-one queue
entries. That is D32 at scale, and it is the mass-automation failure this project exists to reject,
reached from the other side: not by spamming people, but by reaching **nobody at all**.

Azam's instruction was blunt: *"I just want the pipeline to be complete and it should run every
time. Messaging everyone, sending the connections, and everything should be in the pipeline."*

**Decision.** Build `apps/autopilot/outreach.py` as the missing link, and wire the whole loop into
one scheduled entry point — **without** moving the send gate.

```
apply-all -> coverage -> OUTREACH -> Slack ✅ -> flush-approved -> watch-accepts -> nudge
                         ^^^^^^^^     ^^^^^^
                         new code     unchanged human gate (D12)
```

`outreach.py` searches LinkedIn **read-only** through the signed-in Playwright profile `replies.py`
already uses, writes `contact.md`, and posts a Slack card carrying `ref:<slug>`. It never sends a
connection request. Scripted people-search plus auto-connect is the behaviour most reliably
punished with an account restriction, and it is this project's own red line. **Code** finds and
ranks; **the human** ticks; **`flush-approved`** sends one bare invite.

Everything else that was already written but disconnected got wired in the same pass: the follow-up
cadence (D44) now runs on true numbers, and `run-pipeline.ps1` grew from five steps to eight.

**Why the search may be automated when the connect may not.** Reading a public search page is what
a person does before writing to someone; sending unsolicited invites at machine speed is the thing
that gets accounts restricted. Automating the *research* removes the drudgery without touching the
behaviour that carries the risk. Making a step cheap must not remove the cost that forces the
question "is this worth sending?" — so the tick stays.

### ⚠️ Three bugs shipped in the first three live runs, all silent

Found by running it against a real company and **reading the output**, not by reasoning about it.

1. **It recommended a stranger.** LinkedIn's people search matches anywhere in a profile, so
   `"Lotus Interworks" recruiter` returns people who merely share a skill word. Run 1 wrote a
   confident `contact.md` for a Senior AI Engineer with no visible link to the company and posted a
   card asking Azam to connect.
2. **It then recommended an ex-employee.** After adding a company-name check, run 2 picked the
   *same person*: her card genuinely said "Lotus Interworks", on a line beginning **`Past:`**. A
   substring test cannot tell an employee from an alumnus.
3. **It dropped the only genuine lead.** A current Team Lead at the company was discarded twice
   over — his **headline named a different employer** and only the `Current:` line named this one,
   and nothing in `ROLE_KINDS` matched "Team Lead" anyway.

> `employment()` returns **CURRENT / PAST / UNKNOWN**, never a boolean, because the three deserve
> different treatment: contact the employee, never recommend the alumnus, escalate the unknown.

The browser now returns **raw lines and parses nothing**; `parse_card()` does all of it in Python,
pinned by 24 tests built from real harvested cards. The first version parsed inside the browser,
which is precisely why the rule was unreachable from a test.

### The failure directions are split inside one module

Two guards written the same week needed opposite defaults (D36 vs D35), and this module needs both:

- **search ran, zero profiles** → evidence → `record_unreachable()`
- **profiles found, none confirmed at this company** → *not evidence about the company* → escalate
- **search errored / auth wall / timeout** → learned **nothing** → escalate, loudly

`_Outcome.searched_ok` is stored separately from `len(people)` for exactly this reason. Letting one
stand in for the other is D30, and a page full of unconfirmable people says something about what the
card renders, not about the company — blocking on it would burn a real employer permanently.

### Also settled in this pass

- **`nudge.py` feeds the follow-up engine true numbers.** `followups_sent` comes from the send log,
  not a zero standing in for one (D44); `applied_date` from the ledger. Innova ESI correctly showed
  **Day 7**, not Day 3. ⚠️ A nudge card must **never** carry `ref:<slug>` — that string is the
  connection-request approval gate, and a ref would turn "send this follow-up" into "send a
  connection request" through a different runner. There is a test.
- **A default argument freezes a module constant at import.** `coverage.py` carries this warning
  already, and `nudge.py` reintroduced the bug anyway: three tests silently read the *real* send
  log. Every path is now resolved at call time.
- **One browser profile, three steps that want it.** A clean outreach run still left **sixteen**
  `chrome.exe` processes holding the profile; the next Playwright step dies with exit **21**.
  `Release-BrowserProfile` clears leaks but **refuses** to kill a profile held by an interactive
  MCP session — skipping a step is recoverable, killing someone's open browser is not.
- **Force-killing Chromium then reported "logged out". It was not.** `li_at` was on disk, valid to
  2027, and a retry worked. Never diagnose LinkedIn auth from an error string.
- **New scheduled tasks are born broken.** `DisallowStartIfOnBatteries=True` and
  `StartWhenAvailable=False` are the defaults that cost this project a full day in July.
  `schtasks /Create` cannot set them; `Set-ScheduledTask -Settings` can, without admin. And
  `schtasks /TR` mangles a path containing a space — hence `pipeline.cmd`.

**Consequences.** One entry point (`pipeline.cmd`), eight ordered steps, daily at 10:30 plus catch-up
on resume. The human still ticks every invite, sends every nudge, and answers every reply — see
[[32-the-complete-loop]] §7. **187 tests** (was 150).

---

## D48 — The approval gate is removed, on the owner's explicit instruction (2026-08-16)

**Context.** D12 has governed this project since 2026-07-26: nothing goes to a human without Azam
ticking ✅ in Slack. `outreach.py` (D47) was built to that rule — find the recruiter, post a card,
let `flush-approved` send only what was approved. It worked: on 2026-08-15 it queued six cards and
four went out overnight.

He removed the gate himself, unprompted and explicitly:

> *"don't leave it up to Slack. I just want you to do it yourself. Whenever you find a connection
> just go for it ... Don't ask me for permission from Slack. Remove that ... just provide me with
> the details that you have done."*

The risk had already been stated when D47 was written, and he reaffirmed the instruction knowing
it. It is his account. **Slack becomes a receipt, not a request.**

**Decision.** `apps/autopilot/connect.py` sends the bare request directly through the same
Playwright profile; `outreach.py` calls it, hands the invite to `watch-accepts`, and posts one
report per run. `--no-send` restores the old behaviour for a run he wants to eyeball.

### ⚠️ What this costs, recorded so nobody re-litigates it from memory

Automated connection requests are the behaviour LinkedIn most reliably restricts accounts for, and
the gate was the thing keeping this project on the safe side of its own north star. What remains is
**not a substitute** for a human reading each name, and every piece of it got more important the
moment the tick disappeared:

| Guard | Value |
|---|---|
| daily cap, counted from an append-only log | `LINKEDIN_CONNECTS_DAILY_CAP` (5, raise to ~10) |
| randomised throttle | 45s + up to 120s jitter |
| business hours only | 09:00–21:00 — invites at 03:00 are a bot signal no cap disguises |
| one request per person, **ever** | checked against the log before every send |
| **current employees only** | D47's `employment()`, now the last check on who gets contacted |

The guards fire **before the browser is touched**, and a refusal is deliberately *not* written to
the log — logging it would poison `already_requested()` and permanently skip someone never asked.

### Three bugs, and the good failure direction

1. **Connect is not on the top card.** Both live profiles offered only *Follow*; Connect sits in
   the **More** menu. The first version reported `no-connect-button` and moved on.
2. **The sticky nav eats the click.** Playwright scrolls the button into view, which parks it
   *under* LinkedIn's fixed header: *"`<nav>` … intercepts pointer events"*, while the element is
   reported visible, enabled and stable throughout. `force=True` does **not** help — force skips
   actionability, not an element sitting on top (the résumé-radio trap, one layer along).
   `_click_through_sticky_nav()` tries a plain click, then scroll-plus-offset, then a real
   `el.click()` dispatch.
3. **The confirmation was blind.** `get_by_role("button", name=/pending/)` never matches: LinkedIn
   renders the badge with an **empty aria-label** and "Pending" as text, so it has no accessible
   name. An invite that genuinely went out — six Pending markers on the reloaded profile — was
   reported *"sent, but the Pending badge was not seen"*.

That third one failed in the **safe** direction (under-claiming a success), which is the only
reason it was a nuisance rather than a lie. The same blindness in `_top_card_state` would have
invited someone **twice**.

### And one that lost work

A transient `ERR_CONNECTION_CLOSED` on one company's search **aborted the whole batch**: `page.goto`
was outside the try. Every later company went unprocessed and the run died before its Slack report,
so two invites that HAD gone out were reported nowhere. Now guarded per company, and `connect_one`
cannot raise at all — *the caller has already sent invites it owes the owner a report on*.

**Consequences.** Five real connection requests on the first evening, all confirmed by the Pending
badge, all handed to stage 2. **220 tests** (was 198). D12 still governs everything else: the CV,
the pitch, and every nudge remain human-sent.

---

## D49 — An accept with no pitch is worse than never asking (2026-08-16)

**Found by a question, not a test.** Azam asked *"did someone you had requested before accept, and
do you now need to send the message?"*

`invite_tracker.py` answered **"0 accepted"**. That answer was worthless: the tracker records what
`watch-accepts` last *observed*, and `watch-accepts` is a headless Claude session that had not run
since 01:04 — its 18:26 attempt stood down on lock contention. So the honest answer was *"we have
not looked in eighteen hours"*, which D35 already established is indistinguishable in the log from
*"we looked and nobody has"*.

**Two things came out of asking LinkedIn instead.**

### 1. Someone had accepted, and nothing knew
`apps/autopilot/accepts.py` reads the **profiles themselves**, in plain Python over the existing
Playwright profile — no agent, no quota, nothing that can silently decline to run. It found
**Shale Francis (Lotus Interworks) had accepted**, confirmed three ways: zero "Pending" markers, a
`· 1st` badge beside his name, and a Message action present.

It deliberately does **not** send. It marks the accept, which schedules the pitch for a randomised
business-hours moment; detecting an accept and firing instantly is the robotic pattern the two-stage
design exists to avoid. *The delay is the point, not an accident.*

⚠️ Its first verdict came from a bare `\b1st\b` search of the page body, which could match a post or
a sidebar. That was checked against the DOM before anything was scheduled, and it happened to be
right — but a loose text match must never be the sole basis for messaging a real person. Pending is
checked **first**, because it is the unambiguous signal.

### 2. 🔴 The pitch did not exist, for 8 of 14 invites
`watch-accepts` sends the **exact 2b text** from `output/outreach/<slug>/touch-2-linkedin.md` and is
forbidden from inventing one. `outreach.py` wrote only `contact.md`.

So D48 had automated *asking* without automating *answering*: every new invite was heading for a
dead end where the person accepts and hears nothing. **That is worse than never having asked** —
they have now done something and been ignored, which is precisely the fifteen-day failure of D35
with the roles reversed.

**`apps/autopilot/pitch.py`** closes it. Deterministic, role-family-routed (reusing `families.py`),
built only from the verified highlight reel and facts we actually hold. `outreach.py` writes the
pitch **before** anything can accept.

> **It never invents a company detail.** No "I love what you're building", no mission, no funding.
> A detail is either researched or absent, and an invented one is the most obvious tell in a cold
> message. These pitches are honest but **generic**: a researched hook is strictly better, and
> [[30-warm-insider-runbook]] remains the way to get one. This guarantees a floor, not a ceiling.

Tests enforce the tells that have already nearly reached a recruiter from this repo: **no
em-dashes**, no relative time words (D22), OSS framed at project level, no flattery, and
"SHALE FRANCIS" greeted as "Hi Shale" rather than shouted back.

**Consequences.** 8 pitches backfilled; every outstanding invite now has something to send. Shale's
is hand-written and was **not** overwritten by the backfill. **236 tests** (was 220).

---

## D50 — One source is not enough for an action you cannot undo (2026-08-16)

**What happened.** An automatic connection request went to **Aditya Sharma for Berribot**. He does
not work there: his profile mentions Berribot **zero times**, fully scrolled, and he is
banner-flagged *Open to work* — a peer job-seeker, not a route into a company.

**My first diagnosis was wrong, and the wrongness is the lesson.** I said "card bleed": that
`a.closest('li')` had swept a neighbouring result's text into his card. Dumping the raw harvest
disproved it — every card was clean, each person's lines their own. LinkedIn's search card genuinely
says, in its own words:

```
Current: Software Engineer at Berribot
```

So `employment()` (D47) worked exactly as designed. **The search index and the profile disagree.**

> **The defect was not the check. It was trusting one source for an irreversible action.**

### The fix: corroborate on the authority, at the last possible moment

`connect.py::profile_corroborates_company()` runs on the person's own profile immediately before
the Connect click, and refuses with `company-unverified` if the profile never names the employer.
The profile is the authority; the search card is a hint.

It keeps the three-state discipline the rest of this codebase runs on, because the failure
directions differ:

| Observation | Response |
|---|---|
| profile loaded, does **not** name the company | **refuse** — an invite cannot be recalled |
| profile could not be read / rendered nothing | **not evidence** — fall back to the card |

Collapsing those two would block every private or slow-loading profile.

⚠️ **My own verification produced a false negative first.** The initial hand check read the page
body **without scrolling** and reported "Berribot appears 0×" — which happened to be right, but for
the wrong reason: LinkedIn lazy-loads Experience far below the fold. The instrument nearly lied in
both directions on the same day. `profile_corroborates_company` scrolls five times before reading.

### The second defect: the verdict was never written down

`contact.md` recorded only `Why them: engineer` — **no employment field at all**. So the mistake was
invisible in the exact file a human would review.

> **A three-state check is worthless if its verdict is never persisted.** Persist the *evidence*,
> not just the decision.

`contact.md` now carries **Works there: CURRENT/PAST/UNKNOWN** plus the literal card line it came
from, and `Candidate.reviewable` makes a candidate whose evidence cannot be quoted **ineligible to
be contacted at all**.

### Containment and the audit

The invite is spent and unrecallable. **The pitch was withheld** — marked FAILED, and the file
renamed so `watch-accepts` cannot find `touch-2-linkedin.md`. Kept rather than deleted, with the
corrected diagnosis on it, so the mistake stays reviewable.

Audit of the other four sent that day: **TCS, Discovr AI and ANSR** all name the employer in the
headline; **BayOne verified by hand** ("BayOne" appears 5× on his profile). **1 wrong in 5.**

**Consequences.** **251 tests** (was 236). Both stacks share `outreach.py`, so this was fixed before
any OmniRoute work began — building on top of it would have duplicated the defect rather than
contained it.

---

## D51 — The OmniRoute stack is built, beside the Claude one (2026-08-16/17)

**Context.** Azam has free keys across several providers and asked for the pipeline to stop
depending on Claude. He then set the constraint that shaped the whole build: *"I don't want you to
replace all this ... the previous one with the cloud agents should be there. It should not get
deleted."*

**Decision.** Additive, not a migration. Two entry points, both runnable:

```
pipeline.cmd       -> Claude stack     UNCHANGED, still scheduled 10:30
pipeline-free.cmd  -> OmniRoute stack  NEW, opt-in, unscheduled
```

Proven untouched: `git diff rewrite/phase-0` for `run-pipeline.ps1`, `cv.py` and all six agent
runners is **empty**, and no `free/` module mentions `claude.exe`. Thirteen already-Claude-free
modules are **shared** by both stacks rather than forked.

**Built:** `env.py` · `free/discover.py` · `free/cv.py` + `free/cv_validate.py` · `free/dm.py` ·
`free/gmail.py` · `run-pipeline-free.ps1`. **349 tests** (was 236 at the start of the day).
Full detail and measurements in [[33-omniroute-stack]].

### The five findings, each a general lesson

1. **A config file nothing loads.** `llm.py` read env vars and **nothing ever loaded `.env`**, so
   `freetext.py` — which writes into real employer forms — was dead in every scheduled run. It
   worked only in shells where the vars happened to be exported by hand.
2. **Silent truncation at the end.** `max_tokens=128` gave **0/4** exact echoes
   (`ALPHA 12345 OMEGA` → `ALPHA 12`); 512 gave 4/4. The hidden thinking pass spends the same
   budget, HTTP 200 throughout. `ask()` now raises any budget below the floor.
3. **A fallback must fit in the fallback.** The CV prompt carried 24,000 chars and Groq's free tier
   refused it (413, 14,463 tokens against 12,000). *A prompt only the primary can accept makes the
   fallback useless exactly when it is needed.*
4. **Scroll the pane, not the window.** The first scrape returned **7** postings — the number
   runbook 31 cites as the virtualisation symptom. The list has its own scroll container; scrolling
   it *until the count stops growing* gave 40. A fixed number of scrolls is a guess.
5. 🔴 **A missing UTF-8 guard loaded zero of 36 rows.** `intake.py` raised `UnicodeEncodeError`
   printing a job title, **before** the insert, and the only symptom was a quiet `exit 1` inside a
   step I had marked "informational". The regression test then found **six more** modules with the
   same hole, including `run.py`, the apply runner — they survive only because the PowerShell
   runners call `chcp 65001` first.

> **"Informational" must mean "this failing is genuinely fine", not "this fails a lot".** Two
> mistakes compounded there: a missing guard, and a step whose failures the runner was told to
> ignore. The step is no longer soft — "no jobs loaded" is not information.

### Also worth keeping

- **`--dry-run` reported FAILED while printing `attempt 1: PASS`**, because `BuildResult.ok`
  required a written path. Conflating *succeeded* with *persisted* makes the mode you test with lie
  about the thing you are testing.
- **The bulk patch that added six UTF-8 guards broke `coverage.py`**: a "last import line"
  heuristic matched a function signature's closing paren. Caught by running every CLI's `--help`,
  not by the unit tests — which is the argument for a smoke test after any mechanical edit.
- **I swept another session's `tools/post_creator/` changes into a commit**, then made it worse by
  `git checkout HEAD~1 --` on them, which discarded their uncommitted work. Recovered from the
  reflog. Runbook 31 already warns to stage by name; `git add -u tools` ignores that warning.

**Consequences.** Both stacks work. Gmail needs one browser consent and reports `needs-setup`
until then; nothing on the free stack is scheduled yet, by design.

---

## D52 — A control found by the wrong role is a confident lie (2026-08-17)

**Context.** SHALE FRANCIS accepted a connection request at 2026-08-16 19:49; the tracker
scheduled his touch-2 pitch for 09:12 the next morning. Running the delivery step by hand at 10:21
produced:

```
[1/1] SHALE FRANCIS (lotus-interworks)
     not-connected: no Message button; not connected
```

That contradicted the tracker, which had watched him accept fifteen hours earlier. Two sources
disagreeing about a person is precisely the situation [[D50]] says never to resolve by picking the
convenient one, so the page was dumped instead of believed.

**What was actually there.** Thirty-one buttons, none of them Message — and this:

```
link[7] 'Message' -> /messaging/compose/?profileUrn=...&recipient=ACoAABtyRzk...
```

`dm.py` searched `get_by_role("button", name=/^message/)`. **The control is an `<a>`.** The
selector could never have matched, on any profile, for anyone. Every accept this module was ever
pointed at would have been reported "not connected".

> **A negative produced by the wrong selector is byte-identical to a true negative.**

This is the third instance of the same shape: the Pending badge with an empty `aria-label`
([[D48]]), the Gmail-only reply check ([[D35]]), and now this. The distinguishing feature is that
each one *reported* rather than crashed, and the report was calm.

**The trap in fixing it.** The obvious repair — loosen the regex until something matches — walks
directly into [[D50]]. The right-hand rail carries one link per suggested profile:

```
link[46] 'Message Anjum Latif'  -> ...&recipient=ACoAADl3N7g...   (a different person entirely)
link[56] 'Message Dhruv Gupta'  -> ...&recipient=ACoAABJVYgs...
```

A widened match opens a composer addressed to a stranger and types a pitch about a job at a
company they have never worked for. **The fix for a blind selector must be more specific, not less.**

**Decision.** `message_control()` anchors on the accessible name being *exactly* `Message` — the
profile owner's control carries no name, everyone else's is `Message <Name>` — and then requires
every such control to agree on the `recipient` URN in its href. Disagreement is a **refusal**, not
a tie-break. `Message with Premium` is excluded separately: it is InMail, not a 1st-degree message,
and it spends a paid credit.

The recipient URN, once verified, is stronger evidence than any heading, so the composer-name
check now runs **only** when no href was available to bind the recipient. An earlier draft of that
check matched a bare `aside` — which is also the tag of the "People also viewed" rail, and would
have refused every legitimate send while looking like a safety feature.

**Also fixed, same module, same disease.** `mark_sent()` returned `False` silently on a non-zero
exit from the tracker — the *likeliest* failure of the three, and the only unannounced one. That
path means the pitch has already reached a real person and was not recorded, so the next run sends
it **again**. A duplicate pitch to a warm lead is the most embarrassing thing this pipeline could
do, and it was one quiet return value away. Now loud, with the by-hand remedy printed, and `run()`
exits 2 if any delivery went unrecorded.

Relatedly, a Send click that cannot be read back afterwards stays `SENT` **on purpose**: between an
unconfirmed delivery and a duplicate one, the duplicate is worse and it is the one a recruiter
would notice. The count is reported separately (`n confirmed in-thread, m unconfirmed`) so the
choice is never silent.

**Consequences.** 394 tests, the selector ones built from a real profile dump including the sidebar
links. Also proven live in the same hour: the free stack asked for the pipeline lock while the
Claude stack's Reply Check held it, and stood down cleanly — the two stacks cannot collide over the
one browser profile.

## D53 — Consent is not access, and the credential probably already exists (2026-08-17)

**Context.** `free/gmail.py --authorize` dead-ended at *"no OAuth client JSON"* and told the owner
to go build one in the Google Cloud console. Five Desktop-app OAuth clients were already sitting in
`~/Downloads` from his other projects. The work had been done twice over and was invisible to the
tool asking for it.

**Decision, part one.** `--list-clients` enumerates Desktop clients already on the machine
(`~/.credentials` first, so re-running never silently switches Google Cloud project), and
`--client <path>` installs a chosen one. It **lists and never picks**: these belong to different
projects and only the owner knows which is tied to the right account. Choosing for him would
authorise the wrong mailbox and look like success. The file is **copied**, not referenced — one
Downloads tidy-up would otherwise break every unattended run.

**Decision, part two, which is the real one.** The Gmail API is enabled **per Google Cloud
project**. A client borrowed from another project completes OAuth consent perfectly and then 403s
every single call. So a token on disk proves *a human clicked yes* and **nothing whatsoever about
whether mail can be read** — [[D35]] wearing a new hat, in the one channel [[D35]] was about.

`--authorize` therefore ends with a real `getProfile` call. If that fails it **deletes the token**
rather than leaving a credential that turns every later run into a 403 reading like an outage, and
prints the enable URL for that specific project. It distinguishes `SERVICE_DISABLED` from a bad
credential, because sending someone to a page that already says *Enabled* teaches them the tool is
broken.

> **A stored credential is not a readable channel. Prove the read.**
