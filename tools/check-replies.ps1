# check-replies.ps1 — the local scheduled runner for the reply-classifier.
# Runs Claude headless against the reply runbook: read Gmail (read-only) -> classify recruiter replies ->
# update Notion (Reply/Status) -> Slack alert. Never auto-replies or sends.
# Registered as Windows Scheduled Task "Job Hunt - Reply Check" (a few times/day).
$ErrorActionPreference = 'Continue'

$proj = 'd:\linkdin automation'
Set-Location $proj
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\reply-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}.log" -f (Get-Date))
$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'

$prompt = @'
Run the Job Hunt Autopilot REPLY CHECK. Follow docs/knowledge/11-reply-classifier-runbook.md EXACTLY.
First read 11-reply-classifier-runbook.md and 07-current-state.md. Then:
1) Query Notion (data source collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2) for Status='Applied'; get each Company + recruiter email/domain from output/outreach/<slug>/contact.md.
2) Gmail search_threads (READ-ONLY): newer_than:14d in:inbox with from: those recruiter domains. get_thread FULL on hits, read the latest incoming message.
3) Classify each: Interview / Assessment / Rejection / Auto-ack / Other.
4) Update the matching Notion job: tick Reply, set Status (Interview->Interview, Rejection->Rejected, Assessment->keep Applied), add a one-line note.
5) Slack alert per NEW reply: py -3 tools/slack_notify.py --event reply --title "<Company> - <TYPE>" --text "<who> replied: <snippet>. Suggested next step: <one line>". Make Interview loud.
6) De-dupe: skip jobs whose Reply is already ticked unless a newer message arrived.
STRICT: read-only Gmail. Do NOT reply to or send any email. Only detect, classify, update Notion, and Slack.
'@

# One-at-a-time across the WHOLE pipeline — see tools/pipeline-lock.ps1 for why a
# "is anyone running?" check cannot cover the wake-from-sleep stampede.
. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')
if (-not (Enter-PipelineLock -Name 'check-replies' -Log $log)) { exit 0 }

try {
  "=== Reply check run $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8

  # --- STEP 0: the LinkedIn inbox (D35) -------------------------------------------------
  # This runs FIRST and in plain Python, before the agent step, because it is the channel that
  # cost us fifteen days. On 2026-07-26 a warm insider replied in two hours asking for the CV,
  # and EIGHT consecutive runs of this script reported "zero replies" - every one of them
  # honest about the only place it looked, which was Gmail. Nothing here had ever opened
  # LinkedIn messaging, so the reply was not missed, it was unobservable.
  #
  # Deliberately NOT inside the Claude prompt: it must keep working when the agent step is
  # broken, rate-limited or over its usage cap (D25). A dependency on the thing that has failed
  # most often is not a fix.
  "--- LinkedIn inbox scan ---" | Out-File -FilePath $log -Append -Encoding utf8
  $env:PYTHONPATH = $proj
  & py -3 (Join-Path $proj 'apps\autopilot\replies.py') --headless --notify 2>&1 |
    Out-File -FilePath $log -Append -Encoding utf8
  $inboxExit = $LASTEXITCODE

  # Exit 2 means the inbox could NOT be read. That is not "no replies" and must never be
  # allowed to pass quietly - the whole point of D35.
  if ($inboxExit -eq 2) {
    "!! LINKEDIN INBOX UNREADABLE - this is NOT 'no replies'." | Out-File -FilePath $log -Append -Encoding utf8
    & py -3 (Join-Path $proj 'tools\slack_notify.py') --event info `
      --title "Reply check: LinkedIn inbox unreadable" `
      --text "The LinkedIn inbox scan could not run (likely a logged-out browser profile). This is NOT a report of zero replies - that channel went unchecked. Run: py -3 apps/autopilot/run.py login" 2>&1 |
      Out-File -FilePath $log -Append -Encoding utf8
  }

  # --- STEP 0b: applications that reached nobody (D32) -----------------------------------
  # Five of eight submissions reached no human, and that was only discovered by a hand audit on
  # the day someone happened to ask. Counting it on every run is the difference between a fact
  # and a lucky question. Read-only: it identifies the gap, it never contacts anyone.
  "--- coverage: applications with no human attached ---" | Out-File -FilePath $log -Append -Encoding utf8
  & py -3 (Join-Path $proj 'apps\autopilot\coverage.py') --notify 2>&1 |
    Out-File -FilePath $log -Append -Encoding utf8

  # --- STEP 1: Gmail, via the agent runbook ---------------------------------------------
  # Pipe through Out-File rather than `*>>` — PS 5.1 redirection writes UTF-16 and the log comes out garbled.
  & $claude -p $prompt --permission-mode default 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
  "=== end (claude exit $LASTEXITCODE, inbox exit $inboxExit) $(Get-Date -Format o) ===`n" | Out-File -FilePath $log -Append -Encoding utf8
}
finally { Exit-PipelineLock }
