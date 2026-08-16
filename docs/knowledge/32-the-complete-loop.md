# 32 — The complete loop (what runs, in what order, unattended)

> **Read this when the question is "is the pipeline finished?" or "why did nothing happen?"**
> [[31-apply-batch-runbook]] is how to *drive* a batch by hand. This is what the machine does on
> its own, and where the human still sits in the middle on purpose.
>
> Built 2026-08-15, the day after 21 applications went out and **19 reached no human**.

---

## The shape of it

```
  accepts -> flush -> replies -> nudge -> discovery -> apply -> outreach -> packets
  \____ deliver what is owed ____/  \_ chase _/  \____ make new work ____/  \_ prep _/
```

One entry point:

```bash
pipeline.cmd                  # the whole loop
pipeline.cmd -Only outreach   # one step
pipeline.cmd -WhatIf          # list the steps, run nothing
```

Scheduled as **"Job Hunt - Full Pipeline"**, daily 10:30, plus **"Job Hunt - Catch Up"** two
minutes after resume. The per-step tasks (Flush every 30 min, Watch Accepts every 4 h, Reply Check)
still exist and still run — they give faster turnaround than a daily sweep, and the pipeline lock
means a collision just makes one side stand down.

### Ordering is the whole design (D20/D24)

Anything that puts a message in front of a person runs **first**, because those steps have a
deadline. Discovery, applying and packet building are work that keeps. A crash in a late step must
never cost an overdue pitch.

---

## What each step does

| Step | Module | Sends? | Notes |
|---|---|---|---|
| accepts | `tools/watch-accepts.ps1` | **yes**, stage 2 | The one place words go out without a fresh tick — the owner approved them at stage 1 (D12) |
| flush | `tools/flush-approved.ps1` | **yes**, stage 1 | Bare connection request, only for cards ticked ✅ |
| replies | `tools/check-replies.ps1` | no | Step 0 is `replies.py` reading the **LinkedIn inbox** (D35) |
| nudge | `apps/autopilot/nudge.py` | no | Day-3 / Day-7 drafts to Slack |
| discovery | `tools/daily-discovery.ps1` | no | Currently **disabled** as a task; runs here |
| apply | `apps/autopilot/run.py apply-all` | submits | Capped `-ApplyMax 8`, once a day |
| outreach | `apps/autopilot/outreach.py` | **YES** (D48) | Finds a named human, **connects**, writes the 2b pitch, reports after |
| accepts | `apps/autopilot/accepts.py` | no | Asks LinkedIn who accepted, in plain Python (D49) |
| packets | `tools/sweep-packets.ps1` | no | Tailored CVs |

---

## 1. The gap this closed

`coverage.py` could always *count* applications that reached nobody. It counted **19 of 21** on
2026-08-15. It could never *fix* one, because the next move — find a recruiter at that company —
existed only as a runbook a person read by hand ([[30-warm-insider-runbook]]).

So the pipeline could apply twenty-one times in an evening and produce twenty-one queue entries.
That is the mass-automation failure this project exists to reject, arrived at from the other side:
not by spamming people, but by reaching **nobody at all**.

`outreach.py` is the missing link:

```
apply-all -> coverage -> OUTREACH -> Slack ✅ -> flush-approved -> watch-accepts -> nudge
                         ^^^^^^^^
```

It **searches** LinkedIn read-only through the same signed-in Playwright profile `replies.py` uses,
writes `output/outreach/<slug>/contact.md`, and posts a Slack card carrying `ref:<slug>`.

**It never sends a connection request.** Scripted people-search plus auto-connect is the behaviour
most reliably punished with an account restriction, and it is this project's own red line. The
split is unchanged: **code** finds and ranks, **the human** ticks, **`flush-approved`** sends one
bare invite.

---

## 2. ⚠️ The three bugs the first live runs shipped

All three were found by running it against a real company and *reading the output*, not by
reasoning about it. Every one was plausible, well-formed, wrong and silent.

### It recommended a stranger
LinkedIn's people search matches **anywhere in a profile**, so `"Lotus Interworks" recruiter`
returns people who merely share a skill word. Run 1 wrote a confident `contact.md` for a Senior AI
Engineer with no visible connection to the company and posted a card asking the owner to connect.

### It then recommended an ex-employee
Run 2, after adding a company-name check, picked the *same person* — her card genuinely said
"Lotus Interworks", on a line beginning **`Past:`**. A substring test cannot tell an employee from
an alumnus.

