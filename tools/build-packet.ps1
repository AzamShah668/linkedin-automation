# build-packet.ps1 — turn one board row into a ready-to-send packet.
# Fired from the dashboard ("Build the CV + outreach packet" on a role) or by hand:
#     powershell -ExecutionPolicy Bypass -File tools/build-packet.ps1 -JobId <notion-page-id>
#
# Runs Claude headless against docs/knowledge/15-build-packet-runbook.md, using the local
# LinkedIn MCP (read-only) + the cv-architect and recruiter-outreach skills.
# SENDS NOTHING. It writes files and posts one Slack card for the owner to approve.

param(
  [Parameter(Mandatory = $true)][string]$JobId
)

$ErrorActionPreference = 'Continue'
$proj = 'd:\linkdin automation'
Set-Location $proj

# claude.exe emits UTF-16 to the console; force UTF-8 or the log is unreadable.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\packet-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}-packets.log" -f (Get-Date))
$claude = Join-Path $env:USERPROFILE '.local\bin\claude.exe'

"=== build-packet $JobId  $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8

# Guard 1: the id has to exist on the board. Cheap, offline, and stops a typo from
# sending Claude off to research a company that was never on the list.
$row = & py -3 -c @"
import sys; sys.path.insert(0,'tools')
from board_db import connect, all_rows
hit = [r for r in all_rows(connect()) if r['id'] == '$JobId']
print(f\"{hit[0]['company']} | {hit[0]['job']} | fit {hit[0]['fit']}\" if hit else '')
"@ | Out-String
$row = $row.Trim()
if (-not $row) {
  $msg = "ABORT: no board row with id $JobId. Refresh the board, or check the id."
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 1
}
Write-Output "Target: $row"
"target: $row" | Out-File -FilePath $log -Append -Encoding utf8

# Guard 2: PROFILE CONTENTION. Two Chromium instances cannot share
# ~/.linkedin-mcp/profile, and the MCP misreports the conflict as "Session expired or
# invalid" — a lie that has cost hours twice (05-decisions D13).
# Check BOTH shapes: an open browser holding the profile dir, and — the far more common
# case — another mcp-server-linkedin already existing. The older guards only looked for
# the browser, which is absent until the MCP launches it on demand, so they missed the
# case that actually happens: a second Claude window with its own server.
$holder = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -like '*linkedin-mcp*profile*' }
if ($holder) {
  $msg = "SKIPPED: the LinkedIn browser profile is held by another process (pid $($holder[0].ProcessId)). Close other Claude Code windows and run this again."
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

# Count python-only: each Claude session spawns one server plus two uvx wrappers, so
# counting the whole tree over-reports 3x and would refuse every run.
$servers = @(Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -like '*mcp-server-linkedin*' })
if ($servers.Count -ge 1) {
  $pids = ($servers | ForEach-Object { $_.ProcessId }) -join ', '
  $msg = @"
SKIPPED: $($servers.Count) LinkedIn MCP server(s) already running (pid $pids).
This build needs the browser to itself. Close every other Claude Code window, then press
Build again. Run tools\linkedin-doctor.cmd to confirm nothing is left over.
"@
  Write-Output $msg; $msg | Out-File -FilePath $log -Append -Encoding utf8
  exit 0
}

$prompt = @"
Build the Job Hunt Autopilot APPLICATION PACKET for the board row with Notion page id $JobId.
Follow docs/knowledge/15-build-packet-runbook.md EXACTLY. Read that runbook and
docs/knowledge/07-current-state.md FIRST, then work the steps in order.

Non-negotiables:
- SEND NOTHING. No email, no LinkedIn message, no connection request. The only outbound
  thing is one Slack action card for the owner to approve.
- If output/outreach/<slug>/packet.json already exists, STOP and say it is already built.
- Warm insider before any cold recruiter (decision D8). Never invent a contact; if none is
  findable, say so in contact.md and leave the apply link as the route.
- CV must clear ATS 90. Produce BOTH the html and the PDF (tools/html-to-pdf.sh) — the
  dashboard download button needs the PDF, so a packet without one is half-built.
- No em-dashes, no markdown asterisks, no unresolved placeholders in any message.
- Finish by writing output/outreach/<slug>/packet.json with company matching the Notion
  Company value EXACTLY, plus the ats score and cv_stem. Without that file the dashboard
  cannot see the packet at all.
- Set the row's status to 'To Apply' in Notion and the local mirror.

Report at the end: the slug, the contact you chose and why, the ATS score, the files written,
and confirmation that nothing was sent.
"@

& $claude -p $prompt --permission-mode default 2>&1 |
  Out-File -FilePath $log -Append -Encoding utf8

$code = $LASTEXITCODE
"=== end (exit $code) $(Get-Date -Format o) ===" | Out-File -FilePath $log -Append -Encoding utf8

# Surface the run to the dashboard's output pane.
Get-Content -Path $log -Tail 60 -Encoding utf8 | ForEach-Object { Write-Output $_ }
exit $code
