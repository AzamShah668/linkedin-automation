# 13 — Accept-Watch Runbook (stage 2: they accepted, so send the real pitch)

Back to [[00-INDEX]]. Siblings: [[12-approved-send-runbook]] (stage 1, the knock), [[11-reply-classifier-runbook]] (inbound).

Stage 1 knocks on the door. This is what happens when someone opens it. Runs **every 4 hours while the
laptop is on** (task "Job Hunt - Watch Accepts") and can be run on demand. Followable cold — read
[[07-current-state]] first.

## The design: knock, wait, then pitch

Owner's call, 2026-07-26: *"you first send them the request and a day after you send the CV… you catch
whenever they accept the request and then send the CV as well and it should be done automatically."*

```
stage 1  ✅ on the Slack card  ->  BARE connection request  ->  tracked as `pending`
stage 2  every 4h: did they accept?  ->  yes: schedule the pitch 3-20h out (business hours only)
                                      ->  when due: send CV + full message  ->  Slack + Notion updated
         14 days of silence          ->  expire it, tell the owner, fall back to email
```

### Why the request carries no note

A connection request **with** a note is capped at **3 per month** on a free account. A message to someone
who is **already a 1st-degree connection has no cap at all**. So the note is deliberately skipped and the
whole pitch is delivered after the accept instead. This inverts the old plan ([[12-approved-send-runbook]]
step 3) and removes the cap as a bottleneck entirely — see [[05-decisions]] D12.

The 3 monthly notes are a scarce, precious budget: **spend them only on warm insiders**, sent by hand by the
owner, where the shared-roots line is what earns the accept. Never burn one on a cold recruiter.

Discovered the hard way on 2026-07-26: the LinkedIn MCP's `connect_with_person` returns
`custom_note_limit_reached` and silently sends nothing whenever a `note` is supplied and LinkedIn is showing
its "N personalized invitations remaining" banner — even with invites still left. Text length is not the
cause (it failed identically at 290 and 197 chars; the note box read `0/200` both times, meaning nothing was
ever typed). **Calling it with no `note` argument works fine.** Do not retry with a shorter note.

## Guardrails

- **Never invent the pitch.** Send the exact `2b` text already in `output/outreach/<slug>/touch-2-linkedin.md`,
  with the `{Recruiter-A / Pawan}` and `[To …]` slots resolved for the actual recipient. If a slot cannot be
  resolved, skip, mark failed, and say so.
- **Never send early.** Only rows returned by `invite_tracker.py due` are sendable. The delay is the whole
  point; an instant reply reads as a bot.
- 🔴 **Re-check the pitch's premise before sending it.** The 2b text is written at **stage 1** and delivered
  days later, so it can outlive what it claims. `due` only proves the clock elapsed — it says nothing about
  whether the role still exists. On 2026-08-19 Himaja Madala's pitch came due opening *"I applied for the
  Cloud Engineer WALK IN Chennai role"*; LinkedIn had **rejected that exact req on 08-18 09:20Z, 2h20m
  before she accepted at 11:40Z**. Nothing in the two-stage design re-reads the premise between the knock
  and the pitch, so the send would have gone out blind. Before sending, confirm the role has no rejection
  in the ledger/Notion. If the premise is dead: **do not rewrite the line yourself** (that is inventing the
  pitch) — `mark-failed` with a reason, Slack it, and let `pitch.py` regenerate or the owner drop it.
  `mark-failed` here means *held*, not *delivery failed*; the reason string is what carries that.
- **Business hours only** (`BUSINESS_HOUR_START`/`END`, default 09:00–21:00 IST). **Enforced in `cmd_due`
  since 2026-07-31** — outside the window `due` returns an empty list and says how many rows it is holding.
  Before that it was only enforced at *scheduling* time, which left a live hole: a due time that lapsed while
  the laptop slept stayed due forever, and Windows fires every missed task at once on wake, so the pitch
  could have gone out at 02:00. Caught at 22:19 with Recruiter-B's 16:28 pitch sitting due. If `due`
  returns nothing at night, that is the guardrail working — **do not hand-send around it.**
