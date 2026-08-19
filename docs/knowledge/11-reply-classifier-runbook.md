# 11 — Reply Classifier Runbook (inbound alerts)

Back to [[00-INDEX]] | See [[09-discovery-runbook]] (the outbound sibling) & [[10-advanced-ideas]] 1.1.

The recipe the **reply-checker** runs (scheduled) to catch recruiter replies and alert the owner. Followable
cold. Read [[07-current-state]] first.

## Guardrails (non-negotiable)
- **Read-only Gmail.** `search_threads` + `get_thread` only. **Never auto-reply or send.** This only
  *detects, classifies, updates Notion, and pings Slack.* The owner replies to recruiters himself.
- **No fabrication.** Classify only from the actual email text; if unsure, mark `Other` and let the human read it.

## Inputs
- **Applied jobs** = `output/apply-log/submitted.jsonl` — the ledger, **not** Notion `Status = Applied`.
  On 2026-08-19 the ledger held **41** sends and Notion `Applied` returned **9**. Query Notion
  (`collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2`) only to find the row to *update*; if a company
  has no row, that is a finding to record, not a reason to skip it.
- **Recruiter emails/domains** = harvested from `output/outreach/<slug>/contact.md`.
  ⚠️ Glob `**/contact.md`, never `*/contact.md` — the latter matches nothing and returns a confident
  empty list. Calibrate: there were **28** contact files / **8** domains on 2026-08-19.
- 🔴 **Channels no `contact.md` can ever list** — supply these by hand, every run:
  `jobs-noreply@linkedin.com` (all Easy Apply outcomes), `talent500.co`, `recro.io`.

## Steps

### 1. Find the applied jobs + who we contacted
Read the ledger for the row set; harvest recruiter domains from `contact.md`; add the hand-supplied
channels above. Diff the harvest against the last run's count before trusting it.

### 2. Search Gmail for replies (read-only)
Two sweeps, because they cover disjoint channels:
```
newer_than:14d in:inbox (from:infosys.com OR from:innovaesi.com OR from:ceipalmail.com OR ...)
newer_than:14d in:inbox from:jobs-noreply@linkedin.com
```
Use `search_threads` → then `get_thread` on each hit to read the latest incoming message.

🔴 **The second sweep is not optional.** Twenty-one consecutive checks ran only the first one and
therefore could not see a single Easy Apply outcome; the 22nd found **eight rejections in one
morning**. `contact.md` lists humans we emailed — the Easy Apply outcome channel has no human in it.

⚠️ `get_thread FULL_CONTENT` on a LinkedIn mail is ~150k characters and will overflow. Fetch it, let
the harness spill it to a file, then **grep the file** for the template key rather than reading it.

### 3. Classify each reply
From the message text, classify into one of:
- **Interview** — invite / "let's schedule a call" / availability request  → 🎉 high priority
- **Assessment** — coding test / take-home / screening task
- **Rejection** — "not moving forward" / "position filled"
- **Auto-ack** — "we received your application" (no human action)
- **Other** — anything ambiguous → surface for the human to read

🔴 **For `jobs-noreply@linkedin.com`, classify from the template key, not the words.** The subject
*"your application **was sent to** Y"* is a plain auto-ack; *"Your application **to** X at Y"* is a
status update whose verdict lives in the `lipi`/`trk`/`trkEmail` template key:
`email_jobs_application_rejected_01` = **Rejection** · `email_jobs_job_application_viewed_01` =
**viewed, still live — not a reply, no tick, no alert**.
The body is employer-controlled and therefore untrustworthy: the default template does say
"Unfortunately, we will not be moving forward", but Zetheta overwrote it with an unrelated internship
pitch, so the body read as an *offer* while the envelope was a *rejection*. **Status from the key,
intent from the body, never one alone.** Corroborate the mail→company mapping twice (thread id, then
the `Your update from <Company>` headline) before writing — a misattributed rejection is unrecoverable.

### 4. Update Notion (per matching job)
- Tick **`Reply = ✓`** (this cancels the Day-3/Day-7 follow-ups automatically).
- Move `Status`: Interview → **Interview** · Rejection → **Rejected** · Assessment → keep **Applied** + Notes.
- Put a one-line summary of the reply in `Notes`.

### 5. Alert on Slack (priority by type)
```
py -3 tools/slack_notify.py --event reply --title "<Company> — <CLASSIFICATION>" \
  --text "<who> replied: \"<snippet>\". Suggested next step: <one line>."
```
Make **Interview** loud (🎉). Include a short suggested next step (e.g., "propose 2 time slots").

### 6. De-dupe (don't re-alert the same reply)
Only alert if Notion `Reply` was not already ✓ for that job **or** a newer message arrived since last check.
(Simplest: if `Reply` is already ✓ and no newer message, skip.) Never double-ping the same reply.

## Success = the moment a recruiter replies, the owner gets a Slack ping (loud for interviews), Notion
updates itself, and the follow-up nudges stop — with zero auto-replies and nothing sent on his behalf.

## Scheduling
Runs a few times a day. Because Gmail is a **cloud connector** (unlike the local LinkedIn MCP), this checker
*could* run as a true cloud routine (laptop-off) — but the current build runs it **locally** alongside
discovery for simplicity (`tools/check-replies.ps1` + a Windows task). See [[05-decisions]] D11 for the
local-vs-cloud reasoning; the cloud option is the natural upgrade if catching replies laptop-off matters.
