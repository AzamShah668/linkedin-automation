# sweep-packets.ps1 — build packets for whatever the board has discovered, unattended.
#     powershell -ExecutionPolicy Bypass -File tools/sweep-packets.ps1
#     powershell -ExecutionPolicy Bypass -File tools/sweep-packets.ps1 -Max 3
#
# Why this exists: build-packet.ps1 needs a -JobId, so until now every discovered job
# waited for a human to click Build on its row. Discovery runs daily and nothing
# consumed its output, so the board just accumulated unprocessed roles. This picks the
# highest-fit row that has no packet and builds it.
#
# SENDS NOTHING. It only calls build-packet.ps1, which writes files and posts one Slack
# card for the owner to approve.

param(
  [int]$Max = 2
)

$ErrorActionPreference = 'Continue'
$proj = 'd:\linkdin automation'
Set-Location $proj

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; chcp 65001 > $null } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $proj 'output\packet-log'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("{0:yyyy-MM-dd}-sweep.log" -f (Get-Date))

function Say($msg) {
  Write-Output $msg
  $msg | Out-File -FilePath $log -Append -Encoding utf8
}

Say "=== sweep-packets (max $Max)  $(Get-Date -Format o) ==="

# Cheap early exit FIRST, before anything expensive. A quiet cycle must never wake a
# headless Claude — that is the rule the other scheduled tasks already follow.
$todo = & py -3 -c @"
import json, glob, sys
sys.path.insert(0, 'tools')
from board_db import connect, all_rows

built = set()
for p in glob.glob('output/outreach/*/packet.json'):
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    if d.get('job_id'):
        built.add(d['job_id'])
    if d.get('company'):
        built.add(d['company'].strip().lower())

# 'New' and 'To Apply' are the only statuses worth building for. Anything further along
# has either been handled or deliberately dropped, and rebuilding it would be noise.
WANTED = {'New', 'To Apply'}
rows = [r for r in all_rows(connect())
        if (r.get('status') or 'New') in WANTED
        and r['id'] not in built
        and (r.get('company') or '').strip().lower() not in built]
rows.sort(key=lambda r: (r.get('fit') or 0), reverse=True)
for r in rows:
    print(f\"{r['id']}|{r['company']}|{r.get('fit')}\")
print('OK-SWEEP-QUERY')
"@ | Out-String

# The sentinel is the whole point: without it a Python SyntaxError printed to stdout
# produced zero matching lines, and the script announced "nothing to build" and exited
# 0. A broken query must never be indistinguishable from an empty queue.
if ($todo -notmatch 'OK-SWEEP-QUERY') {
  Say "ABORT: the board query failed, so the queue is unknown (NOT empty). Output was:"
  Say $todo.Trim()
  exit 1
}

$rows = @($todo.Trim() -split "`r?`n" | Where-Object { $_ -match '\|' })
if ($rows.Count -eq 0) {
  Say "nothing to build - every board row already has a packet. Exiting."
  exit 0
}
Say "$($rows.Count) row(s) without a packet; building up to $Max."

# Contention guard, once for the whole sweep. build-packet.ps1 checks this too, but
# doing it here means a blocked machine costs one cheap check instead of $Max of them.
$servers = @(Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -like '*mcp-server-linkedin*' })
if ($servers.Count -ge 1) {
  $pids = ($servers | ForEach-Object { $_.ProcessId }) -join ', '
  Say "SKIPPED: $($servers.Count) LinkedIn MCP server(s) already running (pid $pids). A Claude Code window is open. Nothing built; the queue keeps for the next run."
  exit 0
}

# Held for the WHOLE sweep, not per child: a sweep that released between builds would
# let another runner in halfway through and hit the very collision this prevents.
. (Join-Path $PSScriptRoot 'pipeline-lock.ps1')
if (-not (Enter-PipelineLock -Name 'sweep-packets' -Log $log)) { exit 0 }