- **Caps** from `.env`: `FOLLOWUPS_DAILY_CAP` (3) and `MIN_SECONDS_BETWEEN_SENDS` + `OUTREACH_JITTER_SECONDS`.
  Over cap → leave the rest due; they'll go next run.
- **Idempotency:** `mark-sent` is the guard. Call it the moment a send succeeds, so a crash mid-run can never
  double-message someone.
- **Stop on anything strange.** A LinkedIn warning, a captcha, an unexpected MCP status → mark failed, post to
  Slack, and send nothing else this run. Never retry in a loop.

## Steps

### 1. Age out the dead ones
```
py -3 tools/invite_tracker.py expire
```
Anything pending >14 days becomes `expired`. Report those to the owner as "try email instead" — do not keep
poking them on LinkedIn.

### 2. Check who accepted
```
py -3 tools/invite_tracker.py list --status pending --json
```
For each, call `get_person_profile(linkedin_username)`. The signal is the **degree**: the profile said `2nd`
when the request went out; once accepted it reads `1st`. When it flips:
```
py -3 tools/invite_tracker.py mark-accepted --username <u>
```
That schedules the follow-up 3–20h out, inside business hours. Then tell the owner immediately — an accept is
good news and they may want to jump in themselves:
```
py -3 tools/slack_notify.py --event reply --title "<Person> accepted" --text "<Company> · <role>. Pitch auto-sends around <due time>."
```

### 3. Send whatever is ripe
```
py -3 tools/invite_tracker.py due --json
```
For each due row, open `output/outreach/<slug>/touch-2-linkedin.md`, take the **2b** message, resolve the
recipient slots, and send with `send_message(linkedin_username, message=...)`. They are 1st-degree now, so
this is a normal DM with no invite cost. Space sends by the `.env` delay + jitter. Then:
```
py -3 tools/invite_tracker.py mark-sent --username <u>
```

### 4. Record it
Per person actually messaged: Notion `Status = "Applied"`, `Applied Date = today`, `Follow-ups Sent = 0`, and
append a one-line note of what went to whom. This starts the Day-3/Day-7 cadence in [[08-completion-plan]].
If stage 1 somehow left the card unstamped: `py -3 tools/slack_react.py --slug <slug>`.

### 5. Confirm on Slack
```
py -3 tools/slack_notify.py --event sent --title "Sent <N> follow-ups" --text "<one line each, plus expiries and skips>"
```
If nothing accepted, nothing was due, and nothing expired: **post nothing and exit quietly.** A watcher that
chirps every 4 hours to say "no news" trains the owner to ignore Slack.

**Keep it short** (owner's call, 2026-07-26 — long Slack messages were "making me confused"). One line per
person: name, company, what happened. No explanations, no reasoning, no next-step checklists, no restating
what the system does. If a line doesn't change what the owner would do, cut it.

## Known limits (say these out loud, don't paper over them)

- **Only runs when the laptop is on.** LinkedIn messaging needs the local browser-automation MCP; no cloud
  service can do it ([[05-decisions]] D11). "Every 4 hours" means every 4 hours you're logged in.
- **LinkedIn cannot notify us.** There is no webhook, so acceptance is detected by polling. Keep it gentle —
  a few checks a day, never a tight loop.
- **This is the one place a message sends without a fresh human tick.** The owner approves the *words* at
  stage 1 (the ✅); the robot only picks the *moment*. Volume is what keeps this safe: a handful of unique,
  genuinely personalised messages a week is invisible, fifty identical ones a day is a dead account.

## Success = the owner ticks ✅ once, and days later a real person who chose to accept the request receives
the exact pitch that was approved, at a believable hour, with the board updated and Slack saying so.
