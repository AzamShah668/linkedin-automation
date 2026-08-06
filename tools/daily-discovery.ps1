# daily-discovery.ps1 — the local scheduled runner for the Job Hunt Autopilot discovery robot.
# Runs Claude headless against the discovery runbook, using the LOCAL LinkedIn MCP + Slack + tools.
# Registered as a Windows Scheduled Task ("Job Hunt - Daily Discovery"), daily 08:00 local.
# Permissions are pre-allowlisted in .claude/settings.local.json so it runs unattended without bypass.
$ErrorActionPreference = 'Continue'

$proj = 'd:\linkdin automation'
Set-Location $proj

# claude.exe emits UTF-16 to the console; force UTF-8 so the log is readable, not "Y o u ' v e ...".
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\discovery-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}.log" -f (Get-Date))

$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'

# BROWSER-PROFILE LOCK GUARD (added 2026-07-30). Every other runner has had this since
# D13; discovery was the one that never got it, so an open Claude window did not stop the
# run - it just made LinkedIn report "Session expired or invalid" and the day's discovery
# came back empty, looking like "no new jobs today". An empty result and a blocked machine
# must not look the same in the log.
$holder = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
if ($holder) {
  "$(Get-Date -Format o)  SKIPPED: LinkedIn browser profile is held by another process (pid $($holder[0].ProcessId)). Close other Claude Code windows; discovery will run next cycle." |
    Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# Count python-only: each Claude session spawns one server plus two uvx wrappers, so
# counting the whole tree over-reports 3x and would refuse every run.
$servers = @(Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -like '*mcp-server-linkedin*' })
if ($servers.Count -ge 1) {
  $pids = ($servers | ForEach-Object { $_.ProcessId }) -join ', '
  "$(Get-Date -Format o)  SKIPPED: $($servers.Count) LinkedIn MCP server(s) already running (pid $pids). A Claude Code window is open; discovery will run next cycle." |
    Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

$prompt = @'
Run the Job Hunt Autopilot DAILY JOB DISCOVERY. Follow docs/knowledge/09-discovery-runbook.md EXACTLY.
First read 09-discovery-runbook.md and 07-current-state.md. Then:
1) LinkedIn MCP search_jobs (READ-ONLY) for the target roles/locations, prefer posts < 7 days old.
2) Dedupe against the Notion "Job Hunt - Autopilot" data source collection://2902aad8-1dbd-4bdc-b5e3-6cc4fa494be2 (skip anything already there).
3) Score fit 0-100 vs profile/master-profile.md + output/cv/positioning-selector.md; drop < 70.
4) For each NEW job >= 80, run one search_people warm-intro (shared-roots) check; set Warm Intro + note the verified tie only.
5) Add each NEW job (fit >= 70) to Notion: Job, Company, Fit Score, Location, Work Type, Source=LinkedIn, Status=New, Found=today, Warm Intro, URL, Notes.
6) Post ONE Slack digest: py -3 tools/slack_notify.py --event new_match --title "<N> new jobs (<M> warm)" --text "<top new jobs, fit-sorted>". If none cleared threshold, send a short --event info "no new matches today".
STRICT: read-only discovery. Do NOT send outreach, connect, or DM. Keep searches to a handful (ban-safe).
If LinkedIn MCP errors, run: uvx mcp-server-linkedin@latest --status  (once) then retry.
'@

# One-at-a-time across the WHOLE pipeline. The guards above catch an already-running
# server; they cannot catch four tasks starting in the same second after a wake-from-
# sleep, because at that instant no server exists yet. See tools/pipeline-lock.ps1.
. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')
if (-not (Enter-PipelineLock -Name 'daily-discovery' -Log $log)) { exit 0 }

try {
  "=== Daily discovery run $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8
  # Pipe through Out-File rather than `*>>` — PS 5.1 redirection writes UTF-16 and the log comes out garbled.
  & $claude -p $prompt --permission-mode default 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
  "=== end (exit $LASTEXITCODE) $(Get-Date -Format o) ===`n" | Out-File -FilePath $log -Append -Encoding utf8
}
finally { Exit-PipelineLock }
