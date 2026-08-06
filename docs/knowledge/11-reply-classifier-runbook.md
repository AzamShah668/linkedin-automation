# 11 — Reply Classifier Runbook (inbound alerts)

Back to [[00-INDEX]] | See [[09-discovery-runbook]] (the outbound sibling) & [[10-advanced-ideas]] 1.1.

The recipe the **reply-checker** runs (scheduled) to catch recruiter replies and alert the owner. Followable
cold. Read [[07-current-state]] first.

## Guardrails (non-negotiable)
- **Read-only Gmail.** `search_threads` + `get_thread` only. **Never auto-reply or send.** This only
  *detects, classifies, updates Notion, and pings Slack.* The owner replies to recruiters himself.
- **No fabrication.** Classify only from the actual email text; if unsure, mark `Other` and let the human read it.

## Inputs
- **Applied jobs** = Notion rows with `Status = Applied` (data source
  `collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2`) — these are the ones awaiting a reply.
- **Recruiter emails/domains** = from each `output/outreach/<slug>/contact.md` (the addresses we emailed).

## Steps

### 1. Find the applied jobs + who we contacted
Query Notion for `Status = 'Applied'`; collect Company + recruiter email/domain from the matching contact.md.

### 2. Search Gmail for replies (read-only)
Search the inbox for recent messages from those recruiters, e.g.:
```
newer_than:14d in:inbox (from:infosys.com OR from:innovaesi.com OR from:goodspace.ai)
```
(Build the `from:` list from step 1.) Use `search_threads` → then `get_thread` (FULL) on each hit to read
the latest incoming message.

### 3. Classify each reply
From the message text, classify into one of:
- **Interview** — invite / "let's schedule a call" / availability request  → 🎉 high priority
- **Assessment** — coding test / take-home / screening task
- **Rejection** — "not moving forward" / "position filled"
- **Auto-ack** — "we received your application" (no human action)
- **Other** — anything ambiguous → surface for the human to read

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
