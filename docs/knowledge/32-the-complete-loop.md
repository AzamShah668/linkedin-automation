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
| outreach | `apps/autopilot/outreach.py` | **no** | Finds a named human, asks for a tick |
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

## 7. What is still a human's job, on purpose

1. **Tick the ✅.** Every connection request. This is D12 and it is not a placeholder.
2. **Send the nudges.** The drafts arrive in Slack; the sending is his.
3. **Reply to humans.** `replies.py` finds them and shouts; it never answers.

Automating any of those three converts this project into the thing it was built not to be.

---

Related: [[05-decisions]] **D47** · D32 (volume without contact) · D36 (only evidence may block) ·
D41 (count what reached nobody) · D44 (the engine fed by nothing) · D12 (human approval) · D8
(warm insider first) · [[30-warm-insider-runbook]] · [[31-apply-batch-runbook]] · [[26-apply-at-volume]]