try {

$done = 0
$skipped = 0
$failed = 0
$attempts = 0
foreach ($line in $rows) {
  # Cap ATTEMPTS, not successes. Capping on $done alone meant a run where every build
  # failed never incremented the counter and so marched through the entire queue -
  # observed 2026-08-01, where -Max 2 attempted five companies in a row because the
  # API was refusing every call. A broken environment must cost 2 attempts, not 15.
  if ($attempts -ge $Max) { break }
  # Two consecutive failures is an environment problem, not a data problem. Stop and
  # say so rather than grinding the whole queue into the same wall.
  if ($failed -ge 2) { Say "STOPPING: $failed builds failed in a row. That is the environment (API/auth/quota), not these particular jobs. The queue keeps for the next run."; break }
  $attempts++
  $id, $company, $fit = $line.Split('|')
  Say "--- building $company (fit $fit) id $id"

  # Capture the child's output instead of piping it straight to the log: build-packet.ps1
  # exits 0 when it SKIPS on profile contention, so the exit code cannot tell a real build
  # from a refusal. Counting attempts as builds made the summary line say "built 2" when
  # nothing had been built - the same lie as judging a task by its exit code (D17).
  #
  # NOTE ON THE PROCESS LAYER (D24 corrected 2026-08-01): the spawn below was once blamed
  # for the sweeper never building anything, on the theory that headless claude.exe works
  # two process layers deep and dies at three. That theory is WRONG. Removing this spawn
  # changed nothing; the builds still failed. The log said why, in a line nobody had read:
  #     You've hit your session limit - resets 3:30pm (Asia/Calcutta)
  # The "direct works, nested fails" reproduction was a clock, not a chain - the one
  # success ran before the limit and all seven failures after it. Keep the spawn: process
  # isolation means a crash inside a 16-minute headless build cannot take the sweep with it.
  $out = & powershell -ExecutionPolicy Bypass -File (Join-Path $proj 'tools\build-packet.ps1') -JobId $id 2>&1
  $code = $LASTEXITCODE
  $out | Out-File -FilePath $log -Append -Encoding utf8

  $text = $out -join "`n"

  # A Claude usage limit is not a failure of THIS job, and it will not clear inside this
  # sweep - the reset is hours away. Attempting the next row just burns another launch and
  # files a second misleading "FAILED" against a perfectly good role. Name it loudly:
  # this exact wall silently stopped every packet build on 2026-08-01 while the log read
  # "failed", and the project spent a day blaming process depth (D24) for a quota message
  # sitting in plain text in the log. If everything starts failing at once, read this first.
  if ($text -match "hit your (session|usage) limit|monthly spend limit|rate.?limit") {
    $limit = ([regex]::Match($text, ".*hit your.*limit[^\r\n]*")).Value.Trim()
    Say "STOPPING - CLAUDE USAGE LIMIT, not a problem with $company: $limit"
    Say "Nothing was built and nothing is wrong with the queue. It keeps for the next run, after the reset."
    break
  }

  if ($text -match 'SKIPPED:') {
    $skipped++
    Say "--- $company SKIPPED (not built). The machine is busy; stopping the sweep so the rest keep for the next run."
    break        # contention will not clear mid-sweep, so trying the next row just wastes a launch
  } elseif ($code -ne 0) {
    $failed++
    Say "--- $company FAILED with exit $code (not built)."
  } else {
    $done++
    $failed = 0        # a success clears the streak; only CONSECUTIVE failures mean the environment is broken
    Say "--- $company built."
  }

  # Each build drives a headless Claude and reads LinkedIn. Space them out for the same
  # reason every other step in this project is throttled.
  if ($done -lt $Max) { Start-Sleep -Seconds (Get-Random -Minimum 45 -Maximum 120) }
}

Say "=== end: built $done, failed $failed, skipped $skipped, attempted $attempts of $($rows.Count) queued  $(Get-Date -Format o) ==="

}
finally { Exit-PipelineLock }

exit 0