> `employment()` returns **CURRENT / PAST / UNKNOWN**, never a boolean, because the three deserve
> different treatment: contact the employee, never recommend the alumnus, escalate the unknown.

### It dropped the one genuine lead
A real current Team Lead at the company was discarded, twice over: his **headline named a different
employer** ("Team Lead Simplia") and only the `Current:` line named this one, and nothing in
`ROLE_KINDS` matched the words "Team Lead" anyway.

**Fix:** the browser returns raw lines and parses *nothing*. `parse_card()` does all of it in
Python, where 24 tests pin it against real harvested cards. The first version parsed inside the
browser, which is exactly why the rule was unreachable from a test.

Also caught: mutual-connection facepile links were being harvested as people, producing a
"candidate" named *"Parvaiz Ahmad - Srinagar, SAYAR UL HASSAN & 4 other mutual connections"*.

---

## 3. Which way each guard fails

Two guards written the same week needed **opposite** defaults, and "be safe" names neither.

| Module | Leans | Because |
|---|---|---|
| `replies.py` | escalate anything unclear | A false alarm costs 10 seconds; a false silence cost **15 days** |
| `sourcing.py` | never block on suspicion | Blocking a real employer is unrecoverable; a wasted slot is 15 seconds |
| `outreach.py` | **both, deliberately split** | see below |

`outreach.py` distinguishes three outcomes that a careless version collapses into one:

- **search ran, returned no profiles at all** → evidence → `record_unreachable()` (D36)
- **profiles found, none confirmed at this company** → *not evidence about the company* → escalate
- **search errored / timed out / hit an auth wall** → learned **nothing** → escalate, loudly

> A page full of people none of whom could be confirmed says something about what the card renders,
> not about the company. Blocking on it would burn a real employer forever.

`_Outcome.searched_ok` is stored **separately** from `len(people)` for exactly this reason. Letting
one stand in for the other is D30, the defect this codebase keeps re-finding.

---

## 4. Follow-ups now run on true numbers

`tools/followups.py` computed the cadence correctly for weeks and **had no caller**. Then
`followups_from_board.py` fed it, and had to emit `followups_sent=0` for every row because `jobs`
has no such column — honest, and it left the one dangerous case (a second Day-3 to someone who
already got one) to whoever read the output.

`apps/autopilot/nudge.py` reads both numbers from records that are true:

- **applied_date** ← the append-only ledger, the only artefact here that has never been wrong
- **followups_sent** ← `output/apply-log/followups-sent.jsonl`, a real count
- **stop** ← board status, plus `sourcing`'s unreachable list

It reuses `followups.py`'s cadence and templates by **loading it by file path**, so there is exactly
one definition of the schedule. First real run: 7 due, and Innova ESI correctly showed **Day 7**
rather than Day 3 because its Day-3 is genuinely on record.

> ⚠️ **A nudge card must never contain `ref:<slug>`.** `check_approvals.py` greps for that exact
> string to find *connection-request* approvals and `flush-approved` acts on what it finds. A ref on
> a nudge card would turn "yes, send this follow-up" into "send a connection request", through a
> different runner, with nothing on the card to reveal it. There is a test.

Log a nudge you sent by hand, or the count silently rots:

```bash
py -3 -m apps.autopilot.nudge --mark "Innova ESI"
```

---

## 5. One browser profile, three steps that want it

`replies`, `apply` and `outreach` all drive `.pw_browser\linkedin_user_data`, and Chromium allows
**one process per profile** — a second launch dies with *"Failed to create a ProcessSingleton"*,
**exit code 21**.

Observed 2026-08-15: an outreach run that finished cleanly still left **sixteen** `chrome.exe`
processes holding the profile. `Release-BrowserProfile` in `run-pipeline.ps1` clears leaked
processes before each browser step, and **refuses to touch a profile held by an interactive
LinkedIn MCP session** — skipping a step is recoverable, killing someone's open browser is not.

⚠️ After force-killing Chromium, the next launch reported **logged out**. It was not. `li_at` was on
disk and valid until 2027, and a retry worked. *Never diagnose LinkedIn auth from an error string —
check the cookie, then test with a real call.*

---

## 6. The settings that silently killed every task before

A new scheduled task is created with defaults that have already cost this project a full day:

| Setting | Default | Set to |
|---|---|---|
| `DisallowStartIfOnBatteries` | **True** — dead on battery | False |
| `StopIfGoingOnBatteries` | **True** | False |
| `StartWhenAvailable` | **False** — missed runs never catch up | True |
| `ExecutionTimeLimit` | PT72H | PT3H |
| `MultipleInstances` | — | IgnoreNew |

`schtasks /Create` cannot set these; `Set-ScheduledTask -Settings` can, and worked without admin.

⚠️ **`schtasks /TR` mangles a path containing a space.** `d:\linkdin automation\...` failed with
*"Invalid argument/option"*. `pipeline.cmd` at the repo root exists to give the scheduler a
space-free-ish single target, and is the reason the task is one word long.

---

## 7. What is still a human's job

⚠️ **Changed 2026-08-16 (D48).** Azam removed the connection-request tick himself: *"Whenever you
find a connection just go for it ... just provide me with the details that you have done."* Slack is
now a **receipt** for that step, not a gate.

1. ~~Tick the ✅ on every connection request~~ — **now automatic.** See D48 for what that costs and
   which guards carry the risk in its place (cap, throttle, business hours, never-twice, and
   current-employees-only, which is now the last check on who gets contacted).
2. **Send the nudges.** The drafts arrive in Slack; the sending is his.
3. **Reply to humans.** `replies.py` finds them and shouts; it never answers.

The CV and the pitch still go out only after someone accepts, and every nudge is still his click.
D12 governs everything except the bare invite.

---

Related: [[05-decisions]] **D47** · D32 (volume without contact) · D36 (only evidence may block) ·
D41 (count what reached nobody) · D44 (the engine fed by nothing) · D12 (human approval) · D8
(warm insider first) · [[30-warm-insider-runbook]] · [[31-apply-batch-runbook]] · [[26-apply-at-volume]]

---

## 8. First full unattended run — 2026-08-15 19:22→19:41 (19 minutes)

Triggered through the scheduler, not by hand. All eight steps executed in order.

| Step | Time | Result |
|---|---|---|
| accepts | 251s | exit 0, nothing ripe |
| flush | 1s | exit 0, nothing ticked yet — the cheap guard working |
| replies | 344s | exit 0 |
| nudge | 0s | 7 already announced, 0 re-posted (dedupe working) |
| discovery | 1s | skipped, ran today |
| apply | 302s | 13 rows walked, **0 submitted** |
| outreach | 215s | **4 named recruiters queued**, 1 escalated |
| packets | 0s | **exit 1 — parse error, see below** |

**Outreach worked as designed.** Four current recruiters found at Talentgigs, Hyper Lychee Labs,
slice and IndiGo, each written to `contact.md` and posted for a tick. MyRemoteTeam Inc returned
4 profiles, none confirmed as working there, and was **escalated rather than blocked** — exactly the
middle branch from §3. Coverage fell 19 → 17 in the same run.

### ⚠️ apply submitted 0 of 13, and that is not the pipeline failing

Six `stalled-validation`, five `reached-review`, two `closed`. These 13 are the **leftovers** from a
board whose good rows were already used: earlier the same day, a fresh batch submitted **21 of 21**.

Per §5 of [[31-apply-batch-runbook]], both statuses mean a required field is still empty — usually a
typeahead that displays a value it never accepted. Diagnosing them is the by-hand Playwright loop,
one job at a time. **Do not read this as "apply is broken"; read it as "these rows need the survey
treatment".** Re-discover first — the board rots in about five days.

### 🔴 Sweep Packets had never run. Not once.

```powershell
Say "STOPPING - CLAUDE USAGE LIMIT, not a problem with $company: $limit"
```

A colon straight after a variable name makes PowerShell read `$company:` as a drive-qualified
reference, and that is a **parse** error — the whole file dies before its first line executes. The
scheduled task showed exit code 1 on every run and looked exactly like a build that kept failing.
Nothing was failing. **The script never ran at all.**

The line was written to explain a *different* silent failure (the D25 usage-limit wall) and was
itself a silent failure the whole time.

Fixed with `${company}`, and `tests/test_powershell_parses.py` now parses **every** `tools/*.ps1`
through PowerShell's own parser. It was calibrated on a known positive — a deliberately broken probe
script — because a clean sweep from an unverified check is not evidence. This catches the whole
class: unterminated strings, unbalanced braces, an indented here-string terminator, `$var:` typos.
None of them produce a useful runtime error, because there is no runtime.
