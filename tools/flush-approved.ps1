# flush-approved.ps1 — stage 1 of the two-stage play: knock on the door for anything the owner approved
# on their phone while the laptop was off.
# Runs EVERY 30 MINUTES while logged in (task "Job Hunt - Flush Approved") and can be run on demand.
# Follows docs/knowledge/12-approved-send-runbook.md. Only touches jobs approved with a Slack check mark
# (or marked "APPROVED - SEND" in Notion).
$ErrorActionPreference = 'Continue'

$proj = 'd:\linkdin automation'
Set-Location $proj
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\send-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}.log" -f (Get-Date))
$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'

# CHEAP GUARD — this runs every 30 min, so never wake Claude unless something is actually approved.
# Slack is the primary gate; a Notion-only approval gets picked up by the next run that has Slack work,
# or on demand. Costs one Slack read per cycle instead of a whole headless Claude session.
$approvals = & py -3 tools/check_approvals.py --json | Out-String
if ($approvals -notmatch '"slug"') {
  "$(Get-Date -Format o)  nothing approved, skipping" | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# BROWSER-PROFILE LOCK GUARD — see the same block in watch-accepts.ps1 for the full reasoning. Short version:
# an interactive Claude session holding ~/.linkedin-mcp/profile makes this run report a fake "session expired".
$holder = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
if ($holder) {
  "$(Get-Date -Format o)  SKIPPED: LinkedIn browser profile is held by another session (pid $($holder[0].ProcessId)). Approvals stay queued for the next run." |
    Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# Give the network/MCP a moment to settle before touching LinkedIn.
Start-Sleep -Seconds 30

$prompt = @'
Run the Job Hunt Autopilot APPROVED-SEND flush. Follow docs/knowledge/12-approved-send-runbook.md EXACTLY.
First read 12-approved-send-runbook.md and 07-current-state.md. Then:
1) Find approvals from BOTH gates and de-duplicate by company slug:
   a) Slack reactions: py -3 tools/check_approvals.py --json   (this is the primary gate)
   b) Notion: rows in collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2 where Status = 'APPROVED - SEND'
   If none, exit quietly without posting anything.
2) For each, open output/outreach/<company-slug>/contact.md for the named recipient. Skip any row with no named contact, and say so.
3) Send a BARE connection request: connect_with_person(linkedin_username) with NO note argument. A request carrying a note is capped at 3/month and the MCP refuses it anyway (custom_note_limit_reached) — the pitch is delivered after they accept instead. Use send_message only for contacts who are ALREADY 1st-degree. Respect LINKEDIN_CONNECTS_DAILY_CAP and MIN_SECONDS_BETWEEN_SENDS from .env; highest Fit Score first; leave any over-cap rows still approved.
3b) For each request sent: py -3 tools/invite_tracker.py add --slug <slug> --person "<Name>" --username <u> --role "<role>"   so the accept watcher picks it up.
4) For each row actually sent: set Status='Invite sent' (NOT 'Applied' — a request is not an application; 13-accept-watch-runbook flips it to Applied when the real pitch lands) and append a note of who was contacted.
4b) MANDATORY, immediately after each successful send (not batched at the end): py -3 tools/slack_react.py --slug <slug>   This stamps the outbox_tray reaction. It is the send-twice guard: check_approvals.py skips stamped cards, so skipping this means the SAME person gets another connection request on every 30-minute run.
5) Post one Slack summary: py -3 tools/slack_notify.py --event sent --title "Knocked on <N> doors" --text "<one line each, plus any skips or cap deferrals>". Say plainly these are connection requests and the CV follows once they accept.
STRICT: never rewrite an approved message, never send to anything not marked APPROVED - SEND, never double-send.
'@

# One-at-a-time across the WHOLE pipeline — see tools/pipeline-lock.ps1. This runner
# SENDS, so a collided run is worse here than anywhere else.
. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')
if (-not (Enter-PipelineLock -Name 'flush-approved' -Log $log)) { exit 0 }

try {
  "=== Flush approved run $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8
  # Pipe through Out-File rather than `*>>` — PS 5.1 redirection writes UTF-16 and the log comes out garbled.
  & $claude -p $prompt --permission-mode default 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
  "=== end (exit $LASTEXITCODE) $(Get-Date -Format o) ===`n" | Out-File -FilePath $log -Append -Encoding utf8
}
finally { Exit-PipelineLock }
