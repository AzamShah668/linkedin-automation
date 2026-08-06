# tools/ — the Path A "glue" layer

Small, dependency-light helpers that turn the MCP-first pipeline into a complete system
(see `docs/knowledge/08-completion-plan.md`, decision D10). None of these send anything on their own or
bypass the human approval gate — they render, alert, and compute.

| Tool | What it does | Example |
|------|--------------|---------|
| `html-to-pdf.sh` | HTML CV / cover letter → print-ready PDF (headless Chrome/Edge, no installs) → `output/pdf/` | `bash tools/html-to-pdf.sh --all` |
| `slack_notify.py` | Post a pipeline event to Slack (reads token from `.env`) | `py -3 tools/slack_notify.py --event draft_ready --title "..." --text "..."` |
| `followups.py` | Decide which applied jobs are due a Day-3 / Day-7 nudge; print the draft; `--notify` fires Slack | `py -3 tools/followups.py --file jobs.json --notify` |
| `send_queue.py` | Enforce daily cap + min-delay + jitter on APPROVED items; print the throttled send plan (dry-run; never sends) | `py -3 tools/send_queue.py --file queue.json` |
| `daily-discovery.ps1` | The local scheduled runner: runs Claude headless against `docs/knowledge/09-discovery-runbook.md` (LinkedIn→Notion→Slack, read-only). Registered as Windows Task "Job Hunt - Daily Discovery" (daily 08:00). | `Start-ScheduledTask -TaskName "Job Hunt - Daily Discovery"` (manual test) |
| `check_approvals.py` | Read Slack for job cards you approved with a ✅ reaction (the phone-side gate). Read-only. Needs `channels:history` + `reactions:read`. | `py -3 tools/check_approvals.py --json` |
| `flush-approved.ps1` | At logon: send everything approved (Slack ✅ or Notion status) via the LinkedIn MCP, update the board, confirm on Slack. Install with `install-flush-task.cmd`. | `Start-ScheduledTask -TaskName "Job Hunt - Flush Approved"` |
| `slack_upload.py` | Upload a tailored CV PDF into the Slack channel (private to the workspace, reachable from the phone). Needs the `files:write` scope. | `py -3 tools/slack_upload.py --file output/pdf/<cv>.pdf --title "..."` |
| `ats_audit.py` | ATS keyword-gap auditor: CV (html/md/txt) vs a keyword list or JD → match %% + missing terms | `py -3 tools/ats_audit.py --cv <cv> --keywords "docker,kubernetes,..."` |
| `slack_action_card.py` | Push a complete phone-ready outreach card per job to Slack: who + tappable LinkedIn link + exact message to copy + email/CV + a DO-THIS checklist. Act entirely from your phone, no files. | `py -3 tools/slack_action_card.py --all` |

> **Note:** the Python tools force UTF-8 stdout so they don't crash on Windows' cp1252 console (·, —, ≥).
> Throttle caps are read from `.env` (`DAILY_OUTREACH_CAP`, `MIN_SECONDS_BETWEEN_SENDS`,
> `OUTREACH_JITTER_SECONDS`, `LINKEDIN_CONNECTS_DAILY_CAP`).

## Notion tracking convention (the job store's status model)

The **Notion "Job Hunt — Autopilot"** DB is the source of truth. Keep these fields honest so `followups.py`
and the digests work. Update them via the Notion MCP (`notion-update-page`) at each pipeline transition:

| Transition | Set in Notion |
|------------|---------------|
| Packet drafted | `Status = To Apply` (fire Slack `draft_ready`) |
| Touch 1 actually sent | `Status = Applied`, `Applied Date = today`, `Follow-ups Sent = 0` (fire `sent`) |
| A nudge sent | `Follow-ups Sent += 1`, `Next Action = +4 days` |
| Reply arrives | `Reply = ✓`, `Status = Interview` (or keep, but cancels follow-ups) |
| Dead | `Status = Rejected / Skipped` |

## The follow-up run loop (Path A — no Notion token, so the runner supplies data)

`followups.py` can't read Notion directly (no token in `.env`). The **runner** (Claude via MCP now, or a
scheduler with a Notion token later) does:

1. Query Notion for `Status = 'Applied'` jobs, selecting `Job, Company, Status, "Applied Date", Reply,
   "Follow-ups Sent", url`.
2. Shape rows into the JSON `followups.py` expects (`applied_date`, `reply`, `followups_sent`, `url`).
3. `py -3 tools/followups.py --notify` → Slack gets a `followup_due` per due nudge; each is still
   human-approved before it goes out.
4. After a nudge is approved+sent, bump `Follow-ups Sent` in Notion (see table above).

Nudge templates live in `.claude/skills/recruiter-outreach/references/message-rules.md` (Day 3 / Day 7);
`followups.py` carries short defaults but a real nudge should be personalized per company.

## Two-stage LinkedIn outreach (added 2026-07-26)

| Tool | What it does |
|---|---|
| `invite_tracker.py` | State store for pending connection requests. Records the knock, schedules the pitch. |
| `slack_react.py` | Stamps 📤 on a card. **The send-twice guard** — skip it and the same person is messaged every 30 min. |
| `watch-accepts.ps1` | Every 4h: who accepted? Send whatever pitch is due. Drives [[13-accept-watch-runbook]]. |
| `install-watch-task.cmd` | Owner double-clicks once to register the 4-hourly task. |

```
py -3 tools/slack_react.py --slug infosys              # stamp the card as sent (idempotent)
py -3 tools/slack_react.py --slug infosys --remove     # un-stamp, e.g. to re-queue a job
```

```
py -3 tools/invite_tracker.py add --slug infosys --person "Recruiter-A" \
    --username recruiter-a-recruiter-a-42670216a --role "AI Application Engineer"
py -3 tools/invite_tracker.py list --status pending
py -3 tools/invite_tracker.py mark-accepted --username <u>   # schedules the pitch 3-20h out
py -3 tools/invite_tracker.py due --json                     # ripe to send right now
py -3 tools/invite_tracker.py mark-sent --username <u>
py -3 tools/invite_tracker.py expire                         # age out 14-day silence -> try email
```

**Why bare requests:** a request *with* a note is capped at 3/month on a free account; a DM to an existing
1st-degree connection has no cap. So the note is skipped and the pitch lands after the accept. The 3 monthly
notes are reserved for warm insiders, sent by hand. See `05-decisions.md` D12.

**Notion status flow:** `To Apply` -> `Invite sent` (stage 1, the request) -> `Applied` (stage 2, the actual
pitch). A connection request is not an application; the Day-3/Day-7 follow-up clock starts at `Applied`.
