# 12 — Approved-Send Runbook (stage 1: approve on phone, knock when the laptop wakes)

Back to [[00-INDEX]]. Siblings: [[13-accept-watch-runbook]] (stage 2, the pitch),
[[09-discovery-runbook]] (find), [[11-reply-classifier-runbook]] (inbound).

The recipe that turns an approval made on the phone into an actual LinkedIn send. Runs **every 30 minutes**
while logged in, via task "Job Hunt - Flush Approved" (installed 2026-07-26), and can be run on demand.
Followable cold — read [[07-current-state]] first.

> **Cost guard:** `flush-approved.ps1` runs `check_approvals.py --json` first and exits in under a second when
> nothing is approved, so it never wakes a headless Claude on an idle cycle. Keep that guard if you change the
> schedule. The trigger is timed rather than at-logon because registering an at-logon task needs admin rights;
> timed is also more responsive, since it doesn't wait for a logout/login.

> **This is only stage 1 — the knock on the door.** It sends a *bare* connection request and records it.
> The CV and the real pitch go out in [[13-accept-watch-runbook]], hours after the person accepts.
> One ✅ from the owner authorises both stages; the words are approved here, the moment is chosen there.

## The design: approve anywhere, send when the laptop wakes

Owner asked for an approve button that works with the laptop **off**. LinkedIn messaging only works through
the local browser-automation MCP, so **no cloud service can send it** — that part is a hard limit
([[05-decisions]] D11). What *can* work is splitting the decision from the delivery:

```
phone, laptop off:  react ✅ on the Slack job card   (primary — owner found Notion confusing)
                    or set Notion Status -> "APPROVED - SEND"   (alternate, same effect)
laptop turns on:    logon task -> this runbook -> Claude sends -> Slack confirms
```

**Slack reaction is the primary gate** (owner's call, 2026-07-26: "put it on Slack, in Notion it gets
confusing"). Chosen over Slack buttons because reactions need only two extra bot scopes
(`channels:history`, `reactions:read`) rather than Socket Mode plus an app-level token, and a reaction is
one tap on a phone. Each card carries a `ref:<slug>` marker so a reaction maps back to the right job.
Reactions recognised: ✅/☑️/👍/🚀 approve · ❌/⛔ skip · 📤 already sent (the send-twice guard).

## Guardrails
- **Only ever send for rows with `Status = "APPROVED - SEND"`.** Nothing else is sendable, ever.
- **Send the exact text already reviewed** in `output/outreach/<slug>/touch-2-linkedin.md` (the 2a connect
  note). Never rewrite it at send time — the owner approved specific words.
- **Caps** from `.env`: `LINKEDIN_CONNECTS_DAILY_CAP` (5) and `MIN_SECONDS_BETWEEN_SENDS` + jitter. If more
  are approved than the cap allows, send the highest Fit Score first and leave the rest approved for tomorrow.
- **Idempotency:** the status change *is* the guard. Move the row off `APPROVED - SEND` the moment it sends,
  so a second run can never double-send.
- **Never invent recipients or text.** If `contact.md` has no named contact or the note still has a `[…]`
  slot, skip the row, set Notes, and report it.

## Steps

### 1. Find what was approved (check BOTH gates)
```
py -3 tools/check_approvals.py --json     # Slack ✅ reactions -> [{slug, ts, job}]
```
and also the Notion alternate:
```sql
SELECT "Job","Company","Fit Score","Notes",url FROM "collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2"
WHERE "Status" = 'APPROVED - SEND'
```
Union the two, de-duplicating by company slug. Nothing approved → post nothing, exit quietly.

### 2. Load the reviewed message
For each row, open `output/outreach/<company-slug>/` → `contact.md` (recipient + LinkedIn URL) and
`touch-2-linkedin.md` (the **2a** connect note, ≤300 chars). Confirm no unfilled slots remain.

### 3. Send on LinkedIn — a BARE request, no note
Most targets are 2nd/3rd degree, so the action is a connection request:
`connect_with_person(linkedin_username=<from the profile URL>)` — **with no `note` argument.**

Then record it so stage 2 can pick it up:
```
py -3 tools/invite_tracker.py add --slug <slug> --person "<Name>" --username <u> --role "<role>"
```

Why no note (2026-07-26, [[05-decisions]] D12): a request *with* a note is capped at **3 per month** on a free
account, while a DM to an existing 1st-degree connection has **no cap at all**. Skipping the note removes the
bottleneck and moves the whole pitch to [[13-accept-watch-runbook]]. The MCP also refuses to attach one — it
returns `custom_note_limit_reached` and sends nothing whenever `note` is supplied and LinkedIn is showing its
quota banner, regardless of length. Do not retry with a shorter note.

**The 3 monthly notes are reserved for warm insiders, sent by hand by the owner** — that's where the
shared-roots line earns the accept. Never spend one on a cold recruiter.

Only use `send_message` when the person is already 1st-degree. Space sends by the `.env` delay + jitter; stop
at the daily connect cap.

### 4. Record it
Per row sent: `Status = "Invite sent"`, and append a one-line note saying who was contacted. **Not "Applied"**
— a bare connection request is not an application, and marking it so would lie to the board. `Status` becomes
`Applied` in [[13-accept-watch-runbook]] step 4, when the actual pitch lands. The Day-3/Day-7 cadence in
[[08-completion-plan]] step 3 starts from *that* moment, not this one.

### 4b. Close the Slack loop — **NOT OPTIONAL**
```
py -3 tools/slack_react.py --slug <slug>
```
Stamps 📤 (`outbox_tray`) on the card. **This is the send-twice guard.** `check_approvals.py` skips any card
carrying 📤; skip this step and the job stays "approved" forever, so the every-30-min flush sends the same
person another connection request on every single run. Do it immediately after each successful send, not in a
batch at the end — a crash mid-run must not leave an unstamped card behind.

### 5. Confirm on Slack
```
py -3 tools/slack_notify.py --event sent --title "Knocked on <N> doors" --text "<who, which role, one line each>"
```
Report skips and cap-deferrals in the same message, honestly.

**Keep it short** (owner's call, 2026-07-26 — long Slack messages were "making me confused"). One line per
person: name, company, what happened. No explanations, no checklists, no restating how the system works. If a
line doesn't change what the owner would do, cut it. The same rule governs the job cards themselves — see the
docstring in `tools/slack_action_card.py` before adding any field to them.

## Success = the owner taps Approve on their phone at any hour, and the next time the laptop is on, the
right person receives a connection request, it is tracked as pending, and Slack says so — with the real pitch
queued up in [[13-accept-watch-runbook]] for the moment they accept.
