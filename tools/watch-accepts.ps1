# watch-accepts.ps1 — stage 2 of the two-stage LinkedIn play.
# Checks who accepted a pending connection request and sends the approved pitch once its delay is up.
# Runs EVERY 4 HOURS while logged in (task "Job Hunt - Watch Accepts") and can be run on demand.
# Follows docs/knowledge/13-accept-watch-runbook.md. Only ever touches people already tracked as pending.
$ErrorActionPreference = 'Continue'

$proj = 'd:\linkdin automation'
Set-Location $proj
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\send-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}-accepts.log" -f (Get-Date))
$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'

# Nothing is tracked yet -> don't wake Claude at all. Keeps idle runs free.
$state = Join-Path $proj 'output\outreach\pending-invites.json'
if (-not (Test-Path $state)) {
  "$(Get-Date -Format o)  no pending-invites.json, nothing to watch" | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}
$live = & py -3 tools/invite_tracker.py list --status pending --json | Out-String
$ripe = & py -3 tools/invite_tracker.py due --json | Out-String
if ($live -notmatch '"linkedin_username"' -and $ripe -notmatch '"linkedin_username"') {
  "$(Get-Date -Format o)  nothing pending and nothing due, skipping" | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# BROWSER-PROFILE LOCK GUARD. Two Chromium instances cannot share ~/.linkedin-mcp/profile. If an interactive
# Claude session already holds it, this run gets an empty, logged-out browser and the MCP reports
# "Session expired or invalid" — a lie that previously sent us chasing a non-existent auth problem
# (2026-07-26, proven: headless said expired while the interactive session read profiles fine seconds later).
# Skip cleanly instead of misreporting. Proper fix is a second profile via --user-data-dir; see
# docs/knowledge/07-current-state.md.
$holder = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
if ($holder) {
  "$(Get-Date -Format o)  SKIPPED: LinkedIn browser profile is held by another session (pid $($holder[0].ProcessId)). Close Claude Code sessions to let this run." |
    Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# Let the network/MCP settle before touching LinkedIn (matters on the post-logon run).
Start-Sleep -Seconds 30

$prompt = @'
Run the Job Hunt Autopilot ACCEPT WATCH. Follow docs/knowledge/13-accept-watch-runbook.md EXACTLY.
First read 13-accept-watch-runbook.md and 07-current-state.md. Then:
1) py -3 tools/invite_tracker.py expire   — anything pending >14 days is dead; report it as "try email instead".
2) py -3 tools/invite_tracker.py list --status pending --json. For each, get_person_profile(linkedin_username)
   and read the DEGREE. Still 2nd/3rd = not accepted, leave it alone. Flipped to 1st = accepted:
   py -3 tools/invite_tracker.py mark-accepted --username <u>, then post a Slack "reply" event naming the
   person, the company and roughly when the pitch will auto-send.
3) py -3 tools/invite_tracker.py due --json. For each due row: open output/outreach/<slug>/touch-2-linkedin.md,
   take the EXACT 2b message, resolve the {Recruiter-A / Pawan} and [To ...] slots for THIS recipient, and send via
   send_message(linkedin_username, message=...). They are 1st-degree now so there is no invite cost.
   Respect FOLLOWUPS_DAILY_CAP and MIN_SECONDS_BETWEEN_SENDS + OUTREACH_JITTER_SECONDS from .env.
   After each success: py -3 tools/invite_tracker.py mark-sent --username <u>.
4) For each person actually messaged: Notion collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2 ->
   Status='Applied', Applied Date=today, Follow-ups Sent=0, plus a note of what was sent to whom.
5) Post ONE Slack summary only if something actually happened (accept, send, or expiry). If nothing happened,
   post NOTHING and exit quietly.
STRICT: never rewrite an approved message. Never send before invite_tracker says it is due. Never message
anyone not tracked as accepted. On any captcha, LinkedIn warning or unexpected MCP status: mark-failed, post
to Slack, stop the run — do not retry in a loop.
'@

# One-at-a-time across the WHOLE pipeline — see tools/pipeline-lock.ps1. This runner
# SENDS, so a collided run is worse here than anywhere else.
. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')
if (-not (Enter-PipelineLock -Name 'watch-accepts' -Log $log)) { exit 0 }

try {
  "=== Accept watch run $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8
  # Pipe through Out-File rather than `*>>` — PS 5.1 redirection writes UTF-16 and the log comes out garbled.
  & $claude -p $prompt --permission-mode default 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
  "=== end (exit $LASTEXITCODE) $(Get-Date -Format o) ===`n" | Out-File -FilePath $log -Append -Encoding utf8
}
finally { Exit-PipelineLock }
